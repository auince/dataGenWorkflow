# MISSING_CHECKPOINTER

您正在尝试使用LangGraph内置的持久化功能，但未提供检查点工具。

这种情况发生在@`StateGraph`或@`@entrypoint`的`compile()`方法中缺少`checkpointer`时。

## 故障排除

以下方法可能有助于解决此错误：

*   初始化并将检查点工具传递给@`StateGraph`或@`@entrypoint`的`compile()`方法。

```python
from langgraph.checkpoint.memory import InMemorySaver
checkpointer = InMemorySaver()
# Graph API
graph = StateGraph(...).compile(checkpointer=checkpointer)
# Functional API
@entrypoint(checkpointer=checkpointer)
def workflow(messages: list[str]) -> str:
    ...
```

```typescript
import { InMemorySaver, StateGraph } from "@langchain/langgraph";
const checkpointer = new InMemorySaver();
// Graph API
import { StateGraph } from "@langchain/langgraph";
const graph = new StateGraph(...).compile({ checkpointer });
// Functional API
import { entrypoint } from "@langchain/langgraph";
const workflow = entrypoint(
    { checkpointer, name: "workflow" },
    async (messages: string[]) => {
        // ...
    }
);
```

*   使用LangGraph API，这样您就不需要手动实现或配置检查点工具。API会为您处理所有持久化基础设施。

## 相关链接

*   阅读更多关于[持久化](../persistence.html)的信息。