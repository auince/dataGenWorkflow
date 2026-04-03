# 可观察性

追踪（Traces）是你的应用程序从输入到输出所采取的一系列步骤。这些单个步骤中的每一个都由一个运行（run）表示。你可以使用[LangSmith](https://smith.langchain.com/)来可视化这些执行步骤。要使用它，请[为你的应用程序启用追踪](https://langchain-doc.cn/langsmith/trace-with-langgraph)。这使你能够执行以下操作：

*   [调试本地运行的应用程序](https://langchain-doc.cn/langsmith/observability-studio#debug-langsmith-traces)。
*   [评估应用程序性能](https://langchain-doc.cn/v1/python/langchain/evals)。
*   [监控应用程序](https://langchain-doc.cn/langsmith/dashboards)。

## 先决条件

在开始之前，请确保你具备以下条件：

*   一个[LangSmith账户](https://smith.langchain.com/)（免费注册）

## 启用追踪

要为你的应用程序启用追踪，请设置以下环境变量：

```bash
export LANGSMITH_TRACING=true
export LANGSMITH_API_KEY=<your-api-key>
```

默认情况下，追踪将记录到名为`default`的项目中。要配置自定义项目名称，请参阅[记录到项目](#log-to-a-project)。

有关更多信息，请参阅[使用LangGraph进行追踪](https://langchain-doc.cn/langsmith/trace-with-langgraph)。

> 注意：文档中引用的部分内容因系统限制无法显示，请参考LangSmith官方文档获取完整的可观察性指南。

## 使用匿名器防止敏感数据在追踪中记录

你可能希望屏蔽敏感数据，以防止其被记录到LangSmith中。你可以创建[匿名器](https://langchain-doc.cn/langsmith/mask-inputs-outputs#rule-based-masking-of-inputs-and-outputs)并通过配置将其应用到你的图中。以下示例将从发送到LangSmith的追踪中编辑任何匹配社会安全号码格式XXX-XX-XXXX的内容。

```python
from langchain_core.tracers.langchain import LangChainTracer
from langgraph.graph import StateGraph, MessagesState
from langsmith import Client
from langsmith.anonymizer import create_anonymizer
anonymizer = create_anonymizer([
    # 匹配SSN
    { "pattern": r"\b\d{3}-?\d{2}-?\d{4}\b", "replace": "<ssn>" }
])
tracer_client = Client(anonymizer=anonymizer)
tracer = LangChainTracer(client=tracer_client)
# 定义图
graph = (
    StateGraph(MessagesState)
    ...
    .compile()
    .with_config({'callbacks': [tracer]})
)
```

```typescript
import { StateGraph } from "@langchain/langgraph";
import { LangChainTracer } from "@langchain/core/tracers/tracer_langchain";
import { StateAnnotation } from "./state.js";
import { createAnonymizer } from "langsmith/anonymizer"
import { Client } from "langsmith"
const anonymizer = createAnonymizer([
    // 匹配SSN
    { pattern: /\b\d{3}-?\d{2}-?\d{4}\b/, replace: "<ssn>" }
])
const langsmithClient = new Client({ anonymizer })
const tracer = new LangChainTracer({
  client: langsmithClient,
});
export const graph = new StateGraph(StateAnnotation)
  .compile()
  .withConfig({
    callbacks: [tracer],
});