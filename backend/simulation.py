import copy
from datetime import datetime, timezone
from uuid import uuid4

from .models import Flow
from .validation import PLACEHOLDER


class SimulationError(Exception):
    pass


def new_simulation(flow_id: str, flow: Flow, scenario: str):
    return {
        'id': uuid4().hex, 'flow_id': flow_id, 'scenario': scenario,
        'status': 'running', 'current_node_id': next(n.id for n in flow.nodes if n.type == 'trigger'),
        'variables': {}, 'transcript': [], 'trace': [], 'visited_node_ids': [],
        'elapsed_seconds': 0, 'steps': 0, 'revision': 0,
        'created_at': datetime.now(timezone.utc).isoformat(),
    }


def lookup(variables, name):
    value = variables
    for part in name.split('.'):
        if not isinstance(value, dict) or part not in value:
            raise SimulationError(f'Variable "{name}" is unavailable on this path.')
        value = value[part]
    return value


def render(text, variables):
    return PLACEHOLDER.sub(lambda m: str(lookup(variables, m.group(1))), text)


def compare(actual, operator, expected):
    if operator == 'exists':
        return actual is not None and str(actual).strip() != ''
    if operator in {'gt', 'lt'}:
        try:
            a, b = float(actual), float(expected)
            return a > b if operator == 'gt' else a < b
        except (ValueError, TypeError):
            return False
    a, b = str(actual).strip().casefold(), str(expected).strip().casefold()
    return {'eq': lambda: a == b, 'neq': lambda: a != b, 'contains': lambda: b in a}[operator]()


def emit(state, role, content, node_id):
    state['transcript'].append({'role': role, 'content': content, 'node_id': node_id, 'at_seconds': state['elapsed_seconds']})


def move(state, flow, handle):
    edges = [e for e in flow.edges if e.source == state['current_node_id'] and e.handle == handle]
    if len(edges) != 1:
        raise SimulationError(f'Expected exactly one "{handle}" transition.')
    state['current_node_id'] = edges[0].target


def advance(state, flow: Flow):
    nodes = {n.id: n for n in flow.nodes}
    try:
        while state['status'] == 'running':
            if state['steps'] >= 80:
                raise SimulationError('Execution stopped at the 80-step safety limit.')
            node = nodes[state['current_node_id']]
            state['steps'] += 1
            state['visited_node_ids'].append(node.id)
            entry = {'node_id': node.id, 'label': node.label, 'type': node.type, 'at_seconds': state['elapsed_seconds'], 'detail': ''}
            state['trace'].append(entry)
            handle = 'next'
            if node.type == 'trigger':
                entry['detail'] = f'Simulated trigger: {node.event}'
            elif node.type == 'send_message':
                emit(state, 'bot', render(node.message, state['variables']), node.id)
                entry['detail'] = 'Message sent in this simulation.'
            elif node.type == 'ask_question':
                emit(state, 'bot', render(node.question, state['variables']), node.id)
                state['status'] = 'waiting'
                state['question'] = {'text': render(node.question, state['variables']), 'choices': node.choices, 'timeout_seconds': node.timeout_seconds}
                entry['detail'] = f'Waiting for an answer → {node.variable}'
                break
            elif node.type == 'condition':
                handle = 'true' if compare(lookup(state['variables'], node.variable), node.operator, node.value) else 'false'
                entry['detail'] = f'{node.variable} {node.operator} {node.value!s} → {handle}'
            elif node.type == 'api_call':
                target = render(node.url, state['variables'])
                handle = 'error' if state['scenario'] == 'api_failure' else 'success'
                if handle == 'success':
                    state['variables'][node.save_as] = copy.deepcopy(node.mock_response)
                entry['detail'] = f'SIMULATED {node.method} {target} → {handle}. No business request sent.'
                emit(state, 'system', entry['detail'], node.id)
            elif node.type == 'assign_team':
                entry['detail'] = f'SIMULATED assignment to {node.team}.'
                emit(state, 'system', entry['detail'], node.id)
            elif node.type == 'wait':
                state['elapsed_seconds'] += node.duration_seconds
                entry['detail'] = f'Virtual time advanced by {node.duration_seconds}s. No real wait.'
                emit(state, 'system', entry['detail'], node.id)
            elif node.type == 'end':
                state['status'] = 'completed'
                entry['detail'] = 'Flow completed.'
                break
            move(state, flow, handle)
    except (SimulationError, KeyError) as exc:
        state['status'] = 'failed'
        state['error'] = str(exc)
        emit(state, 'system', f'Simulation stopped: {exc}', state['current_node_id'])
    return state


def answer(state, flow, text: str | None, timeout: bool):
    if state['status'] != 'waiting':
        raise SimulationError('This simulation is not waiting for an answer.')
    node = next(n for n in flow.nodes if n.id == state['current_node_id'])
    if timeout:
        if not node.timeout_seconds:
            raise SimulationError('This question has no timeout configured.')
        state['elapsed_seconds'] += node.timeout_seconds
        emit(state, 'system', f'Simulated no reply for {node.timeout_seconds}s.', node.id)
        handle = 'timeout'
    else:
        text = (text or '').strip()
        if not text:
            raise SimulationError('Enter a non-empty answer.')
        if node.choices:
            choices = {c.casefold(): c for c in node.choices}
            if text.casefold() not in choices:
                raise SimulationError('Choose one of the listed answers.')
            text = choices[text.casefold()]
        state['variables'][node.variable] = text
        emit(state, 'user', text, node.id)
        handle = 'next'
    state['question'] = None
    state['status'] = 'running'
    state['revision'] += 1
    move(state, flow, handle)
    return advance(state, flow)
