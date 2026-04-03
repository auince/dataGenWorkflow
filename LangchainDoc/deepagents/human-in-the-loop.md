# 人机交互

某些工具操作可能很敏感，执行前需要人工批准。深度Agent通过 LangGraph 的中断功能支持人机交互工作流。您可以使用 `interrupt_on` 参数配置哪些工具需要批准。

## 基本配置

`interrupt_on` 参数接受一个将工具名称映射到中断配置的字典。每个工具可以配置为：

- **`True`**: 启用具有默认行为（允许批准、编辑、拒绝）的中断
- **`False`**: 禁用此工具的中断
- **`{"allowed_decisions": [...]}`**: 具有特定允许决策的自定义配置

```python
from langchain_core.tools import tool
from deepagents import create_deep_agent
from langgraph.checkpoint.memory import MemorySaver

@tool
def delete_file(path: str) -> str:
    """从文件系统中删除文件。"""
    return f"已删除 {path}"

@tool
def read_file(path: str) -> str:
    """从文件系统中读取文件。"""
    return f" {path} 的内容"

@tool
def send_email(to: str, subject: str, body: str) -> str:
    """发送电子邮件。"""
    return f"已发送邮件至 {to}"

# 人机交互需要检查点
checkpointer = MemorySaver()
agent = create_deep_agent(
    model="claude-sonnet-4-5-20250929",
    tools=[delete_file, read_file, send_email],
    interrupt_on={
        "delete_file": True,  # 默认：批准、编辑、拒绝
        "read_file": False,   # 无需中断
        "send_email": {"allowed_decisions": ["approve", "reject"]},  # 禁止编辑
    },
    checkpointer=checkpointer  # 必需！
)
```

```typescript
// TODO: 添加 JS 实现
```

## 决策类型

`allowed_decisions` 列表控制了人类在审查工具调用时可以采取的操作：

- **`"approve"`**: 使用Agent提出的原始参数执行工具
- **`"edit"`**: 在执行前修改工具参数
- **`"reject"`**: 完全跳过执行此工具调用

您可以为每个工具自定义可用的决策：

```python
interrupt_on = {
    # 敏感操作：允许所有选项
    "delete_file": {"allowed_decisions": ["approve", "edit", "reject"]},
    # 中等风险：仅允许批准或拒绝
    "write_file": {"allowed_decisions": ["approve", "reject"]},
    # 必须批准（不允许拒绝）
    "critical_operation": {"allowed_decisions": ["approve"]},
}
```

```typescript
// TODO: 添加 JS 实现
```

## 处理中断

当触发中断时，Agent会暂停执行并返回控制权。检查结果中的中断并相应地处理它们。

```python
import uuid
from langgraph.types import Command

# 创建带有 thread_id 的配置以实现状态持久化
config = {"configurable": {"thread_id": str(uuid.uuid4())}}

# 调用Agent
result = agent.invoke({
    "messages": [{"role": "user", "content": "删除文件 temp.txt"}]
}, config=config)

# 检查执行是否被中断
if result.get("__interrupt__"):
    # 提取中断信息
    interrupts = result["__interrupt__"][0].value
    action_requests = interrupts["action_requests"]
    review_configs = interrupts["review_configs"]

    # 创建从工具名称到审查配置的查找映射
    config_map = {cfg["action_name"]: cfg for cfg in review_configs}

    # 向用户显示待处理的操作
    for action in action_requests:
        review_config = config_map[action["name"]]
        print(f"工具: {action['name']}")
        print(f"参数: {action['args']}")
        print(f"允许的决策: {review_config['allowed_decisions']}")

    # 获取用户决策（每个 action_request 一个，按顺序）
    decisions = [
        {"type": "approve"}  # 用户批准了删除
    ]

    # 使用决策恢复执行
    result = agent.invoke(
        Command(resume={"decisions": decisions}),
        config=config  # 必须使用相同的配置！
    )

# 处理最终结果
print(result["messages"][-1]["content"])
```

```typescript
// TODO: 添加 JS 实现
```

## 多个工具调用

当Agent调用多个需要批准的工具时，所有中断都会被批处理到单个中断中。您必须按顺序为每个中断提供决策。

```python
config = {"configurable": {"thread_id": str(uuid.uuid4())}}
result = agent.invoke({
    "messages": [{
        "role": "user",
        "content": "删除 temp.txt 并向 admin@example.com 发送电子邮件"
    }]
}, config=config)

if result.get("__interrupt__"):
    interrupts = result["__interrupt__"][0].value
    action_requests = interrupts["action_requests"]

    # 两个工具需要批准
    assert len(action_requests) == 2

    # 按与 action_requests 相同的顺序提供决策
    decisions = [
        {"type": "approve"},  # 第一个工具：delete_file
        {"type": "reject"}    # 第二个工具：send_email
    ]

    result = agent.invoke(
        Command(resume={"decisions": decisions}),
        config=config
    )
```

```typescript
// TODO: 添加 JS 实现
```

## 编辑工具参数

当 `"edit"` 在允许的决策中时，您可以在执行前修改工具参数：

```python
if result.get("__interrupt__"):
    interrupts = result["__interrupt__"][0].value
    action_request = interrupts["action_requests"][0]

    # Agent的原始参数
    print(action_request["args"])  # {"to": "everyone@company.com", ...}

    # 用户决定编辑收件人
    decisions = [{
        "type": "edit",
        "edited_action": {
            "name": action_request["name"],  # 必须包含工具名称
            "args": {"to": "team@company.com", "subject": "...", "body": "..."}
        }
    }]

    result = agent.invoke(
        Command(resume={"decisions": decisions}),
        config=config
    )
```

```typescript
// TODO: 添加 JS 实现
```

## 子Agent中断

每个子Agent都可以有自己的 `interrupt_on` 配置，该配置会覆盖主Agent的设置：

```python
agent = create_deep_agent(
    tools=[delete_file, read_file],
    interrupt_on={
        "delete_file": True,
        "read_file": False,
    },
    subagents=[{
        "name": "file-manager",
        "description": "管理文件操作",
        "system_prompt": "你是一个文件管理助手。",
        "tools": [delete_file, read_file],
        "interrupt_on": {
            # 覆盖：在此子Agent中要求批准读取
            "delete_file": True,
            "read_file": True,  # 与主Agent不同！
        }
    }],
    checkpointer=checkpointer
)
```

```typescript
// TODO: 添加 JS 实现
```

当子Agent触发中断时，处理方式是相同的——检查 `__interrupt__` 并使用 `Command` 恢复。

## 最佳实践

### 始终使用检查点

人机交互需要一个检查点来在中断和恢复之间持久化Agent状态：

```python
from langgraph.checkpoint.memory import MemorySaver

checkpointer = MemorySaver()
agent = create_deep_agent(
    tools=[...],
    interrupt_on={...},
    checkpointer=checkpointer  # HITL 必需
)
```

### 使用相同的线程 ID

恢复时，您必须使用具有相同 `thread_id` 的相同配置：

```python
# 第一次调用
config = {"configurable": {"thread_id": "my-thread"}}
result = agent.invoke(input, config=config)

# 恢复（使用相同的配置）
result = agent.invoke(Command(resume={...}), config=config)
```

### 将决策顺序与操作匹配

决策列表必须与 `action_requests` 的顺序匹配：

```python
if result.get("__interrupt__"):
    interrupts = result["__interrupt__"][0].value
    action_requests = interrupts["action_requests"]

    # 为每个操作创建一个决策，按顺序
    decisions = []
    for action in action_requests:
        decision = get_user_decision(action)  # 您的逻辑
        decisions.append(decision)

    result = agent.invoke(
        Command(resume={"decisions": decisions}),
        config=config
    )
```

### 根据风险定制配置

根据风险级别配置不同的工具：

```python
interrupt_on = {
    # 高风险：完全控制（批准、编辑、拒绝）
    "delete_file": {"allowed_decisions": ["approve", "edit", "reject"]},
    "send_email": {"allowed_decisions": ["approve", "edit", "reject"]},
    # 中等风险：不允许编辑
    "write_file": {"allowed_decisions": ["approve", "reject"]},
    # 低风险：无中断
    "read_file": False,
    "list_files": False,
}