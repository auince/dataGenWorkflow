# 功能API概述

**功能API**允许您在对现有代码进行最少更改的情况下，向应用程序添加LangGraph的关键功能——[持久化](persistence.html)、[内存](add-memory.html)、[人机协作](interrupts.html)和[流式传输](streaming.html)。

它设计用于将这些功能集成到可能使用标准语言原语进行分支和控制流的现有代码中，例如`if`语句、`for`循环和函数调用。与许多要求将代码重构为显式管道或DAG的数据编排框架不同，功能API允许您整合这些功能而无需强制执行严格的执行模型。

功能API使用两个关键构建块：

```python
# Python
* **`@entrypoint`** – 将函数标记为工作流的起始点，封装逻辑并管理执行流程，包括处理长时间运行的任务和中断。
* **`@task`** – 表示一个离散的工作单元，如API调用或数据处理步骤，可以在入口点内异步执行。任务返回一个类似future的对象，可以同步等待或解析。
```

```js
// JavaScript
* **`entrypoint`** – 入口点封装工作流逻辑并管理执行流程，包括处理长时间运行的任务和中断。
* **`task`** – 表示一个离散的工作单元，如API调用或数据处理步骤，可以在入口点内异步执行。任务返回一个类似future的对象，可以同步等待或解析。
```

这提供了一个最小化的抽象，用于构建具有状态管理和流式传输的工作流。

提示：有关如何使用功能API的信息，请参阅[使用功能API](https://langchain-doc.cn/v1/python/langgraph/use-functional-api)。

## 功能API与图API的比较

对于更喜欢声明式方法的用户，LangGraph的[图API](https://langchain-doc.cn/v1/python/langgraph/graph-api)允许您使用图范例定义工作流。两个API共享相同的底层运行时，因此您可以在同一应用程序中一起使用它们。

以下是一些关键差异：

* **控制流**：功能API不需要考虑图结构。您可以使用标准Python构造来定义工作流。这通常会减少您需要编写的代码量。
* **短期记忆**：**图API**需要声明[**状态**](https://langchain-doc.cn/v1/python/langgraph/graph-api#state)，并且可能需要定义[**reducers**](https://langchain-doc.cn/v1/python/langgraph/graph-api#reducers)来管理图状态的更新。`@entrypoint`和`@tasks`不需要显式的状态管理，因为它们的状态作用域限定在函数内，不会跨函数共享。
* **检查点**：两个API都生成并使用检查点。在**图API**中，每个[superstep](https://langchain-doc.cn/v1/python/langgraph/graph-api)后都会生成一个新的检查点。在**功能API**中，当任务执行时，它们的结果会保存到与给定入口点关联的现有检查点中，而不是创建新的检查点。
* **可视化**：图API使工作流可以轻松可视化为图表，这对于调试、理解工作流和与他人共享非常有用。功能API不支持可视化，因为图表是在运行时动态生成的。

## 示例

下面我们展示一个简单的应用程序，它编写一篇文章并[中断](interrupts.html)以请求人工审核。

### Python 示例

```python
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.func import entrypoint, task
from langgraph.types import interrupt
@task
def write_essay(topic: str) -> str:
    """Write an essay about the given topic."""
    time.sleep(1) # A placeholder for a long-running task.
    return f"An essay about topic: {topic}"
@entrypoint(checkpointer=InMemorySaver())
def workflow(topic: str) -> dict:
    """A simple workflow that writes an essay and asks for a review."""
    essay = write_essay("cat").result()
    is_approved = interrupt({
        # Any json-serializable payload provided to interrupt as argument.
        # It will be surfaced on the client side as an Interrupt when streaming data
        # from the workflow.
        "essay": essay, # The essay we want reviewed.
        # We can add any additional information that we need.
        # For example, introduce a key called "action" with some instructions.
        "action": "Please approve/reject the essay",
    })
    return {
        "essay": essay, # The essay that was generated
        "is_approved": is_approved, # Response from HIL
    }
```

### JavaScript 示例

```typescript
import { MemorySaver, entrypoint, task, interrupt } from "@langchain/langgraph";
const writeEssay = task("writeEssay", async (topic: string) => {
  // A placeholder for a long-running task.
  await new Promise((resolve) => setTimeout(resolve, 1000));
  return `An essay about topic: ${topic}`;
});
const workflow = entrypoint(
  { checkpointer: new MemorySaver(), name: "workflow" },
  async (topic: string) => {
    const essay = await writeEssay(topic);
    const isApproved = interrupt({
      // Any json-serializable payload provided to interrupt as argument.
      // It will be surfaced on the client side as an Interrupt when streaming data
      // from the workflow.
      essay, // The essay we want reviewed.
      // We can add any additional information that we need.
      // For example, introduce a key called "action" with some instructions.
      action: "Please approve/reject the essay",
    });
    return {
      essay, // The essay that was generated
      isApproved, // Response from HIL
    };
  }
);
```

### 详细解释

此工作流将撰写一篇关于"cat"主题的文章，然后暂停以获取人工审核。工作流可以中断无限长的时间，直到提供审核。

当工作流恢复时，它从头开始执行，但由于`writeEssay`任务的结果已经保存，任务结果将从检查点加载而不是重新计算。

#### Python 详细示例

```python
import time
import uuid
from langgraph.func import entrypoint, task
from langgraph.types import interrupt
from langgraph.checkpoint.memory import InMemorySaver
@task
def write_essay(topic: str) -> str:
    """Write an essay about the given topic."""
    time.sleep(1)  # This is a placeholder for a long-running task.
    return f"An essay about topic: {topic}"
@entrypoint(checkpointer=InMemorySaver())
def workflow(topic: str) -> dict:
    """A simple workflow that writes an essay and asks for a review."""
    essay = write_essay("cat").result()
    is_approved = interrupt(
        {
            # Any json-serializable payload provided to interrupt as argument.
            # It will be surfaced on the client side as an Interrupt when streaming data
            # from the workflow.
            "essay": essay,  # The essay we want reviewed.
            # We can add any additional information that we need.
            # For example, introduce a key called "action" with some instructions.
            "action": "Please approve/reject the essay",
        }
    )
    return {
        "essay": essay,  # The essay that was generated
        "is_approved": is_approved,  # Response from HIL
    }
thread_id = str(uuid.uuid4())
config = {"configurable": {"thread_id": thread_id}}
for item in workflow.stream("cat", config):
    print(item)
# > {'write_essay': 'An essay about topic: cat'}
# > {
# >     '__interrupt__': (
# >        Interrupt(
# >            value={
# >                'essay': 'An essay about topic: cat',
# >                'action': 'Please approve/reject the essay'
# >            },
# >            id='b9b2b9d788f482663ced6dc755c9e981'
# >        ),
# >    )
# > }
```

文章已经写好并准备审核。一旦提供了审核，我们可以恢复工作流：

```python
from langgraph.types import Command
# Get review from a user (e.g., via a UI)
# In this case, we're using a bool, but this can be any json-serializable value.
human_review = True
for item in workflow.stream(Command(resume=human_review), config):
    print(item)
```

```pycon
{'workflow': {'essay': 'An essay about topic: cat', 'is_approved': False}}
```

工作流已完成，审核已添加到文章中。

#### JavaScript 详细示例

```typescript
import { v4 as uuidv4 } from "uuid";
import { MemorySaver, entrypoint, task, interrupt } from "@langchain/langgraph";
const writeEssay = task("writeEssay", async (topic: string) => {
  // This is a placeholder for a long-running task.
  await new Promise(resolve => setTimeout(resolve, 1000));
  return `An essay about topic: ${topic}`;
});
const workflow = entrypoint(
  { checkpointer: new MemorySaver(), name: "workflow" },
  async (topic: string) => {
    const essay = await writeEssay(topic);
    const isApproved = interrupt({
      // Any json-serializable payload provided to interrupt as argument.
      // It will be surfaced on the client side as an Interrupt when streaming data
      // from the workflow.
      essay, // The essay we want reviewed.
      // We can add any additional information that we need.
      // For example, introduce a key called "action" with some instructions.
      action: "Please approve/reject the essay",
    });
    return {
      essay, // The essay that was generated
      isApproved, // Response from HIL
    };
  }
);
const threadId = uuidv4();
const config = {
  configurable: {
    thread_id: threadId
  }
};
for await (const item of workflow.stream("cat", config)) {
  console.log(item);
}
```

```console
{ writeEssay: 'An essay about topic: cat' }
{
  __interrupt__: [{
    value: { essay: 'An essay about topic: cat', action: 'Please approve/reject the essay' },
    resumable: true,
    ns: ['workflow:f7b8508b-21c0-8b4c-5958-4e8de74d2684'],
    when: 'during'
  }]
}
```

文章已经写好并准备审核。一旦提供了审核，我们可以恢复工作流：

```typescript
import { Command } from "@langchain/langgraph";
// Get review from a user (e.g., via a UI)
// In this case, we're using a bool, but this can be any json-serializable value.
const humanReview = true;
for await (const item of workflow.stream(new Command({ resume: humanReview }), config)) {
  console.log(item);
}
```

```console
{ workflow: { essay: 'An essay about topic: cat', isApproved: true } }
```

工作流已完成，审核已添加到文章中。

## 入口点

```python
# Python
@entrypoint装饰器可用于从函数创建工作流。它封装工作流逻辑并管理执行流程，包括处理长时间运行的任务和[中断](/v1/python/langgraph/interrupts)。
```

```js
// JavaScript
entrypoint函数可用于从函数创建工作流。它封装工作流逻辑并管理执行流程，包括处理长时间运行的任务和[中断](/v1/python/langgraph/interrupts)。
```

### 定义

```python
# Python
**入口点**是通过使用`@entrypoint`装饰器装饰函数来定义的。
该函数**必须接受单个位置参数**，该参数用作工作流输入。如果需要传递多个数据，请使用字典作为第一个参数的输入类型。
使用`entrypoint`装饰函数会生成一个Pregel实例，该实例有助于管理工作流的执行（例如，处理流式传输、恢复和检查点）。
您通常需要向`@entrypoint`装饰器传递一个**检查点**，以启用持久化并使用诸如**人机协作**之类的功能。
同步版本：
```python
from langgraph.func import entrypoint
@entrypoint(checkpointer=checkpointer)
def my_workflow(some_input: dict) -> int:
    # some logic that may involve long-running tasks like API calls,
    # and may be interrupted for human-in-the-loop.
    ...
    return result
```

异步版本：

```python
from langgraph.func import entrypoint
@entrypoint(checkpointer=checkpointer)
async def my_workflow(some_input: dict) -> int:
    # some logic that may involve long-running tasks like API calls,
    # and may be interrupted for human-in-the-loop
    ...
    return result
```

```js
// JavaScript
**入口点**是通过调用带有配置和函数的`entrypoint`函数来定义的。
该函数**必须接受单个位置参数**，该参数用作工作流输入。如果需要传递多个数据，请使用对象作为第一个参数的输入类型。
使用函数创建入口点会生成一个工作流实例，该实例有助于管理工作流的执行（例如，处理流式传输、恢复和检查点）。
您通常需要向`entrypoint`函数传递一个**检查点**，以启用持久化并使用诸如**人机协作**之类的功能。
```typescript
import { entrypoint } from "@langchain/langgraph";
const myWorkflow = entrypoint(
  { checkpointer, name: "workflow" },
  async (someInput: Record<string, any>): Promise<number> => {
    // some logic that may involve long-running tasks like API calls,
    // and may be interrupted for human-in-the-loop
    return result;
  }
);
```

警告：**序列化**
入口点的**输入**和**输出**必须是JSON可序列化的，以支持检查点。请参阅[序列化](#serialization)部分了解更多详细信息。

```python
# Python
### 可注入参数
在声明`entrypoint`时，您可以请求访问将在运行时自动注入的其他参数。这些参数包括：
| 参数    | 描述                                                                                                                                                        |
| ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **previous** | 访问与给定线程的前一个`checkpoint`关联的状态。请参阅[short-term-memory](#short-term-memory)。                                      |
| **store**    | BaseStore的实例。对于[长期记忆](/v1/python/langgraph/use-functional-api#long-term-memory)很有用。                      |
| **writer**   | 用于在使用Async Python &lt; 3.11时访问StreamWriter。有关详细信息，请参阅[使用功能API的流式传输](/v1/python/langgraph/use-functional-api#streaming)。 |
| **config**   | 用于访问运行时配置。有关信息，请参阅[RunnableConfig](https://python.langchain.com/docs/concepts/runnables/#runnableconfig)。                  |
警告：使用适当的名称和类型注释声明参数。
请求可注入参数的示例：
```python
from langchain_core.runnables import RunnableConfig
from langgraph.func import entrypoint
from langgraph.store.base import BaseStore
from langgraph.store.memory import InMemoryStore
in_memory_store = InMemoryStore(...)  # An instance of InMemoryStore for long-term memory
@entrypoint(
    checkpointer=checkpointer,  # Specify the checkpointer
    store=in_memory_store  # Specify the store
)
def my_workflow(
    some_input: dict,  # The input (e.g., passed via `invoke`)
    *,
    previous: Any = None, # For short-term memory
    store: BaseStore,  # For long-term memory
    writer: StreamWriter,  # For streaming custom data
    config: RunnableConfig  # For accessing the configuration passed to the entrypoint
) -> ...:
```

### 执行

```python
# Python
使用[`@entrypoint`](#entrypoint)会产生一个Pregel对象，可以使用`invoke`、`ainvoke`、`stream`和`astream`方法执行。
同步调用：
```python
config = {
    "configurable": {
        "thread_id": "some_thread_id"
    }
}
my_workflow.invoke(some_input, config)  # Wait for the result synchronously
```

异步调用：

```python
config = {
    "configurable": {
        "thread_id": "some_thread_id"
    }
}
await my_workflow.ainvoke(some_input, config)  # Await result asynchronously
```

同步流式传输：

```python
config = {
    "configurable": {
        "thread_id": "some_thread_id"
    }
}
for chunk in my_workflow.stream(some_input, config):
    print(chunk)
```

异步流式传输：

```python
config = {
    "configurable": {
        "thread_id": "some_thread_id"
    }
}
async for chunk in my_workflow.astream(some_input, config):
    print(chunk)
```

```js
// JavaScript
使用[`entrypoint`](#entrypoint)函数将返回一个可以使用`invoke`和`stream`方法执行的对象。
调用：
```typescript
const config = {
  configurable: {
    thread_id: "some_thread_id"
  }
};
await myWorkflow.invoke(someInput, config); // Wait for the result
```

流式传输：

```typescript
const config = {
  configurable: {
    thread_id: "some_thread_id"
  }
};
for await (const chunk of myWorkflow.stream(someInput, config)) {
  console.log(chunk);
}
```

### 恢复

```python
# Python
在中断后恢复执行可以通过向Command原语传递**resume**值来完成。
同步调用恢复：
```python
from langgraph.types import Command
config = {
    "configurable": {
        "thread_id": "some_thread_id"
    }
}
my_workflow.invoke(Command(resume=some_resume_value), config)
```

异步调用恢复：

```python
from langgraph.types import Command
config = {
    "configurable": {
        "thread_id": "some_thread_id"
    }
}
await my_workflow.ainvoke(Command(resume=some_resume_value), config)
```

同步流式传输恢复：

```python
from langgraph.types import Command
config = {
    "configurable": {
        "thread_id": "some_thread_id"
    }
}
for chunk in my_workflow.stream(Command(resume=some_resume_value), config):
    print(chunk)
```

异步流式传输恢复：

```python
from langgraph.types import Command
config = {
    "configurable": {
        "thread_id": "some_thread_id"
    }
}
async for chunk in my_workflow.astream(Command(resume=some_resume_value), config):
    print(chunk)
```

```js
// JavaScript
在中断后恢复执行可以通过向Command原语传递**resume**值来完成。
调用恢复：
```typescript
import { Command } from "@langchain/langgraph";
const config = {
  configurable: {
    thread_id: "some_thread_id"
  }
};
await myWorkflow.invoke(new Command({ resume: someResumeValue }), config);
```

流式传输恢复：

```typescript
import { Command } from "@langchain/langgraph";
const config = {
  configurable: {
    thread_id: "some_thread_id"
  }
};
const stream = await myWorkflow.stream(
  new Command({ resume: someResumableValue }),
  config,
)
for await (const chunk of stream) {
  console.log(chunk);
}
```

```python
# Python
**错误后恢复**
要在错误后恢复，使用`None`和相同的**线程ID**（配置）运行`entrypoint`。
这假设底层**错误**已解决，并且执行可以成功继续。
同步调用恢复：
```python
config = {
    "configurable": {
        "thread_id": "some_thread_id"
    }
}
my_workflow.invoke(None, config)
```

异步调用恢复：

```python
config = {
    "configurable": {
        "thread_id": "some_thread_id"
    }
}
await my_workflow.ainvoke(None, config)
```

同步流式传输恢复：

```python
config = {
    "configurable": {
        "thread_id": "some_thread_id"
    }
}
for chunk in my_workflow.stream(None, config):
    print(chunk)
```

异步流式传输恢复：

```python
config = {
    "configurable": {
        "thread_id": "some_thread_id"
    }
}
async for chunk in my_workflow.astream(None, config):
    print(chunk)
```

```js
// JavaScript
**错误后恢复**
要在错误后恢复，使用`null`和相同的**线程ID**（配置）运行`entrypoint`。
这假设底层**错误**已解决，并且执行可以成功继续。
调用恢复：
```typescript
const config = {
  configurable: {
    thread_id: "some_thread_id"
  }
};
await myWorkflow.invoke(null, config);
```

流式传输恢复：

```typescript
const config = {
  configurable: {
    thread_id: "some_thread_id"
  }
};
for await (const chunk of myWorkflow.stream(null, config)) {
  console.log(chunk);
}
```

### 短期记忆
当使用`checkpointer`定义`entrypoint`时，它会在相同**线程ID**的连续调用之间存储信息在[检查点](/v1/python/langgraph/persistence#checkpoints)中。

```python
# Python
这允许使用`previous`参数访问前一次调用的状态。
默认情况下，`previous`参数是前一次调用的返回值。
```python
@entrypoint(checkpointer=checkpointer)
def my_workflow(number: int, *, previous: Any = None) -> int:
    previous = previous or 0
    return number + previous
config = {
    "configurable": {
        "thread_id": "some_thread_id"
    }
}
my_workflow.invoke(1, config)  # 1 (previous was None)
my_workflow.invoke(2, config)  # 3 (previous was 1 from the previous invocation)
```

```js
// JavaScript
这允许使用`getPreviousState`函数访问前一次调用的状态。
默认情况下，`getPreviousState`函数返回前一次调用的返回值。
```typescript
import { entrypoint, getPreviousState } from "@langchain/langgraph";
const myWorkflow = entrypoint(
  { checkpointer, name: "workflow" },
  async (number: number) => {
    const previous = getPreviousState<number>() ?? 0;
    return number + previous;
  }
);
const config = {
  configurable: {
    thread_id: "some_thread_id",
  },
};
await myWorkflow.invoke(1, config); // 1 (previous was undefined)
await myWorkflow.invoke(2, config); // 3 (previous was 1 from the previous invocation)
```

#### `entrypoint.final`

```python
# Python
entrypoint.final是一个特殊的原语，可以从入口点返回，并允许**解耦**在**检查点中保存的值**和**入口点的返回值**。
第一个值是入口点的返回值，第二个值是将保存在检查点中的值。类型注释是`entrypoint.final[return_type, save_type]`。
```python
@entrypoint(checkpointer=checkpointer)
def my_workflow(number: int, *, previous: Any = None) -> entrypoint.final[int, int]:
    previous = previous or 0
    # This will return the previous value to the caller, saving
    # 2 * number to the checkpoint, which will be used in the next invocation
    # for the `previous` parameter.
    return entrypoint.final(value=previous, save=2 * number)
config = {
    "configurable": {
        "thread_id": "1"
    }
}
my_workflow.invoke(3, config)  # 0 (previous was None)
my_workflow.invoke(1, config)  # 6 (previous was 3 * 2 from the previous invocation)
```

```js
// JavaScript
entrypoint.final是一个特殊的原语，可以从入口点返回，并允许**解耦**在**检查点中保存的值**和**入口点的返回值**。
第一个值是入口点的返回值，第二个值是将保存在检查点中的值。
```typescript
import { entrypoint, getPreviousState } from "@langchain/langgraph";
const myWorkflow = entrypoint(
  { checkpointer, name: "workflow" },
  async (number: number) => {
    const previous = getPreviousState<number>() ?? 0;
    // This will return the previous value to the caller, saving
    // 2 * number to the checkpoint, which will be used in the next invocation
    // for the `previous` parameter.
    return entrypoint.final({
      value: previous,
      save: 2 * number,
    });
  }
);
const config = {
  configurable: {
    thread_id: "1",
  },
};
await myWorkflow.invoke(3, config); // 0 (previous was undefined)
await myWorkflow.invoke(1, config); // 6 (previous was 3 * 2 from the previous invocation)
```

## 任务
**任务**表示一个离散的工作单元，如API调用或数据处理步骤。它有两个关键特性：
* **异步执行**：任务设计为异步执行，允许多个操作并发运行而不阻塞。
* **检查点**：任务结果保存到检查点，启用从最后保存的状态恢复工作流。（有关更多详细信息，请参阅[持久化](/v1/python/langgraph/persistence)）。
### 定义

```python
# Python
任务是使用`@task`装饰器定义的，该装饰器包装了一个常规Python函数。
```python
from langgraph.func import task
@task()
def slow_computation(input_value):
    # Simulate a long-running operation
    ...
    return result
```

```js
// JavaScript
任务是使用`task`函数定义的，该函数包装了一个常规函数。
```typescript
import { task } from "@langchain/langgraph";
const slowComputation = task("slowComputation", async (inputValue: any) => {
  // Simulate a long-running operation
  return result;
});
```

警告：**序列化**
任务的**输出**必须是JSON可序列化的，以支持检查点。
### 执行
**任务**只能从**入口点**、另一个**任务**或[状态图节点](/v1/python/langgraph/graph-api#nodes)内调用。
任务**不能**直接从主应用程序代码调用。

```python
# Python
当您调用**任务**时，它会立即返回一个future对象。future是稍后将可用的结果的占位符。
要获取**任务**的结果，您可以同步等待（使用`result()`）或异步等待（使用`await`）。
同步调用：
```python
@entrypoint(checkpointer=checkpointer)
def my_workflow(some_input: int) -> int:
    future = slow_computation(some_input)
    return future.result()  # Wait for the result synchronously
```

异步调用：

```python
@entrypoint(checkpointer=checkpointer)
async def my_workflow(some_input: int) -> int:
    return await slow_computation(some_input)  # Await result asynchronously
```

```js
// JavaScript
当您调用**任务**时，它会返回一个可以等待的Promise。
```typescript
const myWorkflow = entrypoint(
  { checkpointer, name: "workflow" },
  async (someInput: number): Promise<number> => {
    return await slowComputation(someInput);
  }
);
```

## 何时使用任务
**任务**在以下场景中很有用：
* **检查点**：当您需要将长时间运行的操作的结果保存到检查点时，这样在恢复工作流时就不需要重新计算它。
* **人机协作**：如果您正在构建一个需要人工干预的工作流，您**必须**使用**任务**来封装任何随机性（例如，API调用），以确保工作流可以正确恢复。有关更多详细信息，请参阅[确定性](#determinism)部分。
* **并行执行**：对于I/O绑定的任务，**任务**启用并行执行，允许多个操作并发运行而不阻塞（例如，调用多个API）。
* **可观察性**：将操作包装在**任务**中提供了一种使用[LangSmith](https://docs.smith.langchain.com/)跟踪工作流进度和监控单个操作执行的方法。
* **可重试工作**：当工作需要重试以处理故障或不一致时，**任务**提供了一种封装和管理重试逻辑的方法。
## 序列化
LangGraph中的序列化有两个关键方面：
1. `entrypoint`的输入和输出必须是JSON可序列化的。
2. `task`的输出必须是JSON可序列化的。

```python
# Python
这些要求对于启用检查点和工作流恢复是必要的。使用Python原语，如字典、列表、字符串、数字和布尔值，以确保您的输入和输出是可序列化的。
```

```js
// JavaScript
这些要求对于启用检查点和工作流恢复是必要的。使用原语，如对象、数组、字符串、数字和布尔值，以确保您的输入和输出是可序列化的。
```

序列化确保工作流状态，如任务结果和中间值，可以可靠地保存和恢复。这对于启用人机协作交互、容错和并行执行至关重要。

提供不可序列化的输入或输出将在工作流配置了检查点时导致运行时错误。

## 确定性

要利用**人机协作**等功能，任何随机性都应封装在**任务**内部。这保证了当执行暂停（例如，用于人机协作）然后恢复时，它将遵循相同的步骤序列，即使**任务**结果是非确定性的。

LangGraph通过在执行时保存**任务**和[**子图**](use-subgraphs.html)结果来实现此行为。设计良好的工作流确保恢复执行遵循相同的步骤序列，允许正确检索先前计算的结果，而不必重新执行它们。这对于长时间运行的**任务**或具有非确定性结果的**任务**特别有用，因为它避免了重复先前完成的工作，并允许从本质上相同的位置恢复。

虽然工作流的不同运行可以产生不同的结果，但恢复**特定**运行应始终遵循相同的记录步骤序列。这允许LangGraph高效地查找在图被中断之前执行的**任务**和**子图**结果，并避免重新计算它们。

## 幂等性

幂等性确保多次运行相同的操作产生相同的结果。这有助于防止如果步骤由于故障而重新运行时出现重复的API调用和冗余处理。始终将API调用放在**任务**函数中进行检查点，并将它们设计为幂等的，以防重新执行。如果**任务**开始但未成功完成，可能会发生重新执行。然后，如果工作流恢复，**任务**将再次运行。使用幂等键或验证现有结果以避免重复。

## 常见陷阱

### 处理副作用

将副作用（例如，写入文件、发送电子邮件）封装在任务中，以确保在恢复工作流时不会多次执行它们。

错误示例：
在这个例子中，副作用（写入文件）直接包含在工作流中，因此在恢复工作流时会再次执行。

```python
# Python
@entrypoint(checkpointer=checkpointer)
def my_workflow(inputs: dict) -> int:
    # This code will be executed a second time when resuming the workflow.
    # Which is likely not what you want.
    with open("output.txt", "w") as f:  # [!code highlight]
        f.write("Side effect executed")  # [!code highlight]
    value = interrupt("question")
    return value
```

```typescript
// JavaScript
import { entrypoint, interrupt } from "@langchain/langgraph";
import fs from "fs";
const myWorkflow = entrypoint(
  { checkpointer, name: "workflow },
  async (inputs: Record<string, any>) => {
    // This code will be executed a second time when resuming the workflow.
    // Which is likely not what you want.
    fs.writeFileSync("output.txt", "Side effect executed");
    const value = interrupt("question");
    return value;
  }
);
```

正确示例：
在这个例子中，副作用被封装在任务中，确保恢复时执行一致。

```python
# Python
from langgraph.func import task
@task  # [!code highlight]
def write_to_file():  # [!code highlight]
    with open("output.txt", "w") as f:
        f.write("Side effect executed")
@entrypoint(checkpointer=checkpointer)
def my_workflow(inputs: dict) -> int:
    # The side effect is now encapsulated in a task.
    write_to_file().result()
    value = interrupt("question")
    return value
```

```typescript
// JavaScript
import { entrypoint, task, interrupt } from "@langchain/langgraph";
import * as fs from "fs";
const writeToFile = task("writeToFile", async () => {
  fs.writeFileSync("output.txt", "Side effect executed");
});
const myWorkflow = entrypoint(
  { checkpointer, name: "workflow" },
  async (inputs: Record<string, any>) => {
    // The side effect is now encapsulated in a task.
    await writeToFile();
    const value = interrupt("question");
    return value;
  }
);
```

### 非确定性控制流

可能每次给出不同结果的操作（如获取当前时间或随机数）应封装在任务中，以确保在恢复时返回相同的结果。

* 在任务中：获取随机数（5）→中断→恢复→（再次返回5）→...
* 不在任务中：获取随机数（5）→中断→恢复→获取新的随机数（7）→...

```python
# Python
这在使用具有多个interrupt调用的**人机协作**工作流时尤其重要。LangGraph为每个任务/入口点保留一个恢复值列表。当遇到interrupt时，它会与相应的恢复值匹配。这种匹配是严格基于**索引**的，因此恢复值的顺序应与interrupt的顺序匹配。
```

```js
// JavaScript
这在使用具有多个interrupt调用的**人机协作**工作流时尤其重要。LangGraph为每个任务/入口点保留一个恢复值列表。当遇到interrupt时，它会与相应的恢复值匹配。这种匹配是严格基于**索引**的，因此恢复值的顺序应与interrupt的顺序匹配。
```

如果在恢复时不保持执行顺序，一个interrupt调用可能会与错误的resume值匹配，导致不正确的结果。

请阅读[确定性](#determinism)部分以获取更多详细信息。

错误示例：
在这个例子中，工作流使用当前时间来确定要执行哪个任务。这是非确定性的，因为工作流的结果取决于执行它的时间。

```python
# Python
from langgraph.func import entrypoint
@entrypoint(checkpointer=checkpointer)
def my_workflow(inputs: dict) -> int:
    t0 = inputs["t0"]
    t1 = time.time()  # [!code highlight]
    delta_t = t1 - t0
    if delta_t > 1:
        result = slow_task(1).result()
        value = interrupt("question")
    else:
        result = slow_task(2).result()
        value = interrupt("question")
    return {
        "result": result,
        "value": value
    }
```

```typescript
// JavaScript
import { entrypoint, interrupt } from "@langchain/langgraph";
const myWorkflow = entrypoint(
  { checkpointer, name: "workflow" },
  async (inputs: { t0: number }) => {
    const t1 = Date.now();
    const deltaT = t1 - inputs.t0;
    if (deltaT > 1000) {
      const result = await slowTask(1);
      const value = interrupt("question");
      return { result, value };
    } else {
      const result = await slowTask(2);
      const value = interrupt("question");
      return { result, value };
    }
  }
);
```

正确示例：

```python
# Python
在这个例子中，工作流使用输入`t0`来确定要执行哪个任务。这是确定性的，因为工作流的结果仅取决于输入。
```python
import time
from langgraph.func import task
@task  # [!code highlight]
def get_time() -> float:  # [!code highlight]
    return time.time()
@entrypoint(checkpointer=checkpointer)
def my_workflow(inputs: dict) -> int:
    t0 = inputs["t0"]
    t1 = get_time().result()  # [!code highlight]
    delta_t = t1 - t0
    if delta_t > 1:
        result = slow_task(1).result()
        value = interrupt("question")
    else:
        result = slow_task(2).result()
        value = interrupt("question")
    return {
        "result": result,
        "value": value
    }
```

```typescript
// JavaScript
在这个例子中，工作流使用输入`t0`来确定要执行哪个任务。这是确定性的，因为工作流的结果仅取决于输入。
```typescript
import { entrypoint, task, interrupt } from "@langchain/langgraph";
const getTime = task("getTime", () => Date.now());
const myWorkflow = entrypoint(
  { checkpointer, name: "workflow" },
  async (inputs: { t0: number }): Promise<any> => {
    const t1 = await getTime();
    const deltaT = t1 - inputs.t0;
    if (deltaT > 1000) {