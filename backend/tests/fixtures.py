from backend.models import Flow


def node(id, type, **fields):
    return {'id': id, 'type': type, 'label': id.replace('_', ' ').title(), **fields}


def edge(source, target, handle='next'):
    return {'source': source, 'target': target, 'handle': handle}


def buyer_flow():
    return Flow.model_validate({
        'name': 'Qualify & route', 'description': 'Route buyers to Sales and send sellers a help article.',
        'nodes': [node('start', 'trigger', event='New contact message'), node('role', 'ask_question', question='Are you a buyer or seller?', variable='role', choices=['buyer', 'seller']), node('route', 'condition', variable='role', operator='eq', value='buyer'), node('sales', 'assign_team', team='Sales'), node('help', 'send_message', message='Our help article: https://example.com/help'), node('done', 'end')],
        'edges': [edge('start', 'role'), edge('role', 'route'), edge('route', 'sales', 'true'), edge('route', 'help', 'false'), edge('sales', 'done'), edge('help', 'done')],
    })


def followup_flow():
    return Flow.model_validate({
        'name': 'Follow up gently', 'description': 'Offer a demo, remind after 30 minutes, or follow up after no response.',
        'nodes': [node('start', 'trigger', event='New contact message'), node('interest', 'ask_question', question='Would you like a demo?', variable='interest', choices=['yes', 'no'], timeout_seconds=3600), node('route', 'condition', variable='interest', operator='eq', value='yes'), node('delay', 'wait', duration_seconds=1800), node('remind', 'send_message', message='Here is your friendly demo reminder.'), node('thanks', 'send_message', message='Thank you for your time!'), node('followup', 'send_message', message='Just checking in. Let us know if you need help.'), node('done', 'end')],
        'edges': [edge('start', 'interest'), edge('interest', 'route'), edge('interest', 'followup', 'timeout'), edge('route', 'delay', 'true'), edge('route', 'thanks', 'false'), edge('delay', 'remind'), edge('remind', 'done'), edge('thanks', 'done'), edge('followup', 'done')],
    })


def api_flow():
    return Flow.model_validate({
        'name': 'Order status', 'description': 'Query order status with a safe failure route.',
        'nodes': [node('start', 'trigger', event='Order question'), node('order', 'ask_question', question='What is your order ID?', variable='order_id'), node('lookup', 'api_call', url='https://example.com/orders/{order_id}', save_as='result', mock_response={'status': 'in transit'}), node('status', 'send_message', message='Your order is {result.status}.'), node('sorry', 'send_message', message='Sorry, we could not look up your order.'), node('support', 'assign_team', team='Support'), node('done', 'end')],
        'edges': [edge('start', 'order'), edge('order', 'lookup'), edge('lookup', 'status', 'success'), edge('lookup', 'sorry', 'error'), edge('status', 'done'), edge('sorry', 'support'), edge('support', 'done')],
    })
