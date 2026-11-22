import pytest

from backend.models import ApiNode, Edge
from backend.simulation import advance, answer, new_simulation
from backend.tests.fixtures import api_flow, buyer_flow, edge, followup_flow
from backend.validation import validate_flow


BUYER_INTENT = 'Ask buyer or seller. Route buyers to the Sales team. Send sellers https://example.com/help.'


@pytest.mark.parametrize('url', ['https://[', 'https://example.com:broken/orders', 'https://example.com:99999/orders'])
def test_malformed_api_urls_become_findings(url):
    flow = api_flow()
    next(n for n in flow.nodes if n.type == 'api_call').url = url
    assert any(f.code == 'invalid_api_url' and f.severity == 'error' for f in validate_flow(flow))


def test_overwriting_api_result_invalidates_old_fields():
    flow = api_flow()
    flow.nodes.append(ApiNode(id='second', type='api_call', label='Second lookup', url='https://example.com/other', save_as='result', mock_response={'code': 'ok'}))
    next(e for e in flow.edges if e.source == 'lookup' and e.handle == 'success').target = 'second'
    flow.edges += [Edge(**edge('second', 'status', 'success')), Edge(**edge('second', 'sorry', 'error'))]
    assert any(f.code == 'undefined_placeholder' for f in validate_flow(flow))


def test_question_overwriting_object_invalidates_old_fields():
    flow = api_flow()
    question = next(n for n in flow.nodes if n.type == 'ask_question').model_copy(update={'id': 'confirm', 'variable': 'result', 'question': 'Please confirm'})
    flow.nodes.append(question)
    next(e for e in flow.edges if e.source == 'lookup' and e.handle == 'success').target = 'confirm'
    flow.edges.append(Edge(**edge('confirm', 'status')))
    assert any(f.code == 'undefined_placeholder' for f in validate_flow(flow))


def test_replaced_result_new_fields_remain_available():
    flow = api_flow()
    flow.nodes.append(ApiNode(id='second', type='api_call', label='Second lookup', url='https://example.com/other', save_as='result', mock_response={'code': 'ok'}))
    next(e for e in flow.edges if e.source == 'lookup' and e.handle == 'success').target = 'second'
    next(n for n in flow.nodes if n.id == 'status').message = '{result.code}'
    flow.edges += [Edge(**edge('second', 'status', 'success')), Edge(**edge('second', 'sorry', 'error'))]
    assert not any(f.severity == 'error' for f in validate_flow(flow))


def test_model_added_timeout_is_blocked_even_if_its_duration_is_used_for_a_wait():
    flow = followup_flow()
    prompt = 'Ask if they want a demo. If yes, wait 1 hour and send a reminder.'
    assert any(f.code == 'ungrounded_timeout' for f in validate_flow(flow, prompt=prompt))


@pytest.mark.parametrize('prompt', [
    'Ask if they want a demo. If yes, wait 30 minutes. If they do not reply within 1 hour, send a follow-up.',
    'Ask if they want a demo. If yes, wait thirty minutes. If no reply within an hour, follow up.',
    'Ask if they want a demo. If yes, wait half an hour. If no response within sixty minutes, follow up.',
])
def test_explicit_timing_with_distinct_wait_and_timeout_is_accepted(prompt):
    assert not any(f.code.startswith('ungrounded_') for f in validate_flow(followup_flow(), prompt=prompt))


def test_unspecified_and_negated_waits_are_not_authorized():
    flow = followup_flow()
    for prompt in ['Ask about a demo and follow up later.', 'Ask about a demo. Do not wait 30 minutes.']:
        findings = validate_flow(flow, prompt=prompt)
        assert any(f.code == 'ungrounded_wait' for f in findings)


def test_invented_team_or_url_is_blocked():
    flow = buyer_flow()
    findings = validate_flow(flow, prompt='Ask buyer or seller and send a helpful reply.')
    assert {'ungrounded_team', 'ungrounded_url'} <= {f.code for f in findings}
    assert not any(f.code.startswith('ungrounded_') for f in validate_flow(flow, prompt=BUYER_INTENT))


def test_failed_second_lookup_clears_the_first_lookup_result():
    flow = api_flow()
    confirm = next(n for n in flow.nodes if n.type == 'ask_question').model_copy(update={'id': 'confirm', 'variable': 'confirm', 'question': 'Continue?'})
    flow.nodes += [confirm, ApiNode(id='second', type='api_call', label='Second lookup', url='https://example.com/other', save_as='result', mock_response={'code': 'ok'})]
    next(e for e in flow.edges if e.source == 'lookup' and e.handle == 'success').target = 'confirm'
    next(n for n in flow.nodes if n.id == 'status').message = '{result.code}'
    flow.edges += [Edge(**edge('confirm', 'second')), Edge(**edge('second', 'status', 'success')), Edge(**edge('second', 'sorry', 'error'))]
    assert not any(f.severity == 'error' for f in validate_flow(flow))
    state = advance(new_simulation('test', flow, 'success'), flow)
    answer(state, flow, 'A123', False)
    assert state['status'] == 'waiting' and state['variables']['result']['status'] == 'in transit'
    state['scenario'] = 'api_failure'
    answer(state, flow, 'yes', False)
    assert state['status'] == 'completed' and 'result' not in state['variables']


def test_repeated_question_timeout_does_not_reuse_previous_answer():
    flow = buyer_flow()
    question = next(n for n in flow.nodes if n.type == 'ask_question').model_copy(update={'id': 'again', 'timeout_seconds': 10})
    flow.nodes.append(question)
    next(e for e in flow.edges if e.source == 'sales').target = 'again'
    flow.edges += [Edge(**edge('again', 'done')), Edge(**edge('again', 'done', 'timeout'))]
    assert not any(f.severity == 'error' for f in validate_flow(flow))
    state = advance(new_simulation('test', flow, 'success'), flow)
    answer(state, flow, 'buyer', False)
    assert state['status'] == 'waiting' and 'role' not in state['variables']
    answer(state, flow, None, True)
    assert state['status'] == 'completed' and 'role' not in state['variables']
