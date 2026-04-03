# 运行本地服务器

本指南向你展示如何在本地运行LangGraph应用程序。

## 先决条件

在开始之前，请确保你具备以下条件：

*   [LangSmith](https://smith.langchain.com/settings)的API密钥 - 免费注册

## 1. 安装LangGraph CLI

### Python

```bash
# 需要Python >= 3.11
pip install -U "langgraph-cli[inmem]"
```

```bash
# 需要Python >= 3.11
uv add langgraph-cli[inmem]
```

### JavaScript

```shell
npx @langchain/langgraph-cli
```

## 2. 创建LangGraph应用 🌱

### Python

从[`new-langgraph-project-python`模板](https://github.com/langchain-ai/new-langgraph-project)创建一个新应用。这个模板演示了你可以用自己的逻辑扩展的单节点应用程序。

```shell
langgraph new path/to/your/app --template new-langgraph-project-python
```

**附加模板**
如果你使用`langgraph new`而不指定模板，你将看到一个交互式菜单，允许你从可用模板列表中进行选择。

### JavaScript

从[`new-langgraph-project-js`模板](https://github.com/langchain-ai/new-langgraphjs-project)创建一个新应用。这个模板演示了你可以用自己的逻辑扩展的单节点应用程序。

```shell
npm create langgraph
```

## 3. 安装依赖

在你的新LangGraph应用的根目录中，以`edit`模式安装依赖，以便服务器使用你的本地更改：

### Python

```bash
cd path/to/your/app
pip install -e .
```

```bash
cd path/to/your/app
uv add .
```

### JavaScript

```shell
cd path/to/your/app
npm install
```

## 4. 创建`.env`文件

你将在新LangGraph应用的根目录中找到一个`.env.example`文件。在新LangGraph应用的根目录中创建一个`.env`文件，并将`.env.example`文件的内容复制到其中，填写必要的API密钥：

```bash
LANGSMITH_API_KEY=lsv2...
```

## 5. 启动LangGraph服务器 🚀

在本地启动LangGraph API服务器：

### Python

```shell
langgraph dev
```

### JavaScript

```shell
npx @langchain/langgraph-cli dev
```

示例输出：

```
>    Ready!
>
>    - API: [http://localhost:2024](http://localhost:2024/)
>
>    - Docs: http://localhost:2024/docs
>
>    - LangGraph Studio Web UI: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024
```

`langgraph dev`命令以内存模式启动LangGraph服务器。此模式适合开发和测试目的。对于生产使用，请部署具有持久存储后端访问权限的LangGraph服务器。有关更多信息，请参阅[托管概述](https://langchain-doc.cn/langsmith/platform-setup)。

## 6. 在Studio中测试你的应用程序

[Studio](https://langchain-doc.cn/langsmith/studio)是一个专门的UI，你可以连接到LangGraph API服务器以可视化、交互和调试你的本地应用程序。通过访问`langgraph dev`命令输出中提供的URL在Studio中测试你的图：

```
>    - LangGraph Studio Web UI: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024
```

对于在自定义主机/端口上运行的LangGraph服务器，请更新baseURL参数。

**Safari兼容性**
使用命令的`--tunnel`标志创建安全隧道，因为Safari在连接到localhost服务器时有限制：

```shell
langgraph dev --tunnel
```

## 7. 测试API

### Python

**Python SDK（异步）**

1.  安装LangGraph Python SDK：

```shell
pip install langgraph-sdk
```

2.  向助手发送消息（无线程运行）：

```python
from langgraph_sdk import get_client
import asyncio
client = get_client(url="http://localhost:2024")
async def main():
    async for chunk in client.runs.stream(
        None,  # 无线程运行
        "agent", # 助手名称。在langgraph.json中定义。
        input={
        "messages": [{
            "role": "human",
            "content": "什么是LangGraph？",
            }],
        },
    ):
        print(f"接收类型为: {chunk.event} 的新事件...")
        print(chunk.data)
        print("\n\n")
asyncio.run(main())
```

**Python SDK（同步）**

1.  安装LangGraph Python SDK：

```shell
pip install langgraph-sdk
```

2.  向助手发送消息（无线程运行）：

```python
from langgraph_sdk import get_sync_client
client = get_sync_client(url="http://localhost:2024")
for chunk in client.runs.stream(
    None,  # 无线程运行
    "agent", # 助手名称。在langgraph.json中定义。
    input={
        "messages": [{
            "role": "human",
            "content": "什么是LangGraph？",
        }],
    },
    stream_mode="messages-tuple",
):
    print(f"接收类型为: {chunk.event} 的新事件...")
    print(chunk.data)
    print("\n\n")
```

**REST API**

```bash
curl -s --request POST \
    --url "http://localhost:2024/runs/stream" \
    --header 'Content-Type: application/json' \
    --data "{
        \"assistant_id\": \"agent\",
        \"input\": {
            \"messages\": [
                {
                    \"role\": \"human\",
                    \"content\": \"什么是LangGraph？\"
                }
            ]
        },
        \"stream_mode\": \"messages-tuple\"
    }"
```

### JavaScript

**JavaScript SDK**

1.  安装LangGraph JS SDK：

```shell
npm install @langchain/langgraph-sdk
```

2.  向助手发送消息（无线程运行）：

```js
const { Client } = await import("@langchain/langgraph-sdk");
// 只有在调用langgraph dev时更改了默认端口时才设置apiUrl
const client = new Client({ apiUrl: "http://localhost:2024"});
const streamResponse = client.runs.stream(
    null, // 无线程运行
    "agent", // 助手ID
    {
        input: {
            "messages": [
                { "role": "user", "content": "什么是LangGraph？"}
            ]
        },
        streamMode: "messages-tuple",
    }
);
for await (const chunk of streamResponse) {
    console.log(`接收类型为: ${chunk.event} 的新事件...`);
    console.log(JSON.stringify(chunk.data));
    console.log("\n\n");
}
```

**REST API**

```bash
curl -s --request POST \
    --url "http://localhost:2024/runs/stream" \
    --header 'Content-Type: application/json' \
    --data "{
        \"assistant_id\": \"agent\",
        \"input\": {
            \"messages\": [
                {
                    \"role\": \"human\",
                    \"content\": \"什么是LangGraph？\"
                }
            ]
        },
        \"stream_mode\": \"messages-tuple\"
    }"
```

## 下一步

现在你已经在本地运行了LangGraph应用程序，通过探索部署和高级功能来进一步推进你的旅程：

*   [部署快速入门](https://langchain-doc.cn/langsmith/deployment-quickstart)：使用LangSmith部署你的LangGraph应用。
*   [LangSmith](https://langchain-doc.cn/langsmith/home)：了解LangSmith的基础概念。

### Python

*   [Python SDK参考](https://reference.langchain.com/python/platform/python_sdk/)：探索Python SDK API参考。

### JavaScript

*   [JS/TS SDK参考](https://reference.langchain.com/javascript/modules/_langchain_langgraph-sdk.html)：探索JS/TS SDK API参考。