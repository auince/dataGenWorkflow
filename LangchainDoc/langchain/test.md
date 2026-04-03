# 测试

Agentic 应用程序允许 **大型语言模型（LLM）** 自行决定解决问题的下一步。这种灵活性非常强大，但模型的黑箱性质使得很难预测对 Agent 的某个部分进行的微调将如何影响其余部分。要构建可投入生产使用的 Agent，**彻底的测试**是必不可少的。

## Agent 测试方法

测试您的 Agent 有以下几种方法：

- **单元测试**：使用内存中的**伪造（fake）**对象，在隔离状态下对 Agent 的小型、确定性部分进行测试，以便快速、确定性地断言（assert）准确的行为。
- **集成测试**：使用**真实的网络调用**来测试 Agent，以确认组件协同工作、凭证和模式（schemas）一致，并且延迟可接受。

Agentic 应用程序倾向于更多地依赖集成测试，因为它们将多个组件链接在一起，并且必须处理由于 LLM 的**非确定性**所带来的不稳定性。

## 单元测试 (Unit Testing)

## 模拟聊天模型 (Mocking Chat Model)

对于不需要 API 调用的逻辑，您可以使用内存中的**存根（stub）**来模拟响应。

LangChain 提供了 `GenericFakeChatModel` (https://python.langchain.com/api_reference/core/language_models/langchain_core.language_models.fake_chat_models.GenericFakeChatModel.html) 用于模拟文本响应。它接受一个响应（AIMessages 或字符串）的迭代器，并在每次调用时返回一个响应。它支持常规用法和流式传输用法。

```python
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
model = GenericFakeChatModel(messages=iter([
    AIMessage(content="", tool_calls=[ToolCall(name="foo", args={"bar": "baz"}, id="call_1")]),
    "bar"
]))
model.invoke("hello")
# AIMessage(content='', ..., tool_calls=[{'name': 'foo', 'args': {'bar': 'baz'}, 'id': 'call_1', 'type': 'tool_call'}])
```

如果我们再次调用该模型，它将返回迭代器中的下一个项目：

```python
model.invoke("hello, again!")
# AIMessage(content='bar', ...)
```

## InMemorySaver 检查点 (InMemorySaver Checkpointer)

为了在测试期间启用**持久性（persistence）**，您可以使用 `InMemorySaver` (https://reference.langchain.com/python/langgraph/checkpoints/#langgraph.checkpoint.memory.InMemorySaver) 检查点。这允许您模拟多次对话轮次，以测试**依赖于状态**的行为：

```python
from langgraph.checkpoint.memory import InMemorySaver
agent = create_agent(
    model,
    tools=[],
    checkpointer=InMemorySaver()
)
# 第一次调用
agent.invoke(HumanMessage(content="I live in Sydney, Australia."))
# 第二次调用：第一条消息被持久化（悉尼位置），因此模型返回 GMT+10 时间
agent.invoke(HumanMessage(content="What's my local time?"))
```

## 集成测试 (Integration Testing)

许多 Agent 行为只有在使用**真实 LLM**时才会出现，例如 Agent 决定调用哪个工具、如何格式化响应，或者提示修改是否会影响整个执行轨迹。LangChain 的 `agentevals` (https://github.com/langchain-ai/agentevals) 包提供了专门用于测试带有真实模型的 Agent 轨迹的评估器。

AgentEvals 让您可以通过执行**轨迹匹配（trajectory match）**或使用 **LLM 评判（LLM judge）**来轻松评估 Agent 的轨迹（消息的确切序列，包括工具调用）：

| 评估器 | 描述 | 适用场景 |
| :--- | :--- | :--- |
| **轨迹匹配** | 为给定的输入**硬编码**一个参考轨迹，并通过**逐步比较**来验证运行结果。 | **理想用于测试定义明确的工作流**，您知道预期的行为。当您对应该调用哪些工具以及调用顺序有**特定期望**时使用。此方法是**确定性**的、**快速**且**经济高效**，因为它不需要额外的 LLM 调用。 |
| **LLM 评判** | 使用 **LLM** 来定性验证 Agent 的执行轨迹。这个“评判”LLM 根据**提示词准则**（可以包含参考轨迹）来审查 Agent 的决策。 | **更灵活**，可以评估效率和适当性等**细微方面**，但需要进行 LLM 调用，且**非确定性**较低。当您想要评估 Agent 轨迹的**整体质量和合理性**，而无需严格的工具调用或排序要求时使用。 |

## 安装 AgentEvals

```bash
pip install agentevals
```

或者，直接克隆 [AgentEvals 仓库](https://github.com/langchain-ai/agentevals)。

## 轨迹匹配评估器 (Trajectory Match Evaluator)

AgentEvals 提供了 `create_trajectory_match_evaluator` 函数，用于将您的 Agent 轨迹与参考轨迹进行匹配。有四种模式可供选择：

| 模式 | 描述 | 用例 |
| :--- | :--- | :--- |
| `strict` (严格) | 消息和工具调用**按相同顺序**精确匹配 | 测试特定的序列（例如，授权前的策略查询） |
| `unordered` (无序) | 允许相同的工具调用**以任何顺序**出现 | 验证信息检索时**顺序不重要**的情况 |
| `subset` (子集) | Agent 调用的工具**仅限于**参考轨迹中的工具（不允许额外调用） | 确保 Agent 不**超出预期范围** |
| `superset` (超集) | Agent 调用的工具**至少包含**参考轨迹中的工具（允许额外调用） | 验证已执行**最低要求的操作** |

### 严格匹配 (Strict match)

`strict` 模式确保轨迹包含**相同的消息**、**相同的工具调用**，并**按相同的顺序**，尽管它允许消息内容存在差异。当您需要强制执行特定的操作序列时（例如，在授权操作之前需要进行策略查询），此功能非常有用。

```python
from langchain.agents import create_agent
from langchain.tools import tool
from langchain.messages import HumanMessage, AIMessage, ToolMessage
from agentevals.trajectory.match import create_trajectory_match_evaluator
@tool
def get_weather(city: str):
    """Get weather information for a city."""
    return f"It's 75 degrees and sunny in {city}."
agent = create_agent("gpt-4o", tools=[get_weather])
evaluator = create_trajectory_match_evaluator(  # [!code highlight]
    trajectory_match_mode="strict",  # [!code highlight]
)  # [!code highlight]
def test_weather_tool_called_strict():
    result = agent.invoke({
        "messages": [HumanMessage(content="What's the weather in San Francisco?")]
    })
    reference_trajectory = [
        HumanMessage(content="What's the weather in San Francisco?"),
        AIMessage(content="", tool_calls=[
            {"id": "call_1", "name": "get_weather", "args": {"city": "San Francisco"}}
        ]),
        ToolMessage(content="It's 75 degrees and sunny in San Francisco.", tool_call_id="call_1"),
        AIMessage(content="The weather in San Francisco is 75 degrees and sunny."),
    ]
    evaluation = evaluator(
        outputs=result["messages"],
        reference_outputs=reference_trajectory
    )
    # {
    #     'key': 'trajectory_strict_match',
    #     'score': True,
    #     'comment': None,
    # }
    assert evaluation["score"] is True
```

### 无序匹配 (Unordered match)

`unordered` 模式允许**相同的工具调用以任何顺序**出现，当您想要验证是否检索了特定信息但**不关心顺序**时，此模式很有帮助。例如，Agent 可能需要检查城市的天气和活动，但顺序无关紧要。

```python
from langchain.agents import create_agent
from langchain.tools import tool
from langchain.messages import HumanMessage, AIMessage, ToolMessage
from agentevals.trajectory.match import create_trajectory_match_evaluator
@tool
def get_weather(city: str):
    """Get weather information for a city."""
    return f"It's 75 degrees and sunny in {city}."
@tool
def get_events(city: str):
    """Get events happening in a city."""
    return f"Concert at the park in {city} tonight."
agent = create_agent("gpt-4o", tools=[get_weather, get_events])
evaluator = create_trajectory_match_evaluator(  # [!code highlight]
    trajectory_match_mode="unordered",  # [!code highlight]
)  # [!code highlight]
def test_multiple_tools_any_order():
    result = agent.invoke({
        "messages": [HumanMessage(content="What's happening in SF today?")]
    })
    # 参考轨迹中工具调用的顺序与实际执行的顺序不同
    reference_trajectory = [
        HumanMessage(content="What's happening in SF today?"),
        AIMessage(content="", tool_calls=[
            {"id": "call_1", "name": "get_events", "args": {"city": "SF"}},
            {"id": "call_2", "name": "get_weather", "args": {"city": "SF"}},
        ]),
        ToolMessage(content="Concert at the park in SF tonight.", tool_call_id="call_1"),
        ToolMessage(content="It's 75 degrees and sunny in SF.", tool_call_id="call_2"),
        AIMessage(content="Today in SF: 75 degrees and sunny with a concert at the park tonight."),
    ]
    evaluation = evaluator(
        outputs=result["messages"],
        reference_outputs=reference_trajectory,
    )
    # {
    #     'key': 'trajectory_unordered_match',
    #     'score': True,
    # }
    assert evaluation["score"] is True
```

### 子集和超集匹配 (Subset and superset match)

`superset` 和 `subset` 模式匹配**部分轨迹**。`superset` 模式验证 Agent **至少调用了参考轨迹中的工具**，允许有额外的工具调用。`subset` 模式确保 Agent **没有调用超出参考轨迹中工具的任何工具**。

```python
from langchain.agents import create_agent
from langchain.tools import tool
from langchain.messages import HumanMessage, AIMessage, ToolMessage
from agentevals.trajectory.match import create_trajectory_match_evaluator
@tool
def get_weather(city: str):
    """Get weather information for a city."""
    return f"It's 75 degrees and sunny in {city}."
@tool
def get_detailed_forecast(city: str):
    """Get detailed weather forecast for a city."""
    return f"Detailed forecast for {city}: sunny all week."
agent = create_agent("gpt-4o", tools=[get_weather, get_detailed_forecast])
evaluator = create_trajectory_match_evaluator(  # [!code highlight]
    trajectory_match_mode="superset",  # [!code highlight]
)  # [!code highlight]
def test_agent_calls_required_tools_plus_extra():
    result = agent.invoke({
        "messages": [HumanMessage(content="What's the weather in Boston?")]
    })
    # 参考轨迹仅要求 get_weather，但 Agent 可能会调用额外的工具
    reference_trajectory = [
        HumanMessage(content="What's the weather in Boston?"),
        AIMessage(content="", tool_calls=[
            {"id": "call_1", "name": "get_weather", "args": {"city": "Boston"}},
        ]),
        ToolMessage(content="It's 75 degrees and sunny in Boston.", tool_call_id="call_1"),
        AIMessage(content="The weather in Boston is 75 degrees and sunny."),
    ]
    evaluation = evaluator(
        outputs=result["messages"],
        reference_outputs=reference_trajectory,
    )
    # {
    #     'key': 'trajectory_superset_match',
    #     'score': True,
    #     'comment': None,
    # }
    assert evaluation["score"] is True
```

> 您还可以设置 `tool_args_match_mode` 属性和/或 `tool_args_match_overrides`，以自定义评估器如何考虑实际轨迹与参考轨迹中工具调用之间的相等性。默认情况下，只有**具有相同参数的相同工具调用**才被视为相等。请访问 [仓库](https://github.com/langchain-ai/agentevals?tab=readme-ov-file#tool-args-match-modes) 了解更多详细信息。

## LLM 评判评估器 (LLM-as-Judge Evaluator)

您还可以使用 `create_trajectory_llm_as_judge` 函数，用 LLM 来评估 Agent 的执行路径。与轨迹匹配评估器不同，它**不需要参考轨迹**，但如果可用，也可以提供。

### 不带参考轨迹

```python
from langchain.agents import create_agent
from langchain.tools import tool
from langchain.messages import HumanMessage, AIMessage, ToolMessage
from agentevals.trajectory.llm import create_trajectory_llm_as_judge, TRAJECTORY_ACCURACY_PROMPT
@tool
def get_weather(city: str):
    """Get weather information for a city."""
    return f"It's 75 degrees and sunny in {city}."
agent = create_agent("gpt-4o", tools=[get_weather])
evaluator = create_trajectory_llm_as_judge(  # [!code highlight]
    model="openai:o3-mini",  # [!code highlight]
    prompt=TRAJECTORY_ACCURACY_PROMPT,  # [!code highlight]
)  # [!code highlight]
def test_trajectory_quality():
    result = agent.invoke({
        "messages": [HumanMessage(content="What's the weather in Seattle?")]
    })
    evaluation = evaluator(
        outputs=result["messages"],
    )
    # {
    #     'key': 'trajectory_accuracy',
    #     'score': True,
    #     'comment': 'The provided agent trajectory is reasonable...'
    # }
    assert evaluation["score"] is True
```

### 带参考轨迹

如果您有参考轨迹，可以在提示词中添加一个额外的变量，并传入参考轨迹。下面，我们使用预构建的 `TRAJECTORY_ACCURACY_PROMPT_WITH_REFERENCE` 提示词，并配置 `reference_outputs` 变量：

```python
evaluator = create_trajectory_llm_as_judge(
    model="openai:o3-mini",
    prompt=TRAJECTORY_ACCURACY_PROMPT_WITH_REFERENCE,
)
evaluation = judge_with_reference(
    outputs=result["messages"],
    reference_outputs=reference_trajectory,
)
```

> 有关如何让 LLM 评估轨迹的更多可配置性，请访问 [仓库](https://github.com/langchain-ai/agentevals?tab=readme-ov-file#trajectory-llm-as-judge)。

## 异步支持 (Async Support)

所有 `agentevals` 评估器都支持 Python **asyncio**。对于使用工厂函数的评估器，可以通过在函数名中的 `create_` 之后添加 `async` 来获得异步版本。

### 异步评判和评估器示例

```python
from agentevals.trajectory.llm import create_async_trajectory_llm_as_judge, TRAJECTORY_ACCURACY_PROMPT
from agentevals.trajectory.match import create_async_trajectory_match_evaluator
async_judge = create_async_trajectory_llm_as_judge(
    model="openai:o3-mini",
    prompt=TRAJECTORY_ACCURACY_PROMPT,
)
async_evaluator = create_async_trajectory_match_evaluator(
    trajectory_match_mode="strict",
)
async def test_async_evaluation():
    result = await agent.ainvoke({
        "messages": [HumanMessage(content="What's the weather?")]
    })
    evaluation = await async_judge(outputs=result["messages"])
    assert evaluation["score"] is True
```

## LangSmith 集成 (LangSmith Integration)

为了跟踪随时间变化的实验，您可以将评估器结果记录到 [LangSmith](https://smith.langchain.com/)，这是一个用于构建生产级 LLM 应用程序的平台，其中包括**追踪（tracing）**、**评估（evaluation）和实验工具**。

首先，通过设置所需的环境变量来配置 LangSmith：

```bash
export LANGSMITH_API_KEY="your_langsmith_api_key"
export LANGSMITH_TRACING="true"
```

LangSmith 提供了两种主要的运行评估方法：[pytest 集成](https://langchain-doc.cn/langsmith/pytest)和 `evaluate` 函数。

### 使用 pytest 集成

```python
import pytest
from langsmith import testing as t
from agentevals.trajectory.llm import create_trajectory_llm_as_judge, TRAJECTORY_ACCURACY_PROMPT
trajectory_evaluator = create_trajectory_llm_as_judge(
    model="openai:o3-mini",
    prompt=TRAJECTORY_ACCURACY_PROMPT,
)
@pytest.mark.langsmith
def test_trajectory_accuracy():
    result = agent.invoke({
        "messages": [HumanMessage(content="What's the weather in SF?")]
    })
    reference_trajectory = [
        HumanMessage(content="What's the weather in SF?"),
        AIMessage(content="", tool_calls=[
            {"id": "call_1", "name": "get_weather", "args": {"city": "SF"}},
        ]),
        ToolMessage(content="It's 75 degrees and sunny in SF.", tool_call_id="call_1"),
        AIMessage(content="The weather in SF is 75 degrees and sunny."),
    ]
    # 将输入、输出和参考输出记录到 LangSmith
    t.log_inputs({})
    t.log_outputs({"messages": result["messages"]})
    t.log_reference_outputs({"messages": reference_trajectory})
    trajectory_evaluator(
        outputs=result["messages"],
        reference_outputs=reference_trajectory
    )
```

使用 pytest 运行评估：

```bash
pytest test_trajectory.py --langsmith-output
```

结果将自动记录到 LangSmith。

### 使用 evaluate 函数

或者，您可以在 LangSmith 中创建一个数据集并使用 `evaluate` 函数：

```python
from langsmith import Client
from agentevals.trajectory.llm import create_trajectory_llm_as_judge, TRAJECTORY_ACCURACY_PROMPT
client = Client()
trajectory_evaluator = create_trajectory_llm_as_judge(
    model="openai:o3-mini",
    prompt=TRAJECTORY_ACCURACY_PROMPT,
)
def run_agent(inputs):
    """Your agent function that returns trajectory messages."""
    return agent.invoke(inputs)["messages"]
experiment_results = client.evaluate(
    run_agent,
    data="your_dataset_name",
    evaluators=[trajectory_evaluator]
)
```

结果将自动记录到 LangSmith。

> 💡 要了解有关评估 Agent 的更多信息，请参阅 [LangSmith 文档](https://langchain-doc.cn/langsmith/pytest)。

## 记录和重放 HTTP 调用 (Recording & Replaying HTTP Calls)

调用真实 LLM API 的集成测试可能**缓慢且昂贵**，尤其是在 CI/CD 管道中频繁运行时。我们建议使用一个库来**记录 HTTP 请求和响应**，然后在后续运行中**重放**它们，而无需进行实际的网络调用。

您可以使用 [`vcrpy`](https://langchain-doc.cn/v1/python/langchain/%5Bhttps://pypi.org/project/vcrpy/1.5.2/%5D(https://pypi.org/project/vcrpy/1.5.2/)) 来实现此目的。如果您使用的是 `pytest`，[`pytest-recording` 插件](https://pypi.org/project/pytest-recording/)提供了一种简单的只需少量配置即可启用此功能的方法。请求/响应被记录在**磁带（cassettes）**中，然后用于在后续运行中模拟真实的网络调用。

设置您的 `conftest.py` 文件以从磁带中过滤掉敏感信息：

```python
import pytest
@pytest.fixture(scope="session")
def vcr_config():
    return {
        "filter_headers": [
            ("authorization", "XXXX"),
            ("x-api-key", "XXXX"),
            # ... 其他您想要屏蔽的 header
        ],
        "filter_query_parameters": [
            ("api_key", "XXXX"),
            ("key", "XXXX"),
        ],
    }
```

然后配置您的项目以识别 `vcr` 标记：

```ini
[pytest]
markers =
    vcr: record/replay HTTP via VCR
addopts = --record-mode=once
```

或

```toml
[tool.pytest.ini_options]
markers = [
    "vcr: record/replay HTTP via VCR"
]
addopts = "--record-mode=once"
```

> `--record-mode=once` 选项会在第一次运行时记录 HTTP 交互，并在后续运行中重放它们。

现在，只需使用 `vcr` 标记来装饰您的测试：

```python
@pytest.mark.vcr()
def test_agent_trajectory():
    # ...
```

第一次运行此测试时，您的 Agent 将进行**真实的网络调用**，pytest 将在 `tests/cassettes` 目录中生成一个磁带文件 `test_agent_trajectory.yaml`。后续运行将使用该磁带来**模拟真实的网络调用**，前提是 Agent 的请求没有从前一次运行中发生变化。如果发生变化，测试将失败，您将需要**删除磁带**并**重新运行测试**以记录新的交互。

> ⚠️ **警告**
>
> 当您修改提示词、添加新工具或更改预期轨迹时，您保存的磁带将**过时**，并且您现有的测试将**失败**。您应该删除相应的磁带文件并重新运行测试以记录新的交互。