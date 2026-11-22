"""TEST-ONLY entrypoint: replace the external provider, retain the real API/engine.

Never use this module to launch the application or claim real DeepSeek verification.
"""
from backend import llm
from backend.main import app
from backend.models import Generation
from backend.tests.fixtures import api_flow, buyer_flow, followup_flow


async def fixture_generation(prompt):
    text = prompt.lower()
    if 'model error' in text:
        raise llm.LLMError('model_rate_limit', 'DeepSeek is rate limiting requests. Wait and retry.', 503)
    if 'missing' in text:
        return Generation(flow=None, explanation='Please supply the destination URL.', clarification_questions=['What is your help article URL?'])
    flow = api_flow() if 'order' in text else followup_flow() if 'demo' in text else buyer_flow()
    if 'broken' in text:
        flow.edges = [e for e in flow.edges if e.handle != 'false']
    if 'dangling' in text:
        flow.edges[0].target = 'missing_node'
    return Generation(flow=flow, explanation='TEST FIXTURE: a deterministic provider response for browser regression tests. Production generation always calls DeepSeek.')


llm.generate = fixture_generation
llm.settings = lambda: {'key': 'test-only', 'base_url': 'https://example.invalid', 'model': 'contract-test-only'}
