# LangGraph 运行时

`Pregel` 实现了LangGraph的运行时，管理LangGraph应用程序的执行。编译`StateGraph`或创建`@entrypoint`会生成一个`Pregel`实例，可以用输入来调用。

本指南从高级层面解释了运行时，并提供了直接使用Pregel实现应用程序的指导。

> 注意：`Pregel`运行时的命名源于[Google的Pregel算法](https://research.google/pubs/pub37252/)，该算法描述了一种使用图进行大规模并行计算的高效方法。

## 概述

在LangGraph中，Pregel将[**actors**](https://en.wikipedia.org/wiki/Actor_model)和**channels**组合成一个单一应用程序。**Actors**从channels读取数据并向channels写入数据。Pregel将应用程序的执行组织成多个步骤，遵循**Pregel算法**/**Bulk Synchronous Parallel**模型。

每个步骤包含三个阶段：

- **计划**：确定在这一步骤中执行哪些**actors**。例如，在第一步中，选择订阅特殊**input** channels的**actors**；在后续步骤中，选择订阅上一步骤中更新的channels的**actors**。
- **执行**：并行执行所有选定的**actors**，直到全部完成，或一个失败，或达到超时。在这个阶段，channel更新对actors是不可见的，直到下一步。
- **更新**：使用此步骤中**actors**写入的值更新channels。

重复直到没有**actors**被选择执行，或达到最大步骤数。

## Actors

**Actor**是一个`PregelNode`。它订阅channels，从它们读取数据，并向它们写入数据。它可以被视为Pregel算法中的一个**actor**。`PregelNodes`实现了LangChain的Runnable接口。

## Channels

Channels用于actors（PregelNodes）之间的通信。每个channel都有一个值类型、一个更新类型和一个更新函数——它接收一系列更新并修改存储的值。Channels可用于从一个链向另一个链发送数据，或在未来步骤中从一个链向自身发送数据。LangGraph提供了多种内置channels：

- `LastValue`：默认channel，存储发送到channel的最后一个值，适用于输入和输出值，或用于从一个步骤向下一步骤发送数据。
- `Topic`：可配置的PubSub Topic，适用于在**actors**之间发送多个值，或用于累积输出。可以配置为去重值或在多个步骤过程中累积值。
- `BinaryOperatorAggregate`：存储一个持久值，通过对当前值和发送到channel的每个更新应用二元运算符来更新，适用于计算多个步骤的聚合；例如，`total = BinaryOperatorAggregate(int, operator.add)`

## 示例

虽然大多数用户会通过`StateGraph` API或`@entrypoint`装饰器与Pregel交互，但也可以直接与Pregel交互。

### 单个节点

#### Python

```python
from langgraph.channels import EphemeralValue
from langgraph.pregel import Pregel, NodeBuilder
node1 = (
    NodeBuilder().subscribe_only("a")
    .do(lambda x: x + x)
    .write_to("b")
)
app = Pregel(
    nodes={"node1": node1},
    channels={
        "a": EphemeralValue(str),
        "b": EphemeralValue(str),
    },
    input_channels=["a"],
    output_channels=["b"],
)
app.invoke({"a": "foo"})
```

```
{'b': 'foofoo'}
```

#### JavaScript

```typescript
import { EphemeralValue } from "@langchain/langgraph/channels";
import { Pregel, NodeBuilder } from "@langchain/langgraph/pregel";
const node1 = new NodeBuilder()
  .subscribeOnly("a")
  .do((x: string) => x + x)
  .writeTo("b");
const app = new Pregel({
  nodes: { node1 },
  channels: {
    a: new EphemeralValue<string>(),
    b: new EphemeralValue<string>(),
  },
  inputChannels: ["a"],
  outputChannels: ["b"],
});
await app.invoke({ a: "foo" });
```

```
{ b: 'foofoo' }
```

### 多个节点

#### Python

```python
from langgraph.channels import LastValue, EphemeralValue
from langgraph.pregel import Pregel, NodeBuilder
node1 = (
    NodeBuilder().subscribe_only("a")
    .do(lambda x: x + x)
    .write_to("b")
)
node2 = (
    NodeBuilder().subscribe_only("b")
    .do(lambda x: x + x)
    .write_to("c")
)
app = Pregel(
    nodes={"node1": node1, "node2": node2},
    channels={
        "a": EphemeralValue(str),
        "b": LastValue(str),
        "c": EphemeralValue(str),
    },
    input_channels=["a"],
    output_channels=["b", "c"],
)
app.invoke({"a": "foo"})
```

```
{'b': 'foofoo', 'c': 'foofoofoofoo'}
```

#### JavaScript

```typescript
import { LastValue, EphemeralValue } from "@langchain/langgraph/channels";
import { Pregel, NodeBuilder } from "@langchain/langgraph/pregel";
const node1 = new NodeBuilder()
  .subscribeOnly("a")
  .do((x: string) => x + x)
  .writeTo("b");
const node2 = new NodeBuilder()
  .subscribeOnly("b")
  .do((x: string) => x + x)
  .writeTo("c");
const app = new Pregel({
  nodes: { node1, node2 },
  channels: {
    a: new EphemeralValue<string>(),
    b: new LastValue<string>(),
    c: new EphemeralValue<string>(),
  },
  inputChannels: ["a"],
  outputChannels: ["b", "c"],
});
await app.invoke({ a: "foo" });
```

```
{ b: 'foofoo', c: 'foofoofoofoo' }
```

### Topic

#### Python

```python
from langgraph.channels import EphemeralValue, Topic
from langgraph.pregel import Pregel, NodeBuilder
node1 = (
    NodeBuilder().subscribe_only("a")
    .do(lambda x: x + x)
    .write_to("b", "c")
)
node2 = (
    NodeBuilder().subscribe_to("b")
    .do(lambda x: x["b"] + x["b"])
    .write_to("c")
)
app = Pregel(
    nodes={"node1": node1, "node2": node2},
    channels={
        "a": EphemeralValue(str),
        "b": EphemeralValue(str),
        "c": Topic(str, accumulate=True),
    },
    input_channels=["a"],
    output_channels=["c"],
)
app.invoke({"a": "foo"})
```

```
{'c': ['foofoo', 'foofoofoofoo']}
```

#### JavaScript

```typescript
import { EphemeralValue, Topic } from "@langchain/langgraph/channels";
import { Pregel, NodeBuilder } from "@langchain/langgraph/pregel";
const node1 = new NodeBuilder()
  .subscribeOnly("a")
  .do((x: string) => x + x)
  .writeTo("b", "c");
const node2 = new NodeBuilder()
  .subscribeTo("b")
  .do((x: { b: string }) => x.b + x.b)
  .writeTo("c");
const app = new Pregel({
  nodes: { node1, node2 },
  channels: {
    a: new EphemeralValue<string>(),
    b: new EphemeralValue<string>(),
    c: new Topic<string>({ accumulate: true }),
  },
  inputChannels: ["a"],
  outputChannels: ["c"],
});
await app.invoke({ a: "foo" });
```

```
{ c: ['foofoo', 'foofoofoofoo'] }
```

### BinaryOperatorAggregate

此示例演示如何使用`BinaryOperatorAggregate` channel实现reducer。

#### Python

```python
from langgraph.channels import EphemeralValue, BinaryOperatorAggregate
from langgraph.pregel import Pregel, NodeBuilder
node1 = (
    NodeBuilder().subscribe_only("a")
    .do(lambda x: x + x)
    .write_to("b", "c")
)
node2 = (
    NodeBuilder().subscribe_only("b")
    .do(lambda x: x + x)
    .write_to("c")
)
def reducer(current, update):
    if current:
        return current + " | " + update
    else:
        return update
app = Pregel(
    nodes={"node1": node1, "node2": node2},
    channels={
        "a": EphemeralValue(str),
        "b": EphemeralValue(str),
        "c": BinaryOperatorAggregate(str, operator=reducer),
    },
    input_channels=["a"],
    output_channels=["c"],
)
app.invoke({"a": "foo"})
```

#### JavaScript

```typescript
import { EphemeralValue, BinaryOperatorAggregate } from "@langchain/langgraph/channels";
import { Pregel, NodeBuilder } from "@langchain/langgraph/pregel";
const node1 = new NodeBuilder()
  .subscribeOnly("a")
  .do((x: string) => x + x)
  .writeTo("b", "c");
const node2 = new NodeBuilder()
  .subscribeOnly("b")
  .do((x: string) => x + x)
  .writeTo("c");
const reducer = (current: string, update: string) => {
  if (current) {
    return current + " | " + update;
  } else {
    return update;
  }
};
const app = new Pregel({
  nodes: { node1, node2 },
  channels: {
    a: new EphemeralValue<string>(),
    b: new EphemeralValue<string>(),
    c: new BinaryOperatorAggregate<string>({ operator: reducer }),
  },
  inputChannels: ["a"],
  outputChannels: ["c"],
});
await app.invoke({ a: "foo" });
```

### 循环

#### Python

此示例演示如何在图中引入循环，通过让一个链写入它订阅的channel。执行将继续，直到向channel写入`None`值。

```python
from langgraph.channels import EphemeralValue
from langgraph.pregel import Pregel, NodeBuilder, ChannelWriteEntry
example_node = (
    NodeBuilder().subscribe_only("value")
    .do(lambda x: x + x if len(x) < 10 else None)
    .write_to(ChannelWriteEntry("value", skip_none=True))
)
app = Pregel(
    nodes={"example_node": example_node},
    channels={
        "value": EphemeralValue(str),
    },
    input_channels=["value"],
    output_channels=["value"],
)
app.invoke({"value": "a"})
```

```
{'value': 'aaaaaaaaaaaaaaaa'}
```

#### JavaScript

此示例演示如何在图中引入循环，通过让一个链写入它订阅的channel。执行将继续，直到向channel写入`null`值。

```typescript
import { EphemeralValue } from "@langchain/langgraph/channels";
import { Pregel, NodeBuilder, ChannelWriteEntry } from "@langchain/langgraph/pregel";
const exampleNode = new NodeBuilder()
  .subscribeOnly("value")
  .do((x: string) => x.length < 10 ? x + x : null)
  .writeTo(new ChannelWriteEntry("value", { skipNone: true }));
const app = new Pregel({
  nodes: { exampleNode },
  channels: {
    value: new EphemeralValue<string>(),
  },
  inputChannels: ["value"],
  outputChannels: ["value"],
});
await app.invoke({ value: "a" });
```

```
{ value: 'aaaaaaaaaaaaaaaa' }
```

## 高级API

LangGraph提供了两种用于创建Pregel应用程序的高级API：[StateGraph (图API)](https://langchain-doc.cn/v1/python/langgraph/graph-api)和[功能API](https://langchain-doc.cn/v1/python/langgraph/functional-api)。

### StateGraph (图API)

`StateGraph (图API)`是一个更高级的抽象，简化了Pregel应用程序的创建。它允许您定义节点和边的图。当您编译图时，StateGraph API会自动为您创建Pregel应用程序。

#### Python

```python
from typing import TypedDict
from langgraph.constants import START
from langgraph.graph import StateGraph
class Essay(TypedDict):
    topic: str
    content: str | None
    score: float | None
def write_essay(essay: Essay):
    return {
        "content": f"Essay about {essay['topic']}",
    }
def score_essay(essay: Essay):
    return {
        "score": 10
    }
builder = StateGraph(Essay)
builder.add_node(write_essay)
builder.add_node(score_essay)
builder.add_edge(START, "write_essay")
builder.add_edge("write_essay", "score_essay")
# 编译图。
# 这将返回一个Pregel实例。
graph = builder.compile()
```

编译的Pregel实例将与节点和channel的列表相关联。您可以通过打印它们来检查节点和channel。

```python
print(graph.nodes)
```

您将看到类似这样的内容：

```
{'__start__': <langgraph.pregel.read.PregelNode at 0x7d05e3ba1810>,
 'write_essay': <langgraph.pregel.read.PregelNode at 0x7d05e3ba14d0>,
 'score_essay': <langgraph.pregel.read.PregelNode at 0x7d05e3ba1710>}
```

```python
print(graph.channels)
```

您应该看到类似这样的内容

```
{'topic': <langgraph.channels.last_value.LastValue at 0x7d05e3294d80>,
 'content': <langgraph.channels.last_value.LastValue at 0x7d05e3295040>,
 'score': <langgraph.channels.last_value.LastValue at 0x7d05e3295980>,
 '__start__': <langgraph.channels.ephemeral_value.EphemeralValue at 0x7d05e3297e00>,
 'write_essay': <langgraph.channels.ephemeral_value.EphemeralValue at 0x7d05e32960c0>,
 'score_essay': <langgraph.channels.ephemeral_value.EphemeralValue at 0x7d05e2d8ab80>,
 'branch:__start__:__self__:write_essay': <langgraph.channels.ephemeral_value.EphemeralValue at 0x7d05e32941c0>,
 'branch:__start__:__self__:score_essay': <langgraph.channels.ephemeral_value.EphemeralValue at 0x7d05e2d88800>,
 'branch:write_essay:__self__:write_essay': <langgraph.channels.ephemeral_value.EphemeralValue at 0x7d05e3295ec0>,
 'branch:write_essay:__self__:score_essay': <langgraph.channels.ephemeral_value.EphemeralValue at 0x7d05e2d8ac00>,
 'branch:score_essay:__self__:write_essay': <langgraph.channels.ephemeral_value.EphemeralValue at 0x7d05e2d89700>,
 'branch:score_essay:__self__:score_essay': <langgraph.channels.ephemeral_value.EphemeralValue at 0x7d05e2d8b400>,
 'start:write_essay': <langgraph.channels.ephemeral_value.EphemeralValue at 0x7d05e2d8b280>}
```

#### JavaScript

```typescript
import { START, StateGraph } from "@langchain/langgraph";
interface Essay {
  topic: string;
  content?: string;
  score?: number;
}
const writeEssay = (essay: Essay) => {
  return {
    content: `Essay about ${essay.topic}`,
  };
};
const scoreEssay = (essay: Essay) => {
  return {
    score: 10
  };
};
const builder = new StateGraph<Essay>({
  channels: {
    topic: null,
    content: null,
    score: null,
  }
})
  .addNode("writeEssay", writeEssay)
  .addNode("scoreEssay", scoreEssay)
  .addEdge(START, "writeEssay")
  .addEdge("writeEssay", "scoreEssay");
// 编译图。
// 这将返回一个Pregel实例。
const graph = builder.compile();
```

编译的Pregel实例将与节点和channel的列表相关联。您可以通过打印它们来检查节点和channel。

```typescript
console.log(graph.nodes);
```

您将看到类似这样的内容：

```
{
  __start__: PregelNode { ... },
  writeEssay: PregelNode { ... },
  scoreEssay: PregelNode { ... }
}
```

```typescript
console.log(graph.channels);
```

您应该看到类似这样的内容

```
{
  topic: LastValue { ... },
  content: LastValue { ... },
  score: LastValue { ... },
  __start__: EphemeralValue { ... },
  writeEssay: EphemeralValue { ... },
  scoreEssay: EphemeralValue { ... },
  'branch:__start__:__self__:writeEssay': EphemeralValue { ... },
  'branch:__start__:__self__:scoreEssay': EphemeralValue { ... },
  'branch:writeEssay:__self__:writeEssay': EphemeralValue { ... },
  'branch:writeEssay:__self__:scoreEssay': EphemeralValue { ... },
  'branch:scoreEssay:__self__:writeEssay': EphemeralValue { ... },
  'branch:scoreEssay:__self__:scoreEssay': EphemeralValue { ... },
  'start:writeEssay': EphemeralValue { ... }
}
```

### 功能API

#### Python

在[功能API](https://langchain-doc.cn/v1/python/langgraph/functional-api)中，您可以使用`@entrypoint`创建Pregel应用程序。`entrypoint`装饰器允许您定义一个接收输入并返回输出的函数。

```python
from typing import TypedDict
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.func import entrypoint
class Essay(TypedDict):
    topic: str
    content: str | None
    score: float | None
checkpointer = InMemorySaver()
@entrypoint(checkpointer=checkpointer)
def write_essay(essay: Essay):
    return {
        "content": f"Essay about {essay['topic']}",
    }
print("Nodes: ")
print(write_essay.nodes)
print("Channels: ")
print(write_essay.channels)
```

```
Nodes:
{'write_essay': <langgraph.pregel.read.PregelNode object at 0x7d05e2f9aad0>}
Channels:
{'__start__': <langgraph.channels.ephemeral_value.EphemeralValue object at 0x7d05e2c906c0>, '__end__': <langgraph.channels.last_value.LastValue object at 0x7d05e2c90c40>, '__previous__': <langgraph.channels.last_value.LastValue object at 0x7d05e1007280>}
```

#### JavaScript

在[功能API](https://langchain-doc.cn/v1/python/langgraph/functional-api)中，您可以使用`entrypoint`创建Pregel应用程序。`entrypoint`装饰器允许您定义一个接收输入并返回输出的函数。

```typescript
import { MemorySaver } from "@langchain/langgraph";
import { entrypoint } from "@langchain/langgraph/func";
interface Essay {
  topic: string;
  content?: string;
  score?: number;
}
const checkpointer = new MemorySaver();
const writeEssay = entrypoint(
  { checkpointer, name: "writeEssay" },
  async (essay: Essay) => {
    return {
      content: `Essay about ${essay.topic}`,
    };
  }
);
console.log("Nodes: ");
console.log(writeEssay.nodes);
console.log("Channels: ");
console.log(writeEssay.channels);
```

```
Nodes:
{ writeEssay: PregelNode { ... } }
Channels:
{
  __start__: EphemeralValue { ... },
  __end__: LastValue { ... },
  __previous__: LastValue { ... }
}