# 检索

大型语言模型 (LLM) 功能强大，但它们有两个主要的局限性：

*   **有限的上下文** — 它们无法一次性消化整个语料库。
*   **静态的知识** — 它们的训练数据是固定在某个时间点的。

**检索**通过在查询时获取相关的外部知识来解决这些问题。这是**检索增强生成 (Retrieval-Augmented Generation, RAG)** 的基础：用特定于上下文的信息来增强 LLM 的答案。

## 构建知识库

**知识库**是用于检索的文档或结构化数据的存储库。

如果您需要一个自定义知识库，您可以使用 LangChain 的文档加载器 (document loaders) 和向量存储 (vector stores) 从您自己的数据中构建一个。

> **注意：**
>
> 如果您已经拥有一个知识库（例如，SQL 数据库、CRM 或内部文档系统），您**不需要**重建它。您可以：
>
> *   将其作为 **工具** 连接到 Agentic RAG 中的智能体。
> *   查询它并将检索到的内容作为上下文提供给 LLM [（2 步 RAG）](#2-step-rag)。

请参阅以下教程来构建一个可搜索的知识库和最小的 RAG 工作流程：

> 教程：语义搜索 (Semantic search)
>
> 了解如何使用 LangChain 的文档加载器、嵌入和向量存储从您自己的数据中创建一个可搜索的知识库。
>
> 在本教程中，您将基于一个 PDF 文件构建一个搜索引擎，从而能够检索与查询相关的段落。您还将在此引擎之上实现一个最小的 RAG 工作流程，以了解如何将外部知识集成到 LLM 的推理中。

### 从检索到 RAG

**检索**允许 LLM 在运行时访问相关上下文。但大多数实际应用会更进一步：它们将**检索与生成相结合**以产生有依据的、上下文感知的答案。

这是**检索增强生成 (RAG)** 背后的核心思想。检索管道成为一个将搜索与生成相结合的更广泛系统的基础。

### 检索管道

一个典型的检索工作流程如下所示：

```mermaid
flowchart LR
  S(["来源<br>(Google Drive, Slack, Notion, etc.)"]) --> L[文档加载器 (Document Loaders)]
  L --> A([文档 (Documents)])
  A --> B[切分成块 (Split into chunks)]
  B --> C[转化为嵌入 (Turn into embeddings)]
  C --> D[(向量存储 (Vector Store))]
  Q([用户查询 (User Query)]) --> E[查询嵌入 (Query embedding)]
  E --> D
  D --> F[检索器 (Retriever)]
  F --> G[LLM 使用检索到的信息 (LLM uses retrieved info)]
  G --> H([答案 (Answer)])
```

每个组件都是**模块化**的：您可以互换加载器、切分器、嵌入或向量存储，而无需重写应用程序的逻辑。

### 构成要素

| 组件名称 | 描述 |
| :--- | :--- |
| **文档加载器 (Document loaders)** | 从外部源（Google Drive、Slack、Notion 等）摄取数据，返回标准化的 [`Document`](https://reference.langchain.com/python/langchain_core/documents/#langchain_core.documents.base.Document) 对象。 |
| **文本切分器 (Text splitters)** | 将大文档拆分成更小的块，这些块将可以单独检索，并适应模型的上下文窗口。 |
| **嵌入模型 (Embedding models)** | 嵌入模型将文本转化为一个数字向量，使得含义相似的文本在该向量空间中彼此靠近。 |
| **向量存储 (Vector stores)** | 用于存储和搜索嵌入的专用数据库。 |
| **检索器 (Retrievers)** | 检索器是一个接口，给定一个非结构化查询，它会返回文档。 |

## RAG 架构

RAG 可以通过多种方式实现，具体取决于您系统的需求。我们将在以下部分概述每种类型。

| 架构 | 描述 | 控制 | 灵活性 | 延迟 | 示例用例 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **2 步 RAG** | 检索总是在生成之前发生。简单且可预测。 | ✅ 高 | ❌ 低 | ⚡ 快 | 常见问题 (FAQs)、文档机器人 |
| **Agentic RAG (智能体式 RAG)** | 由 LLM 驱动的智能体决定在推理期间**何时**以及**如何**检索。 | ❌ 低 | ✅ 高 | ⏳ 可变 | 可访问多个工具的研究助理 |
| **混合 RAG (Hybrid)** | 结合了两种方法的特点，并带有验证步骤。 | ⚖️ 中 | ⚖️ 中 | ⏳ 可变 | 带有质量验证的领域特定问答 |

> **信息：延迟**
>
> 在 **2 步 RAG** 中，延迟通常更**可预测**，因为 LLM 调用的最大次数是已知且受限制的。这种可预测性假设 LLM 推理时间是主导因素。然而，实际延迟也可能受到检索步骤性能的影响——例如 API 响应时间、网络延迟或数据库查询——这些会根据所使用的工具和基础设施而有所不同。

### 2 步 RAG (2-step RAG)

在 **2 步 RAG** 中，**检索步骤总是在生成步骤之前执行**。这种架构直接且可预测，适用于许多将相关文档检索作为生成答案的明确先决条件的应用程序。

```mermaid
graph LR
         A[用户问题 (User Question)] --> B["检索相关文档 (Retrieve Relevant Documents)"]
         B --> C["生成答案 (Generate Answer)"]
         C --> D[将答案返回给用户 (Return Answer to User)]
         %% Styling
         classDef startend fill:#2e7d32,stroke:#1b5e20,stroke-width:2px,color:#fff
         classDef process fill:#1976d2,stroke:#0d47a1,stroke-width:1.5px,color:#fff
         class A,D startend
         class B,C process
```

> 教程：检索增强生成 (RAG)
>
> 了解如何使用**检索增强生成**构建一个问答聊天机器人，该机器人可以根据您的数据回答问题。
>
> 本教程介绍了两种方法：
>
> *   **RAG 智能体**：使用灵活的工具运行搜索——非常适合通用用途。
> *   **2 步 RAG 链**：每次查询只需要一次 LLM 调用——对于简单任务来说快速且高效。

### Agentic RAG (智能体式 RAG)

**智能体式检索增强生成 (Agentic RAG)** 结合了检索增强生成和基于智能体的推理的优点。智能体（由 LLM 驱动）不是在回答之前检索文档，而是**逐步推理**，并决定在交互过程中**何时**以及**如何**检索信息。

> **提示：** 智能体实现 RAG 行为所需要的只是访问一个或多个可以获取外部知识的**工具**——例如文档加载器、Web API 或数据库查询。

```mermaid
graph LR
         A[用户输入 / 问题 (User Input / Question)] --> B["智能体 (LLM) (Agent (LLM))"]
         B --> C{需要外部信息吗？ (Need external info?)}
         C -- Yes --> D["使用工具搜索 (Search using tool(s))"]
         D --> H{足以回答吗？ (Enough to answer?)}
         H -- No --> B
         H -- Yes --> I[生成最终答案 (Generate final answer)]
         C -- No --> I
         I --> J[返回给用户 (Return to user)]
         %% Dark-mode friendly styling
         classDef startend fill:#2e7d32,stroke:#1b5e20,stroke-width:2px,color:#fff
         classDef decision fill:#f9a825,stroke:#f57f17,stroke-width:2px,color:#000
         classDef process fill:#1976d2,stroke:#0d47a1,stroke-width:1.5px,color:#fff
         class A,J startend
         class B,D,I process
         class C,H decision
```

```python
import requests
from langchain.tools import tool
from langchain.chat_models import init_chat_model
from langchain.agents import create_agent
@tool
def fetch_url(url: str) -> str:
    """Fetch text content from a URL"""
    response = requests.get(url, timeout=10.0)
    response.raise_for_status()
    return response.text
system_prompt = """\
Use fetch_url when you need to fetch information from a web-page; quote relevant snippets.
"""
agent = create_agent(
    model="claude-sonnet-4-5-20250929",
    tools=[fetch_url], # A tool for retrieval [!code highlight]
    system_prompt=system_prompt,
)
```

> 扩展示例：用于 LangGraph 的 llms.txt 的 Agentic RAG
>
> 此示例实现了一个 **Agentic RAG 系统**，用于协助用户查询 LangGraph 文档。该智能体首先加载 [llms.txt](https://llmstxt.org/)，其中列出了可用的文档 URL，然后可以动态地使用 `fetch_documentation` 工具来根据用户的问题检索和处理相关内容。
>
> ```python
> import requests
> from langchain.agents import create_agent
> from langchain.messages import HumanMessage
> from langchain.tools import tool
> from markdownify import markdownify
> ```
>
> ALLOWED_DOMAINS = ["https://langchain-ai.github.io/"]
> LLMS_TXT = 'https://langchain-ai.github.io/langgraph/llms.txt'
>
> @tool
> def fetch_documentation(url: str) -> str: # [!code highlight]
> """Fetch and convert documentation from a URL"""
> if not any(url.startswith(domain) for domain in ALLOWED_DOMAINS):
> return (
> "Error: URL not allowed. "
> f"Must start with one of: {', '.join(ALLOWED_DOMAINS)}"
> )
> response = requests.get(url, timeout=10.0)
> response.raise_for_status()
> return markdownify(response.text)
>
> # We will fetch the content of llms.txt, so this can
> # be done ahead of time without requiring an LLM request.
> llms_txt_content = requests.get(LLMS_TXT).text
>
> # System prompt for the agent
> system_prompt = f"""
> You are an expert Python developer and technical assistant.
> Your primary role is to help users with questions about LangGraph and related tools.
>
> Instructions:
>
> 1. If a user asks a question you're unsure about — or one that likely involves API usage,
> behavior, or configuration — you MUST use the `fetch_documentation` tool to consult the relevant docs.
> 2. When citing documentation, summarize clearly and include relevant context from the content.
> 3. Do not use any URLs outside of the allowed domain.
> 4. If a documentation fetch fails, tell the user and proceed with your best expert understanding.
>
> You can access official documentation from the following approved sources:
>
> {llms_txt_content}
>
> You MUST consult the documentation to get up to date documentation
> before answering a user's question about LangGraph.
>
> Your answers should be clear, concise, and technically accurate.
> """
>
> tools = [fetch_documentation]
>
> model = init_chat_model("claude-sonnet-4-0", max_tokens=32_000)
>
> agent = create_agent(
> model=model,
> tools=tools, # [!code highlight]
> system_prompt=system_prompt, # [!code highlight]
> name="Agentic RAG",
> )
>
> response = agent.invoke({
> 'messages': [
> HumanMessage(content=(
> "Write a short example of a langgraph agent using the "
> "prebuilt create react agent. the agent should be able "
> "to look up stock pricing information."
> ))
> ]
> })
>
> print(response['messages'][-1].content)
>
> 教程：检索增强生成 (RAG)
>
> 了解如何使用**检索增强生成**构建一个问答聊天机器人，该机器人可以根据您的数据回答问题。
>
> 本教程介绍了两种方法：
>
> *   **RAG 智能体**：使用灵活的工具运行搜索——非常适合通用用途。
> *   **2 步 RAG 链**：每次查询只需要一次 LLM 调用——对于简单任务来说快速且高效。

### 混合 RAG (Hybrid RAG)

**混合 RAG** 结合了 2 步 RAG 和 Agentic RAG 的特点。它引入了中间步骤，例如查询预处理、检索验证和生成后检查。这些系统比固定的管道提供更高的灵活性，同时保持对执行的一定控制。

典型组件包括：

*   **查询增强**：修改输入问题以提高检索质量。这可能涉及重写不清晰的查询、生成多个变体或用额外上下文扩展查询。
*   **检索验证**：评估检索到的文档是否相关和充分。如果不是，系统可能会优化查询并再次检索。
*   **答案验证**：检查生成的答案的准确性、完整性以及与源内容的对齐程度。如果需要，系统可以重新生成或修改答案。

该架构通常支持这些步骤之间的多次迭代：

```mermaid
graph LR
         A[用户问题 (User Question)] --> B[查询增强 (Query Enhancement)]
         B --> C[检索文档 (Retrieve Documents)]
         C --> D{信息充足吗？ (Sufficient Info?)}
         D -- No --> E[优化查询 (Refine Query)]
         E --> C
         D -- Yes --> F[生成答案 (Generate Answer)]
         F --> G{答案质量可以吗？ (Answer Quality OK?)}
         G -- No --> H{尝试不同方法吗？ (Try Different Approach?)}
         H -- Yes --> E
         H -- No --> I[返回最佳答案 (Return Best Answer)]
         G -- Yes --> I
         I --> J[返回给用户 (Return to User)]
         classDef startend fill:#2e7d32,stroke:#1b5e20,stroke-width:2px,color:#fff
         classDef decision fill:#f9a825,stroke:#f57f17,stroke-width:2px,color:#000
         classDef process fill:#1976d2,stroke:#0d47a1,stroke-width:1.5px,color:#fff
         class A,J startend
         class B,C,E,F,I process
         class D,G,H decision
```

这种架构适用于：

*   带有模糊或未明确说明的查询的应用程序
*   需要验证或质量控制步骤的系统
*   涉及多个来源或迭代优化的工作流程

> 教程：带有自我修正的 Agentic RAG
>
> 一个结合了智能体推理、检索和自我修正的**混合 RAG** 示例。