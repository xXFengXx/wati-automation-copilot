# Verification record

Checked on 2026-11-22 (Asia/Shanghai).

| Check | Result | Boundary |
| --- | --- | --- |
| `python -m pytest backend/tests -q` | 40 passed | Unit/API tests; provider HTTP mocked, engine real. One upstream Starlette/httpx deprecation warning. |
| `npm run build` | Passed | TypeScript checked and production bundle generated. Vendor bundle size and compiler directive advisories remain non-blocking. |
| `npm run test:e2e` | 7 passed | Headless installed Edge; real API/validator/interpreter with test-only provider; includes resizing an existing desktop graph to mobile. |
| Desktop / mobile visual inspection | Passed | Graph, branches, node details, conversation, and narrow viewport inspected. Graph fit has an explicit visibility assertion. |
| One-page write-up PDF | 1 page; rendered and inspected | Text fits without clipping. |
| Normal app `/` | HTTP 200 | Production static frontend served by FastAPI on loopback. |
| Normal app generation without key | HTTP 503 `model_not_configured` | Explicit failure; no generated template fallback. |
| Real DeepSeek acceptance | Passed: 3 real generations / 7 simulation paths | DeepSeek `deepseek-flash`; explicit business-result assertions. Latest sample generation times: 3.888s / 4.632s / 4.235s, not a performance guarantee. |
| Real-provider browser smoke | Passed | Normal application, no test stubs: real generation, graph, buyer → Sales, execution trace, no JavaScript errors, desktop/mobile layout. |

Browser checks cover both qualification answers, JSON inspection/export, virtual wait and question timeout, API failure handoff, clarification, blocking validation, provider errors, mobile horizontal overflow, and graph inspection with a dangling connection.

The initial sandbox could not launch Edge. Tests passed after the same local-only suite ran outside the sandbox; no production authorization or business credentials were involved. Browser screenshots and traces are temporary artifacts under `tmp/browser-tests/` and are not evidence of real model inference.

Live evidence is saved in `output/live-acceptance.json` (generated flows, explanations, findings, traces, request IDs) and `output/live-ui-result.json`; real-provider screenshots are `output/live-ui-desktop.png` and `output/live-ui-mobile.png`. None contains the API key. Generated explanations were reviewed against the flow semantics; the prompt now explicitly distinguishes real build-time inference from deterministic simulation replies. Advisory findings remain for intentionally unconfigured question timeouts and simulated actions; there are no blocking findings in the accepted flows.

The final recording, candidate human review, public hosting, and submission to a recruiter have not been performed.

## Resize regression

Live browser inspection exposed an existing flow going off-canvas when resized from desktop to mobile. The minimised command `npm run test:e2e -- --grep recenters` reproduced the failure with fixed local provider data, without paid calls. Instrumentation confirmed container dimensions updated, but `useNodesInitialized()` stayed false for this read-only controlled graph, preventing its resize effect. The fix uses the explicitly known node bounds and direct `fitBounds()` viewport updates, avoiding measured-node state and queued node mutations. The same regression passed after the change, then all seven browser tests and the original real-provider browser scenario passed. Temporary debug logs were removed.
