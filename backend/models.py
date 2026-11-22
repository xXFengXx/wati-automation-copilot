from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints


Identifier = Annotated[str, StringConstraints(pattern=r'^[A-Za-z_][A-Za-z0-9_]{0,63}$')]
VariableRef = Annotated[str, StringConstraints(pattern=r'^[A-Za-z_][A-Za-z0-9_]{0,63}(\.[A-Za-z_][A-Za-z0-9_]{0,63})?$')]
Text = Annotated[str, StringConstraints(min_length=1, max_length=2000)]
Scalar = str | int | float | bool | None


class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)


class NodeBase(StrictModel):
    id: Identifier
    label: Annotated[str, StringConstraints(min_length=1, max_length=100)]


class TriggerNode(NodeBase):
    type: Literal['trigger']
    event: Text


class MessageNode(NodeBase):
    type: Literal['send_message']
    message: Text


class QuestionNode(NodeBase):
    type: Literal['ask_question']
    question: Text
    variable: Identifier
    choices: list[Annotated[str, StringConstraints(min_length=1, max_length=100)]] = Field(default_factory=list, max_length=10)
    timeout_seconds: int | None = Field(default=None, ge=1, le=604800, strict=True)


class ConditionNode(NodeBase):
    type: Literal['condition']
    variable: VariableRef
    operator: Literal['eq', 'neq', 'contains', 'gt', 'lt', 'exists']
    value: Scalar = None


class ApiNode(NodeBase):
    type: Literal['api_call']
    url: Text
    method: Literal['GET', 'POST'] = 'GET'
    save_as: Identifier
    mock_response: dict[str, Scalar] = Field(default_factory=dict, max_length=20)


class AssignNode(NodeBase):
    type: Literal['assign_team']
    team: Text


class WaitNode(NodeBase):
    type: Literal['wait']
    duration_seconds: int = Field(ge=1, le=604800, strict=True)


class EndNode(NodeBase):
    type: Literal['end']


Node = Annotated[TriggerNode | MessageNode | QuestionNode | ConditionNode | ApiNode | AssignNode | WaitNode | EndNode, Field(discriminator='type')]


class Edge(StrictModel):
    source: Identifier
    target: Identifier
    handle: Literal['next', 'true', 'false', 'success', 'error', 'timeout'] = 'next'


class Flow(StrictModel):
    name: Annotated[str, StringConstraints(min_length=1, max_length=100)]
    description: Text
    nodes: list[Node] = Field(min_length=2, max_length=40)
    edges: list[Edge] = Field(min_length=1, max_length=80)


class Generation(StrictModel):
    flow: Flow | None
    explanation: Annotated[str, StringConstraints(max_length=6000)]
    clarification_questions: list[Text] = Field(default_factory=list, max_length=5)


class Finding(StrictModel):
    severity: Literal['error', 'warning']
    code: str
    message: str
    node_id: str | None = None
