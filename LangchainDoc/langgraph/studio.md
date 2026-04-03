# Studio

本指南将指导你如何使用 **Studio** 在本地可视化、交互和调试你的 Agent。

Studio 是我们免费、强大的 Agent IDE，它集成了 [LangSmith](https://langchain-doc.cn/langsmith/home)，可以进行追踪（tracing）、评估（evaluation）和提示工程（prompt engineering）。你可以准确地看到你的 Agent 是如何思考的，追踪每一个决策，并发布更智能、更可靠的 Agent。

## 前提条件

在你开始之前，请确保你拥有以下条件：

*   一个 [LangSmith](https://smith.langchain.com/settings) 的 API 密钥（可免费注册）

## 设置本地 LangGraph 服务器

### 1. 安装 LangGraph CLI

```shell
# 需要 Python >= 3.11。
pip install --upgrade "langgraph-cli[inmem]"
```

### 2. 准备你的 Agent

我们将使用以下简单的 Agent 作为示例：

**agent.py**

```python
from langchain.agents import create_agent

def send_email(to: str, subject: str, body: str):
    """发送一封邮件"""
    email = {
        "to": to,
        "subject": subject,
        "body": body
    }
    # ... 邮件发送逻辑
    return f"Email sent to {to}"

agent = create_agent(
    "gpt-4o",
    tools=[send_email],
    system_prompt="You are an email assistant. Always use the send_email tool.",
)
```

### 3. 环境变量

在项目的根目录下创建一个 **`.env`** 文件，并填入必要的 API 密钥。我们需要将 `LANGSMITH_API_KEY` 环境变量设置为你从 [LangSmith](https://smith.langchain.com/settings) 获取的 API 密钥。

> **警告**
> 请确保不要将你的 **`.env`** 文件提交到 Git 等版本控制系统！

```bash
LANGSMITH_API_KEY=lsv2...
```

### 4. 创建 LangGraph 配置文件

在你的应用目录下，创建一个名为 `langgraph.json` 的配置文件：

**langgraph.json**

```json
{
  "dependencies": ["."],
  "graphs": {
    "agent": "./src/agent.py:agent"
  },
  "env": ".env"
}
```

[`create_agent`](https://langchain-doc.cn/v1/python/langgraph/%5Bhttps:/reference.langchain.com/python/langchain/agents/#langchain.agents.create_agent%5D(https://reference.langchain.com/python/langchain/agents/#langchain.agents.create_agent)) 会自动返回一个已编译的 LangGraph 图，我们可以将其传递给配置文件的 `graphs` 键。

> **信息**
> 有关配置文件的 JSON 对象中每个键的详细解释，请参阅 [LangGraph 配置文件参考](https://langchain-doc.cn/langsmith/cli#configuration-file)。

到目前为止，我们的项目结构如下所示：

```bash
my-app/
├── src
│   └── agent.py
├── .env
└── langgraph.json
```

### 5. 安装依赖项

在你的新 LangGraph 应用的根目录下，安装依赖项：

```shell
pip install -e .
```

或

```shell
uv sync
```

### 6. 在 Studio 中查看你的 Agent

启动你的 LangGraph 服务器：

```shell
langgraph dev
```

> **警告**
> Safari 浏览器会阻止对 Studio 的 `localhost` 连接。要解决此问题，请运行上述命令并加上 `--tunnel` 选项，以通过安全隧道访问 Studio。

你的 Agent 将可以通过 API (`http://127.0.0.1:2024`) 和 Studio UI (`https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024`) 访问：

Studio 使你的 Agent 的每一步都易于观察。你可以重放任何输入，并检查确切的提示、工具参数、返回值以及 Token/延迟指标。如果工具抛出异常，Studio 会记录它和周围的状态，这样你就可以减少调试时间。

保持你的开发服务器运行，编辑提示或工具签名，并观察 Studio **热重载**。你可以从任何步骤重新运行对话线程，以验证行为更改。有关更多详细信息，请参阅 [管理线程](https://langchain-doc.cn/langsmith/use-studio#edit-thread-history)。

随着你的 Agent 的发展，同样的视图可以从单工具演示扩展到多节点图，保持决策清晰和可复现。

> **提示**
> 要深入了解 Studio，请查看[概览页面](https://langchain-doc.cn/langsmith/studio)。