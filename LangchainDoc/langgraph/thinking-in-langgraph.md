# 使用LangGraph思考

LangGraph可以改变你构建代理的思维方式。当你使用LangGraph构建代理时，首先需要将其分解为称为**节点**的离散步骤。然后，描述每个节点的不同决策和转换。最后，通过共享的**状态**将节点连接在一起，每个节点都可以读取和写入这个状态。在本教程中，我们将指导你通过构建客户支持电子邮件代理的思考过程来理解LangGraph。

## 从你想要自动化的流程开始

假设你需要构建一个处理客户支持电子邮件的AI代理。产品团队给你提供了以下要求：

该代理应该：

- 读取传入的客户电子邮件
- 按紧急程度和主题分类
- 搜索相关文档来回答问题
- 起草适当的回复
- 将复杂问题升级给人类代理
- 在需要时安排后续跟进

需要处理的示例场景：

1. 简单的产品问题："如何重置我的密码？"
2. 错误报告："当我选择PDF格式时，导出功能崩溃"
3. 紧急账单问题："我的订阅被重复收费了！"
4. 功能请求："你能为移动应用添加深色模式吗？"
5. 复杂技术问题："我们的API集成间歇性失败，出现504错误"

在LangGraph中实现代理，通常遵循以下五个步骤。

## 步骤1：将工作流映射为离散步骤

首先确定流程中的不同步骤。每个步骤将成为一个**节点**（执行特定任务的函数）。然后勾勒这些步骤如何相互连接。

```
flowchart TD
    A[START] --> B[读取邮件]
    B --> C[分类意图]
    C -.-> D[文档搜索]
    C -.-> E[错误追踪]
    C -.-> F[人工审核]
    D --> G[起草回复]
    E --> G
    F --> G
    G -.-> H[人工审核]
    G -.-> I[发送回复]
    H --> J[END]
    I --> J[END]
```

箭头显示可能的路径，但实际选择哪条路径的决定发生在每个节点内部。

现在你已经确定了工作流中的组件，让我们了解每个节点需要做什么：

- 读取邮件：提取和解析邮件内容
- 分类意图：使用LLM对紧急程度和主题进行分类，然后路由到适当的操作
- 文档搜索：查询知识库以获取相关信息
- 错误追踪：在跟踪系统中创建或更新问题
- 起草回复：生成适当的回复
- 人工审核：升级给人类代理进行批准或处理
- 发送回复：发送电子邮件回复

提示：注意一些节点决定下一步去哪里（分类意图、起草回复、人工审核），而其他节点总是继续到同一个下一步（读取邮件总是转到分类意图，文档搜索总是转到起草回复）。

## 步骤2：确定每个步骤需要做什么

对于图中的每个节点，确定它代表什么类型的操作以及它正常工作需要什么上下文。

### LLM步骤

当步骤需要理解、分析、生成文本或做出推理决策时：

**分类意图节点**

- 静态上下文（提示）：分类类别、紧急程度定义、响应格式
- 动态上下文（来自状态）：邮件内容、发件人信息
- 期望结果：确定路由的结构化分类

**起草回复节点**

- 静态上下文（提示）：语气指南、公司政策、回复模板
- 动态上下文（来自状态）：分类结果、搜索结果、客户历史
- 期望结果：可供审核的专业电子邮件回复

### 数据步骤

当步骤需要从外部源检索信息时：

**文档搜索节点**

- 参数：根据意图和主题构建的查询
- 重试策略：是，对瞬态故障使用指数退避
- 缓存：可以缓存常见查询以减少API调用

**客户历史查询**

- 参数：来自状态的客户电子邮件或ID
- 重试策略：是，但如果不可用则回退到基本信息
- 缓存：是，使用生存时间来平衡新鲜度和性能

### 操作步骤

当步骤需要执行外部操作时：

**发送回复节点**

- 何时执行：在批准后（人工或自动）
- 重试策略：是，对网络问题使用指数退避
- 不应缓存：每次发送都是唯一的操作

**错误追踪节点**

- 何时执行：当意图为"错误"时总是执行
- 重试策略：是，关键是不要丢失错误报告
- 返回：要包含在回复中的工单ID

### 用户输入步骤

当步骤需要人工干预时：

**人工审核节点**

- 决策上下文：原始邮件、草拟回复、紧急程度、分类
- 预期输入格式：批准布尔值加上可选的编辑回复
- 何时触发：高紧急度、复杂问题或质量问题

## 步骤3：设计状态

状态是所有节点可访问的共享[内存](https://langchain-doc.cn/v1/python/concepts/memory)。将其视为代理用来跟踪工作过程中学习和决定的所有内容的笔记本。

### 什么应该包含在状态中？

对于每个数据项，问自己这些问题：

- **包含在状态中**：它需要在步骤之间持久化吗？如果是，它应该在状态中。
- **不存储**：你可以从其他数据派生它吗？如果是，在需要时计算它，而不是将其存储在状态中。

对于我们的电子邮件代理，我们需要跟踪：

- 原始邮件和发件人信息（无法重建）
- 分类结果（多个下游节点需要）
- 搜索结果和客户数据（重新获取成本高）
- 草拟回复（需要在审核过程中持久化）
- 执行元数据（用于调试和恢复）

### 保持状态原始，按需格式化提示

一个关键原则：状态应该存储原始数据，而不是格式化文本。在需要时在节点内格式化提示。

这种分离意味着：

- 不同节点可以根据需要以不同方式格式化相同数据
- 你可以更改提示模板而无需修改状态模式
- 调试更清晰 - 你可以确切地看到每个节点收到了什么数据
- 你的代理可以在不破坏现有状态的情况下发展

让我们定义我们的状态：

```python
from typing import TypedDict, Literal
# 定义电子邮件分类的结构
class EmailClassification(TypedDict):
    intent: Literal["question", "bug", "billing", "feature", "complex"]
    urgency: Literal["low", "medium", "high", "critical"]
    topic: str
    summary: str
class EmailAgentState(TypedDict):
    # 原始邮件数据
    email_content: str
    sender_email: str
    email_id: str
    # 分类结果
    classification: EmailClassification | None
    # 原始搜索/API结果
    search_results: list[str] | None  # 原始文档块列表
    customer_history: dict | None  # 来自CRM的原始客户数据
    # 生成的内容
    draft_response: str | None
    messages: list[str] | None
```

```typescript
import * as z from "zod";
// 定义电子邮件分类的结构
const EmailClassificationSchema = z.object({
  intent: z.enum(["question", "bug", "billing", "feature", "complex"]),
  urgency: z.enum(["low", "medium", "high", "critical"]),
  topic: z.string(),
  summary: z.string(),
});
const EmailAgentState = z.object({
  // 原始邮件数据
  emailContent: z.string(),
  senderEmail: z.string(),
  emailId: z.string(),
  // 分类结果
  classification: EmailClassificationSchema.optional(),
  // 原始搜索/API结果
  searchResults: z.array(z.string()).optional(),  // 原始文档块列表
  customerHistory: z.record(z.any()).optional(),  // 来自CRM的原始客户数据
  // 生成的内容
  responseText: z.string().optional(),
});
type EmailAgentStateType = z.infer<typeof EmailAgentState>;
type EmailClassificationType = z.infer<typeof EmailClassificationSchema>;
```

注意，状态只包含原始数据 - 没有提示模板，没有格式化字符串，没有指令。分类输出直接以单个字典形式从LLM存储。

## 步骤4：构建节点

现在我们将每个步骤实现为函数。LangGraph中的节点只是一个Python或JavaScript函数，它接受当前状态并返回对它的更新。

### 适当处理错误

不同的错误需要不同的处理策略：

| 错误类型 | 谁来修复 | 策略 | 何时使用 |
| --- | --- | --- | --- |
| 瞬态错误（网络问题、速率限制） | 系统（自动） | 重试策略 | 通常在重试后解决的临时故障 |
| LLM可恢复错误（工具故障、解析问题） | LLM | 在状态中存储错误并循环返回 | LLM可以看到错误并调整其方法 |
| 用户可修复错误（缺少信息、不明确的指令） | 人类 | 使用`interrupt()`暂停 | 需要用户输入才能继续 |
| 意外错误 | 开发者 | 让它们冒泡 | 需要调试的未知问题 |

#### 瞬态错误

添加重试策略以自动重试网络问题和速率限制：

```python
from langgraph.types import RetryPolicy
workflow.add_node(
    "search_documentation",
    search_documentation,
    retry_policy=RetryPolicy(max_attempts=3, initial_interval=1.0)
)
```

```typescript
import type { RetryPolicy } from "@langchain/langgraph";
workflow.addNode(
"searchDocumentation",
searchDocumentation,
{
    retryPolicy: { maxAttempts: 3, initialInterval: 1.0 },
},
);
```

#### LLM可恢复错误

在状态中存储错误并循环返回，以便LLM可以看到出了什么问题并再次尝试：

```python
from langgraph.types import Command
def execute_tool(state: State) -> Command[Literal["agent", "execute_tool"]]:
    try:
        result = run_tool(state['tool_call'])
        return Command(update={"tool_result": result}, goto="agent")
    except ToolError as e:
        # 让LLM看到出了什么问题并再次尝试
        return Command(
            update={"tool_result": f"工具错误: {str(e)}"},
            goto="agent"
        )
```

```typescript
import { Command } from "@langchain/langgraph";
async function executeTool(state: State) {
  try {
    const result = await runTool(state.toolCall);
    return new Command({
    update: { toolResult: result },
    goto: "agent",
    });
  } catch (error) {
    // 让LLM看到出了什么问题并再次尝试
    return new Command({
    update: { toolResult: `工具错误: ${error}` },
    goto: "agent",
    });
  }
}
```

#### 用户可修复错误

在需要时暂停并从用户那里收集信息（如账户ID、订单号或澄清）：

```python
from langgraph.types import Command
def lookup_customer_history(state: State) -> Command[Literal["draft_response"]]:
    if not state.get('customer_id'):
        user_input = interrupt({
            "message": "需要客户ID",
            "request": "请提供客户的账户ID以查询其订阅历史"
        })
        return Command(
            update={"customer_id": user_input['customer_id']},
            goto="lookup_customer_history"
        )
    # 现在继续查询
    customer_data = fetch_customer_history(state['customer_id'])
    return Command(update={"customer_history": customer_data}, goto="draft_response")
```

```typescript
import { Command, interrupt } from "@langchain/langgraph";
async function lookupCustomerHistory(state: State) {
  if (!state.customerId) {
    const userInput = interrupt({
    message: "需要客户ID",
    request: "请提供客户的账户ID以查询其订阅历史",
    });
    return new Command({
    update: { customerId: userInput.customerId },
    goto: "lookupCustomerHistory",
    });
  }
  // 现在继续查询
  const customerData = await fetchCustomerHistory(state.customerId);
  return new Command({
    update: { customerHistory: customerData },
    goto: "draftResponse",
  });
}
```

#### 意外错误

让它们冒泡以供调试。不要捕获你无法处理的内容：

```python
def send_reply(state: EmailAgentState):
    try:
        email_service.send(state["draft_response"])
    except Exception:
        raise  # 暴露意外错误
```

```typescript
async function sendReply(state: EmailAgentStateType): Promise<void> {
  try {
    await emailService.send(state.responseText);
  } catch (error) {
    throw error;  // 暴露意外错误
  }
}
```

### 实现我们的电子邮件代理节点

我们将每个节点实现为一个简单的函数。记住：节点接收状态，执行工作，并返回更新。

#### 读取和分类节点

```python
from typing import Literal
from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt, Command, RetryPolicy
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
llm = ChatOpenAI(model="gpt-4")
def read_email(state: EmailAgentState) -> dict:
    """提取和解析电子邮件内容"""
    # 在生产环境中，这将连接到您的电子邮件服务
    return {
        "messages": [HumanMessage(content=f"处理邮件: {state['email_content']}")]
    }
def classify_intent(state: EmailAgentState) -> Command[Literal["search_documentation", "human_review", "draft_response", "bug_tracking"]]:
    """使用LLM对电子邮件意图和紧急程度进行分类，然后相应地路由"""
    # 创建返回EmailClassification字典的结构化LLM
    structured_llm = llm.with_structured_output(EmailClassification)
    # 按需格式化提示，不存储在状态中
    classification_prompt = f"""
    分析这封客户电子邮件并进行分类：
    邮件: {state['email_content']}
    来自: {state['sender_email']}
    提供包括意图、紧急程度、主题和摘要的分类。
    """
    # 直接获取结构化响应作为字典
    classification = structured_llm.invoke(classification_prompt)
    # 根据分类确定下一个节点
    if classification['intent'] == 'billing' or classification['urgency'] == 'critical':
        goto = "human_review"
    elif classification['intent'] in ['question', 'feature']:
        goto = "search_documentation"
    elif classification['intent'] == 'bug':
        goto = "bug_tracking"
    else:
        goto = "draft_response"
    # 将分类作为单个字典存储在状态中
    return Command(
        update={"classification": classification},
        goto=goto
    )
```

```typescript
import { StateGraph, START, END, Command } from "@langchain/langgraph";
import { HumanMessage } from "@langchain/core/messages";
import { ChatAnthropic } from "@langchain/anthropic";
const llm = new ChatAnthropic({ model: "claude-sonnet-4-5-20250929" });
async function readEmail(state: EmailAgentStateType) {
  // 提取和解析电子邮件内容
  // 在生产环境中，这将连接到您的电子邮件服务
  console.log(`处理邮件: ${state.emailContent}`);
  return {};
}
async function classifyIntent(state: EmailAgentStateType) {
  // 使用LLM对电子邮件意图和紧急程度进行分类，然后相应地路由
  // 创建返回EmailClassification对象的结构化LLM
  const structuredLlm = llm.withStructuredOutput(EmailClassificationSchema);
  // 按需格式化提示，不存储在状态中
  const classificationPrompt = `
  分析这封客户电子邮件并进行分类：
  邮件: ${state.emailContent}
  来自: ${state.senderEmail}
  提供包括意图、紧急程度、主题和摘要的分类。
  `;
  // 直接获取结构化响应作为对象
  const classification = await structuredLlm.invoke(classificationPrompt);
  // 根据分类确定下一个节点
  let nextNode: "searchDocumentation" | "humanReview" | "draftResponse" | "bugTracking";
  if (classification.intent === "billing" || classification.urgency === "critical") {
    nextNode = "humanReview";
  } else if (classification.intent === "question" || classification.intent === "feature") {
    nextNode = "searchDocumentation";
  } else if (classification.intent === "bug") {
    nextNode = "bugTracking";
  } else {
    nextNode = "draftResponse";
  }
  // 将分类作为单个对象存储在状态中
  return new Command({
    update: { classification },
    goto: nextNode,
  });
}
```

#### 搜索和追踪节点

```python
def search_documentation(state: EmailAgentState) -> Command[Literal["draft_response"]]:
    """搜索知识库以获取相关信息"""
    # 从分类构建搜索查询
    classification = state.get('classification', {})
    query = f"{classification.get('intent', '')} {classification.get('topic', '')}"
    try:
        # 在此实现您的搜索逻辑
        # 存储原始搜索结果，而不是格式化文本
        search_results = [
            "通过设置 > 安全性 > 更改密码重置密码",
            "密码必须至少12个字符",
            "包含大写、小写、数字和符号"
        ]
    except SearchAPIError as e:
        # 对于可恢复的搜索错误，存储错误并继续
        search_results = [f"搜索暂时不可用: {str(e)}"]
    return Command(
        update={"search_results": search_results},  # 存储原始结果或错误
        goto="draft_response"
    )
def bug_tracking(state: EmailAgentState) -> Command[Literal["draft_response"]]:
    """创建或更新错误追踪工单"""
    # 在您的错误追踪系统中创建工单
    ticket_id = "BUG-12345"  # 将通过API创建
    return Command(
        update={
            "search_results": [f"错误工单 {ticket_id} 已创建"],
            "current_step": "bug_tracked"
        },
        goto="draft_response"
    )
```

```typescript
async function searchDocumentation(state: EmailAgentStateType) {
  // 搜索知识库以获取相关信息
  // 从分类构建搜索查询
  const classification = state.classification!;
  const query = `${classification.intent} ${classification.topic}`;
  let searchResults: string[];
  try {
    // 在此实现您的搜索逻辑
    // 存储原始搜索结果，而不是格式化文本
    searchResults = [
    "通过设置 > 安全性 > 更改密码重置密码",
    "密码必须至少12个字符",
    "包含大写、小写、数字和符号",
    ];
  } catch (error) {
    // 对于可恢复的搜索错误，存储错误并继续
    searchResults = [`搜索暂时不可用: ${error}`];
  }
  return new Command({
    update: { searchResults },  // 存储原始结果或错误
    goto: "draftResponse",
  });
}
async function bugTracking(state: EmailAgentStateType) {
  // 创建或更新错误追踪工单
  // 在您的错误追踪系统中创建工单
  const ticketId = "BUG-12345";  // 将通过API创建
  return new Command({
    update: { searchResults: [`错误工单 ${ticketId} 已创建`] },
    goto: "draftResponse",
  });
}
```

#### 回复节点

```python
def draft_response(state: EmailAgentState) -> Command[Literal["human_review", "send_reply"]]:
    """使用上下文生成回复并根据质量路由"""
    classification = state.get('classification', {})
    # 按需从原始状态数据格式化上下文
    context_sections = []
    if state.get('search_results'):
        # 为提示格式化搜索结果
        formatted_docs = "\n".join([f"- {doc}" for doc in state['search_results']])
        context_sections.append(f"相关文档:\n{formatted_docs}")
    if state.get('customer_history'):
        # 为提示格式化客户数据
        context_sections.append(f"客户等级: {state['customer_history'].get('tier', 'standard')}")
    # 使用格式化上下文构建提示
    draft_prompt = f"""
    起草对这封客户电子邮件的回复：
    {state['email_content']}
    邮件意图: {classification.get('intent', 'unknown')}
    紧急程度: {classification.get('urgency', 'medium')}
    {chr(10).join(context_sections)}
    指南：
    - 保持专业和有帮助
    - 解决他们的具体问题
    - 相关时使用提供的文档
    """
    response = llm.invoke(draft_prompt)
    # 根据紧急程度和意图确定是否需要人工审核
    needs_review = (
        classification.get('urgency') in ['high', 'critical'] or
        classification.get('intent') == 'complex'
    )
    # 路由到适当的下一个节点
    goto = "human_review" if needs_review else "send_reply"
    return Command(
        update={"draft_response": response.content},  # 只存储原始响应
        goto=goto
    )
def human_review(state: EmailAgentState) -> Command[Literal["send_reply", END]]:
    """使用interrupt暂停进行人工审核，并根据决策路由"""
    classification = state.get('classification', {})
    # interrupt() 必须首先出现 - 其之前的任何代码在恢复时都会重新运行
    human_decision = interrupt({
        "email_id": state.get('email_id',''),
        "original_email": state.get('email_content',''),
        "draft_response": state.get('draft_response',''),
        "urgency": classification.get('urgency'),
        "intent": classification.get('intent'),
        "action": "请审核并批准/编辑此回复"
    })
    # 现在处理人类的决策
    if human_decision.get("approved"):
        return Command(
            update={"draft_response": human_decision.get("edited_response", state.get('draft_response',''))},
            goto="send_reply"
        )
    else:
        # 拒绝意味着人类将直接处理
        return Command(update={}, goto=END)
def send_reply(state: EmailAgentState) -> dict:
    """发送电子邮件回复"""
    # 与电子邮件服务集成
    print(f"发送回复: {state['draft_response'][:100]}...")
    return {}
```

```typescript
import { Command, interrupt } from "@langchain/langgraph";
async function draftResponse(state: EmailAgentStateType) {
  // 使用上下文生成回复并根据质量路由
  const classification = state.classification!;
  // 按需从原始状态数据格式化上下文
  const contextSections: string[] = [];
  if (state.searchResults) {
    // 为提示格式化搜索结果
    const formattedDocs = state.searchResults.map(doc => `- ${doc}`).join("\n");
    contextSections.push(`相关文档:\n${formattedDocs}`);
  }
  if (state.customerHistory) {
    // 为提示格式化客户数据
    contextSections.push(`客户等级: ${state.customerHistory.tier ?? "standard"}`);
  }
  // 使用格式化上下文构建提示
  const draftPrompt = `
  起草对这封客户电子邮件的回复：
  ${state.emailContent}
  邮件意图: ${classification.intent}
  紧急程度: ${classification.urgency}
  ${contextSections.join("\n\n")}
  指南：
  - 保持专业和有帮助
  - 解决他们的具体问题
  - 相关时使用提供的文档
  `;
  const response = await llm.invoke([new HumanMessage(draftPrompt)]);
  // 根据紧急程度和意图确定是否需要人工审核
  const needsReview = (
      classification.urgency === "high" ||
      classification.urgency === "critical" ||
      classification.intent === "complex"
  );
  // 路由到适当的下一个节点
  const nextNode = needsReview ? "humanReview" : "sendReply";
  return new Command({
      update: { responseText: response.content.toString() },  // 只存储原始响应
      goto: nextNode,
  });
}
async function humanReview(state: EmailAgentStateType) {
  // 使用interrupt暂停进行人工审核，并根据决策路由
  const classification = state.classification!;
  // interrupt() 必须首先出现 - 其之前的任何代码在恢复时都会重新运行
  const humanDecision = interrupt({
      emailId: state.emailId,
      originalEmail: state.emailContent,
      draftResponse: state.responseText,
      urgency: classification.urgency,
      intent: classification.intent,
      action: "请审核并批准/编辑此回复",
  });
  // 现在处理人类的决策
  if (humanDecision.approved) {
      return new Command({
      update: { responseText: humanDecision.editedResponse || state.responseText },
      goto: "sendReply",
      });
  } else {
      // 拒绝意味着人类将直接处理
      return new Command({ update: {}, goto: END });
  }
}
async function sendReply(state: EmailAgentStateType): Promise<{}> {
  // 发送电子邮件回复
  // 与电子邮件服务集成
  console.log(`发送回复: ${state.responseText!?.substring(0, 100)}...`);
  return {};
}
```

## 步骤5：连接在一起

现在我们将节点连接成一个工作图。由于我们的节点处理自己的路由决策，我们只需要几个必要的边。

要使用`interrupt()`启用[人机协作](interrupts.html)，我们需要使用[检查点](persistence.html)进行编译，以在运行之间保存状态：

### 图编译代码

```python
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import RetryPolicy
# 创建图
workflow = StateGraph(EmailAgentState)
# 添加带有适当错误处理的节点
workflow.add_node("read_email", read_email)
workflow.add_node("classify_intent", classify_intent)
# 为可能有瞬态故障的节点添加重试策略
workflow.add_node(
    "search_documentation",
    search_documentation,
    retry_policy=RetryPolicy(max_attempts=3)
)
workflow.add_node("bug_tracking", bug_tracking)
workflow.add_node("draft_response", draft_response)
workflow.add_node("human_review", human_review)
workflow.add_node("send_reply", send_reply)
# 只添加必要的边
workflow.add_edge(START, "read_email")
workflow.add_edge("read_email", "classify_intent")
workflow.add_edge("send_reply", END)
# 使用检查点进行持久化编译
memory = MemorySaver()
app = workflow.compile(checkpointer=memory)
```

```typescript
import { MemorySaver, RetryPolicy } from "@langchain/langgraph";
// 创建图
const workflow = new StateGraph(EmailAgentState)
  // 添加带有适当错误处理的节点
  .addNode("readEmail", readEmail)
  .addNode("classifyIntent", classifyIntent)
  // 为可能有瞬态故障的节点添加重试策略
  .addNode(
    "searchDocumentation",
    searchDocumentation,
    { retryPolicy: { maxAttempts: 3 } },
  )
  .addNode("bugTracking", bugTracking)
  .addNode("draftResponse", draftResponse)
  .addNode("humanReview", humanReview)
  .addNode("sendReply", sendReply)
  // 只添加必要的边
  .addEdge(START, "readEmail")
  .addEdge("readEmail", "classifyIntent")
  .addEdge("sendReply", END);
// 使用检查点进行持久化编译
const memory = new MemorySaver();
const app = workflow.compile({ checkpointer: memory });
```

图结构最小化，因为路由通过节点内部的`Command`对象发生。每个节点通过类型提示（如`Command[Literal["node1", "node2"]]`）声明它可以去哪里，使流程明确且可追踪。

### 测试你的代理

让我们使用需要人工审核的紧急账单问题来运行我们的代理：

#### 测试代理

```python
# 使用紧急账单问题测试
initial_state = {
    "email_content": "我的订阅被重复收费了！这很紧急！",
    "sender_email": "customer@example.com",
    "email_id": "email_123",
    "messages": []
}
# 使用thread_id进行持久化运行
config = {"configurable": {"thread_id": "customer_123"}}
result = app.invoke(initial_state, config)
# 图将在human_review处暂停
print(f"草稿准备审核: {result['draft_response'][:100]}...")
# 准备好后，提供人工输入以恢复
from langgraph.types import Command
human_response = Command(
    resume={
        "approved": True,
        "edited_response": "我们真诚地为重复收费道歉。我已立即启动退款程序..."
    }
)
# 恢复执行
final_result = app.invoke(human_response, config)
print("电子邮件发送成功！")
```

```typescript
// 使用紧急账单问题测试
const initialState: EmailAgentStateType = {
  emailContent: "我的订阅被重复收费了！这很紧急！",
  senderEmail: "customer@example.com",
  emailId: "email_123"
};
// 使用thread_id进行持久化运行
const config = { configurable: { thread_id: "customer_123" } };
const result = await app.invoke(initialState, config);
// 图将在human_review处暂停
console.log(`草稿准备审核: ${result.responseText?.substring(0, 100)}...`);
// 准备好后，提供人工输入以恢复
import { Command } from "@langchain/langgraph";
const humanResponse = new Command({
  resume: {
    approved: true,
    editedResponse: "我们真诚地为重复收费道歉。我已立即启动退款程序...",
  }
});
// 恢复执行
const finalResult = await app.invoke(humanResponse, config);
console.log("电子邮件发送成功！");
```

当图遇到`interrupt()`时，它会暂停，将所有内容保存到检查点，并等待。它可以在几天后恢复，从它停止的确切位置继续。`thread_id`确保此对话的所有状态都一起保留。

## 总结和后续步骤

### 关键见解

构建这个电子邮件代理向我们展示了LangGraph的思考方式：

- **分解为离散步骤**：每个节点做好一件事。这种分解启用流式进度更新、可以暂停和恢复的持久执行，以及清晰的调试，因为你可以检查步骤之间的状态。

- **状态是共享内存**：存储原始数据，而不是格式化文本。这让不同节点以不同方式使用相同信息。

- **节点是函数**：它们接收状态，执行工作，并返回更新。当它们需要做出路由决策时，它们指定状态更新和下一个目的地。

- **错误是流程的一部分**：瞬态故障获取重试，LLM可恢复错误带有上下文循环返回，用户可修复问题暂停等待输入，意外错误冒泡供调试。

- **人类输入是一等公民**：`interrupt()`函数无限期暂停执行，保存所有状态，并在提供输入时从停止的确切位置恢复。当与节点中的其他操作结合时，它必须首先出现。

- **图结构自然出现**：你定义基本连接，节点处理自己的路由逻辑。这使控制流明确且可追踪 - 通过查看当前节点，你始终可以理解代理下一步将做什么。

### 高级考虑

#### 节点粒度权衡

你可能想知道：为什么不将"读取邮件"和"分类意图"合并为一个节点？

或者为什么要将"文档搜索"与"起草回复"分开？

答案涉及弹性和可观察性之间的权衡。

**弹性考虑**：LangGraph的[持久执行](durable-execution.html)在节点边界创建检查点。当工作流在中断或故障后恢复时，它从执行停止的节点开始。较小的节点意味着更频繁的检查点，这意味着如果出现问题，需要重复的工作更少。如果你将多个操作合并到一个大型节点中，接近末尾的故障意味着从头开始重新执行该节点中的所有内容。

我们为电子邮件代理选择这种分解的原因：

- **外部服务的隔离**：文档搜索和错误追踪是单独的节点，因为它们调用外部API。如果搜索服务速度慢或失败，我们希望将其与LLM调用隔离。我们可以为这些特定节点添加重试策略，而不影响其他节点。

- **中间可见性**：将"分类意图"作为自己的节点让我们在采取行动之前检查LLM的决定。这对于调试和监控很有价值—你可以确切地看到代理何时以及为什么路由到人工审核。

- **不同的故障模式**：LLM调用、数据库查询和电子邮件发送有不同的重试策略。单独的节点让你独立配置这些。

- **可重用性和测试**：较小的节点更容易独立测试并在其他工作流中重用。

另一种有效方法：你可以将"读取邮件"和"分类意图"合并为单个节点。你会失去在分类之前检查原始邮件的能力，并且在该节点中的任何故障时都会重复这两个操作。对于大多数应用程序，独立节点的可观察性和调试优势值得权衡。

应用级考虑：步骤2中的缓存讨论（是否缓存搜索结果）是应用级决策，而不是LangGraph框架功能。你基于特定要求在节点函数中实现缓存—LangGraph不规定这一点。

性能考虑：更多节点并不意味着更慢的执行。LangGraph默认在后台写入检查点（[异步持久化模式](durable-execution.html#durability-modes)），因此你的图继续运行而无需等待检查点完成。这意味着你可以获得频繁的检查点，而性能影响最小。如果需要，你可以调整此行为—使用"exit"模式仅在完成时检查点，或使用"sync"模式阻塞执行，直到每个检查点都写入。

### 下一步去哪里

这是使用LangGraph构建代理的思考过程的介绍。你可以使用以下内容扩展这个基础：

- **人机协作模式**：学习如何在执行前添加工具批准、批量批准和其他模式

- **子图**：为复杂的多步操作创建子图

- **流式传输**：添加流式传输以向用户显示实时进度

- **可观察性**：使用LangSmith添加可观察性以进行调试和监控

- **工具集成**：集成更多工具进行网络搜索、数据库查询和API调用

- **重试逻辑**：使用指数退避实现失败操作的重试逻辑