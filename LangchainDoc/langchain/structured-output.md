# 结构化输出

结构化输出允许 **智能体（agents）** 以特定的、可预测的格式返回数据。这样，您无需解析自然语言响应，即可获得 **JSON 对象**、**Pydantic 模型** 或 **数据类（dataclasses）** 形式的结构化数据，供您的应用程序直接使用。

LangChain 的 [`create_agent`](https://langchain-doc.cn/v1/python/langchain/[https:/reference.langchain.com/python/langchain/agents/#langchain.agents.create_agent](https://reference.langchain.com/python/langchain/agents/#langchain.agents.create_agent)) 会自动处理结构化输出。用户设置所需的结构化输出 **模式（schema）**，当模型生成结构化数据时，它会被捕获、验证，并作为智能体状态中 `'structured_response'` 键的值返回。

```python
def create_agent(
    ...
    response_format: Union[
        ToolStrategy[StructuredResponseT],
        ProviderStrategy[StructuredResponseT],
        type[StructuredResponseT],
    ]
```

## 响应格式 (Response Format)

该参数控制智能体如何返回结构化数据：

- **`ToolStrategy[StructuredResponseT]`**: 使用 **工具调用（tool calling）** 实现结构化输出。
- **`ProviderStrategy[StructuredResponseT]`**: 使用 **提供商原生（provider-native）** 的结构化输出功能。
- **`type[StructuredResponseT]`**: **模式类型（Schema type）** - 会根据模型功能自动选择最佳策略。
- **`None`**: 不进行结构化输出。

当直接提供模式类型时，LangChain 会自动选择：

- **`ProviderStrategy`**: 适用于支持原生结构化输出的模型（例如 [OpenAI](../integrations/providers/openai.html)、[Grok](https://langchain-doc.cn/v1/python/integrations/providers/xai)）。
- **`ToolStrategy`**: 适用于所有其他模型。

结构化响应将在智能体最终状态的 **`structured_response`** 键中返回。

## 提供商策略 (Provider strategy)

一些模型提供商通过其 **API** 原生支持结构化输出（目前仅限 OpenAI 和 Grok）。在可用时，这是最可靠的方法。

要使用此策略，请配置 `ProviderStrategy`：

```python
class ProviderStrategy(Generic[SchemaT]):
    schema: type[SchemaT]
```

> **`schema`** (必需)
>
> 定义结构化输出格式的模式。支持：
>
> - **Pydantic 模型**: 带有字段验证的 `BaseModel` 子类。
> - **数据类 (Dataclasses)**: 带有类型注解的 Python 数据类。
> - **TypedDict**: 类型化字典类。
> - **JSON Schema**: 带有 JSON 模式规范的字典。

当您将模式类型直接传递给 [`create_agent.response_format`](https://langchain-doc.cn/v1/python/langchain/[https:/reference.langchain.com/python/langchain/agents/#langchain.agents.create_agent](https://reference.langchain.com/python/langchain/agents/#langchain.agents.create_agent)(response_format)) 并且模型支持原生结构化输出时，LangChain 会自动使用 `ProviderStrategy`：

```python
# Pydantic Model 示例
from pydantic import BaseModel, Field
from langchain.agents import create_agent
class ContactInfo(BaseModel):
    """一个人的联系信息。"""
    name: str = Field(description="该人的姓名")
    email: str = Field(description="该人的电子邮件地址")
    phone: str = Field(description="该人的电话号码")
agent = create_agent(
    model="openai:gpt-5",
    tools=tools,
    response_format=ContactInfo  # 自动选择 ProviderStrategy
)
result = agent.invoke({
    "messages": [{"role": "user", "content": "Extract contact info from: John Doe, john@example.com, (555) 123-4567"}]
})
result["structured_response"]
# ContactInfo(name='John Doe', email='john@example.com', phone='(555) 123-4567')
```

```python
# Dataclass 示例
from dataclasses import dataclass
from langchain.agents import create_agent
@dataclass
class ContactInfo:
    """一个人的联系信息。"""
    name: str # 该人的姓名
    email: str # 该人的电子邮件地址
    phone: str # 该人的电话号码
agent = create_agent(
    model="openai:gpt-5",
    tools=tools,
    response_format=ContactInfo  # 自动选择 ProviderStrategy
)
result = agent.invoke({
    "messages": [{"role": "user", "content": "Extract contact info from: John Doe, john@example.com, (555) 123-4567"}]
})
result["structured_response"]
# ContactInfo(name='John Doe', email='john@example.com', phone='(555) 123-4567')
```

```python
# TypedDict 示例
from typing_extensions import TypedDict
from langchain.agents import create_agent
class ContactInfo(TypedDict):
    """一个人的联系信息。"""
    name: str # 该人的姓名
    email: str # 该人的电子邮件地址
    phone: str # 该人的电话号码
agent = create_agent(
    model="openai:gpt-5",
    tools=tools,
    response_format=ContactInfo  # 自动选择 ProviderStrategy
)
result = agent.invoke({
    "messages": [{"role": "user", "content": "Extract contact info from: John Doe, john@example.com, (555) 123-4567"}]
})
result["structured_response"]
# {'name': 'John Doe', 'email': 'john@example.com', 'phone': '(555) 123-4567'}
```

```python
# JSON Schema 示例
from langchain.agents import create_agent
contact_info_schema = {
    "type": "object",
    "description": "一个人的联系信息。",
    "properties": {
        "name": {"type": "string", "description": "该人的姓名"},
        "email": {"type": "string", "description": "该人的电子邮件地址"},
        "phone": {"type": "string", "description": "该人的电话号码"}
    },
    "required": ["name", "email", "phone"]
}
agent = create_agent(
    model="openai:gpt-5",
    tools=tools,
    response_format=contact_info_schema  # 自动选择 ProviderStrategy
)
result = agent.invoke({
    "messages": [{"role": "user", "content": "Extract contact info from: John Doe, john@example.com, (555) 123-4567"}]
})
result["structured_response"]
# {'name': 'John Doe', 'email': 'john@example.com', 'phone': '(555) 123-4567'}
```

提供商原生的结构化输出具有高可靠性和严格的验证，因为模型提供商会强制执行模式。请在可用时使用它。

> 💡 **请注意:** 如果提供商对您选择的模型原生支持结构化输出，那么编写 `response_format=ProductReview` 和 `response_format=ToolStrategy(ProductReview)` 在功能上是等效的。无论哪种情况，如果不支持结构化输出，智能体都将退回到工具调用策略。

## 工具调用策略 (Tool calling strategy)

对于不支持原生结构化输出的模型，LangChain 使用 **工具调用（tool calling）** 来达到相同的效果。这适用于所有支持工具调用的模型，即大多数现代模型。

要使用此策略，请配置 `ToolStrategy`：

```python
class ToolStrategy(Generic[SchemaT]):
    schema: type[SchemaT]
    tool_message_content: str | None
    handle_errors: Union[
        bool,
        str,
        type[Exception],
        tuple[type[Exception], ...],
        Callable[[Exception], str],
    ]
```

> **`schema`** (必需)
>
> 定义结构化输出格式的模式。支持：
>
> - **Pydantic 模型**: 带有字段验证的 `BaseModel` 子类。
> - **数据类 (Dataclasses)**: 带有类型注解的 Python 数据类。
> - **TypedDict**: 类型化字典类。
> - **JSON Schema**: 带有 JSON 模式规范的字典。
> - **联合类型 (Union types)**: 多个模式选项。模型将根据上下文选择最合适的模式。

> **`tool_message_content`** (可选)
>
> 生成结构化输出时，返回的工具消息的自定义内容。
> 如果未提供，默认为显示结构化响应数据的消息。

> **`handle_errors`** (可选)
>
> 结构化输出验证失败的错误处理策略。默认为 `True`。
>
> - **`True`**: 捕获所有错误并使用默认错误模板。
> - **`str`**: 捕获所有错误并使用此自定义消息。
> - **`type[Exception]`**: 仅捕获此异常类型并使用默认消息。
> - **`tuple[type[Exception], ...]`**: 仅捕获这些异常类型并使用默认消息。
> - **`Callable[[Exception], str]`**: 返回错误消息的自定义函数。
> - **`False`**: 不重试，让异常传播。

```python
# Pydantic Model 示例
from pydantic import BaseModel, Field
from typing import Literal
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
class ProductReview(BaseModel):
    """对产品评论的分析。"""
    rating: int | None = Field(description="产品的评分", ge=1, le=5)
    sentiment: Literal["positive", "negative"] = Field(description="评论的情感倾向")
    key_points: list[str] = Field(description="评论的要点。小写，每条 1-3 个词。")
agent = create_agent(
    model="openai:gpt-5",
    tools=tools,
    response_format=ToolStrategy(ProductReview)
)
result = agent.invoke({
    "messages": [{"role": "user", "content": "Analyze this review: 'Great product: 5 out of 5 stars. Fast shipping, but expensive'"}]
})
result["structured_response"]
# ProductReview(rating=5, sentiment='positive', key_points=['fast shipping', 'expensive'])
```

*(为简洁起见，省略了 Dataclass、TypedDict、JSON Schema 和 Union Types 的 ToolStrategy 示例，它们的结构与 Provider Strategy 类似。)*

### 自定义工具消息内容 (Custom tool message content)

`tool_message_content` 参数允许您自定义生成结构化输出时，对话历史中显示的消息：

```python
from pydantic import BaseModel, Field
from typing import Literal
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
class MeetingAction(BaseModel):
    """从会议记录中提取的行动事项。"""
    task: str = Field(description="需要完成的具体任务")
    assignee: str = Field(description="负责该任务的人员")
    priority: Literal["low", "medium", "high"] = Field(description="优先级")
agent = create_agent(
    model="openai:gpt-5",
    tools=[],
    response_format=ToolStrategy(
        schema=MeetingAction,
        tool_message_content="行动事项已捕获并添加到会议记录中！"
    )
)
agent.invoke({
    "messages": [{"role": "user", "content": "From our meeting: Sarah needs to update the project timeline as soon as possible"}]
})
```

在上述示例中，最终的工具消息将是：

```
================================= Tool Message =================================
Name: MeetingAction
Action item captured and added to meeting notes!
```

如果没有 `tool_message_content`，最终的 [`ToolMessage`](https://langchain-doc.cn/v1/python/langchain/[https:/reference.langchain.com/python/langchain/messages/#langchain.messages.ToolMessage](https://reference.langchain.com/python/langchain/messages/#langchain.messages.ToolMessage)) 将是：

```
================================= Tool Message =================================
Name: MeetingAction
Returning structured response: {'task': 'update the project timeline', 'assignee': 'Sarah', 'priority': 'high'}
```

### 错误处理 (Error handling)

模型在通过工具调用生成结构化输出时可能会出错。LangChain 提供了智能的重试机制来自动处理这些错误。

#### 多个结构化输出错误 (Multiple structured outputs error)

当模型错误地调用了多个结构化输出工具时，智能体会通过 [`ToolMessage`](https://langchain-doc.cn/v1/python/langchain/[https:/reference.langchain.com/python/langchain/messages/#langchain.messages.ToolMessage](https://reference.langchain.com/python/langchain/messages/#langchain.messages.ToolMessage)) 提供错误反馈，并提示模型重试：

```
...
================================== Ai Message ==================================
Tool Calls:
  ContactInfo (call_1)
  Call ID: call_1
  Args:
    name: John Doe
    email: john@email.com
  EventDetails (call_2)
  Call ID: call_2
  Args:
    event_name: Tech Conference
    date: March 15th
================================= Tool Message =================================
Name: ContactInfo
Error: Model incorrectly returned multiple structured responses (ContactInfo, EventDetails) when only one is expected.
  Please fix your mistakes.
...
```

#### 模式验证错误 (Schema validation error)

当结构化输出与预期模式不匹配时，智能体会提供具体的错误反馈：

```
...
================================== Ai Message ==================================
Tool Calls:
  ProductRating (call_1)
  Call ID: call_1
  Args:
    rating: 10
    comment: Amazing product
================================= Tool Message =================================
Name: ProductRating
Error: Failed to parse structured output for tool 'ProductRating': 1 validation error for ProductRating.rating
  Input should be less than or equal to 5 [type=less_than_equal, input_value=10, input_type=int].
  Please fix your mistakes.
...
```

#### 错误处理策略 (Error handling strategies)

您可以使用 **`handle_errors`** 参数来自定义错误处理方式：

- **自定义错误消息**：
  ```python
  ToolStrategy(
      schema=ProductRating,
      handle_errors="请提供 1-5 之间的有效评分并包含评论。"
  )
  ```
  （如果 `handle_errors` 是一个字符串，智能体将始终使用固定的工具消息提示模型重试。）

- **仅处理特定异常**：
  ```python
  ToolStrategy(
      schema=ProductRating,
      handle_errors=ValueError  # 仅在 ValueError 时重试，否则抛出
  )
  ```

- **处理多个异常类型**：
  ```python
  ToolStrategy(
      schema=ProductRating,
      handle_errors=(ValueError, TypeError)  # 在 ValueError 和 TypeError 时重试
  )
  ```

- **自定义错误处理函数**：
  ```python
  def custom_error_handler(error: Exception) -> str:
      if isinstance(error, StructuredOutputValidationError):
          return "格式存在问题。请重试。"
      elif isinstance(error, MultipleStructuredOutputsError):
          return "返回了多个结构化输出。请选择最相关的一个。"
      else:
          return f"错误: {str(error)}"
  ToolStrategy(
      schema=ToolStrategy(Union[ContactInfo, EventDetails]),
      handle_errors=custom_error_handler
  )
  ```

- **不进行错误处理**：
  ```python
  response_format = ToolStrategy(
      schema=ProductRating,
      handle_errors=False  # 所有错误都抛出
  )