# GRAPH_RECURSION_LIMIT

您的 LangGraph [StateGraph](https://langchain-ai.github.io/langgraph/reference/graphs/#langgraph.graph.state.StateGraph) 在达到停止条件之前达到了最大步骤数。
这通常是由无限循环引起的，例如下面的代码示例：

```python
class State(TypedDict):
    some_key: str
builder = StateGraph(State)
builder.add_node("a", ...)
builder.add_node("b", ...)
builder.add_edge("a", "b")
builder.add_edge("b", "a")
...
graph = builder.compile()
```

```typescript
import { StateGraph } from "@langchain/langgraph";
import * as z from "zod";
const State = z.object({
  someKey: z.string(),
});
const builder = new StateGraph(State)
  .addNode("a", ...)
  .addNode("b", ...)
  .addEdge("a", "b")
  .addEdge("b", "a")
  ...
const graph = builder.compile();
```

然而，复杂的图形可能自然地达到默认限制。

## 故障排除

*   如果您不期望图形经过多次迭代，则可能存在循环。检查您的逻辑是否存在无限循环。

*   如果您有一个复杂的图形，可以在调用图形时传入更高的 `recursion_limit` 值到您的 `config` 对象中：

```python
graph.invoke({...}, {"recursion_limit": 100})
```

*   如果您有一个复杂的图形，可以在调用图形时传入更高的 `recursionLimit` 值到您的 `config` 对象中：

```typescript
await graph.invoke({...}, { recursionLimit: 100 });