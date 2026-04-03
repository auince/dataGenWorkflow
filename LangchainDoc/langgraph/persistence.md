# 持久化

LangGraph 支持图状态的持久化和重放。在本文档中，我们将探讨如何通过检查点（checkpointing）来持久化图状态，以及如何利用这些检查点执行图的重放和状态更新。

## 检查点

检查点是图状态的快照，在图的每个超级步骤（superstep）执行后保存。每个检查点都与一个**线程（thread）**相关联，线程是检查点的集合。

### 线程

线程是与特定执行实例相关联的检查点集合。线程通过 `thread_id` 进行标识，这是一个字符串，可以是您想要的任何内容（例如会话 ID、用户 ID、对话 ID 等）。

当您调用图时，可以指定 `thread_id` 作为图配置的一部分。如果您不提供 `thread_id`，LangGraph 会自动生成一个。

要配置 `thread_id`，您需要将其作为 `configurable` 部分的一部分传递给图调用：

```python
config = {"configurable": {"thread_id": "1"}}
graph.invoke(..., config=config)
```

```typescript
const config = { configurable: { thread_id: "1" } };
await graph.invoke(..., { config });
```

### 检查点结构

每个检查点都是一个 `StateSnapshot` 对象，其中包含：

- `values`: 图状态的值
- `next`: 下一个要执行的节点
- `config`: 检查点配置，包括 `thread_id` 和 `checkpoint_id`
- `metadata`: 关于检查点的元数据，如源节点和写入的内容
- `created_at`: 创建时间
- `parent_config`: 父检查点的配置
- `tasks`: 与检查点相关的任务

### 示例：检查点的保存

让我们通过一个简单的例子来说明检查点是如何保存的。首先，我们需要创建一个图并启用检查点：

```python
from langgraph.graph import StateGraph
from langgraph.checkpoint.memory import InMemorySaver
from typing import TypedDict
class State(TypedDict):
    foo: str
    bar: list[str]
def node_a(state: State) -> State:
    return {"foo": "a", "bar": ["a"]}
def node_b(state: State) -> State:
    return {"foo": "b", "bar": ["b"]}
# 创建图
graph = StateGraph(State)
graph.add_node("node_a", node_a)
graph.add_node("node_b", node_b)
# 设置边
graph.add_edge("__start__", "node_a")
graph.add_edge("node_a", "node_b")
# 创建检查点
saver = InMemorySaver()
# 编译图时启用检查点
graph = graph.compile(checkpointer=saver)
```

```typescript
import { StateGraph } from "@langchain/langgraph";
import { MemorySaver } from "@langchain/langgraph/checkpoint";
import { z } from "zod";
const State = z.object({
  foo: z.string(),
  bar: z.array(z.string()),
});
function nodeA(state: z.infer<typeof State>) {
  return { foo: "a", bar: ["a"] };
}
function nodeB(state: z.infer<typeof State>) {
  return { foo: "b", bar: ["b"] };
}
// 创建图
const workflow = new StateGraph(State);
workflow.addNode("nodeA", nodeA);
workflow.addNode("nodeB", nodeB);
// 设置边
workflow.addEdge("__start__", "nodeA");
workflow.addEdge("nodeA", "nodeB");
// 创建检查点
const saver = new MemorySaver();
// 编译图时启用检查点
const graph = workflow.compile({ checkpointer: saver });
```

现在，让我们调用这个图，指定一个 `thread_id`：

```python
config = {"configurable": {"thread_id": "1"}}
graph.invoke({"foo": "", "bar": []}, config=config)
```

```typescript
const config = { configurable: { thread_id: "1" } };
await graph.invoke({ foo: "", bar: [] }, { config });
```

当我们调用图时，LangGraph 会在每个超级步骤后保存检查点。在这个例子中，它会保存以下检查点：

1. 初始状态（在调用 `__start__` 之前）
2. 调用 `node_a` 后的状态
3. 调用 `node_b` 后的状态

### 获取状态

我们可以使用 `get_state` 方法获取特定检查点的状态。这可以通过指定 `thread_id` 和可选的 `checkpoint_id` 来完成：

```python
# 获取最新的状态快照
config = {"configurable": {"thread_id": "1"}}
graph.get_state(config)
# 获取特定检查点 ID 的状态快照
config = {
  "configurable": {
    "thread_id": "1",
    "checkpoint_id": "1ef663ba-28fe-6528-8002-5a559208592c",
  },
}
graph.get_state(config)
```

```typescript
// 获取最新的状态快照
const config = { configurable: { thread_id: "1" } };
await graph.getState(config);
// 获取特定检查点 ID 的状态快照
const config = {
  configurable: {
    thread_id: "1",
    checkpoint_id: "1ef663ba-28fe-6528-8002-5a559208592c",
  },
};
await graph.getState(config);
```

在我们的例子中，`get_state` 的输出将如下所示：

```
StateSnapshot(
    values={'foo': 'b', 'bar': ['a', 'b']},
    next=(),
    config={'configurable': {'thread_id': '1', 'checkpoint_ns': '', 'checkpoint_id': '1ef663ba-28fe-6528-8002-5a559208592c'}},
    metadata={'source': 'loop', 'writes': {'node_b': {'foo': 'b', 'bar': ['b']}}, 'step': 2},
    created_at='2024-08-29T19:19:38.821749+00:00',
    parent_config={'configurable': {'thread_id': '1', 'checkpoint_ns': '', 'checkpoint_id': '1ef663ba-28f9-6ec4-8001-31981c2c39f8'}},
    tasks=()
)
```

```typescript
StateSnapshot {
  values: { foo: 'b', bar: ['a', 'b'] },
  next: [],
  config: {
    configurable: {
      thread_id: '1',
      checkpoint_ns: '',
      checkpoint_id: '1ef663ba-28fe-6528-8002-5a559208592c'
    }
  },
  metadata: {
    source: 'loop',
    writes: { nodeB: { foo: 'b', bar: ['b'] } },
    step: 2
  },
  createdAt: '2024-08-29T19:19:38.821749+00:00',
  parentConfig: {
    configurable: {
      thread_id: '1',
      checkpoint_ns: '',
      checkpoint_id: '1ef663ba-28f9-6ec4-8001-31981c2c39f8'
    }
  },
  tasks: []
}
```

### 获取状态历史

您可以通过调用 `graph.get_state_history(config)` 来获取给定线程的图执行的完整历史。这将返回与配置中提供的线程 ID 关联的 `StateSnapshot` 对象列表。重要的是，检查点将按时间顺序排列，最近的检查点/`StateSnapshot` 是列表中的第一个。

```python
config = {"configurable": {"thread_id": "1"}}
list(graph.get_state_history(config))
```

```typescript
const config = { configurable: { thread_id: "1" } };
for await (const state of graph.getStateHistory(config)) {
  console.log(state);
}
```

在我们的例子中，`get_state_history` 的输出将如下所示：

```
[
    StateSnapshot(
        values={'foo': 'b', 'bar': ['a', 'b']},
        next=(),
        config={'configurable': {'thread_id': '1', 'checkpoint_ns': '', 'checkpoint_id': '1ef663ba-28fe-6528-8002-5a559208592c'}},
        metadata={'source': 'loop', 'writes': {'node_b': {'foo': 'b', 'bar': ['b']}}, 'step': 2},
        created_at='2024-08-29T19:19:38.821749+00:00',
        parent_config={'configurable': {'thread_id': '1', 'checkpoint_ns': '', 'checkpoint_id': '1ef663ba-28f9-6ec4-8001-31981c2c39f8'}},
        tasks=(),
    ),
    StateSnapshot(
        values={'foo': 'a', 'bar': ['a']},
        next=('node_b',),
        config={'configurable': {'thread_id': '1', 'checkpoint_ns': '', 'checkpoint_id': '1ef663ba-28f9-6ec4-8001-31981c2c39f8'}},
        metadata={'source': 'loop', 'writes': {'node_a': {'foo': 'a', 'bar': ['a']}}, 'step': 1},
        created_at='2024-08-29T19:19:38.819946+00:00',
        parent_config={'configurable': {'thread_id': '1', 'checkpoint_ns': '', 'checkpoint_id': '1ef663ba-28f4-6b4a-8000-ca575a13d36a'}},
        tasks=(PregelTask(id='6fb7314f-f114-5413-a1f3-d37dfe98ff44', name='node_b', error=None, interrupts=()),),
    ),
    StateSnapshot(
        values={'foo': '', 'bar': []},
        next=('node_a',),
        config={'configurable': {'thread_id': '1', 'checkpoint_ns': '', 'checkpoint_id': '1ef663ba-28f4-6b4a-8000-ca575a13d36a'}},
        metadata={'source': 'loop', 'writes': None, 'step': 0},
        created_at='2024-08-29T19:19:38.817813+00:00',
        parent_config={'configurable': {'thread_id': '1', 'checkpoint_ns': '', 'checkpoint_id': '1ef663ba-28f0-6c66-bfff-6723431e8481'}},
        tasks=(PregelTask(id='f1b14528-5ee5-579c-949b-23ef9bfbed58', name='node_a', error=None, interrupts=()),),
    ),
    StateSnapshot(
        values={'bar': []},
        next=('__start__',),
        config={'configurable': {'thread_id': '1', 'checkpoint_ns': '', 'checkpoint_id': '1ef663ba-28f0-6c66-bfff-6723431e8481'}},
        metadata={'source': 'input', 'writes': {'foo': ''}, 'step': -1},
        created_at='2024-08-29T19:19:38.816205+00:00',
        parent_config=None,
        tasks=(PregelTask(id='6d27aa2e-d72b-5504-a36f-8620e54a76dd', name='__start__', error=None, interrupts=()),),
    )
]
```

```typescript
[
  StateSnapshot {
    values: { foo: 'b', bar: ['a', 'b'] },
    next: [],
    config: {
      configurable: {
        thread_id: '1',
        checkpoint_ns: '',
        checkpoint_id: '1ef663ba-28fe-6528-8002-5a559208592c'
      }
    },
    metadata: {
      source: 'loop',
      writes: { nodeB: { foo: 'b', bar: ['b'] } },
      step: 2
    },
    createdAt: '2024-08-29T19:19:38.821749+00:00',
    parentConfig: {
      configurable: {
        thread_id: '1',
        checkpoint_ns: '',
        checkpoint_id: '1ef663ba-28f9-6ec4-8001-31981c2c39f8'
      }
    },
    tasks: []
  },
  StateSnapshot {
    values: { foo: 'a', bar: ['a'] },
    next: ['nodeB'],
    config: {
      configurable: {
        thread_id: '1',
        checkpoint_ns: '',
        checkpoint_id: '1ef663ba-28f9-6ec4-8001-31981c2c39f8'
      }
    },
    metadata: {
      source: 'loop',
      writes: { nodeA: { foo: 'a', bar: ['a'] } },
      step: 1
    },
    createdAt: '2024-08-29T19:19:38.819946+00:00',
    parentConfig: {
      configurable: {
        thread_id: '1',
        checkpoint_ns: '',
        checkpoint_id: '1ef663ba-28f4-6b4a-8000-ca575a13d36a'
      }
    },
    tasks: [
      PregelTask {
        id: '6fb7314f-f114-5413-a1f3-d37dfe98ff44',
        name: 'nodeB',
        error: null,
        interrupts: []
      }
    ]
  },
  StateSnapshot {
    values: { foo: '', bar: [] },
    next: ['node_a'],
    config: {
      configurable: {
        thread_id: '1',
        checkpoint_ns: '',
        checkpoint_id: '1ef663ba-28f4-6b4a-8000-ca575a13d36a'
      }
    },
    metadata: {
      source: 'loop',
      writes: null,
      step: 0
    },
    createdAt: '2024-08-29T19:19:38.817813+00:00',
    parentConfig: {
      configurable: {
        thread_id: '1',
        checkpoint_ns: '',
        checkpoint_id: '1ef663ba-28f0-6c66-bfff-6723431e8481'
      }
    },
    tasks: [
      PregelTask {
        id: 'f1b14528-5ee5-579c-949b-23ef9bfbed58',
        name: 'node_a',
        error: null,
        interrupts: []
      }
    ]
  },
  StateSnapshot {
    values: { bar: [] },
    next: ['__start__'],
    config: {
      configurable: {
        thread_id: '1',
        checkpoint_ns: '',
        checkpoint_id: '1ef663ba-28f0-6c66-bfff-6723431e8481'
      }
    },
    metadata: {
      source: 'input',
      writes: { foo: '' },
      step: -1
    },
    createdAt: '2024-08-29T19:19:38.816205+00:00',
    parentConfig: null,
    tasks: [
      PregelTask {
        id: '6d27aa2e-d72b-5504-a36f-8620e54a76dd',
        name: '__start__',
        error: null,
        interrupts: []
      }
    ]
  }
]
```

### 重放

也可以重放先前的图执行。如果我们使用 `thread_id` 和 `checkpoint_id` 调用图，我们将**重放**对应于 `checkpoint_id` 之前的检查点的先前执行步骤，并且只执行检查点之后的步骤。

- `thread_id` 是线程的 ID。
- `checkpoint_id` 是引用线程中特定检查点的标识符。

您必须在调用图时将这些作为配置的 `configurable` 部分传递：

```python
config = {"configurable": {"thread_id": "1", "checkpoint_id": "0c62ca34-ac19-445d-bbb0-5b4984975b2a"}}
graph.invoke(None, config=config)
```

```typescript
const config = {
  configurable: {
    thread_id: "1",
    checkpoint_id: "0c62ca34-ac19-445d-bbb0-5b4984975b2a",
  },
};
await graph.invoke(null, config);
```

重要的是，LangGraph 知道特定步骤是否已经执行过。如果已经执行过，LangGraph 只会**重放**图中的该特定步骤，而不会重新执行该步骤，但这仅适用于提供的 `checkpoint_id` 之前的步骤。`checkpoint_id` 之后的所有步骤都将执行（即新分支），即使它们之前已经执行过。

### 更新状态

除了从特定的 `checkpoint` 重放图外，我们还可以**编辑**图状态。我们使用 `update_state` 来做到这一点。此方法接受三个不同的参数：

#### `config`

配置应包含指定要更新哪个线程的 `thread_id`。当只传递 `thread_id` 时，我们更新（或分支）当前状态。可选地，如果我们包含 `checkpoint_id` 字段，那么我们分支所选的检查点。

#### `values`

这些是将用于更新状态的值。请注意，此更新的处理方式与来自节点的任何更新完全相同。这意味着这些值将传递给图状态中为某些通道定义的 [reducer](https://langchain-doc.cn/v1/python/langgraph/graph-api#reducers) 函数。这意味着 `update_state` 不会自动覆盖每个通道的通道值，而只会覆盖没有 reducer 的通道。让我们通过一个例子来说明。

假设您已经使用以下模式定义了图的状态（请参见上面的完整示例）：

```python
from typing import Annotated
from typing_extensions import TypedDict
from operator import add
class State(TypedDict):
    foo: int
    bar: Annotated[list[str], add]
```

```typescript
import { registry } from "@langchain/langgraph/zod";
import * as z from "zod";
const State = z.object({
  foo: z.number(),
  bar: z.array(z.string()).register(registry, {
    reducer: {
      fn: (x, y) => x.concat(y),
    },
    default: () => [] as string[],
  }),
});
```

现在假设图的当前状态是：

```
{"foo": 1, "bar": ["a"]}
```

```typescript
{ foo: 1, bar: ["a"] }
```

如果您按如下方式更新状态：

```python
graph.update_state(config, {"foo": 2, "bar": ["b"]})
```

```typescript
await graph.updateState(config, { foo: 2, bar: ["b"] });
```

那么图的新状态将是：

```
{"foo": 2, "bar": ["a", "b"]}
```

`foo` 键（通道）完全更改了（因为没有为该通道指定 reducer，所以 `update_state` 会覆盖它）。但是，为 `bar` 键指定了 reducer，因此它将 `"b"` 添加到 `bar` 的状态中。

```typescript
{ foo: 2, bar: ["a", "b"] }
```

`foo` 键（通道）完全更改了（因为没有为该通道指定 reducer，所以 `updateState` 会覆盖它）。但是，为 `bar` 键指定了 reducer，因此它将 `"b"` 添加到 `bar` 的状态中。

#### `as_node`

调用 `update_state` 时可以可选指定的最后一个参数是 `as_node`。如果您提供它，更新将被应用，就好像它来自节点 `as_node`。如果未提供 `as_node`，它将被设置为最后一个更新状态的节点（如果不明确）。这很重要，因为要执行的下一步取决于最后一个提供更新的节点，因此这可以用来控制下一个执行的节点。

## 内存存储

[状态模式](https://langchain-doc.cn/v1/python/langgraph/graph-api#schema) 指定了一组在图执行时填充的键。如上所述，状态可以由检查点保存器在每个图步骤写入线程，从而实现状态持久化。

但是，如果我们想在**线程之间**保留一些信息怎么办？考虑聊天机器人的情况，我们希望在与该用户的**所有**聊天对话（例如线程）中保留有关用户的特定信息！

仅靠检查点，我们无法在线程之间共享信息。这就催生了 [`Store`](https://python.langchain.com/api_reference/langgraph/index.html#module-langgraph.store) 接口的需求。例如，我们可以定义一个 `InMemoryStore` 来存储跨线程的用户信息。我们只需像之前一样使用检查点编译图，并使用我们新的 `in_memory_store` 变量。

**LangGraph API 自动处理存储**
当使用 LangGraph API 时，您不需要手动实现或配置存储。API 在幕后为您处理所有存储基础设施。

### 基本用法

首先，让我们在不使用 LangGraph 的情况下单独展示这一点。

```python
from langgraph.store.memory import InMemoryStore
in_memory_store = InMemoryStore()
```

```typescript
import { MemoryStore } from "@langchain/langgraph";
const memoryStore = new MemoryStore();
```

记忆按 `tuple` 进行命名空间管理，在这个特定例子中是 `(<user_id>, "memories")`。命名空间可以是任意长度，表示任何内容，不一定是用户特定的。

```python
user_id = "1"
namespace_for_memory = (user_id, "memories")
```

```typescript
const userId = "1";
const namespaceForMemory = [userId, "memories"];
```

我们使用 `store.put` 方法将记忆保存到存储中的命名空间。当我们这样做时，我们指定上面定义的命名空间，以及记忆的键值对：键只是记忆的唯一标识符 (`memory_id`)，值（字典）是记忆本身。

```python
memory_id = str(uuid.uuid4())
memory = {"food_preference" : "I like pizza"}
in_memory_store.put(namespace_for_memory, memory_id, memory)
```

```typescript
import { v4 as uuidv4 } from "uuid";
const memoryId = uuidv4();
const memory = { food_preference: "I like pizza" };
await memoryStore.put(namespaceForMemory, memoryId, memory);
```

我们可以使用 `store.search` 方法读取命名空间中的记忆，该方法将返回给定用户的所有记忆作为列表。最近的记忆是列表中的最后一个。

```python
memories = in_memory_store.search(namespace_for_memory)
memories[-1].dict()
{'value': {'food_preference': 'I like pizza'},
 'key': '07e0caf4-1631-47b7-b15f-65515d4c1843',
 'namespace': ['1', 'memories'],
 'created_at': '2024-10-02T17:22:31.590602+00:00',
 'updated_at': '2024-10-02T17:22:31.590605+00:00'}
```

每个记忆类型是一个 Python 类 ([`Item`](https://langchain-ai.github.io/langgraph/reference/store/#langgraph.store.base.Item))，具有某些属性。我们可以通过如上所述的 `.dict` 转换将其作为字典访问。

它具有的属性包括：

- `value`: 此记忆的值（本身是一个字典）
- `key`: 此记忆在此命名空间中的唯一键
- `namespace`: 字符串列表，此记忆类型的命名空间
- `created_at`: 此记忆创建的时间戳
- `updated_at`: 此记忆更新的时间戳

```typescript
const memories = await memoryStore.search(namespaceForMemory);
memories[memories.length - 1];
// {
//   value: { food_preference: 'I like pizza' },
//   key: '07e0caf4-1631-47b7-b15f-65515d4c1843',
//   namespace: ['1', 'memories'],
//   createdAt: '2024-10-02T17:22:31.590602+00:00',
//   updatedAt: '2024-10-02T17:22:31.590605+00:00'
// }
```

它具有的属性包括：

- `value`: 此记忆的值
- `key`: 此记忆在此命名空间中的唯一键
- `namespace`: 字符串列表，此记忆类型的命名空间
- `createdAt`: 此记忆创建的时间戳
- `updatedAt`: 此记忆更新的时间戳

### 语义搜索

除了简单的检索外，存储还支持语义搜索，允许您基于含义而不是精确匹配来查找记忆。要启用此功能，请使用嵌入模型配置存储：

```python
from langchain.embeddings import init_embeddings
store = InMemoryStore(
    index={
        "embed": init_embeddings("openai:text-embedding-3-small"),  # 嵌入提供者
        "dims": 1536,                              # 嵌入维度
        "fields": ["food_preference", "$"]              # 要嵌入的字段
    }
)
```

```typescript
import { OpenAIEmbeddings } from "@langchain/openai";
const store = new InMemoryStore({
  index: {
    embeddings: new OpenAIEmbeddings({ model: "text-embedding-3-small" }),
    dims: 1536,
    fields: ["food_preference", "$"], // 要嵌入的字段
  },
});
```

现在，在搜索时，您可以使用自然语言查询来查找相关记忆：

```python
# 查找有关食物偏好的记忆
# （这可以在将记忆放入存储后完成）
memories = store.search(
    namespace_for_memory,
    query="What does the user like to eat?",
    limit=3  # 返回前 3 个匹配项
)
```

```typescript
// 查找有关食物偏好的记忆
// （这可以在将记忆放入存储后完成）
const memories = await store.search(namespaceForMemory, {
  query: "What does the user like to eat?",
  limit: 3, // 返回前 3 个匹配项
});
```

您可以通过配置 `fields` 参数或在存储记忆时指定 `index` 参数来控制记忆的哪些部分被嵌入：

```python
# 使用特定字段嵌入存储
store.put(
    namespace_for_memory,
    str(uuid.uuid4()),
    {
        "food_preference": "I love Italian cuisine",
        "context": "Discussing dinner plans"
    },
    index=["food_preference"]  # 仅嵌入 "food_preferences" 字段
)
# 不嵌入存储（仍然可检索，但不可搜索）
store.put(
    namespace_for_memory,
    str(uuid.uuid4()),
    {"system_info": "Last updated: 2024-01-01"},
    index=False
)
```

```typescript
// 使用特定字段嵌入存储
await store.put(
  namespaceForMemory,
  uuidv4(),
  {
    food_preference: "I love Italian cuisine",
    context: "Discussing dinner plans",
  },
  { index: ["food_preference"] } // 仅嵌入 "food_preferences" 字段
);
// 不嵌入存储（仍然可检索，但不可搜索）
await store.put(
  namespaceForMemory,
  uuidv4(),
  { system_info: "Last updated: 2024-01-01" },
  { index: false }
);
```

### 在 LangGraph 中使用

有了这一切，我们在 LangGraph 中使用 `in_memory_store`。`in_memory_store` 与检查点协同工作：检查点将状态保存到线程（如上所述），而 `in_memory_store` 允许我们存储任意信息以在**线程之间**访问。我们使用检查点和 `in_memory_store` 编译图如下：

```python
from langgraph.checkpoint.memory import InMemorySaver
# 我们需要这个因为我们想启用线程（对话）
checkpointer = InMemorySaver()
# ... 定义图 ...
# 使用检查点和存储编译图
graph = graph.compile(checkpointer=checkpointer, store=in_memory_store)
```

```typescript
import { MemorySaver } from "@langchain/langgraph";
// 我们需要这个因为我们想启用线程（对话）
const checkpointer = new MemorySaver();
// ... 定义图 ...
// 使用检查点和存储编译图
const graph = workflow.compile({ checkpointer, store: memoryStore });
```

我们像之前一样使用 `thread_id` 调用图，同时也使用 `user_id`，我们将使用它来为此特定用户的记忆设置命名空间，如上面所示。

```python
# 调用图
user_id = "1"
config = {"configurable": {"thread_id": "1", "user_id": user_id}}
# 首先让我们向 AI 问好
for update in graph.stream(
    {"messages": [{"role": "user", "content": "hi"}]}, config, stream_mode="updates"
):
    print(update)
```

```typescript
// 调用图
const userId = "1";
const config = { configurable: { thread_id: "1", user_id: userId } };
// 首先让我们向 AI 问好
for await (const update of await graph.stream(
  { messages: [{ role: "user", content: "hi" }] },
  { ...config, streamMode: "updates" }
)) {
  console.log(update);
}
```

我们可以通过在节点参数中传递 `store: BaseStore` 和 `config: RunnableConfig` 来在**任何节点**中访问 `in_memory_store` 和 `user_id`。以下是我们如何在节点中使用语义搜索来查找相关记忆的示例：

```python
def update_memory(state: MessagesState, config: RunnableConfig, *, store: BaseStore):
    # 从配置中获取用户 ID
    user_id = config["configurable"]["user_id"]
    # 为记忆设置命名空间
    namespace = (user_id, "memories")
    # ... 分析对话并创建新记忆
    # 创建新的记忆 ID
    memory_id = str(uuid.uuid4())
    # 我们创建新的记忆
    store.put(namespace, memory_id, {"memory": memory})
```

```typescript
import { MessagesZodMeta, Runtime } from "@langchain/langgraph";
import { BaseMessage } from "@langchain/core/messages";
import { registry } from "@langchain/langgraph/zod";
import * as z from "zod";
const MessagesZodState = z.object({
  messages:
    z.array(z.custom<BaseMessage>())
    .register(registry, MessagesZodMeta),
});
const updateMemory = async (
  state: z.infer<typeof MessagesZodState>,
  runtime: Runtime<{ user_id: string }>,
) => {
  // 从配置中获取用户 ID
  const userId = runtime.context?.user_id;
  if (!userId) throw new Error("User ID is required");
  // 为记忆设置命名空间
  const namespace = [userId, "memories"];
  // ... 分析对话并创建新记忆
  // 创建新的记忆 ID
  const memoryId = uuidv4();
  // 我们创建新的记忆
  await runtime.store?.put(namespace, memoryId, { memory });
};
```

如前所述，我们也可以在任何节点中访问存储并使用 `store.search` 方法获取记忆。回忆一下，记忆作为可以转换为字典的对象列表返回。

```python
memories[-1].dict()
{'value': {'food_preference': 'I like pizza'},
 'key': '07e0caf4-1631-47b7-b15f-65515d4c1843',
 'namespace': ['1', 'memories'],
 'created_at': '2024-10-02T17:22:31.590602+00:00',
 'updated_at': '2024-10-02T17:22:31.590605+00:00'}
```

```typescript
memories[memories.length - 1];
// {
//   value: { food_preference: 'I like pizza' },
//   key: '07e0caf4-1631-47b7-b15f-65515d4c1843',
//   namespace: ['1', 'memories'],
//   createdAt: '2024-10-02T17:22:31.590602+00:00',
//   updatedAt: '2024-10-02T17:22:31.590605+00:00'
// }
```

我们可以访问记忆并在模型调用中使用它们。

```python
def call_model(state: MessagesState, config: RunnableConfig, *, store: BaseStore):
    # 从配置中获取用户 ID
    user_id = config["configurable"]["user_id"]
    # 为记忆设置命名空间
    namespace = (user_id, "memories")
    # 基于最新消息进行搜索
    memories = store.search(
        namespace,
        query=state["messages"][-1].content,
        limit=3
    )
    info = "\n".join([d.value["memory"] for d in memories])
    # ... 在模型调用中使用记忆
```

```typescript
const callModel = async (
  state: z.infer<typeof MessagesZodState>,
  config: LangGraphRunnableConfig,
  store: BaseStore
) => {
  // 从配置中获取用户 ID
  const userId = config.configurable?.user_id;
  // 为记忆设置命名空间
  const namespace = [userId, "memories"];
  // 基于最新消息进行搜索
  const memories = await store.search(namespace, {
    query: state.messages[state.messages.length - 1].content,
    limit: 3,
  });
  const info = memories.map((d) => d.value.memory).join("\n");
  // ... 在模型调用中使用记忆
};
```

如果我们创建一个新线程，只要 `user_id` 相同，我们仍然可以访问相同的记忆。

```python
# 调用图
config = {"configurable": {"thread_id": "2", "user_id": "1"}}
# 让我们再次问好
for update in graph.stream(
    {"messages": [{"role": "user", "content": "hi, tell me about my memories"}]}, config, stream_mode="updates"
):
    print(update)
```

```typescript
// 调用图
const config = { configurable: { thread_id: "2", user_id: "1" } };
// 让我们再次问好
for await (const update of await graph.stream(
  { messages: [{ role: "user", content: "hi, tell me about my memories" }] },
  { ...config, streamMode: "updates" }
)) {
  console.log(update);
}
```

当我们使用 LangSmith 时，无论是本地（例如在 [Studio](https://langchain-doc.cn/langsmith/studio) 中）还是通过 [LangSmith 托管](https://langchain-doc.cn/langsmith/platform-setup)，基础存储默认可用，不需要在图编译期间指定。但是，要启用语义搜索，您**确实**需要在 `langgraph.json` 文件中配置索引设置。例如：

```json
{
    ...
    "store": {
        "index": {
            "embed": "openai:text-embeddings-3-small",
            "dims": 1536,
            "fields": ["$"]
        }
    }
}
```

有关更多详细信息和配置选项，请参阅 [部署指南](https://langchain-doc.cn/langsmith/semantic-search)。

## 检查点库

在底层，检查点功能由符合 `BaseCheckpointSaver` 接口的检查点对象提供支持。LangGraph 提供了几个检查点实现，全部通过独立的、可安装的库实现：

- `langgraph-checkpoint`：检查点保存器的基本接口 (`BaseCheckpointSaver`) 和序列化/反序列化接口 (`SerializerProtocol`)。包括用于实验的内存检查点实现 (`InMemorySaver`)。LangGraph 包含 `langgraph-checkpoint`。
- `langgraph-checkpoint-sqlite`：使用 SQLite 数据库的 LangGraph 检查点实现 (`SqliteSaver`/`AsyncSqliteSaver`)。适用于实验和本地工作流程。需要单独安装。
- `langgraph-checkpoint-postgres`：使用 Postgres 数据库的高级检查点 (`PostgresSaver`/`AsyncPostgresSaver`)，用于 LangSmith。适用于生产环境。需要单独安装。
- `@langchain/langgraph-checkpoint`：检查点保存器的基本接口 (`BaseCheckpointSaver`) 和序列化/反序列化接口 (`SerializerProtocol`)。包括用于实验的内存检查点实现 (`MemorySaver`)。LangGraph 包含 `@langchain/langgraph-checkpoint`。
- `@langchain/langgraph-checkpoint-sqlite`：使用 SQLite 数据库的 LangGraph 检查点实现 (`SqliteSaver`)。适用于实验和本地工作流程。需要单独安装。
- `@langchain/langgraph-checkpoint-postgres`：使用 Postgres 数据库的高级检查点 (`PostgresSaver`)，用于 LangSmith。适用于生产环境。需要单独安装。

###