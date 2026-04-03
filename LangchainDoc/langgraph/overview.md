# LangGraph 概述

**LangGraph v1.0现已发布！**

有关完整的变更列表和如何升级代码的说明，请参阅[发布说明](releases/langgraph-v1.html)和[迁移指南](migrate/langgraph-v1.html)。

如果您遇到任何问题或有反馈，请[提交issue](https://github.com/langchain-ai/docs/issues/new?template=02-langgraph.yml&labels=langgraph)以便我们改进。要查看v0.x文档，请[访问存档内容](https://github.com/langchain-ai/langgraph/tree/main/docs/docs)。

## 什么是LangGraph？

LangGraph是一个低级编排框架和运行时，用于构建、管理和部署长时间运行的有状态代理。它受到包括Klarna、Replit、Elastic等塑造代理未来的公司的信任。

LangGraph非常低级，完全专注于代理**编排**。在使用LangGraph之前，我们建议您熟悉一些用于构建代理的组件，从[模型](../langchain/models.html)和[工具](../langchain/tools.html)开始。

在文档中，我们通常会使用[LangChain](../langchain/overview.html)组件来集成模型和工具，但您不需要使用LangChain来使用LangGraph。如果您刚开始接触代理或想要更高级的抽象，我们建议您使用LangChain的[代理](../langchain/agents.html)，它们为常见的LLM和工具调用循环提供了预构建的架构。

LangGraph专注于对代理编排重要的底层功能：持久执行、流式传输、人机协作等。

## 安装

### Python

```bash
pip install -U langgraph
```

或使用uv：

```bash
uv add langgraph
```

### JavaScript

```bash
npm install @langchain/langgraph @langchain/core
```

或使用pnpm：

```bash
pnpm add @langchain/langgraph @langchain/core
```

或使用yarn：

```bash
yarn add @langchain/langgraph @langchain/core
```

或使用bun：

```bash
bun add @langchain/langgraph @langchain/core
```

然后，创建一个简单的Hello World示例：

### Python

```python
from langgraph.graph import StateGraph, MessagesState, START, END
def mock_llm(state: MessagesState):
    return {"messages": [{"role": "ai", "content": "hello world"}]}
graph = StateGraph(MessagesState)
graph.add_node(mock_llm)
graph.add_edge(START, "mock_llm")
graph.add_edge("mock_llm", END)
graph = graph.compile()
graph.invoke({"messages": [{"role": "user", "content": "hi!"}]})
```

### JavaScript

```typescript
import { MessagesAnnotation, StateGraph, START, END } from "@langchain/langgraph";
const mockLlm = (state: typeof MessagesAnnotation.State) => {
  return { messages: [{ role: "ai", content: "hello world" }] };
};
const graph = new StateGraph(MessagesAnnotation)
  .addNode("mock_llm", mockLlm)
  .addEdge(START, "mock_llm")
  .addEdge("mock_llm", END)
  .compile();
await graph.invoke({ messages: [{ role: "user", content: "hi!" }] });
```

## 核心优势

LangGraph为任何长时间运行的有状态工作流或代理提供低级支持基础设施。LangGraph不抽象提示或架构，并提供以下核心优势：

*   [持久执行](durable-execution.html)：构建能够在故障中持久存在并可以长时间运行的代理，从停止的地方继续执行。
*   [人机协作](interrupts.html)：通过在任何点检查和修改代理状态来纳入人工监督。
*   [全面的记忆](https://langchain-doc.cn/v1/python/concepts/memory)：创建具有短期工作记忆（用于持续推理）和跨会话长期记忆的有状态代理。
*   [使用LangSmith进行调试](https://langchain-doc.cn/langsmith/home)：通过可视化工具深入了解复杂的代理行为，这些工具可以跟踪执行路径、捕获状态转换并提供详细的运行时指标。
*   [生产就绪的部署](https://langchain-doc.cn/langsmith/deployments)：使用专为处理有状态、长时间运行的工作流的独特挑战而设计的可扩展基础设施，自信地部署复杂的代理系统。

## LangGraph生态系统

虽然LangGraph可以独立使用，但它也可以与任何LangChain产品无缝集成，为开发人员提供构建代理的全套工具。为了改善您的LLM应用程序开发，请将LangGraph与以下产品配对：

*   [LangSmith](http://www.langchain.com/langsmith) — 有助于代理评估和可观察性。调试性能不佳的LLM应用程序运行，评估代理轨迹，获得生产环境中的可见性，并随着时间的推移提高性能。
*   [LangSmith](https://langchain-doc.cn/langsmith/home) — 使用专为长时间运行的有状态工作流设计的部署平台，轻松部署和扩展代理。在团队中发现、重用、配置和共享代理，并通过[Studio](https://langchain-doc.cn/langsmith/studio)中的可视化原型设计快速迭代。
*   [LangChain](../langchain/overview.html) - 提供集成和可组合组件，简化LLM应用程序开发。包含基于LangGraph构建的代理抽象。

## 鸣谢

LangGraph的灵感来自[Pregel](https://research.google/pubs/pub37252/)和[Apache Beam](https://beam.apache.org/)。公共接口从[NetworkX](https://networkx.org/documentation/latest/)汲取灵感。LangGraph由LangChain Inc构建，LangChain的创建者，但可以在不使用LangChain的情况下使用。