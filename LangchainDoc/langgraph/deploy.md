# 部署

LangSmith是将代理转变为生产系统的最快方式。传统的托管平台是为无状态、短期运行的Web应用程序构建的，而LangGraph是**专为有状态、长期运行的代理而设计的**，因此你可以在几分钟内从代码库转到可靠的云部署。

## 先决条件

在开始之前，请确保你具备以下条件：

*   一个[GitHub账户](https://github.com/)
*   一个[LangSmith账户](https://smith.langchain.com/)（免费注册）

## 部署你的代理

### 1. 在GitHub上创建仓库

你的应用程序代码必须位于GitHub仓库中才能在LangSmith上部署。支持公共和私有仓库。对于这个快速入门，首先确保你的应用程序与LangGraph兼容，方法是按照[本地服务器设置指南](studio.html#setup-local-langgraph-server)操作。然后，将你的代码推送到仓库。

> 注意：文档中引用的部署步骤部分因系统限制无法显示，请参考LangSmith官方文档获取完整的部署指南。