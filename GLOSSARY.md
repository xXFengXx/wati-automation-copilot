# Automation Builder Copilot

帮助用户将自然语言描述的自动化意图转成可理解、可检查并可模拟的聊天机器人流程。

## Language

**Automation Intent（自动化意图）**:
用户描述的自动化目标，包含启动时机、条件、期望动作及时间要求。
_Avoid_: Prompt（仅指输入文本时使用）

**Flow（流程）**:
描述聊天机器人如何从启动条件出发，经过各个步骤与分支完成自动化目标的整体安排。
_Avoid_: Conversation（对话实例）

**Node（节点）**:
流程中的一个步骤，例如发送消息、提问、判断条件、调用 API、分配团队或等待。
_Avoid_: Agent（智能体）

**Transition（流转）**:
从一个节点进入后续节点的关系，可能由条件决定。
_Avoid_: Action（动作）

**Trigger（触发条件）**:
启动流程的事件或条件，例如新联系人发送消息。
_Avoid_: Condition（流程中的条件判断）

**Simulation（模拟执行）**:
在上线前通过虚拟输入体验流程行为的一次试运行。
_Avoid_: Live Execution（真实执行）

**Validation（流程校验）**:
对流程是否存在损坏、矛盾或无法继续的路径进行检查。
_Avoid_: Simulation（模拟执行）

**Risk Finding（风险提示）**:
指出流程中可能导致不期望结果的具体问题，供用户判断或修正。
_Avoid_: Validation Error（阻止有效执行的错误）
