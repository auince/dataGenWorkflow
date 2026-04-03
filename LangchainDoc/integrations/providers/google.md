# Google

所有 LangChain 与 [Google Cloud](https://cloud.google.com/)、[Google Gemini](https://ai.google.dev/gemini-api/docs) 以及其他 Google 产品的集成。

1.  **Google Generative AI (Gemini API 与 AI Studio)**: 通过 **Gemini API** 直接访问 **Google Gemini** 模型。使用 [Google AI Studio](https://aistudio.google.com/) 进行快速原型设计并使用 `langchain-google-genai` 包快速入门。对于个人开发者来说，这通常是**最佳起点**。
2.  **Google Cloud (Vertex AI 与其他服务)**: 通过 [Google Cloud Platform](https://cloud.google.com/) 访问 Gemini 模型、**Vertex AI 模型库 (Model Garden)** 以及各种云服务（数据库、存储、文档 AI 等）。使用 `langchain-google-vertexai` 包处理 **Vertex AI** 模型，并使用特定包（例如 `langchain-google-cloud-sql-pg`、`langchain-google-community`）处理其他云服务。这对于已经使用 Google Cloud 或需要 MLOps、特定模型调优或企业支持等**企业级功能**的开发者来说是理想选择。

有关差异的更多详细信息，请参阅 Google 关于**[从 Gemini API 迁移到 Vertex AI](https://ai.google.dev/gemini-api/docs/migrate-to-cloud)** 的指南。

用于 Gemini 模型和 Vertex AI 平台的集成包在 [`langchain-google`](https://langchain-doc.cn/v1/python/integrations/providers/%5Bhttps://github.com/langchain-ai/langchain-google%5D(https://github.com/langchain-ai/langchain-google)) 仓库中维护。您可以在 [googleapis](https://github.com/googleapis?q=langchain-&type=all&language=&sort=) Github 组织和 `langchain-google-community` 包中找到大量与其他 Google API 和服务的 LangChain 集成。

## Google Generative AI (Gemini API 与 AI Studio)

直接使用 **Gemini API** 访问 Google Gemini 模型，最适合**快速开发和实验**。Gemini 模型可在 [Google AI Studio](https://aistudio.google.com/) 中使用。

```bash
pip install -U langchain-google-genai
```

```bash
uv add langchain-google-genai
```

从 [Google AI Studio](https://aistudio.google.com/app/apikey) **免费开始**并获取您的 API 密钥。

```bash
export GOOGLE_API_KEY="YOUR_API_KEY"
```

### 聊天模型

使用 `ChatGoogleGenerativeAI` 类与 **Gemini 模型**进行交互。请参阅[本指南](https://langchain-doc.cn/v1/python/integrations/chat/google_generative_ai)中的详细信息。

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.messages import HumanMessage
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
# 简单的文本调用
result = llm.invoke("Sing a ballad of LangChain.")
print(result.content)
# 使用 gemini-pro-vision 进行多模态调用
message = HumanMessage(
    content=[
        {
            "type": "text",
            "text": "What's in this image?",
        },
        {"type": "image_url", "image_url": "https://picsum.photos/seed/picsum/200/300"},
    ]
)
result = llm.invoke([message])
print(result.content)
```

`image_url` 可以是公共 URL、GCS URI (`gs://...`)、本地文件路径、Base64 编码的图像字符串 (`data:image/png;base64,...`) 或 **PIL Image** 对象。

### 嵌入模型

使用 `GoogleGenerativeAIEmbeddings` 类生成文本嵌入，模型如 `gemini-embedding-001`。

请参阅[使用示例](https://langchain-doc.cn/v1/python/integrations/text_embedding/google_generative_ai)。

```python
from langchain_google_genai import GoogleGenerativeAIEmbeddings
embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
vector = embeddings.embed_query("What are embeddings?")
print(vector[:5])
```

### LLMs (大型语言模型)

使用 **`GoogleGenerativeAI`** 类通过（遗留的）LLM 接口访问相同的 **Gemini 模型**。

请参阅[使用示例](https://langchain-doc.cn/v1/python/integrations/llms/google_ai)。

```python
from langchain_google_genai import GoogleGenerativeAI
llm = GoogleGenerativeAI(model="gemini-2.5-flash")
result = llm.invoke("Sing a ballad of LangChain.")
print(result)
```

## Google Cloud

通过 **Vertex AI** 和特定的云集成，访问 **Gemini 模型**、Vertex AI 模型库以及其他 Google Cloud 服务。

Vertex AI 模型需要 **`langchain-google-vertexai`** 包。其他服务可能需要额外的包，如 `langchain-google-community`、`langchain-google-cloud-sql-pg` 等。

```bash
pip install langchain-google-vertexai
# pip install langchain-google-community[...] # For other services (对于其他服务)
```

```bash
uv add langchain-google-vertexai
# uv add langchain-google-community[...] # For other services (对于其他服务)
```

Google Cloud 集成通常使用**应用程序默认凭证 (Application Default Credentials, ADC)**。请参阅 [Google Cloud 身份验证文档](https://cloud.google.com/docs/authentication)以获取设置说明（例如，使用 `gcloud auth application-default login`）。

### 聊天模型

#### Vertex AI

通过 **Vertex AI 平台**访问 Gemini 等聊天模型。

请参阅[使用示例](https://langchain-doc.cn/v1/python/integrations/chat/google_vertex_ai_palm)。

```python
from langchain_google_vertexai import ChatVertexAI
```

#### Anthropic on Vertex AI Model Garden (Vertex AI 模型库上的 Anthropic)

请参阅[使用示例](https://langchain-doc.cn/v1/python/integrations/llms/google_vertex_ai_palm)。

```python
from langchain_google_vertexai.model_garden import ChatAnthropicVertex
```

#### Llama on Vertex AI Model Garden (Vertex AI 模型库上的 Llama)

```python
from langchain_google_vertexai.model_garden_maas.llama import VertexModelGardenLlama
```

#### Mistral on Vertex AI Model Garden (Vertex AI 模型库上的 Mistral)

```python
from langchain_google_vertexai.model_garden_maas.mistral import VertexModelGardenMistral
```

#### Gemma local from Hugging Face (来自 Hugging Face 的本地 Gemma)

> 从 HuggingFace 加载的本地 Gemma 模型。需要 `langchain-google-vertexai`。

```python
from langchain_google_vertexai.gemma import GemmaChatLocalHF
```

#### Gemma local from Kaggle (来自 Kaggle 的本地 Gemma)

> 从 Kaggle 加载的本地 Gemma 模型。需要 `langchain-google-vertexai`。

```python
from langchain_google_vertexai.gemma import GemmaChatLocalKaggle
```

#### Gemma on Vertex AI Model Garden (Vertex AI 模型库上的 Gemma)

> 需要 `langchain-google-vertexai`。

```python
from langchain_google_vertexai.gemma import GemmaChatVertexAIModelGarden
```

#### Vertex AI image captioning (Vertex AI 图像字幕生成)

> 图像字幕生成模型作为聊天的实现。需要 `langchain-google-vertexai`。

```python
from langchain_google_vertexai.vision_models import VertexAIImageCaptioningChat
```

#### Vertex AI image editor (Vertex AI 图像编辑器)

> 给定图像和提示，编辑图像。目前仅支持无遮罩编辑。需要 `langchain-google-vertexai`。

```python
from langchain_google_vertexai.vision_models import VertexAIImageEditorChat
```

#### Vertex AI image generator (Vertex AI 图像生成器)

> 从提示生成图像。需要 `langchain-google-vertexai`。

```python
from langchain_google_vertexai.vision_models import VertexAIImageGeneratorChat
```

#### Vertex AI visual QnA (Vertex AI 视觉问答)

> 视觉问答模型的聊天实现。需要 `langchain-google-vertexai`。

```python
from langchain_google_vertexai.vision_models import VertexAIVisualQnAChat
```

### LLMs

您还可以使用（遗留的）**字符串输入、字符串输出**的 LLM 接口。

#### Vertex AI Model Garden (Vertex AI 模型库)

通过 Vertex AI Model Garden 服务访问 **Gemini** 和数百个 **OSS 模型**。需要 `langchain-google-vertexai`。

请参阅[使用示例](https://langchain-doc.cn/v1/python/integrations/llms/google_vertex_ai_palm#vertex-model-garden)。

```python
from langchain_google_vertexai import VertexAIModelGarden
```

#### Gemma local from Hugging Face (来自 Hugging Face 的本地 Gemma)

> 从 HuggingFace 加载的本地 Gemma 模型。需要 `langchain-google-vertexai`。

```python
from langchain_google_vertexai.gemma import GemmaLocalHF
```

#### Gemma local from Kaggle (来自 Kaggle 的本地 Gemma)

> 从 Kaggle 加载的本地 Gemma 模型。需要 `langchain-google-vertexai`。

```python
from langchain_google_vertexai.gemma import GemmaLocalKaggle
```

#### Gemma on Vertex AI Model Garden (Vertex AI 模型库上的 Gemma)

> 需要 `langchain-google-vertexai`。

```python
from langchain_google_vertexai.gemma import GemmaVertexAIModelGarden
```

#### Vertex AI image captioning (Vertex AI 图像字幕生成)

> 图像字幕生成模型作为 LLM 的实现。需要 `langchain-google-vertexai`。

```python
from langchain_google_vertexai.vision_models import VertexAIImageCaptioning
```

### 嵌入模型

#### Vertex AI

使用部署在 **Vertex AI** 上的模型生成嵌入。需要 `langchain-google-vertexai`。

请参阅[使用示例](https://langchain-doc.cn/v1/python/integrations/text_embedding/google_vertex_ai_palm)。

```python
from langchain_google_vertexai import VertexAIEmbeddings
```

### 文档加载器

从各种 Google Cloud 来源加载文档。

#### AlloyDB for PostgreSQL

> [Google Cloud AlloyDB](https://cloud.google.com/alloydb) 是一个**完全托管**的 **PostgreSQL 兼容数据库**服务。

安装 Python 包：

```bash
pip install langchain-google-alloydb-pg
```

```bash
uv add langchain-google-alloydb-pg
```

请参阅[使用示例](https://langchain-doc.cn/v1/python/integrations/document_loaders/google_alloydb)。

```python
from langchain_google_alloydb_pg import AlloyDBLoader # AlloyDBEngine 也可用
```

#### BigQuery

> [Google Cloud BigQuery](https://cloud.google.com/bigquery) 是一个**无服务器数据仓库**。

使用 BigQuery 依赖项进行安装：

```bash
pip install langchain-google-community[bigquery]
```

```bash
uv add langchain-google-community[bigquery]
```

请参阅[使用示例](https://langchain-doc.cn/v1/python/integrations/document_loaders/google_bigquery)。

```python
from langchain_google_community import BigQueryLoader
```

#### Bigtable

> [Google Cloud Bigtable](https://cloud.google.com/bigtable/docs) 是一个**完全托管**的 NoSQL **大数据数据库**服务。

安装 Python 包：

```bash
pip install langchain-google-bigtable
```

```bash
uv add langchain-google-bigtable
```

请参阅[使用示例](https://langchain-doc.cn/v1/python/integrations/document_loaders/google_bigtable)。

```python
from langchain_google_bigtable import BigtableLoader
```

#### Cloud SQL for MySQL

> [Google Cloud SQL for MySQL](https://cloud.google.com/sql) 是一个**完全托管**的 **MySQL 数据库**服务。

安装 Python 包：

```bash
pip install langchain-google-cloud-sql-mysql
```

```bash
uv add langchain-google-cloud-sql-mysql
```

请参阅[使用示例](https://langchain-doc.cn/v1/python/integrations/document_loaders/google_cloud_sql_mysql)。

```python
from langchain_google_cloud_sql_mysql import MySQLLoader # MySQLEngine 也可用
```

#### Cloud SQL for SQL Server

> [Google Cloud SQL for SQL Server](https://cloud.google.com/sql) 是一个**完全托管**的 **SQL Server 数据库**服务。

安装 Python 包：

```bash
pip install langchain-google-cloud-sql-mssql
```

```bash
uv add langchain-google-cloud-sql-mssql
```

请参阅[使用示例](https://langchain-doc.cn/v1/python/integrations/document_loaders/google_cloud_sql_mssql)。

```python
from langchain_google_cloud_sql_mssql import MSSQLLoader # MSSQLEngine 也可用
```

#### Cloud SQL for PostgreSQL

> [Google Cloud SQL for PostgreSQL](https://cloud.google.com/sql) 是一个**完全托管**的 **PostgreSQL 数据库**服务。

安装 Python 包：

```bash
pip install langchain-google-cloud-sql-pg
```

```bash
uv add langchain-google-cloud-sql-pg
```

请参阅[使用示例](https://langchain-doc.cn/v1/python/integrations/document_loaders/google_cloud_sql_pg)。

```python
from langchain_google_cloud_sql_pg import PostgresLoader # PostgresEngine 也可用
```

#### Cloud Storage

> [Cloud Storage](https://en.wikipedia.org/wiki/Google_Cloud_Storage) 是一个用于存储**非结构化数据**的托管服务。

使用 GCS 依赖项进行安装：

```bash
pip install langchain-google-community[gcs]
```

```bash
uv add langchain-google-community[gcs]
```

从目录或特定文件加载：

请参阅[目录使用示例](https://langchain-doc.cn/v1/python/integrations/document_loaders/google_cloud_storage_directory)。

```python
from langchain_google_community import GCSDirectoryLoader
```

请参阅[文件使用示例](https://langchain-doc.cn/v1/python/integrations/document_loaders/google_cloud_storage_file)。

```python
from langchain_google_community import GCSFileLoader
```

#### Cloud Vision loader (Cloud Vision 加载器)

使用 **Google Cloud Vision API** 加载数据。

使用 Vision 依赖项进行安装：

```bash
pip install langchain-google-community[vision]
```

```bash
uv add langchain-google-community[vision]
```

```python
from langchain_google_community.vision import CloudVisionLoader
```

#### El Carro for Oracle Workloads (用于 Oracle 工作负载的 El Carro)

> Google [El Carro Oracle Operator](https://github.com/GoogleCloudPlatform/elcarro-oracle-operator) 在 **Kubernetes** 中运行 **Oracle 数据库**。

安装 Python 包：

```bash
pip install langchain-google-el-carro
```

```bash
uv add langchain-google-el-carro
```

请参阅[使用示例](https://langchain-doc.cn/v1/python/integrations/document_loaders/google_el_carro)。

```python
from langchain_google_el_carro import ElCarroLoader
```

#### Firestore (Native Mode) (Firestore - 原生模式)

> [Google Cloud Firestore](https://cloud.google.com/firestore/docs/) 是一个 **NoSQL 文档数据库**。

安装 Python 包：

```bash
pip install langchain-google-firestore
```

```bash
uv add langchain-google-firestore
```

请参阅[使用示例](https://langchain-doc.cn/v1/python/integrations/document_loaders/google_firestore)。

```python
from langchain_google_firestore import FirestoreLoader
```

#### Firestore (Datastore Mode) (Firestore - Datastore 模式)

> [Google Cloud Firestore in Datastore mode](https://cloud.google.com/datastore/docs)。

安装 Python 包：

```bash
pip install langchain-google-datastore
```

```bash
uv add langchain-google-datastore
```

请参阅[使用示例](https://langchain-doc.cn/v1/python/integrations/document_loaders/google_datastore)。

```python
from langchain_google_datastore import DatastoreLoader
```

#### Memorystore for Redis

> [Google Cloud Memorystore for Redis](https://cloud.google.com/memorystore/docs/redis) 是一个**完全托管**的 **Redis 服务**。

安装 Python 包：

```bash
pip install langchain-google-memorystore-redis
```

```bash
uv add langchain-google-memorystore-redis
```

请参阅[使用示例](https://langchain-doc.cn/v1/python/integrations/document_loaders/google_memorystore_redis)。

```python
from langchain_google_memorystore_redis import MemorystoreDocumentLoader
```

#### Spanner

> [Google Cloud Spanner](https://cloud.google.com/spanner/docs) 是一个**完全托管**的、**全球分布式**的**关系数据库**服务。

安装 Python 包：

```bash
pip install langchain-google-spanner
```

```bash
uv add langchain-google-spanner
```

请参阅[使用示例](https://langchain-doc.cn/v1/python/integrations/document_loaders/google_spanner)。

```python
from langchain_google_spanner import SpannerLoader
```

#### 语音转文本 (Speech-to-Text)

> [Google Cloud Speech-to-Text](https://cloud.google.com/speech-to-text) 可转录音频文件。

安装 Speech-to-Text 依赖项：

```bash
pip install langchain-google-community[speech]
```

```bash
uv add langchain-google-community[speech]
```

请参阅[使用示例和授权说明](https://langchain-doc.cn/v1/python/integrations/document_loaders/google_speech_to_text)。

```python
from langchain_google_community import SpeechToTextLoader
```

### 文档转换器 (Document Transformers)

使用 Google Cloud 服务转换文档。

#### Document AI

> [Google Cloud Document AI](https://cloud.google.com/document-ai/docs/overview) 是一项 Google Cloud 服务，可将文档中的**非结构化数据**转换为**结构化数据**，使其更易于理解、分析和使用。

我们需要设置一个 [`GCS` 存储桶并创建您自己的 OCR 处理器](https://langchain-doc.cn/v1/python/integrations/providers/%5Bhttps://cloud.google.com/document-ai/docs/create-processor%5D(https://cloud.google.com/document-ai/docs/create-processor))。
`GCS_OUTPUT_PATH` 应该是一个 GCS 上的文件夹路径（以 `gs://` 开头），
并且处理器名称应类似于 `projects/PROJECT_NUMBER/locations/LOCATION/processors/PROCESSOR_ID`。
我们可以通过编程方式获取它，或者从 Google Cloud Console 中“`Processor details`”选项卡的“`Prediction endpoint`”部分复制。

```bash
pip install langchain-google-community[docai]
```

```bash
uv add langchain-google-community[docai]
```

请参阅[使用示例](https://langchain-doc.cn/v1/python/integrations/document_transformers/google_docai)。

```python
from langchain_core.document_loaders.blob_loaders import Blob
from langchain_google_community import DocAIParser
```

#### Google Translate

> [Google Translate (谷歌翻译)](https://translate.google.com/) 是 Google 开发的多语言**神经机器翻译**服务，用于将文本、文档和网站从一种语言翻译成另一种语言。

`GoogleTranslateTransformer` 允许您使用 [Google Cloud Translation API](https://cloud.google.com/translate) 翻译文本和 HTML。

首先，我们需要安装带有翻译依赖项的 `langchain-google-community`。

```bash
pip install langchain-google-community[translate]
```

```bash
uv add langchain-google-community[translate]
```

请参阅[使用示例和授权说明](https://langchain-doc.cn/v1/python/integrations/document_transformers/google_translate)。

```python
from langchain_google_community import GoogleTranslateTransformer
```

### 向量存储 (Vector Stores)

使用 Google Cloud 数据库和 Vertex AI Vector Search 存储和搜索向量。

#### AlloyDB for PostgreSQL

> [Google Cloud AlloyDB](https://cloud.google.com/alloydb) 是一种**完全托管的关系数据库**服务，在 Google Cloud 上提供高性能、无缝集成和令人印象深刻的可扩展性。AlloyDB **100% 兼容 PostgreSQL**。

安装 Python 包：

```bash
pip install langchain-google-alloydb-pg
```

```bash
uv add langchain-google-alloydb-pg
```

请参阅[使用示例](https://langchain-doc.cn/v1/python/integrations/vectorstores/google_alloydb)。

```python
from langchain_google_alloydb_pg import AlloyDBVectorStore # AlloyDBEngine 也可用
```

#### BigQuery Vector Search

> [Google Cloud BigQuery](https://cloud.google.com/bigquery)，
> BigQuery 是 Google Cloud 中一个**无服务器**、**经济高效的企业数据仓库**。

> [Google Cloud BigQuery Vector Search](https://cloud.google.com/bigquery/docs/vector-search-intro)
> BigQuery 向量搜索允许您使用 GoogleSQL 进行**语义搜索**，使用**向量索引**实现快速但近似的结果，或使用**暴力搜索**实现精确结果。

> 它可以计算**欧几里得距离**或**余弦距离**。在 LangChain 中，我们默认使用欧几里得距离。

我们需要安装几个 Python 包。

```bash
pip install google-cloud-bigquery
```

```bash
uv add google-cloud-bigquery
```

请参阅[使用示例](https://langchain-doc.cn/v1/python/integrations/vectorstores/google_bigquery_vector_search)。

```python
# 注意：BigQueryVectorSearch 可能在 langchain 或 langchain_community 中，具体取决于版本
# 请检查使用示例中的导入。
from langchain.vectorstores import BigQueryVectorSearch # 或 langchain_community.vectorstores
```

#### Memorystore for Redis

> 使用 [Memorystore for Redis](https://cloud.google.com/memorystore/docs/redis) 的向量存储。

安装 Python 包：

```bash
pip install langchain-google-memorystore-redis
```

```bash
uv add langchain-google-memorystore-redis
```

请参阅[使用示例](https://langchain-doc.cn/v1/python/integrations/vectorstores/google_memorystore_redis)。

```python
from langchain_google_memorystore_redis import RedisVectorStore
```

#### Spanner

> 使用 [Cloud Spanner](https://cloud.google.com/spanner/docs) 的向量存储。

安装 Python 包：

```bash
pip install langchain-google-spanner
```

```bash
uv add langchain-google-spanner
```

请参阅[使用示例](https://langchain-doc.cn/v1/python/integrations/vectorstores/google_spanner)。

```python
from langchain_google_spanner import SpannerVectorStore
```

#### Firestore (Native Mode) (Firestore - 原生模式)

> 使用 [Firestore](https://cloud.google.com/firestore/docs/) 的向量存储。

安装 Python 包：

```bash
pip install langchain-google-firestore
```

```bash
uv add langchain-google-firestore
```

请参阅[使用示例](https://langchain-doc.cn/v1/python/integrations/vectorstores/google_firestore)。

```python
from langchain_google_firestore import FirestoreVectorStore
```

#### Cloud SQL for MySQL

> 使用 [Cloud SQL for MySQL](https://cloud.google.com/sql) 的向量存储。

安装 Python 包：

```bash
pip install langchain-google-cloud-sql-mysql
```

```bash
uv add langchain-google-cloud-sql-mysql
```

请参阅[使用示例](https://langchain-doc.cn/v1/python/integrations/vectorstores/google_cloud_sql_mysql)。

```python
from langchain_google_cloud_sql_mysql import MySQLVectorStore # MySQLEngine 也可用
```

#### Cloud SQL for PostgreSQL

> 使用 [Cloud SQL for PostgreSQL](https://cloud.google.com/sql) 的向量存储。

安装 Python 包：

```bash
pip install langchain-google-cloud-sql-pg
```

```bash
uv add langchain-google-cloud-sql-pg
```

请参阅[使用示例](https://langchain-doc.cn/v1/python/integrations/vectorstores/google_cloud_sql_pg)。

```python
from langchain_google_cloud_sql_pg import PostgresVectorStore # PostgresEngine 也可用
```

#### Vertex AI Vector Search

> [Google Cloud Vertex AI Vector Search](https://cloud.google.com/vertex-ai/docs/vector-search/overview) 来自 Google Cloud，
> 前身称为 `Vertex AI Matching Engine`，提供了业界领先的**高规模**、**低延迟**的**向量数据库**。这些向量数据库通常被称为向量相似性匹配或近似最近邻 (ANN) 服务。

安装 Python 包：

```bash
pip install langchain-google-vertexai
```

```bash
uv add langchain-google-vertexai
```

请参阅[使用示例](https://langchain-doc.cn/v1/python/integrations/vectorstores/google_vertex_ai_vector_search)。

```python
from langchain_google_vertexai import VectorSearchVectorStore
```

##### With DataStore Backend (使用 Datastore 后端)

> 使用 Datastore 进行文档存储的向量搜索。

请参阅[使用示例](https://langchain-doc.cn/v1/python/integrations/vectorstores/google_vertex_ai_vector_search/#optional--you-can-also-create-vectore-and-store-chunks-in-a-datastore)。

```python
from langchain_google_vertexai import VectorSearchVectorStoreDatastore
```

##### With GCS Backend (使用 GCS 后端)

> `VectorSearchVectorStore` 的别名，用于将文档/索引存储在 GCS 中。

```python
from langchain_google_vertexai import VectorSearchVectorStoreGCS
```

### 检索器 (Retrievers)

使用 Google Cloud 服务检索信息。

#### Vertex AI Search

> 使用 [Vertex AI Search](https://cloud.google.com/generative-ai-app-builder/docs/introduction) 构建由**生成式 AI 驱动的搜索引擎**。
> Google Cloud 的此服务允许开发者快速为客户和员工构建由生成式 AI 驱动的搜索引擎。

请参阅[使用示例](https://langchain-doc.cn/v1/python/integrations/retrievers/google_vertex_ai_search)。

注意：`GoogleVertexAISearchRetriever` 已弃用。请使用下方来自 `langchain-google-community` 的组件。

安装 `google-cloud-discoveryengine` 包以进行底层访问。

```bash
pip install google-cloud-discoveryengine langchain-google-community
```

```bash
uv add google-cloud-discoveryengine langchain-google-community
```

##### VertexAIMultiTurnSearchRetriever (Vertex AI 多轮搜索检索器)

```python
from langchain_google_community import VertexAIMultiTurnSearchRetriever
```

##### VertexAISearchRetriever (Vertex AI 搜索检索器)

```python
# 注意：示例代码显示的是 VertexAIMultiTurnSearchRetriever，请确认 VertexAISearchRetriever 是否单独存在或相关。
# 假设它可能相关或原文档中存在错字：
from langchain_google_community import VertexAISearchRetriever # 如有需要，请验证类名
```

##### VertexAISearchSummaryTool (Vertex AI 搜索摘要工具)

```python
from langchain_google_community import VertexAISearchSummaryTool
```

#### Document AI Warehouse

> 使用 [Document AI Warehouse](https://cloud.google.com/document-ai-warehouse) 搜索、存储和管理文档。

注意：`GoogleDocumentAIWarehouseRetriever`（来自 `langchain`）已弃用。请使用来自 `langchain-google-community` 的 `DocumentAIWarehouseRetriever`。

需要安装相关的 Document AI 包（请查阅具体文档）。

```bash
pip install langchain-google-community # 如果需要，请添加特定的 docai 依赖项
```

```bash
uv add langchain-google-community # 如果需要，请添加特定的 docai 依赖项
```

```python
from langchain_google_community.documentai_warehouse import DocumentAIWarehouseRetriever
```

### 工具 (Tools)

将智能体 (agents) 与各种 Google 服务集成。

#### Text-to-Speech (文本转语音)

> [Google Cloud Text-to-Speech](https://cloud.google.com/text-to-speech) 是一项 Google Cloud 服务，使开发者能够**合成**具有 **100 多种**语音、多种语言和变体的**自然语音**。它应用了 DeepMind 在 WaveNet 方面的突破性研究和 Google 强大的神经网络，以提供最高的保真度。

安装所需的包：

```bash
pip install google-cloud-text-to-speech langchain-google-community
```

```bash
uv add google-cloud-text-to-speech langchain-google-community
```

请参阅[使用示例和授权说明](https://langchain-doc.cn/v1/python/integrations/tools/google_cloud_texttospeech)。

```python
from langchain_google_community import TextToSpeechTool
```

#### Google Drive

用于与 Google Drive 交互的工具。

安装所需的包：

```bash
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib langchain-googledrive
```

```bash
uv add google-api-python-client google-auth-httplib2 google-auth-oauthlib langchain-googledrive
```

请参阅[使用示例和授权说明](https://langchain-doc.cn/v1/python/integrations/tools/google_drive)。

```python
from langchain_googledrive.utilities.google_drive import GoogleDriveAPIWrapper
from langchain_googledrive.tools.google_drive.tool import GoogleDriveSearchTool
```

#### Google Finance (谷歌财经)

查询财务数据。需要 `google-search-results` 包和 SerpApi 密钥。

```bash
pip install google-search-results langchain-community # 需要 langchain-community
```

```bash
uv add google-search-results langchain-community # 需要 langchain-community
```

请参阅[使用示例和授权说明](https://langchain-doc.cn/v1/python/integrations/tools/google_finance)。

```python
from langchain_community.tools.google_finance import GoogleFinanceQueryRun
from langchain_community.utilities.google_finance import GoogleFinanceAPIWrapper
```

#### Google Jobs (谷歌职位)

查询职位列表。需要 `google-search-results` 包和 SerpApi 密钥。

```bash
pip install google-search-results langchain-community # 需要 langchain-community
```

```bash
uv add google-search-results langchain-community # 需要 langchain-community
```

请参阅[使用示例和授权说明](https://langchain-doc.cn/v1/python/integrations/tools/google_jobs)。

```python
from langchain_community.tools.google_jobs import GoogleJobsQueryRun
# 注意：实用程序可能共享，例如，此处列出了 GoogleFinanceAPIWrapper，请验证正确的实用程序
# from langchain_community.utilities.google_jobs import GoogleJobsAPIWrapper # 如果存在
```

#### Google Lens

执行视觉搜索。需要 `google-search-results` 包和 SerpApi 密钥。

```bash
pip install google-search-results langchain-community # 需要 langchain-community
```

```bash
uv add google-search-results langchain-community # 需要 langchain-community
```

请参阅[使用示例和授权说明](https://langchain-doc.cn/v1/python/integrations/tools/google_lens)。

```python
from langchain_community.tools.google_lens import GoogleLensQueryRun
from langchain_community.utilities.google_lens import GoogleLensAPIWrapper
```

#### Google Places (谷歌地点)

搜索地点信息。需要 `googlemaps` 包和 Google Maps API 密钥。

```bash
pip install googlemaps langchain # 需要基础 langchain
```

```bash
uv add googlemaps langchain # 需要基础 langchain
```

请参阅[使用示例和授权说明](https://langchain-doc.cn/v1/python/integrations/tools/google_places)。

```python
# 注意：GooglePlacesTool 可能在 langchain 或 langchain_community 中，具体取决于版本
from langchain.tools import GooglePlacesTool # 或 langchain_community.tools
```

#### Google Scholar (谷歌学术)

搜索学术论文。需要 `google-search-results` 包和 SerpApi 密钥。

```bash
pip install google-search-results langchain-community # 需要 langchain-community
```

```bash
uv add google-search-results langchain-community # 需要 langchain-community
```

请参阅[使用示例和授权说明](https://langchain-doc.cn/v1/python/integrations/tools/google_scholar)。

```python
from langchain_community.tools.google_scholar import GoogleScholarQueryRun
from langchain_community.utilities.google_scholar import GoogleScholarAPIWrapper
```

#### Google Search (谷歌搜索)

使用 Google Custom Search Engine (CSE) 执行网络搜索。需要 `GOOGLE_API_KEY` 和 `GOOGLE_CSE_ID`。

安装 `langchain-google-community`：

```bash
pip install langchain-google-community
```

```bash
uv add langchain-google-community
```

封装器 (Wrapper)：

```python
from langchain_google_community import GoogleSearchAPIWrapper
```

工具：

```python
from langchain_community.tools import GoogleSearchRun, GoogleSearchResults
```

智能体加载 (Agent Loading)：

```python
from langchain_community.agent_toolkits.load_tools import load_tools
tools = load_tools(["google-search"])
```

请参阅[详细笔记本](https://langchain-doc.cn/v1/python/integrations/tools/google_search)。

#### Google Trends (谷歌趋势)

查询 Google Trends 数据。需要 `google-search-results` 包和 SerpApi 密钥。

```bash
pip install google-search-results langchain-community # 需要 langchain-community
```

```bash
uv add google-search-results langchain-community # 需要 langchain-community
```

请参阅[使用示例和授权说明](https://langchain-doc.cn/v1/python/integrations/tools/google_trends)。

```python
from langchain_community.tools.google_trends import GoogleTrendsQueryRun
from langchain_community.utilities.google_trends import GoogleTrendsAPIWrapper
```

### 工具包 (Toolkits)

特定 Google 服务的工具集合。

#### Gmail

> [Google Gmail (谷歌邮箱)](https://en.wikipedia.org/wiki/Gmail) 是 Google 提供的**免费电子邮件服务**。
> 此工具包通过 `Gmail API` 处理电子邮件。

```bash
pip install langchain-google-community[gmail]
```

```bash
uv add langchain-google-community[gmail]
```

请参阅[使用示例和授权说明](https://langchain-doc.cn/v1/python/integrations/tools/gmail)。

```python
# 加载整个工具包
from langchain_google_community import GmailToolkit
# 或使用单独的工具
from langchain_google_community.gmail.create_draft import GmailCreateDraft
from langchain_google_community.gmail.get_message import GmailGetMessage
from langchain_google_community.gmail.get_thread import GmailGetThread
from langchain_google_community.gmail.search import GmailSearch
from langchain_google_community.gmail.send_message import GmailSendMessage
```

### MCP Toolbox

[MCP Toolbox](https://github.com/googleapis/genai-toolbox) 提供了一种**简单高效**的方式来连接您的数据库，包括 Google Cloud 上的数据库，如 [Cloud SQL](https://cloud.google.com/sql/docs) 和 [Alloy