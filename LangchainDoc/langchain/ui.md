# Agent 聊天用户界面

LangChain 提供了一个功能强大的预构建用户界面，可与使用 [`create_agent`](agents.html) 创建的 Agent 无缝协作。无论您是在本地运行还是在部署环境中（例如 [LangSmith](https://langchain-doc.cn/langsmith/)），此 UI 都旨在通过最少的设置，为您的 Agent 提供丰富、交互式的体验。

## Agent Chat UI

[Agent Chat UI](https://github.com/langchain-ai/agent-chat-ui) 是一个 Next.js 应用程序，它提供了一个对话界面，用于与任何 LangChain Agent 进行交互。它支持**实时聊天**、**工具可视化**以及**时间旅行调试**和**状态分叉**等高级功能。

Agent Chat UI 是开源的，可以根据您的应用需求进行调整。

### 功能

#### **工具可视化 (Tool visualization)**

Studio 会在一个直观的界面中自动渲染工具调用和结果。

#### **时间旅行调试 (Time-travel debugging)**

在对话历史中导航，并从任何时间点分叉（fork）出新的对话。

#### **状态检查 (State inspection)**

在执行过程中的任何时间点查看和修改 Agent 状态。

#### **人在回路中 (Human-in-the-loop)**

内置支持审核和响应 Agent 请求。

> 💡 您可以在 Agent Chat UI 中使用**生成式 UI**。有关更多信息，请参阅 [使用 LangGraph 实现生成式用户界面](https://langchain-doc.cn/langsmith/generative-ui-react)。

### 快速开始

最快的入门方法是使用托管版本：

1.  **访问 [Agent Chat UI](https://agentchat.vercel.app)**
2.  通过输入您的**部署 URL 或本地服务器地址**来**连接您的 Agent**
3.  **开始聊天** - UI 将自动检测并渲染工具调用和中断

### 本地开发

为了进行定制或本地开发，您可以在本地运行 Agent Chat UI：

| 使用 npx | 克隆仓库 |
| :--- | :--- |
| ` bash<br># 创建一个新的 Agent Chat UI 项目<br>npx create-agent-chat-app --project-name my-chat-ui<br>cd my-chat-ui<br><br># 安装依赖项并启动<br>pnpm install<br>pnpm dev<br>` | `bash<br># 克隆仓库<br>git clone https://github.com/langchain-ai/agent-chat-ui.git<br>cd agent-chat-ui<br><br># 安装依赖项并启动<br>pnpm install<br>pnpm dev<br>` |

### 连接到您的 Agent

Agent Chat UI 可以连接到[本地 Agent](studio.html#setup-local-langgraph-server) 和[已部署的 Agent](deploy.html)。

启动 Agent Chat UI 后，您需要配置它以连接到您的 Agent：

1.  **Graph ID**：输入您的图名称（在您的 `langgraph.json` 文件中的 `graphs` 下查找）
2.  **部署 URL**：您的 LangGraph 服务器的端点（例如，本地开发的 `http://localhost:2024`，或您已部署 Agent 的 URL）
3.  **LangSmith API 密钥（可选）**：添加您的 LangSmith API 密钥（如果使用本地 LangGraph 服务器则不需要）

配置完成后，Agent Chat UI 将自动获取并显示来自您的 Agent 的任何**中断线程**。

> 💡 Agent Chat UI 开箱即支持渲染工具调用和工具结果消息。要自定义显示哪些消息，请参阅 [Hiding Messages in the Chat](https://github.com/langchain-ai/agent-chat-ui?tab=readme-ov-file#hiding-messages-in-the-chat)。