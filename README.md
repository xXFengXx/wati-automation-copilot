# Wati Automation Builder Copilot

A local, interactive take-home prototype: describe an automation, generate a typed flow with **real DeepSeek inference**, inspect its graph and validation findings, then walk through a mock conversation.

Python / FastAPI / Pydantic backend; React / TypeScript / React Flow frontend. Flow generation and explanation use DeepSeek. Business API calls, team assignments, triggers, and waits are explicitly simulated. There is no offline generation fallback or native Wati import claim.

## Quick start (Windows PowerShell)

Requirements: Python 3.12+, Node.js 22.12+ (24 LTS recommended), npm, and a funded DeepSeek API account. Tested here with Python 3.14 and Node 26. Run commands from the repository root.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.lock.txt
Copy-Item .env.example .env
```

Edit `.env` locally and set `DEEPSEEK_API_KEY`. Do not commit it. The model is configurable; the default is `deepseek-flash`. Restart the backend after changing configuration.

```powershell
Set-Location frontend
npm ci
npm run build
Set-Location ..
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000). Interactive API docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs). The status badge reports whether a key is configured; the first generation request verifies credentials and connectivity. An absent/invalid key, insufficient balance, a provider timeout, and invalid model output each produce an explicit error.

For frontend development, run the backend command above with `--reload`; in another terminal run `npm run dev` from `frontend` and open the displayed local Vite URL. Vite proxies `/api` to port 8000.

macOS/Linux: use `.venv/bin/python` instead of `.venv\Scripts\python.exe`. Browser tests default to installed Microsoft Edge; set `PLAYWRIGHT_CHANNEL=chromium` and run `npx playwright install chromium` inside `frontend` when Edge is unavailable.

## Walkthrough

1. Choose one of the three example prompts, or write a complete English automation intent. Example business URLs use `example.com` and are explicitly supplied as simulation inputs.
2. Generate. If required business details are missing, add the requested information to the prompt and generate again. The application never invents a missing business URL on purpose; review generated content before use.
3. Inspect the graph; click nodes for details, review findings, read the explanation, or inspect/download JSON. Editing is through natural-language regeneration; graph wiring is read-only.
4. Start a simulation, choose or type answers, and watch the visited path. Restart to try a different branch. Choose business API failure **before restarting** to test the error route. A no-reply button advances a configured question timeout.
5. Inspect the execution trace, collected variables, and virtual clock. Nothing is sent to customers or external business systems.

## Architecture and contract

```text
React UI → FastAPI → DeepSeek JSON generation + explanation
                  → Pydantic schema → graph/data-flow validation
                  → immutable flow record → deterministic simulator
```

- `backend/models.py`: bounded, discriminated node types; flat API fixtures; no code execution.
- `backend/llm.py`: JSON-mode request; one bounded retry for malformed structured output, explicit provider errors. Structural/semantic validation findings remain visible rather than being silently rewritten. The explanation is AI-generated and should be checked against the flow.
- `backend/validation.py`: trigger/end rules, legal branch handles, dangling/duplicate nodes, reachability, end paths, cycle rejection, and branch-sensitive definite assignment. Timeout and API failure paths do not produce success variables. Warnings include simulated APIs, virtual waits, and missing response timeouts.
- `backend/simulation.py`: reproducible interpreter; supported nodes are trigger, send message, ask question, condition, API call, assign team, wait, end. Questions pause execution. Each answer carries a revision to reject stale/duplicate submissions. Text matching is case-insensitive; invalid numeric input follows the false branch. Question choices are enforced.
- `backend/main.py`: JSON HTTP API, request IDs and metadata-only logs, bounded in-memory stores (100 flows / 300 sessions), a lock for session transitions. Eviction or restart removes data; regenerating creates a new flow and resets the UI conversation. Cycles are rejected and execution also has an 80-step ceiling.

The trigger is descriptive and is activated by “Start simulation”; it does not listen for live Wati events. Each simulated API uses its generated test fixture on success or follows its error edge in failure mode. Virtual waits advance a counter. Assignments become trace entries.

Endpoints: `GET /api/health`, `POST /api/flows/generate`, `GET /api/flows/{id}`, `POST /api/simulations`, `POST /api/simulations/{id}/answers`. Use `/docs` for request/response exploration. Generated flows with blocking errors cannot start.

## Verification

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests -q
Set-Location frontend
npm run build
npm run test:e2e
```

Unit/API tests cover all three scenarios, exclusive branches, virtual timing, API errors, variable safety, session isolation, duplicate answers, clarification and provider errors/repair. Browser tests run the real API and interpreter with a **test-only provider stub** (`backend.tests.e2e_server`), covering graph inspection, JSON export, conversation branches, validation, failures, and mobile layout. They do not verify real DeepSeek connectivity. Never launch the test server for a demo. Production uses only `backend.main:app`.

After configuring the key and starting the normal backend, run `.\.venv\Scripts\python.exe scripts\verify_live.py`. It makes three real generation requests and exercises seven simulation paths; inspect generated business content and explanations manually afterward. It refuses to count the test-only provider as live verification.

Live acceptance has passed against DeepSeek `deepseek-flash`, including business-result checks. Evidence is in `output/live-acceptance.json`. The optional `npm run test:live-ui` command (from `frontend`) checks the normal app in Edge with **one real, billed inference request** and saves screenshots and a summary in `output/`. See [verification details](docs/verification.md) for the scope of each check.

The UI needs no database, login, or real Wati account. This local demo has no authentication or multi-tenant isolation; it should be bound to loopback. Adding public hosting requires an explicit authentication/rate-limit/persistence design. Do not enter customer data or secrets into prompts: intent text is sent to DeepSeek.

## Submission materials

- [One-page write-up](docs/write-up.md)
- [One-page PDF](output/pdf/automation-copilot-write-up.pdf)
- [Decision record](docs/adr/0001-validated-flows-and-deterministic-simulation.md), [glossary](GLOSSARY.md), and [agreed scope](docs/implementation-plan.md)
- Real-key acceptance has passed. The final screen recording and candidate human review remain submission steps; no recording or deployment is claimed by this repository.

## References

The [assignment's Wati node reference](https://support.wati.io/en/articles/11463029-guide-to-chatbot-nodes-in-wati) defines the node vocabulary; our JSON is an internal executable format. DeepSeek configuration follows the [official API](https://api-docs.deepseek.com/), [chat completion contract](https://api-docs.deepseek.com/api/create-chat-completion/), [JSON mode requirements](https://api-docs.deepseek.com/guides/json_mode/), and [error codes](https://api-docs.deepseek.com/quick_start/error_codes/), checked on 2026-11-22.
