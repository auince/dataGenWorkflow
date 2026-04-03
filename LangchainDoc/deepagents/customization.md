# 自定义深度Agent

## 模型

默认情况下，`deepagents` 使用 `"claude-sonnet-4-5-20250929"`。您可以通过传递任何 [LangChain 模型对象](https://python.langchain.com/docs/integrations/chat/) 来自定义它。

```python
from langchain.chat_models import init_chat_model
from deepagents import create_deep_agent
model = init_chat_model(
    model="gpt-5",
)
agent = create_deep_agent(
    model=model,
)
```

```typescript
// TODO: 添加 JS 实现
```

## 系统提示

深度Agent带有一个内置的系统提示，其灵感来自 Claude Code 的系统提示。默认系统提示包含使用内置规划工具、文件系统工具和子Agent的详细说明。

每个针对特定用例的深度Agent都应包含一个特定于该用例的自定义系统提示。

```python
from deepagents import create_deep_agent
research_instructions = """\
您是一位专业的研究员。您的工作是进行 \
深入的研究，然后撰写一份精美的报告。 \
"""
agent = create_deep_agent(
    system_prompt=research_instructions,
)
```

```typescript
// TODO: 添加 JS 实现
```

## 工具

就像调用工具的Agent一样，深度Agent可以访问一组顶层工具。

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
agent = create_deep_agent(
    tools=[internet_search]
)
```

```typescript
// TODO: 添加 JS 实现
```

除了您提供的任何工具外，深度Agent还可以访问许多默认工具：

* `write_todos` – 更新Agent的待办事项列表
* `ls` – 列出Agent文件系统中的所有文件
* `read_file` – 从Agent的文件系统中读取文件
* `write_file` – 在Agent的文件系统中写入一个新文件
* `edit_file` – 编辑Agent文件系统中的现有文件
* `task` – 生成一个子Agent来处理特定任务