# Scripts Directory

本目录包含各种开发和调试脚本，按功能分类组织。

## 目录结构

### debug/
调试和问题诊断脚本

- `debug_navigation.py` - 调试页面导航问题
- `debug_page_content.py` - 调试页面内容获取
- `debug_page_detailed.py` - 详细调试页面状态
- `debug_page_recognition.py` - 调试页面元素识别
- `diagnose_navigation_issue.py` - 诊断导航相关问题

### auth/
认证和状态保存脚本

- `save_login_state.py` - 保存登录状态
- `save_real_auth_state.py` - 保存真实的认证状态
- `auth_session.example.json` - 会话认证数据模板（示例）
- `auth_state.example.json` - 认证状态模板（示例）
- `auth_state_real.example.json` - 真实环境认证状态模板（示例）

### test/
各种测试脚本

- `test_browser_auth.py` - 浏览器认证测试
- `test_context_minimal.py` - 最小化上下文测试
- `test_context_simple.py` - 简单上下文测试
- `test_page_state.py` - 页面状态测试
- `test_page_state_simple.py` - 简单页面状态测试
- `test_refactor_final.py` - 重构最终测试
- `test_refactor_validation.py` - 重构验证测试
- `test_simple.py` - 简单测试
- `test_simple_refactor.py` - 简单重构测试
- `test_snapshot.py` - 快照测试
- `test_snapshot_detailed.py` - 详细快照测试

### migration/
迁移相关文档

- `MIGRATION.md` - 系统迁移指南

## 顶层脚本

以下脚本位于 `scripts/` 目录下，不属于任何子目录：

- `run_workflow_test.py` - 运行工作流测试
- `validate_environment.py` - 验证开发环境配置

## 使用说明

1. **调试脚本**：在开发遇到问题时使用，帮助定位和解决问题
2. **认证脚本**：用于保存和管理各种认证状态
3. **测试脚本**：用于验证系统各部分功能
4. **迁移文档**：系统升级和迁移时的参考

## 注意事项

- 运行这些脚本前请确保在正确的 Python 环境中
- 部分脚本需要特定的依赖或配置
- 测试脚本可能会产生临时文件，请在使用后清理
- `scripts/auth/*.json` 为本地敏感认证文件，禁止提交到 Git
