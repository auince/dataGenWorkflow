# 学习

> 教程、概念指南和资源，助您入门。

在文档的**学习**部分，您将找到一系列教程、概念概述和附加资源，以帮助您使用 LangChain 和 LangGraph 构建强大的应用程序。

## 用例

下面是常见用例的教程，按框架组织。

### LangChain

[LangChain](langchain/overview.html) [智能体](langchain/agents.html)实现使得大多数用例的入门变得容易。

*   **[语义搜索](https://langchain-doc.cn/v1/python/langchain/knowledge-base)**
    *   利用 LangChain 组件在 PDF 上构建语义搜索引擎。
*   **[RAG 智能体](https://langchain-doc.cn/v1/python/langchain/rag)**
    *   创建一个检索增强生成 (RAG) 智能体。
*   **[SQL 智能体](https://langchain-doc.cn/v1/python/langchain/sql-agent)**
    *   构建一个 SQL 智能体，通过人工审核与数据库进行交互。
*   **[主管智能体](https://langchain-doc.cn/v1/python/langchain/supervisor)**
    *   构建一个将任务委托给子智能体的个人助理。

### LangGraph

LangChain 的[智能体](langchain/agents.html)实现使用了 [LangGraph](langgraph/overview.html) 原语。如果需要更深层次的定制，可以直接在 LangGraph 中实现智能体。

*   **[自定义 RAG 智能体](https://langchain-doc.cn/v1/python/langgraph/agentic-rag)**
    *   使用 LangGraph 原语构建 RAG 智能体，以实现细粒度控制。
*   **[自定义 SQL 智能体](https://langchain-doc.cn/v1/python/langgraph/sql-agent)**
    *   直接在 LangGraph 中实现 SQL 智能体，以获得最大的灵活性。

## 概念概述

这些指南解释了 LangChain 和 LangGraph 背后的核心概念和 API。

*   **[内存](https://langchain-doc.cn/v1/python/concepts/memory)**
    *   了解线程内部和跨线程交互的持久性。
*   **[上下文工程](https://langchain-doc.cn/v1/python/concepts/context)**
    *   学习为 AI 应用提供正确信息和工具来完成任务的方法。
*   **[图 API](https://langchain-doc.cn/v1/python/langgraph/graph-api)**
    *   探索 LangGraph 的声明式图构建 API。
*   **[函数式 API](https://langchain-doc.cn/v1/python/langgraph/functional-api)**
    *   将智能体构建为单个函数。

## 附加资源

*   **[LangChain 学院](https://academy.langchain.com/)**
    *   课程和练习，提升您的 LangChain 技能。
*   **[案例研究](https://langchain-doc.cn/v1/python/langgraph/case-studies)**
    *   查看团队如何在生产环境中使用 LangChain 和 LangGraph。