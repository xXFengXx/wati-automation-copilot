import re
from collections import Counter, defaultdict, deque
from urllib.parse import urlparse

from .models import Finding, Flow
from .intent_validation import validate_intent_alignment


PLACEHOLDER = re.compile(r'\{([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)?)\}')


def validate_flow(flow: Flow, prompt: str | None = None) -> list[Finding]:
    findings: list[Finding] = []

    def add(severity, code, message, node_id=None):
        findings.append(Finding(severity=severity, code=code, message=message, node_id=node_id))

    counts = Counter(n.id for n in flow.nodes)
    for node_id, count in counts.items():
        if count > 1:
            add('error', 'duplicate_node', f'Node ID "{node_id}" is used more than once.', node_id)
    nodes = {n.id: n for n in flow.nodes}
    starts = [n for n in flow.nodes if n.type == 'trigger']
    if len(starts) != 1:
        add('error', 'trigger_count', 'A flow must have exactly one trigger.')
    if not any(n.type == 'end' for n in flow.nodes):
        add('error', 'missing_end', 'A flow must have an end node.')
    outgoing = defaultdict(list)
    incoming = defaultdict(list)
    for edge in flow.edges:
        if edge.source not in nodes or edge.target not in nodes:
            add('error', 'dangling_edge', f'Connection {edge.source} → {edge.target} references a missing node.')
            continue
        outgoing[edge.source].append(edge)
        incoming[edge.target].append(edge.source)
    for node in flow.nodes:
        required = {'end': set(), 'condition': {'true', 'false'}, 'api_call': {'success', 'error'}}.get(node.type, {'next'})
        if node.type == 'ask_question' and node.timeout_seconds:
            required = {'next', 'timeout'}
        actual = Counter(e.handle for e in outgoing[node.id])
        for handle in sorted(required - actual.keys()):
            add('error', 'missing_branch', f'"{node.label}" needs a "{handle}" connection.', node.id)
        for handle in actual:
            if handle not in required or actual[handle] != 1:
                add('error', 'ambiguous_branch', f'"{node.label}" must have exactly one connection per allowed branch; unexpected or duplicate "{handle}".', node.id)
        if node.type == 'trigger' and incoming[node.id]:
            add('error', 'trigger_incoming', 'The trigger cannot have incoming connections.', node.id)
        if node.type == 'api_call':
            parsed = None
            try:
                parsed = urlparse(node.url)
                # urllib defers invalid/out-of-range port checks until this access.
                _ = parsed.port
                if parsed.scheme not in {'https', 'http'} or not parsed.hostname or re.search(r'\s', node.url):
                    raise ValueError('Invalid HTTP(S) URL')
            except ValueError:
                add('error', 'invalid_api_url', 'Supply an explicit HTTP(S) business API URL.', node.id)
                parsed = None
            if parsed and (parsed.username or parsed.password):
                add('error', 'url_credentials', 'Remove credentials from the API URL.', node.id)
            if parsed and parsed.scheme == 'http':
                add('warning', 'insecure_url', 'This API URL uses unencrypted HTTP.', node.id)
            add('warning', 'simulated_api', 'Business API responses are test fixtures; no business request will be sent.', node.id)
        if node.type == 'condition' and node.operator != 'exists' and node.value is None:
            add('error', 'missing_condition_value', 'This comparison requires a value.', node.id)
        if node.type == 'condition' and node.operator in {'gt', 'lt'}:
            try:
                float(node.value)
            except (ValueError, TypeError):
                add('error', 'invalid_numeric_comparison', 'Numeric comparisons require a numeric value.', node.id)
        if node.type == 'ask_question' and not node.timeout_seconds:
            add('warning', 'no_question_timeout', 'No response timeout is configured; the conversation waits for a reply.', node.id)
        if node.type == 'wait':
            add('warning', 'virtual_wait', f'Wait advances the virtual clock by {node.duration_seconds} seconds; no real delay occurs.', node.id)

    reachable = set()
    if len(starts) == 1:
        pending = [starts[0].id]
        while pending:
            current = pending.pop()
            if current in reachable:
                continue
            reachable.add(current)
            pending.extend(e.target for e in outgoing[current])
        for node in flow.nodes:
            if node.id not in reachable:
                add('warning', 'unreachable_node', f'"{node.label}" cannot be reached from the trigger.', node.id)
        can_end = {n.id for n in flow.nodes if n.type == 'end'}
        pending = list(can_end)
        while pending:
            current = pending.pop()
            for parent in incoming[current]:
                if parent not in can_end:
                    can_end.add(parent)
                    pending.append(parent)
        for node_id in sorted(reachable - can_end):
            add('error', 'no_end_path', 'No path from this node reaches an end.', node_id)

    # A topological pass detects cycles before branch-specific data-flow analysis.
    degrees = {node_id: sum(p in reachable for p in incoming[node_id]) for node_id in reachable}
    queue = deque(k for k, v in degrees.items() if v == 0)
    processed = 0
    while queue:
        node_id = queue.popleft()
        processed += 1
        for edge in outgoing[node_id]:
            if edge.target in degrees:
                degrees[edge.target] -= 1
                if degrees[edge.target] == 0:
                    queue.append(edge.target)
    if processed < len(reachable):
        add('error', 'cycle', 'Cycles are outside this demo’s scope. Remove the loop before simulation.')

    # Question timeout and API failure paths do not create their normal output variables.
    # Recheck availability with branch-specific facts for acyclic graphs.
    if processed == len(reachable) and reachable:
        degrees = {node_id: sum(p in reachable for p in incoming[node_id]) for node_id in reachable}
        queue = deque(k for k, v in degrees.items() if v == 0)
        edge_vars = defaultdict(list)
        while queue:
            node_id = queue.popleft()
            node = nodes[node_id]
            definite = set.intersection(*edge_vars[node_id]) if edge_vars[node_id] else set()
            if node.type == 'condition' and node.variable not in definite:
                add('error', 'undefined_variable', f'"{node.variable}" is not guaranteed to exist on every incoming path.', node.id)
            for key in ('message', 'question', 'url'):
                for variable in PLACEHOLDER.findall(getattr(node, key, '')):
                    if variable not in definite:
                        add('error', 'undefined_placeholder', f'"{{{variable}}}" is not available on every incoming path.', node.id)
            for edge in outgoing[node_id]:
                outputs = definite.copy()
                # Starting a new collection/lookup invalidates the previous value,
                # including fields that belonged to its old object shape.
                replaced = node.variable if node.type == 'ask_question' else node.save_as if node.type == 'api_call' else None
                if replaced:
                    outputs = {name for name in outputs if name != replaced and not name.startswith(replaced + '.')}
                if node.type == 'ask_question' and edge.handle == 'next':
                    outputs.add(node.variable)
                if node.type == 'api_call' and edge.handle == 'success':
                    outputs.add(node.save_as)
                    outputs.update(f'{node.save_as}.{key}' for key in node.mock_response)
                edge_vars[edge.target].append(outputs)
                degrees[edge.target] -= 1
                if degrees[edge.target] == 0:
                    queue.append(edge.target)
    if prompt is not None:
        findings.extend(validate_intent_alignment(flow, prompt))
    return findings
