import asyncio
import json

import httpx
import pytest
from fastapi.testclient import TestClient

from backend import llm, main
from backend.models import Generation
from backend.tests.fixtures import buyer_flow


@pytest.fixture
def client(monkeypatch):
    main.flows.clear()
    main.sessions.clear()

    async def generate(prompt):
        return Generation(flow=buyer_flow(), explanation='Buyers go to Sales; sellers receive the help article.')

    monkeypatch.setattr(llm, 'generate', generate)
    with TestClient(main.app) as client:
        yield client


def create_flow(client):
    response = client.post('/api/flows/generate', json={'prompt': 'Route buyers and sellers.'})
    assert response.status_code == 200
    assert response.headers['X-Request-ID']
    return response.json()['id']


def test_api_full_path_and_duplicate_answer_protection(client):
    flow_id = create_flow(client)
    sim = client.post('/api/simulations', json={'flow_id': flow_id}).json()
    payload = {'answer': 'buyer', 'expected_revision': 0}
    path = f'/api/simulations/{sim["id"]}/answers'
    response = client.post(path, json=payload)
    assert response.status_code == 200
    assert response.json()['status'] == 'completed'
    assert client.post(path, json=payload).status_code == 409


def test_api_invalid_flow_cannot_start(client):
    flow_id = create_flow(client)
    main.flows[flow_id]['flow']['edges'] = [e for e in main.flows[flow_id]['flow']['edges'] if e['handle'] != 'false']
    assert client.post('/api/simulations', json={'flow_id': flow_id}).status_code == 409


def test_clarification_is_not_a_flow(client, monkeypatch):
    async def clarify(prompt):
        return Generation(flow=None, explanation='A URL is needed.', clarification_questions=['What is the help article URL?'])
    monkeypatch.setattr(llm, 'generate', clarify)
    result = client.post('/api/flows/generate', json={'prompt': 'Send them our help article.'}).json()
    assert result['status'] == 'needs_clarification'
    assert not main.flows


def test_unknown_resources_and_invalid_input(client):
    assert client.get('/api/flows/missing').status_code == 404
    assert client.post('/api/flows/generate', json={'prompt': '   '}).status_code == 422
    assert client.post('/api/simulations', json={'flow_id': 'missing'}).status_code == 404
    assert client.post('/api/simulations/missing/answers', json={'answer': 'yes', 'expected_revision': 0}).status_code == 404


def mock_deepseek(monkeypatch, handler):
    monkeypatch.setenv('DEEPSEEK_API_KEY', 'test-key-not-real')
    cls = httpx.AsyncClient
    monkeypatch.setattr(httpx, 'AsyncClient', lambda **kwargs: cls(transport=httpx.MockTransport(handler), **kwargs))


@pytest.mark.parametrize(('status', 'code'), [(401, 'model_auth'), (402, 'model_balance'), (429, 'model_rate_limit'), (422, 'model_request'), (503, 'model_unavailable')])
def test_deepseek_errors_are_actionable(monkeypatch, status, code):
    mock_deepseek(monkeypatch, lambda request: httpx.Response(status, json={'error': 'upstream details intentionally not exposed'}))
    with pytest.raises(llm.LLMError) as error:
        asyncio.run(llm.generate('Say hello to a new contact.'))
    assert error.value.code == code


def test_live_request_contract_and_one_schema_repair(monkeypatch):
    requests = []
    valid = Generation(flow=buyer_flow(), explanation='A real model result.').model_dump_json()
    def handler(request):
        body = json.loads(request.content)
        requests.append(body)
        assert request.headers['authorization'] == 'Bearer test-key-not-real'
        assert body['response_format'] == {'type': 'json_object'}
        return httpx.Response(200, json={'choices': [{'finish_reason': 'stop', 'message': {'content': 'broken JSON' if len(requests) == 1 else valid}}]})
    mock_deepseek(monkeypatch, handler)
    result = asyncio.run(llm.generate('Route buyers and sellers.'))
    assert result.flow.name == 'Qualify & route'
    assert len(requests) == 2


@pytest.mark.parametrize(('content', 'finish'), [('', 'stop'), ('   ', 'stop'), ('{}', 'length'), ('not JSON', 'stop')])
def test_invalid_output_never_becomes_fake_success(monkeypatch, content, finish):
    mock_deepseek(monkeypatch, lambda request: httpx.Response(200, json={'choices': [{'finish_reason': finish, 'message': {'content': content}}]}))
    with pytest.raises(llm.LLMError, match='repair attempt'):
        asyncio.run(llm.generate('Say hello to a new contact.'))


def test_missing_key_is_explicit(monkeypatch):
    monkeypatch.delenv('DEEPSEEK_API_KEY', raising=False)
    with pytest.raises(llm.LLMError) as error:
        asyncio.run(llm.generate('Say hello to a new contact.'))
    assert error.value.code == 'model_not_configured'


def test_timeout_is_explicit(monkeypatch):
    def handler(request):
        raise httpx.ReadTimeout('timed out', request=request)
    mock_deepseek(monkeypatch, handler)
    with pytest.raises(llm.LLMError) as error:
        asyncio.run(llm.generate('Say hello to a new contact.'))
    assert error.value.code == 'model_timeout'
