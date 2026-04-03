# 子Agent

深度Agent可以创建子Agent来委派工作。你可以在 `subagents` 参数中指定自定义的子Agent。子Agent对于[上下文隔离](https://www.dbreunig.com/2025/06/26/how-to-fix-your-context.html#context-quarantine)（保持主Agent上下文的整洁）和提供专门的指令非常有用。

## 为什么使用子Agent？

子Agent解决了**上下文膨胀问题**。当Agent使用具有大量输出的工具（网络搜索、文件读取、数据库查询）时，上下文窗口会迅速被中间结果填满。子Agent将这些详细的工作隔离开来——主Agent只接收最终结果，而不是产生它的数十个工具调用。

**何时使用子Agent：**

*   ✅ 会使主Agent上下文混乱的多步骤任务
*   ✅ 需要自定义指令或工具的专业领域
*   ✅ 需要不同模型能力的任务
*   ✅ 当你希望主Agent专注于高层协调时

**何时不使用子Agent：**

*   ❌ 简单的单步任务
*   ❌ 当你需要维护中间上下文时
*   ❌ 当开销超过收益时

## 配置

`subagents` 应该是一个字典列表或 `CompiledSubAgent` 对象。有两种类型：

### SubAgent (基于字典)

对于大多数用例，将子Agent定义为字典：

**必填字段：**

*   **name** (`str`): 子Agent的唯一标识符。主Agent在调用 `task()` 工具时使用此名称。
*   **description** (`str`): 此子Agent的功能。要具体并以行动为导向。主Agent使用它来决定何时委派。
*   **system_prompt** (`str`): 给子Agent的指令。包括工具使用指南和输出格式要求。
*   **tools** (`List[Callable]`): 子Agent可以使用的工具。保持最小化，只包括需要的内容。

**可选字段：**

*   **model** (`str | BaseChatModel`): 覆盖主Agent的模型。使用格式 `"provider:model-name"` (例如, `"openai:gpt-4o"`)。
*   **middleware** (`List[Middleware]`): 用于自定义行为、日志记录或速率限制的附加中间件。
*   **interrupt_on** (`Dict[str, bool]`): 为特定工具配置人机交互。需要一个检查点。

### CompiledSubAgent

对于复杂的工作流，使用预构建的 LangGraph 图：

**字段：**

*   **name** (`str`): 唯一标识符
*   **description** (`str`): 此子Agent的功能
*   **runnable** (`Runnable`): 一个已编译的 LangGraph 图 (必须先调用 `.compile()`)

## 使用 SubAgent

```python
import os
from typing import Literal
from tavily import TavilyClient
from deepagents import create_deep_agent

tavily_client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])

def internet_search(
    query: str,
    max_results: int = 5,
    topic: Literal["general", "news", "finance"] = "general",
    include_raw_content: bool = False,
):
    """运行网络搜索"""
    return tavily_client.search(
        query,
        max_results=max_results,
        include_raw_content=include_raw_content,
        topic=topic,
    )

research_subagent = {
    "name": "research-agent",
    "description": "用于研究更深入的问题",
    "system_prompt": "你是一位出色的研究员",
    "tools": [internet_search],
    "model": "openai:gpt-4o",  # 可选覆盖，默认为主Agent模型
}

subagents = [research_subagent]

agent = create_deep_agent(
    model="claude-sonnet-4-5-20250929",
    subagents=subagents
)
```

## 使用 CompiledSubAgent

对于更复杂的用例，你可以提供自己预构建的 LangGraph 图作为子Agent：

```python
from deepagents import create_deep_agent, CompiledSubAgent
from langchain.agents import create_agent

# 创建一个自定义Agent图
custom_graph = create_agent(
    model=your_model,
    tools=specialized_tools,
    prompt="你是一个用于数据分析的专业Agent..."
)

# 将其用作自定义子Agent
custom_subagent = CompiledSubAgent(
    name="data-analyzer",
    description="用于复杂数据分析任务的专业Agent",
    runnable=custom_graph
)

subagents = [custom_subagent]

agent = create_deep_agent(
    model="claude-sonnet-4-5-20250929",
    tools=[internet_search],
    system_prompt=research_instructions,
    subagents=subagents
)
```

```typescript
// TODO: 添加 JS 实现
```

## 通用子Agent

除了任何用户定义的子Agent外，深度Agent随时可以访问一个 `general-purpose` 子Agent。该子Agent：

*   与主Agent具有相同的系统提示
*   可以访问所有相同的工具
*   使用相同的模型（除非被覆盖）

### 何时使用

通用子Agent非常适合在没有专门行为的情况下进行上下文隔离。主Agent可以将一个复杂的多步骤任务委派给该子Agent，并获得一个简洁的结果，而不会因中间工具调用而导致上下文膨胀。

> **示例**
>
> 主Agent不是进行10次网络搜索并用结果填充其上下文，而是委派给通用子Agent：`task(name="general-purpose", task="研究量子计算趋势")`。子Agent在内部执行所有搜索，并仅返回一个摘要。

## 最佳实践

### 编写清晰的描述

主Agent使用描述来决定调用哪个子Agent。要具体：

✅ **好的:** `"分析财务数据并生成带有置信度分数的投资见解"`

❌ **不好的:** `"做金融方面的事情"`

### 保持系统提示的详细性

包括有关如何使用工具和格式化输出的具体指南：

```python
research_subagent = {
    "name": "research-agent",
    "description": "使用网络搜索进行深入研究并综合发现",
    "system_prompt": """你是一位彻底的研究员。你的工作是：
    1. 将研究问题分解为可搜索的查询
    2. 使用 internet_search 查找相关信息
    3. 将发现综合成一个全面但简洁的摘要
    4. 在提出主张时引用来源
    输出格式：
    - 摘要 (2-3段)
    - 主要发现 (项目符号)
    - 来源 (附带URL)
    保持你的回应在500字以内，以保持上下文的整洁。""",
    "tools": [internet_search],
}
```

```typescript
// TODO: 添加 JS 实现
```

### 最小化工具集

只给子Agent他们需要的工具。这可以提高专注度和安全性：

```python
# ✅ 好的: 专注的工具集
email_agent = {
    "name": "email-sender",
    "tools": [send_email, validate_email],  # 仅与电子邮件相关
}

# ❌ 不好的: 工具太多
email_agent = {
    "name": "email-sender",
    "tools": [send_email, web_search, database_query, file_upload],  # 不专注
}
```

```typescript
// TODO: 添加 JS 实现
```

### 按任务选择模型

不同的模型擅长不同的任务：

```python
subagents = [
    {
        "name": "contract-reviewer",
        "description": "审查法律文件和合同",
        "system_prompt": "你是一位专业的法律审查员...",
        "tools": [read_document, analyze_contract],
        "model": "claude-sonnet-4-5-20250929",  # 用于长文档的大上下文
    },
    {
        "name": "financial-analyst",
        "description": "分析财务数据和市场趋势",
        "system_prompt": "你是一位专业的财务分析师...",
        "tools": [get_stock_price, analyze_fundamentals],
        "model": "openai:gpt-4o",  # 更适合数值分析
    },
]
```

```typescript
// TODO: 添加 JS 实现
```

### 返回简洁的结果

指示子Agent返回摘要，而不是原始数据：

```python
data_analyst = {
    "system_prompt": """分析数据并返回：
    1. 关键见解 (3-5个项目符号)
    2. 总体置信度分数
    3. 建议的后续行动
    不要包括：
    - 原始数据
    - 中间计算
    - 详细的工具输出
    保持回应在300字以内。"""
}
```

```typescript
// TODO: 添加 JS 实现
```

## 常见模式

### 多个专业子Agent

为不同领域创建专业子Agent：

```python
from deepagents import create_deep_agent

subagents = [
    {
        "name": "data-collector",
        "description": "从各种来源收集原始数据",
        "system_prompt": "收集关于该主题的全面数据",
        "tools": [web_search, api_call, database_query],
    },
    {
        "name": "data-analyzer",
        "description": "分析收集的数据以获取见解",
        "system_prompt": "分析数据并提取关键见解",
        "tools": [statistical_analysis],
    },
    {
        "name": "report-writer",
        "description": "根据分析撰写精美的报告",
        "system_prompt": "根据见解创建专业报告",
        "tools": [format_document],
    },
]

agent = create_deep_agent(
    model="claude-sonnet-4-5-20250929",
    system_prompt="你协调数据分析和报告。使用子Agent完成专业任务。",
    subagents=subagents
)
```

```typescript
// TODO: 添加 JS 实现
```

**工作流程：**

1.  主Agent创建高层计划
2.  将数据收集委派给 data-collector
3.  将结果传递给 data-analyzer
4.  将见解发送给 report-writer
5.  编译最终输出

每个子Agent都在只专注于其任务的干净上下文中工作。

## 故障排除

### 子Agent未被调用

**问题**: 主Agent试图自己完成工作，而不是委派。

**解决方案**:

1.  **使描述更具体：**

    ```python
    # ✅ 好的
    {"name": "research-specialist", "description": "使用网络搜索对特定主题进行深入研究。当你需要需要多次搜索的详细信息时使用。"}
    # ❌ 不好的
    {"name": "helper", "description": "帮助处理事情"}
    ```

2.  **指示主Agent进行委派：**

    ```python
    agent = create_deep_agent(
        system_prompt="""...你的指令...
        重要提示：对于复杂的任务，使用 task() 工具委派给你的子Agent。
        这可以保持你的上下文整洁并改善结果。""",
        subagents=[...]
    )
    ```

### 上下文仍然臃肿

**问题**: 尽管使用了子Agent，上下文仍然被填满。

**解决方案**:

1.  **指示子Agent返回简洁的结果：**

    ```python
    system_prompt="""...
    重要提示：只返回必要的摘要。
    不要包括原始数据、中间搜索结果或详细的工具输出。
    你的回应应在500字以内。"""
    ```

2.  **使用文件系统处理大数据：**

    ```python
    system_prompt="""当你收集大量数据时：
    1. 将原始数据保存到 /data/raw_results.txt
    2. 处理和分析数据
    3. 只返回分析摘要
    这可以保持上下文的整洁。"""
    ```

### 选择了错误的子Agent

**问题**: 主Agent为任务调用了不合适的子Agent。

**解决方案**: 在描述中清楚地区分子Agent：

```python
subagents = [
    {
        "name": "quick-researcher",
        "description": "用于需要1-2次搜索的简单、快速的研究问题。当你需要基本事实或定义时使用。",
    },
    {
        "name": "deep-researcher",
        "description": "用于需要多次搜索、综合和分析的复杂、深入的研究。用于综合报告。",
    }
]