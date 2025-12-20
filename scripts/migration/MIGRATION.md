# Migration Guide: Workflow-First Architecture

## 概述

本文档描述从旧版架构迁移到新的Workflow-First架构的步骤。

## 主要变更

### 1. 架构重构
- **旧**: 基于步骤的通用执行（steps/*.py）
- **新**: Workflow→Phase→Action的分层架构

### 2. 配置格式变更
- **旧**: config/config.yaml中的测试步骤配置
- **新**: workflows/目录中的YAML DSL v1格式

### 3. 程序入口变更
- **旧**: `python src/main.py`
- **新**: `python src/main_workflow.py --workflow workflows/example.yaml`

## 迁移步骤

### 1. 安装依赖
新的架构需要相同的依赖，无需额外安装。

### 2. 创建Workflow配置
将现有的测试配置转换为Workflow DSL v1格式：

```yaml
# workflows/my_test.yaml
workflow:
  name: my_test_workflow
  phases:
    - name: navigation
      steps:
        - open_page:
            url: "http://your-target.com"
    - name: interaction
      steps:
        - input:
            selector: "#prompt-input"
            text: "测试提示词"
        - click:
            selector: "#generate-btn"
```

### 3. 运行新架构
```bash
# 运行Workflow
python src/main_workflow.py --workflow workflows/my_test.yaml

# 带调试模式
python src/main_workflow.py --workflow workflows/my_test.yaml --debug
```

### 4. 自定义Actions
如需自定义Action，继承Action基类：

```python
from models.action import Action
from models.context import Context

class CustomAction(Action):
    def get_step_name(self):
        return "custom_action"

    def execute(self, context):
        # 实现自定义逻辑
        return context
```

### 5. MCP集成
MCP现在作为纯观察者，配置保持不变：
- MCP在`config/config.yaml`中的`mcp`部分配置
- 默认启用，自动收集执行证据

### 6. 报告格式
新的报告系统生成决策导向的JSON报告：
- 成功判定基于任务完成，而非质量评估
- 包含失败分析和改进建议

## 向后兼容性

### 临时支持
为确保平滑迁移，旧版本仍可运行：
```bash
# 旧版本（仍在支持）
python src/main.py --config config/config.yaml
```

### 迁移检查清单
- [ ] 创建Workflow配置文件
- [ ] 验证YAML语法
- [ ] 测试单个Action
- [ ] 执行完整Workflow
- [ ] 检查MCP证据收集
- [ ] 验证报告生成

## 故障排除

### 常见问题
1. **YAML语法错误**: 使用在线YAML验证器检查
2. **Selector无效**: 更新为当前应用的CSS选择器
3. **Action参数错误**: 检查必需的参数是否提供
4. **MCP启动失败**: 检查mcp配置是否正确

### 获取帮助
```bash
# 查看示例Workflow
cat workflows/example.yaml

# 查看所有可用命令
python src/main_workflow.py --help
```

## 新架构优势

1. **清晰职责分离**: Workflow/Phase/Action层次明确
2. **原子化操作**: Action仅做最小交互，无业务逻辑
3. **状态集中管理**: Context作为状态载体，线程安全
4. **观察者模式**: MCP作为独立证据采集器
5. **线性约束**: 简化执行模型，易于调试
6. **决策导向报告**: 聚焦任务完成度，支持业务决策