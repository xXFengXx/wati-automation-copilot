# Demo 录制对照稿：中文操作 + 英文口播

建议成片 **4 分 30 秒到 4 分 50 秒**。正文英文口播约 **487 词**；以每分钟 120–130 词的自然语速讲，加上点击和必要停顿，目标落在作业要求的 3–5 分钟内。最终时长以你的一次实际彩排为准。

这份是录制时看的对照稿；[英文提交版](demo-script.md)还包含完整提示词、应急处理和录前检查。

## 录制前准备

- 打开正式应用 `http://127.0.0.1:8000/`，使用真实 DeepSeek 配置；不要启动测试替身服务。
- 桌面窗口建议宽 1440 像素以上，让三栏同时可见；关闭通知和无关页面。
- 提前打开 `docs/verification.md`，定位到结果表，方便后半段切过去展示。
- 先彩排三个例子，核对实际生成的团队、URL、条件和时间。模型可能改变节点名字、文案和布局，不必追求与截图一模一样。
- 最近检查发现的边界问题仍需优化：模型自行添加业务规则、异常 URL、变量覆盖校验。录制时不要声称它们已经修好，也不要把“通过结构校验”说成“所有业务规则都正确”。
- 不展示 `.env` 或包含密钥的终端。不要逐字朗读长提示词，直接使用三个示例按钮即可。

## 怎么使用这份稿子

“操作”告诉你屏幕上做什么；“英文口播”是可以直接讲的话；“节奏提示”不需要念出来。操作和口播尽量同步进行，不是先把按钮全点完，再补讲解。

## 1. 开场｜0:00–0:20

**操作**

打开一个干净的工作区。鼠标依次指向左侧意图输入、中间流程图、右侧对话模拟，先不要点击生成。

**英文口播**

> Hi, let me show you the Automation Builder Copilot. The idea is simple: describe the conversation you want, get a flow you can inspect, and try it before anything goes live. I’ll walk through three examples: routing a contact, following up, and handling an API failure.

**节奏提示**

像给同事介绍自己做的东西，语气轻松。说到三个例子时稍作停顿，不用照着界面标题逐字念。

## 2. 买家／卖家分流：生成｜0:20–0:35

**操作**

点击左侧 **Qualify & route**，停一秒让观众看清描述，再点击 **Generate flow**。生成期间讲下面这段，不要把整段提示词读出来。

**英文口播**

> First, I want to ask whether a new contact is a buyer or a seller. Buyers should go to Sales, and sellers should get this help article. This button makes a real DeepSeek request.

**节奏提示**

  说到 Sales 和 help article 时，可以指一下输入里的对应要求。生成结束后先让画面稳定，再进入讲解。

## 3. 检查流程、解释与 JSON｜0:35–0:55

**操作**

指向提问节点和条件节点，点击条件节点展示详情，然后点详情栏右侧的关闭图标，恢复自然语言解释。切到 **Review**，再切到 **JSON** 停约两秒，最后回到 **Flow**。时间充足才点右上角下载图标。

**英文口播**

> Here’s the question, and here’s the decision that splits the conversation. The explanation underneath describes those paths. Review separates blocking issues from advisory findings. And JSON shows the actual structured flow that the simulator uses.

**节奏提示**

不要逐条朗读 JSON。让观众知道它是可执行的结构化产物，并且与模拟器使用的是同一份流程。Review 中有什么就讲什么，不要说“没有任何风险”。

## 4. 分别跑买家和卖家｜0:55–1:25

**操作**

点击 **Start simulation**，选择 **buyer**，指向 Sales 分配记录和高亮路径。再点 **Restart simulation**，选择 **seller**，展示帮助链接和路径变化。

**英文口播**

> Let’s try buyer. The conversation goes to Sales, and the graph highlights the path it took. Now I’ll restart and choose seller. This time, I get the help link instead. The assignment is simulated, so nobody is actually contacted.

**节奏提示**

每次点击答案后留半秒给观众看结果。这里强调的是两次选择确实进入不同分支，不需要把机器人回复再念一遍。

## 5. 加入等待与超时：生成｜1:25–1:40

**操作**

点击 **Follow up gently**，再点击当前显示的 **Regenerate flow** 或 **Generate flow**。指一下提示词里的 30 minutes 和 within 1 hour。

**英文口播**

> Next, let’s add timing. If the contact wants a demo, send a reminder after thirty minutes. If they don’t reply within an hour, send a gentle follow-up instead.

**节奏提示**

把 thirty minutes 和 one hour 说清楚。这两个时间分别属于“回答 yes 后等待”和“没有回答时超时”，不是同一个逻辑。

## 6. 对比回答 yes 和不回复｜1:40–2:25

**操作**

指出等待节点与问题的 timeout 分支。点击 **Start simulation → yes**，展示虚拟时钟 **+30m**。然后 **Restart simulation → Simulate no reply for 1h**，展示 **+1h** 和跟进消息。时间够再打开 **Execution trace**。

**英文口播**

> There are two different things to test here. If I answer yes, the flow waits thirty minutes and sends the reminder. That’s virtual time, so we can test it immediately.
>
> Now I’ll restart and simulate no reply. We take the timeout branch, advance one hour, and send the follow-up. We don’t store an answer that never arrived. The trace lets me check which steps actually ran.

**节奏提示**

说完第一段时展示 +30m，再重启并讲第二段。这里不必再现场跑 no 分支，它已包含在验收记录中。不要真的等待 30 分钟。

## 7. 查询订单：生成｜2:25–2:40

**操作**

点击 **Handle API failures** 并生成流程。指一下输入中明确给出的 API 地址，以及失败时转 Support 的要求。

**英文口播**

> Finally, let’s look up an order. This example asks for an order ID, checks an API, and either returns the status or hands the conversation to Support.

**节奏提示**

不要把 example.com 说成已接入的真实订单服务。DeepSeek 生成是真实调用，订单 API 是明确标识的模拟动作。

## 8. API 成功路径｜2:40–3:00

**操作**

确认右侧 **Business API outcome** 为 **Success**。点击 **Start simulation**，在 **Your reply** 输入 `A123` 并发送。指向回复中的 **in transit**。

**英文口播**

> I’ll enter A123. On success, the bot fills the saved message with the returned status: in transit. DeepSeek generated the flow, but the business API here uses clearly labelled test data. We’re not calling a real order system.

**节奏提示**

A123 可以读作 “A one two three”。讲清楚返回状态由保存的消息模板填入，而不是每一轮都重新调用模型写回复。

## 9. API 失败路径与执行记录｜3:00–3:35

**操作**

把 **Business API outcome** 改为 **Failure**，然后点击 **Restart simulation**，再次输入 `A123`。展示道歉和 Support 分配。切到 **Execution trace**，展开 **Collected variables**，指出这次没有保存 API 成功结果；变量名以实际生成内容为准。

**英文口播**

> Now I’ll switch to failure and restart. Instead of giving a delivery status, the bot apologizes and routes the conversation to Support. In the trace, we can see the error path. And there’s no successful API result stored for this run, so this branch can’t use a status it never received.

**节奏提示**

一定要改下拉框后再重启，单独切换下拉框不会重跑当前对话。先指着失败结果讲前两句，再打开 trace 和变量讲后半段。

## 10. 架构、AI 使用和验证｜3:35–4:20

**操作**

切到提前准备好的 `docs/verification.md`，指出 40 项后端测试、7 项浏览器测试，以及真实 DeepSeek 验收的记录。不在录屏里重新跑完整测试。说到最后一句前，切回应用。

**英文口播**

> Under the hood, the Python backend owns validation and execution. DeepSeek produces the flow and explanation; it doesn’t decide each step while the simulation is running. That keeps a given flow reproducible.
>
> I used Codex to help clarify the scope, build the prototype, and design regression tests. The evidence here includes forty backend tests, seven browser tests, and seven paths through real DeepSeek-generated flows. It’s a useful starting point, but still a small evaluation set.
>
> I kept storage in memory and graph wiring read-only to keep the scope manageable.

**节奏提示**

不用逐个念框架名，也不要说测试已经证明所有输入都可靠。这里重点是：模型生成产物，Python 负责校验和执行；AI 的使用有明确目的和验证证据。

## 11. 收尾｜4:20–4:40

**操作**

回到应用；如果仍在 trace 页签，切回 **Conversation**，保留流程图和失败转交 Support 的对话。最后一句停止移动鼠标，结束后留两秒再停录。

**英文口播**

> So that’s the loop: describe it, inspect it, and try the conversation. My next priority would be checking that generated business rules match the original request, then expanding the evaluation set. Thanks for watching.

**节奏提示**

收尾说下一步优先改进业务规则一致性和评估集，与当前已知优化项保持一致。不要临时承诺完整编辑器或生产执行。

## 现场出现不同结果时怎么接话

下面是备用话术，不需要全部加进主稿；否则容易超过五分钟。

| 情况 | 操作与处理 | 可以直接说的英文 |
| --- | --- | --- |
| 生成比彩排慢 | 保留加载画面，讲完一句就等，不要反复点击生成。 | “While that’s generating, the key thing is that the output is a structured flow we can inspect and test.” |
| 缺少资料，出现澄清问题 | 把缺少的资料补回原输入，再生成。 | “It needs one more detail here. I’ll add the actual URL rather than have it guess.” |
| 生成了没要求的超时规则 | 指出差异，明确补充不需要超时；无法在时限内解决就修正后重录。 | “I didn’t ask for that timeout, so I’d change this before accepting the flow.” |
| Review 有普通提醒 | 按实际内容解释，不要把它说成运行失败。 | “This is an advisory. It’s calling out a behavior I should review, rather than stopping the simulation.” |
| Review 有阻断错误 | 展示错误、修正描述再生成；不要跳过校验。 | “This flow needs attention before it can run. I’ll correct that and generate it again.” |
| 输入不在允许选项内 | 展示反馈，再点一个有效选项。 | “That reply isn’t one of the allowed options, so the question stays open. I’ll choose buyer.” |
| 模型服务报错 | 展示错误，必要时重试一次；持续失败就恢复后重录。 | “The provider request failed, and the app is showing that instead of returning a pretend flow.” |
| 节点位置或名称与彩排不同 | 讲节点的作用，不说“左边第三个节点”之类固定位置。 | “This is the decision step that chooses between the two paths.” |

如果第一段真的出现“没有配置问题超时”的提醒，可以补一句：

> This question has no timeout, so it keeps waiting for a reply.

如果没有任何 finding，可以改说：

> This run has no findings from the checks we currently support.

不要在没有对应画面时念这两句。

## 让口播更自然的几个细节

- 用讲解给同事听的语气，别按标点机械停顿。**Let’s try… / Now I’ll… / Here’s…** 都是自然的转场。
- 点完 buyer、seller 或发送订单号后，稍停一下，让观众看见结果再继续。
- 不要重复朗读屏幕上的机器人回复；指出它证明了哪个分支或行为就够了。
- **API、JSON、LLM** 按字母读即可；**A123** 读作 “A one two three”。
- 除了必须展示的行为，其他节点文案可用自己的话解释；不要硬背节点数量和位置。
- 如果超时，先删 JSON 下载、等待场景的可选 trace 展示和额外警告解释；保留三个例子、校验、解释和模拟。
- 关于个人审阅的第一人称表述，只讲自己实际做过的工作。测试结果按验证记录讲，不扩大成“已经没有 bug”。

## 开录前最后确认

- [ ] 三个实际生成流程的业务规则均已检查，解释与 JSON 一致。
- [ ] 已试过 buyer/seller、yes/no/timeout、API success/failure。
- [ ] 已理解提醒，没有跳过阻断错误。
- [ ] 录制画面不含密钥、真实客户资料或无关通知。
- [ ] 能清楚区分真实 AI 生成与模拟业务动作。
- [ ] 已完整计时彩排一次，连同操作和等待不超过五分钟。
- [ ] 成片检查过声音、画面、鼠标指向和页面切换。
