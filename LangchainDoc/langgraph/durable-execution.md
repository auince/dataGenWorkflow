# 持久执行

**持久执行**是一种技术，其中流程或工作流在关键点保存其进度，使其能够暂停并在稍后从停止的确切位置恢复。这在需要[人在循环](interrupts.html)的场景中特别有用，用户可以在继续之前检查、验证或修改流程，以及在可能遇到中断或错误的长时间运行任务中（例如，LLM调用超时）。通过保留已完成的工作，持久执行使流程能够恢复而无需重新处理之前的步骤——即使在显著延迟后（例如，一周后）。

LangGraph的内置[持久化](persistence.html)层为工作流提供持久执行，确保每个执行步骤的状态都保存到持久存储中。这种能力保证了如果工作流被中断——无论是由于系统故障还是为了[人在循环](interrupts.html)交互——它都可以从最后记录的状态恢复。

**提示：** 如果您在LangGraph中使用了checkpointer，那么您已经启用了持久执行。您可以在任何点暂停和恢复工作流，即使在中断或失败后也是如此。
为了充分利用持久执行，请确保您的工作流设计为[确定性的和一致重放](#确定性和一致重放)和[确定性的和一致重放](#确定性和一致重放)，并将任何副作用或非确定性操作包装在[任务](https://langchain-doc.cn/v1/python/langgraph/functional-api#task)中。您可以从[StateGraph（Graph API）](https://langchain-doc.cn/v1/python/langgraph/graph-api)和[Functional API](https://langchain-doc.cn/v1/python/langgraph/functional-api)中使用[任务](https://langchain-doc.cn/v1/python/langgraph/functional-api#task)。

## 要求

要在LangGraph中利用持久执行，您需要：

1. 通过指定[checkpointer](persistence.html#checkpointer-libraries)来保存工作流进度，从而在工作流中启用[持久化](persistence.html)。
2. 在执行工作流时指定[线程标识符](persistence.html#threads)。这将跟踪特定工作流实例的执行历史。

在Python中：

* 将任何非确定性操作（例如，随机数生成）或具有副作用的操作（例如，文件写入、API调用）包装在`@task`中，以确保当工作流恢复时，这些操作不会为特定运行重复，而是从持久层中检索其结果。有关更多信息，请参阅[确定性和一致重放](#确定性和一致重放)。

在JavaScript中：

* 将任何非确定性操作（例如，随机数生成）或具有副作用的操作（例如，文件写入、API调用）包装在`@task`中，以确保当工作流恢复时，这些操作不会为特定运行重复，而是从持久层中检索其结果。有关更多信息，请参阅[确定性和一致重放](#确定性和一致重放)。

## 确定性和一致重放

当您恢复工作流运行时，代码**不会**从执行停止的**同一行代码**恢复；相反，它会识别一个适当的[起点](#工作流恢复的起点)，从那里继续。这意味着工作流将从[起点](#工作流恢复的起点)重放所有步骤，直到到达停止的点。

因此，当您为持久执行编写工作流时，必须将任何非确定性操作（例如，随机数生成）和任何具有副作用的操作（例如，文件写入、API调用）包装在[任务](https://langchain-doc.cn/v1/python/langgraph/functional-api#task)或[节点](https://langchain-doc.cn/v1/python/langgraph/graph-api#nodes)中。

为确保您的工作流是确定性的并且可以一致地重放，请遵循以下准则：

* **避免重复工作**：如果[节点](https://langchain-doc.cn/v1/python/langgraph/graph-api#nodes)包含多个具有副作用的操作（例如，日志记录、文件写入或网络调用），请将每个操作包装在单独的**任务**中。这确保当工作流恢复时，操作不会重复，并且它们的结果会从持久层中检索。
* **封装非确定性操作**：将可能产生非确定性结果的任何代码（例如，随机数生成）包装在**任务**或**节点**中。这确保在恢复时，工作流遵循完全记录的步骤序列，具有相同的结果。
* **使用幂等操作**：尽可能确保副作用（例如，API调用、文件写入）是幂等的。这意味着如果操作在工作流失败后重试，它将产生与第一次执行相同的效果。这对于导致数据写入的操作尤为重要。如果**任务**开始但未能成功完成，工作流的恢复将重新运行**任务**，依靠记录的结果来保持一致性。使用幂等键或验证现有结果以避免意外重复，确保工作流执行平稳且可预测。

在Python中，有关要避免的常见陷阱示例，请参阅功能API中的[常见陷阱](https://langchain-doc.cn/v1/python/langgraph/functional-api#common-pitfalls)部分，该部分展示了如何使用**任务**来构建代码以避免这些问题。相同的原则也适用于`StateGraph`（Graph API）。

在JavaScript中，有关要避免的常见陷阱示例，请参阅功能API中的[常见陷阱](https://langchain-doc.cn/v1/python/langgraph/functional-api#common-pitfalls)部分，该部分展示了如何使用**任务**来构建代码以避免这些问题。相同的原则也适用于`StateGraph`（Graph API）。

## 持久性模式

LangGraph支持三种持久性模式，允许您根据应用程序的要求平衡性能和数据一致性。从最少到最持久的持久性模式如下：

* [`"exit"`](#exit)
* [`"async"`](#async)
* [`"sync"`](#sync)

较高的持久性模式会给工作流执行增加更多开销。

**提示：**
**v0.6.0新增**
使用`durability`参数而不是`checkpoint_during`（v0.6.0中已弃用）进行持久性策略管理：

* `durability="async"` 替代 `checkpoint_during=True`
* `durability="exit"` 替代 `checkpoint_during=False`

### `"exit"`

更改仅在图形执行完成时（成功或出错）才会持久化。这为长时间运行的图形提供了最佳性能，但意味着中间状态不会保存，因此您无法从执行过程中的失败中恢复或中断图形执行。

### `"async"`

更改在执行下一步的同时异步持久化。这提供了良好的性能和持久性，但如果进程在执行期间崩溃，检查点可能不会被写入，存在小风险。

### `"sync"`

更改在开始下一步之前同步持久化。这确保每个检查点在继续执行之前被写入，以牺牲一些性能开销为代价提供高持久性。

您可以在调用任何图形执行方法时指定持久性模式：

```python
graph.stream(
    {"input": "test"},
    durability="sync"
)
```

## 在节点中使用任务

如果[节点](https://langchain-doc.cn/v1/python/langgraph/graph-api#nodes)包含多个操作，您可能会发现将每个操作转换为**任务**比将操作重构为单独的节点更容易。

### Python示例

#### 原始代码

```python
from typing import NotRequired
from typing_extensions import TypedDict
import uuid
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, START, END
import requests
# 定义TypedDict表示状态
class State(TypedDict):
    url: str
    result: NotRequired[str]
def call_api(state: State):
    """示例节点，用于发出API请求。"""
    result = requests.get(state['url']).text[:100]  # 副作用
    return {
        "result": result
    }
# 创建StateGraph构建器并为call_api函数添加节点
builder = StateGraph(State)
builder.add_node("call_api", call_api)
# 连接开始和结束节点到call_api节点
builder.add_edge(START, "call_api")
builder.add_edge("call_api", END)
# 指定checkpointer
checkpointer = InMemorySaver()
# 用checkpointer编译图形
graph = builder.compile(checkpointer=checkpointer)
# 定义带有线程ID的配置。
thread_id = uuid.uuid4()
config = {"configurable": {"thread_id": thread_id}}
# 调用图形
graph.invoke({"url": "https://www.example.com"}, config)
```

#### 使用任务

```python
from typing import NotRequired
from typing_extensions import TypedDict
import uuid
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.func import task
from langgraph.graph import StateGraph, START, END
import requests
# 定义TypedDict表示状态
class State(TypedDict):
    urls: list[str]
    result: NotRequired[list[str]]
@task
def _make_request(url: str):
    """发出请求。"""
    return requests.get(url).text[:100]
def call_api(state: State):
    """示例节点，用于发出API请求。"""
    requests = [_make_request(url) for url in state['urls']]
    results = [request.result() for request in requests]
    return {
        "results": results
    }
# 创建StateGraph构建器并为call_api函数添加节点
builder = StateGraph(State)
builder.add_node("call_api", call_api)
# 连接开始和结束节点到call_api节点
builder.add_edge(START, "call_api")
builder.add_edge("call_api", END)
# 指定checkpointer
checkpointer = InMemorySaver()
# 用checkpointer编译图形
graph = builder.compile(checkpointer=checkpointer)
# 定义带有线程ID的配置。
thread_id = uuid.uuid4()
config = {"configurable": {"thread_id": thread_id}}
# 调用图形
graph.invoke({"urls": ["https://www.example.com"]}, config)
```

### JavaScript示例

#### 原始代码

```typescript
import { StateGraph, START, END } from "@langchain/langgraph";
import { MemorySaver } from "@langchain/langgraph";
import { v4 as uuidv4 } from "uuid";
import * as z from "zod";
// 定义Zod架构表示状态
const State = z.object({
  url: z.string(),
  result: z.string().optional(),
});
const callApi = async (state: z.infer<typeof State>) => {
  const response = await fetch(state.url);  // 副作用
  const text = await response.text();
  const result = text.slice(0, 100);
  return {
    result,
  };
};
// 创建StateGraph构建器并为callApi函数添加节点
const builder = new StateGraph(State)
  .addNode("callApi", callApi)
  .addEdge(START, "callApi")
  .addEdge("callApi", END);
// 指定checkpointer
const checkpointer = new MemorySaver();
// 用checkpointer编译图形
const graph = builder.compile({ checkpointer });
// 定义带有线程ID的配置。
const threadId = uuidv4();
const config = { configurable: { thread_id: threadId } };
// 调用图形
await graph.invoke({ url: "https://www.example.com" }, config);
```

#### 使用任务

```typescript
import { StateGraph, START, END } from "@langchain/langgraph";
import { MemorySaver } from "@langchain/langgraph";
import { task } from "@langchain/langgraph";
import { v4 as uuidv4 } from "uuid";
import * as z from "zod";
// 定义Zod架构表示状态
const State = z.object({
  urls: z.array(z.string()),
  results: z.array(z.string()).optional(),
});
const makeRequest = task("makeRequest", async (url: string) => {
  const response = await fetch(url);  // 副作用
  const text = await response.text();
  return text.slice(0, 100);
});
const callApi = async (state: z.infer<typeof State>) => {
  const requests = state.urls.map((url) => makeRequest(url));
  const results = await Promise.all(requests);
  return {
    results,
  };
};
// 创建StateGraph构建器并为callApi函数添加节点
const builder = new StateGraph(State)
  .addNode("callApi", callApi)
  .addEdge(START, "callApi")
  .addEdge("callApi", END);
// 指定checkpointer
const checkpointer = new MemorySaver();
// 用checkpointer编译图形
const graph = builder.compile({ checkpointer });
// 定义带有线程ID的配置。
const threadId = uuidv4();
const config = { configurable: { thread_id: threadId } };
// 调用图形
await graph.invoke({ urls: ["https://www.example.com"] }, config);
```

## 恢复工作流

一旦您在工作流中启用了持久执行，您可以在以下场景中恢复执行：

### Python中

* **暂停和恢复工作流：** 使用`interrupt`函数在特定点暂停工作流，并使用`Command`原语用更新的状态恢复它。有关更多详细信息，请参阅[**中断**](interrupts.html)。
* **从失败中恢复：** 在异常（例如，LLM提供商中断）后自动从最后一个成功的检查点恢复工作流。这涉及通过提供`None`作为输入值（请参阅功能API中的[示例](https://langchain-doc.cn/v1/python/langgraph/use-functional-api#resuming-after-an-error)）使用相同的线程标识符执行工作流。

### JavaScript中

* **暂停和恢复工作流：** 使用`interrupt`函数在特定点暂停工作流，并使用`Command`原语用更新的状态恢复它。有关更多详细信息，请参阅[**中断**](interrupts.html)。
* **从失败中恢复：** 在异常（例如，LLM提供商中断）后自动从最后一个成功的检查点恢复工作流。这涉及通过提供`null`作为输入值（请参阅功能API中的[示例](https://langchain-doc.cn/v1/python/langgraph/use-functional-api#resuming-after-an-error)）使用相同的线程标识符执行工作流。

## 工作流恢复的起点

### Python中

* 如果您使用`StateGraph`（Graph API），起点是执行停止的[**节点**](https://langchain-doc.cn/v1/python/langgraph/graph-api#nodes)的开始。
* 如果您在节点内进行子图调用，起点将是调用被暂停的子图的**父**节点。在子图内部，起点将是执行停止的特定[**节点**](https://langchain-doc.cn/v1/python/langgraph/graph-api#nodes)。
* 如果您使用Functional API，起点是执行停止的[**入口点**](https://langchain-doc.cn/v1/python/langgraph/functional-api#entrypoint)的开始。

### JavaScript中

* 如果您使用[StateGraph（Graph API）](https://langchain-doc.cn/v1/python/langgraph/graph-api)，起点是执行停止的[**节点**](https://langchain-doc.cn/v1/python/langgraph/graph-api#nodes)的开始。
* 如果您在节点内进行子图调用，起点将是调用被暂停的子图的**父**节点。在子图内部，起点将是执行停止的特定[**节点**](https://langchain-doc.cn/v1/python/langgraph/graph-api#nodes)。
* 如果您使用Functional API，起点是执行停止的[**入口点**](https://langchain-doc.cn/v1/python/langgraph/functional-api#entrypoint)的开始。