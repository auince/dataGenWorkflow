# 模型上下文协议 (MCP)

[**模型上下文协议 (MCP)**](https://modelcontextprotocol.io/introduction) 是一种开放协议，它**标准化了应用程序如何向 LLM 提供工具和上下文**。LangChain 代理可以使用 [`langchain-mcp-adapters`](https://langchain-doc.cn/v1/python/langchain/[https://github.com/langchain-ai/langchain-mcp-adapters](https://github.com/langchain-ai/langchain-mcp-adapters)) 库来使用在 MCP 服务器上定义的工具。

## 安装

安装 `langchain-mcp-adapters` 库，以便在 LangGraph 中使用 MCP 工具：

```bash
# 使用 pip
pip install langchain-mcp-adapters
```

```bash
# 使用 uv
uv add langchain-mcp-adapters
```

## 传输类型

MCP 支持用于客户端-服务器通信的不同传输机制：

- **stdio**：客户端将服务器作为子进程启动，并通过标准输入/输出进行通信。最适合本地工具和简单的设置。
- **Streamable HTTP**：服务器作为独立进程运行，处理 HTTP 请求。支持远程连接和多个客户端。
- **Server-Sent Events (SSE)**：Streamable HTTP 的一个变体，针对实时流式通信进行了优化。

## 使用 MCP 工具

`langchain-mcp-adapters` 使代理能够使用在一个或多个 MCP 服务器上定义的工具。

```python
# 访问多个 MCP 服务器
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent
client = MultiServerMCPClient(
    {
        "math": {
            "transport": "stdio",  # 本地子进程通信
            "command": "python",
            # 您的 math_server.py 文件的绝对路径
            "args": ["/path/to/math_server.py"],
        },
        "weather": {
            "transport": "streamable_http",  # 基于 HTTP 的远程服务器
            # 确保您在 8000 端口启动了您的天气服务器
            "url": "http://localhost:8000/mcp",
        }
    }
)
tools = await client.get_tools()
agent = create_agent(
    "anthropic:claude-sonnet-4-5",
    tools
)
math_response = await agent.ainvoke(
    {"messages": [{"role": "user", "content": "what's (3 + 5) x 12?"}]}
)
weather_response = await agent.ainvoke(
    {"messages": [{"role": "user", "content": "what is the weather in nyc?"}]}
)
```

> `MultiServerMCPClient` **默认是无状态的**。每次工具调用都会创建一个新的 MCP `ClientSession`，执行工具，然后进行清理。

## 自定义 MCP 服务器

要创建您自己的 MCP 服务器，您可以使用 `mcp` 库。该库提供了一种简单的方式来定义[工具](https://modelcontextprotocol.io/docs/learn/server-concepts#tools-ai-actions)并将其作为服务器运行。

```bash
# 使用 pip
pip install mcp
```

```bash
# 使用 uv
uv add mcp
```

使用以下参考实现来测试您的代理与 MCP 工具服务器的交互。

```python
# Math server (stdio transport)
from mcp.server.fastmcp import FastMCP
mcp = FastMCP("Math")
@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b
@mcp.tool()
def multiply(a: int, b: int) -> int:
    """Multiply two numbers"""
    return a * b
if __name__ == "__main__":
    mcp.run(transport="stdio")
```

```python
# Weather server (streamable HTTP transport)
from mcp.server.fastmcp import FastMCP
mcp = FastMCP("Weather")
@mcp.tool()
async def get_weather(location: str) -> str:
    """Get weather for location."""
    return "It's always sunny in New York"
if __name__ == "__main__":
    mcp.run(transport="streamable-http")
```

## 有状态的工具使用

对于在工具调用之间维护上下文的**有状态**服务器，请使用 `client.session()` 来创建持久化的 `ClientSession`。

```python
# 使用 MCP ClientSession 进行有状态的工具使用
from langchain_mcp_adapters.tools import load_mcp_tools
client = MultiServerMCPClient({...})
async with client.session("math") as session:
    tools = await load_mcp_tools(session)
```

## 附加资源

- [MCP 文档](https://modelcontextprotocol.io/introduction)
- [MCP 传输文档](https://modelcontextprotocol.io/docs/concepts/transports)
- [`langchain-mcp-adapters`](https://langchain-doc.cn/v1/python/langchain/[https://github.com/langchain-ai/langchain-mcp-adapters](https://github.com/langchain-ai/langchain-mcp-adapters))