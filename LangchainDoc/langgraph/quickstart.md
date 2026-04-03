# 快速开始

本快速入门演示了如何使用LangGraph Graph API或Functional API构建计算器代理。

- 如果您更喜欢将代理定义为节点和边的图形，请使用[Graph API](#使用graph-api)。
- 如果您更喜欢将代理定义为单个函数，请使用[Functional API](#使用functional-api)。

有关概念信息，请参阅[Graph API概述](https://langchain-doc.cn/v1/python/langgraph/graph-api)和[Functional API概述](https://langchain-doc.cn/v1/python/langgraph/functional-api)。

**提示：** 对于本示例，您需要设置[Claude (Anthropic)](https://www.anthropic.com/)账户并获取API密钥。然后，在终端中设置`ANTHROPIC_API_KEY`环境变量。

## 使用Graph API

### 1. 定义工具和模型

在本示例中，我们将使用Claude Sonnet 4.5模型并定义加法、乘法和除法工具。

```python
from langchain.tools import tool
from langchain.chat_models import init_chat_model
model = init_chat_model(
    "claude-sonnet-4-5-20250929",
    temperature=0
)
# 定义工具
@tool
def multiply(a: int, b: int) -> int:
    """将`a`和`b`相乘。
    参数：
        a: 第一个整数
        b: 第二个整数
    """
    return a * b
@tool
def add(a: int, b: int) -> int:
    """将`a`和`b`相加。
    参数：
        a: 第一个整数
        b: 第二个整数
    """
    return a + b
@tool
def divide(a: int, b: int) -> float:
    """将`a`除以`b`。
    参数：
        a: 第一个整数
        b: 第二个整数
    """
    return a / b
# 增强LLM的工具能力
tools = [add, multiply, divide]
tools_by_name = {tool.name: tool for tool in tools}
model_with_tools = model.bind_tools(tools)
```

```typescript
import { ChatAnthropic } from "@langchain/anthropic";
import { tool } from "@langchain/core/tools";
import * as z from "zod";
const model = new ChatAnthropic({
  model: "claude-sonnet-4-5-20250929",
  temperature: 0,
});
// 定义工具
const add = tool(({ a, b }) => a + b, {
  name: "add",
  description: "Add two numbers",
  schema: z.object({
    a: z.number().describe("First number"),
    b: z.number().describe("Second number"),
  }),
});
const multiply = tool(({ a, b }) => a * b, {
  name: "multiply",
  description: "Multiply two numbers",
  schema: z.object({
    a: z.number().describe("First number"),
    b: z.number().describe("Second number"),
  }),
});
const divide = tool(({ a, b }) => a / b, {
  name: "divide",
  description: "Divide two numbers",
  schema: z.object({
    a: z.number().describe("First number"),
    b: z.number().describe("Second number"),
  }),
});
// 增强LLM的工具能力
const toolsByName = {
  [add.name]: add,
  [multiply.name]: multiply,
  [divide.name]: divide,
};
const tools = Object.values(toolsByName);
const modelWithTools = model.bindTools(tools);
```

### 2. 定义状态

图形的状态用于存储消息和LLM调用次数。

**提示：** LangGraph中的状态在代理执行过程中持续存在。带有`operator.add`的`Annotated`类型确保新消息被追加到现有列表中，而不是替换它。

```python
from langchain.messages import AnyMessage
from typing_extensions import TypedDict, Annotated
import operator
class MessagesState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    llm_calls: int
```

```typescript
import { StateGraph, START, END } from "@langchain/langgraph";
import { MessagesZodMeta } from "@langchain/langgraph";
import { registry } from "@langchain/langgraph/zod";
import { type BaseMessage } from "@langchain/core/messages";
const MessagesState = z.object({
  messages: z
    .array(z.custom<BaseMessage>())
    .register(registry, MessagesZodMeta),
  llmCalls: z.number().optional(),
});
```

### 3. 定义模型节点

模型节点用于调用LLM并决定是否调用工具。

```python
from langchain.messages import SystemMessage
def llm_call(state: dict):
    """LLM决定是否调用工具"""
    return {
        "messages": [
            model_with_tools.invoke(
                [
                    SystemMessage(
                        content="你是一个有用的助手，负责对一组输入执行算术运算。"
                    )
                ]
                + state["messages"]
            )
        ],
        "llm_calls": state.get('llm_calls', 0) + 1
    }
```

```typescript
import { SystemMessage } from "@langchain/core/messages";
async function llmCall(state: z.infer<typeof MessagesState>) {
  return {
    messages: await modelWithTools.invoke([
      new SystemMessage(
        "你是一个有用的助手，负责对一组输入执行算术运算。"
      ),
      ...state.messages,
    ]),
    llmCalls: (state.llmCalls ?? 0) + 1,
  };
}
```

### 4. 定义工具节点

工具节点用于调用工具并返回结果。

```python
from langchain.messages import ToolMessage
def tool_node(state: dict):
    """执行工具调用"""
    result = []
    for tool_call in state["messages"][-1].tool_calls:
        tool = tools_by_name[tool_call["name"]]
        observation = tool.invoke(tool_call["args"])
        result.append(ToolMessage(content=observation, tool_call_id=tool_call["id"]))
    return {"messages": result}
```

```typescript
import { isAIMessage, ToolMessage } from "@langchain/core/messages";
async function toolNode(state: z.infer<typeof MessagesState>) {
  const lastMessage = state.messages.at(-1);
  if (lastMessage == null || !isAIMessage(lastMessage)) {
    return { messages: [] };
  }
  const result: ToolMessage[] = [];
  for (const toolCall of lastMessage.tool_calls ?? []) {
    const tool = toolsByName[toolCall.name];
    const observation = await tool.invoke(toolCall);
    result.push(observation);
  }
  return { messages: result };
}
```

### 5. 定义结束逻辑

条件边函数用于根据LLM是否进行了工具调用来路由到工具节点或结束。

```python
from typing import Literal
from langgraph.graph import StateGraph, START, END
def should_continue(state: MessagesState) -> Literal["tool_node", END]:
    """决定是否继续循环或停止，基于LLM是否进行了工具调用"""
    messages = state["messages"]
    last_message = messages[-1]
    # 如果LLM进行了工具调用，则执行操作
    if last_message.tool_calls:
        return "tool_node"
    # 否则，我们停止（回复用户）
    return END
```

```typescript
async function shouldContinue(state: z.infer<typeof MessagesState>) {
  const lastMessage = state.messages.at(-1);
  if (lastMessage == null || !isAIMessage(lastMessage)) return END;
  // 如果LLM进行了工具调用，则执行操作
  if (lastMessage.tool_calls?.length) {
    return "toolNode";
  }
  // 否则，我们停止（回复用户）
  return END;
}
```

### 6. 构建并编译代理

代理使用`StateGraph`类构建，并使用`compile`方法编译。

```python
# 构建工作流
agent_builder = StateGraph(MessagesState)
# 添加节点
agent_builder.add_node("llm_call", llm_call)
agent_builder.add_node("tool_node", tool_node)
# 添加边连接节点
agent_builder.add_edge(START, "llm_call")
agent_builder.add_conditional_edges(
    "llm_call",
    should_continue,
    ["tool_node", END]
)
agent_builder.add_edge("tool_node", "llm_call")
# 编译代理
agent = agent_builder.compile()
# 显示代理
from IPython.display import Image, display
display(Image(agent.get_graph(xray=True).draw_mermaid_png()))
# 调用
from langchain.messages import HumanMessage
messages = [HumanMessage(content="3加4等于多少。")]
messages = agent.invoke({"messages": messages})
for m in messages["messages"]:
    m.pretty_print()
```

```typescript
const agent = new StateGraph(MessagesState)
  .addNode("llmCall", llmCall)
  .addNode("toolNode", toolNode)
  .addEdge(START, "llmCall")
  .addConditionalEdges("llmCall", shouldContinue, ["toolNode", END])
  .addEdge("toolNode", "llmCall")
  .compile();
// 调用
import { HumanMessage } from "@langchain/core/messages";
const result = await agent.invoke({
  messages: [new HumanMessage("3加4等于多少。")],
});
for (const message of result.messages) {
  console.log(`[${message.getType()}]: ${message.text}`);
}
```

**提示：** 要了解如何使用LangSmith跟踪您的代理，请参阅[LangSmith文档](https://langchain-doc.cn/langsmith/trace-with-langgraph)。

恭喜！您已经使用LangGraph Graph API构建了第一个代理。

## 使用Functional API

### 1. 定义工具和模型

在本示例中，我们将使用Claude Sonnet 4.5模型并定义加法、乘法和除法工具。

```python
from langchain.tools import tool
from langchain.chat_models import init_chat_model
model = init_chat_model(
    "claude-sonnet-4-5-20250929",
    temperature=0
)
# 定义工具
@tool
def multiply(a: int, b: int) -> int:
    """将`a`和`b`相乘。
    参数：
        a: 第一个整数
        b: 第二个整数
    """
    return a * b
@tool
def add(a: int, b: int) -> int:
    """将`a`和`b`相加。
    参数：
        a: 第一个整数
        b: 第二个整数
    """
    return a + b
@tool
def divide(a: int, b: int) -> float:
    """将`a`除以`b`。
    参数：
        a: 第一个整数
        b: 第二个整数
    """
    return a / b
# 增强LLM的工具能力
tools = [add, multiply, divide]
tools_by_name = {tool.name: tool for tool in tools}
model_with_tools = model.bind_tools(tools)
from langgraph.graph import add_messages
from langchain.messages import (
    SystemMessage,
    HumanMessage,
    ToolCall,
)
from langchain_core.messages import BaseMessage
from langgraph.func import entrypoint, task
```

```typescript
import { ChatAnthropic } from "@langchain/anthropic";
import { tool } from "@langchain/core/tools";
import * as z from "zod";
const model = new ChatAnthropic({
  model: "claude-sonnet-4-5-20250929",
  temperature: 0,
});
// 定义工具
const add = tool(({ a, b }) => a + b, {
  name: "add",
  description: "Add two numbers",
  schema: z.object({
    a: z.number().describe("First number"),
    b: z.number().describe("Second number"),
  }),
});
const multiply = tool(({ a, b }) => a * b, {
  name: "multiply",
  description: "Multiply two numbers",
  schema: z.object({
    a: z.number().describe("First number"),
    b: z.number().describe("Second number"),
  }),
});
const divide = tool(({ a, b }) => a / b, {
  name: "divide",
  description: "Divide two numbers",
  schema: z.object({
    a: z.number().describe("First number"),
    b: z.number().describe("Second number"),
  }),
});
// 增强LLM的工具能力
const toolsByName = {
  [add.name]: add,
  [multiply.name]: multiply,
  [divide.name]: divide,
};
const tools = Object.values(toolsByName);
const modelWithTools = model.bindTools(tools);
```

### 2. 定义模型节点

模型节点用于调用LLM并决定是否调用工具。

**提示：** `@task`装饰器将函数标记为可以作为代理一部分执行的任务。任务可以在入口点函数内同步或异步调用。

```python
@task
def call_llm(messages: list[BaseMessage]):
    """LLM决定是否调用工具"""
    return model_with_tools.invoke(
        [
            SystemMessage(
                content="你是一个有用的助手，负责对一组输入执行算术运算。"
            )
        ]
        + messages
    )
```

```typescript
import { task, entrypoint } from "@langchain/langgraph";
import { SystemMessage } from "@langchain/core/messages";
const callLlm = task({ name: "callLlm" }, async (messages: BaseMessage[]) => {
  return modelWithTools.invoke([
    new SystemMessage(
      "你是一个有用的助手，负责对一组输入执行算术运算。"
    ),
    ...messages,
  ]);
});
```

### 3. 定义工具节点

工具节点用于调用工具并返回结果。

```python
@task
def call_tool(tool_call: ToolCall):
    """执行工具调用"""
    tool = tools_by_name[tool_call["name"]]
    return tool.invoke(tool_call)
```

```typescript
import type { ToolCall } from "@langchain/core/messages/tool";
const callTool = task({ name: "callTool" }, async (toolCall: ToolCall) => {
  const tool = toolsByName[toolCall.name];
  return tool.invoke(toolCall);
});
```

### 4. 定义代理

代理使用`@entrypoint`函数构建。

**注意：** 在Functional API中，您不需要显式定义节点和边，而是在单个函数内编写标准控制流逻辑（循环、条件）。

```python
@entrypoint()
def agent(messages: list[BaseMessage]):
    model_response = call_llm(messages).result()
    while True:
        if not model_response.tool_calls:
            break
        # 执行工具
        tool_result_futures = [
            call_tool(tool_call) for tool_call in model_response.tool_calls
        ]
        tool_results = [fut.result() for fut in tool_result_futures]
        messages = add_messages(messages, [model_response, *tool_results])
        model_response = call_llm(messages).result()
    messages = add_messages(messages, model_response)
    return messages
# 调用
messages = [HumanMessage(content="3加4等于多少。")]
for chunk in agent.stream(messages, stream_mode="updates"):
    print(chunk)
    print("\n")
```

```typescript
import { addMessages } from "@langchain/langgraph";
import { type BaseMessage, isAIMessage } from "@langchain/core/messages";
const agent = entrypoint({ name: "agent" }, async (messages: BaseMessage[]) => {
  let modelResponse = await callLlm(messages);
  while (true) {
    if (!modelResponse.tool_calls?.length) {
      break;
    }
    // 执行工具
    const toolResults = await Promise.all(
      modelResponse.tool_calls.map((toolCall) => callTool(toolCall))
    );
    messages = addMessages(messages, [modelResponse, ...toolResults]);
    modelResponse = await callLlm(messages);
  }
  return messages;
});
// 调用
import { HumanMessage } from "@langchain/core/messages";
const result = await agent.invoke([new HumanMessage("3加4等于多少。")]);
for (const message of result) {
  console.log(`[${message.getType()}]: ${message.text}`);
}
```

**提示：** 要了解如何使用LangSmith跟踪您的代理，请参阅[LangSmith文档](https://langchain-doc.cn/langsmith/trace-with-langgraph)。

恭喜！您已经使用LangGraph Functional API构建了第一个代理。