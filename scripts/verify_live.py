"""Run the three agreed acceptance scenarios against the normal local application.

Requires real DeepSeek credentials configured in the backend. Performs three
real inference calls; business execution remains simulated.
"""
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx


SCENARIOS = [
    ('qualification', 'When a new contact messages us, ask whether they are a buyer or seller, with buyer and seller as the allowed answers. Route buyers to the Sales team. Send sellers our help article at https://example.com/help. Then end the conversation.', [('buyer', 'success', False), ('seller', 'success', False)]),
    ('follow-up', 'When a new contact messages us, ask if they would like a product demo, with yes and no as the allowed answers. If yes, wait 30 minutes, then send a friendly demo reminder. If no, send a polite thank-you. If they do not answer within 1 hour, send a gentle follow-up and end. End after each path.', [('yes', 'success', False), ('no', 'success', False), (None, 'success', True)]),
    ('API paths', 'When a contact asks about an order, ask for their order ID as free text. Query GET https://example.com/orders/{order_id}. For the simulated success response, use status="in transit" and tell the customer the status. If the API fails, apologize and assign the conversation to the Support team. Then end.', [('A123', 'success', False), ('A123', 'api_failure', False)]),
]


def check_business_result(name, reply, outcome, timeout, record, state, question_id):
    nodes = {n['id']: n for n in record['flow']['nodes']}
    visited = [nodes[node_id] for node_id in state['visited_node_ids']]
    teams = {n['team'].strip().casefold() for n in visited if n['type'] == 'assign_team'}
    messages = '\n'.join(m['content'] for m in state['transcript'] if m['role'] == 'bot').casefold()
    if name == 'qualification':
        if reply == 'buyer':
            assert 'sales' in teams, 'Buyer did not reach Sales'
            assert 'https://example.com/help' not in messages, 'Buyer incorrectly took the seller route'
        else:
            assert 'https://example.com/help' in messages, 'Seller did not receive the specified help link'
            assert 'sales' not in teams, 'Seller incorrectly reached Sales'
    elif name == 'follow-up':
        expected = 3600 if timeout else 1800 if reply == 'yes' else 0
        assert state['elapsed_seconds'] == expected, 'Unexpected virtual timing'
        assert any(n['type'] == 'send_message' for n in visited), 'Follow-up path sent no message'
        if timeout:
            assert nodes[question_id]['variable'] not in state['variables'], 'Timeout incorrectly stored an answer'
    else:
        apis = [n for n in visited if n['type'] == 'api_call']
        assert len(apis) == 1, 'Expected exactly one business API step'
        api = apis[0]
        assert api['url'] == 'https://example.com/orders/{order_id}', 'Business API URL changed'
        if outcome == 'success':
            assert state['variables'][api['save_as']]['status'] == 'in transit', 'Unexpected success fixture'
            assert 'in transit' in messages, 'Success did not communicate the returned status'
            assert 'support' not in teams, 'Successful lookup incorrectly reached Support'
        else:
            assert api['save_as'] not in state['variables'], 'Failure incorrectly stored a successful result'
            assert 'support' in teams, 'API failure did not reach Support'
            assert 'in transit' not in messages, 'API failure fabricated a delivery status'


def main():
    base = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8000'
    with httpx.Client(base_url=base, timeout=150, trust_env=False) as client:
        health = client.get('/api/health').raise_for_status().json()
        if not health['model_configured']:
            print('NOT RUN: Set DEEPSEEK_API_KEY in .env and restart backend.main:app first.')
            return 2
        if health['model'] == 'contract-test-only':
            print('NOT RUN: The test-only provider is active. Start backend.main:app instead.')
            return 2
        print(f'Live provider: {health["provider"]}; model: {health["model"]}')
        report = {'checked_at_utc': datetime.now(timezone.utc).isoformat(), 'provider': health['provider'], 'model': health['model'], 'business_actions': 'simulated', 'scenarios': []}
        for name, prompt, paths in SCENARIOS:
            started = time.monotonic()
            response = client.post('/api/flows/generate', json={'prompt': prompt})
            if not response.is_success:
                print(f'FAIL {name}: generation HTTP {response.status_code}: {response.json().get("detail")}')
                return 1
            record = response.json()
            if record['status'] != 'generated' or not record.get('valid'):
                print(f'FAIL {name}: clarification or validation errors; inspect in the UI.')
                print(record.get('clarification_questions', record.get('findings')))
                return 1
            assert record['explanation'].strip(), 'Missing flow explanation'
            evidence = {'name': name, 'generation_seconds': round(time.monotonic() - started, 3), 'request_id': response.headers.get('x-request-id'), 'record': record, 'paths': []}
            for reply, outcome, timeout in paths:
                state = client.post('/api/simulations', json={'flow_id': record['id'], 'scenario': outcome}).raise_for_status().json()
                if state['status'] != 'waiting':
                    print(f'FAIL {name}: expected a question before answering.')
                    return 1
                question_id = state['current_node_id']
                state = client.post(f'/api/simulations/{state["id"]}/answers', json={'answer': reply, 'timeout': timeout, 'expected_revision': state['revision']}).raise_for_status().json()
                if state['status'] != 'completed':
                    print(f'FAIL {name}: path did not complete; inspect generated flow in the UI.')
                    return 1
                check_business_result(name, reply, outcome, timeout, record, state, question_id)
                evidence['paths'].append({'answer': reply, 'api_outcome': outcome, 'timeout': timeout, 'result': state})
                print(f'PASS {name}: {reply or "no reply"} / {outcome}; {state["steps"]} steps, +{state["elapsed_seconds"]}s')
            report['scenarios'].append(evidence)
        output = Path(__file__).resolve().parents[1] / 'output' / 'live-acceptance.json'
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f'Evidence saved: {output}')
        print('PASS: live generation and all seven paths completed. Manually review business content and explanation before recording.')
        return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (httpx.HTTPError, AssertionError) as exc:
        print(f'FAIL: {exc}')
        sys.exit(1)
