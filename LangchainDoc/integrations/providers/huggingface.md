# Hugging Face

所有 LangChain 与 **[Hugging Face Hub](https://huggingface.co/)** 的集成，以及与 **[transformers](https://huggingface.co/docs/transformers/index)**、**[sentence transformers](https://sbert.net/)** 和 **[datasets](https://huggingface.co/docs/datasets/index)** 等库的集成。

## 聊天模型 (Chat models)

### ChatHuggingFace

我们可以使用 **`Hugging Face` LLM** 类或直接使用 **`ChatHuggingFace`** 类。

请查看 **[使用示例](https://langchain-doc.cn/v1/python/integrations/chat/huggingface)**。

```python
from langchain_huggingface import ChatHuggingFace
```

## LLMs（大型语言模型）

### HuggingFaceEndpoint

我们可以使用 **`HuggingFaceEndpoint`** 类通过无服务器 **[Inference Providers](https://huggingface.co/docs/inference-providers)** 或专用 **[Inference Endpoints](https://huggingface.co/inference-endpoints/dedicated)** 来运行开源模型。

请查看 **[使用示例](https://langchain-doc.cn/v1/python/integrations/llms/huggingface_endpoint)**。

```python
from langchain_huggingface import HuggingFaceEndpoint
```

### HuggingFacePipeline

我们可以使用 **`HuggingFacePipeline`** 类在本地运行开源模型。

请查看 **[使用示例](https://langchain-doc.cn/v1/python/integrations/llms/huggingface_pipelines)**。

```python
from langchain_huggingface import HuggingFacePipeline
```

## 嵌入模型 (Embedding Models)

### HuggingFaceEmbeddings

我们可以使用 **`HuggingFaceEmbeddings`** 类在本地运行开源嵌入模型。

请查看 **[使用示例](https://langchain-doc.cn/v1/python/integrations/text_embedding/huggingfacehub)**。

```python
from langchain_huggingface import HuggingFaceEmbeddings
```

### HuggingFaceEndpointEmbeddings

我们可以使用 **`HuggingFaceEndpointEmbeddings`** 类通过专用的 **[Inference Endpoint](https://huggingface.co/inference-endpoints/dedicated)** 来运行开源嵌入模型。

请查看 **[使用示例](https://langchain-doc.cn/v1/python/integrations/text_embedding/huggingfacehub)**。

```python
from langchain_huggingface import HuggingFaceEndpointEmbeddings
```

### HuggingFaceInferenceAPIEmbeddings

我们可以使用 **`HuggingFaceInferenceAPIEmbeddings`** 类通过 **[Inference Providers](https://huggingface.co/docs/inference-providers)** 来运行开源嵌入模型。

请查看 **[使用示例](https://langchain-doc.cn/v1/python/integrations/text_embedding/huggingfacehub)**。

```python
from langchain_community.embeddings import HuggingFaceInferenceAPIEmbeddings
```

### HuggingFaceInstructEmbeddings

我们可以使用 **`HuggingFaceInstructEmbeddings`** 类在本地运行开源嵌入模型。

请查看 **[使用示例](https://langchain-doc.cn/v1/python/integrations/text_embedding/instruct_embeddings)**。

```python
from langchain_community.embeddings import HuggingFaceInstructEmbeddings
```

### HuggingFaceBgeEmbeddings

> **[HuggingFace 上的 BGE 模型](https://huggingface.co/BAAI/bge-large-en-v1.5)** 是 **[最好的开源嵌入模型之一](https://huggingface.co/spaces/mteb/leaderboard)**。
> BGE 模型由 **[北京智源人工智能研究院 (BAAI)](https://en.wikipedia.org/wiki/Beijing_Academy_of_Artificial_Intelligence)** 创建。`BAAI` 是一家从事人工智能研究与开发的民办非营利组织。

请查看 **[使用示例](https://langchain-doc.cn/v1/python/integrations/text_embedding/bge_huggingface)**。

```python
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
```

## 文档加载器 (Document loaders)

### Hugging Face 数据集 (Hugging Face dataset)

> **[Hugging Face Hub](https://huggingface.co/docs/hub/index)** 拥有超过 75,000 个 **[数据集](https://huggingface.co/docs/hub/index#datasets)**，涵盖 100 多种语言，可用于 **自然语言处理 (NLP)**、**计算机视觉** 和 **音频** 等领域的广泛任务。它们被用于翻译、自动语音识别和图像分类等多种任务。

我们需要安装 `datasets` python 包。

```bash
pip install datasets
```

```bash
uv add datasets
```

请查看 **[使用示例](https://langchain-doc.cn/v1/python/integrations/document_loaders/hugging_face_dataset)**。

```python
from langchain_community.document_loaders.hugging_face_dataset import HuggingFaceDatasetLoader
```

### Hugging Face 模型加载器 (Hugging Face model loader)

> 从 `Hugging Face Hub` 加载模型信息，包括 README 内容。

> 此加载器与 **`Hugging Face Models API`** 接口交互，以获取并加载模型元数据和 README 文件。
> 该 API 允许您根据特定条件（例如模型标签、作者等）搜索和过滤模型。

```python
from langchain_community.document_loaders import HuggingFaceModelLoader
```

### 图像字幕 (Image captions)

它使用 Hugging Face 模型来生成图像字幕。

我们需要安装几个 python 包。

```bash
pip install transformers pillow
```

```bash
uv add transformers pillow
```

请查看 **[使用示例](https://langchain-doc.cn/v1/python/integrations/document_loaders/image_captions)**。

```python
from langchain_community.document_loaders import ImageCaptionLoader
```

## 工具 (Tools)

### Hugging Face Hub 工具 (Hugging Face Hub Tools)

> **[Hugging Face 工具](https://huggingface.co/docs/transformers/v4.29.0/en/custom_tools)** 支持文本 I/O，并使用 **`load_huggingface_tool`** 函数加载。

我们需要安装几个 python 包。

```bash
pip install transformers huggingface_hub
```

```bash
uv add transformers huggingface_hub
```

请查看 **[使用示例](https://langchain-doc.cn/v1/python/integrations/tools/huggingface_tools)**。

```python
from langchain_community.agent_toolkits.load_tools import load_huggingface_tool
```

### Hugging Face 文本转语音模型推理 (Hugging Face Text-to-Speech Model Inference)

> 它是 `OpenAI Text-to-Speech API` 的一个封装。

```python
from langchain_community.tools.audio import HuggingFaceTextToSpeechModelInference