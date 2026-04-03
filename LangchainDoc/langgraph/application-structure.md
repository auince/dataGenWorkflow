# 应用程序结构

LangGraph应用程序由一个或多个图、一个配置文件（`langgraph.json`）、一个指定依赖项的文件和一个可选的指定环境变量的`.env`文件组成。

本指南展示了应用程序的典型结构，并说明如何指定使用LangSmith部署应用程序所需的信息。

## 关键概念

要使用LangSmith进行部署，应提供以下信息：

1. 一个[LangGraph配置文件](#配置文件)（`langgraph.json`），用于指定应用程序使用的依赖项、图和环境变量。
2. 实现应用程序逻辑的[图](#图)。
3. 一个指定[依赖项](#依赖项)的文件，这些依赖项是运行应用程序所必需的。
4. [环境变量](#环境变量)，这些环境变量是应用程序运行所必需的。

## 文件结构

以下是应用程序的目录结构示例：

### Python (requirements.txt)

```
my-app/
├── my_agent # 所有项目代码都在这里
│   ├── utils # 图的实用工具
│   │   ├── __init__.py
│   │   ├── tools.py # 图的工具
│   │   ├── nodes.py # 图的节点函数
│   │   └── state.py # 图的状态定义
│   ├── __init__.py
│   └── agent.py # 构建图的代码
├── .env # 环境变量
├── requirements.txt # 包依赖项
└── langgraph.json # LangGraph的配置文件
```

### Python (pyproject.toml)

```
my-app/
├── my_agent # 所有项目代码都在这里
│   ├── utils # 图的实用工具
│   │   ├── __init__.py
│   │   ├── tools.py # 图的工具
│   │   ├── nodes.py # 图的节点函数
│   │   └── state.py # 图的状态定义
│   ├── __init__.py
│   └── agent.py # 构建图的代码
├── .env # 环境变量
├── langgraph.json  # LangGraph的配置文件
└── pyproject.toml # 项目依赖项
```

### JavaScript

```
my-app/
├── src # 所有项目代码都在这里
│   ├── utils # 图的可选实用工具
│   │   ├── tools.ts # 图的工具
│   │   ├── nodes.ts # 图的节点函数
│   │   └── state.ts # 图的状态定义
│   └── agent.ts # 构建图的代码
├── package.json # 包依赖项
├── .env # 环境变量
└── langgraph.json # LangGraph的配置文件
```

**注意：** LangGraph应用程序的目录结构可能会根据使用的编程语言和包管理器而有所不同。

## 配置文件

`langgraph.json`文件是一个JSON文件，用于指定部署LangGraph应用程序所需的依赖项、图、环境变量和其他设置。

有关JSON文件中所有支持的键的详细信息，请参阅[LangGraph配置文件参考](https://langchain-doc.cn/langsmith/cli#configuration-file)。

**提示：** [LangGraph CLI](https://langchain-doc.cn/langsmith/cli)默认使用当前目录中的配置文件`langgraph.json`。

### 示例

#### Python

* 依赖项包括一个自定义本地包和`langchain_openai`包。
* 单个图将从文件`./your_package/your_file.py`中加载，变量名为`variable`。
* 环境变量从`.env`文件加载。

```json
{
  "dependencies": ["langchain_openai", "./your_package"],
  "graphs": {
    "my_agent": "./your_package/your_file.py:agent"
  },
  "env": "./.env"
}
```

#### JavaScript

* 依赖项将从本地目录中的依赖文件加载（例如`package.json`）。
* 单个图将从文件`./your_package/your_file.js`中加载，函数名为`agent`。
* 环境变量`OPENAI_API_KEY`是内联设置的。

```json
{
  "dependencies": ["."],
  "graphs": {
    "my_agent": "./your_package/your_file.js:agent"
  },
  "env": {
    "OPENAI_API_KEY": "secret-key"
  }
}
```

## 依赖项

LangGraph应用程序可能依赖于其他Python包或TypeScript/JavaScript库。

要正确设置依赖项，通常需要指定以下信息：

1. 目录中指定依赖项的文件（例如`requirements.txt`、`pyproject.toml`或`package.json`）。
2. [LangGraph配置文件](#配置文件)中的`dependencies`键，用于指定运行LangGraph应用程序所需的依赖项。
3. 任何其他二进制文件或系统库都可以使用[LangGraph配置文件](#配置文件)中的`dockerfile_lines`键来指定。

## 图

使用[LangGraph配置文件](#配置文件)中的`graphs`键来指定在部署的LangGraph应用程序中可用的图。

你可以在配置文件中指定一个或多个图。每个图由一个名称（应该是唯一的）和以下路径之一标识：(1) 编译后的图，或(2) 定义创建图的函数。

## 环境变量

如果你在本地使用已部署的LangGraph应用程序，可以在[LangGraph配置文件](#配置文件)的`env`键中配置环境变量。

对于生产部署，你通常希望在部署环境中配置环境变量。