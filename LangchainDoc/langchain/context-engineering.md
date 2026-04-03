# 智能体中的上下文工程

## 概述 (Overview)

构建代理（或任何大型语言模型应用程序）的**难点在于使其足够可靠**。尽管它们可能适用于原型，但在实际用例中却经常失败。

### 为什么代理会失败？ (Why do agents fail?)

当代理失败时，通常是因为代理内部的大型语言模型（LLM）调用采取了**错误的行动**或**没有达到我们的预期**。LLM 失败的原因有两个：

1. 底层 **LLM 的能力不足**
2. **没有将“正确的”上下文**传递给 LLM

通常情况下，代理不可靠的**首要原因**实际上是第二个。

**上下文工程（Context engineering）就是以正确的格式提供正确的信息和工具**，以便 LLM 能够完成任务。这是 **AI 工程师的头号工作**。这种缺乏“正确”上下文的情况是提高代理可靠性的**最大障碍**，而 LangChain 的代理抽象设计独特，正是为了促进上下文工程。

> **提示：** 对上下文工程不熟悉？请从[概念性概述](https://langchain-doc.cn/v1/python/concepts/context)开始，了解不同类型的上下文及其使用时机。

### 代理循环 (The agent loop)

一个典型的代理循环包括两个主要步骤：

1. **模型调用（Model call）**- 用提示（prompt）和可用工具调用 LLM，返回一个响应或一个执行工具的请求
2. **工具执行（Tool execution）** - 执行 LLM 请求的工具，返回工具结果

这个循环会一直持续，直到 LLM 决定结束。

## 你可以控制什么 (What you can control)

为了构建可靠的代理，你需要控制代理循环的每个步骤中发生的事情，以及步骤之间发生的事情。

| 上下文类型 | 你控制的内容 | 瞬态（Transient）还是持久性（Persistent） |
| :--- | :--- | :--- |
| **[模型上下文](#model-context)** | 进入模型调用的内容（指令、消息历史、工具、响应格式） | 瞬态 |
| **[工具上下文](#tool-context)** | 工具可以访问和产生的内容（对状态、存储、运行时上下文的读/写） | 持久性 |
| **[生命周期上下文](#life-cycle-context)** | 模型调用和工具调用之间发生的内容（摘要、安全防护、日志记录等） | 持久性 |

### 数据源 (Data sources)

在整个过程中，你的代理会访问（读取/写入）不同的数据源：

| 数据源 | 别名 | 范围 | 示例 |
| :--- | :--- | :--- | :--- |
| **运行时上下文 (Runtime Context)** | 静态配置 | 会话范围 | 用户 ID、API 密钥、数据库连接、权限、环境设置 |
| **状态 (State)** | 短期记忆 | 会话范围 | 当前消息、已上传文件、认证状态、工具结果 |
| **存储 (Store)** | 长期记忆 | 跨会话 | 用户偏好、提取的见解、记忆、历史数据 |

### 工作原理 (How it works)

LangChain 的[中间件](middleware.html)是底层机制，它使得使用 LangChain 的开发者能够实际进行上下文工程。

中间件允许你**挂接到**代理生命周期中的任何步骤，并执行以下操作：

- **更新上下文**
- **跳转到**代理生命周期中的不同步骤

在整个指南中，你会频繁看到中间件 API 作为实现上下文工程的手段被使用。

## 模型上下文 (Model Context)

控制每次模型调用中包含的内容——指令、可用工具、使用的模型和输出格式。这些决策直接影响可靠性和成本。

- **[系统提示](#system-prompt)**
  开发者提供给 LLM 的基本指令。
- **[消息](#messages)**
  发送给 LLM 的完整消息列表（对话历史）。
- **[工具](#tools)**
  代理可用于执行操作的实用程序。
- **[模型](#model)**
  实际被调用的模型（包括配置）。
- **[响应格式](#response-format)**
  模型最终响应的模式规范。

所有这些类型的模型上下文都可以从**状态**（短期记忆）、**存储**（长期记忆）或**运行时上下文**（静态配置）中获取。

### 系统提示 (System Prompt)

系统提示设置了 LLM 的行为和能力。不同的用户、上下文或会话阶段需要不同的指令。成功的代理会利用记忆、偏好和配置，为当前的会话状态提供正确的指令。

#### 状态 (State)

从状态中访问消息计数或会话上下文：

```python
from langchain.agents import create_agent
from langchain.agents.middleware import dynamic_prompt, ModelRequest
@dynamic_prompt
def state_aware_prompt(request: ModelRequest) -> str:
    # request.messages 是 request.state["messages"] 的快捷方式
    message_count = len(request.messages)
    base = "You are a helpful assistant."
    if message_count > 10:
        base += "\nThis is a long conversation - be extra concise."
    return base
agent = create_agent(
    model="openai:gpt-4o",
    tools=[...],
    middleware=[state_aware_prompt]
)
```

#### 存储 (Store)

从长期记忆中访问用户偏好：

```python
from dataclasses import dataclass
from langchain.agents import create_agent
from langchain.agents.middleware import dynamic_prompt, ModelRequest
from langgraph.store.memory import InMemoryStore
@dataclass
class Context:
    user_id: str
@dynamic_prompt
def store_aware_prompt(request: ModelRequest) -> str:
    user_id = request.runtime.context.user_id
    # 从 Store 读取：获取用户偏好
    store = request.runtime.store
    user_prefs = store.get(("preferences",), user_id)
    base = "You are a helpful assistant."
    if user_prefs:
        style = user_prefs.value.get("communication_style", "balanced")
        base += f"\nUser prefers {style} responses."
    return base
agent = create_agent(
    model="openai:gpt-4o",
    tools=[...],
    middleware=[store_aware_prompt],
    context_schema=Context,
    store=InMemoryStore()
)
```

#### 运行时上下文 (Runtime Context)

从运行时上下文中访问用户 ID 或配置：

```python
from dataclasses import dataclass
from langchain.agents import create_agent
from langchain.agents.middleware import dynamic_prompt, ModelRequest
@dataclass
class Context:
    user_role: str
    deployment_env: str
@dynamic_prompt
def context_aware_prompt(request: ModelRequest) -> str:
    # 从 Runtime Context 读取：用户角色和环境
    user_role = request.runtime.context.user_role
    env = request.runtime.context.deployment_env
    base = "You are a helpful assistant."
    if user_role == "admin":
        base += "\nYou have admin access. You can perform all operations."
    elif user_role == "viewer":
        base += "\nYou have read-only access. Guide users to read operations only."
    if env == "production":
        base += "\nBe extra careful with any data modifications."
    return base
agent = create_agent(
    model="openai:gpt-4o",
    tools=[...],
    middleware=[context_aware_prompt],
    context_schema=Context
)
```

### 消息 (Messages)

消息构成了发送给 LLM 的提示。**管理消息内容**至关重要，以确保 LLM 拥有正确的信息来做出良好响应。

#### 状态 (State)

当与当前查询相关时，从状态中注入已上传文件上下文：

```python
from langchain.agents import create_agent
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from typing import Callable
@wrap_model_call
def inject_file_context(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse]
) -> ModelResponse:
    """Inject context about files user has uploaded this session."""
    # 从 State 读取：获取已上传文件的元数据
    uploaded_files = request.state.get("uploaded_files", [])
    if uploaded_files:
        # 构建关于可用文件的上下文
        file_descriptions = []
        for file in uploaded_files:
            file_descriptions.append(
                f"- {file['name']} ({file['type']}): {file['summary']}"
            )
        file_context = f"""Files you have access to in this conversation:
    {chr(10).join(file_descriptions)}
    Reference these files when answering questions."""
        # 在最新消息之前注入文件上下文
        messages = [
            *request.messages,
            {"role": "user", "content": file_context},
        ]
        request = request.override(messages=messages)
    return handler(request)
agent = create_agent(
    model="openai:gpt-4o",
    tools=[...],
    middleware=[inject_file_context]
)
```

#### 存储 (Store)

从存储中注入用户的电子邮件写作风格以指导起草：

```python
from dataclasses import dataclass
from langchain.agents import create_agent
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from typing import Callable
from langgraph.store.memory import InMemoryStore
@dataclass
class Context:
    user_id: str
@wrap_model_call
def inject_writing_style(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse]
) -> ModelResponse:
    """Inject user's email writing style from Store."""
    user_id = request.runtime.context.user_id
    # 从 Store 读取：获取用户的写作风格示例
    store = request.runtime.store
    writing_style = store.get(("writing_style",), user_id)
    if writing_style:
        style = writing_style.value
        # 从存储的示例构建风格指南
        style_context = f"""Your writing style:
    - Tone: {style.get('tone', 'professional')}
    - Typical greeting: "{style.get('greeting', 'Hi')}"
    - Typical sign-off: "{style.get('sign_off', 'Best')}"
    - Example email you've written:
    {style.get('example_email', '')}"""
        # 附加到末尾 - 模型对最后的消息更关注
        messages = [
            *request.messages,
            {"role": "user", "content": style_context}
        ]
        request = request.override(messages=messages)
    return handler(request)
agent = create_agent(
    model="openai:gpt-4o",
    tools=[...],
    middleware=[inject_writing_style],
    context_schema=Context,
    store=InMemoryStore()
)
```

#### 运行时上下文 (Runtime Context)

根据用户的管辖范围，从运行时上下文中注入合规规则：

```python
from dataclasses import dataclass
from langchain.agents import create_agent
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from typing import Callable
@dataclass
class Context:
    user_jurisdiction: str
    industry: str
    compliance_frameworks: list[str]
@wrap_model_call
def inject_compliance_rules(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse]
) -> ModelResponse:
    """Inject compliance constraints from Runtime Context."""
    # 从 Runtime Context 读取：获取合规性要求
    jurisdiction = request.runtime.context.user_jurisdiction
    industry = request.runtime.context.industry
    frameworks = request.runtime.context.compliance_frameworks
    # 构建合规性约束
    rules = []
    if "GDPR" in frameworks:
        rules.append("- Must obtain explicit consent before processing personal data")
        rules.append("- Users have right to data deletion")
    if "HIPAA" in frameworks:
        rules.append("- Cannot share patient health information without authorization")
        rules.append("- Must use secure, encrypted communication")
    if industry == "finance":
        rules.append("- Cannot provide financial advice without proper disclaimers")
    if rules:
        compliance_context = f"""Compliance requirements for {jurisdiction}:
    {chr(10).join(rules)}"""
        # 附加到末尾 - 模型对最后的消息更关注
        messages = [
            *request.messages,
            {"role": "user", "content": compliance_context}
        ]
        request = request.override(messages=messages)
    return handler(request)
agent = create_agent(
    model="openai:gpt-4o",
    tools=[...],
    middleware=[inject_compliance_rules],
    context_schema=Context
)
```

> **注意：瞬态与持久性消息更新：**
>
> 上述示例使用 `wrap_model_call` 进行**瞬态**更新——修改发送给模型的单次调用消息，而**不更改**状态中保存的内容。
>
> 对于修改状态的**持久性**更新（例如[生命周期上下文](#summarization)中的摘要示例），请使用 `before_model` 或 `after_model` 等生命周期钩子来**永久**更新对话历史记录。有关更多详细信息，请参阅[中间件文档](middleware.html)。

### 工具 (Tools)

工具允许模型与数据库、API 和外部系统交互。你定义和选择工具的方式直接影响模型是否能有效完成任务。

#### 定义工具 (Defining tools)

每个工具都需要一个清晰的名称、描述、参数名称和参数描述。这些不仅仅是元数据——它们指导模型关于何时以及如何使用工具的推理。

```python
from langchain.tools import tool
@tool(parse_docstring=True)
def search_orders(
    user_id: str,
    status: str,
    limit: int = 10
) -> str:
    """Search for user orders by status.
    Use this when the user asks about order history or wants to check
    order status. Always filter by the provided status.
    Args:
        user_id: Unique identifier for the user
        status: Order status: 'pending', 'shipped', or 'delivered'
        limit: Maximum number of results to return
    """
    # Implementation here
    pass
```

好的，这是将您的内容转换为**标准 Markdown (MD)** 语法并**翻译成中文**的结果。

## 选择工具

并非所有工具都适用于所有情况。**过多的工具**可能会使模型不堪重负（上下文过载）并增加错误；**过少的工具**则会限制其能力。**动态工具选择**根据身份验证状态、用户权限、功能标志或对话阶段来调整可用的工具集。

### 状态 (State)

仅在达到特定的对话里程碑后才启用高级工具：

```python
from langchain.agents import create_agent
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from typing import Callable
@wrap_model_call
def state_based_tools(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse]
) -> ModelResponse:
    """Filter tools based on conversation State."""
    # Read from State: check if user has authenticated
    state = request.state  # [!code highlight]
    is_authenticated = state.get("authenticated", False)  # [!code highlight]
    message_count = len(state["messages"])
    # Only enable sensitive tools after authentication
    if not is_authenticated:
        tools = [t for t in request.tools if t.name.startswith("public_")]
        request = request.override(tools=tools)  # [!code highlight]
    elif message_count < 5:
        # Limit tools early in conversation
        tools = [t for t in request.tools if t.name != "advanced_search"]
        request = request.override(tools=tools)  # [!code highlight]
    return handler(request)
agent = create_agent(
    model="openai:gpt-4o",
    tools=[public_search, private_search, advanced_search],
    middleware=[state_based_tools]
)
```

### 存储 (Store)

根据存储中的**用户偏好**或**功能标志**来过滤工具：

```python
from dataclasses import dataclass
from langchain.agents import create_agent
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from typing import Callable
from langgraph.store.memory import InMemoryStore
@dataclass
class Context:
    user_id: str
@wrap_model_call
def store_based_tools(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse]
) -> ModelResponse:
    """Filter tools based on Store preferences."""
    user_id = request.runtime.context.user_id
    # Read from Store: get user's enabled features
    store = request.runtime.store
    feature_flags = store.get(("features",), user_id)
    if feature_flags:
        enabled_features = feature_flags.value.get("enabled_tools", [])
        # Only include tools that are enabled for this user
        tools = [t for t in request.tools if t.name in enabled_features]
        request = request.override(tools=tools)
    return handler(request)
agent = create_agent(
    model="openai:gpt-4o",
    tools=[search_tool, analysis_tool, export_tool],
    middleware=[store_based_tools],
    context_schema=Context,
    store=InMemoryStore()
)
```

### 运行时上下文 (Runtime Context)

根据运行时上下文中的**用户权限**来过滤工具：

```python
from dataclasses import dataclass
from langchain.agents import create_agent
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from typing import Callable
@dataclass
class Context:
    user_role: str
@wrap_model_call
def context_based_tools(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse]
) -> ModelResponse:
    """Filter tools based on Runtime Context permissions."""
    # Read from Runtime Context: get user role
    user_role = request.runtime.context.user_role
    if user_role == "admin":
        # Admins get all tools
        pass
    elif user_role == "editor":
        # Editors can't delete
        tools = [t for t in request.tools if t.name != "delete_data"]
        request = request.override(tools=tools)
    else:
        # Viewers get read-only tools
        tools = [t for t in request.tools if t.name.startswith("read_")]
        request = request.override(tools=tools)
    return handler(request)
agent = create_agent(
    model="openai:gpt-4o",
    tools=[read_data, write_data, delete_data],
    middleware=[context_based_tools],
    context_schema=Context
)
```

有关更多示例，请参阅 [动态选择工具 (Dynamically selecting tools)](middleware.html#dynamically-selecting-tools)。

## 模型 (Model)

不同的模型具有不同的**优势**、**成本**和**上下文窗口**。为手头的任务选择合适的模型，这可能会在代理运行期间发生变化。

### 状态 (State)

根据状态中**对话的长度**使用不同的模型：

```python
from langchain.agents import create_agent
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from langchain.chat_models import init_chat_model
from typing import Callable
# Initialize models once outside the middleware
large_model = init_chat_model("anthropic:claude-sonnet-4-5")
standard_model = init_chat_model("openai:gpt-4o")
efficient_model = init_chat_model("openai:gpt-4o-mini")
@wrap_model_call
def state_based_model(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse]
) -> ModelResponse:
    """Select model based on State conversation length."""
    # request.messages is a shortcut for request.state["messages"]
    message_count = len(request.messages)  # [!code highlight]
    if message_count > 20:
        # Long conversation - use model with larger context window
        model = large_model
    elif message_count > 10:
        # Medium conversation
        model = standard_model
    else:
        # Short conversation - use efficient model
        model = efficient_model
    request = request.override(model=model)  # [!code highlight]
    return handler(request)
agent = create_agent(
    model="openai:gpt-4o-mini",
    tools=[...],
    middleware=[state_based_model]
)
```

### 存储 (Store)

使用存储中**用户首选的模型**：

```python
from dataclasses import dataclass
from langchain.agents import create_agent
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from langchain.chat_models import init_chat_model
from typing import Callable
from langgraph.store.memory import InMemoryStore
@dataclass
class Context:
    user_id: str
# Initialize available models once
MODEL_MAP = {
    "gpt-4o": init_chat_model("openai:gpt-4o"),
    "gpt-4o-mini": init_chat_model("openai:gpt-4o-mini"),
    "claude-sonnet": init_chat_model("anthropic:claude-sonnet-4-5"),
}
@wrap_model_call
def store_based_model(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse]
) -> ModelResponse:
    """Select model based on Store preferences."""
    user_id = request.runtime.context.user_id
    # Read from Store: get user's preferred model
    store = request.runtime.store
    user_prefs = store.get(("preferences",), user_id)
    if user_prefs:
        preferred_model = user_prefs.value.get("preferred_model")
        if preferred_model and preferred_model in MODEL_MAP:
            request = request.override(model=MODEL_MAP[preferred_model])
    return handler(request)
agent = create_agent(
    model="openai:gpt-4o",
    tools=[...],
    middleware=[store_based_model],
    context_schema=Context,
    store=InMemoryStore()
)
```

### 运行时上下文 (Runtime Context)

根据运行时上下文中的**成本限制**或**环境**选择模型：

```python
from dataclasses import dataclass
from langchain.agents import create_agent
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from langchain.chat_models import init_chat_model
from typing import Callable
@dataclass
class Context:
    cost_tier: str
    environment: str
# Initialize models once outside the middleware
premium_model = init_chat_model("anthropic:claude-sonnet-4-5")
standard_model = init_chat_model("openai:gpt-4o")
budget_model = init_chat_model("openai:gpt-4o-mini")
@wrap_model_call
def context_based_model(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse]
) -> ModelResponse:
    """Select model based on Runtime Context."""
    # Read from Runtime Context: cost tier and environment
    cost_tier = request.runtime.context.cost_tier
    environment = request.runtime.context.environment
    if environment == "production" and cost_tier == "premium":
        # Production premium users get best model
        model = premium_model
    elif cost_tier == "budget":
        # Budget tier gets efficient model
        model = budget_model
    else:
        # Standard tier
        model = standard_model
    request = request.override(model=model)
    return handler(request)
agent = create_agent(
    model="openai:gpt-4o",
    tools=[...],
    middleware=[context_based_model],
    context_schema=Context
)
```

有关更多示例，请参阅 [动态模型 (Dynamic model)](agents.html#dynamic-model)。

## 响应格式 (Response Format)

**结构化输出**将非结构化文本转换为经过验证的结构化数据。当需要提取特定字段或为下游系统返回数据时，自由格式的文本是不够的。

**工作原理：** 当您提供一个 **schema** 作为响应格式时，模型的最终响应将保证符合该 schema。代理会运行模型/工具调用循环，直到模型完成工具调用，然后将最终响应强制转换为所提供的格式。

### 定义格式

Schema 定义用于指导模型。字段名称、类型和描述精确指定了输出应遵循的格式。

```python
from pydantic import BaseModel, Field
class CustomerSupportTicket(BaseModel):
    """Structured ticket information extracted from customer message."""
    category: str = Field(
        description="Issue category: 'billing', 'technical', 'account', or 'product'"
    )
    priority: str = Field(
        description="Urgency level: 'low', 'medium', 'high', or 'critical'"
    )
    summary: str = Field(
        description="One-sentence summary of the customer's issue"
    )
    customer_sentiment: str = Field(
        description="Customer's emotional tone: 'frustrated', 'neutral', or 'satisfied'"
    )
```

好的，这是将您的内容转换为标准 Markdown 格式并翻译成中文的结果。由于原文中的 `<Tabs>`、`<Tab>`、`[!code highlight]`、`<Note>`、`<Callout>`、`<Tip>` 标签以及图片居中和尺寸控制的 HTML/JSX/Docusaurus 语法无法直接转换为纯粹的标准 Markdown，我将它们替换为最接近的标准 Markdown 结构（如代码块、引用块、列表等）。

## 格式选择（Selecting formats）

动态响应格式选择会根据**用户偏好**、**对话阶段**或**角色**来调整模式（schema）——在早期返回简单格式，在复杂性增加时返回详细格式。

### 状态（State）

配置基于对话**状态**的结构化输出：

```python
from langchain.agents import create_agent
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from pydantic import BaseModel, Field
from typing import Callable
class SimpleResponse(BaseModel):
    """Simple response for early conversation."""
    answer: str = Field(description="A brief answer")
class DetailedResponse(BaseModel):
    """Detailed response for established conversation."""
    answer: str = Field(description="A detailed answer")
    reasoning: str = Field(description="Explanation of reasoning")
    confidence: float = Field(description="Confidence score 0-1")
@wrap_model_call
def state_based_output(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse]
) -> ModelResponse:
    """Select output format based on State."""
    # request.messages is a shortcut for request.state["messages"]
    message_count = len(request.messages)  # 高亮
    if message_count < 3:
        # Early conversation - use simple format
        request = request.override(response_format=SimpleResponse)  # 高亮
    else:
        # Established conversation - use detailed format
        request = request.override(response_format=DetailedResponse)  # 高亮
    return handler(request)
agent = create_agent(
    model="openai:gpt-4o",
    tools=[...],
    middleware=[state_based_output]
)
```

### 存储（Store）

配置基于 Store 中**用户偏好**的输出格式：

```python
from dataclasses import dataclass
from langchain.agents import create_agent
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from pydantic import BaseModel, Field
from typing import Callable
from langgraph.store.memory import InMemoryStore
@dataclass
class Context:
    user_id: str
class VerboseResponse(BaseModel):
    """Verbose response with details."""
    answer: str = Field(description="Detailed answer")
    sources: list[str] = Field(description="Sources used")
class ConciseResponse(BaseModel):
    """Concise response."""
    answer: str = Field(description="Brief answer")
@wrap_model_call
def store_based_output(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse]
) -> ModelResponse:
    """Select output format based on Store preferences."""
    user_id = request.runtime.context.user_id
    # Read from Store: get user's preferred response style
    store = request.runtime.store
    user_prefs = store.get(("preferences",), user_id)
    if user_prefs:
        style = user_prefs.value.get("response_style", "concise")
        if style == "verbose":
            request = request.override(response_format=VerboseResponse)
        else:
            request = request.override(response_format=ConciseResponse)
    return handler(request)
agent = create_agent(
    model="openai:gpt-4o",
    tools=[...],
    middleware=[store_based_output],
    context_schema=Context,
    store=InMemoryStore()
)
```

### 运行时上下文（Runtime Context）

配置基于运行时上下文（例如**用户角色**或**环境**）的输出格式：

```python
from dataclasses import dataclass
from langchain.agents import create_agent
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from pydantic import BaseModel, Field
from typing import Callable
@dataclass
class Context:
    user_role: str
    environment: str
class AdminResponse(BaseModel):
    """Response with technical details for admins."""
    answer: str = Field(description="Answer")
    debug_info: dict = Field(description="Debug information")
    system_status: str = Field(description="System status")
class UserResponse(BaseModel):
    """Simple response for regular users."""
    answer: str = Field(description="Answer")
@wrap_model_call
def context_based_output(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse]
) -> ModelResponse:
    """Select output format based on Runtime Context."""
    # Read from Runtime Context: user role and environment
    user_role = request.runtime.context.user_role
    environment = request.runtime.context.environment
    if user_role == "admin" and environment == "production":
        # Admins in production get detailed output
        request = request.override(response_format=AdminResponse)
    else:
        # Regular users get simple output
        request = request.override(response_format=UserResponse)
    return handler(request)
agent = create_agent(
    model="openai:gpt-4o",
    tools=[...],
    middleware=[context_based_output],
    context_schema=Context
)
```

## 工具上下文（Tool Context）

工具比较特殊，它们**既能读取也能写入上下文**。

在最基本的情况下，当工具执行时，它接收大型语言模型（LLM）的请求参数，并返回一个工具消息。工具执行其工作并产生一个结果。

工具还可以为模型获取重要信息，使其能够执行和完成任务。

### 读取（Reads）

大多数实际工具需要的不仅仅是 LLM 的参数。它们需要**用户 ID**用于数据库查询、**API 密钥**用于外部服务，或者**当前会话状态**来做决策。工具从 **State**、**Store** 和 **Runtime Context** 中读取这些信息。

#### 状态（State）

从 **State** 读取以检查当前会话信息：

```python
from langchain.tools import tool, ToolRuntime
from langchain.agents import create_agent
@tool
def check_authentication(
    runtime: ToolRuntime
) -> str:
    """Check if user is authenticated."""
    # Read from State: check current auth status
    current_state = runtime.state
    is_authenticated = current_state.get("authenticated", False)
    if is_authenticated:
        return "User is authenticated"
    else:
        return "User is not authenticated"
agent = create_agent(
    model="openai:gpt-4o",
    tools=[check_authentication]
)
```

#### 存储（Store）

从 **Store** 读取以访问持久化的用户偏好：

```python
from dataclasses import dataclass
from langchain.tools import tool, ToolRuntime
from langchain.agents import create_agent
from langgraph.store.memory import InMemoryStore
@dataclass
class Context:
    user_id: str
@tool
def get_preference(
    preference_key: str,
    runtime: ToolRuntime[Context]
) -> str:
    """Get user preference from Store."""
    user_id = runtime.context.user_id
    # Read from Store: get existing preferences
    store = runtime.store
    existing_prefs = store.get(("preferences",), user_id)
    if existing_prefs:
        value = existing_prefs.value.get(preference_key)
        return f"{preference_key}: {value}" if value else f"No preference set for {preference_key}"
    else:
        return "No preferences found"
agent = create_agent(
    model="openai:gpt-4o",
    tools=[get_preference],
    context_schema=Context,
    store=InMemoryStore()
)
```

#### 运行时上下文（Runtime Context）

从 **Runtime Context** 读取配置，例如 **API 密钥**和**用户 ID**：

```python
from dataclasses import dataclass
from langchain.tools import tool, ToolRuntime
from langchain.agents import create_agent
@dataclass
class Context:
    user_id: str
    api_key: str
    db_connection: str
@tool
def fetch_user_data(
    query: str,
    runtime: ToolRuntime[Context]
) -> str:
    """Fetch data using Runtime Context configuration."""
    # Read from Runtime Context: get API key and DB connection
    user_id = runtime.context.user_id
    api_key = runtime.context.api_key
    db_connection = runtime.context.db_connection
    # Use configuration to fetch data
    results = perform_database_query(db_connection, query, api_key)
    return f"Found {len(results)} results for user {user_id}"
agent = create_agent(
    model="openai:gpt-4o",
    tools=[fetch_user_data],
    context_schema=Context
)
# Invoke with runtime context
result = agent.invoke(
    {"messages": [{"role": "user", "content": "Get my data"}]},
    context=Context(
        user_id="user_123",
        api_key="sk-...",
        db_connection="postgresql://..."
    )
)
```

### 写入（Writes）

工具的结果可以用来帮助代理完成给定的任务。工具既可以直接**将结果返回给模型**，也可以**更新代理的内存**，以便在未来的步骤中提供重要的上下文。

#### 状态（State）

使用 Command 写入 **State** 来跟踪会话特定的信息：

```python
from langchain.tools import tool, ToolRuntime
from langchain.agents import create_agent
from langgraph.types import Command
@tool
def authenticate_user(
    password: str,
    runtime: ToolRuntime
) -> Command:
    """Authenticate user and update State."""
    # Perform authentication (simplified)
    if password == "correct":
        # Write to State: mark as authenticated using Command
        return Command(
            update={"authenticated": True},
        )
    else:
        return Command(update={"authenticated": False})
agent = create_agent(
    model="openai:gpt-4o",
    tools=[authenticate_user]
)
```

#### 存储（Store）

写入 **Store** 以持久化跨会话的数据：

```python
from dataclasses import dataclass
from langchain.tools import tool, ToolRuntime
from langchain.agents import create_agent
from langgraph.store.memory import InMemoryStore
@dataclass
class Context:
    user_id: str
@tool
def save_preference(
    preference_key: str,
    preference_value: str,
    runtime: ToolRuntime[Context]
) -> str:
    """Save user preference to Store."""
    user_id = runtime.context.user_id
    # Read existing preferences
    store = runtime.store
    existing_prefs = store.get(("preferences",), user_id)
    # Merge with new preference
    prefs = existing_prefs.value if existing_prefs else {}
    prefs[preference_key] = preference_value
    # Write to Store: save updated preferences
    store.put(("preferences",), user_id, prefs)
    return f"Saved preference: {preference_key} = {preference_value}"
agent = create_agent(
    model="openai:gpt-4o",
    tools=[save_preference],
    context_schema=Context,
    store=InMemoryStore()
)
```

请参阅 [Tools](tools.html) 了解在工具中访问 State、Store 和 Runtime Context 的完整示例。

## 生命周期上下文（Life-cycle Context）

控制核心代理步骤**之间**发生的事情——拦截数据流以实现**横切关注点**，例如**摘要**、**防护栏**和**日志记录**。

正如您在 [Model Context](#model-context) 和 [Tool Context](#tool-context) 中所见，[middleware](middleware.html) 是使上下文工程实用化的机制。中间件允许您在代理生命周期中的任何步骤进行 Hook，并执行以下操作之一：

1. **更新上下文** - 修改 **State** 和 **Store** 以