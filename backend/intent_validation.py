"""Conservative evidence checks, not a general natural-language correctness proof."""
import re

from .models import Finding, Flow


_SMALL = 'one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen'.split()
_NUMBERS = {word: value for value, word in enumerate(_SMALL, 1)}
for value, word in enumerate('twenty thirty forty fifty sixty seventy eighty ninety'.split(), 2):
    _NUMBERS[word] = value * 10
    _NUMBERS.update({f'{word} {unit}': value * 10 + i for i, unit in enumerate(_SMALL[:9], 1)})
_NUMBERS.update({'a': 1, 'an': 1, 'half': .5, 'half a': .5, 'half an': .5, 'quarter': .25, 'quarter a': .25, 'quarter an': .25})
_WORDS = '|'.join(re.escape(word).replace(r'\ ', '[- ]') for word in sorted(_NUMBERS, key=len, reverse=True))
_DURATION = re.compile(r'\b(?P<amount>\d+(?:\.\d+)?|' + _WORDS + r')\s*(?P<unit>seconds?|secs?|s|minutes?|mins?|m|hours?|hrs?|h|days?|d)\b', re.I)
_NO_REPLY = re.compile(r'\b(?:no|not|without|never|don\x27t|doesn\x27t)\b.{0,45}\b(?:repl(?:y|ied)|answer(?:ed)?|respond(?:ed)?|response)\b|\b(?:timeout|time out|times out)\b|\bwait\s+(?:for|up to)\b.{0,25}\b(?:reply|answer|response)\b')
_NEGATED = re.compile(r'\b(?:do not|don\x27t|never|no)\s+(?:wait|delay|timeout)\b')
_WAIT = re.compile(r'\b(?:wait|delay|remind|reminder|follow.?up|after)\b')


def _timing_evidence(prompt: str) -> tuple[set[int], set[int]]:
    waits, timeouts = set(), set()
    for clause in re.split(r'[,;\n]|(?<=[.!?])\s+', prompt.casefold().replace('’', "'")):
        if _NEGATED.search(clause):
            continue
        target = timeouts if _NO_REPLY.search(clause) else waits if _WAIT.search(clause) else None
        if target is None:
            continue
        for match in _DURATION.finditer(clause):
            amount = match['amount'].replace('-', ' ')
            value = _NUMBERS[amount] if amount in _NUMBERS else float(amount)
            unit = match['unit'][0]
            seconds = value * {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}[unit]
            if seconds > 0 and float(seconds).is_integer():
                target.add(int(seconds))
    return waits, timeouts


def _urls(text: str) -> set[str]:
    return {value.rstrip('.,;:!?)]') for value in re.findall(r'https?://[^\s<>"\x27]+', text)}


def validate_intent_alignment(flow: Flow, prompt: str) -> list[Finding]:
    findings = []
    waits, timeouts = _timing_evidence(prompt)
    source_urls = _urls(prompt)

    def add(code, message, node_id):
        findings.append(Finding(severity='error', code=code, message=message, node_id=node_id))

    for node in flow.nodes:
        if node.type == 'wait' and node.duration_seconds not in waits:
            add('ungrounded_wait', f'The {node.duration_seconds}s wait is not supported by an explicit wait/reminder duration in your description. Specify it or regenerate without this rule.', node.id)
        if node.type == 'ask_question' and node.timeout_seconds and node.timeout_seconds not in timeouts:
            add('ungrounded_timeout', f'The {node.timeout_seconds}s question timeout is not supported by an explicit no-reply duration in your description. Specify it or regenerate without this rule.', node.id)
        if node.type == 'assign_team' and not re.search(r'(?<!\w)' + re.escape(node.team.strip()) + r'(?!\w)', prompt, re.I):
            add('ungrounded_team', f'Team "{node.team}" is not named in your description. Supply the destination explicitly.', node.id)
        used_urls = set()
        for key in ('message', 'question', 'url'):
            used_urls.update(_urls(getattr(node, key, '')))
        for url in sorted(used_urls - source_urls):
            add('ungrounded_url', f'The URL "{url}" is not present in your description. Supply the actual URL rather than accepting a generated destination.', node.id)
    return findings
