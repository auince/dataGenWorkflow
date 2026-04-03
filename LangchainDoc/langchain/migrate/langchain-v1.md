# v1 迁移指南

本指南概述了 [LangChain v1](https://langchain-doc.cn/v1/python/releases/langchain-v1) 与之前版本之间的主要变化。

## 精简的包

在 v1 中，`langchain` 包的命名空间被大幅简化，专注于代理（Agent）的核心构建模块。精简后的包更易于发现和使用核心功能。

### 命名空间

| 模块 | 可用功能 | 备注 |
| :--- | :--- | :--- |
| [`langchain.agents`](https://reference.langchain.com/python/langchain/agents) | [`create_agent`](https://reference.langchain.com/python/langchain/agents/#langchain.agents.create_agent), [`AgentState`](https://reference.langchain.com/python/langchain/agents/#langchain.agents.AgentState) | 核心代理创建功能 |
| [`langchain.messages`](https://reference.langchain.com/python/langchain/messages) | 消息类型、[内容块](https://reference.langchain.com/python/langchain/messages/#langchain.messages.ContentBlock), [`trim_messages`](https://reference.langchain.com/python/langchain/messages/#langchain.messages.trim_messages) | 从 `langchain-core` 重新导出 |
| [`langchain.tools`](https://reference.langchain.com/python/langchain/tools) | [`@tool`](https://reference.langchain.com/python/langchain/tools/#langchain.tools.tool), [`BaseTool`](https://reference.langchain.com/python/langchain/tools/#langchain.tools.BaseTool), 注入工具助手 | 从 `langchain-core` 重新导出 |
| [`langchain.chat_models`](https://reference.langchain.com/python/langchain/models) | [`init_chat_model`](https://reference.langchain.com/python/langchain/models/#langchain.chat_models.init_chat_model), [`BaseChatModel`](https://reference.langchain.com/python/langchain_core/language_models/#langchain_core.language_models.chat_models.BaseChatModel) | 统一模型初始化 |
| [`langchain.embeddings`](https://reference.langchain.com/python/langchain/embeddings) | [`init_embeddings`](https://reference.langchain.com/python/langchain_core/embeddings/#langchain_core.embeddings.embeddings.Embeddings), [`Embeddings`](https://reference.langchain.com/python/langchain_core/embeddings/#langchain_core.embeddings.embeddings.Embeddings) | 嵌入模型 |

### `langchain-classic`

如果你之前使用 `langchain` 包中的以下功能，需要安装 [`langchain-classic`](https://pypi.org/project/langchain-classic/) 并更新导入路径：

*   旧版链（如 `LLMChain`、`ConversationChain` 等）
*   检索器（如 `MultiQueryRetriever` 或以前 `langchain.retrievers` 模块中的内容）
*   索引 API
*   hub 模块（用于程序化管理 prompt）
*   嵌入模块（如 `CacheBackedEmbeddings` 和社区嵌入）
*   [`langchain-community`](https://pypi.org/project/langchain-community) 重新导出
*   其他已弃用功能

```python
# Chains
from langchain_classic.chains import LLMChain
# Retrievers
from langchain_classic.retrievers import ...
# Indexing
from langchain_classic.indexes import ...
# Hub
from langchain_classic import hub
```

旧版本：

```python
# Chains
from langchain.chains import LLMChain
# Retrievers
from langchain.retrievers import ...
# Indexing
from langchain.indexes import ...
# Hub
from langchain import hub
```

安装方式：

```bash
pip install langchain-classic
```

或者使用 `uv`：

```bash
uv add langchain-classic
```

---

## 迁移到 `create_agent`

在 v1.0 之前，我们推荐使用 [`langgraph.prebuilt.create_react_agent`](https://reference.langchain.com/python/langgraph/prebuilt/#langgraph.prebuilt.chat_agent_executor.create_react_agent) 创建代理。现在推荐使用 [`langchain.agents.create_agent`](https://reference.langchain.com/python/langchain/agents/#langchain.agents.create_agent)。

下面的表格概述了从 [`create_react_agent`](https://reference.langchain.com/python/langgraph/prebuilt/#langgraph.prebuilt.chat_agent_executor.create_react_agent) 到 [`create_agent`](https://reference.langchain.com/python/langchain/agents/#langchain.agents.create_agent) 的功能变化：

| 模块 | 变化概览 |
| :--- | :--- |
| [导入路径](#import-path) | 包从 `langgraph.prebuilt` 移动到 `langchain.agents` |
| [Prompts](#prompts) | 参数重命名为 [`system_prompt`](https://reference.langchain.com/python/langchain/agents/#langchain.agents.create_agent%28system_prompt%29)，动态 prompt 使用中间件 |
| [Pre-model hook](#pre-model-hook) | 用中间件的 `before_model` 方法替代 |
| [Post-model hook](#post-model-hook) | 用中间件的 `after_model` 方法替代 |
| [Custom state](#custom-state) | 仅支持 `TypedDict`，可通过 [`state_schema`](https://reference.langchain.com/python/langchain/middleware/#langchain.agents.middleware.AgentMiddleware.state_schema) 或中间件定义 |
| [Model](#model) | 通过中间件动态选择，预绑定模型不再支持 |
| [Tools](#tools) | 工具错误处理移动到中间件中的 `wrap_tool_call` |
| [Structured output](#structured-output) | 移除 prompted output，使用 `ToolStrategy` 或 `ProviderStrategy` |
| [Streaming node name](#streaming-node-name-rename) | 节点名称从 `"agent"` 改为 `"model"` |
| [Runtime context](#runtime-context) | 通过 `context` 参数依赖注入，不再使用 `config["configurable"]` |
| [Namespace](#simplified-namespace) | 精简以专注于代理构建模块，旧代码迁移到 `langchain-classic` |

### Import path

代理的导入路径从 `langgraph.prebuilt` 改为 `langchain.agents`，函数名从 [`create_react_agent`](https://reference.langchain.com/python/langgraph/prebuilt/#langgraph.prebuilt.chat_agent_executor.create_react_agent) 改为 [`create_agent`](https://reference.langchain.com/python/langchain/agents/#langchain.agents.create_agent)：

```python
from langgraph.prebuilt import create_react_agent # 旧
from langchain.agents import create_agent        # 新
```

更多信息参见 [Agents](../agents.html)。

### Prompts

#### 静态 prompt 重命名

`prompt` 参数已重命名为 [`system_prompt`](https://reference.langchain.com/python/langchain/agents/#langchain.agents.create_agent%28system_prompt%29)：

```python
from langchain.agents import create_agent
agent = create_agent(
    model="anthropic:claude-sonnet-4-5",
    tools=[check_weather],
    system_prompt="You are a helpful assistant"  # 新参数
)
```

旧版本：

```python
from langgraph.prebuilt import create_react_agent
agent = create_react_agent(
    model="anthropic:claude-sonnet-4-5",
    tools=[check_weather],
    prompt="You are a helpful assistant"  # 旧参数
)
```

#### `SystemMessage` 改为字符串

如果系统 prompt 使用 [`SystemMessage`](https://reference.langchain.com/python/langchain/messages/#langchain.messages.SystemMessage) 对象，需要提取字符串内容：

```python
from langchain.agents import create_agent
agent = create_agent(
    model="anthropic:claude-sonnet-4-5",
    tools=[check_weather],
    system_prompt="You are a helpful assistant"
)
```

旧版本：

```python
from langchain.messages import SystemMessage
from langgraph.prebuilt import create_react_agent
agent = create_react_agent(
    model="anthropic:claude-sonnet-4-5",
    tools=[check_weather],
    prompt=SystemMessage(content="You are a helpful assistant")
)
```

#### 动态 prompt

动态 prompt 是核心的上下文工程模式——根据当前对话状态调整给模型的提示。可使用 [`@dynamic_prompt`](https://reference.langchain.com/python/langchain/middleware/#langchain.agents.middleware.dynamic_prompt) 装饰器：

```python
from dataclasses import dataclass
from langchain.agents import create_agent
from langchain.agents.middleware import dynamic_prompt, ModelRequest
from langgraph.runtime import Runtime

@dataclass
class Context:
    user_role: str = "user"

@dynamic_prompt
def dynamic_prompt(request: ModelRequest) -> str:
    user_role = request.runtime.context.user_role
    base_prompt = "You are a helpful assistant."
    if user_role == "expert":
        prompt = f"{base_prompt} Provide detailed technical responses."
    elif user_role == "beginner":
        prompt = f"{base_prompt} Explain concepts simply and avoid jargon."
    else:
        prompt = base_prompt
    return prompt

agent = create_agent(
    model="openai:gpt-4o",
    tools=tools,
    middleware=[dynamic_prompt],
    context_schema=Context
)

agent.invoke(
    {"messages": [{"role": "user", "content": "Explain async programming"}]},
    context=Context(user_role="expert")
)
```

旧版本：

```python
from dataclasses import dataclass
from langgraph.prebuilt import create_react_agent, AgentState
from langgraph.runtime import get_runtime

@dataclass
class Context:
    user_role: str

def dynamic_prompt(state: AgentState) -> str:
    runtime = get_runtime(Context)
    user_role = runtime.context.user_role
    base_prompt = "You are a helpful assistant."
    if user_role == "expert":
        return f"{base_prompt} Provide detailed technical responses."
    elif user_role == "beginner":
        return f"{base_prompt} Explain concepts simply and avoid jargon."
    return base_prompt

agent = create_react_agent(
    model="openai:gpt-4o",
    tools=tools,
    prompt=dynamic_prompt,
    context_schema=Context
)

agent.invoke(
    {"messages": [{"role": "user", "content": "Explain async programming"}]},
    context=Context(user_role="expert")
)
```

### Pre-model hook

Pre-model hook 现在通过中间件的 `before_model` 方法实现，更具扩展性——可以在模型调用前定义多个中间件，复用不同代理的通用模式。

常见用途：

*   对话历史摘要
*   消息裁剪
*   输入安全检查（如 PII 脱敏）

v1 内置了摘要中间件：

```python
from langchain.agents import create_agent
from langchain.agents.middleware import SummarizationMiddleware

agent = create_agent(
    model="anthropic:claude-sonnet-4-5",
    tools=tools,
    middleware=[
        SummarizationMiddleware(
            model="anthropic:claude-sonnet-4-5",
            max_tokens_before_summary=1000
        )
    ]
)
```

旧版本：

```python
from langgraph.prebuilt import create_react_agent, AgentState

def custom_summarization_function(state: AgentState):
    """自定义消息摘要逻辑"""
    ...

agent = create_react_agent(
    model="anthropic:claude-sonnet-4-5",
    tools=tools,
    pre_model_hook=custom_summarization_function
)
```

### Post-model hook

Post-model hook 现在通过中间件的 `after_model` 方法实现，更具扩展性——可以在模型调用后定义多个中间件，复用通用模式。

常见用途：

*   [人工审核](../human-in-the-loop.html)
*   输出安全检查

v1 内置了工具调用的人工审核中间件：

```python
from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware

agent = create_agent(
    model="anthropic:claude-sonnet-4-5",
    tools=[read_email, send_email],
    middleware=[HumanInTheLoopMiddleware(
        interrupt_on={
            "send_email": True,
            "description": "Please review this email before sending"
        },
    )]
)
```

旧版本：

```python
from langgraph.prebuilt import create_react_agent, AgentState

def custom_human_in_the_loop_hook(state: AgentState):
    """自定义人工审核逻辑"""
    ...

agent = create_react_agent(
    model="anthropic:claude-sonnet-4-5",
    tools=[read_email, send_email],
    post_model_hook=custom_human_in_the_loop_hook
)
```

### Custom state

自定义状态用于扩展默认代理状态，可通过两种方式定义：

1.  **通过 [`create_agent`](https://reference.langchain.com/python/langchain/agents/#langchain.agents.create_agent) 的 [`state_schema`](https://reference.langchain.com/python/langchain/middleware/#langchain.agents.middleware.AgentMiddleware.state_schema)** ——适合工具使用的状态
2.  **通过中间件** ——适合由特定中间件钩子和其附加工具管理的状态

> 建议通过中间件定义自定义状态，这样可以将状态扩展限定在相关中间件和工具范围内。`state_schema` 仍支持 `create_agent` 的向后兼容。

#### 通过 `state_schema` 定义状态

当自定义状态需要被工具访问时，可使用 [`state_schema`](https://reference.langchain.com/python/langchain/middleware/#langchain.agents.middleware.AgentMiddleware.state_schema) 参数：

```python
from langchain.tools import tool, ToolRuntime
from langchain.agents import create_agent, AgentState

# 定义扩展 AgentState 的自定义状态
class CustomState(AgentState):
    user_name: str

@tool
def greet(
    runtime: ToolRuntime[CustomState]
) -> str:
    """根据用户姓名问候用户"""
    user_name = runtime.state.get("user_name", "Unknown")
    return f"Hello {user_name}!"

agent = create_agent(
    model="anthropic:claude-sonnet-4-5",
    tools=[greet],
    state_schema=CustomState
)
```

旧版本：

```python
from typing import Annotated
from langgraph.prebuilt import InjectedState, create_react_agent
from langgraph.prebuilt.chat_agent_executor import AgentState

class CustomState(AgentState):
    user_name: str

def greet(
    state: Annotated[CustomState, InjectedState]
) -> str:
    """根据用户姓名问候用户"""
    user_name = state["user_name"]
    return f"Hello {user_name}!"

agent = create_react_agent(
    model="anthropic:claude-sonnet-4-5",
    tools=[greet],
    state_schema=CustomState
)
```

#### 通过中间件定义状态

中间件也可以通过设置 [`state_schema`](https://reference.langchain.com/python/langchain/middleware/#langchain.agents.middleware.AgentMiddleware.state_schema) 属性来定义自定义状态。
这有助于将状态扩展概念上限定在相关的中间件和工具中。

```python
from langchain.agents.middleware import AgentState, AgentMiddleware
from typing_extensions import NotRequired
from typing import Any

class CustomState(AgentState):
    model_call_count: NotRequired[int]

class CallCounterMiddleware(AgentMiddleware[CustomState]):
    state_schema = CustomState  # 定义中间件状态结构

    def before_model(self, state: CustomState, runtime) -> dict[str, Any] | None:
        count = state.get("model_call_count", 0)
        if count > 10:
            return {"jump_to": "end"}
        return None

    def after_model(self, state: CustomState, runtime) -> dict[str, Any] | None:
        return {"model_call_count": state.get("model_call_count", 0) + 1}

agent = create_agent(
    model="anthropic:claude-sonnet-4-5",
    tools=[...],
    middleware=[CallCounterMiddleware()]  # 应用中间件
)
```

更多关于通过中间件定义自定义状态的细节请参阅 [中间件文档](../middleware.html#custom-state-schema)。

#### 状态类型限制

[`create_agent`](https://reference.langchain.com/python/langchain/agents/#langchain.agents.create_agent) 仅支持 `TypedDict` 作为状态 schema，不再支持 Pydantic 模型或 dataclass。

```python
# v1 新版
from langchain.agents import AgentState, create_agent

# AgentState 是 TypedDict
class CustomAgentState(AgentState):
    user_id: str

agent = create_agent(
    model="anthropic:claude-sonnet-4-5",
    tools=tools,
    state_schema=CustomAgentState  # 使用自定义状态
)
```

```python
# v0 旧版
from typing_extensions import Annotated
from pydantic import BaseModel
from langgraph.graph import StateGraph
from langgraph.graph.messages import add_messages
from langchain_core.messages import AnyMessage

class AgentState(BaseModel):
    messages: Annotated[list[AnyMessage], add_messages]
    user_id: str

agent = create_react_agent(
    model="anthropic:claude-sonnet-4-5",
    tools=tools,
    state_schema=AgentState
)
```

只需继承 `langchain.agents.AgentState` 而不是 `BaseModel` 或使用 `dataclass` 装饰器即可。
如果需要验证，请在中间件钩子中处理。

---

### 模型

动态模型选择允许根据运行时上下文选择不同模型（例如任务复杂度、成本限制或用户偏好）。
[`create_react_agent`](https://reference.langchain.com/python/langgraph/prebuilt/#langgraph.prebuilt.chat_agent_executor.create_react_agent) 在 v0.6 的 [`langgraph-prebuilt`](https://pypi.org/project/langgraph-prebuilt) 中支持通过传入可调用对象选择动态模型和工具。
该功能在 v1 中已迁移至中间件接口。

#### 动态模型选择

```python
# v1 新版
from langchain.agents import create_agent
from langchain.agents.middleware import AgentMiddleware, ModelRequest, ModelRequestHandler
from langchain.messages import AIMessage
from langchain_openai import ChatOpenAI

basic_model = ChatOpenAI(model="gpt-5-nano")
advanced_model = ChatOpenAI(model="gpt-5")

class DynamicModelMiddleware(AgentMiddleware):
    def wrap_model_call(self, request: ModelRequest, handler: ModelRequestHandler) -> AIMessage:
        if len(request.state.messages) > self.messages_threshold:
            model = advanced_model
        else:
            model = basic_model
        return handler(request.replace(model=model))

    def __init__(self, messages_threshold: int) -> None:
        self.messages_threshold = messages_threshold

agent = create_agent(
    model=basic_model,
    tools=tools,
    middleware=[DynamicModelMiddleware(messages_threshold=10)]
)
```

```python
# v0 旧版
from langgraph.prebuilt import create_react_agent, AgentState
from langchain_openai import ChatOpenAI

basic_model = ChatOpenAI(model="gpt-5-nano")
advanced_model = ChatOpenAI(model="gpt-5")

def select_model(state: AgentState) -> BaseChatModel:
    if len(state.messages) > 10:
        return advanced_model
    return basic_model

agent = create_react_agent(
    model=select_model,
    tools=tools,
)
```

#### 预绑定模型

为了更好地支持结构化输出，[`create_agent`](https://reference.langchain.com/python/langchain/agents/#langchain.agents.create_agent) 不再接受带有工具或配置的预绑定模型。

```python
# 不再支持
model_with_tools = ChatOpenAI().bind_tools([some_tool])
agent = create_agent(model_with_tools, tools=[])
# 正确用法
agent = create_agent("openai:gpt-4o-mini", tools=[some_tool])
```

> 动态模型函数如果不使用结构化输出，可以返回预绑定模型。

---

### 工具

[`create_agent`](https://reference.langchain.com/python/langchain/agents/#langchain.agents.create_agent) 的 `tools` 参数接受：

*   LangChain [`BaseTool`](https://reference.langchain.com/python/langchain/tools/#langchain.tools.BaseTool) 实例（使用 [`@tool`](https://reference.langchain.com/python/langchain/tools/#langchain.tools.tool) 装饰的函数）
*   带有类型提示和 docstring 的可调用对象
*   表示内置提供商工具的 `dict`

不再接受 [`ToolNode`](https://reference.langchain.com/python/langgraph/agents/#langgraph.prebuilt.tool_node.ToolNode) 实例。

```python
# v1 新版
from langchain.agents import create_agent
agent = create_agent(
    model="anthropic:claude-sonnet-4-5",
    tools=[check_weather, search_web]
)
```

```python
# v0 旧版
from langgraph.prebuilt import create_react_agent, ToolNode
agent = create_react_agent(
    model="anthropic:claude-sonnet-4-5",
    tools=ToolNode([check_weather, search_web])
)
```

#### 工具错误处理

现在可以通过中间件实现 `wrap_tool_call` 方法来配置工具错误处理。

```python
# v1 新版
# 示例稍后提供
```

```python
# v0 旧版
# 示例稍后提供
```

---

### 结构化输出

#### 节点变化

结构化输出不再在主智能体之外生成单独节点，而是在主循环中生成，降低成本和延迟。

#### 工具与提供商策略

v1 提供两种结构化输出策略：

*   `ToolStrategy`：通过人工调用工具生成结构化输出
*   `ProviderStrategy`：通过提供商原生方式生成结构化输出

```python
# v1 新版
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy, ProviderStrategy
from pydantic import BaseModel

class OutputSchema(BaseModel):
    summary: str
    sentiment: str

# 使用 ToolStrategy
agent = create_agent(
    model="openai:gpt-4o-mini",
    tools=tools,
    response_format=ToolStrategy(OutputSchema)
)
```

```python
# v0 旧版
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel

class OutputSchema(BaseModel):
    summary: str
    sentiment: str

agent = create_react_agent(
    model="openai:gpt-4o-mini",
    tools=tools,
    response_format=OutputSchema
)
# 或者使用自定义提示生成输出结构
agent = create_react_agent(
    model="openai:gpt-4o-mini",
    tools=tools,
    response_format=("please generate ...", OutputSchema)
)
```

#### Prompt 输出移除

不再通过 `response_format` 支持 **prompt 输出**，相比人工工具调用和提供商原生结构化输出，prompt 输出不够稳定。

---

### 流式节点名称更改

流式事件节点名称从 `"agent"` 改为 `"model"`，更准确反映节点用途。

---

### 运行时上下文

调用智能体时通常需要传递两类数据：

*   动态状态：会随对话变化（如消息历史）
*   静态上下文：在对话中不变（如用户元数据）

v1 通过在 `invoke` 和 `stream` 方法中设置 `context` 参数支持静态上下文。

```python
# v1 新版
from dataclasses import dataclass
from langchain.agents import create_agent

@dataclass
class Context:
    user_id: str
    session_id: str

agent = create_agent(
    model=model,
    tools=tools,
    context_schema=ContextSchema
)

result = agent.invoke(
    {"messages": [{"role": "user", "content": "Hello"}]},
    context=Context(user_id="123", session_id="abc")
)
```

```python
# v0 旧版
from langgraph.prebuilt import create_react_agent

agent = create_react_agent(model, tools)
# 通过配置传递上下文
result = agent.invoke(
    {"messages": [{"role": "user", "content": "Hello"}]},
    config={
        "configurable": {
            "user_id": "123",
            "session_id": "abc"
        }
    }
)
```

> 旧的 `config["configurable"]` 模式仍可兼容，但推荐使用新的 `context` 参数。

---

## 标准内容

v1 中，消息支持供应商无关的标准内容块，可通过 `@[`message.content_blocks`]` 访问，以获得跨供应商一致、类型化的视图。
现有的 [`message.content`](https://reference.langchain.com/python/langchain_core/language_models/#langchain_core.messages.BaseMessage.content_blocks) 字段仍然保留用于字符串或供应商原生结构。

### 变化内容

*   消息新增 [`content_blocks`](https://reference.langchain.com/python/langchain_core/language_models/#langchain_core.messages.BaseMessage.content_blocks) 属性，用于规范化内容
*   标准块结构已统一，文档见 [Messages](../messages.html#standard-content-blocks)
*   可选将标准块序列化到 `content`，通过 `LC_OUTPUT_VERSION=v1` 或 `output_version="v1"` 实现

### 读取标准化内容

```python
# v1 新版
from langchain.chat_models import init_chat_model

model = init_chat_model("openai:gpt-5-nano")
response = model.invoke("解释 AI")

for block in response.content_blocks:
    if block["type"] == "reasoning":
        print(block.get("reasoning"))
    elif block["type"] == "text":
        print(block.get("text"))
```

```python
# v0 旧版
# 各供应商的原生格式不同，需要针对不同提供商处理
response = model.invoke("解释 AI")
for item in response.content:
    if item.get("type") == "reasoning":
        ...  # OpenAI 风格的推理
    elif item.get("type") == "thinking":
        ...  # Anthropic 风格的思考
    elif item.get("type") == "text":
        ...  # 文本
```

### 创建多模态消息

```python
# v1 新版
from langchain.messages import HumanMessage

message = HumanMessage(content_blocks=[
    {"type": "text", "text": "描述这张图片。"},
    {"type": "image", "url": "https://example.com/image.jpg"},
])
res = model.invoke([message])
```

```python
# v0 旧版
from langchain.messages import HumanMessage

message = HumanMessage(content=[
    # 供应商原生结构
    {"type": "text", "text": "描述这张图片。"},
    {"type": "image_url", "image_url": {"url": "https://example.com/image.jpg"}},
])
res = model.invoke([message])
```

### 示例内容块结构

```python
# 文本块
text_block = {
    "type": "text",
    "text": "你好，世界",
}
# 图片块
image_block = {
    "type": "image",
    "url": "https://example.com/image.png",
    "mime_type": "image/png",
}
```

更多内容块详情请参阅 [内容块参考](../messages.html#content-block-reference)。

### 序列化标准内容

标准内容块默认**不会序列化**到 `content` 属性中。如果需要在 `content` 属性中访问标准内容块（例如发送给客户端时），可以选择将它们序列化。

```bash
# 设置环境变量序列化标准内容块
export LC_OUTPUT_VERSION=v1
```

```python
# 初始化参数序列化
from langchain.chat_models import init_chat_model

model = init_chat_model(
    "openai:gpt-5-nano",
    output_version="v1",
)
```

更多信息请查看：[消息内容](../messages.html#message-content)、[标准内容块](../messages.html#standard-content-blocks) 和 [多模态](../messages.html#multimodal)。

## 精简包

在 v1 中，`langchain` 包的命名空间大幅精简，专注于智能体的核心构建模块，使核心功能更易于发现和使用。

### 命名空间

| 模块 | 可用内容 | 说明 |
| :--- | :--- | :--- |
| [`langchain.agents`](https://reference.langchain.com/python/langchain/agents) | [`create_agent`](https://reference.langchain.com/python/langchain/agents/#langchain.agents.create_agent)、[`AgentState`](https://reference.langchain.com/python/langchain/agents/#langchain.agents.AgentState) | 核心智能体创建功能 |
| [`langchain.messages`](https://reference.langchain.com/python/langchain/messages) | 消息类型、[内容块](https://reference.langchain.com/python/langchain/messages/#langchain.messages.ContentBlock)、[`trim_messages`](https://reference.langchain.com/python/langchain/messages/#langchain.messages.trim_messages) | 从 `langchain-core` 重新导出 |
| [`langchain.tools`](https://reference.langchain.com/python/langchain/tools) | [`@tool`](https://reference.langchain.com/python/langchain/tools/#langchain.tools.tool)、[`BaseTool`](https://reference.langchain.com/python/langchain/tools/#langchain.tools.BaseTool)、注入助手 | 从 `langchain-core` 重新导出 |
| [`langchain.chat_models`](https://reference.langchain.com/python/langchain/models) | [`init_chat_model`](https://reference.langchain.com/python/langchain/models/#langchain.chat_models.init_chat_model)、[`BaseChatModel`](https://reference.langchain.com/python/langchain_core/language_models/#langchain_core.language_models.chat_models.BaseChatModel) | 统一模型初始化 |
| [`langchain.embeddings`](https://reference.langchain.com/python/langchain/embeddings) | [`init_embeddings`](https://reference.langchain.com/python/langchain_core/embeddings/#langchain_core.embeddings.embeddings.Embeddings)、[`Embeddings`](https://reference.langchain.com/python/langchain_core/embeddings/#langchain_core.embeddings.embeddings.Embeddings) | 嵌入模型 |

### `langchain-classic`

如果你在 `langchain` 中使用以下功能，需要安装 [`langchain-classic`](https://pypi.org/project/langchain-classic/) 并更新导入：

*   旧链条（`LLMChain`、`ConversationChain` 等）
*   检索器（如 `MultiQueryRetriever` 或旧的 `langchain.retrievers` 模块）
*   索引 API
*   Hub 模块（程序化管理 prompts）
*   嵌入模块（如 `CacheBackedEmbeddings` 和社区 embeddings）
*   [`langchain-community`](https://pypi.org/project/langchain-community) 重新导出
*   其他弃用功能

```python
# v1 新版
# 链条
from langchain_classic.chains import LLMChain
# 检索器
from langchain_classic.retrievers import ...
# 索引
from langchain_classic.indexes import ...
# Hub
from langchain_classic import hub
```

```python
# v0 旧版
# 链条
from langchain.chains import LLMChain
# 检索器
from langchain.retrievers import ...
# 索引
from langchain.indexes import ...
# Hub
from langchain import hub
```

**安装方式**：

```bash
pip install langchain-classic
```

## 破坏性变更

### 不再支持 Python 3.9

所有 LangChain 包现在要求 **Python 3.10 或更高版本**。Python 3.9 将在 2025 年 10 月达到 [生命周期终止](https://devguide.python.org/versions/)。

### 聊天模型返回类型更新

聊天模型返回类型从 [`BaseMessage`](https://reference.langchain.com/python/langchain_core/language_models/#langchain_core.messages.BaseMessage) 改为 [`AIMessage`](https://reference.langchain.com/python/langchain/messages/#langchain.messages.AIMessage)。

```python
# v1 新版
def bind_tools(
        ...
    ) -> Runnable[LanguageModelInput, AIMessage]:
```

```python
# v0 旧版
def bind_tools(
        ...
    ) -> Runnable[LanguageModelInput, BaseMessage]:
```

### OpenAI Responses API 默认消息格式

`langchain-openai` 现在默认将响应项存储在消息 `content` 中。要恢复旧行为，可设置环境变量 `LC_OUTPUT_VERSION=v0`，或在实例化 [`ChatOpenAI`](https://reference.langchain.com/python/integrations/langchain_openai/ChatOpenAI/) 时指定 `output_version="v0"`。

```python
# 恢复旧行为
model = ChatOpenAI(model="gpt-4o-mini", output_version="v0")
```

### `langchain-anthropic` 默认 `max_tokens`

默认 `max_tokens` 值根据模型调整，而不再是 1024。如需旧默认，请显式设置 `max_tokens=1024`。

### 旧功能移至 `langchain-classic`

核心接口与智能体以外的功能已移至 [`langchain-classic`](https://pypi.org/project/langchain-classic)。

### 弃用 API 移除

所有已弃用的方法、函数和对象已删除，请查看 [弃用通知](https://python.langchain.com/docs/versions/migrating_chains) 获取替代 API。

### `.text()` 方法改为属性

```python
# 属性访问
text = response.text
# 旧方法调用（已弃用）
text = response.text()
```

旧用法仍可工作，但会发出警告。