# LangChain 概述

> **LangChain v1.0 已发布！**
>
> 有关完整的更新内容和升级指南，请查看 [发布说明](releases/langchain-v1.html) 和 [迁移指南](migrate/langchain-v1.html)。  
> 如果遇到问题或有反馈，请 [提交 issue](https://github.com/langchain-ai/docs/issues/new?template=01-langchain.yml) 以帮助我们改进。  
> 若需查看 v0.x 文档，请访问 [存档网站](../../../introduction/index.html)。

LangChain 是最快速入门构建基于 LLM 的智能代理和应用的方法。不到 10 行代码，你就可以连接 OpenAI、Anthropic、Google 以及更多提供商（[详见](../integrations/providers/overview.html)）。LangChain 提供预构建的代理架构和模型集成，帮助你快速启动并无缝将 LLM 集成到你的应用中。

如果你想快速构建代理和自主应用，建议使用 LangChain。  
当你有更复杂的需求，需要结合确定性与智能工作流、高度自定义以及精确延迟控制时，可使用 [LangGraph](../langgraph/overview.html)，这是我们提供的低级代理编排框架和运行时。

LangChain [agents](agents.html) 构建在 LangGraph 之上，提供持久化执行、流式处理、人类参与、数据持久化等功能。基础使用无需了解 LangGraph。

## 安装

### Python

```bash
pip install -U langchain
```

```bash
uv add langchain
```

### JavaScript / TypeScript

```bash
npm install langchain @langchain/core
```

```bash
pnpm add langchain @langchain/core
```

```bash
yarn add langchain @langchain/core
```

```bash
bun add langchain @langchain/core
```

## 创建代理

### Python 示例

```python
# pip install -qU "langchain[anthropic]" 调用模型
from langchain.agents import create_agent
def get_weather(city: str) -> str:
    """获取指定城市的天气"""
    return f"{city} 天气总是晴朗！"
agent = create_agent(
    model="anthropic:claude-sonnet-4-5",
    tools=[get_weather],
    system_prompt="你是一个乐于助人的助手",
)
# 执行代理
agent.invoke(
    {"messages": [{"role": "user", "content": "旧金山天气如何？"}]}
)
```

### JavaScript / TypeScript 示例

```ts
import * as z from "zod";
// npm install @langchain/anthropic 调用模型
import { createAgent, tool } from "langchain";
const getWeather = tool(
  ({ city }) => `${city} 天气总是晴朗！`,
  {
    name: "get_weather",
    description: "获取指定城市的天气",
    schema: z.object({
      city: z.string(),
    }),
  },
);
const agent = createAgent({
  model: "anthropic:claude-sonnet-4-5",
  tools: [getWeather],
});
console.log(
  await agent.invoke({
    messages: [{ role: "user", content: "东京天气如何？" }],
  })
);
```

## 核心优势

| 标题 | 描述 |
| :--- | :--- |
| **标准模型接口** | 不同提供商有各自独特的 API，包括响应格式。LangChain 标准化了模型交互方式，使你可以无缝切换提供商，避免锁定。 |
| **易用且高度灵活的代理** | LangChain 的代理抽象非常易于上手，10 行代码即可创建简单代理，同时也支持复杂的上下文管理和自定义操作。 |
| **构建于 LangGraph 之上** | LangChain 的代理构建在 LangGraph 上，支持持久执行、人类参与、持久化等功能。 |
| **使用 LangSmith 调试** | 提供可视化工具，跟踪执行路径、状态转换并生成详细运行时指标，让复杂代理行为可视化。 |