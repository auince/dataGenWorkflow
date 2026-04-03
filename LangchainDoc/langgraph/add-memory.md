# 内存

AI应用需要[内存](https://langchain-doc.cn/v1/python/concepts/memory)来在多次交互之间共享上下文。在LangGraph中，您可以添加两种类型的内存：

* [添加短期内存](#添加短期内存)作为代理[状态](https://langchain-doc.cn/v1/python/langgraph/graph-api#state)的一部分，以启用多轮对话。
* [添加长期内存](#添加长期内存)以跨会话存储特定用户或应用级别的数据。

## 添加短期内存

**短期**内存（线程级[持久化](persistence.html)）使代理能够跟踪多轮对话。要添加短期内存：

```python
from langgraph.checkpoint.memory import InMemorySaver  # [!code highlight]
from langgraph.graph import StateGraph
checkpointer = InMemorySaver()  # [!code highlight]
builder = StateGraph(...)
graph = builder.compile(checkpointer=checkpointer)  # [!code highlight]
graph.invoke(
    {"messages": [{"role": "user", "content": "hi! i am Bob"}]},
    {"configurable": {"thread_id": "1"}},  # [!code highlight]
)
```

```js
import { MemorySaver, StateGraph } from "@langchain/langgraph";
const checkpointer = new MemorySaver();
const builder = new StateGraph(...);
const graph = builder.compile({ checkpointer });
await graph.invoke(
  { messages: [{ role: "user", content: "hi! i am Bob" }] },
  { configurable: { thread_id: "1" } }
);
```

### 在生产环境中使用

在生产环境中，使用由数据库支持的检查点：

```python
from langgraph.checkpoint.postgres import PostgresSaver
DB_URI = "postgresql://postgres:postgres@localhost:5442/postgres?sslmode=disable"
with PostgresSaver.from_conn_string(DB_URI) as checkpointer:  # [!code highlight]
    builder = StateGraph(...)
    graph = builder.compile(checkpointer=checkpointer)  # [!code highlight]
```

```js
import { PostgresSaver } from "@langchain/langgraph-checkpoint-postgres";
const DB_URI = "postgresql://postgres:postgres@localhost:5442/postgres?sslmode=disable";
const checkpointer = PostgresSaver.fromConnString(DB_URI);
const builder = new StateGraph(...);
const graph = builder.compile({ checkpointer });
```

### 示例：使用Postgres检查点

**Python安装**:

```bash
pip install -U "psycopg[binary,pool]" langgraph langgraph-checkpoint-postgres
```

**注意**：首次使用Postgres检查点时，需要调用`checkpointer.setup()`

**同步模式**:

```python
from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, MessagesState, START
from langgraph.checkpoint.postgres import PostgresSaver
model = init_chat_model(model="claude-haiku-4-5-20251001")
DB_URI = "postgresql://postgres:postgres@localhost:5442/postgres?sslmode=disable"
with PostgresSaver.from_conn_string(DB_URI) as checkpointer:
    # checkpointer.setup()
    def call_model(state: MessagesState):
        response = model.invoke(state["messages"])
        return {"messages": response}
    builder = StateGraph(MessagesState)
    builder.add_node(call_model)
    builder.add_edge(START, "call_model")
    graph = builder.compile(checkpointer=checkpointer)
    config = {
        "configurable": {
            "thread_id": "1"
        }
    }
    for chunk in graph.stream(
        {"messages": [{"role": "user", "content": "hi! I'm bob"}]},
        config,
        stream_mode="values"
    ):
        chunk["messages"][-1].pretty_print()
    for chunk in graph.stream(
        {"messages": [{"role": "user", "content": "what's my name?"}]},
        config,
        stream_mode="values"
    ):
        chunk["messages"][-1].pretty_print()
```

**异步模式**:

```python
from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, MessagesState, START
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
model = init_chat_model(model="claude-haiku-4-5-20251001")
DB_URI = "postgresql://postgres:postgres@localhost:5442/postgres?sslmode=disable"
async with AsyncPostgresSaver.from_conn_string(DB_URI) as checkpointer:
    # await checkpointer.setup()
    async def call_model(state: MessagesState):
        response = await model.ainvoke(state["messages"])
        return {"messages": response}
    builder = StateGraph(MessagesState)
    builder.add_node(call_model)
    builder.add_edge(START, "call_model")
    graph = builder.compile(checkpointer=checkpointer)
    config = {
        "configurable": {
            "thread_id": "1"
        }
    }
    async for chunk in graph.astream(
        {"messages": [{"role": "user", "content": "hi! I'm bob"}]},
        config,
        stream_mode="values"
    ):
        chunk["messages"][-1].pretty_print()
    async for chunk in graph.astream(
        {"messages": [{"role": "user", "content": "what's my name?"}]},
        config,
        stream_mode="values"
    ):
        chunk["messages"][-1].pretty_print()
```

**JavaScript安装**:

```bash
npm install @langchain/langgraph-checkpoint-postgres
```

**JavaScript示例**:

```typescript
import { ChatAnthropic } from "@langchain/anthropic";
import { StateGraph, MessagesZodMeta, START } from "@langchain/langgraph";
import { BaseMessage } from "@langchain/core/messages";
import { registry } from "@langchain/langgraph/zod";
import * as z from "zod";
import { PostgresSaver } from "@langchain/langgraph-checkpoint-postgres";
const MessagesZodState = z.object({
  messages: z
    .array(z.custom<BaseMessage>())
    .register(registry, MessagesZodMeta),
});
const model = new ChatAnthropic({ model: "claude-haiku-4-5-20251001" });
const DB_URI = "postgresql://postgres:postgres@localhost:5442/postgres?sslmode=disable";
const checkpointer = PostgresSaver.fromConnString(DB_URI);
// await checkpointer.setup();
const builder = new StateGraph(MessagesZodState)
  .addNode("call_model", async (state) => {
    const response = await model.invoke(state.messages);
    return { messages: [response] };
  })
  .addEdge(START, "call_model");
const graph = builder.compile({ checkpointer });
const config = {
  configurable: {
    thread_id: "1"
  }
};
for await (const chunk of await graph.stream(
  { messages: [{ role: "user", content: "hi! I'm bob" }] },
  { ...config, streamMode: "values" }
)) {
  console.log(chunk.messages.at(-1)?.content);
}
for await (const chunk of await graph.stream(
  { messages: [{ role: "user", content: "what's my name?" }] },
  { ...config, streamMode: "values" }
)) {
  console.log(chunk.messages.at(-1)?.content);
}
```

### 在子图中使用

如果您的图包含[子图](use-subgraphs.html)，您只需在编译父图时提供检查点。LangGraph会自动将检查点传播到子图。

```python
from langgraph.graph import START, StateGraph
from langgraph.checkpoint.memory import InMemorySaver
from typing import TypedDict
class State(TypedDict):
    foo: str
# 子图
def subgraph_node_1(state: State):
    return {"foo": state["foo"] + "bar"}
subgraph_builder = StateGraph(State)
subgraph_builder.add_node(subgraph_node_1)
subgraph_builder.add_edge(START, "subgraph_node_1")
subgraph = subgraph_builder.compile()
# 父图
builder = StateGraph(State)
builder.add_node("node_1", subgraph)
builder.add_edge(START, "node_1")
checkpointer = InMemorySaver()
graph = builder.compile(checkpointer=checkpointer)
```

```js
import { StateGraph, START, MemorySaver } from "@langchain/langgraph";
import * as z from "zod";
const State = z.object({ foo: z.string() });
const subgraphBuilder = new StateGraph(State)
  .addNode("subgraph_node_1", (state) => {
    return { foo: state.foo + "bar" };
  })
  .addEdge(START, "subgraph_node_1");
const subgraph = subgraphBuilder.compile();
const builder = new StateGraph(State)
  .addNode("node_1", subgraph)
  .addEdge(START, "node_1");
const checkpointer = new MemorySaver();
const graph = builder.compile({ checkpointer });
```

如果您希望子图拥有自己的内存，您可以使用适当的检查点选项编译它。这在[多代理](https://langchain-doc.cn/v1/python/langchain/multi-agent.html)系统中很有用，如果您希望代理跟踪它们的内部消息历史。

```python
subgraph_builder = StateGraph(...)
subgraph = subgraph_builder.compile(checkpointer=True)
```

```js
const subgraphBuilder = new StateGraph(...);
const subgraph = subgraphBuilder.compile({ checkpointer: true });
```

## 添加长期内存

使用长期内存跨对话存储用户特定或应用特定的数据。

```python
from langgraph.store.memory import InMemoryStore  # [!code highlight]
from langgraph.graph import StateGraph
store = InMemoryStore()  # [!code highlight]
builder = StateGraph(...)
graph = builder.compile(store=store)  # [!code highlight]
```

```js
import { InMemoryStore, StateGraph } from "@langchain/langgraph";
const store = new InMemoryStore();
const builder = new StateGraph(...);
const graph = builder.compile({ store });
```

### 在生产环境中使用

在生产环境中，使用由数据库支持的存储：

```python
from langgraph.store.postgres import PostgresStore
DB_URI = "postgresql://postgres:postgres@localhost:5442/postgres?sslmode=disable"
with PostgresStore.from_conn_string(DB_URI) as store:  # [!code highlight]
    builder = StateGraph(...)
    graph = builder.compile(store=store)  # [!code highlight]
```

```js
import { PostgresStore } from "@langchain/langgraph-checkpoint-postgres/store";
const DB_URI = "postgresql://postgres:postgres@localhost:5442/postgres?sslmode=disable";
const store = PostgresStore.fromConnString(DB_URI);
const builder = new StateGraph(...);
const graph = builder.compile({ store });
```

### 使用语义搜索

在图的内存存储中启用语义搜索，让图代理通过语义相似性在存储中搜索项目。

```python
from langchain.embeddings import init_embeddings
from langgraph.store.memory import InMemoryStore
# 创建启用语义搜索的存储
embeddings = init_embeddings("openai:text-embedding-3-small")
store = InMemoryStore(
    index={
        "embed": embeddings,
        "dims": 1536,
    }
)
store.put(("user_123", "memories"), "1", {"text": "I love pizza"})
store.put(("user_123", "memories"), "2", {"text": "I am a plumber"})
items = store.search(
    ("user_123", "memories"), query="I'm hungry", limit=1
)
```

```js
import { OpenAIEmbeddings } from "@langchain/openai";
import { InMemoryStore } from "@langchain/langgraph";
// 创建启用语义搜索的存储
const embeddings = new OpenAIEmbeddings({ model: "text-embedding-3-small" });
const store = new InMemoryStore({
  index: {
    embeddings,
    dims: 1536,
  },
});
await store.put(["user_123", "memories"], "1", { text: "I love pizza" });
await store.put(["user_123", "memories"], "2", { text: "I am a plumber" });
const items = await store.search(["user_123", "memories"], {
  query: "I'm hungry",
  limit: 1,
});
```

## 管理短期内存

启用[短期内存](#添加短期内存)后，长对话可能会超出LLM的上下文窗口。常见解决方案包括：

* [修剪消息](#修剪消息)：在调用LLM前删除前N条或后N条消息
* [删除消息](#删除消息)：从LangGraph状态中永久删除消息
* [总结消息](#总结消息)：总结历史记录中的早期消息并用摘要替换它们
* [管理检查点](#管理检查点)：存储和检索消息历史
* 自定义策略（如消息过滤等）

这允许代理跟踪对话，而不会超出LLM的上下文窗口。

### 修剪消息

大多数LLM都有最大支持的上下文窗口（以token计算）。决定何时截断消息的一种方法是计算消息历史中的token数量，并在接近该限制时截断。如果您使用LangChain，可以使用修剪消息工具并指定要从列表中保留的token数量，以及用于处理边界的`strategy`（例如，保留最后`max_tokens`）。

**Python**：使用[`trim_messages`](https://python.langchain.com/api_reference/core/messages/langchain_core.messages.utils.trim_messages.html)函数：

```python
from langchain_core.messages.utils import (
    trim_messages,
    count_tokens_approximately
)
def call_model(state: MessagesState):
    messages = trim_messages(
        state["messages"],
        strategy="last",
        token_counter=count_tokens_approximately,
        max_tokens=128,
        start_on="human",
        end_on=("human", "tool"),
    )
    response = model.invoke(messages)
    return {"messages": [response]}
builder = StateGraph(MessagesState)
builder.add_node(call_model)
...
```

**JavaScript**：使用[`trimMessages`](https://js.langchain.com/docs/how_to/trim_messages/)函数：

```typescript
import { trimMessages } from "@langchain/core/messages";
const callModel = async (state: z.infer<typeof MessagesZodState>) => {
  const messages = trimMessages(state.messages, {
    strategy: "last",
    maxTokens: 128,
    startOn: "human",
    endOn: ["human", "tool"],
  });
  const response = await model.invoke(messages);
  return { messages: [response] };
};
const builder = new StateGraph(MessagesZodState)
  .addNode("call_model", callModel);
// ...
```

### 删除消息

您可以从图状态中删除消息来管理消息历史。当您想删除特定消息或清除整个消息历史时，这很有用。

**Python**：使用`RemoveMessage`删除消息。为了使`RemoveMessage`正常工作，您需要使用带有@[`add_messages`] [reducer](https://langchain-doc.cn/v1/python/langgraph/graph-api#reducers)的状态键，如[`MessagesState`](https://langchain-doc.cn/v1/python/langgraph/graph-api#messagesstate)。

删除特定消息：

```python
from langchain.messages import RemoveMessage
def delete_messages(state):
    messages = state["messages"]
    if len(messages) > 2:
        # 删除最早的两条消息
        return {"messages": [RemoveMessage(id=m.id) for m in messages[:2]]}
```

删除**所有**消息：

```python
from langgraph.graph.message import REMOVE_ALL_MESSAGES
def delete_messages(state):
    return {"messages": [RemoveMessage(id=REMOVE_ALL_MESSAGES)]}
```

**JavaScript**：使用`RemoveMessage`删除消息。

```typescript
import { RemoveMessage } from "@langchain/core/messages";
const deleteMessages = (state) => {
  const messages = state.messages;
  if (messages.length > 2) {
    // 删除最早的两条消息
    return {
      messages: messages
        .slice(0, 2)
        .map((m) => new RemoveMessage({ id: m.id })),
    };
  }
};
```

**警告**：删除消息时，请**确保**生成的消息历史有效。检查您使用的LLM提供商的限制。例如：

* 一些提供商期望消息历史以`user`消息开始
* 大多数提供商要求带有工具调用的`assistant`消息后面跟着相应的`tool`结果消息

### 总结消息

上面显示的修剪或删除消息的问题是，您可能会因为消息队列的剔除而丢失信息。因此，一些应用程序受益于使用聊天模型总结消息历史的更复杂方法。

**Python**：扩展[`MessagesState`](https://langchain-doc.cn/v1/python/langgraph/graph-api#working-with-messages-in-graph-state)以包含`summary`键：

```python
from langgraph.graph import MessagesState
class State(MessagesState):
    summary: str
```

然后，您可以生成聊天历史的摘要，使用任何现有摘要作为下一个摘要的上下文。这个`summarize_conversation`节点可以在`messages`状态键中累积了一定数量的消息后调用。

```python
def summarize_conversation(state: State):
    # 首先，我们获取任何现有摘要
    summary = state.get("summary", "")
    # 创建我们的摘要提示
    if summary:
        # 已经存在摘要
        summary_message = (
            f"This is a summary of the conversation to date: {summary}\n\n"
            "Extend the summary by taking into account the new messages above:"
        )
    else:
        summary_message = "Create a summary of the conversation above:"
    # 将提示添加到我们的历史记录中
    messages = state["messages"] + [HumanMessage(content=summary_message)]
    response = model.invoke(messages)
    # 删除除了最近2条消息之外的所有消息
    delete_messages = [RemoveMessage(id=m.id) for m in state["messages"][:-2]]
    return {"summary": response.content, "messages": delete_messages}
```

**JavaScript**：在状态中包含`summary`键：

```typescript
import { BaseMessage } from "@langchain/core/messages";
import { MessagesZodMeta } from "@langchain/langgraph";
import { registry } from "@langchain/langgraph/zod";
import * as z from "zod";
const State = z.object({
  messages:
    z.array(z.custom<BaseMessage>())
      .register(registry, MessagesZodMeta),
  summary: z.string().optional(),
});
```

### 管理检查点

您可以查看和删除检查点存储的信息。

#### 查看线程状态

**Python**：

```python
config = {
    "configurable": {
        "thread_id": "1",  # 指定线程ID
        # 可选地提供特定检查点的ID，
        # 否则显示最新检查点
        # "checkpoint_id": "1f029ca3-1f5b-6704-8004-820c16b69a5a"
    }
}
graph.get_state(config)
```

**JavaScript**：

```typescript
const config = {
  configurable: {
    thread_id: "1",
    // 可选地提供特定检查点的ID，
    // 否则显示最新检查点
    // checkpoint_id: "1f029ca3-1f5b-6704-8004-820c16b69a5a"
  },
};
await graph.getState(config);
```

#### 查看线程历史

**Python**：

```python
config = {
    "configurable": {
        "thread_id": "1"
    }
}
list(graph.get_state_history(config))
```

**JavaScript**：

```typescript
const config = {
  configurable: {
    thread_id: "1",
  },
};
const history = [];
for await (const state of graph.getStateHistory(config)) {
  history.push(state);
}
```

#### 删除线程的所有检查点

**Python**：

```python
thread_id = "1"
checkpointer.delete_thread(thread_id)
```

**JavaScript**：

```typescript
const threadId = "1";
await checkpointer.deleteThread(threadId);
```

## 预构建内存工具

**LangMem**是一个由LangChain维护的库，提供了用于管理代理中长期记忆的工具。有关使用示例，请参阅[LangMem文档](https://langchain-ai.github.io/langmem/)。