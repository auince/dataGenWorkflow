# Graph API概述

LangGraph 图 API 是一个灵活、强大的工具，用于构建有状态的、基于事件的应用程序。本指南将介绍图 API 的核心概念、组件和使用方法。

## 图

LangGraph 中的图由以下核心组件组成：

1. **状态（State）**：图的全局状态，包含所有节点共享的数据。
2. **节点（Nodes）**：图中的计算单元，处理输入状态并返回更新的状态。
3. **边（Edges）**：定义节点之间的转换规则，控制数据流向。

LangGraph 中的计算基于 [Pregel](https://research.google/pubs/pregel-a-system-for-large-scale-graph-processing/) 模型，这是一种为分布式图处理设计的编程模型。在这个模型中，计算被分解为一系列的 "super-steps"：

1. 在每个 super-step 中，所有节点并行执行。
2. 每个节点接收来自上一步的消息。
3. 每个节点根据消息更新自己的状态。
4. 每个节点向下一个 super-step 中的节点发送消息。
5. 当没有更多的消息要处理时，计算完成。

在 LangGraph 中，super-steps 是隐式的。当您定义图的结构（节点和边）时，LangGraph 会自动处理消息传递和状态更新。

## StateGraph

LangGraph 提供了 `StateGraph` 类，这是构建图的主要接口。`StateGraph` 允许您定义状态结构、添加节点和边，并编译图以供执行。

```python
from typing_extensions import TypedDict
from langgraph.graph import StateGraph

class State(TypedDict):
    input: str
    results: str

builder = StateGraph(State)
# 添加节点
builder.add_node("node1", lambda state: {"results": state["input"] + " processed"})
# 添加边
builder.add_edge("node1", "node2")
# 编译图
graph = builder.compile()
```

```typescript
import { StateGraph } from "@langchain/langgraph";
import * as z from "zod";

const State = z.object({
  input: z.string(),
  results: z.string(),
});

const builder = new StateGraph(State)
  .addNode("node1", (state) => ({
    results: state.input + " processed"
  }))
  .addEdge("node1", "node2")
  .compile();
```

编译后的图是一个 `Runnable` 对象，您可以使用 `invoke` 方法执行它，就像任何其他 LangChain 可运行对象一样：

```python
result = graph.invoke({"input": "hello world"})
print(result)
# {'input': 'hello world', 'results': 'hello world processed'}
```

```typescript
const result = await graph.invoke({ input: "hello world" });
console.log(result);
// { input: 'hello world', results: 'hello world processed' }
```

## 状态

状态是图中所有节点共享的数据。在 LangGraph 中，您可以使用多种方式定义状态：

### Python

在 Python 中，您可以使用以下方式定义状态：

1. **TypedDict**：最常用的方式，提供静态类型检查。
2. **dataclass**：带有默认值的结构化数据类。
3. **Pydantic 模型**：提供验证和序列化。

```python
from typing_extensions import TypedDict
from dataclasses import dataclass
from pydantic import BaseModel

# 使用 TypedDict
class TypedState(TypedDict):
    input: str
    count: int

# 使用 dataclass
@dataclass
class DataclassState:
    input: str
    count: int = 0

# 使用 Pydantic 模型
class PydanticState(BaseModel):
    input: str
    count: int = 0
```

### JavaScript

在 JavaScript 中，您可以使用 Zod schema 或 Annotation API 定义状态：

```typescript
import * as z from "zod";

// 使用 Zod schema
const State = z.object({
  input: z.string(),
  count: z.number().default(0),
});

// 使用 Annotation API
import { createStateAnnotation } from "@langchain/langgraph";
const { State } = createStateAnnotation({ input: "", count: 0 });
```

### 多模式 Schema

LangGraph 支持定义多模式 schema，这允许您定义不同类型的状态用于不同的目的：

1. **InputState**：图的输入状态。
2. **OutputState**：图的输出状态。
3. **OverallState**：图内部使用的完整状态。
4. **PrivateState**：仅对特定节点可见的状态。

```python
from typing_extensions import TypedDict
from langgraph.graph import StateGraph

class InputState(TypedDict):
    input: str

class OverallState(InputState):
    intermediate: str

class OutputState(TypedDict):
    output: str

builder = StateGraph(OverallState)
# 添加节点
builder.add_node("node1", lambda state: {"intermediate": state["input"] + " processed"})
builder.add_node("node2", lambda state: {"output": state["intermediate"] + " again"})
# 添加边
builder.add_edge("node1", "node2")
# 编译图并指定输出状态
graph = builder.compile(output_schema=OutputState)
```

```typescript
import { StateGraph } from "@langchain/langgraph";
import * as z from "zod";

const InputState = z.object({
  input: z.string(),
});

const OverallState = InputState.extend({
  intermediate: z.string(),
});

const OutputState = z.object({
  output: z.string(),
});

const builder = new StateGraph(OverallState)
  .addNode("node1", (state) => ({
    intermediate: state.input + " processed"
  }))
  .addNode("node2", (state) => ({
    output: state.intermediate + " again"
  }))
  .addEdge("node1", "node2")
  .compile({ outputSchema: OutputState });
```

### Reducers

Reducers 定义了如何将节点的输出合并到全局状态中。LangGraph 提供了以下内置 reducers：

1. **默认 reducer**：简单地将节点的输出与全局状态合并。
2. **消息 reducer**：用于合并消息列表。
3. **自定义 reducer**：您可以定义自己的 reducer 函数。

```python
from typing import List
from typing_extensions import TypedDict, Annotated
from langgraph.graph import StateGraph, add_messages

class State(TypedDict):
    # 使用 add_messages reducer
    messages: Annotated[List[str], add_messages]
    # 使用自定义 reducer
    count: int

def custom_reducer(left: int, right: int) -> int:
    return left + right

builder = StateGraph(State)
# 添加节点并指定 reducer
builder.add_node("node1", lambda state: {"count": 1}, reducers={"count": custom_reducer})
builder.add_edge("node1", "node2")
builder.add_node("node2", lambda state: {"count": 2}, reducers={"count": custom_reducer})
# 编译图
graph = builder.compile()
```

```typescript
import { StateGraph, MessagesZodMeta } from "@langchain/langgraph";
import { registry } from "@langchain/langgraph/zod";
import * as z from "zod";

// 使用 MessagesZodMeta 为消息字段添加 reducer
const State = z.object({
  messages: z.array(z.string()).register(registry, MessagesZodMeta),
  count: z.number(),
});

function customReducer(left: number, right: number): number {
  return left + right;
}

const builder = new StateGraph(State)
  // 添加节点并指定 reducer
  .addNode("node1", (state) => ({ count: 1 }), {
    reducers: { count: customReducer }
  })
  .addEdge("node1", "node2")
  .addNode("node2", (state) => ({ count: 2 }), {
    reducers: { count: customReducer }
  })
  .compile();
```

### 图状态中的消息

在构建聊天应用程序时，通常需要在状态中存储消息历史。LangGraph 提供了特殊的支持来处理消息：

```python
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph, add_messages

class State(TypedDict):
    messages: list[BaseMessage]

builder = StateGraph(State)
# 添加节点并使用 add_messages reducer
builder.add_node("node1", lambda state: {"messages": [HumanMessage(content="Hello")]}, reducers={"messages": add_messages})
```

为了简化这个常见用例，LangGraph 提供了 `MessagesState` 预定义状态：

```python
from langgraph.graph import MessagesState

class State(MessagesState):
    documents: list[str]
```

```typescript
import { MessagesZodMeta } from "@langchain/langgraph";
import { registry } from "@langchain/langgraph/zod";
import * as z from "zod";

const MessagesZodState = z.object({
  messages: z
    .array(z.custom())
    .register(registry, MessagesZodMeta),
});
```

## 节点

在 LangGraph 中，节点是接收图状态并返回更新的状态的函数。您可以使用 `add_node` 方法将节点添加到图中。

```python
from typing_extensions import TypedDict
from langgraph.graph import StateGraph
from langgraph.runtime import Runtime
from langchain_core.runnables import RunnableConfig

class State(TypedDict):
    input: str
    results: str

def my_node(state: State, config: RunnableConfig, runtime: Runtime):
    print(f"Thread ID: {config['configurable']['thread_id']}")
    return {"results": f"Hello, {state['input']}!"}

builder = StateGraph(State)
builder.add_node("my_node", my_node)
```

```typescript
import { StateGraph } from "@langchain/langgraph";
import * as z from "zod";

const State = z.object({
  input: z.string(),
  results: z.string(),
});

const builder = new StateGraph(State)
  .addNode("myNode", (state, config) => {
    console.log(`Thread ID: ${config?.configurable?.thread_id}`);
    return { results: `Hello, ${state.input}!` };
  });
```

### 特殊节点

LangGraph 提供了两个特殊节点：

1. **START**：表示图的入口点，用户输入由此进入图。
2. **END**：表示图的终止点，到达此节点时图执行结束。

```python
from langgraph.graph import StateGraph, START, END

class State(TypedDict):
    input: str

builder = StateGraph(State)
builder.add_node("process", lambda state: state)
builder.add_edge(START, "process")
builder.add_edge("process", END)
```

```typescript
import { StateGraph, START, END } from "@langchain/langgraph";
import * as z from "zod";

const State = z.object({
  input: z.string(),
});

const builder = new StateGraph(State)
  .addNode("process", (state) => state)
  .addEdge(START, "process")
  .addEdge("process", END);
```

### 节点缓存

LangGraph 支持基于节点输入的缓存功能，可以提高性能并减少重复计算：

```python
import time
from typing_extensions import TypedDict
from langgraph.graph import StateGraph
from langgraph.cache.memory import InMemoryCache
from langgraph.types import CachePolicy

class State(TypedDict):
    x: int
    result: int

def expensive_node(state: State) -> dict[str, int]:
    # 模拟耗时计算
    time.sleep(2)
    return {"result": state["x"] * 2}

builder = StateGraph(State)
builder.add_node("expensive_node", expensive_node, cache_policy=CachePolicy(ttl=3))
builder.set_entry_point("expensive_node")
builder.set_finish_point("expensive_node")
# 编译图并指定缓存
graph = builder.compile(cache=InMemoryCache())
```

## 边

边定义了图中节点之间的转换规则。LangGraph 支持以下类型的边：

### 普通边

普通边直接从一个节点连接到另一个节点：

```python
graph.add_edge("node_a", "node_b")
```

```typescript
graph.addEdge("nodeA", "nodeB");
```

### 条件边

条件边根据自定义逻辑决定下一个要执行的节点：

```python
def routing_function(state: State):
    if state["count"] > 0:
        return "node_b"
    else:
        return "node_c"

graph.add_conditional_edges("node_a", routing_function)
```

```typescript
function routingFunction(state: any) {
  if (state.count > 0) {
    return "nodeB";
  } else {
    return "nodeC";
  }
}

graph.addConditionalEdges("nodeA", routingFunction);
```

### 入口点

入口点定义了图开始执行时首先调用的节点：

```python
from langgraph.graph import START
graph.add_edge(START, "node_a")
```

```typescript
import { START } from "@langchain/langgraph";
graph.addEdge(START, "nodeA");
```

### 条件入口点

条件入口点允许根据自定义逻辑决定从哪个节点开始执行：

```python
from langgraph.graph import START
graph.add_conditional_edges(START, routing_function)
```

```typescript
import { START } from "@langchain/langgraph";
graph.addConditionalEdges(START, routingFunction);
```

## Send

`Send` 是一个特殊的对象，允许您动态地将状态发送到其他节点，特别适用于 map-reduce 设计模式：

```python
from langgraph.graph import StateGraph, Send
from typing_extensions import TypedDict

class OverallState(TypedDict):
    subjects: list[str]

class JokeState(TypedDict):
    subject: str

def continue_to_jokes(state: OverallState):
    return [Send("generate_joke", {"subject": s}) for s in state['subjects']]

builder = StateGraph(OverallState)
builder.add_conditional_edges("node_a", continue_to_jokes)
```

```typescript
import { StateGraph, Send } from "@langchain/langgraph";
import * as z from "zod";

const graph = new StateGraph(State)
  .addConditionalEdges("nodeA", (state) => {
    return state.subjects.map((subject) => new Send("generateJoke", { subject }));
  });
```

## Command

`Command` 对象允许您在单个节点中同时执行状态更新和控制流：

```python
from langgraph.graph import StateGraph, Command
from typing_extensions import TypedDict, Literal

class State(TypedDict):
    foo: str

def my_node(state: State) -> Command[Literal["my_other_node"]]:
    return Command(
        # 状态更新
        update={"foo": "bar"},
        # 控制流
        goto="my_other_node"
    )

builder = StateGraph(State)
builder.add_node("my_node", my_node)
builder.add_node("my_other_node", lambda state: state)
builder.add_edge("my_other_node", END)
```

```typescript
import { StateGraph, Command, END } from "@langchain/langgraph";
import * as z from "zod";

const builder = new StateGraph(State)
  .addNode("myNode", (state) => {
    return new Command({
      update: { foo: "bar" },
      goto: "myOtherNode",
    });
  }, { ends: ["myOtherNode", END] })
  .addNode("myOtherNode", (state) => state)
  .addEdge("myOtherNode", END);
```

### 在父图中导航到节点

在使用子图时，您可以使用 `Command.PARENT` 在子图内部导航到父图中的节点：

```python
def my_node(state: State) -> Command[Literal["other_subgraph"]]:
    return Command(
        update={"foo": "bar"},
        goto="other_subgraph",  # 其中 other_subgraph 是父图中的节点
        graph=Command.PARENT
    )
```

```typescript
graph.addNode("myNode", (state) => {
  return new Command({
    update: { foo: "bar" },
    goto: "otherSubgraph", // 其中 otherSubgraph 是父图中的节点
    graph: Command.PARENT,
  });
});
```

### 在工具中使用

在工具中使用 `Command` 是一个常见用例，例如在客户支持应用中，您可能需要根据客户的账号或ID查找客户信息。

### 人机交互循环

`Command` 是人机交互工作流的重要组成部分：当使用 `interrupt()` 收集用户输入时，然后使用 `Command(resume="用户输入")` 提供输入并恢复执行。

## 图迁移

LangGraph 可以轻松处理图定义（节点、边和状态）的迁移，即使使用检查点来跟踪状态：

- 对于已完成的线程（即未中断的线程），您可以更改图的整个拓扑结构（所有节点和边，添加、删除、重命名等）
- 对于当前中断的线程，我们支持除重命名/删除节点之外的所有拓扑更改（因为该线程现在可能即将进入不再存在的节点）
- 对于修改状态，我们对添加和删除键有完全的向后和向前兼容性
- 重命名的状态键会丢失现有线程中的保存状态
- 类型以不兼容方式更改的状态键可能会在具有更改前状态的线程中导致问题

## 运行时上下文

创建图时，您可以为传递给节点的运行时上下文指定 `context_schema`。这对于传递不属于图状态的信息非常有用。例如，您可能想要传递依赖项，如模型名称或数据库连接。

```python
from dataclasses import dataclass
from langgraph.graph import StateGraph

@dataclass
class ContextSchema:
    llm_provider: str = "openai"

graph = StateGraph(State, context_schema=ContextSchema)
# 使用 context 参数将上下文传递到图中
graph.invoke(inputs, context={"llm_provider": "anthropic"})
```

```typescript
import * as z from "zod";
import { StateGraph } from "@langchain/langgraph";

const ContextSchema = z.object({
  llm: z.union([z.literal("openai"), z.literal("anthropic")]),
});

const graph = new StateGraph(State, ContextSchema);
// 使用 context 属性将配置传递到图中
const config = { context: { llm: "anthropic" } };
await graph.invoke(inputs, config);
```

然后，您可以在节点或条件边中访问和使用此上下文：

```python
from langgraph.runtime import Runtime

def node_a(state: State, runtime: Runtime[ContextSchema]):
    llm = get_llm(runtime.context.llm_provider)
    # ...
```

```typescript
import { Runtime } from "@langchain/langgraph";
import * as z from "zod";

const nodeA = (
  state: z.infer<typeof State>,
  runtime: Runtime<z.infer<typeof ContextSchema>>,
) => {
  const llm = getLLM(runtime.context?.llm);
  // ...
};
```

### 递归限制

递归限制设置了图在单次执行期间可以执行的最大 super-step 数。一旦达到限制，LangGraph 将抛出 `GraphRecursionError`。默认值设置为 25 步。递归限制可以在运行时设置在任何图上，并通过配置字典传递给 `invoke`/`stream`。重要的是，`recursion_limit` 是一个独立的 `config` 键，不应像所有其他用户定义的配置一样传递到 `configurable` 键内部。

```python
graph.invoke(inputs, config={"recursion_limit": 5}, context={"llm": "anthropic"})
```

```typescript
await graph.invoke(inputs, {
  recursionLimit: 5,
  context: { llm: "anthropic" },
});
```

## 可视化

通常，能够可视化图是很有用的，尤其是当它们变得更复杂时。LangGraph 提供了几种内置的方式来可视化图。