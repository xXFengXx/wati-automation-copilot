import pytest

from backend.models import Flow
from backend.simulation import SimulationError, advance, answer, compare, new_simulation
from backend.validation import validate_flow
from backend.tests.fixtures import api_flow, buyer_flow, edge, followup_flow, node


def codes(flow):
    return {f.code for f in validate_flow(flow) if f.severity == 'error'}


@pytest.mark.parametrize('factory', [buyer_flow, followup_flow, api_flow])
def test_acceptance_flows_are_valid(factory):
    assert codes(factory()) == set()


@pytest.mark.parametrize(('role', 'expected', 'absent'), [('BUYER', 'sales', 'help'), ('seller', 'help', 'sales')])
def test_buyer_and_seller_take_exclusive_routes(role, expected, absent):
    flow = buyer_flow()
    state = advance(new_simulation('flow', flow, 'success'), flow)
    assert state['status'] == 'waiting'
    answer(state, flow, role, False)
    assert state['status'] == 'completed'
    assert expected in state['visited_node_ids']
    assert absent not in state['visited_node_ids']


def test_invalid_choice_does_not_advance_or_mutate():
    flow = buyer_flow()
    state = advance(new_simulation('flow', flow, 'success'), flow)
    before = state.copy()
    with pytest.raises(SimulationError, match='listed answers'):
        answer(state, flow, 'other', False)
    assert state == before


@pytest.mark.parametrize(('reply', 'timeout', 'seconds', 'visited'), [('yes', False, 1800, 'remind'), ('no', False, 0, 'thanks'), (None, True, 3600, 'followup')])
def test_followup_uses_virtual_time(reply, timeout, seconds, visited):
    flow = followup_flow()
    state = advance(new_simulation('flow', flow, 'success'), flow)
    answer(state, flow, reply, timeout)
    assert state['status'] == 'completed'
    assert state['elapsed_seconds'] == seconds
    assert visited in state['visited_node_ids']
    if timeout:
        assert 'interest' not in state['variables']


@pytest.mark.parametrize('scenario', ['success', 'api_failure'])
def test_api_success_and_failure_are_isolated(scenario):
    flow = api_flow()
    state = advance(new_simulation('flow', flow, scenario), flow)
    answer(state, flow, 'A123', False)
    assert state['status'] == 'completed'
    if scenario == 'success':
        assert state['variables']['result']['status'] == 'in transit'
        assert 'support' not in state['visited_node_ids']
        assert any(m['content'] == 'Your order is in transit.' for m in state['transcript'])
    else:
        assert 'result' not in state['variables']
        assert 'support' in state['visited_node_ids']
        assert 'status' not in state['visited_node_ids']


def test_missing_branch_blocks_execution():
    flow = buyer_flow()
    flow.edges = [e for e in flow.edges if e.handle != 'false']
    assert 'missing_branch' in codes(flow)


def test_duplicate_node_and_dangling_edge_are_found():
    flow = buyer_flow()
    flow.nodes.append(flow.nodes[0])
    flow.edges.append(type(flow.edges[0])(source='missing', target='done'))
    assert {'duplicate_node', 'dangling_edge'} <= codes(flow)


def test_api_error_cannot_read_success_result():
    flow = api_flow()
    next(n for n in flow.nodes if n.id == 'sorry').message = '{result.status}'
    assert 'undefined_placeholder' in codes(flow)


def test_timeout_cannot_read_missing_answer():
    flow = followup_flow()
    next(n for n in flow.nodes if n.id == 'followup').message = 'You said {interest}'
    assert 'undefined_placeholder' in codes(flow)


def test_join_requires_variable_on_every_incoming_branch():
    flow = api_flow()
    flow.nodes.append(type(next(n for n in flow.nodes if n.id == 'status'))(id='joined', type='send_message', label='Joined', message='{result.status}'))
    flow.edges = [e for e in flow.edges if e.target != 'done'] + [type(flow.edges[0])(**edge('status', 'joined')), type(flow.edges[0])(**edge('support', 'joined')), type(flow.edges[0])(**edge('joined', 'done'))]
    assert 'undefined_placeholder' in codes(flow)


def test_cycle_and_non_ending_paths_are_found():
    flow = buyer_flow()
    next(e for e in flow.edges if e.source == 'sales').target = 'sales'
    assert {'cycle', 'no_end_path'} <= codes(flow)


def test_unreachable_parent_does_not_create_false_cycle():
    flow = buyer_flow()
    flow.nodes.append(type(next(n for n in flow.nodes if n.id == 'help'))(id='orphan', type='send_message', label='Orphan', message='Unreachable'))
    flow.edges.append(type(flow.edges[0])(**edge('orphan', 'done')))
    findings = validate_flow(flow)
    assert 'cycle' not in codes(flow)
    assert any(f.code == 'unreachable_node' for f in findings)


def test_session_variables_do_not_leak():
    flow = buyer_flow()
    a, b = (advance(new_simulation('f', flow, 'success'), flow) for _ in range(2))
    answer(a, flow, 'buyer', False)
    assert b['variables'] == {} and b['status'] == 'waiting'


@pytest.mark.parametrize(('actual', 'op', 'expected', 'result'), [('BUYER', 'eq', 'buyer', True), (' 12 ', 'gt', 10, True), ('n/a', 'gt', 10, False), ('Hello World', 'contains', 'WORLD', True), ('seller', 'neq', 'buyer', True)])
def test_condition_semantics(actual, op, expected, result):
    assert compare(actual, op, expected) is result
