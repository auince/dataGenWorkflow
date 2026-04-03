# Agent聊天用户界面

LangChain 提供了一个功能强大的预构建用户界面，可与使用 [`create_agent`](../langchain/agents.html) 创建的智能体无缝协作。无论您是在本地运行还是在已部署的环境中（例如 [LangSmith](https://langchain-doc.cn/langsmith/)），该 UI 都旨在通过最少的设置，为您的智能体提供**丰富、交互式的体验**。

## 智能体聊天用户界面（Agent Chat UI）

[Agent Chat UI](https://github.com/langchain-ai/agent-chat-ui) 是一个 Next.js 应用程序，它提供了一个**会话式界面**，用于与任何 LangChain 智能体进行交互。它支持**实时聊天**、**工具可视化**以及**时间旅行调试**和**状态分叉**等高级功能。

Agent Chat UI 是开源的，可以根据您的应用需求进行调整。

### 特性

#### 工具可视化

Studio 会在一个直观的界面中自动渲染工具调用和结果。

> [工具可视化 GIF 示例]
> ![studio_tools.gif](../../../assets/31aad82fad82050ade6a315cc1266bf4.gif)

#### 时间旅行调试

浏览会话历史，并可以从任何时间点**分叉**（fork）新的会话。

> [时间旅行调试 GIF 示例]
> ![studio_fork.gif](../../../assets/ab465961e0d192401dd2d12e2d53e228.gif)

#### 状态检查

在执行过程中的任何时间点**查看和修改**智能体的状态。

> [状态检查 GIF 示例]
> ![studio_state.gif](../../../assets/870da744df02b6089a022a7bfc16b0f8.gif)

#### 人在回路（Human-in-the-loop）

内置支持**审查和响应**智能体的请求。

> [人在回路 GIF 示例]
> ![studio_hitl.gif](../../../assets/bafef44d978985ddb09fbac99b23d08a.gif)

> **提示**
> 您可以在 Agent Chat UI 中使用**生成式 UI**。有关更多信息，请参阅 [使用 LangGraph 实现生成式用户界面](https://langchain-doc.cn/langsmith/generative-ui-react)。

### 快速入门

最快入门的方法是使用托管版本：

1. **访问 [Agent Chat UI](https://agentchat.vercel.app)**
2. 通过输入您的**部署 URL 或本地服务器地址**来**连接您的智能体**。
3. **开始聊天**——UI 将自动检测并渲染工具调用和中断。

### 本地开发

对于定制或本地开发，您可以在本地运行 Agent Chat UI：

#### 使用npx

```shell
# Create a new Agent Chat UI project
npx create-agent-chat-app --project-name my-chat-ui
cd my-chat-ui
# Install dependencies and start
pnpm install
pnpm dev
```

#### 克隆仓库

```shell
# Clone the repository
git clone https://github.com/langchain-ai/agent-chat-ui.git
cd agent-chat-ui
# Install dependencies and start
pnpm install
pnpm dev
```

### 连接到您的智能体

Agent Chat UI 可以连接到**本地** [/v1/python/langgraph/studio#setup-local-langgraph-server] 和**已部署的智能体** [/v1/python/langgraph/deploy]。

启动 Agent Chat UI 后，您需要配置它以连接到您的智能体：

1. **Graph ID（图 ID）**：输入您的图名称（可在您的 `langgraph.json` 文件中的 `graphs` 下找到）。
2. **Deployment URL（部署 URL）**：您的 LangGraph 服务器的端点（例如，本地开发为 `http://localhost:2024`，或您的已部署智能体的 URL）。
3. **LangSmith API key (可选)**：添加您的 LangSmith API 密钥（如果您使用的是本地 LangGraph 服务器，则**不需要**）。

配置完成后，Agent Chat UI 将自动从您的智能体**获取并显示任何中断的线程**。

> **提示**
> Agent Chat UI **开箱即用**地支持渲染工具调用和工具结果消息。要自定义显示哪些消息，请参阅 [在聊天中隐藏消息](https://github.com/langchain-ai/agent-chat-ui?tab=readme-ov-file#hiding-messages-in-the-chat)。