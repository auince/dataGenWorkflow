# 使用函数式API

[**函数式API**](https://langchain-doc.cn/v1/python/langgraph/functional-api)允许您通过对现有代码进行最小的更改，为应用程序添加LangGraph的关键功能——[持久性](persistence.html)、[内存](add-memory.html)、[人机协作](interrupts.html)和[流式传输](streaming.html)。

提示：有关函数式API的概念信息，请参阅[函数式API](https://langchain-doc.cn/v1/python/langgraph/functional-api)。

## 创建简单工作流

定义`entrypoint`时，输入仅限于函数的第一个参数。要传递多个输入，您可以使用字典。

```python
@entrypoint(checkpointer=checkpointer)
def my_workflow(inputs: dict) -> int:
    value = inputs["value"]
    another_value = inputs["another_value"]
    ...
my_workflow.invoke({"value": 1, "another_value": 2})
```

```typescript
const checkpointer = new MemorySaver();
const myWorkflow = entrypoint(
  { checkpointer, name: "myWorkflow" },
  async (inputs: { value: number; anotherValue: number }) => {
    const value = inputs.value;
    const anotherValue = inputs.anotherValue;
    // ...
  }
);
await myWorkflow.invoke({ value: 1, anotherValue: 2 });
```

### 扩展示例：简单工作流

```python
import uuid
from langgraph.func import entrypoint, task
from langgraph.checkpoint.memory import InMemorySaver
# 检查数字是否为偶数的任务
@task
def is_even(number: int) -> bool:
    return number % 2 == 0
# 格式化消息的任务
@task
def format_message(is_even: bool) -> str:
    return "The number is even." if is_even else "The number is odd."
# 创建用于持久性的检查点
checkpointer = InMemorySaver()
@entrypoint(checkpointer=checkpointer)
def workflow(inputs: dict) -> str:
    """简单的工作流来分类数字。"""
    even = is_even(inputs["number"]).result()
    return format_message(even).result()
# 使用唯一的线程ID运行工作流
config = {"configurable": {"thread_id": str(uuid.uuid4())}}
result = workflow.invoke({"number": 7}, config=config)
print(result)
```

```typescript
import { v4 as uuidv4 } from "uuid";
import { entrypoint, task, MemorySaver } from "@langchain/langgraph";
// 检查数字是否为偶数的任务
const isEven = task("isEven", async (number: number) => {
  return number % 2 === 0;
});
// 格式化消息的任务
const formatMessage = task("formatMessage", async (isEven: boolean) => {
  return isEven ? "The number is even." : "The number is odd.";
});
// 创建用于持久性的检查点
const checkpointer = new MemorySaver();
const workflow = entrypoint(
  { checkpointer, name: "workflow" },
  async (inputs: { number: number }) => {
    // 简单的工作流来分类数字
    const even = await isEven(inputs.number);
    return await formatMessage(even);
  }
);
// 使用唯一的线程ID运行工作流
const config = { configurable: { thread_id: uuidv4() } };
const result = await workflow.invoke({ number: 7 }, config);
console.log(result);
```

### 扩展示例：使用LLM撰写文章

此示例演示如何语法上使用`@task`和`@entrypoint`装饰器。由于提供了检查点，工作流结果将持久化在检查点中。

```python
import uuid
from langchain.chat_models import init_chat_model
from langgraph.func import entrypoint, task
from langgraph.checkpoint.memory import InMemorySaver
model = init_chat_model('gpt-3.5-turbo')
# 任务：使用LLM生成文章
@task
def compose_essay(topic: str) -> str:
    """生成关于给定主题的文章。"""
    return model.invoke([
        {"role": "system", "content": "You are a helpful assistant that writes essays."},
        {"role": "user", "content": f"Write an essay about {topic}."}
    ]).content
# 创建用于持久性的检查点
checkpointer = InMemorySaver()
@entrypoint(checkpointer=checkpointer)
def workflow(topic: str) -> str:
    """使用LLM生成文章的简单工作流。"""
    return compose_essay(topic).result()
# 执行工作流
config = {"configurable": {"thread_id": str(uuid.uuid4())}}
result = workflow.invoke("the history of flight", config=config)
print(result)
```

```typescript
import { v4 as uuidv4 } from "uuid";
import { ChatOpenAI } from "@langchain/openai";
import { entrypoint, task, MemorySaver } from "@langchain/langgraph";
const model = new ChatOpenAI({ model: "gpt-3.5-turbo" });
// 任务：使用LLM生成文章
const composeEssay = task("composeEssay", async (topic: string) => {
  // 生成关于给定主题的文章
  const response = await model.invoke([
    { role: "system", content: "You are a helpful assistant that writes essays." },
    { role: "user", content: `Write an essay about ${topic}.` }
  ]);
  return response.content as string;
});
// 创建用于持久性的检查点
const checkpointer = new MemorySaver();
const workflow = entrypoint(
  { checkpointer, name: "workflow" },
  async (topic: string) => {
    // 使用LLM生成文章的简单工作流
    return await composeEssay(topic);
  }
);
// 执行工作流
const config = { configurable: { thread_id: uuidv4() } };
const result = await workflow.invoke("the history of flight", config);
console.log(result);
```

## 并行执行

任务可以通过并发调用来并行执行并等待结果。这对于提高IO密集型任务（例如，调用LLM的API）的性能很有用。

```python
@task
def add_one(number: int) -> int:
    return number + 1
@entrypoint(checkpointer=checkpointer)
def graph(numbers: list[int]) -> list[str]:
    futures = [add_one(i) for i in numbers]
    return [f.result() for f in futures]
```

```typescript
const addOne = task("addOne", async (number: number) => {
  return number + 1;
});
const graph = entrypoint(
  { checkpointer, name: "graph" },
  async (numbers: number[]) => {
    return await Promise.all(numbers.map(addOne));
  }
);
```

### 扩展示例：并行LLM调用

此示例演示如何使用`@task`并行运行多个LLM调用。每个调用生成关于不同主题的段落，并将结果合并为单个文本输出。

```python
import uuid
from langchain.chat_models import init_chat_model
from langgraph.func import entrypoint, task
from langgraph.checkpoint.memory import InMemorySaver
# 初始化LLM模型
model = init_chat_model("gpt-3.5-turbo")
# 生成关于给定主题的段落的任务
@task
def generate_paragraph(topic: str) -> str:
    response = model.invoke([
        {"role": "system", "content": "You are a helpful assistant that writes educational paragraphs."},
        {"role": "user", "content": f"Write a paragraph about {topic}."}
    ])
    return response.content
# 创建用于持久性的检查点
checkpointer = InMemorySaver()
@entrypoint(checkpointer=checkpointer)
def workflow(topics: list[str]) -> str:
    """并行生成多个段落并将它们组合起来。"""
    futures = [generate_paragraph(topic) for topic in topics]
    paragraphs = [f.result() for f in futures]
    return "\n\n".join(paragraphs)
# 运行工作流
config = {"configurable": {"thread_id": str(uuid.uuid4())}}
result = workflow.invoke(["quantum computing", "climate change", "history of aviation"], config=config)
print(result)
```

```typescript
import { v4 as uuidv4 } from "uuid";
import { ChatOpenAI } from "@langchain/openai";
import { entrypoint, task, MemorySaver } from "@langchain/langgraph";
// 初始化LLM模型
const model = new ChatOpenAI({ model: "gpt-3.5-turbo" });
// 生成关于给定主题的段落的任务
const generateParagraph = task("generateParagraph", async (topic: string) => {
  const response = await model.invoke([
    { role: "system", content: "You are a helpful assistant that writes educational paragraphs." },
    { role: "user", content: `Write a paragraph about ${topic}.` }
  ]);
  return response.content as string;
});
// 创建用于持久性的检查点
const checkpointer = new MemorySaver();
const workflow = entrypoint(
  { checkpointer, name: "workflow" },
  async (topics: string[]) => {
    // 并行生成多个段落并将它们组合起来
    const paragraphs = await Promise.all(topics.map(generateParagraph));
    return paragraphs.join("\n\n");
  }
);
// 运行工作流
const config = { configurable: { thread_id: uuidv4() } };
const result = await workflow.invoke(["quantum computing", "climate change", "history of aviation"], config);
console.log(result);
```

此示例使用LangGraph的并发模型来提高执行时间，特别是在任务涉及I/O（如LLM完成）时。

## 调用图

**函数式API**和[**图API**](https://langchain-doc.cn/v1/python/langgraph/graph-api)可以在同一个应用程序中一起使用，因为它们共享相同的底层运行时。

```python
from langgraph.func import entrypoint
from langgraph.graph import StateGraph
builder = StateGraph()
...
some_graph = builder.compile()
@entrypoint()
def some_workflow(some_input: dict) -> int:
    # 调用使用图API定义的图
    result_1 = some_graph.invoke(...)
    # 调用另一个使用图API定义的图
    result_2 = another_graph.invoke(...)
    return {
        "result_1": result_1,
        "result_2": result_2
    }
```

```typescript
import { entrypoint } from "@langchain/langgraph";
import { StateGraph } from "@langchain/langgraph";
const builder = new StateGraph(/* ... */);
// ...
const someGraph = builder.compile();
const someWorkflow = entrypoint(
  { name: "someWorkflow" },
  async (someInput: Record<string, any>) => {
    // 调用使用图API定义的图
    const result1 = await someGraph.invoke(/* ... */);
    // 调用另一个使用图API定义的图
    const result2 = await anotherGraph.invoke(/* ... */);
    return {
      result1,
      result2,
    };
  }
);
```

### 扩展示例：从函数式API调用简单图

```python
import uuid
from typing import TypedDict
from langgraph.func import entrypoint
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph
# 定义共享状态类型
class State(TypedDict):
    foo: int
# 定义简单的转换节点
def double(state: State) -> State:
    return {"foo": state["foo"] * 2}
# 使用图API构建图
builder = StateGraph(State)
builder.add_node("double", double)
builder.set_entry_point("double")
graph = builder.compile()
# 定义函数式API工作流
checkpointer = InMemorySaver()
@entrypoint(checkpointer=checkpointer)
def workflow(x: int) -> dict:
    result = graph.invoke({"foo": x})
    return {"bar": result["foo"]}
# 执行工作流
config = {"configurable": {"thread_id": str(uuid.uuid4())}}
print(workflow.invoke(5, config=config))  # 输出: {'bar': 10}
```

```typescript
import { v4 as uuidv4 } from "uuid";
import { entrypoint, MemorySaver } from "@langchain/langgraph";
import { StateGraph } from "@langchain/langgraph";
import * as z from "zod";
// 定义共享状态类型
const State = z.object({
  foo: z.number(),
});
// 使用图API构建图
const builder = new StateGraph(State)
  .addNode("double", (state) => {
    return { foo: state.foo * 2 };
  })
  .addEdge("__start__", "double");
const graph = builder.compile();
// 定义函数式API工作流
const checkpointer = new MemorySaver();
const workflow = entrypoint(
  { checkpointer, name: "workflow" },
  async (x: number) => {
    const result = await graph.invoke({ foo: x });
    return { bar: result.foo };
  }
);
// 执行工作流
const config = { configurable: { thread_id: uuidv4() } };
console.log(await workflow.invoke(5, config)); // 输出: { bar: 10 }
```

## 调用其他入口点

您可以在**入口点**或**任务**中调用其他**入口点**。

```python
@entrypoint() # 将自动使用父入口点的检查点
def some_other_workflow(inputs: dict) -> int:
    return inputs["value"]
@entrypoint(checkpointer=checkpointer)
def my_workflow(inputs: dict) -> int:
    value = some_other_workflow.invoke({"value": 1})
    return value
```

```typescript
// 将自动使用父入口点的检查点
const someOtherWorkflow = entrypoint(
  { name: "someOtherWorkflow" },
  async (inputs: { value: number }) => {
    return inputs.value;
  }
);
const myWorkflow = entrypoint(
  { checkpointer, name: "myWorkflow" },
  async (inputs: { value: number }) => {
    const value = await someOtherWorkflow.invoke({ value: 1 });
    return value;
  }
);
```

### 扩展示例：调用另一个入口点

```python
import uuid
from langgraph.func import entrypoint
from langgraph.checkpoint.memory import InMemorySaver
# 初始化检查点
checkpointer = InMemorySaver()
# 可重用的子工作流，用于乘法运算
@entrypoint()
def multiply(inputs: dict) -> int:
    return inputs["a"] * inputs["b"]
# 调用子工作流的主工作流
@entrypoint(checkpointer=checkpointer)
def main(inputs: dict) -> dict:
    result = multiply.invoke({"a": inputs["x"], "b": inputs["y"]})
    return {"product": result}
# 执行主工作流
config = {"configurable": {"thread_id": str(uuid.uuid4())}}
print(main.invoke({"x": 6, "y": 7}, config=config))  # 输出: {'product': 42}
```

```typescript
import { v4 as uuidv4 } from "uuid";
import { entrypoint, MemorySaver } from "@langchain/langgraph";
// 初始化检查点
const checkpointer = new MemorySaver();
// 可重用的子工作流，用于乘法运算
const multiply = entrypoint(
  { name: "multiply" },
  async (inputs: { a: number; b: number }) => {
    return inputs.a * inputs.b;
  }
);
// 调用子工作流的主工作流
const main = entrypoint(
  { checkpointer, name: "main" },
  async (inputs: { x: number; y: number }) => {
    const result = await multiply.invoke({ a: inputs.x, b: inputs.y });
    return { product: result };
  }
);
// 执行主工作流
const config = { configurable: { thread_id: uuidv4() } };
console.log(await main.invoke({ x: 6, y: 7 }, config)); // 输出: { product: 42 }
```

## 流式传输

**函数式API**使用与**图API**相同的流式传输机制。请阅读[**流式传输指南**](streaming.html)部分了解更多详细信息。

使用流式传输API同时流式传输更新和自定义数据的示例。

```python
from langgraph.func import entrypoint
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.config import get_stream_writer   # [!code highlight]
checkpointer = InMemorySaver()
@entrypoint(checkpointer=checkpointer)
def main(inputs: dict) -> int:
    writer = get_stream_writer()   # [!code highlight]
    writer("Started processing")   # [!code highlight]
    result = inputs["x"] * 2
    writer(f"Result is {result}")   # [!code highlight]
    return result
config = {"configurable": {"thread_id": "abc"}}
for mode, chunk in main.stream(   # [!code highlight]
    {"x": 5},
    stream_mode=["custom", "updates"],   # [!code highlight]
    config=config
):
    print(f"{mode}: {chunk}")
```

1. 从`langgraph.config`导入`get_stream_writer`。
2. 在入口点内获取流写入器实例。
3. 在计算开始前发出自定义数据。
4. 在计算结果后发出另一条自定义消息。
5. 使用`.stream()`处理流式输出。
6. 指定要使用的流式传输模式。

```
('updates', {'add_one': 2})
('updates', {'add_two': 3})
('custom', 'hello')
('custom', 'world')
('updates', {'main': 5})
```

警告：**Python < 3.11 的异步**
如果使用Python < 3.11并编写异步代码，使用`get_stream_writer`将不起作用。请直接使用`StreamWriter`类。有关更多详细信息，请参阅[Python < 3.11 的异步](streaming.html#async)。

```python
from langgraph.types import StreamWriter
@entrypoint(checkpointer=checkpointer)
async def main(inputs: dict, writer: StreamWriter) -> int:  # [!code highlight]
...
```

```typescript
import {
  entrypoint,
  MemorySaver,
  LangGraphRunnableConfig,
} from "@langchain/langgraph";
const checkpointer = new MemorySaver();
const main = entrypoint(
  { checkpointer, name: "main" },
  async (
    inputs: { x: number },
    config: LangGraphRunnableConfig
  ): Promise<number> => {
    config.writer?.("Started processing");   // [!code highlight]
    const result = inputs.x * 2;
    config.writer?.(`Result is ${result}`);   // [!code highlight]
    return result;
  }
);
const config = { configurable: { thread_id: "abc" } };
  // [!code highlight]
for await (const [mode, chunk] of await main.stream(
  { x: 5 },
  { streamMode: ["custom", "updates"], ...config }   // [!code highlight]
)) {
  console.log(`${mode}: ${JSON.stringify(chunk)}`);
}
```

1. 在计算开始前发出自定义数据。
2. 在计算结果后发出另一条自定义消息。
3. 使用`.stream()`处理流式输出。
4. 指定要使用的流式传输模式。

```
updates: {"addOne": 2}
updates: {"addTwo": 3}
custom: "hello"
custom: "world"
updates: {"main": 5}
```

## 重试策略

```python
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.func import entrypoint, task
from langgraph.types import RetryPolicy
# 这个变量仅用于演示目的，模拟网络故障。
# 这不是您实际代码中会有的内容。
attempts = 0
# 让我们配置RetryPolicy在ValueError时重试。
# 默认的RetryPolicy针对特定的网络错误进行了优化。
retry_policy = RetryPolicy(retry_on=ValueError)
@task(retry_policy=retry_policy)
def get_info():
    global attempts
    attempts += 1
    if attempts < 2:
        raise ValueError('Failure')
    return "OK"
checkpointer = InMemorySaver()
@entrypoint(checkpointer=checkpointer)
def main(inputs, writer):
    return get_info().result()
config = {
    "configurable": {
        "thread_id": "1"
    }
}
main.invoke({'any_input': 'foobar'}, config=config)
```

```
'OK'
```

```typescript
import {
  MemorySaver,
  entrypoint,
  task,
  RetryPolicy,
} from "@langchain/langgraph";
// 这个变量仅用于演示目的，模拟网络故障。
// 这不是您实际代码中会有的内容。
let attempts = 0;
// 让我们配置RetryPolicy在ValueError时重试。
// 默认的RetryPolicy针对特定的网络错误进行了优化。
const retryPolicy: RetryPolicy = { retryOn: (error) => error instanceof Error };
const getInfo = task(
  {
    name: "getInfo",
    retry: retryPolicy,
  },
  () => {
    attempts += 1;
    if (attempts < 2) {
      throw new Error("Failure");
    }
    return "OK";
  }
);
const checkpointer = new MemorySaver();
const main = entrypoint(
  { checkpointer, name: "main" },
  async (inputs: Record<string, any>) => {
    return await getInfo();
  }
);
const config = {
  configurable: {
    thread_id: "1",
  },
};
await main.invoke({ any_input: "foobar" }, config);
```

```
'OK'
```

## 缓存任务

```python
import time
from langgraph.cache.memory import InMemoryCache
from langgraph.func import entrypoint, task
from langgraph.types import CachePolicy
@task(cache_policy=CachePolicy(ttl=120))    # [!code highlight]
def slow_add(x: int) -> int:
    time.sleep(1)
    return x * 2
@entrypoint(cache=InMemoryCache())
def main(inputs: dict) -> dict[str, int]:
    result1 = slow_add(inputs["x"]).result()
    result2 = slow_add(inputs["x"]).result()
    return {"result1": result1, "result2": result2}
for chunk in main.stream({"x": 5}, stream_mode="updates"):
    print(chunk)
#> {'slow_add': 10}
#> {'slow_add': 10, '__metadata__': {'cached': True}}
#> {'main': {'result1': 10, 'result2': 10}}
```

1. `ttl`以秒为单位指定。缓存将在此时间后失效。

```typescript
import {
  InMemoryCache,
  entrypoint,
  task,
  CachePolicy,
} from "@langchain/langgraph";
const slowAdd = task(
  {
    name: "slowAdd",
    cache: { ttl: 120 },   // [!code highlight]
  },
  async (x: number) => {
    await new Promise((resolve) => setTimeout(resolve, 1000));
    return x * 2;
  }
);
const main = entrypoint(
  { cache: new InMemoryCache(), name: "main" },
  async (inputs: { x: number }) => {
    const result1 = await slowAdd(inputs.x);
    const result2 = await slowAdd(inputs.x);
    return { result1, result2 };
  }
);
for await (const chunk of await main.stream(
  { x: 5 },
  { streamMode: "updates" }
)) {
  console.log(chunk);
}
//> { slowAdd: 10 }
//> { slowAdd: 10, '__metadata__': { cached: true } }
//> { main: { result1: 10, result2: 10 } }
```

1. `ttl`以秒为单位指定。缓存将在此时间后失效。

## 错误后恢复

```python
import time
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.func import entrypoint, task
from langgraph.types import StreamWriter
# 这个变量仅用于演示目的，模拟网络故障。
# 这不是您实际代码中会有的内容。
attempts = 0
@task()
def get_info():
    """
    模拟一个在成功前失败一次的任务。
    在第一次尝试时抛出异常，然后在后续尝试中返回"OK"。
    """
    global attempts
    attempts += 1
    if attempts < 2:
        raise ValueError("Failure")  # 在第一次尝试时模拟失败
    return "OK"
# 初始化用于持久性的内存检查点
checkpointer = InMemorySaver()
@task
def slow_task():
    """
    通过引入1秒延迟来模拟一个慢速运行的任务。
    """
    time.sleep(1)
    return "Ran slow task."
@entrypoint(checkpointer=checkpointer)
def main(inputs, writer: StreamWriter):
    """
    顺序运行slow_task和get_info任务的主工作流函数。
    参数：
    - inputs: 包含工作流输入值的字典。
    - writer: 用于流式传输自定义数据的StreamWriter。
    工作流首先执行`slow_task`，然后尝试执行`get_info`，
    这将在第一次调用时失败。
    """
    slow_task_result = slow_task().result()  # 阻塞调用slow_task
    get_info().result()  # 第一次尝试时将在此处引发异常
    return slow_task_result
# 带有唯一线程标识符的工作流执行配置
config = {
    "configurable": {
        "thread_id": "1"  # 用于跟踪工作流执行的唯一标识符
    }
}
# 由于slow_task执行，此调用将花费约1秒
try:
    # 第一次调用将由于`get_info`任务失败而引发异常
    main.invoke({'any_input': 'foobar'}, config=config)
except ValueError:
    pass  # 优雅地处理失败
```

当我们恢复执行时，我们不需要重新运行`slow_task`，因为其结果已经保存在检查点中。

```python
main.invoke(None, config=config)
```

```
'Ran slow task.'
```

```typescript
import { entrypoint, task, MemorySaver } from "@langchain/langgraph";
// 这个变量仅用于演示目的，模拟网络故障。
// 这不是您实际代码中会有的内容。
let attempts = 0;
const getInfo = task("getInfo", async () => {
  /**
   * 模拟一个在成功前失败一次的任务。
   * 在第一次尝试时抛出异常，然后在后续尝试中返回"OK"。
   */
  attempts += 1;
  if (attempts < 2) {
    throw new Error("Failure"); // 在第一次尝试时模拟失败
  }
  return "OK";
});
// 初始化用于持久性的内存检查点
const checkpointer = new MemorySaver();
const slowTask = task("slowTask", async () => {
  /**
   * 通过引入1秒延迟来模拟一个慢速运行的任务。
   */
  await new Promise((resolve) => setTimeout(resolve, 1000));
  return "Ran slow task.";
});
const main = entrypoint(
  { checkpointer, name: "main" },
  async (inputs: Record<string, any>) => {
    /**
     * 顺序运行slowTask和getInfo任务的主工作流函数。
     *
     * 参数：
     * - inputs: 包含工作流输入值的Record<string, any>。
     *
     * 工作流首先执行`slowTask`，然后尝试执行`getInfo`，
     * 这将在第一次调用时失败。
     */
    const slowTaskResult = await slowTask(); // 阻塞调用slowTask
    await getInfo(); // 第一次尝试时将在此处引发异常
    return slowTaskResult;
  }
);
// 带有唯一线程标识符的工作流执行配置
const config = {
  configurable: {
    thread_id: "1", // 用于跟踪工作流执行的唯一标识符
  },
};
// 由于slowTask执行，此调用将花费约1秒
try {
  // 第一次调用将由于`getInfo`任务失败而引发异常
  await main.invoke({ any_input: "foobar" }, config);
} catch (err) {
  // 优雅地处理失败
}
```

当我们恢复执行时，我们不需要重新运行`slowTask`，因为其结果已经保存在检查点中。

```typescript
await main.invoke(null, config);
```

```
'Ran slow task.'
```

## 人机协作

函数式API使用`interrupt`函数和`Command`原语支持[人机协作](interrupts.html)工作流。

### 基本人机协作工作流

我们将创建三个[任务](https://langchain-doc.cn/v1/python/langgraph/functional-api#task)：

1. 追加"bar"。
2. 暂停等待人类输入。恢复时，追加人类输入。
3. 追加"qux"。

```python
from langgraph.func import entrypoint, task
from langgraph.types import Command, interrupt
@task
def step_1(input_query):
    """追加bar。"""
    return f"{input_query} bar"
@task
def human_feedback(input_query):
    """追加用户输入。"""
    feedback = interrupt(f"Please provide feedback: {input_query}")
    return f"{input_query} {feedback}"
@task
def step_3(input_query):
    """追加qux。"""
    return f"{input_query} qux"
```

```typescript
import { entrypoint, task, interrupt, Command } from "@langchain/langgraph";
const step1 = task("step1", async (inputQuery: string) => {
  // 追加bar
  return `${inputQuery} bar`;
});
const humanFeedback = task("humanFeedback", async (inputQuery: string) => {
  // 追加用户输入
  const feedback = interrupt(`Please provide feedback: ${inputQuery}`);
  return `${inputQuery} ${feedback}`;
});
const step3 = task("step3", async (inputQuery: string) => {
  // 追加qux
  return `${inputQuery} qux`;
});
```

我们现在可以在[入口点](https://langchain-doc.cn/v1/python/langgraph/functional-api#entrypoint)中组合这些任务：

```python
from langgraph.checkpoint.memory import InMemorySaver
checkpointer = InMemorySaver()
@entrypoint(checkpointer=checkpointer)
def graph(input_query):
    result_1 = step_1(input_query).result()
    result_2 = human_feedback(result_1).result()
    result_3 = step_3(result_2).result()
    return result_3
```

```typescript
import { MemorySaver } from "@langchain/langgraph";
const checkpointer = new MemorySaver();
const graph = entrypoint(
  { checkpointer, name: "graph" },
  async (inputQuery: string) => {
    const result1 = await step1(inputQuery);
    const result2 = await humanFeedback(result1);
    const result3 = await step3(result2);
    return result3;
  }
);
```

在任务内部调用[interrupt()](interrupts.html#pause-using-interrupt)，使人类能够查看和编辑前一个任务的输出。先前任务的结果——在这种情况下是`step_1`——是持久化的，这样它们就不会在`interrupt`之后再次运行。

让我们发送一个查询字符串：

```python
config = {"configurable": {"thread_id": "1"}}
for event in graph.stream("foo", config):
    print(event)
    print("\n")
```

```typescript
const config = { configurable: { thread_id: "1" } };
for await (const event of await graph.stream("foo", config)) {
  console.log(event);
  console.log("\n");
}
```

请注意，我们在`step_1`之后使用`interrupt`暂停了。中断提供了恢复运行的指令。要恢复，我们发出一个包含`human_feedback`任务所需数据的[`Command`](interrupts.html#resuming-interrupts)。

```python
# 继续执行
for event in graph.stream(Command(resume="baz"), config):
    print(event)
    print("\n")
```

```typescript
// 继续执行
for await (const event of await graph.stream(
  new Command({ resume: "baz" }),
  config
)) {
  console.log(event);
  console.log("\n");
}
```

恢复后，运行继续执行剩余的步骤并按预期终止。

### 审查工具调用

要在执行前审查工具调用，我们添加一个调用[`interrupt`](interrupts.html#pause-using-interrupt)的`review_tool_call`函数。当调用此函数时，执行将暂停，直到我们发出命令恢复它。

给定一个工具调用，我们的函数将`interrupt`等待人类审查。在那一点，我们可以：

- 接受工具调用
- 修改工具调用并继续
- 生成自定义工具消息（例如，指示模型重新格式化其工具调用）

```python
from typing import Union
def review_tool_call(tool_call: ToolCall) -> Union[ToolCall, ToolMessage]:
    """审查工具调用，返回验证版本。"""
    human_review = interrupt(
        {
            "question": "Is this correct?",
            "tool_call": tool_call,
        }
    )
    review_action = human_review["action"]
    review_data = human_review.get("data")
    if review_action == "continue":
        return tool_call
    elif review_action == "update":
        updated_tool_call = {**tool_call, **{"args": review_data}}
        return updated_tool_call
    elif review_action == "feedback":
        return ToolMessage(
            content=review_data, name=tool_call["name"], tool_call_id=tool_call["id"]
        )
```

```typescript
import { ToolCall } from "@langchain/core/messages/tool";
import { ToolMessage } from "@langchain/core/messages";
function reviewToolCall(toolCall: ToolCall): ToolCall | ToolMessage {
  // 审查工具调用，返回验证版本
  const humanReview = interrupt({
    question: "Is this correct?",
    tool_call: toolCall,
  });
  const reviewAction = humanReview.action;
  const reviewData = humanReview.data;
  if (reviewAction === "continue") {
    return toolCall;
  } else if (reviewAction === "update") {
    const updatedToolCall = { ...toolCall, args: reviewData };
    return updatedToolCall;
  } else if (reviewAction === "feedback") {
    return new ToolMessage({
      content: reviewData,
      name: toolCall.name,
      tool_call_id: toolCall.id,
    });
  }
  throw new Error(`Unknown review action: ${reviewAction}`);
}
```

我们现在可以更新[入口点](https://langchain-doc.cn/v1/python/langgraph/functional-api#entrypoint)来审查生成的工具调用。如果工具调用被接受或修改，我们以与之前相同的方式执行。否则，我们只附加人类提供的`ToolMessage`。先前任务的结果——在这种情况下是初始模型调用——是持久化的，这样它们就不会在`interrupt`之后再次运行。

```python
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph.message import add_messages
from langgraph.types import Command, interrupt
checkpointer = InMemorySaver()
@entrypoint(checkpointer=checkpointer)
def agent(messages, previous):
    if previous is not None:
        messages = add_messages(previous, messages)
    model_response = call_model(messages).result()
    while True:
        if not model_response.tool_calls:
            break
        # 审查工具调用
        tool_results = []
        tool_calls = []
        for i, tool_call in enumerate(model_response.tool_calls):
            review = review_tool_call(tool_call)
            if isinstance(review, ToolMessage):
                tool_results.append(review)
            else:  # 是验证过的工具调用
                tool_calls.append(review)
                if review != tool_call:
                    model_response.tool_calls[i] = review  # 更新消息
        # 执行剩余的工具调用
        tool_result_futures = [call_tool(tool_call) for tool_call in tool_calls]
        remaining_tool_results = [fut.result() for fut in tool_result_futures]
        # 追加到消息列表
        messages = add_messages(
            messages,
            [model_response, *tool_results, *remaining_tool_results],
        )
        # 再次调用模型
        model_response = call_model(messages).result