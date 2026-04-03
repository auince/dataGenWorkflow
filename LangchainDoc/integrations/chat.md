# 聊天模型（Chat models）

[聊天模型](../langchain/models.html) 是使用一系列 [消息](../langchain/messages.html) 作为输入，并返回消息作为输出的语言模型。
与传统的 LLM（即输入字符串、输出字符串的模型）不同，聊天模型使用消息接口进行交互。

## 特色提供商

> 虽然以下所有 LangChain 类都支持所列出的高级功能，但某些功能的可用性仍取决于模型提供商或后台服务。
> 详细信息请参阅各自的提供商文档。

| 提供商 | 工具调用 | 结构化输出 | JSON 模式 | 本地运行 | 多模态 | 对应的包 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| [ChatAnthropic](https://langchain-doc.cn/v1/python/integrations/chat/anthropic) | ✅ | ✅ | ❌ | ❌ | ✅ | [langchain-anthropic](https://reference.langchain.com/python/integrations/langchain_anthropic/) |
| [ChatOpenAI](https://langchain-doc.cn/v1/python/integrations/chat/openai) | ✅ | ✅ | ✅ | ❌ | ✅ | [langchain-openai](https://reference.langchain.com/python/integrations/langchain_openai/ChatOpenAI/) |
| [AzureChatOpenAI](https://langchain-doc.cn/v1/python/integrations/chat/azure_chat_openai) | ✅ | ✅ | ✅ | ❌ | ✅ | [langchain-openai](https://reference.langchain.com/python/integrations/langchain_openai/AzureChatOpenAI/) |
| [ChatVertexAI](https://langchain-doc.cn/v1/python/integrations/chat/google_vertex_ai_palm) | ✅ | ✅ | ❌ | ❌ | ✅ | [langchain-google-vertexai](https://reference.langchain.com/python/integrations/langchain_google_vertexai/) |
| [ChatGoogleGenerativeAI](https://langchain-doc.cn/v1/python/integrations/chat/google_generative_ai) | ✅ | ✅ | ❌ | ❌ | ✅ | [langchain-google-genai](https://reference.langchain.com/python/integrations/langchain_google_genai/) |
| [ChatGroq](https://langchain-doc.cn/v1/python/integrations/chat/groq) | ✅ | ✅ | ✅ | ❌ | ❌ | [langchain-groq](https://reference.langchain.com/python/integrations/langchain_groq/) |
| [ChatBedrock](https://langchain-doc.cn/v1/python/integrations/chat/bedrock) | ✅ | ✅ | ❌ | ❌ | ❌ | [langchain-aws](https://reference.langchain.com/python/integrations/langchain_aws/) |
| [ChatHuggingFace](https://langchain-doc.cn/v1/python/integrations/chat/huggingface) | ✅ | ✅ | ❌ | ✅ | ❌ | [langchain-huggingface](https://reference.langchain.com/python/integrations/langchain_huggingface/) |
| [ChatOllama](https://langchain-doc.cn/v1/python/integrations/chat/ollama) | ✅ | ✅ | ✅ | ✅ | ❌ | [langchain-ollama](https://reference.langchain.com/python/integrations/langchain_ollama/) |
| [ChatXAI](https://langchain-doc.cn/v1/python/integrations/chat/xai) | ✅ | ✅ | ❌ | ❌ | ❌ | [langchain-xai](https://reference.langchain.com/python/integrations/langchain_xai/) |
| [ChatNVIDIA](https://langchain-doc.cn/v1/python/integrations/chat/nvidia_ai_endpoints) | ✅ | ✅ | ✅ | ✅ | ✅ | [langchain-nvidia-ai-endpoints](https://reference.langchain.com/python/integrations/langchain_nvidia_ai_endpoints/) |
| [ChatCohere](https://langchain-doc.cn/v1/python/integrations/chat/cohere) | ✅ | ✅ | ❌ | ❌ | ❌ | [langchain-cohere](https://reference.langchain.com/python/integrations/langchain_cohere/) |
| [ChatMistralAI](https://langchain-doc.cn/v1/python/integrations/chat/mistralai) | ✅ | ✅ | ❌ | ❌ | ❌ | [langchain-mistralai](https://reference.langchain.com/python/integrations/langchain_mistralai/) |
| [ChatTogether](https://langchain-doc.cn/v1/python/integrations/chat/together) | ✅ | ✅ | ✅ | ❌ | ❌ | [langchain-together](https://reference.langchain.com/python/integrations/langchain_together/) |
| [ChatFireworks](https://langchain-doc.cn/v1/python/integrations/chat/fireworks) | ✅ | ✅ | ✅ | ❌ | ❌ | [langchain-fireworks](https://reference.langchain.com/python/integrations/langchain_fireworks/) |
| [ChatLlamaCpp](https://langchain-doc.cn/v1/python/integrations/chat/llamacpp) | ✅ | ✅ | ❌ | ✅ | ❌ | [langchain-community](https://python.langchain.com/api_reference/community/chat_models/langchain_community.chat_models.llamacpp.ChatLlamaCpp.html) |
| [ChatDatabricks](https://langchain-doc.cn/v1/python/integrations/chat/databricks) | ✅ | ✅ | ❌ | ❌ | ❌ | [databricks-langchain](https://api-docs.databricks.com/python/databricks-ai-bridge/latest/databricks_langchain.html#databricks_langchain.ChatDatabricks) |
| [ChatPerplexity](https://langchain-doc.cn/v1/python/integrations/chat/perplexity) | ❌ | ✅ | ✅ | ❌ | ✅ | [langchain-perplexity](https://reference.langchain.com/python/integrations/langchain_perplexity/) |

## 聊天补全 API（Chat Completions API）

一些模型提供商提供了兼容 OpenAI [Chat Completions API](https://platform.openai.com/docs/api-reference/chat) 的端点。
在这种情况下，你可以通过设置自定义 `base_url`，使用 [`ChatOpenAI`](https://langchain-doc.cn/v1/python/integrations/chat/openai) 连接这些端点。

**示例：使用 OpenRouter**

要使用 OpenRouter，你需要注册一个账户并获取 [API 密钥](https://openrouter.ai/docs/api-reference/authentication)。

```python
from langchain_openai import ChatOpenAI
model = ChatOpenAI(
    model="...",  # 指定一个在 OpenRouter 上可用的模型
    api_key="OPENROUTER_API_KEY",
    base_url="https://openrouter.ai/api/v1",
)
```

更多信息请参阅 [OpenRouter 官方文档](https://openrouter.ai/docs/quickstart)。

> **注意**：如果你希望捕获 [reasoning tokens（推理令牌）](https://openrouter.ai/docs/use-cases/reasoning-tokens)，请执行以下操作：
> 1. 将导入从 `langchain_openai` 改为 `langchain_deepseek`；
> 2. 使用 `ChatDeepSeek` 替代 `ChatOpenAI`，并将参数 `base_url` 改为 `api_base`；
> 3. 根据需要在 `extra_body` 中启用推理选项，例如：
>
> ```python
> model = ChatDeepSeek(
>     model="...",
>     api_key="...",
>     api_base="https://openrouter.ai/api/v1",
>     extra_body={"reasoning": {"enabled": True}},
> )
> ```
>
> 这是当前 `ChatOpenAI` 的已知限制，未来版本会修复。

## 所有可用聊天模型

以下列出了 LangChain 支持的所有聊天模型（点击名称可查看使用指南）：

* [Abso](https://langchain-doc.cn/v1/python/integrations/chat/abso)
* [AI21 Labs](https://langchain-doc.cn/v1/python/integrations/chat/ai21)
* [Anthropic](https://langchain-doc.cn/v1/python/integrations/chat/anthropic)
* [Azure OpenAI](https://langchain-doc.cn/v1/python/integrations/chat/azure_chat_openai)
* [Baidu Qianfan](https://langchain-doc.cn/v1/python/integrations/chat/baidu_qianfan_endpoint)
* [ChatOllama](https://langchain-doc.cn/v1/python/integrations/chat/ollama)
* [DeepSeek](https://langchain-doc.cn/v1/python/integrations/chat/deepseek)
* [Google Gemini](https://langchain-doc.cn/v1/python/integrations/chat/google_generative_ai)
* [Groq](https://langchain-doc.cn/v1/python/integrations/chat/groq)
* [Llama.cpp](https://langchain-doc.cn/v1/python/integrations/chat/llamacpp)
* [MistralAI](https://langchain-doc.cn/v1/python/integrations/chat/mistralai)
* [NVIDIA AI Endpoints](https://langchain-doc.cn/v1/python/integrations/chat/nvidia_ai_endpoints)
* [OpenAI](https://langchain-doc.cn/v1/python/integrations/chat/openai)
* [Perplexity](https://langchain-doc.cn/v1/python/integrations/chat/perplexity)
* [Together](https://langchain-doc.cn/v1/python/integrations/chat/together)
* [ZHIPU AI（智谱清言）](https://langchain-doc.cn/v1/python/integrations/chat/zhipuai)
* [Tongyi Qwen（通义千问）](https://langchain-doc.cn/v1/python/integrations/chat/tongyi)
* [Upstage](https://langchain-doc.cn/v1/python/integrations/chat/upstage)
* [vLLM Chat](https://langchain-doc.cn/v1/python/integrations/chat/vllm)
* [Volc Engine Maas（火山引擎 MaaS）](https://langchain-doc.cn/v1/python/integrations/chat/volcengine_maas)
* [ChatWriter](https://langchain-doc.cn/v1/python/integrations/chat/writer)
* [xAI](https://langchain-doc.cn/v1/python/integrations/chat/xai)
* [Xinference](https://langchain-doc.cn/v1/python/integrations/chat/xinference)
* [YandexGPT](https://langchain-doc.cn/v1/python/integrations/chat/yandex)
* [ChatYI（零一万物）](https://langchain-doc.cn/v1/python/integrations/chat/yi)
* [Yuan 2.0（元语 2.0）](https://langchain-doc.cn/v1/python/integrations/chat/yuan2)
* [ZHIPU AI（智谱清言）](https://langchain-doc.cn/v1/python/integrations/chat/zhipuai)

## 贡献

如果你希望贡献一个新的模型集成，请参阅：[添加新的集成](../contributing.html#add-a-new-integration)