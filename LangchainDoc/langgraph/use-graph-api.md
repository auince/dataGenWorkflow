# 使用Graph API

本指南将帮助您使用LangGraph的Graph API构建复杂的工作流程。Graph API是LangGraph的低级API，提供了对工作流构建的精细控制。它允许您定义自定义状态、节点和边，从而创建任意复杂的计算图。

## 安装

在开始之前，请确保安装LangGraph：

```bash
pip install langgraph
```

```bash
npm install @langchain/langgraph
```

## 定义和更新状态

Graph API的核心概念是**状态**。状态是在图执行过程中在节点之间传递的数据。在Graph API中，您需要明确定义状态的结构以及如何更新它。

### 状态定义

状态可以使用Python的`TypedDict`或JavaScript的Zod模式来定义。这允许您指定状态中可以包含的键及其类型。

```python
from typing_extensions import TypedDict
class State(TypedDict):
    # 您可以在这里定义任意数量的键和它们的类型
    key1: str
    key2: int
    # 等等...
```

```typescript
import * as z from "zod";
const State = z.object({
  // 您可以在这里定义任意数量的键和它们的类型
  key1: z.string(),
  key2: z.number(),
  // 等等...
});
```

### 使用reducers处理状态更新

当多个节点更新同一状态键时，LangGraph需要知道如何组合这些更新。这是通过**reducers**实现的。Reducers是接收当前状态值和新值并返回组合结果的函数。

在Python中，您可以使用`Annotated`类型提示指定reducer：

```python
from typing import Annotated
import operator
from typing_extensions import TypedDict
class State(TypedDict):
    # 使用operator.add作为reducer
    # 对于列表，这意味着连接列表
    # 对于数字，这意味着相加
    # 对于字符串，这意味着连接字符串
    aggregate: Annotated[list, operator.add]
    count: Annotated[int, operator.add]
```

在JavaScript中，您可以使用Zod的register方法并提供reducer：

```typescript
import { registry } from "@langchain/langgraph/zod";
import * as z from "zod";
const State = z.object({
  // 使用自定义reducer函数
  aggregate: z.array(z.string()).register(registry, {
    reducer: {
      fn: (x, y) => x.concat(y),
    },
    default: () => [] as string[],
  }),
  count: z.number().register(registry, {
    reducer: {
      fn: (x, y) => x + y,
    },
    default: () => 0,
  }),
});
```

#### 使用预构建的MessagesState

对于处理消息的常见用例，LangGraph提供了预构建的`MessagesState`类，它包含一个已配置了reducer的`messages`字段，用于连接消息列表。

```python
from langgraph.graph import MessagesState
# MessagesState是一个预定义的TypedDict，具有以下结构
# class MessagesState(TypedDict):
#     messages: Annotated[list, add_messages]
# 您可以继承它来添加自己的字段
class MyState(MessagesState):
    additional_field: str
```

```typescript
import { MessagesZodMeta } from "@langchain/langgraph";
import { registry } from "@langchain/langgraph/zod";
import * as z from "zod";
// 创建一个类似MessagesState的Zod模式
const MessagesZodState = z.object({
  messages: z.array(z.any()).register(registry, MessagesZodMeta),
  additionalField: z.string(),
});
```

## 创建单节点图

让我们从创建一个简单的单节点图开始。这将帮助您理解Graph API的基本组件。

### Python

```python
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
# 定义状态
class State(TypedDict):
    count: int
# 定义节点函数
# 节点函数接收当前状态并返回更新后的状态
def my_node(state: State):
    # 读取当前状态
    current_count = state["count"]
    # 返回更新后的状态
    return {"count": current_count + 1}
# 创建图
builder = StateGraph(State)
# 添加节点
builder.add_node("my_node", my_node)
# 添加边（定义控制流）
builder.add_edge(START, "my_node")
builder.add_edge("my_node", END)
# 编译图
graph = builder.compile()
# 执行图
result = graph.invoke({"count": 0})
print(result)
# {'count': 1}
```

### JavaScript

```typescript
import { StateGraph, START, END } from "@langchain/langgraph";
import * as z from "zod";
// 定义状态
const State = z.object({
  count: z.number(),
});
// 定义节点函数
const myNode = (state: z.infer<typeof State>) => {
  // 读取当前状态
  const currentCount = state.count;
  // 返回更新后的状态
  return { count: currentCount + 1 };
};
// 创建图
const graph = new StateGraph(State)
  // 添加节点
  .addNode("myNode", myNode)
  // 添加边（定义控制流）
  .addEdge(START, "myNode")
  .addEdge("myNode", END)
  // 编译图
  .compile();
// 执行图
const result = await graph.invoke({ count: 0 });
console.log(result);
// { count: 1 }
```

## 可视化您的图

您可以使用LangGraph的可视化功能来查看您创建的图的结构。

### Python

```python
from IPython.display import Image, display
# 绘制图并显示
image = graph.get_graph().draw_mermaid_png()
display(Image(image))
```

### JavaScript

```typescript
import * as fs from "node:fs/promises";
// 获取可绘制的图
const drawableGraph = await graph.getGraphAsync();
// 绘制为PNG
const image = await drawableGraph.drawMermaidPng();
// 转换为Buffer
const imageBuffer = new Uint8Array(await image.arrayBuffer());
// 保存到文件
await fs.writeFile("graph.png", imageBuffer);
```

## 添加重试策略

在许多情况下，您可能希望为节点添加自定义重试策略，例如在调用API、查询数据库或调用LLM时。LangGraph允许您为节点添加重试策略。

### Python

要配置重试策略，请将`retry_policy`参数传递给`add_node`。`retry_policy`参数接受一个`RetryPolicy`命名元组对象。

```python
from langgraph.types import RetryPolicy
builder.add_node(
    "node_name",
    node_function,
    retry_policy=RetryPolicy(),
)
```

默认情况下，`retry_on`参数使用`default_retry_on`函数，该函数在任何异常情况下重试，除了以下异常：

- `ValueError`
- `TypeError`
- `ArithmeticError`
- `ImportError`
- `LookupError`
- `NameError`
- `SyntaxError`
- `RuntimeError`
- `ReferenceError`
- `StopIteration`
- `StopAsyncIteration`
- `OSError`

此外，对于来自流行HTTP请求库（如`requests`和`httpx`）的异常，它仅在5xx状态码时重试。

### JavaScript

要配置重试策略，请将`retryPolicy`参数传递给`addNode`。`retryPolicy`参数接受一个`RetryPolicy`对象。

```typescript
import { RetryPolicy } from "@langchain/langgraph";
const graph = new StateGraph(State)
  .addNode("nodeName", nodeFunction, { retryPolicy: {} })
  .compile();
```

默认情况下，重试策略在任何异常情况下重试，除了以下异常：

- `TypeError`
- `SyntaxError`
- `ReferenceError`

## 添加节点缓存

节点缓存在您希望避免重复操作的情况下很有用，例如在执行昂贵的操作（无论是时间还是成本方面）时。LangGraph允许您为图中的节点添加个性化缓存策略。

### Python

要配置缓存策略，请将`cache_policy`参数传递给`add_node`函数。在下面的例子中，一个`CachePolicy`对象使用120秒的生存时间和默认的`key_func`生成器实例化，然后与节点关联：

```python
from langgraph.types import CachePolicy
builder.add_node(
    "node_name",
    node_function,
    cache_policy=CachePolicy(ttl=120),
)
```

然后，要为图启用节点级缓存，请在编译图时设置`cache`参数。下面的例子使用`InMemoryCache`设置一个带有内存缓存的图，但`SqliteCache`也可用。

```python
from langgraph.cache.memory import InMemoryCache
graph = builder.compile(cache=InMemoryCache())
```

## 创建步骤序列

### Python

要添加一系列节点，我们使用图的`add_node`和`add_edge`方法：

```python
from langgraph.graph import START, StateGraph
builder = StateGraph(State)
# 添加节点
builder.add_node(step_1)
builder.add_node(step_2)
builder.add_node(step_3)
# 添加边
builder.add_edge(START, "step_1")
builder.add_edge("step_1", "step_2")
builder.add_edge("step_2", "step_3")
```

我们也可以使用内置的简写`.add_sequence`：

```python
builder = StateGraph(State).add_sequence([step_1, step_2, step_3])
builder.add_edge(START, "step_1")
```

### JavaScript

要添加一系列节点，我们使用图的`.addNode`和`.addEdge`方法：

```typescript
import { START, StateGraph } from "@langchain/langgraph";
const builder = new StateGraph(State)
  .addNode("step1", step1)
  .addNode("step2", step2)
  .addNode("step3", step3)
  .addEdge(START, "step1")
  .addEdge("step1", "step2")
  .addEdge("step2", "step3");
```

## 创建分支

节点的并行执行对于加速整个图操作至关重要。LangGraph提供了对节点并行执行的原生支持，这可以显著提高基于图的工作流的性能。这种并行化是通过扇出和扇入机制实现的，利用标准边和条件边。

### 并行运行图节点

在这个例子中，我们从`节点A`扇出到`B和C`，然后扇入到`D`。对于我们的状态，我们指定reducer的add操作。这将合并或累积State中特定键的值，而不是简单地覆盖现有值。对于列表，这意味着将新列表与现有列表连接起来。

#### Python

```python
import operator
from typing import Annotated, Any
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
class State(TypedDict):
    # operator.add reducer使此仅可追加
    aggregate: Annotated[list, operator.add]
def a(state: State):
    print(f'向 {state["aggregate"]} 添加 "A"')
    return {"aggregate": ["A"]}
def b(state: State):
    print(f'向 {state["aggregate"]} 添加 "B"')
    return {"aggregate": ["B"]}
def c(state: State):
    print(f'向 {state["aggregate"]} 添加 "C"')
    return {"aggregate": ["C"]}
def d(state: State):
    print(f'向 {state["aggregate"]} 添加 "D"')
    return {"aggregate": ["D"]}
builder = StateGraph(State)
builder.add_node(a)
builder.add_node(b)
builder.add_node(c)
builder.add_node(d)
builder.add_edge(START, "a")
builder.add_edge("a", "b")
builder.add_edge("a", "c")
builder.add_edge("b", "d")
builder.add_edge("c", "d")
builder.add_edge("d", END)
graph = builder.compile()
```

#### JavaScript

```typescript
import { StateGraph, START, END } from "@langchain/langgraph";
import { registry } from "@langchain/langgraph/zod";
import * as z from "zod";
const State = z.object({
  // reducer使此仅可追加
  aggregate: z.array(z.string()).register(registry, {
    reducer: {
      fn: (x, y) => x.concat(y),
    },
    default: () => [] as string[],
  }),
});
const nodeA = (state: z.infer<typeof State>) => {
  console.log(`向 ${state.aggregate} 添加 "A"`);
  return { aggregate: ["A"] };
};
const nodeB = (state: z.infer<typeof State>) => {
  console.log(`向 ${state.aggregate} 添加 "B"`);
  return { aggregate: ["B"] };
};
const nodeC = (state: z.infer<typeof State>) => {
  console.log(`向 ${state.aggregate} 添加 "C"`);
  return { aggregate: ["C"] };
};
const nodeD = (state: z.infer<typeof State>) => {
  console.log(`向 ${state.aggregate} 添加 "D"`);
  return { aggregate: ["D"] };
};
const graph = new StateGraph(State)
  .addNode("a", nodeA)
  .addNode("b", nodeB)
  .addNode("c", nodeC)
  .addNode("d", nodeD)
  .addEdge(START, "a")
  .addEdge("a", "b")
  .addEdge("a", "c")
  .addEdge("b", "d")
  .addEdge("c", "d")
  .addEdge("d", END)
  .compile();
```

### 延迟节点执行

延迟节点执行在您希望延迟节点执行直到所有其他挂起任务完成的情况下很有用。这在分支长度不同的工作流中特别相关，这在map-reduce等工作流中很常见。

#### Python

```python
builder.add_node(d, defer=True)
```

### 条件分支

如果您的扇出应该在运行时根据状态变化，您可以使用`add_conditional_edges`使用图状态选择一个或多个路径。

#### Python

```python
def conditional_edge(state: State) -> Literal["b", "c"]:
    # 在这里填写任意逻辑，使用状态
    # 确定下一个节点
    return state["which"]
builder.add_conditional_edges("a", conditional_edge)
```

#### JavaScript

```typescript
const conditionalEdge = (state: z.infer<typeof State>): "b" | "c" => {
  // 在这里填写任意逻辑，使用状态
  // 确定下一个节点
  return state.which as "b" | "c";
};
const graph = new StateGraph(State)
  .addConditionalEdges("a", conditionalEdge)
  .compile();
```

## Map-Reduce和Send API

LangGraph支持使用Send API进行map-reduce和其他高级分支模式。

### Python

```python
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send
from typing_extensions import TypedDict, Annotated
import operator
class OverallState(TypedDict):
    topic: str
    subjects: list[str]
    jokes: Annotated[list[str], operator.add]
    best_selected_joke: str
def generate_topics(state: OverallState):
    return {"subjects": ["lions", "elephants", "penguins"]}
def generate_joke(state: OverallState):
    joke_map = {
        "lions": "为什么狮子不喜欢快餐？因为它们抓不到！",
        "elephants": "为什么大象不用电脑？它们害怕鼠标！",
        "penguins": "为什么企鹅不喜欢在派对上和陌生人交谈？因为它们很难打破僵局。"
    }
    return {"jokes": [joke_map[state["subject"]]]}
def continue_to_jokes(state: OverallState):
    return [Send("generate_joke", {"subject": s}) for s in state["subjects"]]
def best_joke(state: OverallState):
    return {"best_selected_joke": "penguins"}
builder = StateGraph(OverallState)
builder.add_node("generate_topics", generate_topics)
builder.add_node("generate_joke", generate_joke)
builder.add_node("best_joke", best_joke)
builder.add_edge(START, "generate_topics")
builder.add_conditional_edges("generate_topics", continue_to_jokes, ["generate_joke"])
builder.add_edge("generate_joke", "best_joke")
builder.add_edge("best_joke", END)
graph = builder.compile()
```

### JavaScript

```typescript
import { StateGraph, START, END, Send } from "@langchain/langgraph";
import { registry } from "@langchain/langgraph/zod";
import * as z from "zod";
const OverallState = z.object({
  topic: z.string(),
  subjects: z.array(z.string()),
  jokes: z.array(z.string()).register(registry, {
    reducer: {
      fn: (x, y) => x.concat(y),
    },
  }),
  bestSelectedJoke: z.string(),
});
const generateTopics = (state: z.infer<typeof OverallState>) => {
  return { subjects: ["lions", "elephants", "penguins"] };
};
const generateJoke = (state: { subject: string }) => {
  const jokeMap: Record<string, string> = {
    lions: "为什么狮子不喜欢快餐？因为它们抓不到！",
    elephants: "为什么大象不用电脑？它们害怕鼠标！",
    penguins: "为什么企鹅不喜欢在派对上和陌生人交谈？因为它们很难打破僵局。"
  };
  return { jokes: [jokeMap[state.subject]] };
};
const continueToJokes = (state: z.infer<typeof OverallState>) => {
  return state.subjects.map((subject) => new Send("generateJoke", { subject }));
};
const bestJoke = (state: z.infer<typeof OverallState>) => {
  return { bestSelectedJoke: "penguins" };
};
const graph = new StateGraph(OverallState)
  .addNode("generateTopics", generateTopics)
  .addNode("generateJoke", generateJoke)
  .addNode("bestJoke", bestJoke)
  .addEdge(START, "generateTopics")
  .addConditionalEdges("generateTopics", continueToJokes)
  .addEdge("generateJoke", "bestJoke")
  .addEdge("bestJoke", END)
  .compile();
```

## 创建和控制循环

创建带有循环的图时，我们需要一种终止执行的机制。这通常是通过添加一个条件边来实现的，该条件边在达到某个终止条件后路由到END节点。

您还可以在调用或流式传输图时设置图递归限制。递归限制设置了图在引发错误之前允许执行的超级步数。

### Python

```python
import operator
from typing import Annotated, Literal
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
class State(TypedDict):
    # operator.add reducer使此仅可追加
    aggregate: Annotated[list, operator.add]
def a(state: State):
    print(f'节点A看到 {state["aggregate"]}')
    return {"aggregate": ["A"]}
def b(state: State):
    print(f'节点B看到 {state["aggregate"]}')
    return {"aggregate": ["B"]}
# 定义节点
builder = StateGraph(State)
builder.add_node(a)
builder.add_node(b)
# 定义边
def route(state: State) -> Literal["b", END]:
    if len(state["aggregate"]) < 7:
        return "b"
    else:
        return END
builder.add_edge(START, "a")
builder.add_conditional_edges("a", route)
builder.add_edge("b", "a")
graph = builder.compile()
```

### JavaScript

```typescript
import { StateGraph, START, END } from "@langchain/langgraph";
import { registry } from "@langchain/langgraph/zod";
import * as z from "zod";
const State = z.object({
  // reducer使此仅可追加
  aggregate: z.array(z.string()).register(registry, {
    reducer: {
      fn: (x, y) => x.concat(y),
    },
    default: () => [] as string[],
  }),
});
const nodeA = (state: z.infer<typeof State>) => {
  console.log(`节点A看到 ${state.aggregate}`);
  return { aggregate: ["A"] };
};
const nodeB = (state: z.infer<typeof State>) => {
  console.log(`节点B看到 ${state.aggregate}`);
  return { aggregate: ["B"] };
};
// 定义边
const route = (state: z.infer<typeof State>): "b" | typeof END => {
  if (state.aggregate.length < 7) {
    return "b";
  } else {
    return END;
  }
};
const graph = new StateGraph(State)
  .addNode("a", nodeA)
  .addNode("b", nodeB)
  .addEdge(START, "a")
  .addConditionalEdges("a", route)
  .addEdge("b", "a")
  .compile();
```

### 施加递归限制

在某些应用程序中，我们可能不能保证达到给定的终止条件。在这些情况下，我们可以设置图的递归限制。这将在给定数量的超级步骤后引发`GraphRecursionError`。然后我们可以捕获并处理这个异常。

#### Python

```python
from langgraph.errors import GraphRecursionError
try:
    graph.invoke({"aggregate": []}, {"recursion_limit": 4})
except GraphRecursionError:
    print("递归错误")
```

#### JavaScript

```typescript
import { GraphRecursionError } from "@langchain/langgraph";
try {
  await graph.invoke({ aggregate: [] }, { recursionLimit: 4 });
} catch (error) {
  if (error instanceof GraphRecursionError) {
    console.log("递归错误");
  }
}
```

## 使用Command组合控制流和状态更新

组合控制流（边）和状态更新（节点）可能很有用。例如，您可能希望在同一节点中执行状态更新并决定下一步要去哪个节点。LangGraph通过从节点函数返回`Command`对象来提供这种功能。

### Python

```python
def my_node(state: State) -> Command[Literal["my_other_node"]]:
    return Command(
        # 状态更新
        update={"foo": "bar"},
        # 控制流
        goto="my_other_node"
    )
```

### JavaScript

```typescript
import { Command } from "@langchain/langgraph";
const myNode = (state: State): Command => {
  return new Command({
    // 状态更新
    update: { foo: "bar" },
    // 控制流
    goto: "myOtherNode"
  });
};
```

## 异步

使用异步编程范式可以在并发运行IO绑定代码时产生显著的性能改进（例如，对聊天模型提供商进行并发API请求）。

要将图的同步实现转换为异步实现，您需要：

1. 更新节点使用`async def`而不是`def`。
2. 更新内部代码以适当使用`await`。
3. 按需要使用`.ainvoke`或`.astream`调用图。

### Python

```python
from langchain.chat_models import init_chat_model
from langgraph.graph import MessagesState, StateGraph
async def node(state: MessagesState):
    new_message = await llm.ainvoke(state["messages"])
    return {"messages": [new_message]}
builder = StateGraph(MessagesState).add_node(node).set_entry_point("node")
graph = builder.compile()
input_message = {"role": "user", "content": "你好"}
result = await graph.ainvoke({"messages": [input_message]})
```

## 可视化您的图

LangGraph提供了可视化您创建的图的功能。您可以可视化任何任意图，包括StateGraph。

### Mermaid

我们也可以将图类转换为Mermaid语法。

#### Python

```python
print(app.get_graph().draw_mermaid())
```

#### JavaScript

```typescript
const drawableGraph = await app.getGraphAsync();
console.log(drawableGraph.drawMermaid());
```

### PNG

如果您愿意，我们可以将图渲染为`.png`文件。

#### Python

默认情况下，`draw_mermaid_png()`使用Mermaid.Ink的API生成图表。

```python
from IPython.display import Image, display
image = app.get_graph().draw_mermaid_png()
display(Image(image))
```

#### JavaScript

这使用Mermaid.ink API生成图表。

```typescript
import * as fs from "node:fs/promises";
const drawableGraph = await app.getGraphAsync();
const image = await drawableGraph.drawMermaidPng();
const imageBuffer = new Uint8Array(await image.arrayBuffer());
await fs.writeFile("graph.png", imageBuffer);
```

## 总结

本指南介绍了LangGraph的Graph API的核心概念和功能。您现在应该能够：

1. 定义和更新状态
2. 创建单节点和多节点图
3. 添加重试策略和节点缓存
4. 创建步骤序列和分支
5. 实现map-reduce模式
6. 创建和控制循环
7. 使用异步编程
8. 组合控制流和状态更新
9. 可视化您的图

通过这些功能，您可以构建复杂而强大的工作流，以满足各种应用程序需求。