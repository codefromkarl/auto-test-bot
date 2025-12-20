# 浏览器管理器能力契约

本文档定义了新架构中 BrowserManager 必须提供的能力接口，用于确保迁移过程中的完整性和一致性。

## 核心能力需求

基于 `src/executor/workflow_executor.py` 的实际调用分析，新 BrowserManager 必须提供以下接口：

### 1. 生命周期管理
- `initialize()` - 初始化浏览器实例
- `close()` - 关闭浏览器实例

### 2. 页面操作
- `navigate_to(url: str)` - 导航到指定URL
- `get_page_url() -> str` - 获取当前页面URL
- `wait_for_selector(selector: str, timeout: Optional[int] = None)` - 等待元素出现
- `click_element(selector: str)` - 点击元素
- `fill_input(selector: str, value: str)` - 填写输入框

### 3. 状态和诊断
- `take_screenshot() -> str` - 截图（返回图片路径）
- `assert_logged_in() -> bool` - 检查登录状态

### 4. 属性访问
- `page` - Playwright Page 对象（用于高级操作）

## 实现要求

### 基础要求
1. **方法签名一致性**：必须与上述签名完全匹配
2. **错误处理**：提供清晰的错误信息和异常类型
3. **返回值**：遵循指定的返回值类型
4. **超时处理**：支持合理的默认超时时间

### 质量要求
1. **稳定性**：在高并发或长时间运行时保持稳定
2. **性能**：操作响应时间在合理范围内
3. **兼容性**：支持目标浏览器版本
4. **可观测性**：提供日志记录和调试信息

## 当前状态

### Legacy 实现 (src/browser.py)
- ✅ 完整实现所有能力
- ✅ 包含登录态管理、诊断等高级功能
- ✅ 经过生产环境验证

### New 实现 (src/browser_manager.py)
- ❌ 存在明显 bug (navigate_to 返回逻辑错误)
- ❌ 缺少 `assert_logged_in()` 等关键方法
- ❌ Playwright 启动方式不正确
- ❌ 功能不完整，无法直接替代

## 迁移策略

### 阶段目标
1. **Phase 0**：明确能力契约（本文档）
2. **Phase 1**：修复 browser_manager.py 使其满足契约
3. **Phase 2**：重构 browser.py 为门面适配器
4. **Phase 3**：逐步迁移调用方
5. **Phase 4**：移除旧实现

### 验证标准
- [ ] 所有 workflow_executor.py 中的调用点都能正常工作
- [ ] 新旧实现的输出行为等价
- [ ] 所有测试用例通过
- [ ] CI 检查确保无旧引用

## 风险控制

### 回滚机制
- 配置开关支持 legacy/new 实现切换
- 保留 `browser_legacy.py` 作为备份

### 质量保证
- 单元测试覆盖所有方法
- 集成测试验证端到端流程
- 性能基准测试确保无回归

---

**版本**: v1.0
**最后更新**: 2025-12-17
**负责人**: 架构重构团队