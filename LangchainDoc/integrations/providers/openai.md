# OpenAI

与[OpenAI](https://en.wikipedia.org/wiki/OpenAI)的所有LangChain集成

## 安装和设置

```bash
pip install langchain-openai
```

```bash
uv add langchain-openai
```

获取[OpenAI Platform](https://platform.openai.com/docs/overview) API密钥并将其设置为环境变量`OPENAI_API_KEY`。

## 模型接口

*   [ChatOpenAI](https://langchain-doc.cn/v1/python/integrations/chat/openai): OpenAI 聊天模型。
*   [AzureChatOpenAI](https://langchain-doc.cn/v1/python/integrations/chat/azure_chat_openai): 托管在 Azure 上的 OpenAI 聊天模型的包装器。
*   [OpenAI](https://langchain-doc.cn/v1/python/integrations/llms/openai): (传统) OpenAI 文本补全模型。
*   [AzureOpenAI](https://langchain-doc.cn/v1/python/integrations/llms/azure_openai): 托管在 Azure 上的 (传统) OpenAI 文本补全模型的包装器。
*   [OpenAIEmbeddings](https://langchain-doc.cn/v1/python/integrations/text_embedding/openai): OpenAI 嵌入模型。
*   [AzureOpenAIEmbeddings](https://langchain-doc.cn/v1/python/integrations/text_embedding/azure_openai.mdx): 托管在 Azure 上的 OpenAI 嵌入模型的包装器。

## 工具和工具包

*   [Dall-E Image Generator](https://langchain-doc.cn/v1/python/integrations/tools/dalle_image_generator): 使用 OpenAI 的 Dall-E 模型进行文本到图像的生成。

## 检索器

*   [ChatGPTPluginRetriever](https://langchain-doc.cn/v1/python/integrations/retrievers/chatgpt-plugin): 检索实时信息；例如，体育比分、股票价格、最新新闻等。

## 文档加载器

*   [ChatGPTLoader](https://langchain-doc.cn/v1/python/integrations/document_loaders/chatgpt_loader): 从您的 ChatGPT 数据导出文件夹中加载 `conversations.json`。

## 其他

*   [Adapter](https://langchain-doc.cn/v1/python/integrations/adapters/openai): 使 LangChain 模型适应 OpenAI API。
*   [OpenAIModerationChain](https://python.langchain.com/v0.1/docs/guides/productionization/safety/moderation): 检测可能包含仇恨、暴力等内容的文本。