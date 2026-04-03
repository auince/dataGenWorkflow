# 长期记忆

LangChain 智能体使用 [LangGraph 持久化](../langgraph/persistence.html#memory-store)来实现**长期记忆**。这是一个更高级的主题，需要了解 LangGraph 才能使用。

## 内存存储 (Memory storage)

LangGraph 将长期记忆作为 JSON 文档存储在**存储 (store)** 中，具体请参考 [LangGraph 内存存储](../langgraph/persistence.html#memory-store)。

每条记忆都组织在一个自定义的 **`namespace`**（类似于文件夹）和一个独特的 **`key`**（类似于文件名）下。命名空间通常包含用户或组织 ID 或其他标签，以便于组织信息。

这种结构支持记忆的**层次化组织**。随后可以通过内容过滤器支持**跨命名空间搜索**。

```python
from langgraph.store.memory import InMemoryStore
def embed(texts: list[str]) -> list[list[float]]:
    # 替换为实际的嵌入函数或 LangChain 嵌入对象
    return [[1.0, 2.0] * len(texts)]
# InMemoryStore 将数据保存到内存字典中。在生产环境中使用基于数据库的存储。
store = InMemoryStore(index={"embed": embed, "dims": 2}) # [!code highlight]
user_id = "my-user"
application_context = "chitchat"
namespace = (user_id, application_context) # [!code highlight]
store.put( # [!code highlight]
    namespace,
    "a-memory",
    {
        "rules": [
            "User likes short, direct language",
            "User only speaks English & python",
        ],
        "my-key": "my-value",
    },
)
# 通过 ID 获取 "memory"
item = store.get(namespace, "a-memory") # [!code highlight]
# 在此命名空间内搜索 "memories"，过滤内容等价性，并按向量相似度排序
items = store.search( # [!code highlight]
    namespace, filter={"my-key": "my-value"}, query="language preferences"
)
```

有关内存存储的更多信息，请参阅 [持久化](../langgraph/persistence.html#memory-store) 指南。

## 在工具中读取长期记忆

```python
from dataclasses import dataclass
from langchain_core.runnables import RunnableConfig
from langchain.agents import create_agent
from langchain.tools import tool, ToolRuntime
from langgraph.store.memory import InMemoryStore
@dataclass
class Context:
    user_id: str
# InMemoryStore 将数据保存到内存字典中。在生产环境中使用基于数据库的存储。
store = InMemoryStore() # [!code highlight]
# 使用 put 方法向 store 写入示例数据
store.put( # [!code highlight]
    ("users",),  # 用于将相关数据分组的命名空间（用于用户数据的 users 命名空间）
    "user_123",  # 命名空间内的 Key（用户 ID 作为 Key）
    {
        "name": "John Smith",
        "language": "English",
    }  # 为给定用户存储的数据
)
@tool
def get_user_info(runtime: ToolRuntime[Context]) -> str:
    """Look up user info."""
    # 访问 store - 与提供给 `create_agent` 的 store 相同
    store = runtime.store # [!code highlight]
    user_id = runtime.context.user_id
    # 从 store 检索数据 - 返回带有 value 和 metadata 的 StoreValue 对象
    user_info = store.get(("users",), user_id) # [!code highlight]
    return str(user_info.value) if user_info else "Unknown user"
agent = create_agent(
    model="claude-sonnet-4-5-20250929",
    tools=[get_user_info],
    # 将 store 传递给智能体 - 使智能体能够在运行工具时访问 store
    store=store, # [!code highlight]
    context_schema=Context
)
# 运行智能体
agent.invoke(
    {"messages": [{"role": "user", "content": "look up user information"}]},
    context=Context(user_id="user_123") # [!code highlight]
)
```

## 从工具中写入长期记忆

```python
from dataclasses import dataclass
from typing_extensions import TypedDict
from langchain.agents import create_agent
from langchain.tools import tool, ToolRuntime
from langgraph.store.memory import InMemoryStore
# InMemoryStore 将数据保存到内存字典中。在生产环境中使用基于数据库的存储。
store = InMemoryStore() # [!code highlight]
@dataclass
class Context:
    user_id: str
# TypedDict 定义了供 LLM 使用的用户信息结构
class UserInfo(TypedDict):
    name: str
# 允许智能体更新用户信息的工具（适用于聊天应用）
@tool
def save_user_info(user_info: UserInfo, runtime: ToolRuntime[Context]) -> str:
    """Save user info."""
    # 访问 store - 与提供给 `create_agent` 的 store 相同
    store = runtime.store # [!code highlight]
    user_id = runtime.context.user_id # [!code highlight]
    # 在 store 中存储数据 (namespace, key, data)
    store.put(("users",), user_id, user_info) # [!code highlight]
    return "Successfully saved user info."
agent = create_agent(
    model="claude-sonnet-4-5-20250929",
    tools=[save_user_info],
    store=store, # [!code highlight]
    context_schema=Context
)
# 运行智能体
agent.invoke(
    {"messages": [{"role": "user", "content": "My name is John Smith"}]},
    # 在 context 中传入 user_id 以识别正在更新谁的信息
    context=Context(user_id="user_123") # [!code highlight]
)
# 您可以直接访问 store 来获取该值
store.get(("users",), "user_123").value