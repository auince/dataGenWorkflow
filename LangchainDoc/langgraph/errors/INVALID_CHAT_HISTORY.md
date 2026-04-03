# INVALID_CHAT_HISTORY

这个错误在预构建的@[create_agent][create_agent]中当`call_model`图节点收到格式错误的消息列表时抛出。具体来说，当有带有`tool_calls`（LLM请求调用工具）的`AIMessages`但没有对应的@[`ToolMessage`]（工具调用结果返回给LLM）时，格式就不正确。

这个错误在预构建的@[createAgent][create_agent]中当`callModel`图节点收到格式错误的消息列表时抛出。具体来说，当有带有`tool_calls`（LLM请求调用工具）的`AIMessage`但没有对应的@[`ToolMessage`]（工具调用结果返回给LLM）时，格式就不正确。

您看到此错误的原因可能有几个：

1. 您在调用图时手动传递了格式错误的消息列表，例如`graph.invoke({'messages': [AIMessage(..., tool_calls=[...])]})`

2. 图在收到`tools`节点的更新（即@[`ToolMessage`]的列表）之前被中断了
   并且您使用非None或非ToolMessage的输入调用了它，
   例如`graph.invoke({'messages': [HumanMessage(...)]}, config)`。
   此中断可能通过以下方式之一触发：
   * 您在`create_agent`中手动设置了`interrupt_before = ['tools']`
   * 其中一个工具引发了未被@[`ToolNode`]（`"tools"`）处理的错误

3. 您在调用图时手动传递了格式错误的消息列表，例如`graph.invoke({messages: [new AIMessage({..., tool_calls: [...]})]})`

4. 图在收到`tools`节点的更新（即@[`ToolMessage`]的列表）之前被中断了
   并且您使用非null或非ToolMessage的输入调用了它，
   例如`graph.invoke({messages: [new HumanMessage(...)]}, config)`。
   此中断可能通过以下方式之一触发：
   * 您在`createAgent`中手动设置了`interruptBefore: ['tools']`
   * 其中一个工具引发了未被@[`ToolNode`]（`"tools"`）处理的错误

## 故障排除

要解决此问题，您可以执行以下操作之一：

1. 不要使用格式错误的消息列表调用图
2. 在中断的情况下（手动或由于错误），您可以：
   * 提供与现有工具调用匹配的@[`ToolMessage`]对象并调用`graph.invoke({'messages': [ToolMessage(...)]})`。
     **注意**：这将把消息附加到历史记录中，并从START节点运行图。
     * 手动更新状态并从中断点恢复图：
       1. 使用`graph.get_state(config)`从图状态获取最近的消息列表
       2. 修改消息列表，要么从未回答的AIMessages中删除工具调用
         或者添加具有与未回答工具调用匹配的`tool_call_ids`的@[`ToolMessage`]对象
       3. 使用修改后的消息列表调用`graph.update_state(config, {'messages': ...})`
       4. 恢复图，例如调用`graph.invoke(None, config)`
   * 提供与现有工具调用匹配的`ToolMessage`对象并调用`graph.invoke({messages: [new ToolMessage(...)]})`。
     **注意**：这将把消息附加到历史记录中，并从START节点运行图。
     * 手动更新状态并从中断点恢复图：
       1. 使用`graph.getState(config)`从图状态获取最近的消息列表
       2. 修改消息列表，要么从未回答的AIMessages中删除工具调用
         或者添加具有与未回答工具调用匹配的`toolCallId`的`ToolMessage`对象
       3. 使用修改后的消息列表调用`graph.updateState(config, {messages: ...})`
       4. 恢复图，例如调用`graph.invoke(null, config)`