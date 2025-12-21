# Active Context

## 🚀 Current Focus
- **Issue**: [ISSUE-AUTO-1766320095](issues/ISSUE-AUTO-1766320095.md) (Task)
- **Status**: **In Progress**
- **Last Action**: 已创建新 Issue 并登记到索引，准备执行层级选择器重构。

## 📝 Handover Notes
- 需要新增 AIGC 选择器层级配置并提供扁平化编译兼容。
- 重点文件：`config/main_config_with_testid.yaml`、`src/utils/config_loader.py`、新增层级编译模块。
- **Next Action**: 实现层级定位器编译器并补充单元测试。

## 💻 Commands
```bash
python3 -m pytest tests/unit/test_locator_hierarchy.py
```
