# Auto Test Bot

自动化测试机器人 - 基于 Playwright 的稳定执行引擎，配备 Chrome DevTools MCP 作为调试显微镜。

> **核心理念**: Playwright 负责稳定执行，MCP 只用于看清问题，AI 帮助快速修复

## 🎯 功能特性

### 执行层（稳定可靠）
- **Playwright 自动化**: 唯一的测试执行引擎，确保 CI/CD 稳定可复现
- **确定性测试**: 固定 selectors、固定等待条件、固定断言
- **定时执行**: 支持 Cron 定时任务，24/7 无人值守运行

### 调试层（深度观测）
- **Chrome DevTools MCP**: 仅在失败时启用的深度调试工具
- **行为观测**: DOM 变化、网络请求、路由事件、JS 错误精准捕获
- **证据采集**: 结构化失败现场，为 AI 分析提供完整上下文

### 智能层（辅助决策）
- **AI 诊断**: 基于证据的智能错误分析
- **修复建议**: AI 提供代码修复建议，人工审核后应用
- **多格式报告**: JSON 和 HTML 格式的结构化测试报告

### 高级测试能力（新增）
- **复杂场景测试**: 多项目管理、并发操作、数据完整性验证
- **边界条件测试**: 输入验证、资源约束、错误恢复边界测试
- **网络模拟**: 7种网络条件（3G/4G/离线/不稳定）模拟测试
- **智能数据管理**: 动态数据生成、数据隔离、数据变异功能
- **增强错误处理**: 智能重试、优雅降级、用户友好的错误提示

## 🏗️ 架构设计

### 分层架构

```
【执行层 - 确定】
├── browser.py           # Playwright 浏览器管理
├── steps/              # 测试步骤实现
└── workflows/          # 测试流程定义

【调试层 - 探索】
└── debug/              # MCP 调试工具（可选）
    ├── mcp_helper.py    # MCP 辅助类
    ├── evidence_collector.py  # 证据采集
    └── analyzer.py      # 调试分析器

【智能层 - 建议】
├── reporter/           # 报告生成器
└── ai/                # AI 分析引擎（规划中）
```

### 目录结构

```
auto-test-bot/
├── config/                 # 配置文件
│   ├── config.yaml        # 主配置文件
│   ├── debug_config.yaml   # 调试模式配置
│   └── ci_config.yaml     # CI 环境配置
├── src/
│   ├── main_workflow.py    # 主程序入口
│   ├── browser.py         # Playwright 浏览器管理
│   ├── browser_manager.py  # 浏览器管理兼容层
│   ├── debug/             # MCP 调试工具
│   │   ├── mcp_bridge.py  # MCP 桥接器
│   │   └── collector.py   # 证据采集器
│   ├── steps/             # 测试步骤
│   ├── workflows/         # 测试流程定义
│   ├── reporter/          # 报告生成
│   └── utils/             # 通用工具
│       ├── test_data_manager.py     # 测试数据管理器
│       └── network_simulator.py     # 网络模拟器
├── tests/                 # 测试文件
├── evidence/              # MCP 采集的证据
├── docs/                  # 项目文档
│   ├── chrome-devtools-mcp-guide.md  # MCP 使用指南
│   ├── architecture.md    # 架构设计
│   ├── RF_MIGRATION_FINAL_SUMMARY.md  # RF迁移完成总结
│   ├── rf_full_migration_verification_report.md  # RF迁移验证报告
│   ├── optimization_todo.md  # 项目优化计划
│   ├── complex_scenario_guide.md     # 复杂场景测试指南
│   ├── boundary_condition_guide.md  # 边界条件测试指南
│   └── api.md            # API 参考
├── workflows/             # 测试工作流
│   ├── at/               # 冒烟测试用例
│   ├── e2e/              # 端到端测试用例
│   ├── fc/               # 功能测试用例
│   │   ├── naohai_FC_NH_*.yaml       # 原版FC文件（59个）
│   │   └── naohai_FC_NH_*_rf.yaml    # RF语义化版本（59个）
│   ├── resilience/       # 容错和恢复测试
│   │   ├── naohai_complex_multi_project_management.yaml    # 多项目管理测试
│   │   ├── naohai_boundary_condition_stress_test.yaml      # 边界条件测试
│   │   ├── naohai_enhanced_error_handling_test.yaml       # 增强错误处理测试
│   │   └── naohai_resilience_test.yaml                   # 容错性测试
│   ├── rt/               # 回归测试用例
│   └── shared/           # 共享工作流组件
└── scripts/               # 辅助脚本
```

## 🚀 快速开始

### 环境要求

- Python 3.8+
- Node.js (用于 MCP 服务器)
- Chrome/Chromium 浏览器

### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd auto-test-bot
```

2. **创建虚拟环境**
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. **安装依赖**
```bash
pip install -r requirements.txt
playwright install
```

4. **配置 MCP 服务器**
```bash
# 参考 config/mcp_config.yaml 模板
cp config/mcp_config.yaml.example config/mcp_config.yaml
# 编辑配置文件填入实际参数
```

5. **配置测试参数**
```bash
# 编辑 config/config.yaml
# 设置测试网站 URL、选择器、超时等参数
```

6. **运行测试**
```bash
python src/main.py
```

### 手动运行特定测试

```bash
# 正常执行（纯 Playwright）
python src/main.py

# 调试模式（失败时自动启用 MCP）
python src/main.py --debug

# MCP 深度诊断模式（全程启用 MCP）
python src/main.py --mcp-diagnostic

# 指定配置文件
python src/main.py --config path/to/config.yaml
```

> ⚠️ **重要提醒**: 生产环境和 CI 应始终使用默认模式，不要启用 MCP

## ⚙️ 配置说明

### 配置文件清单

- **config.yaml** - 主配置文件（默认使用）
- **debug_config.yaml** - 调试模式配置（本地开发）
- **ci_config.yaml** - CI/生产环境配置（禁用 MCP）

### 主配置 (config.yaml)
```yaml
test:
  url: "https://your-test-site.com"
  timeout: 30000
  selectors:
    prompt_input: "#prompt-input"
    generate_button: "#generate-btn"
    image_result: ".image-result"
    video_result: ".video-result"

steps:
  open_site: true
  generate_image: true
  generate_video: true
```

### 调试配置 (debug_config.yaml)
```yaml
debug:
  enable_devtools_mcp: true      # 开启 MCP
  capture_on_failure: true        # 失败时采集证据
  mcp_tools:
    console: true
    network: true
    dom_debug: true
    screenshot: true
```

### CI 配置 (ci_config.yaml)
```yaml
debug:
  enable_devtools_mcp: false     # 严禁 MCP
  evidence_tools:
    playwright_screenshot: true   # 仅用 Playwright
```

> 💡 **提示**: 使用 `--config` 参数指定配置文件
> - 本地调试: `--config debug_config.yaml`
> - CI 环境: `--config ci_config.yaml`

## 📊 监控功能

### 控制台监控
- JavaScript 错误自动捕获
- console.log/warning/error 记录
- 错误堆栈分析

### 网络监控
- API 请求/响应监控
- 失败请求自动识别
- 响应时间统计

### 性能监控
- 页面加载时间
- 资源加载性能
- 性能瓶颈识别

### DOM 调试
- 元素状态检查
- 页面结构分析
- 布局问题诊断

## 🕐 定时任务

设置 Cron 任务每日凌晨 2 点执行：

```bash
# 编辑 crontab
crontab -e

# 添加任务
0 2 * * * /path/to/auto-test-bot/cron/cronjob.sh
```

## 📋 测试流程

### 基础功能测试
1. **网站访问** - 验证页面可访问性和关键元素存在
2. **文生图测试** - 输入提示词，生成图片并验证结果
3. **图生视频测试** - 基于图片生成视频并验证结果

### 高级测试能力
4. **复杂场景测试** - 多项目管理、并发操作、数据完整性验证
5. **边界条件测试** - 输入验证、资源约束、错误恢复边界测试
6. **网络模拟测试** - 多种网络条件下的系统行为验证
7. **智能诊断** - 失败时自动进行深度分析
8. **报告生成** - 生成详细的测试报告

## 🎯 RF语义化迁移（已完成）

### 迁移成果
- ✅ **全量完成**：59个FC全部迁移为RF语义化版本
- ✅ **质量提升**：平均改进分数79.8/100
- ✅ **技术债务减少**：消除369个硬编码Selector
- ✅ **语义Action**：引入260个语义化Action

### 使用方式
```bash
# 使用RF语义化版本
python src/main_workflow.py --workflow workflows/fc/naohai_FC_NH_XXX_rf.yaml

# 使用原版（向后兼容）
python src/main_workflow.py --workflow workflows/fc/naohai_FC_NH_XXX.yaml
```

### 详细文档
- [RF迁移完成总结](docs/RF_MIGRATION_FINAL_SUMMARY.md)
- [RF迁移验证报告](docs/rf_full_migration_verification_report.md)

## 📝 日志和报告

- **测试日志**: `logs/test_*.log`
- **MCP 证据**: `evidence/` 目录（仅调试模式）
- **错误截图**: `screenshots/` 目录
- **测试报告**: JSON 格式的结构化报告

## 📚 项目文档索引

### 快速导航
- **📖 完整索引**：[文档索引](docs/DOCUMENTATION_INDEX.md) - 按功能分类的完整文档导航
- **🏗️ 架构文档**：[架构总览](docs/architecture-design/README.md) - 三层架构设计体系
- **🎉 RF迁移文档**：[迁移总结](docs/RF_MIGRATION_FINAL_SUMMARY.md) - 59个FC全量迁移成果
- **⚡ 项目优化**：[优化计划](docs/optimization_todo.md) - 详细的优化任务清单
- **🚀 测试增强**：[测试增强完成报告](runs/2025-12-21/test_enhancement_completion_report.md) - 复杂场景和边界条件测试能力

### 核心文档
| 分类 | 文档 | 用途 | 状态 |
|------|------|------|------|
| **项目指南** | README.md | 项目使用和配置 | ✅ 最新 |
| **架构设计** | architecture-design/README.md | 架构总览和导航 | ✅ 完整 |
| **RF迁移** | RF_MIGRATION_FINAL_SUMMARY.md | 迁移成果和总结 | ✅ 完成 |
| **工作流** | README_WORKFLOWS.md | 工作流使用指南 | ✅ 有效 |
| **MCP调试** | chrome-devtools-mcp-guide.md | 调试工具使用 | ✅ 有效 |
| **复杂场景** | docs/complex_scenario_guide.md | 复杂场景测试指南 | ✅ 新增 |
| **边界条件** | docs/boundary_condition_guide.md | 边界条件测试指南 | ✅ 新增 |
| **数据管理** | docs/test_data_management_best_practices.md | 测试数据管理最佳实践 | ✅ 新增 |

### 历史文档（已归档）
- `docs/auto_test_bot_todo_archived.md` - 原项目TODO（已归档）
- `docs/rf_small_scale_migration_report_archived.md` - 小规模迁移报告（已归档）
- `docs/architecture-design/code-templates_archived.md` - 原代码模板（已归档）

### 使用建议
1. **新成员**：先阅读项目README，再根据角色查看相应文档
2. **开发人员**：重点关注架构设计和RF迁移文档
3. **测试人员**：重点参考工作流指南和MCP调试文档
4. **项目管理**：参考RF迁移总结和优化计划文档

## 🔍 MCP 使用指南

> **必读**: [Chrome DevTools MCP 使用指南](docs/chrome-devtools-mcp-guide.md)

该指南详细说明了：
- MCP 的正确使用场景和边界
- 禁止的用途和常见误区
- 调试模式配置方法
- 失败证据采集规范
- AI 辅助修复的工作流程

**核心原则**: MCP 用来"看清楚"，代码用来"跑稳定"，AI 用来"帮人更快修"。

## 🛠️ 开发和调试

### 本地开发
```bash
# 开发模式运行
python src/main.py --debug --mcp-diagnostic

# 运行单元测试
python -m pytest tests/

# 代码格式化
black src/ tests/
```

### 故障排查
1. 检查浏览器是否正确安装
2. 验证 MCP 服务器连接
3. 查看配置文件格式
4. 检查网络连接和目标网站可访问性

## 📈 监控指标

### 基础指标
- 测试成功率
- 平均执行时间
- 错误类型分布
- 性能指标趋势

### 高级指标（新增）
- 复杂场景测试覆盖率
- 边界条件测试通过率
- 网络模拟测试结果
- 错误恢复成功率
- 数据一致性验证结果
- 并发操作稳定性指标

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交变更
4. 创建 Pull Request

## 📄 许可证

MIT License

## 🆘 支持

如有问题或需要帮助：
- 查看文档 `docs/` 目录
- 检查 `tests/manual_test.md` 手动测试指南
- 查看 `logs/` 目录的错误日志