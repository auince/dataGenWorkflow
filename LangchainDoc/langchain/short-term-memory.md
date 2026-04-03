# 短期记忆

## 概览 (Overview)

**记忆**是一个系统，用于记住关于先前交互的信息。对于 **AI 代理** (AI agents) 而言，记忆至关重要，因为它能让他们记住之前的交互、从反馈中学习并适应用户偏好。随着代理处理涉及大量用户交互的更复杂任务，这种能力对于**效率**和**用户满意度**都变得至关重要。

**短期记忆**让您的应用程序能够记住**单个线程**或**对话**中的先前交互。

> 💡 **注意：**
> 一个线程 (thread) 在一个会话 (session) 中组织多次交互，类似于电子邮件将消息分组到一个对话中的方式。

**会话历史记录** (Conversation history) 是短期记忆最常见的形式。对于当今的 **LLM** (大型语言模型) 来说，**长对话**是一个挑战；完整的历史记录可能无法完全容纳在一个 LLM 的**上下文窗口** (context window) 内，从而导致**上下文丢失** (context loss) 或**错误**。

即使您的模型支持完整的上下文长度，大多数 LLM 在处理**长上下文**时的表现仍然不佳。它们会被陈旧或跑题的内容“分心”，同时还会导致**响应时间变慢**和**成本更高**。

聊天模型使用 **消息** (messages) 接受上下文，这些消息包括**指令**（系统消息 system message）和**输入**（人类消息 human messages）。在聊天应用程序中，消息在人类输入和模型响应之间交替，导致消息列表随着时间推移而变长。由于上下文窗口是有限的，许多应用程序可以受益于使用技术来**移除**或**“遗忘”**陈旧信息。

## 用法 (Usage)

要向代理添加短期记忆（线程级持久性），您需要在创建代理时指定一个 **`checkpointer`**。

> ℹ️ **信息：**
> LangChain 的代理将短期记忆作为代理**状态** (state) 的一部分进行管理。
>
> 通过将这些存储在图 (graph) 的状态中，代理可以访问给定对话的完整上下文，同时保持不同线程之间的分离。
>
> 状态使用 **checkpointer** 持久化到数据库（或内存）中，以便线程可以随时恢复。
>
> 当代理被调用或一个步骤（如工具调用）完成时，短期记忆会更新，并在每个步骤开始时读取状态。

```python
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver  # [!code highlight]
agent = create_agent(
    "openai:gpt-5",
    [get_user_info],
    checkpointer=InMemorySaver(),  # [!code highlight]
)
agent.invoke(
    {"messages": [{"role": "user", "content": "Hi! My name is Bob."}]},
    {"configurable": {"thread_id": "1"}},  # [!code highlight]
)
```

#### 生产环境 (In production)

在生产环境中，请使用由**数据库**支持的 checkpointer：

```shell
pip install langgraph-checkpoint-postgres
```

```python
from langchain.agents import create_agent
from langgraph.checkpoint.postgres import PostgresSaver  # [!code highlight]
DB_URI = "postgresql://postgres:postgres@localhost:5442/postgres?sslmode=disable"
with PostgresSaver.from_conn_string(DB_URI) as checkpointer:
    checkpointer.setup() # auto create tables in PostgresSql
    agent = create_agent(
        "openai:gpt-5",
        [get_user_info],
        checkpointer=checkpointer,  # [!code highlight]
    )
```

## 自定义代理记忆 (Customizing agent memory)

默认情况下，代理使用 **`AgentState`** 来管理短期记忆，特别是通过 **`messages`** 键来管理会话历史记录。

您可以扩展 **`AgentState`** 以添加额外的字段。自定义状态模式通过 **`state_schema`** 参数传递给 **`create_agent`**。

```python
from langchain.agents import create_agent, AgentState
from langgraph.checkpoint.memory import InMemorySaver
class CustomAgentState(AgentState):  # [!code highlight]
    user_id: str  # [!code highlight]
    preferences: dict  # [!code highlight]
agent = create_agent(
    "openai:gpt-5",
    [get_user_info],
    state_schema=CustomAgentState,  # [!code highlight]
    checkpointer=InMemorySaver(),
)
# Custom state can be passed in invoke
result = agent.invoke(
    {
        "messages": [{"role": "user", "content": "Hello"}],
        "user_id": "user_123",  # [!code highlight]
        "preferences": {"theme": "dark"}  # [!code highlight]
    },
    {"configurable": {"thread_id": "1"}})
```

## 常见模式 (Common patterns)

启用**短期记忆**后，长对话可能会超出 LLM 的上下文窗口。常见的解决方案有：

| 模式 | 描述 |
| :--- | :--- |
| **修剪消息** (Trim messages) ✂️ | 移除最初或最后的 N 条消息（在调用 LLM 之前）。 |
| **删除消息** (Delete messages) 🗑️ | 从 LangGraph 状态中**永久**删除消息。 |
| **总结消息** (Summarize messages) 📝 | 总结历史记录中较早的消息，并用摘要替换它们。 |
| **自定义策略** (Custom strategies) ⚙️ | 自定义策略（例如：消息过滤等）。 |

这使得代理能够在不超出 LLM 上下文窗口的情况下跟踪对话。

#### 修剪消息 (Trim messages)

大多数 LLM 都有一个最大支持的上下文窗口（以 token 计）。

决定何时截断消息的一种方法是**计算消息历史记录中的 token 数**，并在接近该限制时进行截断。如果您使用 LangChain，可以使用**修剪消息实用程序** (trim messages utility) 并指定要从列表中保留的 token 数量，以及用于处理边界的 `strategy`（例如：保留最后的 `max_tokens`）。

要在代理中修剪消息历史记录，请使用 **`@before_model`** 中间件装饰器：

```python
from langchain.messages import RemoveMessage
from langgraph.graph.message import REMOVE_ALL_MESSAGES
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents import create_agent, AgentState
from langchain.agents.middleware import before_model
from langgraph.runtime import Runtime
from langchain_core.runnables import RunnableConfig
from typing import Any
@before_model
def trim_messages(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    """Keep only the last few messages to fit context window."""
    messages = state["messages"]
    if len(messages) <= 3:
        return None  # No changes needed
    first_msg = messages[0]
    recent_messages = messages[-3:] if len(messages) % 2 == 0 else messages[-4:]
    new_messages = [first_msg] + recent_messages
    return {
        "messages": [
            RemoveMessage(id=REMOVE_ALL_MESSAGES),
            *new_messages
        ]
    }
agent = create_agent(
    model,
    tools=tools,
    middleware=[trim_messages],
    checkpointer=InMemorySaver(),
)
config: RunnableConfig = {"configurable": {"thread_id": "1"}}
agent.invoke({"messages": "hi, my name is bob"}, config)
agent.invoke({"messages": "write a short poem about cats"}, config)
agent.invoke({"messages": "now do the same but for dogs"}, config)
final_response = agent.invoke({"messages": "what's my name?"}, config)
final_response["messages"][-1].pretty_print()
"""
================================== Ai Message ==================================
Your name is Bob. You told me that earlier.
If you'd like me to call you a nickname or use a different name, just say the word.
"""
```

#### 删除消息 (Delete messages)

您可以从图状态中删除消息以管理消息历史记录。

当您想要删除特定消息或清除整个消息历史记录时，这非常有用。

要从图状态中删除消息，可以使用 **`RemoveMessage`**。

要使 `RemoveMessage` 工作，您需要使用具有 **`add_messages`** [reducer] 的状态键。

默认的 **`AgentState`** 提供了此功能。

删除**特定**消息：

```python
from langchain.messages import RemoveMessage  # [!code highlight]
def delete_messages(state):
    messages = state["messages"]
    if len(messages) > 2:
        # remove the earliest two messages
        return {"messages": [RemoveMessage(id=m.id) for m in messages[:2]]}  # [!code highlight]
```

删除**所有**消息：

```python
from langgraph.graph.message import REMOVE_ALL_MESSAGES  # [!code highlight]
def delete_messages(state):
    return {"messages": [RemoveMessage(id=REMOVE_ALL_MESSAGES)]}  # [!code highlight]
```

> ⚠️ **警告：**
> 删除消息时，**请确保**生成的消息历史记录是**有效**的。请检查您正在使用的 LLM 提供商的限制。例如：
>
> *   一些提供商期望消息历史记录以 `user` 消息开始
> *   大多数提供商要求带有工具调用的 `assistant` 消息后跟相应的 `tool` 结果消息。

```python
from langchain.messages import RemoveMessage
from langchain.agents import create_agent, AgentState
from langchain.agents.middleware import after_model
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.runtime import Runtime
from langchain_core.runnables import RunnableConfig
@after_model
def delete_old_messages(state: AgentState, runtime: Runtime) -> dict | None:
    """Remove old messages to keep conversation manageable."""
    messages = state["messages"]
    if len(messages) > 2:
        # remove the earliest two messages
        return {"messages": [RemoveMessage(id=m.id) for m in messages[:2]]}
    return None
agent = create_agent(
    "openai:gpt-5-nano",
    tools=[],
    system_prompt="Please be concise and to the point.",
    middleware=[delete_old_messages],
    checkpointer=InMemorySaver(),
)
config: RunnableConfig = {"configurable": {"thread_id": "1"}}
for event in agent.stream(
    {"messages": [{"role": "user", "content": "hi! I'm bob"}]},
    config,
    stream_mode="values",
):
    print([(message.type, message.content) for message in event["messages"]])
for event in agent.stream(
    {"messages": [{"role": "user", "content": "what's my name?"}]},
    config,
    stream_mode="values",
):
    print([(message.type, message.content) for message in event["messages"]])
```

```
[('human', "hi! I'm bob")]
[('human', "hi! I'm bob"), ('ai', 'Hi Bob! Nice to meet you. How can I help you today? I can answer questions, brainstorm ideas, draft text, explain things, or help with code.')]
[('human', "hi! I'm bob"), ('ai', 'Hi Bob! Nice to meet you. How can I help you today? I can answer questions, brainstorm ideas, draft text, explain things, or help with code.'), ('human', "what's my name?")]
[('human', "hi! I'm bob"), ('ai', 'Hi Bob! Nice to meet you. How can I help you today? I can answer questions, brainstorm ideas, draft text, explain things, or help with code.'), ('human', "what's my name?"), ('ai', 'Your name is Bob. How can I help you today, Bob?')]
[('human', "what's my name?"), ('ai', 'Your name is Bob. How can I help you today, Bob?')]
```

#### 总结消息 (Summarize messages)

如上所示，修剪或删除消息的问题是您可能会因为删除消息队列而**丢失信息**。
因此，一些应用程序受益于使用**聊天模型**来总结消息历史记录的更复杂方法。

要在代理中总结消息历史记录，请使用内置的 **`SummarizationMiddleware`**：

```python
from langchain.agents import create_agent
from langchain.agents.middleware import SummarizationMiddleware
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.runnables import RunnableConfig
checkpointer = InMemorySaver()
agent = create_agent(
    model="openai:gpt-4o",
    tools=[],
    middleware=[
        SummarizationMiddleware(
            model="openai:gpt-4o-mini",
            max_tokens_before_summary=4000,  # Trigger summarization at 4000 tokens
            messages_to_keep=20,  # Keep last 20 messages after summary
        )
    ],
    checkpointer=checkpointer,
)
config: RunnableConfig = {"configurable": {"thread_id": "1"}}
agent.invoke({"messages": "hi, my name is bob"}, config)
agent.invoke({"messages": "write a short poem about cats"}, config)
agent.invoke({"messages": "now do the same but for dogs"}, config)
final_response = agent.invoke({"messages": "what's my name?"}, config)
final_response["messages"][-1].pretty_print()
"""
================================== Ai Message ==================================
Your name is Bob!
"""
```

请参阅 `SummarizationMiddleware` 了解更多配置选项。

## 访问记忆 (Access memory)

您可以通过几种方式访问和修改代理的短期记忆（状态）：

#### 工具 (Tools)

##### 在工具中读取短期记忆 (Read short-term memory in a tool)

使用 **`ToolRuntime`** 参数在工具中访问短期记忆（状态）。

`tool_runtime` 参数对工具签名是**隐藏**的（因此模型看不到它），但工具可以通过它访问状态。

```python
from langchain.agents import create_agent, AgentState
from langchain.tools import tool, ToolRuntime
class CustomState(AgentState):
    user_id: str
@tool
def get_user_info(
    runtime: ToolRuntime
) -> str:
    """Look up user info."""
    user_id = runtime.state["user_id"]
    return "User is John Smith" if user_id == "user_123" else "Unknown user"
agent = create_agent(
    model="openai:gpt-5-nano",
    tools=[get_user_info],
    state_schema=CustomState,
)
result = agent.invoke({
    "messages": "look up user information",
    "user_id": "user_123"
})
print(result["messages"][-1].content)
# > User is John Smith.
```

##### 从工具写入短期记忆 (Write short-term memory from tools)

要在执行期间修改代理的短期记忆（状态），您可以直接从工具返回**状态更新** (state updates)。

这对于持久化中间结果或使信息可供后续工具或提示访问非常有用。

```python
from langchain.tools import tool, ToolRuntime
from langchain_core.runnables import RunnableConfig
from langchain.messages import ToolMessage
from langchain.agents import create_agent, AgentState
from langgraph.types import Command
from pydantic import BaseModel
class CustomState(AgentState):  # [!code highlight]
    user_name: str
class CustomContext(BaseModel):
    user_id: str
@tool
def update_user_info(
    runtime: ToolRuntime[CustomContext, CustomState],
) -> Command:
    """Look up and update user info."""
    user_id = runtime.context.user_id  # [!code highlight]
    name = "John Smith" if user_id == "user_123" else "Unknown user"
    return Command(update={
        "user_name": name,
        # update the message history
        "messages": [
            ToolMessage(
                "Successfully looked up user information",
                tool_call_id=runtime.tool_call_id
            )
        ]
    })
@tool
def greet(
    runtime: ToolRuntime[CustomContext, CustomState]
) -> str:
    """Use this to greet the user once you found their info."""
    user_name = runtime.state["user_name"]
    return f"Hello {user_name}!"
  # [!code highlight]
agent = create_agent(
    model="openai:gpt-5-nano",
    tools=[update_user_info, greet],
    state_schema=CustomState,
    context_schema=CustomContext,  # [!code highlight]
)
agent.invoke(
    {"messages": [{"role": "user", "content": "greet the user"}]},
    context=CustomContext(user_id="user_123"),
)
```

#### 提示 (Prompt)

在**中间件** (middleware) 中访问短期记忆（状态），以基于对话历史记录或自定义状态字段创建**动态提示** (dynamic prompts)。

```python
from langchain.messages import AnyMessage
from langchain.agents import create_agent, AgentState
from typing import TypedDict
class CustomContext(TypedDict):
    user_name: str
from langchain.agents.middleware import dynamic_prompt, ModelRequest
def get_weather(city: str) -> str:
    """Get the weather in a city."""
    return f"The weather in {city} is always sunny!"
@dynamic_prompt
def dynamic_system_prompt(request: ModelRequest) -> str:
    user_name = request.runtime.context["user_name"]
    system_prompt = f"You are a helpful assistant. Address the user as {user_name}."
    return system_prompt
agent = create_agent(
    model="openai:gpt-5-nano",
    tools=[get_weather],
    middleware=[dynamic_system_prompt],
    context_schema=CustomContext,
)
result = agent.invoke(
    {"messages": [{"role": "user", "content": "What is the weather in SF?"}]},
    context=CustomContext(user_name="John Smith"),
)
for msg in result["messages"]:
    msg.pretty_print()
```

**Output**

```shell
================================ Human Message =================================
What is the weather in SF?
================================== Ai Message ==================================
Tool Calls:
  get_weather (call_WFQlOGn4b2yoJrv7cih342FG)
  Call ID: call_WFQlOGn4b2yoJrv7cih342FG
  Args:
    city: San Francisco
================================= Tool Message =================================
Name: get_weather
The weather in San Francisco is always sunny!
================================== Ai Message ==================================
Hi John Smith, the weather in San Francisco is always sunny!
```

#### 模型之前 (Before model)

在 **`@before_model`** 中间件中访问短期记忆（状态），以在模型调用之前处理消息。

```python
from langchain.messages import RemoveMessage
from langgraph.graph.message import REMOVE_ALL_MESSAGES
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents import create_agent, AgentState
from langchain.agents.middleware import before_model
from langgraph.runtime import Runtime
from typing import Any
@before_model
def trim_messages(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    """Keep only the last few messages to fit context window."""
    messages = state["messages"]
    if len(messages) <= 3:
        return None  # No changes needed
    first_msg = messages[0]
    recent_messages = messages[-3:] if len(messages) % 2 == 0 else messages[-4:]
    new_messages = [first_msg] + recent_messages
    return {
        "messages": [
            RemoveMessage(id=REMOVE_ALL_MESSAGES),
            *new_messages
        ]
    }
agent = create_agent(
    model,
    tools=tools,
    middleware=[trim_messages]
)
config: RunnableConfig = {"configurable": {"thread_id": "1"}}
agent.invoke({"messages": "hi, my name is bob"}, config)
agent.invoke({"messages": "write a short poem about cats"}, config)
agent.invoke({"messages": "now do the same but for dogs"}, config)
final_response = agent.invoke({"messages": "what's my name?"}, config)
final_response["messages"][-1].pretty_print()
"""
================================== Ai Message ==================================
Your name is Bob. You told me that earlier.
If you'd like me to call you a nickname or use a different name, just say the word.
"""
```

#### 模型之后 (After model)

在 **`@after_model`** 中间件中访问短期记忆（状态），以在模型调用之后处理消息。

```python
from langchain.messages import RemoveMessage
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents import create_agent, AgentState
from langchain.agents.middleware import after_model
from langgraph.runtime import Runtime
@after_model
def validate_response(state: AgentState, runtime: Runtime) -> dict | None:
    """Remove messages containing sensitive words."""
    STOP_WORDS = ["password", "secret"]
    last_message = state["messages"][-1]
    if any(word in last_message.content for word in STOP_WORDS):
        return {"messages": [RemoveMessage(id=last_message.id)]}
    return None
agent = create_agent(
    model="openai:gpt-5-nano",
    tools=[],
    middleware=[validate_response],
    checkpointer=InMemorySaver(),
)