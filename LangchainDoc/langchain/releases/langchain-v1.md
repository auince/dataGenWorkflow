# v1 新特性

**LangChain v1 是一个专注且可用于生产的智能体构建基础框架。** 我们围绕三个核心改进优化了框架：

## 主要更新亮点

*   **create_agent**
    *   LangChain 构建智能体的新标准，替代了 `langgraph.prebuilt.create_react_agent`。
*   **标准内容块**
    *   新增 `content_blocks` 属性，可统一访问各提供商的现代 LLM 功能。
*   **简化的命名空间**
    *   `langchain` 命名空间精简，只保留智能体的核心构建模块，旧功能移至 `langchain-classic`。

---

## 升级方法

```bash
pip install -U langchain
```

```bash
uv add langchain
```

完整更新列表请参考：[迁移指南](https://langchain-doc.cn/v1/python/migrate/langchain-v1)。

## `create_agent`

[`create_agent`](https://reference.langchain.com/python/langchain/agents/#langchain.agents.create_agent) 是 LangChain 1.0 中构建智能体的标准方式。它比 [`langgraph.prebuilt.create_react_agent`](https://reference.langchain.com/python/langgraph/prebuilt/#langgraph.prebuilt.chat_agent_executor.create_react_agent) 更简单，同时通过 [middleware](#middleware-中间件) 提供更高的自定义潜力。

```python
from langchain.agents import create_agent
agent = create_agent(
    model="anthropic:claude-sonnet-4-5",
    tools=[search_web, analyze_data, send_email],
    system_prompt="你是一个有帮助的研究助理。"
)
result = agent.invoke({
    "messages": [
        {"role": "user", "content": "研究 AI 安全趋势"}
    ]
})
```

内部实现基于智能体循环：调用模型 → 选择工具执行 → 当不再调用工具时结束。

![智能体核心循环](https://mintcdn.com/langchain-5e9cc07a/Tazq8zGc0yYUYrDl/v1/images/core_agent_loop.png)
智能体核心循环

更多信息，请参考 [智能体文档](../agents.html)。

### Middleware（中间件）

Middleware 是 [`create_agent`](https://reference.langchain.com/python/langchain/agents/#langchain.agents.create_agent) 的核心功能，提供高度可定制的入口点，帮助你实现更复杂的智能体。

中间件可用于动态控制提示、会话摘要、选择性工具访问、状态管理及安全护栏。

#### 内置中间件

LangChain 提供了一些常用的 [内置中间件](../middleware.html#built-in-middleware)：

*   [`PIIMiddleware`](https://reference.langchain.com/python/langchain/middleware/#langchain.agents.middleware.PIIMiddleware)：在发送给模型前屏蔽敏感信息
*   [`SummarizationMiddleware`](https://reference.langchain.com/python/langchain/middleware/#langchain.agents.middleware.SummarizationMiddleware)：当对话过长时自动摘要
*   [`HumanInTheLoopMiddleware`](https://reference.langchain.com/python/langchain/middleware/#langchain.agents.middleware.HumanInTheLoopMiddleware)：敏感工具调用需人工审批

```python
from langchain.agents import create_agent
from langchain.agents.middleware import (
    PIIMiddleware,
    SummarizationMiddleware,
    HumanInTheLoopMiddleware
)
agent = create_agent(
    model="anthropic:claude-sonnet-4-5",
    tools=[read_email, send_email],
    middleware=[
        PIIMiddleware(patterns=["email", "phone", "ssn"]),
        SummarizationMiddleware(model="anthropic:claude-sonnet-4-5", max_tokens_before_summary=500),
        HumanInTheLoopMiddleware(interrupt_on={"send_email": {"allowed_decisions": ["approve", "edit", "reject"]}})
    ]
)
```

#### 自定义中间件

你也可以实现自定义中间件，通过在智能体执行的每一步挂钩来自定义行为：

| Hook | 执行时机 | 用例示例 |
| :--- | :--- | :--- |
| `before_agent` | 调用智能体前 | 加载记忆、校验输入 |
| `before_model` | 每次 LLM 调用前 | 更新提示、修剪消息 |
| `wrap_model_call` | 包裹每次 LLM 调用 | 拦截并修改请求/响应 |
| `wrap_tool_call` | 包裹每次工具调用 | 拦截并修改工具执行 |
| `after_model` | 每次 LLM 响应后 | 校验输出、应用安全护栏 |
| `after_agent` | 智能体完成后 | 保存结果、清理资源 |

示例自定义中间件：

```python
from dataclasses import dataclass
from typing import Callable
from langchain_openai import ChatOpenAI
from langchain.agents.middleware import AgentMiddleware, ModelRequest
from langchain.agents.middleware.types import ModelResponse

@dataclass
class Context:
    user_expertise: str = "beginner"

class ExpertiseBasedToolMiddleware(AgentMiddleware):
    def wrap_model_call(self, request: ModelRequest, handler: Callable[[ModelRequest], ModelResponse]) -> ModelResponse:
        user_level = request.runtime.context.user_expertise
        if user_level == "expert":
            model = ChatOpenAI(model="openai:gpt-5")
            tools = [advanced_search, data_analysis]
        else:
            model = ChatOpenAI(model="openai:gpt-5-nano")
            tools = [simple_search, basic_calculator]
        request.model = model
        request.tools = tools
        return handler(request)

agent = create_agent(
    model="anthropic:claude-sonnet-4-5",
    tools=[simple_search, advanced_search, basic_calculator, data_analysis],
    middleware=[ExpertiseBasedToolMiddleware()],
    context_schema=Context
)
```

完整中间件指南：[中间件文档](../middleware.html)。

---

### 构建于 LangGraph 之上

[`create_agent`](https://reference.langchain.com/python/langchain/agents/#langchain.agents.create_agent) 基于 [LangGraph](../../langgraph.html) 构建，因此自动支持：

*   **持久化**：会话间对话自动保存
*   **流式处理**：实时传输令牌、工具调用及推理轨迹
*   **人工干预**：敏感操作前暂停智能体以等待人工审批
*   **时间旅行**：回溯对话历史，探索不同路径和提示

---

### 结构化输出

[`create_agent`](https://reference.langchain.com/python/langchain/agents/#langchain.agents.create_agent) 支持更优的结构化输出生成：

*   **主循环集成**：结构化输出在主循环中生成，无需额外 LLM 调用
*   **输出策略**：模型可选择调用工具或使用提供商侧的结构化输出
*   **成本优化**：减少额外 LLM 调用带来的费用

```python
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from pydantic import BaseModel

class Weather(BaseModel):
    temperature: float
    condition: str

def weather_tool(city: str) -> str:
    return f"{city} 天气晴，70°F"

agent = create_agent(
    "openai:gpt-4o-mini",
    tools=[weather_tool],
    response_format=ToolStrategy(Weather)
)

result = agent.invoke({"messages": [{"role": "user", "content": "旧金山天气如何？"}]})
print(result["structured_response"])
```

## 标准内容块

当前 `content_blocks` 仅支持以下集成：

*   `langchain-anthropic`
*   `langchain-aws`
*   `langchain-openai`
*   `langchain-google-genai`
*   `langchain-ollama`

`content_blocks` 提供统一的消息内容表示，可跨提供商使用：

```python
from langchain_anthropic import ChatAnthropic

model = ChatAnthropic(model="claude-sonnet-4-5")
response = model.invoke("法国首都是什么？")

for block in response.content_blocks:
    if block["type"] == "reasoning":
        print(f"模型推理: {block['reasoning']}")
    elif block["type"] == "text":
        print(f"响应: {block['text']}")
    elif block["type"] == "tool_call":
        print(f"工具调用: {block['name']}({block['args']})")
```

## 简化命名空间

LangChain v1 精简了 `langchain` 包，只保留核心构建模块：

| 模块 | 功能 |
| :--- | :--- |
| `langchain.agents` | `create_agent`、AgentState 核心智能体功能 |
| `langchain.messages` | 消息类型、内容块、trim_messages |
| `langchain.tools` | 工具相关类和注解 |
| `langchain.chat_models` | 初始化聊天模型 |