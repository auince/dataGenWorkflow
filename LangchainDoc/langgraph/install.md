# 安装LangGraph

## 基本安装

要安装基础的LangGraph包：

### Python

```bash
pip install -U langgraph
```

或使用uv：

```bash
uv add langgraph
```

### JavaScript

```bash
npm install @langchain/langgraph @langchain/core
```

或使用pnpm：

```bash
pnpm add @langchain/langgraph @langchain/core
```

或使用yarn：

```bash
yarn add @langchain/langgraph @langchain/core
```

或使用bun：

```bash
bun add @langchain/langgraph @langchain/core
```

## 安装LangChain（可选）

使用LangGraph时，您通常需要访问LLM并定义工具。您可以以任何适合您的方式进行。

一种方法是使用[LangChain](../langchain/overview.html)（我们在文档中会使用这种方式）。

### Python

```bash
pip install -U langchain
```

或使用uv：

```bash
uv add langchain
```

### JavaScript

```bash
npm install langchain
```

或使用pnpm：

```bash
pnpm add langchain
```

或使用yarn：

```bash
yarn add langchain
```

或使用bun：

```bash
bun add langchain
```

## 安装特定的LLM提供商包

要使用特定的LLM提供商包，您需要单独安装它们。

请参考[集成](../integrations/providers/overview.html)页面获取提供商特定的安装说明。