# 深度Agent中间件

深度Agent采用模块化的中间件架构构建。深度Agent可以访问：

1. 规划工具
2. 用于存储上下文和长期记忆的文件系统
3. 派生子Agent的能力

每个功能都作为独立的中间件实现。当您使用 `create_deep_agent` 创建深度Agent时，我们会自动将 `TodoListMiddleware`、`FilesystemMiddleware` 和 `SubAgentMiddleware` 附加到您的Agent。

中间件是可组合的——您可以根据需要向Agent添加任意数量的中间件。您可以独立使用任何中间件。

以下部分解释了每个中间件提供的功能。

## 规划中间件

规划是解决复杂问题的组成部分。如果您最近使用过 Claude Code，您会注意到它在处理复杂的多部分任务之前会先写出一个待办事项列表。您还会注意到，随着更多信息的输入，它可以动态地调整和更新这个待办事项列表。

`TodoListMiddleware` 为您的Agent提供了一个专门用于更新此待办事项列表的工具。在执行多部分任务之前和期间，系统会提示Agent使用 `write_todos` 工具来跟踪它正在做什么以及还需要做什么。

```python
from langchain.agents import create_agent
from langchain.agents.middleware import TodoListMiddleware
# TodoListMiddleware 默认包含在 create_deep_agent 中
# 如果构建自定义Agent，您可以对其进行自定义
agent = create_agent(
    model="claude-sonnet-4-5-20250929",
    # 可以通过中间件添加自定义规划指令
    middleware=[
        TodoListMiddleware(
            system_prompt="使用 write_todos 工具来..."  # 可选：对系统提示的自定义添加
        ),
    ],
)
```

```typescript
// TODO: 添加 JS 实现
```

## 文件系统中间件

上下文工程是构建有效Agent的主要挑战。当使用返回可变长度结果的工具（例如 web_search 和 rag）时，这尤其困难，因为长的工具结果会迅速填满您的上下文窗口。

`FilesystemMiddleware` 提供了四个用于与短期和长期记忆交互的工具：

- **ls**: 列出文件系统中的文件
- **read_file**: 从文件中读取整个文件或特定行数
- **write_file**: 将新文件写入文件系统
- **edit_file**: 编辑文件系统中的现有文件

```python
from langchain.agents import create_agent
from deepagents.middleware.filesystem import FilesystemMiddleware
# FilesystemMiddleware 默认包含在 create_deep_agent 中
# 如果构建自定义Agent，您可以对其进行自定义
agent = create_agent(
    model="claude-sonnet-4-5-20250929",
    middleware=[
        FilesystemMiddleware(
            long_term_memory=False,  # 启用对长期记忆的访问，默认为 False。您必须附加一个存储才能使用长期记忆。
            system_prompt="当...时写入文件系统",  # 可选的对系统提示的自定义添加
            custom_tool_descriptions={
                "ls": "当...时使用 ls 工具",
                "read_file": "使用 read_file 工具来..."
            }  # 可选：文件系统工具的自定义描述
        ),
    ],
)
```

### 短期与长期文件系统

默认情况下，这些工具会写入图状态中的本地“文件系统”。如果您向Agent运行时提供 `Store` 对象，您还可以启用保存到长期记忆，该记忆在Agent的不同线程**之间**持久存在。

```python
from langchain.agents import create_agent
from deepagents.middleware import FilesystemMiddleware
from langgraph.store.memory import InMemoryStore
store = InMemoryStore()
agent = create_agent(
    model="claude-sonnet-4-5-20250929",
    store=store,
    middleware=[
        FilesystemMiddleware(
            long_term_memory=True,
            custom_tool_descriptions={
                "ls": "当...时使用 ls 工具",
                "read_file": "使用 read_file 工具来..."
            }  # 可选：文件系统工具的自定义描述
        ),
    ],
)
```

```typescript
// TODO: 添加 JS 实现
```

如果您启用 `use_longterm_memory=True` 并在Agent运行时提供 `Store`，则任何以 **/memories/** 为前缀的文件都将保存到长期记忆存储中。请注意，任何部署在 LangGraph 平台上的Agent都会自动提供长期记忆存储。

## 子Agent中间件

将任务移交给子Agent可以隔离上下文，在深入处理任务的同时保持主（主管）Agent的上下文窗口清洁。

子Agent中间件允许您通过 `task` 工具提供子Agent。

```python
from langchain_core.tools import tool
from langchain.agents import create_agent
from deepagents.middleware.subagents import SubAgentMiddleware
@tool
def get_weather(city: str) -> str:
    """获取一个城市的天气。"""
    return f"{city} 的天气是晴天。"
agent = create_agent(
    model="claude-sonnet-4-5-20250929",
    middleware=[
        SubAgentMiddleware(
            default_model="claude-sonnet-4-5-20250929",
            default_tools=[],
            subagents=[
                {
                    "name": "weather",
                    "description": "此子Agent可以获取城市的天气。",
                    "system_prompt": "使用 get_weather 工具获取城市的天气。",
                    "tools": [get_weather],
                    "model": "gpt-4.1",
                    "middleware": [],
                }
            ],
        )
    ],
)
```

子Agent由**名称**、**描述**、**系统提示**和**工具**定义。您还可以为子Agent提供自定义**模型**或附加**中间件**。当您希望让子Agent与主Agent共享附加状态键时，这尤其有用。

对于更复杂的用例，您还可以提供自己预构建的 LangGraph 图作为子Agent。

```python
from langchain.agents import create_agent
from deepagents.middleware.subagents import SubAgentMiddleware
from deepagents import CompiledSubAgent
from langgraph.graph import StateGraph
# 创建一个自定义的 LangGraph 图
def create_weather_graph():
    workflow = StateGraph(...)
    # 构建您的自定义图
    return workflow.compile()
weather_graph = create_weather_graph()
# 将其包装在 CompiledSubAgent 中
weather_subagent = CompiledSubAgent(
    name="weather",
    description="此子Agent可以获取城市的天气。",
    runnable=weather_graph
)
agent = create_agent(
    model="claude-sonnet-4-5-20250929",
    middleware=[
        SubAgentMiddleware(
            default_model="claude-sonnet-4-5-20250929",
            default_tools=[],
            subagents=[weather_subagent],
        )
    ],
)
```

```typescript
// TODO: 添加 JS 实现
```

除了任何用户定义的子Agent之外，主Agent始终可以访问一个`通用`子Agent。该子Agent具有与主Agent相同的指令以及它可以访问的所有工具。`通用`子Agent的主要目的是上下文隔离——主Agent可以将复杂的任务委托给该子Agent，并获得简洁的答案，而不会因中间工具调用而臃肿。