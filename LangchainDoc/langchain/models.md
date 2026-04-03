# 模型

[大语言模型（LLMs）](https://en.wikipedia.org/wiki/Large_language_model) 是强大的 AI 工具，能够像人类一样理解和生成文本。它们用途广泛，可用于撰写内容、翻译语言、总结信息和回答问题，而无需针对每项任务进行专门训练。

除了文本生成之外，许多模型还支持：

*   **工具调用** - 调用外部工具（如数据库查询或 API 调用）并将结果用于响应中。
*   **结构化输出** - 模型的响应被限制为遵循定义的格式。
*   **多模态** - 处理和返回非文本数据，如图像、音频和视频。
*   **推理** - 模型执行多步推理以得出结论。

模型是 [代理](agents.html) 的推理引擎。它们驱动代理的决策过程，决定调用哪些工具、如何解释结果以及何时提供最终答案。

您选择的模型的质量和能力直接影响代理的可靠性和性能。不同模型在不同任务上表现出色——有些更擅长遵循复杂指令，有些更擅长结构化推理，有些支持更大的上下文窗口以处理更多信息。

LangChain 的标准模型接口为您提供对众多不同提供商集成的访问，这使得实验和切换模型以找到最适合您用例的模型变得非常容易。

> **信息**
> 有关特定提供商的集成信息和功能，请参阅提供商的[集成页面](../integrations/providers/overview.html)。

## 基本用法

模型可以通过两种方式使用：

1.  **与代理一起使用** - 创建[代理](agents.html#model)时可动态指定模型。
2.  **独立使用** - 模型可直接调用（在代理循环之外），用于文本生成、分类或提取等任务，而无需代理框架。

同一模型接口在两种上下文中均适用，这为您提供了从简单开始并根据需要扩展到更复杂基于代理的工作流程的灵活性。

### 初始化模型

在 LangChain 中开始使用独立模型的最简单方法是使用 [`init_chat_model`](https://reference.langchain.com/python/langchain/models/#langchain.chat_models.init_chat_model) 从您选择的[提供商](../integrations/providers/overview.html)初始化一个模型（以下示例）：

---

### OpenAI

👉 阅读 [OpenAI 聊天模型集成文档](https://langchain-doc.cn/v1/python/integrations/chat/openai/)

```shell
pip install -U "langchain[openai]"
```

```python
import os
from langchain.chat_models import init_chat_model
os.environ["OPENAI_API_KEY"] = "sk-..."
model = init_chat_model("openai:gpt-4.1")
```

```python
import os
from langchain_openai import ChatOpenAI
os.environ["OPENAI_API_KEY"] = "sk-..."
model = ChatOpenAI(model="gpt-4.1")
```

---

### Anthropic

👉 阅读 [Anthropic 聊天模型集成文档](https://langchain-doc.cn/v1/python/integrations/chat/anthropic/)

```shell
pip install -U "langchain[anthropic]"
```

```python
import os
from langchain.chat_models import init_chat_model
os.environ["ANTHROPIC_API_KEY"] = "sk-..."
model = init_chat_model("anthropic:claude-sonnet-4-5")
```

```python
import os
from langchain_anthropic import ChatAnthropic
os.environ["ANTHROPIC_API_KEY"] = "sk-..."
model = ChatAnthropic(model="claude-sonnet-4-5")
```

---

### Azure

👉 阅读 [Azure 聊天模型集成文档](https://langchain-doc.cn/v1/python/integrations/chat/azure_chat_openai/)

```shell
pip install -U "langchain[openai]"
```

```python
import os
from langchain.chat_models import init_chat_model
os.environ["AZURE_OPENAI_API_KEY"] = "..."
os.environ["AZURE_OPENAI_ENDPOINT"] = "..."
os.environ["OPENAI_API_VERSION"] = "2025-03-01-preview"
model = init_chat_model(
    "azure_openai:gpt-4.1",
    azure_deployment=os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"],
)
```

```python
import os
from langchain_openai import AzureChatOpenAI
os.environ["AZURE_OPENAI_API_KEY"] = "..."
os.environ["AZURE_OPENAI_ENDPOINT"] = "..."
os.environ["OPENAI_API_VERSION"] = "2025-03-01-preview"
model = AzureChatOpenAI(
    model="gpt-4.1",
    azure_deployment=os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"]
)
```

---

### Google Gemini

👉 阅读 [Google GenAI 聊天模型集成文档](https://langchain-doc.cn/v1/python/integrations/chat/google_generative_ai/)

```shell
pip install -U "langchain[google-genai]"
```

```python
import os
from langchain.chat_models import init_chat_model
os.environ["GOOGLE_API_KEY"] = "..."
model = init_chat_model("google_genai:gemini-2.5-flash-lite")
```

```python
import os
from langchain_google_genai import ChatGoogleGenerativeAI
os.environ["GOOGLE_API_KEY"] = "..."
model = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite")
```

---

### AWS Bedrock

👉 阅读 [AWS Bedrock 聊天模型集成文档](https://langchain-doc.cn/v1/python/integrations/chat/bedrock/)

```shell
pip install -U "langchain[aws]"
```

```python
from langchain.chat_models import init_chat_model
# 请按照此处的步骤配置您的凭据：
# https://docs.aws.amazon.com/bedrock/latest/userguide/getting-started.html
model = init_chat_model(
    "anthropic.claude-3-5-sonnet-20240620-v1:0",
    model_provider="bedrock_converse",
)
```

```python
from langchain_aws import ChatBedrock
model = ChatBedrock(model="anthropic.claude-3-5-sonnet-20240620-v1:0")
```

---

```python
response = model.invoke("为什么鹦鹉会说话？")
```

有关更多详细信息，包括如何传递模型[参数](models.html#%E5%8F%82%E6%95%B0)，请参阅 [`init_chat_model`](https://reference.langchain.com/python/langchain/models/#langchain.chat_models.init_chat_model)。

### 关键方法

| 方法 | 说明 |
| :--- | :--- |
| **Invoke** | 模型接受消息作为输入，并在生成完整响应后输出消息。 |
| **Stream** | 调用模型，但实时流式传输生成的输出。 |
| **Batch** | 将多个请求批量发送给模型，以实现更高效的处理。 |

> **信息**
> 除了聊天模型之外，LangChain 还支持其他相关技术，如嵌入模型和向量存储。详情请参阅[集成页面](../integrations/providers/overview.html)。

## 参数

聊天模型接受可用于配置其行为的一组参数。支持的参数集因模型和提供商而异，但标准参数包括：

| 参数 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| `model` | string | 是 | 您想使用的特定模型的名称或标识符。 |
| `api_key` | string | 否 | 用于向模型提供商进行身份验证的密钥。通常在注册访问模型时颁发。通常通过设置**环境变量**访问。 |
| `temperature` | number | 否 | 控制模型输出的随机性。值越高，响应越具创造性；值越低，响应越确定性。 |
| `timeout` | number | 否 | 在取消请求之前等待模型响应的最大时间（秒）。 |
| `max_tokens` | number | 否 | 限制响应中的**令牌**总数，有效控制输出长度。 |
| `max_retries` | number | 否 | 如果因网络超时或速率限制等问题而失败，系统将重新发送请求的最大尝试次数。 |

使用 [`init_chat_model`](https://reference.langchain.com/python/langchain/models/#langchain.chat_models.init_chat_model)，将这些参数作为内联 `**kwargs` 传递：

```python
model = init_chat_model(
    "anthropic:claude-sonnet-4-5",
    # 传递给模型的 Kwargs：
    temperature=0.7,
    timeout=30,
    max_tokens=1000,
)
```

> **信息**
> 每个聊天模型集成可能具有用于控制提供商特定功能的额外参数。例如，[`ChatOpenAI`](https://reference.langchain.com/python/integrations/langchain_openai/ChatOpenAI/) 具有 `use_responses_api` 以决定是否使用 OpenAI Responses 或 Completions API。
> 要查找给定聊天模型支持的所有参数，请转到[聊天模型集成](../integrations/chat.html)页面。

---

## 调用

必须调用聊天模型以生成输出。主要有三种调用方法，每种方法适用于不同的用例。

### Invoke

调用模型的最直接方法是使用 [`invoke()`](https://reference.langchain.com/python/langchain_core/language_models/#langchain_core.language_models.chat_models.BaseChatModel.invoke) 传入单个消息或消息列表。

```python
response = model.invoke("为什么鹦鹉有五颜六色的羽毛？")
print(response)
```

可以向模型提供消息列表以表示对话历史。每条消息都有一个角色，模型用它来指示对话中谁发送了消息。有关角色、类型和内容的更多详细信息，请参阅[消息](messages.html)指南。

```python
from langchain.messages import HumanMessage, AIMessage, SystemMessage
conversation = [
    {"role": "system", "content": "你是一个将英语翻译成法语的有用助手。"},
    {"role": "user", "content": "翻译：我喜欢编程。"},
    {"role": "assistant", "content": "J'adore la programmation."},
    {"role": "user", "content": "翻译：我喜欢构建应用程序。"}
]
response = model.invoke(conversation)
print(response)  # AIMessage("J'adore créer des applications.")
```

```python
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
conversation = [
    SystemMessage("你是一个将英语翻译成法语的有用助手。"),
    HumanMessage("翻译：我喜欢编程。"),
    AIMessage("J'adore la programmation。"),
    HumanMessage("翻译：我喜欢构建应用程序。")
]
response = model.invoke(conversation)
print(response)  # AIMessage("J'adore créer des applications。")
```

### Stream

大多数模型可以在生成时流式传输其输出内容。通过逐步显示输出，流式传输显著改善了用户体验，尤其是对于较长的响应。

调用 [`stream()`](https://reference.langchain.com/python/langchain_core/language_models/#langchain_core.language_models.chat_models.BaseChatModel.stream) 返回一个**迭代器**，它在生成时逐块产生输出。您可以使用循环实时处理每个块：

```python
for chunk in model.stream("为什么鹦鹉有五颜六色的羽毛？"):
    print(chunk.text, end="|", flush=True)
```

```python
for chunk in model.stream("天空是什么颜色？"):
    for block in chunk.content_blocks:
        if block["type"] == "reasoning" and (reasoning := block.get("reasoning")):
            print(f"推理：{reasoning}")
        elif block["type"] == "tool_call_chunk":
            print(f"工具调用块：{block}")
        elif block["type"] == "text":
            print(block["text"])
        else:
            ...
```

与返回单个 [`AIMessage`](https://reference.langchain.com/python/langchain/messages/#langchain.messages.AIMessage) 的 [`invoke()`](models.html#invoke) 不同，`stream()` 返回多个 [`AIMessageChunk`](https://reference.langchain.com/python/langchain/messages/#langchain.messages.AIMessageChunk) 对象，每个对象包含一部分输出文本。重要的是，流中的每个块都设计为通过求和聚合成完整消息：

```python
full = None  # None | AIMessageChunk
for chunk in model.stream("天空是什么颜色？"):
    full = chunk if full is None else full + chunk
    print(full.text)
# 天空
# 天空是
# 天空通常
# 天空通常是蓝色
# ...
print(full.content_blocks)
# [{"type": "text", "text": "天空通常是蓝色..."}]
```

生成的消息可以与使用 [`invoke()`](models.html#invoke) 生成的消息相同处理——例如，它可以聚合成消息历史并作为对话上下文传递回模型。

> **警告**
> 流式传输仅在程序的所有步骤都知道如何处理块流时才有效。例如，无法流式传输的应用程序是需要先将整个输出存储在内存中才能处理的情况。

#### 高级流式传输主题

##### “自动流式传输”聊天模型

LangChain 通过在某些情况下自动启用流式传输模式来简化从聊天模型进行流式传输，即使您未显式调用流式传输方法。这在您使用非流式传输的 invoke 方法但仍希望流式传输整个应用程序（包括聊天模型的中间结果）时特别有用。

例如，在 [LangGraph 代理](agents.html) 中，您可以在节点内调用 `model.invoke()`，但如果在流式传输模式下运行，LangChain 将自动委托给流式传输。

**工作原理**

当您 `invoke()` 一个聊天模型时，如果 LangChain 检测到您正在尝试流式传输整个应用程序，它将自动切换到内部流式传输模式。对于使用 invoke 的代码，结果是相同的；然而，在聊天模型流式传输时，LangChain 将负责在 LangChain 的回调系统中调用 [`on_llm_new_token`](https://reference.langchain.com/python/langchain_core/callbacks/#langchain_core.callbacks.base.AsyncCallbackHandler.on_llm_new_token) 事件。

回调事件允许 LangGraph 的 `stream()` 和 [`astream_events()`](https://reference.langchain.com/python/langchain_core/language_models/#langchain_core.language_models.chat_models.BaseChatModel.astream_events) 实时显示聊天模型的输出。

##### 流式传输事件

LangChain 聊天模型还可以使用 [`astream_events()`](https://reference.langchain.com/python/langchain_core/language_models/#langchain_core.language_models.chat_models.BaseChatModel.astream_events) 流式传输语义事件。

这简化了基于事件类型和其他元数据的过滤，并在后台聚合完整消息。请参阅以下示例。

```python
async for event in model.astream_events("你好"):
    if event["event"] == "on_chat_model_start":
        print(f"输入：{event['data']['input']}")
    elif event["event"] == "on_chat_model_stream":
        print(f"令牌：{event['data']['chunk'].text}")
    elif event["event"] == "on_chat_model_end":
        print(f"完整消息：{event['data']['output'].text}")
    else:
        pass
```

```txt
输入：你好
令牌：你
令牌：好
令牌：！
令牌：我
令牌：能
令牌：如
...
完整消息：你好！今天我能如何帮助您？
```

> **提示**
> 请参阅 [`astream_events()`](https://reference.langchain.com/python/langchain_core/language_models/#langchain_core.language_models.chat_models.BaseChatModel.astream_events) 参考，了解事件类型和其他详细信息。

### Batch

将一组独立请求批量处理给模型可以显著提高性能并降低成本，因为处理可以并行进行：

```python
responses = model.batch([
    "为什么鹦鹉有五颜六色的羽毛？",
    "飞机是如何飞行的？",
    "什么是量子计算？"
])
for response in responses:
    print(response)
```

> **注意**
> 本节描述的是聊天模型方法 [`batch()`](https://reference.langchain.com/python/langchain_core/language_models/#langchain_core.language_models.chat_models.BaseChatModel.batch)，它在客户端并行化模型调用。
> 它**不同于**推理提供商支持的批量 API，例如 [OpenAI](https://platform.openai.com/docs/guides/batch) 或 [Anthropic](https://docs.claude.com/en/docs/build-with-claude/batch-processing#message-batches-api)。

默认情况下，[`batch()`](https://reference.langchain.com/python/langchain_core/language_models/#langchain_core.language_models.chat_models.BaseChatModel.batch) 仅返回整个批次的最终输出。如果您希望在每个单独输入完成生成时接收输出，可以使用 [`batch_as_completed()`](https://reference.langchain.com/python/langchain_core/language_models/#langchain_core.language_models.chat_models.BaseChatModel.batch_as_completed) 流式传输结果：

```python
for response in model.batch_as_completed([
    "为什么鹦鹉有五颜六色的羽毛？",
    "飞机是如何飞行的？",
    "什么是量子计算？"
]):
    print(response)
```

> **注意**
> 使用 [`batch_as_completed()`](https://reference.langchain.com/python/langchain_core/language_models/#langchain_core.language_models.chat_models.BaseChatModel.batch_as_completed) 时，结果可能无序到达。每个结果包括输入索引，以便根据需要匹配和重建原始顺序。

> **提示**
> 在使用 [`batch()`](https://reference.langchain.com/python/langchain_core/language_models/#langchain_core.language_models.chat_models.BaseChatModel.batch) 或 [`batch_as_completed()`](https://reference.langchain.com/python/langchain_core/language_models/#langchain_core.language_models.chat_models.BaseChatModel.batch_as_completed) 处理大量输入时，您可能希望控制最大并行调用数。这可以通过在 [`RunnableConfig`](https://reference.langchain.com/python/langchain_core/runnables/#langchain_core.runnables.RunnableConfig) 字典中设置 [`max_concurrency`](https://reference.langchain.com/python/langchain_core/runnables/#langchain_core.runnables.RunnableConfig.max_concurrency) 属性来完成。

```python
model.batch(
    list_of_inputs,
    config={
        'max_concurrency': 5,  # 限制为 5 个并行调用
    }
)
```

有关批处理的更多详细信息，请参阅[参考](https://reference.langchain.com/python/langchain_core/language_models/#langchain_core.language_models.chat_models.BaseChatModel.batch)。

---

## 工具调用

模型可以请求调用执行任务的工具，例如从数据库获取数据、搜索网络或运行代码。工具是以下内容的配对：

1.  架构，包括工具的名称、描述和/或参数定义（通常是 JSON 架构）
2.  要执行的函数或**协程**

> **注意**
> 您可能会听到“函数调用”一词。我们将此与“工具调用”互换使用。

要使您定义的工具可供模型使用，您必须使用 [`bind_tools()`](https://reference.langchain.com/python/langchain_core/language_models/#langchain_core.language_models.chat_models.BaseChatModel.bind_tools) 绑定它们。在后续调用中，模型可以根据需要选择调用任何绑定的工具。

一些模型提供商提供内置工具，可通过模型或调用参数启用（例如 [`ChatOpenAI`](https://langchain-doc.cn/v1/python/integrations/chat/openai)、[`ChatAnthropic`](https://langchain-doc.cn/v1/python/integrations/chat/anthropic)）。请查看相应的[提供商参考](../integrations/providers/overview.html)以了解详细信息。

> **提示**
> 有关创建工具的详细信息和其他选项，请参阅[工具指南](tools.html)。

```python
from langchain.tools import tool
@tool
def get_weather(location: str) -> str:
    """获取某个位置的天气。"""
    return f"{location} 天气晴朗。"
model_with_tools = model.bind_tools([get_weather])  # [!code highlight]
response = model_with_tools.invoke("波士顿的天气怎么样？")
for tool_call in response.tool_calls:
    # 查看模型发出的工具调用
    print(f"工具：{tool_call['name']}")
    print(f"参数：{tool_call['args']}")
```

绑定用户定义的工具时，模型的响应包括**请求**执行工具。当将模型与[代理](agents.html)分开使用时，您需要执行请求的操作并将结果返回给模型以用于后续推理。请注意，当使用[代理](agents.html)时，代理循环将为您处理工具执行循环。

下面展示了一些使用工具调用的常见方法。

### 工具执行循环

当模型返回工具调用时，您需要执行工具并将结果传递回模型。这会创建一个对话循环，模型可以使用工具结果生成其最终响应。LangChain 包含[代理](agents.html)抽象来为您处理此协调。

以下是一个简单示例：

```python
# 将（可能多个）工具绑定到模型
model_with_tools = model.bind_tools([get_weather])
# 步骤 1：模型生成工具调用
messages = [{"role": "user", "content": "波士顿的天气怎么样？"}]
ai_msg = model_with_tools.invoke(messages)
messages.append(ai_msg)
# 步骤 2：执行工具并收集结果
for tool_call in ai_msg.tool_calls:
    # 使用生成的参数执行工具
    tool_result = get_weather.invoke(tool_call)
    messages.append(tool_result)
# 步骤 3：将结果传递回模型以获取最终响应
final_response = model_with_tools.invoke(messages)
print(final_response.text)
# "波士顿当前天气为 72°F，晴朗。"
```

每个由工具返回的 [`ToolMessage`](https://reference.langchain.com/python/langchain/messages/#langchain.messages.ToolMessage) 包含一个与原始工具调用匹配的 `tool_call_id`，帮助模型将结果与请求相关联。

### 强制工具调用

默认情况下，模型可以根据用户输入自由选择使用哪个绑定的工具。但是，您可能希望强制选择工具，确保模型使用特定工具或给定列表中的**任何**工具：

```python
model_with_tools = model.bind_tools([tool_1], tool_choice="any")
```

```python
model_with_tools = model.bind_tools([tool_1], tool_choice="tool_1")
```

### 并行工具调用

许多模型支持在适当时并行调用多个工具。这允许模型同时从不同来源收集信息。

```python
model_with_tools = model.bind_tools([get_weather])
response = model_with_tools.invoke(
    "波士顿和东京的天气怎么样？"
)
# 模型可能会生成多个工具调用
print(response.tool_calls)
# [
#   {'name': 'get_weather', 'args': {'location': 'Boston'}, 'id': 'call_1'},
#   {'name': 'get_weather', 'args': {'location': 'Tokyo'}, 'id': 'call_2'},
# ]
# 执行所有工具（可以使用 async 并行执行）
results = []
for tool_call in response.tool_calls:
    if tool_call['name'] == 'get_weather':
        result = get_weather.invoke(tool_call)
    ...
    results.append(result)
```

模型根据请求操作的独立性智能地确定何时适合并行执行。

> **提示**
> 大多数支持工具调用的模型默认启用并行工具调用。某些模型（包括 [OpenAI](https://langchain-doc.cn/v1/python/integrations/chat/openai) 和 [Anthropic](https://langchain-doc.cn/v1/python/integrations/chat/anthropic)）允许您禁用此功能。要执行此操作，请设置 `parallel_tool_calls=False`：

```python
model.bind_tools([get_weather], parallel_tool_calls=False)
```

### 流式传输工具调用

在流式传输响应时，工具调用通过 [`ToolCallChunk`](https://reference.langchain.com/python/langchain/messages/#langchain.messages.ToolCallChunk) 逐步构建。这允许您在生成工具调用时查看它们，而不是等待完整响应。

```python
for chunk in model_with_tools.stream(
    "波士顿和东京的天气怎么样？"
):
    # 工具调用块逐步到达
    for tool_chunk in chunk.tool_call_chunks:
        if name := tool_chunk.get("name"):
            print(f"工具：{name}")
        if id_ := tool_chunk.get("id"):
            print(f"ID：{id_}")
        if args := tool_chunk.get("args"):
            print(f"参数：{args}")
# 输出：
# 工具：get_weather
# ID：call_SvMlU1TVIZugrFLckFE2ceRE
# 参数：{"lo
# 参数：catio
# 参数：n": "B
# 参数：osto
# 参数：n"}
# 工具：get_weather
# ID：call_QMZdy6qInx13oWKE7KhuhOLR
# 参数：{"lo
# 参数：catio
# 参数：n": "T
# 参数：okyo
# 参数："}
```

您可以累积块以构建完整的工具调用：

```python
gathered = None
for chunk in model_with_tools.stream("波士顿的天气怎么样？"):
    gathered = chunk if gathered is None else gathered + chunk
    print(gathered.tool_calls)
```

---

## 结构化输出

可以请求模型以匹配给定架构的格式提供其响应。这对于确保输出易于解析并用于后续处理非常有用。LangChain 支持多种架构类型和强制执行结构化输出的方法。

### Pydantic

[Pydantic 模型](https://docs.pydantic.dev/latest/concepts/models/#basic-model-usage) 提供最丰富的功能集，包括字段验证、描述和嵌套结构。

```python
from pydantic import BaseModel, Field
class Movie(BaseModel):
    """一部带有详细信息的电影。"""
    title: str = Field(..., description="电影标题")
    year: int = Field(..., description="电影上映年份")
    director: str = Field(..., description="电影导演")
    rating: float = Field(..., description="电影评分，满分 10 分")
model_with_structure = model.with_structured_output(Movie)
response = model_with_structure.invoke("提供关于电影《盗梦空间》的详细信息")
print(response)  # Movie(title="Inception", year=2010, director="Christopher Nolan", rating=8.8)
```

### TypedDict

`TypedDict` 提供使用 Python 内置类型的更简单替代方案，适用于不需要运行时验证的情况。

```python
from typing_extensions import TypedDict, Annotated
class MovieDict(TypedDict):
    """一部带有详细信息的电影。"""
    title: Annotated[str, ..., "电影标题"]
    year: Annotated[int, ..., "电影上映年份"]
    director: Annotated[str, ..., "电影导演"]
    rating: Annotated[float, ..., "电影评分，满分 10 分"]
model_with_structure = model.with_structured_output(MovieDict)
response = model_with_structure.invoke("提供关于电影《盗梦空间》的详细信息")
print(response)  # {'title': 'Inception', 'year': 2010, 'director': 'Christopher Nolan', 'rating': 8.8}
```

### JSON Schema

为了获得最大控制或互操作性，您可以提供原始 JSON 架构。

```python
import json
json_schema = {
    "title": "Movie",
    "description": "一部带有详细信息的电影",
    "type": "object",
    "properties": {
        "title": {
            "type": "string",
            "description": "电影标题"
        },
        "year": {
            "type": "integer",
            "description": "电影上映年份"
        },
        "director": {
            "type": "string",
            "description": "电影导演"
        },
        "rating": {
            "type": "number",
            "description": "电影评分，满分 10 分"
        }
    },
    "required": ["title", "year", "director", "rating"]
}
model_with_structure = model.with_structured_output(
    json_schema,
    method="json_schema",
)
response = model_with_structure.invoke("提供关于电影《盗梦空间》的详细信息")
print(response)  # {'title': 'Inception', 'year': 2010, ...}
```

> **注意**
> **结构化输出的关键考虑因素：**
>
> *   **方法参数**：某些提供商支持不同的方法（`'json_schema'`、`'function_calling'`、`'json_mode'`）
>     *   `'json_schema'` 通常指提供商提供的专用结构化输出功能
>     *   `'function_calling'` 通过强制[工具调用](models.html#%E5%B7%A5%E5%85%B7%E8%B0%83%E7%94%A8)遵循给定架构来派生结构化输出
>     *   `'json_mode'` 是某些提供商提供的 `'json_schema'` 的前身——它生成有效的 JSON，但架构必须在提示中描述
> *   **包含原始**：使用 `include_raw=True` 以同时获取已解析的输出和原始 AI 消息
> *   **验证**：Pydantic 模型提供自动验证，而 `TypedDict` 和 JSON Schema 需要手动验证

#### 示例：消息输出与解析结构并存

返回原始 [`AIMessage`](https://reference.langchain.com/python/langchain/messages/#langchain.messages.AIMessage) 对象与解析表示一起以访问响应元数据（如[令牌计数](models.html#%E4%BB%A4%E7%89%8C%E4%BD%BF%E7%94%A8%E6%83%85%E5%86%B5)）可能很有用。为此，在调用 [`with_structured_output`](https://reference.langchain.com/python/langchain_core/language_models/#langchain_core.language_models.chat_models.BaseChatModel.with_structured_output) 时设置 [`include_raw=True`](https://reference.langchain.com/python/langchain_core/language_models/#langchain_core.language_models.chat_models.BaseChatModel.with_structured_output(include_raw))：

```python
from pydantic import BaseModel, Field
class Movie(BaseModel):
    """一部带有详细信息的电影。"""
    title: str = Field(..., description="电影标题")
    year: int = Field(..., description="电影上映年份")
    director: str = Field(..., description="电影导演")
    rating: float = Field(..., description="电影评分，满分 10 分")
model_with_structure = model.with_structured_output(Movie, include_raw=True)  # [!code highlight]
response = model_with_structure.invoke("提供关于电影《盗梦空间》的详细信息")
response
# {
#     "raw": AIMessage(...),
#     "parsed": Movie(title=..., year=..., ...),
#     "parsing_error": None,
# }
```

#### 示例：嵌套结构

架构可以嵌套：

```python
from pydantic import BaseModel, Field
class Actor(BaseModel):
    name: str
    role: str
class MovieDetails(BaseModel):
    title: str
    year: int
    cast: list[Actor]
    genres: list[str]
    budget: float | None = Field(None, description="预算（百万美元）")
model_with_structure = model.with_structured_output(MovieDetails)
```

```python
from typing_extensions import Annotated, TypedDict
class Actor(TypedDict):
    name: str
    role: str
class MovieDetails(TypedDict):
    title: str
    year: int
    cast: list[Actor]
    genres: list[str]
    budget: Annotated[float | None, ..., "预算（百万美元）"]
model_with_structure = model.with_structured_output(MovieDetails)
```

---

## 支持的模型

LangChain 支持所有主要模型提供商，包括 OpenAI、Anthropic、Google、Azure、AWS Bedrock 等。每个提供商提供具有不同功能的各种模型。有关 LangChain 中支持的模型完整列表，请参阅[集成页面](../integrations/providers/overview.html)。

---

## 高级主题

### 多模态

某些模型可以处理和返回非文本数据，如图像、音频和视频。您可以通过提供[内容块](messages.html#message-content)将非文本数据传递给模型。

> **提示**
> 所有具有底层多模态功能的 LangChain 聊天模型都支持：
>
> 1.  跨提供商标准格式的数据（请参阅[我们的消息指南](messages.html)）
> 2.  OpenAI [聊天完成](https://platform.openai.com/docs/api-reference/chat)格式
> 3.  特定于该提供商的任何格式（例如，Anthropic 模型接受 Anthropic 原生格式）

有关详细信息，请参阅消息指南的[多模态部分](messages.html#multimodal)。

> **提示**
> 并非所有 LLM 都是平等的！
> 某些模型可以作为其响应的一部分返回多模态数据。如果调用它们这样做，则生成的 [`AIMessage`](https://reference.langchain.com/python/langchain/messages/#langchain.messages.AIMessage) 将具有多模态类型的内容块。

```python
response = model.invoke("创建一张猫的图片")
print(response.content_blocks)
# [
#     {"type": "text", "text": "这是一张猫的图片"},
#     {"type": "image", "base64": "...", "mime_type": "image/jpeg"},
# ]
```

有关特定提供商的详细信息，请参阅[集成页面](../integrations/providers/overview.html)。

### 推理

较新的模型能够执行多步推理以得出结论。这涉及将复杂问题分解为更小、更易管理的步骤。

**如果底层模型支持**，您可以显示此推理过程以更好地理解模型如何得出其最终答案。

```python
for chunk in model.stream("为什么鹦鹉有五颜六色的羽毛？"):
    reasoning_steps = [r for r in chunk.content_blocks if r["type"] == "reasoning"]
    print(reasoning_steps if reasoning_steps else chunk.text)
```

```python
response = model.invoke("为什么鹦鹉有五颜六色的羽毛？")
reasoning_steps = [b for b in response.content_blocks if b["type"] == "reasoning"]
print(" ".join(step["reasoning"] for step in reasoning_steps))
```

根据模型，您有时可以指定它应投入推理的努力程度。同样，您可以请求模型完全关闭推理。这可能采用“层级”（例如 `'low'` 或 `'high'`）或整数令牌预算的形式。

有关详细信息，请参阅[集成页面](../integrations/providers/overview.html)或您相应聊天模型的[参考](https://reference.langchain.com/python/integrations/)。

### 本地模型

LangChain 支持在您自己的硬件上本地运行模型。这对于数据隐私至关重要、您想调用自定义模型或希望避免使用基于云的模型所产生的成本的场景非常有用。

[Ollama](https://langchain-doc.cn/v1/python/integrations/chat/ollama) 是本地运行模型的最简单方法之一。请参阅[集成页面](../integrations/providers/overview.html)上的本地集成完整列表。

### 提示缓存

许多提供商提供提示缓存功能，以减少对相同令牌重复处理的延迟和成本。这些功能可以是**隐式**或**显式**：

*   **隐式提示缓存：** 如果请求命中缓存，提供商将自动传递成本节省。示例：[OpenAI](https://langchain-doc.cn/v1/python/integrations/chat/openai) 和 [Gemini](https://langchain-doc.cn/v1/python/integrations/chat/google_generative_ai)（Gemini 2.5 及以上）。
*   **显式缓存：** 提供商允许您手动指示缓存点以获得更大控制或保证成本节省。示例：[`ChatOpenAI`](https://reference.langchain.com/python/integrations/langchain_openai/ChatOpenAI/)（通过 `prompt_cache_key`）、Anthropic 的 [`AnthropicPromptCachingMiddleware`](https://langchain-doc.cn/v1/python/integrations/chat/anthropic#prompt-caching) 和 [`cache_control`](https://docs.langchain.com/v1/python/integrations/chat/anthropic#prom