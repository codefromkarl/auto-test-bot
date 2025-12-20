Always reply in simplified Chinese.

# Project Context & Tools

## Semantic Search (mgrep)
您可以使用一个名为 `mgrep` 的语义搜索工具。
**规则:** 在需要进行基于概念或自然语言的查询时，尤其是当精确关键词匹配（`search_file_content`）不足时，**必须**通过 `run_shell_command` 调用 `mgrep`。

**使用示例:**
1. **代码搜索:** `mgrep "验证用户登录逻辑" src/`
2. **网络搜索:** `mgrep --web --answer "pytest fixtures 的最佳实践"`

**何时使用:**
- 当不确定功能的精确命名时（例如，搜索“auth 中间件”）。
- 理解高层架构模式。
- 需要在本地文件或网络上进行语义搜索以查找相关信息。