# 运行时

## 概述 (Overview)

LangChain 的 **`create_agent`** 实际上是在 **LangGraph** 的运行时环境下运行的。

LangGraph 暴露了一个 **`Runtime`** 对象，其中包含以下信息：

1. **Context (上下文)**: 静态信息，例如用户 ID、数据库连接，或代理调用所需的其他依赖项。
2. **Store (存储)**: 一个 **`BaseStore`** 实例，用于**长期记忆**。
3. **Stream writer (流写入器)**: 一个用于通过 `"custom"` 流模式进行信息流式传输的对象。

你可以在**工具 (tools)** 和**中间件 (middleware)** 中访问运行时信息。

## 访问 (Access)

使用 **`create_agent`** 创建代理时，你可以指定一个 **`context_schema`** 来定义存储在代理 **`Runtime`** 中的 **`context`** 结构。

在调用代理时，通过传入 **`context`** 参数来提供运行的相关配置：

```python
from dataclasses import dataclass
from langchain.agents import create_agent

@dataclass
class Context:
    user_name: str

agent = create_agent(
    model="openai:gpt-5-nano",
    tools=[...],
    context_schema=Context  # [!code highlight]
)

agent.invoke(
    {"messages": [{"role": "user", "content": "What's my name?"}]},
    context=Context(user_name="John Smith")  # [!code highlight]
)
```

### 在工具内部 (Inside tools)

你可以在工具内部访问运行时信息，以实现：

- 访问上下文
- 读取或写入长期记忆
- 写入**自定义流**（例如，工具进度/更新）

使用 **`ToolRuntime`** 参数来访问工具内部的 **`Runtime`** 对象。

```python
from dataclasses import dataclass
from langchain.tools import tool, ToolRuntime  # [!code highlight]

@dataclass
class Context:
    user_id: str

@tool
def fetch_user_email_preferences(runtime: ToolRuntime[Context]) -> str:  # [!code highlight]
    """Fetch the user's email preferences from the store."""
    user_id = runtime.context.user_id  # [!code highlight]
    preferences: str = "The user prefers you to write a brief and polite email."
    if runtime.store:  # [!code highlight]
        if memory := runtime.store.get(("users",), user_id):  # [!code highlight]
            preferences = memory.value["preferences"]
    return preferences
```

### 在中间件内部 (Inside middleware)

你可以在中间件中访问运行时信息，以便根据用户上下文创建**动态提示**、**修改消息**或**控制代理行为**。

使用 **`request.runtime`** 来访问中间件装饰器内部的 **`Runtime`** 对象。运行时对象在传递给中间件函数的 **`ModelRequest`** 参数中可用。

```python
from dataclasses import dataclass
from langchain.messages import AnyMessage
from langchain.agents import create_agent, AgentState
from langchain.agents.middleware import dynamic_prompt, ModelRequest, before_model, after_model
from langgraph.runtime import Runtime

@dataclass
class Context:
    user_name: str

# Dynamic prompts
@dynamic_prompt
def dynamic_system_prompt(request: ModelRequest) -> str:
    user_name = request.runtime.context.user_name  # [!code highlight]
    system_prompt = f"You are a helpful assistant. Address the user as {user_name}."
    return system_prompt

# Before model hook
@before_model
def log_before_model(state: AgentState, runtime: Runtime[Context]) -> dict | None:  # [!code highlight]
    print(f"Processing request for user: {runtime.context.user_name}")  # [!code highlight]
    return None

# After model hook
@after_model
def log_after_model(state: AgentState, runtime: Runtime[Context]) -> dict | None:  # [!code highlight]
    print(f"Completed request for user: {runtime.context.user_name}")  # [!code highlight]
    return None

agent = create_agent(
    model="openai:gpt-5-nano",
    tools=[...],
    middleware=[dynamic_system_prompt, log_before_model, log_after_model],  # [!code highlight]
    context_schema=Context
)

agent.invoke(
    {"messages": [{"role": "user", "content": "What's my name?"}]},
    context=Context(user_name="John Smith")
)
```

> **注意**: [在 GitHub 上编辑此页面的源代码。](https://github.com/langchain-ai/docs/edit/main/src/v1/langchain/runtime.mdx)

> **提示**: [以编程方式连接这些文档](https://langchain-doc.cn/use-these-docs)到 Claude、VSCode 等，通过 MCP 获得实时答案。