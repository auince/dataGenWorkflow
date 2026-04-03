# 长期记忆

深度Agent带有一个本地文件系统来卸载内存。该文件系统存储在状态中，因此**对于单个线程是短暂的**——当对话结束时，文件将丢失。

您可以通过提供 LangGraph `Store` 并设置 `use_longterm_memory=True` 来为深度Agent扩展**长期记忆**。这可以实现跨线程和对话的持久存储。

## 设置

```python
from deepagents import create_deep_agent
from langgraph.store.memory import InMemoryStore
store = InMemoryStore()  # 或任何其他 Store 对象
agent = create_deep_agent(
    store=store,
    use_longterm_memory=True
)
```

```typescript
// TODO: 添加 JS 实现
```

## 工作原理

启用长期记忆后，深度Agent会维护**两个独立的文件系统**：

### 1. 短期（瞬态）文件系统

*   存储在Agent的状态中
*   仅在单个线程内持久存在
*   线程结束时文件会丢失
*   通过标准路径访问：`/notes.txt`

### 2. 长期（持久）文件系统

*   存储在 LangGraph Store 中
*   在所有线程和对话中持久存在
*   文件无限期保留
*   通过特殊前缀访问：`/memories/notes.txt`

## /memories/ 路径约定

**长期记忆的关键是 `/memories/` 路径前缀：**

*   路径以 `/memories/` 开头的文件存储在 Store 中（持久）
*   没有此前缀的文件保留在瞬态中
*   所有文件系统工具（`ls`、`read_file`、`write_file`、`edit_file`）都适用于这两种文件

```python
# 瞬态文件（线程结束后丢失）
agent.invoke({
    "messages": [{"role": "user", "content": "将草稿写入 /draft.txt"}]
})
# 持久文件（跨线程保留）
agent.invoke({
    "messages": [{"role": "user", "content": "将最终报告保存到 /memories/report.txt"}]
})
```

```typescript
// TODO: 添加 JS 实现
```

## 跨线程持久性

`/memories/` 中的文件可以从任何线程访问：

```python
import uuid
# 线程 1：写入长期记忆
config1 = {"configurable": {"thread_id": str(uuid.uuid4())}}
agent.invoke({
    "messages": [{"role": "user", "content": "将我的偏好保存到 /memories/preferences.txt"}]
}, config=config1)
# 线程 2：从长期记忆中读取（不同的对话！）
config2 = {"configurable": {"thread_id": str(uuid.uuid4())}}
agent.invoke({
    "messages": [{"role": "user", "content": "我的偏好是什么？"}]
}, config=config2)
# Agent可以从第一个线程读取 /memories/preferences.txt
```

```typescript
// TODO: 添加 JS 实现
```

## 用例

### 用户偏好

存储跨会话持久存在的用户偏好：

```python
agent = create_deep_agent(
    store=store,
    use_longterm_memory=True,
    system_prompt="""当用户告诉您他们的偏好时，请将其保存到
    /memories/user_preferences.txt，以便您在将来的对话中记住它们。"""
)
```

```typescript
// TODO: 添加 JS 实现
```

### 自我完善的说明

Agent可以根据反馈更新自己的说明：

```python
agent = create_deep_agent(
    store=store,
    use_longterm_memory=True,
    system_prompt="""您在 /memories/instructions.txt 有一个包含其他
    说明和偏好的文件。
    在对话开始时阅读此文件以了解用户偏好。
    当用户提供诸如“请总是执行 X”或“我更喜欢 Y”之类的反馈时，
    使用 edit_file 工具更新 /memories/instructions.txt。"""
)
```

```typescript
// TODO: 添加 JS 实现
```

随着时间的推移，说明文件会累积用户偏好，帮助Agent改进。

### 知识库

在多个对话中积累知识：

```python
# 对话 1：了解一个项目
agent.invoke({
    "messages": [{"role": "user", "content": "我们正在使用 React 构建一个 Web 应用程序。保存项目说明。"}]
})
# 对话 2：使用该知识
agent.invoke({
    "messages": [{"role": "user", "content": "我们正在使用什么框架？"}]
})
# Agent从上一个对话中读取 /memories/project_notes.txt
```

```typescript
// TODO: 添加 JS 实现
```

### 研究项目

跨会话维护研究状态：

```python
research_agent = create_deep_agent(
    store=store,
    use_longterm_memory=True,
    system_prompt="""你是一名研究助理。
    将您的研究进度保存到 /memories/research/：
    - /memories/research/sources.txt - 找到的来源列表
    - /memories/research/notes.txt - 主要发现和笔记
    - /memories/research/report.md - 最终报告草稿
    这允许研究在多个会话中继续进行。"""
)
```

```typescript
// TODO: 添加 JS 实现
```

## Store 实现

任何 LangGraph `BaseStore` 实现都可以工作：

### InMemoryStore (开发)

适用于测试和开发，但数据在重启时会丢失：

```python
from langgraph.store.memory import InMemoryStore
store = InMemoryStore()
agent = create_deep_agent(store=store, use_longterm_memory=True)
```

```typescript
// TODO: 添加 JS 实现
```

### PostgresStore (生产)

对于生产环境，请使用持久性存储：

```python
from langgraph.store.postgres import PostgresStore
import os
store = PostgresStore(connection_string=os.environ["DATABASE_URL"])
agent = create_deep_agent(store=store, use_longterm_memory=True)
```

```typescript
// TODO: 添加 JS 实现
```

## 最佳实践

### 使用描述性路径

使用清晰的、分层的路径组织长期文件：

```python
# ✅ 好的：有组织且具有描述性
/memories/user_preferences/language.txt
/memories/projects/project_alpha/status.txt
/memories/research/quantum_computing/sources.txt
# ❌ 坏的：通用且无组织
/memories/temp.txt
/memories/data.txt
/memories/file1.txt
```

### 记录持久化的内容

在系统提示中，阐明何时使用长期存储与短期存储：

```python
system_prompt="""您可以访问两种类型的存储：
短期（没有 /memories/ 的路径）：
- 当前对话记录
- 临时草稿
- 草稿文件
长期（以 /memories/ 开头的路径）：
- 用户偏好和设置
- 已完成的报告和文档
- 应在对话之间持久存在的知识
- 项目状态和进度
对于应在本次对话之后保留的信息，请始终使用 /memories/。"""
```

### 按助手 ID 隔离存储

对于多租户应用程序，请提供 `assistant_id` 以隔离存储：

```python
config = {
    "configurable": {
        "thread_id": "thread-123",
    },
    "metadata": {
        "assistant_id": "user-456"  # 命名空间隔离
    }
}
agent.invoke({"messages": [...]}, config=config)
```

每个助手在 Store 中都有自己的命名空间，以防止交叉污染。

### 在生产中使用持久性存储

```python
# ❌ 仅限开发 - 数据在重启时丢失
store = InMemoryStore()
# ✅ 生产 - 数据持久存在
from langgraph.store.postgres import PostgresStore
store = PostgresStore(connection_string=os.environ["DATABASE_URL"])
```

## 列出文件

`ls` 工具显示来自两个文件系统的文件：

```python
agent.invoke({
    "messages": [{"role": "user", "content": "列出所有文件"}]
})
# 示例输出：
# 瞬态文件：
# - /draft.txt
# - /temp_notes.txt
#
# 长期文件：
# - /memories/user_preferences.txt
# - /memories/project_status.txt
```

来自 Store 的文件在列表中以 `/memories/` 为前缀。

## 限制

### Store 是必需的

启用长期记忆时必须提供 Store：

```python
# ❌ 这会报错
agent = create_deep_agent(use_longterm_memory=True)  # 缺少 store！
# ✅ 正确
agent = create_deep_agent(
    use_longterm_memory=True,
    store=InMemoryStore()
)
```

### Agent必须使用正确的路径

Agent必须学会使用 `/memories/` 前缀来实现持久性。系统提示会教导这一点，但Agent必须遵循说明。

### 没有自动清理

长期文件会无限期地持久存在。没有内置的 TTL 或自动清理功能。如果需要，您需要自己实现清理策略。