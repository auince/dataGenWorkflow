# 中断

中断允许您在特定点暂停图执行，并在继续之前等待外部输入。这使能了人在循环中的模式，在这些模式中，您需要外部输入才能继续。当触发中断时，LangGraph使用其[持久化](persistence.html)层保存图状态，并无限期等待直到您恢复执行。

中断通过在图节点的任何点调用`interrupt()`函数来工作。该函数接受任何JSON可序列化的值，这些值会显示给调用者。当您准备好继续时，您通过使用`Command`重新调用图来恢复执行，然后它成为节点内部`interrupt()`调用的返回值。

与静态断点（在特定节点之前或之后暂停）不同，中断是**动态的**—它们可以放置在代码中的任何位置，并且可以基于您的应用程序逻辑是有条件的。

- **检查点保持您的位置**：检查点写入确切的图状态，以便您可以稍后恢复，即使在错误状态下也是如此。
- **`thread_id`是您的指针**：设置`config={"configurable": {"thread_id": ...}}`以告诉检查点加载哪个状态。
- **中断负载显示为`__interrupt__`**：您传递给`interrupt()`的值在`__interrupt__`字段中返回给调用者，以便您知道图在等待什么。

- **检查点保持您的位置**：检查点写入确切的图状态，以便您可以稍后恢复，即使在错误状态下也是如此。
- **`thread_id`是您的指针**：使用`{ configurable: { thread_id: ... } }`作为`invoke`方法的选项，以告诉检查点加载哪个状态。
- **中断负载显示为`__interrupt__`**：您传递给`interrupt()`的值在`__interrupt__`字段中返回给调用者，以便您知道图在等待什么。

您选择的`thread_id`实际上是您的持久游标。重用它会恢复相同的检查点；使用新值会启动一个具有空状态的全新线程。

## 使用`interrupt`暂停

@[`interrupt`]函数暂停图执行并向调用者返回值。当您在节点内调用@[`interrupt`]时，LangGraph保存当前图状态并等待您用输入恢复执行。

要使用@[`interrupt`]，您需要：

1. 一个**检查点**来持久化图状态（在生产环境中使用持久检查点）
2. 配置中的**线程ID**，以便运行时知道要从中恢复哪个状态
3. 在您想要暂停的地方调用`interrupt()`（负载必须是JSON可序列化的）

```python
from langgraph.types import interrupt
def approval_node(state: State):
    # 暂停并请求批准
    approved = interrupt("Do you approve this action?")
    # 当您恢复时，Command(resume=...)在这里返回该值
    return {"approved": approved}
```

```js
```typescript
import { interrupt } from "@langchain/langgraph";
async function approvalNode(state: State) {
    // 暂停并请求批准
    const approved = interrupt("Do you approve this action?");
    // Command({ resume: ... })提供返回到此变量的值
    return { approved };
}
```

当您调用@[`interrupt`]时，会发生以下情况：

1. **图执行在调用@[`interrupt`]的确切点被挂起**
2. **状态被保存**使用检查点，以便执行可以稍后恢复，在生产环境中，这应该是一个持久检查点（例如，由数据库支持）
3. **值被返回**给调用者，位于`__interrupt__`下；它可以是任何JSON可序列化的值（字符串、对象、数组等）
4. **图无限期等待**，直到您用响应恢复执行
5. **响应被传回**到节点，当您恢复时，成为`interrupt()`调用的返回值

## 恢复中断

中断暂停执行后，您可以通过再次使用包含恢复值的`Command`调用图来恢复图。恢复值被传递回`interrupt`调用，允许节点使用外部输入继续执行。

```python
```python
from langgraph.types import Command
# 初始运行 - 触发中断并暂停
# thread_id是持久指针（在生产环境中存储稳定ID）
config = {"configurable": {"thread_id": "thread-1"}}
result = graph.invoke({"input": "data"}, config=config)
# 检查被中断的内容
# __interrupt__包含传递给interrupt()的负载
print(result["__interrupt__"])
# > [Interrupt(value='Do you approve this action?')]
# 使用人类的响应恢复
# 恢复负载成为节点内部interrupt()的返回值
graph.invoke(Command(resume=True), config=config)
```

```js
```typescript
import { Command } from "@langchain/langgraph";
// 初始运行 - 触发中断并暂停
// thread_id是指向保存的检查点的持久指针
const config = { configurable: { thread_id: "thread-1" } };
const result = await graph.invoke({ input: "data" }, config);
// 检查被中断的内容
// __interrupt__镜像您传递给interrupt()的每个负载
console.log(result.__interrupt__);
// [{ value: 'Do you approve this action?', ... }]
// 使用人类的响应恢复
// Command({ resume })从节点中的interrupt()返回该值
await graph.invoke(new Command({ resume: true }), config);
```

**关于恢复的关键点：**

- 恢复时，您必须使用与中断发生时相同的**线程ID**
- 传递给`Command(resume=...)`的值成为@[`interrupt`]调用的返回值
- 节点从中断调用所在的节点开始处重新启动，因此中断前的任何代码都会再次运行
- 您可以传递任何JSON可序列化的值作为恢复值

## 常见模式

中断解锁的关键功能是暂停执行并等待外部输入的能力。这对于各种用例都很有用，包括：

- ✅ [批准工作流](#批准或拒绝)：在执行关键操作（API调用、数据库更改、财务交易）前暂停
- ✏️ [审查和编辑](#审查和编辑状态)：让人类在继续之前审查和修改LLM输出或工具调用
- 🔧 [中断工具调用](#工具中的中断)：在执行工具调用前暂停，以在执行前审查和编辑工具调用
- 🛡️ [验证人类输入](#验证人类输入)：在下一个步骤前暂停，以验证人类输入

### 批准或拒绝

中断最常见的用途之一是在关键操作前暂停并请求批准。例如，您可能希望请求人类批准API调用、数据库更改或任何其他重要决策。

```python
```python
from typing import Literal
from langgraph.types import interrupt, Command
def approval_node(state: State) -> Command[Literal["proceed", "cancel"]]:
    # 暂停执行；负载显示在result["__interrupt__"]下
    is_approved = interrupt({
        "question": "Do you want to proceed with this action?",
        "details": state["action_details"]
    })
    # 基于响应进行路由
    if is_approved:
        return Command(goto="proceed")  # 在提供恢复负载后运行
    else:
        return Command(goto="cancel")
```

```js
```typescript
import { interrupt, Command } from "@langchain/langgraph";
function approvalNode(state: State): Command {
  // 暂停执行；负载显示在result.__interrupt__中
  const isApproved = interrupt({
    question: "Do you want to proceed?",
    details: state.actionDetails
  });
  // 基于响应进行路由
  if (isApproved) {
    return new Command({ goto: "proceed" }); // 在提供恢复负载后运行
  } else {
    return new Command({ goto: "cancel" });
  }
}
```

当您恢复图时，传递`true`表示批准或`false`表示拒绝：

```python
```python
# 批准
graph.invoke(Command(resume=True), config=config)
# 拒绝
graph.invoke(Command(resume=False), config=config)
```

```js
```typescript
// 批准
await graph.invoke(new Command({ resume: true }), config);
// 拒绝
await graph.invoke(new Command({ resume: false }), config);
```

### 审查和编辑状态

有时您希望让人类在继续之前审查和编辑图状态的一部分。这对于纠正LLM、添加缺失信息或进行调整很有用。

```python
```python
from langgraph.types import interrupt
def review_node(state: State):
    # 暂停并显示当前内容以供审查（显示在result["__interrupt__"]中）
    edited_content = interrupt({
        "instruction": "Review and edit this content",
        "content": state["generated_text"]
    })
    # 用编辑后的版本更新状态
    return {"generated_text": edited_content}
```

```js
```typescript
import { interrupt } from "@langchain/langgraph";
function reviewNode(state: State) {
  // 暂停并显示当前内容以供审查（显示在result.__interrupt__中）
  const editedContent = interrupt({
    instruction: "Review and edit this content",
    content: state.generatedText
  });
  // 用编辑后的版本更新状态
  return { generatedText: editedContent };
}
```

恢复时，提供编辑后的内容：

```python
```python
graph.invoke(
    Command(resume="The edited and improved text"),  # 值成为interrupt()的返回值
    config=config
)
```

```js
```typescript
await graph.invoke(
  new Command({ resume: "The edited and improved text" }), // 值成为interrupt()的返回值
  config
);
```

### 工具中的中断

您也可以直接在工具函数中放置中断。这使工具本身在每次调用时都暂停等待批准，并允许在执行前对工具调用进行人类审查和编辑。

首先，定义一个使用@[`interrupt`]的工具：

```python
```python
from langchain.tools import tool
from langgraph.types import interrupt
@tool
def send_email(to: str, subject: str, body: str):
    """Send an email to a recipient."""
    # 发送前暂停；负载显示在result["__interrupt__"]中
    response = interrupt({
        "action": "send_email",
        "to": to,
        "subject": subject,
        "body": body,
        "message": "Approve sending this email?"
    })
    if response.get("action") == "approve":
        # 恢复值可以在执行前覆盖输入
        final_to = response.get("to", to)
        final_subject = response.get("subject", subject)
        final_body = response.get("body", body)
        return f"Email sent to {final_to} with subject '{final_subject}'"
    return "Email cancelled by user"
```

```js
```typescript
import { tool } from "@langchain/core/tools";
import { interrupt } from "@langchain/langgraph";
import * as z from "zod";
const sendEmailTool = tool(
  async ({ to, subject, body }) => {
    // 发送前暂停；负载显示在result.__interrupt__中
    const response = interrupt({
      action: "send_email",
      to,
      subject,
      body,
      message: "Approve sending this email?",
    });
    if (response?.action === "approve") {
      // 恢复值可以在执行前覆盖输入
      const finalTo = response.to ?? to;
      const finalSubject = response.subject ?? subject;
      const finalBody = response.body ?? body;
      return `Email sent to ${finalTo} with subject '${finalSubject}'`;
    }
    return "Email cancelled by user";
  },
  {
    name: "send_email",
    description: "Send an email to a recipient",
    schema: z.object({
      to: z.string(),
      subject: z.string(),
      body: z.string(),
    }),
  },
);
```

这种方法在您希望批准逻辑与工具本身一起存在时很有用，使其可以在图的不同部分重用。LLM可以自然地调用该工具，并且每当调用该工具时，中断都会暂停执行，允许您批准、编辑或取消操作。

### 验证人类输入

有时您需要验证来自人类的输入，并在无效时再次询问。您可以通过在循环中使用多个@[`interrupt`]调用来实现这一点。

```python
```python
from langgraph.types import interrupt
def get_age_node(state: State):
    prompt = "What is your age?"
    while True:
        answer = interrupt(prompt)  # 负载显示在result["__interrupt__"]中
        # 验证输入
        if isinstance(answer, int) and answer > 0:
            # 有效输入 - 继续
            break
        else:
            # 无效输入 - 用更具体的提示再次询问
            prompt = f"'{answer}' is not a valid age. Please enter a positive number."
    return {"age": answer}
```

```js
```typescript
import { interrupt } from "@langchain/langgraph";
function getAgeNode(state: State) {
  let prompt = "What is your age?";
  while (true) {
    const answer = interrupt(prompt); // 负载显示在result.__interrupt__中
    // 验证输入
    if (typeof answer === "number" && answer > 0) {
      // 有效输入 - 继续
      return { age: answer };
    } else {
      // 无效输入 - 用更具体的提示再次询问
      prompt = `'${answer}' is not a valid age. Please enter a positive number.`;
    }
  }
}
```

每次您用无效输入恢复图时，它会用更清晰的消息再次询问。一旦提供了有效输入，节点完成，图继续。

> 注意：由于文件长度限制，此文档仅包含interrupts.mdx的主要内容部分。完整示例代码和更多详细信息可能需要参考原始文档。