# Demo recording script

Target: **4 minutes 30 seconds to 4 minutes 50 seconds**. English narration, with actions alongside speech. Aim for about 120–130 words per minute. Do not read the long prompts aloud.

For Chinese operating notes and the same English narration, use [the recording companion](demo-script.zh-CN.md).

## Recording setup

1. Launch the normal application with `backend.main:app` and open `http://127.0.0.1:8000/`. Never use the browser-test server for the recording.
2. Use a desktop viewport, ideally 1440 pixels wide or more. Keep the three-column workspace visible, close unrelated tabs, and enable Do Not Disturb.
3. Prepare a second tab or editor window with `docs/verification.md`, positioned at the results table. Do not open `.env` or terminals containing credentials.
4. Rehearse the three examples. Check generated teams, links, conditions, and timing against each prompt. Start a fresh page for the take.
5. Real generation varies: node names, layout, wording, and node counts can change. Describe node roles rather than exact positions or counts.
6. The review identified remaining edge cases: unrequested model-added timing, malformed URLs, and overwritten API variables. Do not claim they are solved or that structural validation proves arbitrary business correctness. Inspect the actual output before accepting it.

## Timeline

| Time | Actions | Main point |
| --- | --- | --- |
| 0:00–0:20 | Introduce the three panels | Describe → inspect → try |
| 0:20–1:25 | Qualification: generate, inspect, run both answers | Concrete artifact, explanation, branching |
| 1:25–2:25 | Follow-up: yes and no-reply paths | Virtual wait versus question timeout |
| 2:25–3:35 | Order API: success, failure, trace | Explicit error handling and simulation boundary |
| 3:35–4:20 | Verification record and architecture | Backend responsibilities, evidence, trade-offs |
| 4:20–4:40 | Return to the workspace and close | User value and next priority |

These are rehearsal targets. Talk during generation; pause briefly on results so the viewer can follow.

## 1. Opening — 0:00–0:20

**Do**

- Start on a fresh workspace.
- Move the pointer slowly from the intent panel to the flow panel, then to the conversation panel.
- Do not generate yet.

**Say**

> Hi, let me show you the Automation Builder Copilot. The idea is simple: describe the conversation you want, get a flow you can inspect, and try it before anything goes live. I’ll walk through three examples: routing a contact, following up, and handling an API failure.

## 2. Qualification — 0:20–1:25

### Generate — approximately 0:20–0:35

**Do**

1. Click **Qualify & route**.
2. Pause on the prompt so the viewer sees the buyer/seller requirement and supplied URL.
3. Click **Generate flow**.

**Say while generation runs**

> First, I want to ask whether a new contact is a buyer or a seller. Buyers should go to Sales, and sellers should get this help article. This button makes a real DeepSeek request.

### Inspect — approximately 0:35–0:55

**Do**

1. Point to the question and condition nodes. Click the condition to show its details.
2. Close node details with **×**, restoring the plain-English explanation.
3. Click **Review** and point to the actual findings.
4. Click **JSON**, pause for two seconds, then return to **Flow**. If time permits, use the download icon at the top right to export JSON.

**Say**

> Here’s the question, and here’s the decision that splits the conversation. The explanation underneath describes those paths. Review separates blocking issues from advisory findings. And JSON shows the actual structured flow that the simulator uses.

Optional, only if the missing-timeout advisory is visible:

> This question has no timeout, so it keeps waiting for a reply.

If there are no findings, use this instead:

> This run has no findings from the checks we currently support.

Do not say “no risk” or describe a warning that is not on screen.

### Run both branches — approximately 0:55–1:25

**Do**

1. Click **Start simulation**, then the **buyer** choice.
2. Point to the simulated Sales assignment and highlighted route.
3. Click **Restart simulation**, then **seller**.
4. Point to `https://example.com/help` and the changed route.

**Say**

> Let’s try buyer. The conversation goes to Sales, and the graph highlights the path it took. Now I’ll restart and choose seller. This time, I get the help link instead. The assignment is simulated, so nobody is actually contacted.

## 3. Timing and no reply — 1:25–2:25

### Generate — approximately 1:25–1:40

**Do**

1. Click **Follow up gently**.
2. Click **Regenerate flow** or **Generate flow**, whichever is shown.
3. Point to “30 minutes” and “within 1 hour” in the prompt.

**Say**

> Next, let’s add timing. If the contact wants a demo, send a reminder after thirty minutes. If they don’t reply within an hour, send a gentle follow-up instead.

### Compare paths — approximately 1:40–2:25

**Do**

1. Point to the wait node and the question’s timeout branch. Click a node if needed to show its configured seconds.
2. Click **Start simulation**, then **yes**. Point to the virtual clock at **+30m**.
3. Click **Restart simulation**.
4. Click **Simulate no reply for 1h**.
5. Point to **+1h** and the follow-up message. Open **Execution trace** if time permits.

**Say**

> There are two different things to test here. If I answer yes, the flow waits thirty minutes and sends the reminder. That’s virtual time, so we can test it immediately.
>
> Now I’ll restart and simulate no reply. We take the timeout branch, advance one hour, and send the follow-up. We don’t store an answer that never arrived. The trace lets me check which steps actually ran.

The no path is covered by acceptance checks. It does not need a third restart in this short recording.

## 4. API success and failure — 2:25–3:35

### Generate — approximately 2:25–2:40

**Do**

1. Click **Handle API failures** and generate the flow.
2. Point to the supplied API URL and requested error handling in the prompt.

**Say**

> Finally, let’s look up an order. This example asks for an order ID, checks an API, and either returns the status or hands the conversation to Support.

### Run success — approximately 2:40–3:00

**Do**

1. Confirm **Business API outcome → Success**.
2. Click **Start simulation**.
3. Enter `A123` in **Your reply**, then click Send or press Enter.
4. Point to the reply containing **in transit**.

**Say**

> I’ll enter A123. On success, the bot fills the saved message with the returned status: in transit. DeepSeek generated the flow, but the business API here uses clearly labelled test data. We’re not calling a real order system.

### Run failure — approximately 3:00–3:35

**Do**

1. Change **Business API outcome** to **Failure**.
2. Click **Restart simulation**. Changing the dropdown alone does not rerun the current conversation.
3. Enter `A123` again.
4. Point to the apology and simulated Support assignment.
5. Open **Execution trace**, then expand **Collected variables**. The successful API response variable should be absent; its exact name may vary.

**Say**

> Now I’ll switch to failure and restart. Instead of giving a delivery status, the bot apologizes and routes the conversation to Support. In the trace, we can see the error path. And there’s no successful API result stored for this run, so this branch can’t use a status it never received.

## 5. Engineering and scope — 3:35–4:20

**Do**

1. Switch to the prepared `docs/verification.md` tab or editor window.
2. Point to **40 backend tests**, **7 browser tests**, and the **real DeepSeek acceptance** rows. Show recorded results; do not spend the recording rerunning tests.
3. Return to the app before closing.

**Say**

> Under the hood, the Python backend owns validation and execution. DeepSeek produces the flow and explanation; it doesn’t decide each step while the simulation is running. That keeps a given flow reproducible.
>
> I used Codex to help clarify the scope, build the prototype, and design regression tests. The evidence here includes forty backend tests, seven browser tests, and seven paths through real DeepSeek-generated flows. It’s a useful starting point, but still a small evaluation set.
>
> I kept storage in memory and graph wiring read-only to keep the scope manageable.

## 6. Closing — 4:20–4:40

**Do**

- Finish on the app with the graph and API-failure conversation visible. Switch from trace back to **Conversation** if needed.
- Stop moving the pointer for the last sentence. Leave two seconds before ending the recording.

**Say**

> So that’s the loop: describe it, inspect it, and try the conversation. My next priority would be checking that generated business rules match the original request, then expanding the evaluation set. Thanks for watching.

## Short recovery lines

Use these only when relevant, replacing nearby narration rather than adding every line to the main take.

| Situation | Action | Natural line |
| --- | --- | --- |
| Generation takes longer | Leave the loading state visible; wait for the result. | “While that’s generating, the key thing is that the output is a structured flow we can inspect and test.” |
| A clarification appears | Add the missing detail to the original prompt and generate again. | “It needs one more detail here. I’ll add the actual URL rather than have it guess.” |
| An unrequested rule appears | Point it out and amend the prompt explicitly; retake if necessary. | “I didn’t ask for that timeout, so I’d change this before accepting the flow.” |
| An advisory appears | Explain the actual finding. | “This is an advisory. It’s calling out a behavior I should review, rather than stopping the simulation.” |
| A blocking issue appears | Keep it visible; correct the intent or retake. Do not bypass validation. | “This flow needs attention before it can run. I’ll correct that and generate it again.” |
| An answer is outside the choices | Show the feedback, then choose a valid option. | “That reply isn’t one of the allowed options, so the question stays open. I’ll choose buyer.” |
| The provider returns an error | Show it and retry once if appropriate; stop and retake if persistent. | “The provider request failed, and the app is showing that instead of returning a pretend flow.” |
| Node names or layout differ | Refer to the node’s role. | “This is the decision step that chooses between the two paths.” |

If the take exceeds five minutes, remove JSON download, the optional timing trace, and the extra warning sentence first. Keep all three prompts, validation, explanation, and simulation. Do not describe an older flow as a new live result.

## Prompt reference — paste, do not read aloud

The three example buttons already populate these prompts.

**Qualification**

> When a new contact messages us, ask whether they are a buyer or seller, with buyer and seller as the allowed answers. Route buyers to the Sales team. Send sellers our help article at https://example.com/help. Then end the conversation.

**Timing**

> When a new contact messages us, ask if they would like a product demo, with yes and no as the allowed answers. If yes, wait 30 minutes, then send a friendly demo reminder. If no, send a polite thank-you. If they do not answer within 1 hour, send a gentle follow-up and end. End after each path.

**API failure**

> When a contact asks about an order, ask for their order ID as free text. Query GET https://example.com/orders/{order_id}. For the simulated success response, use status="in transit" and tell the customer the status. If the API fails, apologize and assign the conversation to the Support team. Then end.

## Final pre-recording check

- [ ] Actual generated teams, URLs, conditions, and timing match the prompt; the explanation matches JSON.
- [ ] Buyer/seller, yes/no/timeout, and API success/failure paths have been rehearsed.
- [ ] Supported checks show no blocking findings for the demonstrated flows; advisories are understood.
- [ ] The normal app uses the intended DeepSeek configuration; no credentials or customer data are visible.
- [ ] Generation is a real model call; business actions are clearly labelled simulations.
- [ ] First-person claims about personal review reflect work the speaker actually performed.
- [ ] One timed rehearsal fits within 3–5 minutes, including clicks and model wait time.
- [ ] Review the final video and audio before submitting repository and recording links.
