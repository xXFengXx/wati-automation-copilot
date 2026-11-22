import copy
import logging
import threading
import time
from collections import OrderedDict
from pathlib import Path
from typing import Literal
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import Field

from . import llm
from .models import StrictModel
from .simulation import SimulationError, advance, answer, new_simulation
from .validation import validate_flow


logging.basicConfig(level=logging.INFO, format='%(asctime)s %(name)s %(levelname)s %(message)s')
logger = logging.getLogger('wati.api')
app = FastAPI(title='Wati Automation Builder Copilot', version='0.1.0')
flows: OrderedDict = OrderedDict()
sessions: OrderedDict = OrderedDict()
lock = threading.RLock()
MAX_FLOWS, MAX_SESSIONS = 100, 300


@app.middleware('http')
async def request_logging(request: Request, call_next):
    request_id = uuid4().hex[:12]
    started = time.monotonic()
    response = await call_next(request)
    response.headers['X-Request-ID'] = request_id
    logger.info('request id=%s method=%s path=%s status=%d duration_ms=%d', request_id, request.method, request.url.path, response.status_code, (time.monotonic() - started) * 1000)
    return response


@app.exception_handler(llm.LLMError)
async def model_error(request, exc):
    return JSONResponse(status_code=exc.status, content={'detail': {'code': exc.code, 'message': exc.message}})


@app.get('/api/health')
def health():
    config = llm.settings()
    return {'status': 'ok', 'model_configured': bool(config['key']), 'provider': 'DeepSeek', 'model': config['model'], 'business_actions': 'simulated', 'storage': 'in-memory'}


class GenerateRequest(StrictModel):
    prompt: str = Field(min_length=10, max_length=6000)


@app.post('/api/flows/generate')
async def generate_flow(body: GenerateRequest):
    if not body.prompt.strip() or len(body.prompt.strip()) < 10:
        raise HTTPException(422, 'Describe the automation in at least 10 characters.')
    generated = await llm.generate(body.prompt.strip())
    if generated.flow is None:
        return {'status': 'needs_clarification', **generated.model_dump()}
    findings = validate_flow(generated.flow, prompt=body.prompt.strip())
    record = {'id': uuid4().hex, 'prompt': body.prompt.strip(), 'flow': generated.flow.model_dump(), 'explanation': generated.explanation, 'findings': [f.model_dump() for f in findings], 'valid': not any(f.severity == 'error' for f in findings), 'provider': 'DeepSeek', 'model': llm.settings()['model']}
    with lock:
        flows[record['id']] = record
        while len(flows) > MAX_FLOWS:
            evicted_id, _ = flows.popitem(last=False)
            for session_id in [key for key, value in sessions.items() if value['flow_id'] == evicted_id]:
                del sessions[session_id]
    return {'status': 'generated', **record}


@app.get('/api/flows/{flow_id}')
def get_flow(flow_id: str):
    with lock:
        if flow_id not in flows:
            raise HTTPException(404, 'Flow not found. In-memory data is cleared on restart or evicted after 100 flows.')
        return copy.deepcopy(flows[flow_id])


class SimulationRequest(StrictModel):
    flow_id: str = Field(min_length=1, max_length=64)
    scenario: Literal['success', 'api_failure'] = 'success'


@app.post('/api/simulations')
def start_simulation(body: SimulationRequest):
    from .models import Flow
    with lock:
        record = flows.get(body.flow_id)
        if not record:
            raise HTTPException(404, 'Flow not found. Generate it again.')
        flow = Flow.model_validate(record['flow'])
        if any(f.severity == 'error' for f in validate_flow(flow, prompt=record['prompt'])):
            raise HTTPException(409, 'Resolve validation errors before simulation.')
        state = advance(new_simulation(body.flow_id, flow, body.scenario), flow)
        sessions[state['id']] = state
        while len(sessions) > MAX_SESSIONS:
            sessions.popitem(last=False)
        return copy.deepcopy(state)


class AnswerRequest(StrictModel):
    answer: str | None = Field(default=None, max_length=2000)
    timeout: bool = False
    expected_revision: int = Field(ge=0, strict=True)


@app.post('/api/simulations/{session_id}/answers')
def submit_answer(session_id: str, body: AnswerRequest):
    from .models import Flow
    with lock:
        state = sessions.get(session_id)
        if not state:
            raise HTTPException(404, 'Simulation expired. Start a new simulation.')
        if state['revision'] != body.expected_revision:
            raise HTTPException(409, 'This answer is stale. Start a new simulation.')
        if body.timeout and body.answer:
            raise HTTPException(422, 'Submit either an answer or a timeout, not both.')
        record = flows.get(state['flow_id'])
        if not record:
            raise HTTPException(404, 'Flow expired. Generate a new flow.')
        try:
            return copy.deepcopy(answer(state, Flow.model_validate(record['flow']), body.answer, body.timeout))
        except SimulationError as exc:
            raise HTTPException(422, str(exc)) from exc


dist = Path(__file__).resolve().parents[1] / 'frontend' / 'dist'
if dist.exists():
    app.mount('/', StaticFiles(directory=dist, html=True), name='frontend')
