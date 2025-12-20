# auto-test-bot TODO（已归档）

> ⚠️ **状态更新**：本TODO已归档，RF迁移项目已完成
>
> **替代文档**：[optimization_todo.md](./optimization_todo.md) - 当前项目优化计划
>
> **完成情况**：
> - ✅ RF迁移项目超预期完成（59个FC全量迁移）
> - ✅ 语义Action体系建立（260个rf_前缀Action）
> - ✅ 技术债务大幅减少（369个硬编码Selector消除）
> - ✅ 项目架构优化和升级完成

---

## 🔴 第一阶段（必须完成｜否则后续全是空转）

### 1. 拆分页面状态（Page State）

- [ ] 定义页面状态枚举（最少 4 个）
  - `HOME`（首页 / 营销页）
  - `AI_CREATE`（AI创作总览页）
  - `TEXT_TO_IMAGE`（文生图页）
  - `IMAGE_TO_VIDEO`（图生视频页，可后置）

- [ ] 新建 `page_state.py`
  - 仅负责定义状态常量 / Enum

✅ 完成标准：
- 代码里**不再用“感觉”判断页面**，而是明确状态

---

### 2. 给每个关键页面写「识别函数」

- [ ] 实现 `is_home_page(page)`
- [ ] 实现 `is_ai_create_page(page)`
- [ ] 实现 `is_text_to_image_page(page)`

建议特征（任选 2~3 个即可）：
- URL / hash
- 顶部导航选中状态
- 页面独有文案或按钮

❌ 不追求 100% 精准，80% 即可

✅ 完成标准：
- 能在日志中明确打印：`current_page_state = HOME / AI_CREATE / ...`

---

### 3. 重构 `OpenSiteStep`（降级职责）

当前问题：
- `OpenSiteStep` 同时做了 **打开 + 页面判断 + 业务验证** ❌

要改成：
- [ ] `OpenSiteStep` **只负责**：
  - 打开首页 URL
  - 验证「这是首页」

首页最小断言示例：
- NowHi logo 存在
- 顶部导航存在

❌ 不允许在此步骤：
- 查找 prompt
- 查找 textarea

✅ 完成标准：
- 首页能稳定通过，但不做任何 AI 功能判断

---

## 🟡 第二阶段（真正把流程走通）

### 4. 新增导航步骤：`NavigateToAICreateStep`

- [ ] 新建 Step：`navigate_to_ai_create`
- [ ] 行为：
  - 点击顶部导航「AI创作」或首页 Banner「AI创作」按钮

- [ ] 断言：
  - 页面状态从 `HOME` → `AI_CREATE`

✅ 完成标准：
- 日志中清晰看到页面状态迁移

---

### 5. 新增功能页导航：进入文生图

- [ ] 新建 Step：`NavigateToTextToImageStep`
- [ ] 行为：
  - 在 AI创作页点击「文生图」

- [ ] 断言：
  - 页面状态变为 `TEXT_TO_IMAGE`

✅ 完成标准：
- 只有进入该状态后，才允许生成图片

---

## 🟢 第三阶段（业务自动化本体）

### 6. 约束业务步骤的「前置页面状态」

- [ ] `GenerateImageStep` 增加前置校验：
  - 当前页面必须是 `TEXT_TO_IMAGE`

- [ ] 若状态不对：
  - 直接失败（并给出清晰错误）

✅ 完成标准：
- 不再出现「在首页找 prompt」的逻辑错误

---

### 7. Selector 语义化（替换脆弱 selector）

- [ ] 优先使用：
  - `get_by_role`
  - `get_by_placeholder`
  - `get_by_text`

- [ ] 避免：
  - 强结构 selector（`.xxx > div:nth-child(3)`）

✅ 完成标准：
- UI 小改不需要立刻改自动化

---

## 🔵 第四阶段（可维护 / 可诊断）

### 8. 每个 Step 输出统一的状态日志

每个 Step result 至少包含：

```json
{
  "step": "navigate_to_ai_create",
  "success": true,
  "current_url": "...",
  "page_state": "AI_CREATE",
  "action": "click_nav_ai_create"
}
```

- [ ] 在失败时输出：
  - 当前 URL
  - 当前页面状态

✅ 完成标准：
- 失败日志可读，不靠猜

---

### 9. 区分两类失败（非常重要）

- [ ] 页面状态错误（流程 / 逻辑错误）
- [ ] selector 找不到（UI / 前端错误）

不要混在一个 error 里。

---

## ⚪ 第五阶段（进阶，可后置）

### 10. 引入 Page Object（当 selector 开始重复）

- [ ] `HomePage`
- [ ] `AICreatePage`
- [ ] `TextToImagePage`

职责：
- 封装 selector
- 封装页面级动作

---

### 11. 把测试流程配置化

- [ ] 支持类似：

```yaml
test_flow:
  - open_site
  - goto_ai_create
  - goto_text_to_image
  - generate_image
```

---

## ✅ 当前里程碑定义（很重要）

**MVP 成功标准（先别贪）**：

- [ ] 能从首页 → AI创作 → 文生图
- [ ] 能稳定定位 prompt 输入框
- [ ] 不生成图片也没关系

> 只要这个跑通，你的 auto-test-bot 就已经超过 80% UI 自动化项目。

---

> 建议：这个 TODO.md 就放在仓库根目录，**每完成一项就勾一项**。
> 
> 你现在不是在“试错”，而是在**按工程路径推进一个 Agent 系统**。