# 快速入门

本指南将引导您创建第一个具有规划、文件系统工具和子Agent功能的深度Agent。您将构建一个可以进行研究并撰写报告的研究Agent。

## 先决条件

在开始之前，请确保您拥有模型提供商（例如 Anthropic、OpenAI）的 API 密钥。

### 第 1 步：安装依赖项

```bash
pip install deepagents tavily-python
```

### 第 2 步：设置您的 API 密钥

```bash
export ANTHROPIC_API_KEY="your-api-key"
export TAVILY_API_KEY="your-tavily-api-key"
```

### 第 3 步：创建搜索工具

```python
import os
from typing import Literal
from tavily import TavilyClient
from deepagents import create_deep_agent
tavily_client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])
def internet_search(
    query: str,
    max_results: int = 5,
    topic: Literal["general", "news", "finance"] = "general",
    include_raw_content: bool = False,
):
    """运行网络搜索"""
    return tavily_client.search(
        query,
        max_results=max_results,
        include_raw_content=include_raw_content,
        topic=topic,
    )
```

### 第 4 步：创建深度Agent

```python
# 系统提示，引导Agent成为专家级研究员
research_instructions = """您是一位专家级研究员。您的工作是进行彻底的研究，然后撰写一份精美的报告。
您可以访问互联网搜索工具，作为收集信息的主要方式。
## `internet_search`
使用此工具对给定查询进行互联网搜索。您可以指定要返回的最大结果数、主题以及是否应包含原始内容。
"""
agent = create_deep_agent(
    tools=[internet_search],
    system_prompt=research_instructions
)
```

### 第 5 步：运行Agent

```python
result = agent.invoke({"messages": [{"role": "user", "content": "什么是 langgraph？"}]})
# 打印Agent的响应
print(result["messages"][-1].content)
```

## 发生了什么？

您的深度Agent会自动：

1. **规划其方法**：使用内置的 `write_todos` 工具来分解研究任务
2. **进行研究**：调用 `internet_search` 工具来收集信息
3. **管理上下文**：使用文件系统工具（`write_file`、`read_file`）来卸载大型搜索结果
4. **派生子Agent**（如果需要）：将复杂的子任务委托给专门的子Agent
5. **综合报告**：将调查结果汇编成连贯的响应

## 下一步

现在您已经构建了第一个深度Agent：

*   **自定义您的Agent**：了解[自定义选项](customization.html)，包括自定义系统提示、工具和子Agent。
*   **了解中间件**：深入了解支持深度Agent的[中间件架构](https://langchain-doc.cn/v1/python/deepagents/middleware)。
*   **添加长期记忆**：在对话中启用[持久记忆](long-term-memory.html)。
*   **部署到生产**：了解 LangGraph 应用程序的[部署选项](../langgraph/deploy.html)。