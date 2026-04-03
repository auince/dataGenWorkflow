# 守卫

> 为您的智能体实施安全检查和内容过滤

守卫通过在您的智能体执行的关键点验证和过滤内容，帮助您构建**安全、合规**的 AI 应用。它们可以在问题发生前检测敏感信息、强制执行内容策略、验证输出并防止不安全行为。

### 常见用例

*   **防止 PII（个人身份信息）泄露**
*   **检测和阻止提示注入 (prompt injection) 攻击**
*   **阻止不当或有害内容**
*   **强制执行业务规则和合规要求**
*   **验证输出质量和准确性**

您可以使用 **[中间件 (middleware)](middleware.html)** 来实施守卫，在策略性节点拦截执行——在智能体开始前、完成后，或围绕模型和工具调用时。

### 守卫的两种方法

守卫可以通过两种互补的方法实施：

| 方法 | 描述 |
| :--- | :--- |
| **确定性守卫 (Deterministic guardrails)** | 使用基于规则的逻辑，如正则表达式、关键词匹配或明确检查。**快速、可预测、经济高效**，但可能会错过细微的违规行为。 |
| **基于模型的守卫 (Model-based guardrails)** | 使用 **LLMs 或分类器**通过语义理解来评估内容。可以捕获规则遗漏的**微妙问题**，但速度较慢且成本较高。 |

LangChain 提供了**内置守卫**（例如，[PII 检测](#pii-detection)、[人工审核](#human-in-the-loop)）和一个灵活的中间件系统，可使用任一方法构建**自定义守卫**。

## 内置守卫 (Built-in guardrails)

### 个人身份信息 (PII) 检测

LangChain 提供了内置中间件用于检测和处理对话中的**个人身份信息 (PII)**。此中间件可以检测常见的 PII 类型，如电子邮件、信用卡、IP 地址等。

PII 检测中间件适用于需要合规要求的医疗保健和金融应用、需要清理日志的客户服务智能体，以及通常处理敏感用户数据的任何应用。

PII 中间件支持多种处理检测到的 PII 的策略：

| 策略 (`Strategy`) | 描述 | 示例 |
| :--- | :--- | :--- |
| `redact` | 替换为 `[REDACTED_TYPE]` | `[REDACTED_EMAIL]` |
| `mask` | 部分遮盖（例如，后 4 位） | `****-****-****-1234` |
| `hash` | 替换为确定性哈希值 | `a8f5f167...` |
| `block` | 检测到时抛出异常 | 抛出错误 |

```python
from langchain.agents import create_agent
from langchain.agents.middleware import PIIMiddleware
agent = create_agent(
    model="openai:gpt-4o",
    tools=[customer_service_tool, email_tool],
    middleware=[
        # 在发送给模型之前，将用户输入中的电子邮件编辑掉
        PIIMiddleware(
            "email",
            strategy="redact",
            apply_to_input=True,
        ),
        # 遮盖用户输入中的信用卡
        PIIMiddleware(
            "credit_card",
            strategy="mask",
            apply_to_input=True,
        ),
        # 阻止 API 密钥 - 如果检测到则抛出错误
        PIIMiddleware(
            "api_key",
            detector=r"sk-[a-zA-Z0-9]{32}",
            strategy="block",
            apply_to_input=True,
        ),
    ],
)
# 当用户提供 PII 时，它将根据策略进行处理
result = agent.invoke({
    "messages": [{"role": "user", "content": "My email is john.doe@example.com and card is 4532-1234-5678-9010"}]
})
```

<details>
<summary>**内置 PII 类型和配置**</summary>

**内置 PII 类型：**

*   `email` - 电子邮件地址
*   `credit_card` - 信用卡号（经过 Luhn 验证）
*   `ip` - IP 地址
*   `mac_address` - MAC 地址
*   `url` - URL

**配置选项：**

| 参数 (`Parameter`) | 描述 | 默认值 (`Default`) |
| :--- | :--- | :--- |
| `pii_type` | 要检测的 PII 类型（内置或自定义） | 必需 |
| `strategy` | 如何处理检测到的 PII (`"block"`, `"redact"`, `"mask"`, `"hash"`) | `"redact"` |
| `detector` | 自定义检测器函数或正则表达式模式 | `None`（使用内置） |
| `apply_to_input` | 在模型调用前检查用户消息 | `True` |
| `apply_to_output` | 在模型调用后检查 AI 消息 | `False` |
| `apply_to_tool_results` | 在执行后检查工具结果消息 | `False` |

</details>

请参阅 **[中间件文档](middleware.html#pii-detection)** 了解 PII 检测功能的完整详情。

### 人工审核 (Human-in-the-loop)

LangChain 提供了内置中间件，要求在执行敏感操作之前进行**人工批准**。这是针对高风险决策最有效的守卫之一。

人工审核中间件适用于以下情况：金融交易和转账、删除或修改生产数据、向外部方发送通信，以及任何具有重大业务影响的操作。

```python
from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command
agent = create_agent(
    model="openai:gpt-4o",
    tools=[search_tool, send_email_tool, delete_database_tool],
    middleware=[
        HumanInTheLoopMiddleware(
            interrupt_on={
                # 要求批准敏感操作
                "send_email": True,
                "delete_database": True,
                # 自动批准安全操作
                "search": False,
            }
        ),
    ],
    # 在中断期间持久化状态
    checkpointer=InMemorySaver(),
)
# 人工审核需要一个线程 ID 来进行持久化
config = {"configurable": {"thread_id": "some_id"}}
# 在执行敏感工具之前，智能体将暂停并等待批准
result = agent.invoke(
    {"messages": [{"role": "user", "content": "Send an email to the team"}]},
    config=config
)
result = agent.invoke(
    Command(resume={"decisions": [{"type": "approve"}]}),
    config=config # 相同的线程 ID 以恢复暂停的对话
)
```

> 💡 **提示：**
> 请参阅 **[人工审核文档](human-in-the-loop.html)** 了解实施批准工作流程的完整详情。

## 自定义守卫 (Custom guardrails)

对于更复杂的守卫，您可以创建**自定义中间件**，在智能体执行之前或之后运行。这使您可以完全控制验证逻辑、内容过滤和安全检查。

### 智能体执行前守卫 (Before agent guardrails)

使用“**智能体执行前**”的钩子 (hooks) 在每次调用开始时验证请求一次。这对于会话级别的检查（如身份验证、速率限制或在任何处理开始前阻止不当请求）非常有用。

<details>
<summary> **类的语法** </summary>

```python
from typing import Any
from langchain.agents.middleware import AgentMiddleware, AgentState, hook_config
from langgraph.runtime import Runtime
class ContentFilterMiddleware(AgentMiddleware):
    """Deterministic guardrail: Block requests containing banned keywords."""
    def __init__(self, banned_keywords: list[str]):
        super().__init__()
        self.banned_keywords = [kw.lower() for kw in banned_keywords]
    @hook_config(can_jump_to=["end"])
    def before_agent(self, state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
        # Get the first user message
        if not state["messages"]:
            return None
        first_message = state["messages"][0]
        if first_message.type != "human":
            return None
        content = first_message.content.lower()
        # Check for banned keywords
        for keyword in self.banned_keywords:
            if keyword in content:
                # Block execution before any processing
                return {
                    "messages": [{
                        "role": "assistant",
                        "content": "I cannot process requests containing inappropriate content. Please rephrase your request."
                    }],
                    "jump_to": "end"
                }
        return None
# Use the custom guardrail
from langchain.agents import create_agent
agent = create_agent(
    model="openai:gpt-4o",
    tools=[search_tool, calculator_tool],
    middleware=[
        ContentFilterMiddleware(
            banned_keywords=["hack", "exploit", "malware"]
        ),
    ],
)
# This request will be blocked before any processing
result = agent.invoke({
    "messages": [{"role": "user", "content": "How do I hack into a database?"}]
})
```

</details>

<details>
<summary> **修饰符的语法** </summary>

```python
from typing import Any
from langchain.agents.middleware import before_agent, AgentState, hook_config
from langgraph.runtime import Runtime
banned_keywords = ["hack", "exploit", "malware"]
@before_agent(can_jump_to=["end"])
def content_filter(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    """Deterministic guardrail: Block requests containing banned keywords."""
    # Get the first user message
    if not state["messages"]:
        return None
    first_message = state["messages"][0]
    if first_message.type != "human":
        return None
    content = first_message.content.lower()
    # Check for banned keywords
    for keyword in banned_keywords:
        if keyword in content:
            # Block execution before any processing
            return {
                "messages": [{
                    "role": "assistant",
                    "content": "I cannot process requests containing inappropriate content. Please rephrase your request."
                }],
                "jump_to": "end"
            }
    return None
# Use the custom guardrail
from langchain.agents import create_agent
agent = create_agent(
    model="openai:gpt-4o",
    tools=[search_tool, calculator_tool],
    middleware=[content_filter],
)
# This request will be blocked before any processing
result = agent.invoke({
    "messages": [{"role": "user", "content": "How do I hack into a database?"}]
})
```

</details>

### 智能体执行后守卫 (After agent guardrails)

使用“**智能体执行后**”的钩子在返回给用户之前验证最终输出一次。这对于基于模型的安全检查、质量验证或对完整的智能体响应进行最终合规扫描非常有用。

<details>
<summary>**类的语法**</summary>

```python
from langchain.agents.middleware import AgentMiddleware, AgentState, hook_config
from langgraph.runtime import Runtime
from langchain_core.messages import AIMessage
from langchain.chat_models import init_chat_model
from typing import Any
class SafetyGuardrailMiddleware(AgentMiddleware):
    """Model-based guardrail: Use an LLM to evaluate response safety."""
    def __init__(self):
        super().__init__()
        self.safety_model = init_chat_model("openai:gpt-4o-mini")
    @hook_config(can_jump_to=["end"])
    def after_agent(self, state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
        # Get the final AI response
        if not state["messages"]:
            return None
        last_message = state["messages"][-1]
        if not isinstance(last_message, AIMessage):
            return None
        # Use a model to evaluate safety
        safety_prompt = f"""Evaluate if this response is safe and appropriate.
        Respond with only 'SAFE' or 'UNSAFE'.
        Response: {last_message.content}"""
        result = self.safety_model.invoke([{"role": "user", "content": safety_prompt}])
        if "UNSAFE" in result.content:
            return {
                "messages": [{
                    "role": "assistant",
                    "content": "I cannot provide that response. Please rephrase your request."
                }],
                "jump_to": "end"
            }
        return None
# Use the safety guardrail
from langchain.agents import create_agent
agent = create_agent(
    model="openai:gpt-4o",
    tools=[search_tool, calculator_tool],
    middleware=[SafetyGuardrailMiddleware()],
)
result = agent.invoke({
    "messages": [{"role": "user", "content": "How do I make explosives?"}]
})
```

</details>

<details>
<summary>**修饰词的语法**</summary>

```python
from langchain.agents.middleware import after_agent, AgentState, hook_config
from langgraph.runtime import Runtime
from langchain_core.messages import AIMessage
from langchain.chat_models import init_chat_model
from typing import Any
safety_model = init_chat_model("openai:gpt-4o-mini")
@after_agent(can_jump_to=["end"])
def safety_guardrail(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    """Model-based guardrail: Use an LLM to evaluate response safety."""
    # Get the final AI response
    if not state["messages"]:
        return None
    last_message = state["messages"][-1]
    if not isinstance(last_message, AIMessage):
        return None
    # Use a model to evaluate safety
    safety_prompt = f"""Evaluate if this response is safe and appropriate.
    Respond with only 'SAFE' or 'UNSAFE'.
    Response: {last_message.content}"""
    result = safety_model.invoke([{"role": "user", "content": safety_prompt}])
    if "UNSAFE" in result.content:
        return {
            "messages": [{
                "role": "assistant",
                "content": "I cannot provide that response. Please rephrase your request."
            }],
            "jump_to": "end"
        }
    return None
# Use the safety guardrail
from langchain.agents import create_agent
agent = create_agent(
    model="openai:gpt-4o",
    tools=[search_tool, calculator_tool],
    middleware=[safety_guardrail],
)
result = agent.invoke({
    "messages": [{"role": "user", "content": "How do I make explosives?"}]
})
```

</details>

### 组合多个守卫

您可以通过将多个守卫添加到中间件数组中来**堆叠**它们。它们按顺序执行，允许您构建分层保护：

```python
from langchain.agents import create_agent
from langchain.agents.middleware import PIIMiddleware, HumanInTheLoopMiddleware
agent = create_agent(
    model="openai:gpt-4o",
    tools=[search_tool, send_email_tool],
    middleware=[
        # 第 1 层: 确定性输入过滤器（智能体执行前）
        ContentFilterMiddleware(banned_keywords=["hack", "exploit"]),
        # 第 2 层: PII 保护（模型执行前和后）
        PIIMiddleware("email", strategy="redact", apply_to_input=True),
        PIIMiddleware("email", strategy="redact", apply_to_output=True),
        # 第 3 层: 敏感工具的人工批准
        HumanInTheLoopMiddleware(interrupt_on={"send_email": True}),
        # 第 4 层: 基于模型的安全检查（智能体执行后）
        SafetyGuardrailMiddleware(),
    ],
)
```

## 附加资源

*   [**中间件文档**](middleware.html) - 自定义中间件的完整指南
*   [**中间件 API 参考**](https://reference.langchain.com/python/langchain/middleware/) - 自定义中间件的完整指南
*   [**人工审核**](human-in-the-loop.html) - 为敏感操作添加人工审核
*   [**测试智能体**](test.html) - 测试安全机制的策略