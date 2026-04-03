# 亚马逊 (AWS)

> [亚马逊云科技 (AWS)](https://aws.amazon.com/) 是全球最全面、应用最广泛的云，从全球数据中心提供超过 200 项功能齐全的服务。

本页面介绍了与亚马逊 AWS 的集成。

## 模型接口

### 聊天模型

- [Bedrock Chat](https://langchain-doc.cn/docs/integrations/chat/bedrock): 通过 API 使用来自亚马逊和第三方模型提供商（如 AI21 Labs、Anthropic、Cohere、Meta、Mistral AI 和 Stability AI）的基础模型构建聊天应用程序。
- [Bedrock Converse](https://langchain-doc.cn/docs/integrations/chat/bedrock_converse): 通过 API 使用来自亚马逊和第三方模型提供商（如 AI21 Labs、Anthropic、Cohere、Meta、Mistral AI 和 Stability AI）的基础模型构建聊天应用程序。

### LLM

- [Bedrock](https://langchain-doc.cn/docs/integrations/llms/bedrock): 通过 API 使用来自亚马逊和第三方模型提供商（如 AI21 Labs、Anthropic、Cohere、Meta 和 Stability AI）的基础模型构建应用程序。
- [Amazon API Gateway](https://langchain-doc.cn/docs/integrations/llms/amazon_api_gateway): 在任何规模下创建、发布、维护、监控和保护 API。
- [SageMaker Endpoint](https://langchain-doc.cn/docs/integrations/llms/sagemaker_endpoint): 使用完全托管的基础设施、工具和工作流，为任何用例构建、训练和部署机器学习 (ML) 模型。

### 嵌入模型

- [Bedrock](https://langchain-doc.cn/docs/integrations/text_embedding/bedrock): 使用来自亚马逊和第三方模型提供商（如 Cohere 和 Mistral AI）的基础模型生成文本嵌入。
- [SageMaker Endpoint](https://langchain-doc.cn/docs/integrations/text_embedding/sagemaker_endpoint): 使用完全托管的基础设施、工具和工作流，为任何用例构建、训练和部署机器学习 (ML) 模型。

## 文档加载器

- [AWS S3](https://langchain-doc.cn/docs/integrations/document_loaders/aws_s3): 从 AWS S3 加载文档。
- [Amazon Textract](https://langchain-doc.cn/docs/integrations/document_loaders/amazon_textract): 从扫描的文档中自动提取文本、手写和数据。
- [Amazon Athena](https://langchain-doc.cn/docs/integrations/document_loaders/amazon_athena): 使用标准 SQL 运行交互式查询。
- [AWS Glue](https://langchain-doc.cn/docs/integrations/document_loaders/aws_glue): 一种无服务器数据集成服务，可以轻松发现、准备和组合数据，用于分析、机器学习和应用程序开发。

## 向量存储

- [Amazon OpenSearch Service](https://langchain-doc.cn/docs/integrations/vectorstores/opensearch): 一种托管服务，可以轻松在 AWS 云中部署、操作和扩展 OpenSearch 集群。
- [Amazon DocumentDB Vector Search](https://langchain-doc.cn/docs/integrations/vectorstores/amazon_documentdb): 一种可扩展、高度耐用且完全托管的数据库服务，用于运行任务关键型 JSON 工作负载。
- [Amazon MemoryDB](https://langchain-doc.cn/docs/integrations/vectorstores/amazon_memorydb): 一种与 Redis 兼容、持久的内存数据库服务，可实现超快性能。

## 检索器

- [Amazon Kendra](https://langchain-doc.cn/docs/integrations/retrievers/amazon_kendra): 一种由机器学习提供支持的智能搜索服务。
- [Amazon Bedrock Knowledge Bases](https://langchain-doc.cn/docs/integrations/retrievers/bedrock): 构建使用您公司私有数据源的相关且准确的生成式 AI 应用程序。

## 工具

- [AWS Lambda](https://langchain-doc.cn/docs/integrations/tools/aws_lambda): 一种无服务器、事件驱动的计算服务，让您无需预置或管理服务器即可为几乎任何类型的应用程序或后端服务运行代码。

## 图

- [Amazon Neptune with Cypher](https://langchain-doc.cn/docs/integrations/graphs/neptune_cypher): 一种快速、可靠、完全托管的图数据库服务，可以轻松构建和运行处理高度连接数据集的应用程序。
- [Amazon Neptune with SPARQL](https://langchain-doc.cn/docs/integrations/graphs/neptune_sparql): 一种快速、可靠、完全托管的图数据库服务，可以轻松构建和运行处理高度连接数据集的应用程序。

## 回调

- [Bedrock token usage](https://langchain-doc.cn/docs/integrations/callbacks/bedrock): 跟踪 Bedrock 模型的分词使用情况。
- [SageMaker Tracking](https://langchain-doc.cn/docs/integrations/callbacks/sagemaker_tracking): 跟踪您的 SageMaker 机器学习实验。
- [Amazon Comprehend Moderation Chain](https://langchain-doc.cn/docs/integrations/callbacks/amazon_comprehend_moderation): 一个预构建的链，使用 Amazon Comprehend 来审核其他链的输入和输出。