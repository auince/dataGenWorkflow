# Microsoft

LangChain 与 [Microsoft Azure](https://portal.azure.com) 以及其他 [Microsoft](https://www.microsoft.com) 产品的全部集成。

## 聊天模型（Chat Models）

Microsoft 提供三种主要方式来通过 Azure 访问聊天模型：

1. [Azure OpenAI](https://learn.microsoft.com/en-us/azure/ai-services/openai/)
   提供访问 OpenAI 的强大模型（如 o3、4.1 等），并通过 Microsoft Azure 的企业安全平台运行。

2. [Azure AI](https://learn.microsoft.com/en-us/azure/ai-studio/how-to/deploy-models)
   可通过统一 API 访问来自不同提供商（如 Anthropic、DeepSeek、Cohere、Phi、Mistral）的多种模型。

3. [Azure ML](https://learn.microsoft.com/en-us/azure/machine-learning/)
   支持通过 Azure 机器学习部署和管理自定义模型或微调的开源模型。

### Azure OpenAI

> [Microsoft Azure](https://en.wikipedia.org/wiki/Microsoft_Azure)，简称 `Azure`，是由 Microsoft 运营的云计算平台，可通过全球数据中心提供应用和服务的访问、管理和开发。
> 它提供 SaaS（软件即服务）、PaaS（平台即服务）和 IaaS（基础设施即服务）等多种能力，并支持多种编程语言、工具和框架（包括 Microsoft 自家和第三方软件系统）。

> [Azure OpenAI](https://learn.microsoft.com/en-us/azure/cognitive-services/openai/) 是一个集成 OpenAI 模型（包括 `GPT-3`、`Codex` 和 Embeddings 模型系列）的 Azure 服务，可用于内容生成、摘要、语义搜索和自然语言代码转换。

```bash
pip install langchain-openai
```

或：

```bash
uv add langchain-openai
```

设置环境变量以访问 `Azure OpenAI` 服务：

```python
import os
os.environ["AZURE_OPENAI_ENDPOINT"] = "https://<your-endpoint>.openai.azure.com/"
os.environ["AZURE_OPENAI_API_KEY"] = "your AzureOpenAI key"
```

参见 [使用示例](https://langchain-doc.cn/v1/python/integrations/chat/azure_chat_openai)：

```python
from langchain_openai import AzureChatOpenAI
```

### Azure AI

> [Azure AI Foundry](https://learn.microsoft.com/en-us/azure/developer/python/get-started)
> 提供来自 Azure OpenAI、DeepSeek R1、Cohere、Phi 和 Mistral 等提供商的多种模型，可通过 `AzureAIChatCompletionsModel` 类访问。

```bash
pip install -U langchain-azure-ai
```

或：

```bash
uv add langchain-azure-ai
```

配置你的 API Key 和 Endpoint：

```bash
export AZURE_AI_CREDENTIAL=your-api-key
export AZURE_AI_ENDPOINT=your-endpoint
```

```python
from langchain_azure_ai.chat_models import AzureAIChatCompletionsModel
llm = AzureAIChatCompletionsModel(
    model_name="gpt-4o",
    api_version="2024-05-01-preview",
)
```

参见 [使用示例](https://langchain-doc.cn/v1/python/integrations/chat/azure_ai)

### Azure ML 聊天端点

可参见 [文档](https://langchain-doc.cn/v1/python/integrations/chat/azureml_chat_endpoint)，了解如何访问托管在 [Azure Machine Learning](https://azure.microsoft.com/en-us/products/machine-learning/) 上的聊天模型。

## 大语言模型（LLMs）

### Azure ML

参见 [使用示例](https://langchain-doc.cn/v1/python/integrations/llms/azure_ml)。

```python
from langchain_community.llms.azureml_endpoint import AzureMLOnlineEndpoint
```

### Azure OpenAI

参见 [使用示例](https://langchain-doc.cn/v1/python/integrations/llms/azure_openai)。

```python
from langchain_openai import AzureOpenAI
```

## 向量嵌入模型（Embedding Models）

Microsoft 提供两种主要方式通过 Azure 访问嵌入模型：

### Azure OpenAI

参见 [使用示例](https://langchain-doc.cn/v1/python/integrations/text_embedding/azure_openai)

```python
from langchain_openai import AzureOpenAIEmbeddings
```

### Azure AI

```bash
pip install -U langchain-azure-ai
```

或：

```bash
uv add langchain-azure-ai
```

配置环境变量：

```bash
export AZURE_AI_CREDENTIAL=your-api-key
export AZURE_AI_ENDPOINT=your-endpoint
```

```python
from langchain_azure_ai.embeddings import AzureAIEmbeddingsModel
embed_model = AzureAIEmbeddingsModel(
    model_name="text-embedding-ada-002"
)
```

## 文档加载器（Document Loaders）

### Azure AI Data

> [Azure AI Foundry](https://ai.azure.com/)（原 Azure AI Studio）
> 支持将数据资产上传到云存储，并注册以下来源的数据：
> *   Microsoft OneLake
> *   Azure Blob Storage
> *   Azure Data Lake gen 2

安装必要的 Python 包：

```bash
pip install azureml-fsspec azure-ai-generative
```

或：

```bash
uv add azureml-fsspec azure-ai-generative
```

参见 [使用示例](https://langchain-doc.cn/v1/python/integrations/document_loaders/azure_ai_data)。

```python
from langchain.document_loaders import AzureAIDataLoader
```

### Azure AI Document Intelligence

> [Azure AI Document Intelligence](https://aka.ms/doc-intelligence)（原名 `Azure Form Recognizer`）
> 是一项基于机器学习的服务，可从数字或扫描的 PDF、图片、Office 文件和 HTML 文件中提取文本（包括手写体）、表格、文档结构以及键值对等内容。
>
> Document Intelligence 支持以下格式：`PDF`、`JPEG/JPG`、`PNG`、`BMP`、`TIFF`、`HEIF`、`DOCX`、`XLSX`、`PPTX` 和 `HTML`。

首先，你需要安装对应的 Python 包。

```bash
pip install azure-ai-documentintelligence
```

或：

```bash
uv add azure-ai-documentintelligence
```

查看 [使用示例](https://langchain-doc.cn/v1/python/integrations/document_loaders/azure_document_intelligence)。

```python
from langchain.document_loaders import AzureAIDocumentIntelligenceLoader
```

### Azure Blob Storage

> [Azure Blob Storage](https://learn.microsoft.com/en-us/azure/storage/blobs/storage-blobs-introduction)
> 是 Microsoft 提供的云端对象存储解决方案。
> Blob Storage 专为存储海量的**非结构化数据**而优化，所谓非结构化数据，是指不符合特定数据模型或定义的数据，如文本或二进制数据。

`Azure Blob Storage` 的典型用途包括：

*   直接向浏览器提供图片或文档。
*   存储供分布式访问的文件。
*   流式传输音频和视频。
*   写入日志文件。
*   存储用于备份、恢复、灾难恢复和归档的数据。
*   存储供本地或 Azure 托管服务进行分析的数据。

```bash
pip install langchain-azure-storage
```

或：

```bash
uv add langchain-azure-storage
```

查看 [Azure Blob Storage Loader 使用示例](https://langchain-doc.cn/v1/python/integrations/document_loaders/azure_blob_storage)。

```python
from langchain_azure_storage.document_loaders import AzureBlobStorageLoader
```

### Microsoft OneDrive

> [Microsoft OneDrive](https://en.wikipedia.org/wiki/OneDrive)（原名 `SkyDrive`）
> 是由 Microsoft 运营的文件托管服务。

首先，你需要安装对应的 Python 包。

```bash
pip install o365
```

或：

```bash
uv add o365
```

查看 [使用示例](https://langchain-doc.cn/v1/python/integrations/document_loaders/microsoft_onedrive)。

```python
from langchain_community.document_loaders import OneDriveLoader
```

### Microsoft OneDrive File

> [Microsoft OneDrive](https://en.wikipedia.org/wiki/OneDrive)（原名 `SkyDrive`）
> 是由 Microsoft 运营的文件托管服务。

首先，你需要安装对应的 Python 包。

```bash
pip install o365
```

或：

```bash
uv add o365
```

```python
from langchain_community.document_loaders import OneDriveFileLoader
```

### Microsoft Word

> [Microsoft Word](https://www.microsoft.com/en-us/microsoft-365/word)
> 是由 Microsoft 开发的文字处理软件。

查看 [使用示例](https://langchain-doc.cn/v1/python/integrations/document_loaders/microsoft_word)。

```python
from langchain_community.document_loaders import UnstructuredWordDocumentLoader
```

### Microsoft Excel

> [Microsoft Excel](https://en.wikipedia.org/wiki/Microsoft_Excel)
> 是一款由 Microsoft 为 Windows、macOS、Android、iOS 和 iPadOS 开发的电子表格软件。
> 它具备计算、绘图工具、数据透视表，以及基于 VBA（Visual Basic for Applications）的宏编程功能。
> Excel 是 Microsoft 365 办公套件的一部分。

`UnstructuredExcelLoader` 用于加载 `Microsoft Excel` 文件，支持 `.xlsx` 和 `.xls` 格式。
页面内容会是 Excel 文件的原始文本。
如果使用 `"elements"` 模式，文档元数据中 `text_as_html` 键下会包含 Excel 文件的 HTML 表示形式。

查看 [使用示例](https://langchain-doc.cn/v1/python/integrations/document_loaders/microsoft_excel)。

```python
from langchain_community.document_loaders import UnstructuredExcelLoader
```

### Microsoft SharePoint

> [Microsoft SharePoint](https://en.wikipedia.org/wiki/SharePoint)
> 是一个基于网站的协作系统，使用工作流应用、“列表”数据库以及其他网页组件和安全特性，帮助企业团队高效协作。
> 该平台由 Microsoft 开发。

查看 [使用示例](https://langchain-doc.cn/v1/python/integrations/document_loaders/microsoft_sharepoint)。

```python
from langchain_community.document_loaders.sharepoint import SharePointLoader
```

### Microsoft PowerPoint

> [Microsoft PowerPoint](https://en.wikipedia.org/wiki/Microsoft_PowerPoint) 是由 Microsoft 开发的演示文稿程序。

查看 [使用示例](https://langchain-doc.cn/v1/python/integrations/document_loaders/microsoft_powerpoint)。

```python
from langchain_community.document_loaders import UnstructuredPowerPointLoader
```

### Microsoft OneNote

首先，安装依赖项：

```bash
pip install bs4 msal
```

或：

```bash
uv add bs4 msal
```

查看 [使用示例](https://langchain-doc.cn/v1/python/integrations/document_loaders/microsoft_onenote)。

```python
from langchain_community.document_loaders.onenote import OneNoteLoader
```

### Playwright URL Loader

> [Playwright](https://github.com/microsoft/playwright) 是由 `Microsoft` 开发的开源自动化工具，
> 可用于以编程方式控制和自动化网页浏览器。
> 它专为端到端测试、网页抓取以及跨浏览器自动化任务设计，支持 `Chromium`、`Firefox` 和 `WebKit` 等浏览器。

首先，安装依赖项：

```bash
pip install playwright unstructured
```

或：

```bash
uv add playwright unstructured
```

查看 [使用示例](https://langchain-doc.cn/v1/python/integrations/document_loaders/url/#playwright-url-loader)。

```python
from langchain_community.document_loaders.onenote import OneNoteLoader
```

## 向量存储（Vector Stores）

### Azure Cosmos DB

AI 代理可以将 Azure Cosmos DB 作为统一的[记忆系统](https://learn.microsoft.com/en-us/azure/cosmos-db/ai-agents#memory-can-make-or-break-agents)，
实现高速、可扩展且简单的存储体验。该服务成功支持了 [OpenAI 的 ChatGPT 服务](https://www.youtube.com/watch?v=6IIUtEFKJec&t)，
实现了高可靠性与低维护的动态扩展。
Azure Cosmos DB 基于原子记录序列引擎，是全球首个同时支持 [NoSQL](https://learn.microsoft.com/en-us/azure/cosmos-db/distributed-nosql)、[关系型](https://learn.microsoft.com/en-us/azure/cosmos-db/distributed-relational) 和 [向量数据库](https://learn.microsoft.com/en-us/azure/cosmos-db/vector-database) 的全球分布式数据库服务，并提供无服务器模式。

以下是两种可用于向量存储的 Azure Cosmos DB API。

#### Azure Cosmos DB for MongoDB (vCore)

> [Azure Cosmos DB for MongoDB vCore](https://learn.microsoft.com/en-us/azure/cosmos-db/mongodb/vcore/)
> 使您能够轻松创建具有原生 MongoDB 支持的数据库。
> 您可以使用熟悉的 MongoDB 驱动、SDK 和工具，通过连接字符串直接访问该服务。
> 通过在 Azure Cosmos DB for MongoDB vCore 中使用向量搜索，
> 您可以无缝地将 AI 应用与 Cosmos DB 中的数据集成。

##### 安装与设置

查看 [详细配置说明](https://langchain-doc.cn/v1/python/integrations/vectorstores/azure_cosmos_db_mongo_vcore)。

安装 `pymongo` Python 包：

```bash
pip install pymongo
```

或：

```bash
uv add pymongo
```

##### 在 Microsoft Azure 上部署 Azure Cosmos DB

Azure Cosmos DB for MongoDB vCore 提供完全托管的、与 MongoDB 兼容的数据库服务，
帮助开发者构建现代化应用。
它支持原生 Azure 集成、低 TCO（总体拥有成本）以及熟悉的 vCore 架构，
便于迁移或构建新应用。

[免费注册](https://azure.microsoft.com/en-us/free/) 以立即开始使用。

查看 [使用示例](https://langchain-doc.cn/v1/python/integrations/vectorstores/azure_cosmos_db_mongo_vcore)。

```python
from langchain_community.vectorstores import AzureCosmosDBVectorSearch
```

#### Azure Cosmos DB NoSQL

> [Azure Cosmos DB for NoSQL](https://learn.microsoft.com/en-us/azure/cosmos-db/nosql/vector-search)
> 现已支持向量索引与搜索（预览版）。
> 此功能可处理高维向量，实现任意规模下的高效向量搜索。
> 现在可以将向量与数据一起直接存储在文档中，
> 每个文档既可包含传统的无模式数据，也可包含高维向量。
> 这种数据与向量共存的方式使索引与搜索更高效，
> 同时简化了 AI 应用架构与数据管理。

##### 安装与设置

查看 [详细配置说明](https://langchain-doc.cn/v1/python/integrations/vectorstores/azure_cosmos_db_no_sql)。

安装 `azure-cosmos` Python 包：

```bash
pip install azure-cosmos
```

或：

```bash
uv add azure-cosmos
```

##### 在 Microsoft Azure 上部署 Azure Cosmos DB

Azure Cosmos DB 为现代应用与智能工作负载提供了高响应性和弹性扩展能力。
它可在所有 Azure 区域中使用，并可自动将数据复制到更接近用户的区域，
具备 SLA 级别的低延迟与高可用性。

[免费注册](https://learn.microsoft.com/en-us/azure/cosmos-db/nosql/quickstart-python?pivots=devcontainer-codespace) 以开始使用。

查看 [使用示例](https://langchain-doc.cn/v1/python/integrations/vectorstores/azure_cosmos_db_no_sql)。

```python
from langchain_community.vectorstores import AzureCosmosDBNoSQLVectorSearch
```

### Azure Database for PostgreSQL

> [Azure Database for PostgreSQL - Flexible Server](https://learn.microsoft.com/en-us/azure/postgresql/flexible-server/service-overview)
> 是基于开源 Postgres 数据库引擎的关系型数据库服务。
> 它是一种完全托管的数据库即服务（DBaaS），能够在高安全性、高可用性和可预测性能下运行关键业务负载。

查看 [设置说明](https://learn.microsoft.com/en-us/azure/postgresql/flexible-server/quickstart-create-server-portal)。

直接使用来自 Azure Portal 的 [连接字符串](https://learn.microsoft.com/en-us/azure/postgresql/flexible-server/connect-python?tabs=cmd%2Cpassword#add-authentication-code)。

Azure Database for PostgreSQL 基于开源 Postgres，
可通过 [LangChain 的 Postgres 集成](https://langchain-doc.cn/v1/python/integrations/vectorstores/pgvector/) 进行连接。

### Azure SQL Database

> [Azure SQL Database](https://learn.microsoft.com/azure/azure-sql/database/sql-database-paas-overview?view=azuresql)
> 是一个具有可扩展性、安全性和高可用性的数据库服务。
> 它支持专用的向量数据类型与内置函数，可直接在关系数据库中存储与查询向量嵌入，
> 无需单独的向量数据库，从而提升安全性并降低复杂度。

利用现有 SQL Server 数据库执行向量搜索，可提升数据能力、减少迁移成本并避免系统切换风险。

##### 安装与设置

查看 [详细配置说明](https://langchain-doc.cn/v1/python/integrations/vectorstores/sqlserver)。

安装 `langchain-sqlserver` Python 包：

```bash
!pip install langchain-sqlserver==0.1.1
```

##### 在 Microsoft Azure 上部署 Azure SQL DB

[免费注册](https://learn.microsoft.com/azure/azure-sql/database/free-offer?view=azuresql) 以立即开始使用。

查看 [使用示例](https://langchain-doc.cn/v1/python/integrations/vectorstores/sqlserver)。

```python
from langchain_sqlserver import SQLServer_VectorStore
```

### Azure AI Search

[Azure AI Search](https://learn.microsoft.com/azure/search/search-what-is-azure-search)
是一项云端搜索服务，
为开发者提供基础设施、API 和工具，用于在大规模下执行向量、关键词或混合查询。
查看 [使用示例](https://langchain-doc.cn/v1/python/integrations/vectorstores/azuresearch)。

```python
from langchain_community.vectorstores.azuresearch import AzureSearch
```

### Azure 认知服务（Azure Cognitive Services）

我们需要安装以下几个 Python 包：

```bash
pip install azure-ai-formrecognizer azure-cognitiveservices-speech azure-ai-vision-imageanalysis
```

或使用：

```bash
uv add azure-ai-formrecognizer azure-cognitiveservices-speech azure-ai-vision-imageanalysis
```

查看[使用示例](https://langchain-doc.cn/v1/python/integrations/tools/azure_cognitive_services)。

```python
from langchain_community.agent_toolkits import AzureCognitiveServicesToolkit
```

#### Azure AI 服务独立工具

`azure_ai_services` 工具包包含以下可以调用 `Azure Cognitive Services` 的工具：

*   `AzureCogsFormRecognizerTool`：表单识别 API
*   `AzureCogsImageAnalysisTool`：图像分析 API
*   `AzureCogsSpeech2TextTool`：语音转文字 API
*   `AzureCogsText2SpeechTool`：文字转语音 API
*   `AzureCogsTextAnalyticsHealthTool`：健康文本分析 API

```python
from langchain_community.tools.azure_cognitive_services import (
    AzureCogsFormRecognizerTool,
    AzureCogsImageAnalysisTool,
    AzureCogsSpeech2TextTool,
    AzureCogsText2SpeechTool,
    AzureCogsTextAnalyticsHealthTool,
)
```

### Microsoft Office 365 邮件与日历

我们需要安装 `O365` Python 包：

```bash
pip install O365
```

或使用：

```bash
uv add O365
```

查看[使用示例](https://langchain-doc.cn/v1/python/integrations/tools/office365)。

```python
from langchain_community.agent_toolkits import O365Toolkit
```

#### Office 365 独立工具

你可以使用来自 Office 365 工具包的单独工具：

*   `O365CreateDraftMessage`：创建邮件草稿
*   `O365SearchEmails`：搜索邮件
*   `O365SearchEvents`：搜索日历事件
*   `O365SendEvent`：发送日历事件
*   `O365SendMessage`：发送电子邮件

```python
from langchain_community.tools.office365 import O365CreateDraftMessage
from langchain_community.tools.office365 import O365SearchEmails
from langchain_community.tools.office365 import O365SearchEvents
from langchain_community.tools.office365 import O365SendEvent
from langchain_community.tools.office365 import O365SendMessage
```

### Microsoft Azure PowerBI

我们需要安装 `azure-identity` Python 包：

```bash
pip install azure-identity
```

或使用：

```bash
uv add azure-identity
```

查看[使用示例](https://langchain-doc.cn/v1/python/integrations/tools/powerbi)。

```python
from langchain_community.agent_toolkits import PowerBIToolkit
from langchain_community.utilities.powerbi import PowerBIDataset
```

#### PowerBI 独立工具

你可以使用来自 Azure PowerBI 工具包的单独工具：

*   `InfoPowerBITool`：获取 PowerBI 数据集的元数据
*   `ListPowerBITool`：获取表名
*   `QueryPowerBITool`：查询 PowerBI 数据集

```python
from langchain_community.tools.powerbi.tool import InfoPowerBITool
from langchain_community.tools.powerbi.tool import ListPowerBITool
from langchain_community.tools.powerbi.tool import QueryPowerBITool
```

### PlayWright 浏览器工具包

[Playwright](https://github.com/microsoft/playwright) 是由微软开发的开源自动化工具，
允许你通过代码控制和自动化网页浏览器。它被设计用于端到端测试、网页抓取和跨浏览器自动化任务，
支持 `Chromium`、`Firefox` 和 `WebKit` 等浏览器。

我们需要安装以下 Python 包：

```bash
pip install playwright lxml
```

或使用：

```bash
uv add playwright lxml
```

查看[使用示例](https://langchain-doc.cn/v1/python/integrations/tools/playwright)。

```python
from langchain_community.agent_toolkits import PlayWrightBrowserToolkit
```

#### PlayWright 浏览器独立工具

你可以使用来自 PlayWright 浏览器工具包的单独工具：

```python
from langchain_community.tools.playwright import ClickTool
from langchain_community.tools.playwright import CurrentWebPageTool
from langchain_community.tools.playwright import ExtractHyperlinksTool
from langchain_community.tools.playwright import ExtractTextTool
from langchain_community.tools.playwright import GetElementsTool
from langchain_community.tools.playwright import NavigateTool
from langchain_community.tools.playwright import NavigateBackTool
```

## 图数据库（Graphs）

### Azure Cosmos DB for Apache Gremlin

我们需要安装一个 Python 包：

```bash
pip install gremlinpython
```

或使用：

```bash
uv add gremlinpython
```

查看[使用示例](https://langchain-doc.cn/v1/python/integrations/graphs/azure_cosmosdb_gremlin)。

```python
from langchain_community.graphs import GremlinGraph
from langchain_community.graphs.graph_document import GraphDocument, Node, Relationship
```

## 实用工具（Utilities）

### Bing 搜索 API

[Microsoft Bing](https://www.bing.com/)，简称 `Bing` 或 `Bing Search`，
是微软拥有并运营的网页搜索引擎。

查看[使用示例](https://langchain-doc.cn/v1/python/integrations/tools/bing_search)。

```python
from langchain_community.utilities import BingSearchAPIWrapper
```

## 其他（More）

### Microsoft Presidio

[Presidio](https://microsoft.github.io/presidio/)（来源于拉丁语 praesidium，意为“保护”）
是一款用于确保敏感数据得到妥善管理和治理的工具。
它提供了快速的识别和匿名化模块，用于检测和隐藏文本或图像中的私密信息，
如信用卡号、姓名、地址、社会保障号、比特币钱包、电话号码、财务数据等。

首先，你需要安装以下 Python 包并下载 `SpaCy` 模型：

```bash
pip install langchain-experimental openai presidio-analyzer presidio-anonymizer spacy Faker
python -m spacy download en_core_web_lg
```

或使用：

```bash
uv add langchain-experimental openai presidio-analyzer presidio-anonymizer spacy Faker
python -m spacy download en_core_web_lg
```

查看[使用示例](https://python.langchain.com/v0.1/docs/guides/productionization/safety/presidio_data_anonymization)。

```python
from langchain_experimental.data_anonymizer import PresidioAnonymizer, PresidioReversibleAnonymizer