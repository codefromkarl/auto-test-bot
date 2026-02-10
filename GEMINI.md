
- 总是用中文回复 -->

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

## UI Automation Protocol (Hard Rules)

**1. Fail-Fast (快速失败原则)**
- **UI 交互**（点击、断言可见性）必须使用 **短超时 (2000ms - 5000ms)**。
- 禁止使用默认长超时（30s+）等待 UI 元素，除非是 AIGC 生成过程。
- 如果操作是探测性的（如检查空态），必须显式设置 `timeout: 2000`。

**2. Diagnosis First (诊断优先)**
- 遇到 `TimeoutError` 或 `ElementNotFound` 时，**严禁盲目修改选择器**。
- **必须**先执行以下步骤之一：
  1. 读取 `screenshots/errors/` 下最新的失败截图。
  2. 检查自动生成的 `.ai/issues/ISSUE-AUTO-*.md` 报告。
  3. (如有) 使用 `dump_dom` 或相关工具获取页面结构。
- 只有在看到证据后，才能修改代码。

**3. Interception Handling (遮罩处理)**
- 遇到 `intercepts pointer events` 错误时，说明有弹窗/遮罩未消失。
- **必须**在点击前添加显式等待：
  ```yaml
  - action: "wait_for"
    condition:
      selector: ".el-overlay, .loading-mask"
      not_visible: true
    timeout: 5000
  ```

**4. Loop Optimization (闭环优化)**
- 遇到阻塞性问题（Blocker），不要让测试无限重试。
- 确保测试配置了 `stop_on_phase_failure: true` 和合理的 `max_step_duration_ms`。
