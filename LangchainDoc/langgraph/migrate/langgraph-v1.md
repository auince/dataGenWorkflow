# v1 迁移指南

本指南概述了 LangGraph v1 中的变化以及如何从早期版本进行迁移。有关更改的概览，请参阅 [v1 版本新特性](../releases/langgraph-v1.html) 页面。

要升级：

```bash
pip install -U langgraph langchain-core
```

或

```bash
uv add langgraph langchain-core
```

---

## 更改摘要

LangGraph v1 大部分与早期版本**向后兼容**。主要的变化是**弃用了** [`create_react_agent`](https://langchain-doc.cn/v1/python/langgraph/migrate/%5Bhttps:/reference.langchain.com/python/langgraph/prebuilt/#langgraph.prebuilt.chat_agent_executor.create_react_agent%5D(https://reference.langchain.com/python/langgraph/prebuilt/#langgraph.prebuilt.chat_agent_executor.create_react_agent))，转而使用 LangChain 新的 [`create_agent`](https://langchain-doc.cn/v1/python/langgraph/migrate/%5Bhttps:/reference.langchain.com/python/langchain/agents/#langchain.agents.create_agent%5D(https://reference.langchain.com/python/langchain/agents/#langchain.agents.create_agent)) 函数。

## 弃用项

下表列出了 LangGraph v1 中所有已弃用的项：

| 已弃用项 | 替代项 |
| :--- | :--- |
| `create_react_agent` | [`langchain.agents.create_agent`](https://langchain-doc.cn/v1/python/langgraph/migrate/%5Bhttps:/reference.langchain.com/python/langchain/agents/#langchain.agents.create_agent%5D(https://reference.langchain.com/python/langchain/agents/#langchain.agents.create_agent)) |
| `AgentState` | [`langchain.agents.AgentState`](https://langchain-doc.cn/v1/python/langgraph/migrate/%5Bhttps:/reference.langchain.com/python/langchain/agents/#langchain.agents.AgentState%5D(https://reference.langchain.com/python/langchain/agents/#langchain.agents.AgentState)) |
| `AgentStatePydantic` | `langchain.agents.AgentState` (不再有 pydantic 状态) |
| `AgentStateWithStructuredResponse` | `langchain.agents.AgentState` |
| `AgentStateWithStructuredResponsePydantic` | `langchain.agents.AgentState` (不再有 pydantic 状态) |
| `HumanInterruptConfig` | `langchain.agents.middleware.human_in_the_loop.InterruptOnConfig` |
| `ActionRequest` | `langchain.agents.middleware.human_in_the_loop.InterruptOnConfig` |
| `HumanInterrupt` | `langchain.agents.middleware.human_in_the_loop.HITLRequest` |
| `ValidationNode` | 使用 [`create_agent`](https://langchain-doc.cn/v1/python/langgraph/migrate/%5Bhttps:/reference.langchain.com/python/langchain/agents/#langchain.agents.create_agent%5D(https://reference.langchain.com/python/langchain/agents/#langchain.agents.create_agent)) 时，工具会自动验证输入 |
| `MessageGraph` | 带有一个 `messages` 键的 [`StateGraph`](https://langchain-doc.cn/v1/python/langgraph/migrate/%5Bhttps:/reference.langchain.com/python/langgraph/graphs/#langgraph.graph.state.StateGraph%5D(https://reference.langchain.com/python/langgraph/graphs/#langgraph.graph.state.StateGraph))，如 [`create_agent`](https://langchain-doc.cn/v1/python/langgraph/migrate/%5Bhttps:/reference.langchain.com/python/langchain/agents/#langchain.agents.create_agent%5D(https://reference.langchain.com/python/langchain/agents/#langchain.agents.create_agent)) 所提供的 |

---

## `create_react_agent` → `create_agent`

LangGraph v1 弃用了 [`create_react_agent`](https://langchain-doc.cn/v1/python/langgraph/migrate/%5Bhttps:/reference.langchain.com/python/langgraph/prebuilt/#langgraph.prebuilt.chat_agent_executor.create_react_agent%5D(https://reference.langchain.com/python/langgraph/prebuilt/#langgraph.prebuilt.chat_agent_executor.create_react_agent)) 预构建功能。请使用 LangChain 的 [`create_agent`](https://langchain-doc.cn/v1/python/langgraph/migrate/%5Bhttps:/reference.langchain.com/python/langchain/agents/#langchain.agents.create_agent%5D(https://reference.langchain.com/python/langchain/agents/#langchain.agents.create_agent))，它运行在 LangGraph 之上并添加了一个灵活的**中间件系统**。

请参阅 LangChain v1 文档了解详细信息：

* [发布说明](https://langchain-doc.cn/v1/python/releases/langchain-v1#createagent)
* [迁移指南](https://langchain-doc.cn/v1/python/migrate/langchain-v1#migrate-to-create_agent)

**v1 (新)**

```python
from langchain.agents import create_agent
agent = create_agent(  # 突出显示
    model,
    tools,
    system_prompt="You are a helpful assistant.",
)
```

**v0 (旧)**

```python
from langgraph.prebuilt import create_react_agent
agent = create_react_agent(  # 突出显示
    model,
    tools,
    prompt="You are a helpful assistant.",  # 突出显示
)
```

---

## 破坏性更改

### 停止支持 Python 3.9

所有 LangChain 包现在都要求使用 **Python 3.10 或更高版本**。Python 3.9 已于 2025 年 10 月达到[生命周期结束](https://devguide.python.org/versions/)。