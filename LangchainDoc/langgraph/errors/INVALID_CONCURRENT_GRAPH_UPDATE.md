# INVALID_CONCURRENT_GRAPH_UPDATE

LangGraph [`StateGraph`](https://langchain-ai.github.io/langgraph/reference/graphs/#langgraph.graph.state.StateGraph) 收到了来自多个节点对其状态的并发更新，但该状态属性不支持这种操作。

这种情况可能发生在您在图中使用[扇出](https://langchain-doc.cn/v1/python/langgraph/graph-api#map-reduce-and-the-send-api)或其他并行执行，并且定义了如下所示的图时：

```python
class State(TypedDict):
    some_key: str  # [!code highlight]
def node(state: State):
    return {"some_key": "some_string_value"}
def other_node(state: State):
    return {"some_key": "some_string_value"}
builder = StateGraph(State)
builder.add_node(node)
builder.add_node(other_node)
builder.add_edge(START, "node")
builder.add_edge(START, "other_node")
graph = builder.compile()
```

```typescript
import { StateGraph, Annotation, START } from "@langchain/langgraph";
import * as z from "zod";  // [!code highlight]
const State = z.object({
  someKey: z.string(),
});
const builder = new StateGraph(State)
  .addNode("node", (state) => {
    return { someKey: "some_string_value" };
  })
  .addNode("otherNode", (state) => {
    return { someKey: "some_string_value" };
  })
  .addEdge(START, "node")
  .addEdge(START, "otherNode");
const graph = builder.compile();
```

如果上述图中的节点返回`{ "some_key": "some_string_value" }`，这将用`"some_string_value"`覆盖`"some_key"`的状态值。
但是，如果在单个步骤中的扇出等情况下，多个节点返回`"some_key"`的值，图将抛出此错误，因为
存在关于如何更新内部状态的不确定性。

如果上述图中的节点返回`{ someKey: "some_string_value" }`，这将用`"some_string_value"`覆盖`someKey`的状态值。
但是，如果在单个步骤中的扇出等情况下，多个节点返回`someKey`的值，图将抛出此错误，因为
存在关于如何更新内部状态的不确定性。

要解决这个问题，您可以定义一个reducer来组合多个值：

```python
import operator
from typing import Annotated
class State(TypedDict):
    # operator.add reducer 函数使其成为仅追加的  # [!code highlight]
    some_key: Annotated[list, operator.add]  # [!code highlight]
```

```typescript
import { registry } from "@langchain/langgraph/zod";
import * as z from "zod";
const State = z.object({  // [!code highlight]
  someKey: z.array(z.string()).register(registry, {  // [!code highlight]
    reducer: {  // [!code highlight]
      fn: (existing, update) => existing.concat(update),  // [!code highlight]
    },
    default: () => [] as string[],
  }),
});
```

这将允许您定义处理从并行执行的多个节点返回的相同键的逻辑。

## 故障排除

以下方法可能有助于解决此错误：

*   如果您的图并行执行节点，请确保已为相关状态键定义了reducer。