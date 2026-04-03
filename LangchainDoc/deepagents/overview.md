# 深度Agent概述

[`deepagents`](https://pypi.org/project/deepagents/) 是一个独立的库，用于构建能够处理复杂、多步骤任务的Agent。深度Agent基于 LangGraph 构建，并受到 Claude Code、Deep Research 和 Manus 等应用的启发，具备规划能力、用于上下文管理的文件系统以及派生子Agent的能力。

## 何时使用深度Agent

当您需要Agent能够执行以下操作时，请使用深度Agent：

*   **处理需要规划和分解的复杂、多步骤任务**
*   **通过文件系统工具管理大量上下文**
*   **将工作委托**给专门的子Agent以实现上下文隔离
*   **在对话和线程之间持久化内存**

对于更简单的用例，请考虑使用 LangChain 的 [`create_agent`](../langchain/agents.html) 或构建自定义的 [LangGraph](../langgraph/overview.html) 工作流。

## 核心功能

### 规划和任务分解

深度Agent包含一个内置的 `write_todos` 工具，使Agent能够将复杂任务分解为离散的步骤，跟踪进度，并在新信息出现时调整计划。

### 上下文管理

文件系统工具（`ls`、`read_file`、`write_file`、`edit_file`）允许Agent将大量上下文卸载到内存中，防止上下文窗口溢出，并能够处理可变长度的工具结果。

### 子Agent派生

内置的 `task` 工具使Agent能够为上下文隔离派生专门的子Agent。这可以保持主Agent的上下文清洁，同时仍能深入处理特定的子任务。

### 长期记忆

使用 LangGraph 的 Store 扩展Agent，使其具有跨线程的持久内存。Agent可以从以前的对话中保存和检索信息。

## 与 LangChain 生态系统的关系

深度Agent建立在以下基础之上：

*   **LangGraph** - 提供底层的图执行和状态管理
*   **LangChain** - 工具和模型集成与深度Agent无缝协作
*   **LangSmith** - 通过 LangGraph 平台实现可观察性和部署

深度Agent应用程序可以通过 [LangSmith 部署](https://langchain-doc.cn/langsmith/deployments) 进行部署，并使用 [LangSmith 可观察性](https://langchain-doc.cn/langsmith/observability) 进行监控。

## 开始

*   [**快速入门**](quickstart.html)
    构建您的第一个深度Agent
*   [**自定义**](customization.html)
    了解自定义选项
*   [**中间件**](https://langchain-doc.cn/v1/python/deepagents/middleware)
    了解中间件架构
*   [**参考**](https://reference.langchain.com/python/deepagents/)
    查看 `deepagents` API 参考