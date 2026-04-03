# 后端

深度Agent通过`ls`、`read_file`、`write_file`、`edit_file`、`glob`和`grep`等工具向Agent公开文件系统界面。这些工具通过可插拔的后端运行。

本页介绍如何[选择后端](#指定后端)、[将不同路径路由到不同后端](#路由到不同后端)、[实现您自己的虚拟文件系统](#使用虚拟文件系统)（例如 S3 或 Postgres）、[添加策略挂钩](#添加策略挂钩)以及[遵守后端协议](#协议参考)。

## 快速入门

以下是一些预构建的文件系统后端，您可以快速将其与深度Agent一起使用：

| 内置后端 | 描述 |
| :--- | :--- |
| [默认](#statebackend-短暂) | `agent = create_deep_agent()` <br/> 状态中短暂存在。Agent的默认文件系统后端存储在`langgraph`状态中。请注意，此文件系统仅在*单个线程*中持久存在。 |
| [本地文件系统持久化](#filesystembackend-本地磁盘) | `agent = create_deep_agent(backend=FilesystemBackend(root_dir="/Users/nh/Desktop/"))` <br/>这使深度Agent可以访问您本地计算机的文件系统。您可以指定Agent有权访问的根目录。请注意，任何提供的`root_dir`都必须是绝对路径。 |
| [持久存储（LangGraph 存储）](#storebackend-langgraph-存储) | `agent = create_deep_agent(backend=lambda rt: StoreBackend(rt))` <br/>这使Agent可以访问*跨线程持久化*的长期存储。这对于存储适用于Agent多次执行的长期记忆或指令非常有用。 |
| [复合](#compositebackend-路由器) | 默认情况下是短暂的，`/memories/`是持久的。复合后端具有最大的灵活性。您可以在文件系统中指定不同的路由以指向不同的后端。有关可直接粘贴的示例，请参见下面的复合路由。 |

## 内置后端

### StateBackend（短暂）

```python
# 默认情况下，我们提供一个 StateBackend
agent = create_deep_agent()
# 在底层，它看起来像这样
from deepagents.backends import StateBackend
agent = create_deep_agent(
    backend=(lambda rt: StateBackend(rt))   # 请注意，工具通过 runtime.state 访问状态
)
```

**工作原理：**

*   在当前线程的 LangGraph Agent状态中存储文件。
*   通过检查点在同一线程上的多个Agent轮次中持久存在。

**最适用于：**

*   Agent用于写入中间结果的草稿板。
*   自动逐出大型工具输出，Agent可以随后逐段读回。

### FilesystemBackend（本地磁盘）

```python
from deepagents.backends import FilesystemBackend
agent = create_deep_agent(
    backend=FilesystemBackend(root_dir="/Users/nh/Desktop/")
)
```

**工作原理：**

*   在可配置的`root_dir`下读取/写入真实文件。
*   注意：`root_dir`必须是绝对路径。
*   您可以选择设置`virtual_mode=True`以在`root_dir`下沙盒化和规范化路径。
*   使用安全路径解析，尽可能防止不安全的符号链接遍历，可以使用 ripgrep 进行快速`grep`。

**最适用于：**

*   您机器上的本地项目
*   CI 沙盒
*   挂载的持久卷

### StoreBackend（LangGraph 存储）

```python
from deepagents.backends import StoreBackend
agent = create_deep_agent(
    backend=(lambda rt: StoreBackend(rt))   # 请注意，工具通过 runtime.store 访问存储
)
```

**工作原理：**

*   将文件存储在运行时提供的 LangGraph `BaseStore`中，从而实现跨线程的持久存储。

**最适用于：**

*   当您已经使用配置好的 LangGraph 存储运行时（例如，Redis、Postgres 或`BaseStore`背后的云实现）。
*   当您通过 LangSmith Deployments 部署Agent时（会自动为您的Agent配置一个存储）。

### CompositeBackend（路由器）

```python
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from deepagents.backends.composite import build_composite_state_backend
composite_backend = lambda rt: CompositeBackend(
    default=StateBackend(rt)
    routes={
        "/memories/": StoreBackend(rt),
        "/docs/": CustomBackend()
    }
)
agent = create_deep_agent(backend=composite_backend)
```

**工作原理：**

*   根据路径前缀将文件操作路由到不同的后端。
*   在列表和搜索结果中保留原始路径前缀。

**最适用于：**

*   当您希望为Agent提供短暂和跨线程存储时，CompositeBackend 允许您同时提供 StateBackend 和 StoreBackend
*   当您有多个信息源希望作为单个文件系统的一部分提供给Agent时。
    *   例如，您将长期记忆存储在一个存储的 /memories/ 下，并且您还有一个自定义后端，其文档可在 /docs/ 访问。

## 指定后端

*   将后端传递给`create_deep_agent(backend=...)`。文件系统中间件将其用于所有工具。
*   您可以传递：
    *   实现`BackendProtocol`的实例（例如，`FilesystemBackend(root_dir=".")`），或
    *   一个工厂`BackendFactory = Callable[[ToolRuntime], BackendProtocol]`（对于需要运行时的后端，如`StateBackend`或`StoreBackend`）。
*   如果省略，则默认为`lambda rt: StateBackend(rt)`。

## 路由到不同后端

将命名空间的一部分路由到不同的后端。通常用于持久化`/memories/*`并使其他所有内容保持短暂。

```python
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from deepagents.backends.composite import build_composite_state_backend
composite_backend = lambda rt: CompositeBackend(
    routes={
        "/memories/": FilesystemBackend(root_dir="/deepagents/myagent"),
    },
)
agent = create_deep_agent(backend=composite_backend)
```

行为：

*   `/workspace/plan.md` → StateBackend（短暂）
*   `/memories/agent.md` → `/deepagents/myagent`下的 FilesystemBackend
*   `ls`、`glob`、`grep`聚合结果并显示原始路径前缀。

注意：

*   较长的前缀优先（例如，路由`"/memories/projects/"`可以覆盖`"/memories/"`）。
*   对于 StoreBackend 路由，请确保Agent运行时提供一个存储（`runtime.store`）。

## 使用虚拟文件系统

构建一个自定义后端，将远程或数据库文件系统（例如 S3 或 Postgres）投影到工具命名空间中。

设计指南：

*   路径是绝对的（`/x/y.txt`）。决定如何将它们映射到您的存储键/行。
*   高效地实现`ls_info`和`glob_info`（在可用的情况下进行服务器端列表，否则进行本地筛选）。
*   对于丢失的文件或无效的正则表达式模式，返回用户可读的错误字符串。
*   对于外部持久化，在结果中设置`files_update=None`；只有状态内后端才应返回`files_update`字典。

S3 风格大纲：

```python
from deepagents.backends.protocol import BackendProtocol, WriteResult, EditResult
from deepagents.backends.utils import FileInfo, GrepMatch
class S3Backend(BackendProtocol):
    def __init__(self, bucket: str, prefix: str = ""):
        self.bucket = bucket
        self.prefix = prefix.rstrip("/")
    def _key(self, path: str) -> str:
        return f"{self.prefix}{path}"
    def ls_info(self, path: str) -> list[FileInfo]:
        # 列出 _key(path) 下的对象；构建 FileInfo 条目（路径、大小、修改时间）
        ...
    def read(self, file_path: str, offset: int = 0, limit: int = 2000) -> str:
        # 获取对象；返回带编号的内容或错误字符串
        ...
    def grep_raw(self, pattern: str, path: str | None = None, glob: str | None = None) -> list[GrepMatch] | str:
        # 可选择在服务器端进行筛选；否则列出并扫描内容
        ...
    def glob_info(self, pattern: str, path: str = "/") -> list[FileInfo]:
        # 在键上相对于路径应用 glob
        ...
    def write(self, file_path: str, content: str) -> WriteResult:
        # 强制执行仅创建语义；返回 WriteResult(path=file_path, files_update=None)
        ...
    def edit(self, file_path: str, old_string: str, new_string: str, replace_all: bool = False) -> EditResult:
        # 读取 → 替换（尊重唯一性与 replace_all）→ 写入 → 返回出现次数
        ...
```

Postgres 风格大纲：

*   表`files(path text primary key, content text, created_at timestamptz, modified_at timestamptz)`
*   将工具操作映射到 SQL：
    *   `ls_info`使用`WHERE path LIKE $1 || '%'`
    *   `glob_info`在 SQL 中筛选或获取然后在 Python 中应用 glob
    *   `grep_raw`可以按扩展名或最后修改时间获取候选行，然后扫描行

## 添加策略挂钩

通过子类化或包装后端来强制执行企业规则。

在选定的前缀下阻止写入/编辑（子类）：

```python
from deepagents.backends.filesystem import FilesystemBackend
from deepagents.backends.protocol import WriteResult, EditResult
class GuardedBackend(FilesystemBackend):
    def __init__(self, *, deny_prefixes: list[str], **kwargs):
        super().__init__(**kwargs)
        self.deny_prefixes = [p if p.endswith("/") else p + "/" for p in deny_prefixes]
    def write(self, file_path: str, content: str) -> WriteResult:
        if any(file_path.startswith(p) for p in self.deny_prefixes):
            return WriteResult(error=f"不允许在 {file_path} 下写入")
        return super().write(file_path, content)
    def edit(self, file_path: str, old_string: str, new_string: str, replace_all: bool = False) -> EditResult:
        if any(file_path.startswith(p) for p in self.deny_prefixes):
            return EditResult(error=f"不允许在 {file_path} 下编辑")
        return super().edit(file_path, old_string, new_string, replace_all)
```

通用包装器（适用于任何后端）：

```python
from deepagents.backends.protocol import BackendProtocol, WriteResult, EditResult
from deepagents.backends.utils import FileInfo, GrepMatch
class PolicyWrapper(BackendProtocol):
    def __init__(self, inner: BackendProtocol, deny_prefixes: list[str] | None = None):
        self.inner = inner
        self.deny_prefixes = [p if p.endswith("/") else p + "/" for p in (deny_prefixes or [])]
    def _deny(self, path: str) -> bool:
        return any(path.startswith(p) for p in self.deny_prefixes)
    def ls_info(self, path: str) -> list[FileInfo]:
        return self.inner.ls_info(path)
    def read(self, file_path: str, offset: int = 0, limit: int = 2000) -> str:
        return self.inner.read(file_path, offset=offset, limit=limit)
    def grep_raw(self, pattern: str, path: str | None = None, glob: str | None = None) -> list[GrepMatch] | str:
        return self.inner.grep_raw(pattern, path, glob)
    def glob_info(self, pattern: str, path: str = "/") -> list[FileInfo]:
        return self.inner.glob_info(pattern, path)
    def write(self, file_path: str, content: str) -> WriteResult:
        if self._deny(file_path):
            return WriteResult(error=f"不允许在 {file_path} 下写入")
        return self.inner.write(file_path, content)
    def edit(self, file_path: str, old_string: str, new_string: str, replace_all: bool = False) -> EditResult:
        if self._deny(file_path):
            return EditResult(error=f"不允许在 {file_path} 下编辑")
        return self.inner.edit(file_path, old_string, new_string, replace_all)
```

## 协议参考

后端必须实现`BackendProtocol`。

必需的端点：

*   `ls_info(path: str) -> list[FileInfo]`
    *   返回至少包含`path`的条目。在可用时包括`is_dir`、`size`、`modified_at`。按`path`排序以获得确定性输出。
*   `read(file_path: str, offset: int = 0, limit: int = 2000) -> str`
    *   返回带编号的内容。如果文件不存在，则返回`"错误：找不到文件 '/x'"`。
*   `grep_raw(pattern: str, path: Optional[str] = None, glob: Optional[str] = None) -> list[GrepMatch] | str`
    *   返回结构化匹配项。对于无效的正则表达式，返回一个字符串，如`"无效的正则表达式模式：..."`（不要引发异常）。
*   `glob_info(pattern: str, path: str = "/") -> list[FileInfo]`
    *   将匹配的文件作为`FileInfo`条目返回（如果没有，则返回空列表）。
*   `write(file_path: str, content: str) -> WriteResult`
    *   仅创建。如果发生冲突，则返回`WriteResult(error=...)`。成功后，设置`path`，对于状态后端，设置`files_update={...}`；外部后端应使用`files_update=None`。
*   `edit(file_path: str, old_string: str, new_string: str, replace_all: bool = False) -> EditResult`
    *   除非`replace_all=True`，否则强制`old_string`的唯一性。如果未找到，则返回错误。成功时包括`occurrences`。

支持类型：

*   `WriteResult(error, path, files_update)`
*   `EditResult(error, path, files_update, occurrences)`
*   `FileInfo`，包含字段：`path`（必需），可选`is_dir`、`size`、`modified_at`。
*   `GrepMatch`，包含字段：`path`、`line`、`text`。