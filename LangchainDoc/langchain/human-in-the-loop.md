# 人机交互

**人机交互 (HITL)** 中间件允许您在**代理工具调用**中添加人工监督。

当模型提出一个可能需要人工审查的操作时——例如，写入文件或执行 SQL——该中间件可以暂停执行并等待决策。

它是通过对照一个**可配置的策略**检查每个工具调用来实现的。如果需要干预，中间件会发出一个[中断 (interrupt)](https://reference.langchain.com/python/langgraph/types/#langgraph.types.interrupt) 来停止执行。图的状态会使用 LangGraph 的[持久化层](../langgraph/persistence.html)进行保存，以便执行可以**安全地暂停并稍后恢复**。

随后的人工决策将决定接下来发生什么：该操作可以**按原样批准** (`approve`)、**修改后运行** (`edit`)，或**带反馈拒绝** (`reject`)。

## 中断决策类型 (Interrupt decision types)

中间件定义了三种内置的人类响应中断的方式：

| 决策类型 | 描述 | 示例用例 |
| :--- | :--- | :--- |
| `approve` | 该操作按原样批准并执行，不进行任何更改。 | 完全按照草稿发送电子邮件 |
| `edit` | 工具调用经过修改后执行。 | 在发送电子邮件前更改收件人 |
| `reject` | 工具调用被拒绝，并将解释添加到对话中。 | 拒绝电子邮件草稿并解释如何重写 |

每种工具可用的决策类型取决于您在 `interrupt_on` 中配置的策略。

当多个工具调用同时暂停时，每个操作都需要单独的决策。决策必须以与操作在中断请求中出现的**相同顺序**提供。

> **提示：**
> 在**编辑**工具参数时，请保守地进行更改。对原始参数进行重大修改可能会导致模型重新评估其方法，并可能多次执行工具或采取意外操作。

## 配置中断 (Configuring interrupts)

要使用 **HITL**，请在创建代理时将该中间件添加到代理的 `middleware` 列表中。

您需要通过一个映射进行配置，该映射将**工具操作**映射到**允许的决策类型**。当工具调用与映射中的操作匹配时，中间件将中断执行。

```python
from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware # [!code highlight]
from langgraph.checkpoint.memory import InMemorySaver # [!code highlight]
agent = create_agent(
    model="openai:gpt-4o",
    tools=[write_file_tool, execute_sql_tool, read_data_tool],
    middleware=[
        HumanInTheLoopMiddleware( # [!code highlight]
            interrupt_on={
                "write_file": True,  # 允许所有决策（批准、编辑、拒绝）
                "execute_sql": {"allowed_decisions": ["approve", "reject"]},  # 不允许编辑
                # 安全操作，无需批准
                "read_data": False,
            },
            # 中断消息的前缀 - 与工具名称和参数结合形成完整消息
            # 例如, "Tool execution pending approval: execute_sql with query='DELETE FROM...'"
            # 单个工具可以通过在其中断配置中指定 "description" 来覆盖此项
            description_prefix="Tool execution pending approval",
        ),
    ],
    # 人在回路需要检查点来处理中断。
    # 在生产环境中，请使用持久性检查点，如 AsyncPostgresSaver。
    checkpointer=InMemorySaver(),  # [!code highlight]
)
```

> **信息：**
>
> 您**必须**配置一个检查点来在中断时持久化图状态。
>
> 在生产环境中，请使用持久性检查点，如 [`AsyncPostgresSaver`](https://langchain-doc.cn/v1/python/langchain/[https:/reference.langchain.com/python/langgraph/checkpoints/#langgraph.checkpoint.postgres.aio.AsyncPostgresSaver](https://reference.langchain.com/python/langgraph/checkpoints/#langgraph.checkpoint.postgres.aio.AsyncPostgresSaver))。对于测试或原型设计，请使用 [`InMemorySaver`](https://langchain-doc.cn/v1/python/langchain/[https:/reference.langchain.com/python/langgraph/checkpoints/#langgraph.checkpoint.memory.InMemorySaver](https://reference.langchain.com/python/langgraph/checkpoints/#langgraph.checkpoint.memory.InMemorySaver))。
>
> 在调用代理时，请传入一个包含**线程 ID** 的 `config`，以将执行与对话线程关联。
>
> 详情请参阅 [LangGraph 中断文档](../langgraph/interrupts.html)。

## 响应中断 (Responding to interrupts)

当您调用代理时，它会运行直到完成或触发中断。当工具调用与您在 `interrupt_on` 中配置的策略匹配时，就会触发中断。在这种情况下，调用结果将包含一个 `__interrupt__` 字段，其中包含需要审查的操作。然后，您可以将这些操作呈现给审阅者，并在提供决策后恢复执行。

```python
from langgraph.types import Command
# 人在回路利用 LangGraph 的持久化层。
# 您必须提供一个线程 ID (thread ID) 以将执行与对话线程关联起来，
# 从而使对话能够暂停和恢复（这对于人工审查是必需的）。
config = {"configurable": {"thread_id": "some_id"}} # [!code highlight]
# 运行图直到遇到中断。
result = agent.invoke(
    {
        "messages": [
            {
                "role": "user",
                "content": "Delete old records from the database",
            }
        ]
    },
    config=config # [!code highlight]
)
# 中断包含完整的 HITL 请求，带有 action_requests 和 review_configs
print(result['__interrupt__'])
# > [
# >     Interrupt(
# >         value={
# >           'action_requests': [
# >               {
# >                   'name': 'execute_sql',
# >                   'arguments': {'query': 'DELETE FROM records WHERE created_at < NOW() - INTERVAL \'30 days\';'},
# >                   'description': 'Tool execution pending approval\n\nTool: execute_sql\nArgs: {...}'
# >               }
# >            ],
# >            'review_configs': [
# >               {
# >                    'action_name': 'execute_sql',
# >                    'allowed_decisions': ['approve', 'reject']
# >               }
# >            ]
# >         }
# >     )
# > ]
# 以批准决策恢复
agent.invoke(
    Command( # [!code highlight]
        resume={"decisions": [{"type": "approve"}]}  # 或 "edit", "reject" [!code highlight]
    ), # [!code highlight]
    config=config # 相同的线程 ID 以恢复暂停的对话
)
```

### 决策类型 (Decision types)

#### ✅ `approve`

使用 `approve` 来按原样批准工具调用并执行它，不进行任何更改。

```python
agent.invoke(
    Command(
        # 决策以列表形式提供，每个待审查操作一个。
        # 决策的顺序必须与
        # `__interrupt__` 请求中列出的操作顺序匹配。
        resume={
            "decisions": [
                {
                    "type": "approve",
                }
            ]
        }
    ),
    config=config  # 相同的线程 ID 以恢复暂停的对话
)
```

#### ✏️ `edit`

使用 `edit` 来在执行前修改工具调用。提供包含新的工具名称和参数的已编辑操作。

```python
agent.invoke(
    Command(
        # 决策以列表形式提供，每个待审查操作一个。
        # 决策的顺序必须与
        # `__interrupt__` 请求中列出的操作顺序匹配。
        resume={
            "decisions": [
                {
                    "type": "edit",
                    # 包含工具名称和参数的已编辑操作
                    "edited_action": {
                        # 要调用的工具名称。
                        # 通常与原始操作相同。
                        "name": "new_tool_name",
                        # 传递给工具的参数。
                        "args": {"key1": "new_value", "key2": "original_value"},
                    }
                }
            ]
        }
    ),
    config=config  # 相同的线程 ID 以恢复暂停的对话
)
```

> **提示：**
> 在**编辑**工具参数时，请保守地进行更改。对原始参数进行重大修改可能会导致模型重新评估其方法，并可能多次执行工具或采取意外操作。

#### ❌ `reject`

使用 `reject` 来拒绝工具调用并提供反馈而不是执行。

```python
agent.invoke(
    Command(
        # 决策以列表形式提供，每个待审查操作一个。
        # 决策的顺序必须与
        # `__interrupt__` 请求中列出的操作顺序匹配。
        resume={
            "decisions": [
                {
                    "type": "reject",
                    # 关于操作为何被拒绝的解释
                    "message": "No, this is wrong because ..., instead do this ...",
                }
            ]
        }
    ),
    config=config  # 相同的线程 ID 以恢复暂停的对话
)
```

`message` 会作为反馈添加到对话中，以帮助代理理解操作被拒绝的原因以及它应该做什么。

##### 多个决策 (Multiple decisions)

当有多个操作待审查时，请按它们出现在中断中的**相同顺序**为每个操作提供一个决策：

```python
{
    "decisions": [
        {"type": "approve"},
        {
            "type": "edit",
            "edited_action": {
                "name": "tool_name",
                "args": {"param": "new_value"}
            }
        },
        {
            "type": "reject",
            "message": "This action is not allowed"
        }
    ]
}
```

## 执行生命周期 (Execution lifecycle)

中间件定义了一个 `after_model` 钩子，它在模型生成响应之后但在执行任何工具调用之前运行：

1.  代理调用模型以生成响应。
2.  中间件检查响应中的工具调用。
3.  如果任何调用需要人工输入，中间件会构建一个包含 `action_requests` 和 `review_configs` 的 `HITLRequest`，并调用 [interrupt](https://reference.langchain.com/python/langgraph/types/#langgraph.types.interrupt)。
4.  代理等待人工决策。
5.  根据 `HITLResponse` 决策，中间件执行已批准或已编辑的调用，为已拒绝的调用合成 [ToolMessage](https://reference.langchain.com/python/langchain/messages/#langchain.messages.ToolMessage)，并恢复执行。

## 自定义 HITL 逻辑 (Custom HITL logic)

对于更专业的工作流程，您可以直接使用 [interrupt](https://reference.langchain.com/python/langgraph/types/#langgraph.types.interrupt) 原语和 [middleware](middleware.html) 抽象来构建**自定义 HITL 逻辑**。

请回顾上方的[执行生命周期](#执行生命周期-execution-lifecycle)，以了解如何将中断集成到代理的操作中。