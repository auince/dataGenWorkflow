# MULTIPLE_SUBGRAPHS

您正在单个LangGraph节点内多次调用子图，并且每个子图都启用了检查点。

由于子图检查点命名空间工作方式的内部限制，目前不允许这样做。

## 故障排除

以下方法可能有助于解决此错误：

- 如果您不需要中断/恢复子图，请在编译时传递`checkpointer=False`，如下所示：`.compile(checkpointer=False)`

- 如果您不需要中断/恢复子图，请在编译时传递`checkpointer: false`，如下所示：`.compile({ checkpointer: false })`

- 不要在同一个节点中命令式地多次调用图，而是使用[`Send`](https://langchain-doc.cn/v1/python/langgraph/graph-api#send) API。