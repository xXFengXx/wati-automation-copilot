# Verification record

Checked on 2026-11-22 (Asia/Shanghai).

| Check | Result | Boundary |
| --- | --- | --- |
| `python -m pytest backend/tests -q` | 56 passed | Unit/API tests; provider HTTP mocked, engine real. Includes malformed URLs, overwritten values, and prompt-evidence checks. One upstream Starlette/httpx deprecation warning. |
| `npm run build` | Passed | TypeScript checked and production bundle generated. Vendor bundle size and compiler directive advisories remain non-blocking. |
| `npm run test:e2e` | 7 passed | Headless installed Edge; real API/validator/interpreter with test-only provider; includes resizing an existing desktop graph to mobile. |
| Desktop / mobile visual inspection | Passed | Graph, branches, node details, conversation, and narrow viewport inspected. Graph fit has an explicit visibility assertion. |
| One-page write-up PDF | 1 page; rendered and inspected | Text fits without clipping. |
| Normal app `/` | HTTP 200 | Production static frontend served by FastAPI on loopback. |
| Normal app generation without key | HTTP 503 `model_not_configured` | Explicit failure; no generated template fallback. |
| Real DeepSeek acceptance | Passed: 3 real generations / 7 simulation paths, plus 2 clarification cases | DeepSeek `deepseek-flash`; checks destinations, timing, safe failure, missing help URL, and vague follow-up timing. Five requests with `scripts/verify_live.py --edge-cases`; not a reliability guarantee. |
| Real-provider browser smoke | Passed | Normal application, no test stubs: real generation, graph, buyer → Sales, execution trace, no JavaScript errors, desktop/mobile layout. |

Browser checks cover both qualification answers, JSON inspection/export, virtual wait and question timeout, API failure handoff, clarification, blocking validation, provider errors, mobile horizontal overflow, and graph inspection with a dangling connection.

The initial sandbox could not launch Edge. Tests passed after the same local-only suite ran outside the sandbox; no production authorization or business credentials were involved. Browser screenshots and traces are temporary artifacts under `tmp/browser-tests/` and are not evidence of real model inference.

Raw live evidence is generated locally under `output/` and is deliberately not tracked in Git. This document is the public verification summary. The one-page submission document is `docs/write-up.pdf`, with editable source in `docs/write-up.md`. Earlier real-provider browser screenshots remain local; the seven browser regression tests were rerun after the latest backend changes. Advisory findings remain for intentionally unconfigured question timeouts and simulated actions; there are no blocking findings in the accepted flows.

The final recording, candidate human review, public hosting, and submission to a recruiter have not been performed.

## Validation regressions

- Malformed IPv6 syntax and invalid/out-of-range API ports previously raised exceptions or passed validation. They now produce `invalid_api_url` findings and remain inspectable; the generation endpoint returns a structured invalid-flow record instead of HTTP 500.
- Reusing an API result or question variable previously retained stale field availability. The validator now removes the old root and field facts before defining a replacement. The interpreter clears the previous value when a new collection/lookup begins, including timeout and error paths. Tests cover a failed second lookup and a repeated question timeout.
- Prompt-only instructions previously allowed model-added timing. The backend now checks explicit wait versus no-reply timing evidence separately, and requires team names/URLs to appear in the input. Ungrounded rules block simulation. The live suite additionally checks missing-URL and vague-timing clarification.
- Evidence matching is intentionally conservative: it supports common English duration quantities and numeric units, not arbitrary scheduling prose. It does not establish that every condition or branch faithfully captures the business intent; inspect the generated artifact and explanation before accepting it.

## Resize regression

Live browser inspection exposed an existing flow going off-canvas when resized from desktop to mobile. The minimised command `npm run test:e2e -- --grep recenters` reproduced the failure with fixed local provider data, without paid calls. Instrumentation confirmed container dimensions updated, but `useNodesInitialized()` stayed false for this read-only controlled graph, preventing its resize effect. The fix uses the explicitly known node bounds and direct `fitBounds()` viewport updates, avoiding measured-node state and queued node mutations. The same regression passed after the change, then all seven browser tests and the original real-provider browser scenario passed. Temporary debug logs were removed.
