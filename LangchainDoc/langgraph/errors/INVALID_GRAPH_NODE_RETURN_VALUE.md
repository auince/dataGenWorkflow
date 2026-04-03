# INVALID_GRAPH_NODE_RETURN_VALUE

LangGraph [`StateGraph`](https://langchain-ai.github.io/langgraph/reference/graphs/#langgraph.graph.state.StateGraph) 从节点收到了非字典返回类型。以下是一个例子：

```python
class State(TypedDict):
    some_key: str
def bad_node(state: State):
    # 应该返回一个带有"some_key"值的字典，而不是列表
    return ["whoops"]
builder = StateGraph(State)
builder.add_node(bad_node)
...
graph = builder.compile()
```

调用上面的图会产生如下错误：

```python
graph.invoke({ "some_key": "someval" });
```

```
InvalidUpdateError: Expected dict, got ['whoops']
For troubleshooting, visit: https://python.langchain.com/docs/troubleshooting/errors/INVALID_GRAPH_NODE_RETURN_VALUE
```

图中的节点必须返回一个包含一个或多个在状态中定义的键的字典。

LangGraph [`StateGraph`](https://langchain-ai.github.io/langgraph/reference/graphs/#langgraph.graph.state.StateGraph) 从节点收到了非对象返回类型。以下是一个例子：

```typescript
import * as z from "zod";
import { StateGraph } from "@langchain/langgraph";
const State = z.object({
  someKey: z.string(),
});
const badNode = (state: z.infer<typeof State>) => {
  // 应该返回一个带有"someKey"值的对象，而不是数组
  return ["whoops"];
};
const builder = new StateGraph(State).addNode("badNode", badNode);
// ...
const graph = builder.compile();
```

调用上面的图会产生如下错误：

```typescript
await graph.invoke({ someKey: "someval" });
```

```
InvalidUpdateError: Expected object, got ['whoops']
For troubleshooting, visit: https://langchain-ai.github.io/langgraphjs/troubleshooting/errors/INVALID_GRAPH_NODE_RETURN_VALUE
```

图中的节点必须返回一个包含一个或多个在状态中定义的键的对象。

## 故障排除

以下方法可能有助于解决此错误：

*   如果您的节点中有复杂逻辑，请确保所有代码路径都返回适合您定义状态的字典。
*   如果您的节点中有复杂逻辑，请确保所有代码路径都返回适合您定义状态的对象。