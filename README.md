# Auto Test Bot

自动化测试机器人 - 基于 Playwright 和 Chrome DevTools MCP 的深度监控系统，用于 Web 应用的端到端自动化测试和智能错误诊断。

## 🎯 功能特性

- **智能自动化**: 基于 Playwright 的浏览器自动化测试
- **深度监控**: 集成 Chrome DevTools MCP 进行开发者工具级别监控
- **AI 诊断**: AI Agent 原生的错误分析和智能诊断
- **定时执行**: 支持 Cron 定时任务，24/7 无人值守运行
- **实时日志**: 完整的测试过程记录和错误追踪
- **多格式报告**: JSON 和 HTML 格式的结构化测试报告
- **性能监控**: 实时性能指标收集和分析
- **可视化支持**: 测试过程截图和快照

## 🏗️ 架构设计

```
auto-test-bot/
├── config/                 # 配置文件
│   ├── config.yaml        # 主配置文件
│   └── mcp_config.yaml    # MCP 监控配置
├── src/
│   ├── main.py            # 主程序入口和流程控制
│   ├── browser.py         # 浏览器管理和基础操作
│   ├── mcp/               # MCP 深度监控模块
│   │   ├── console.py      # 控制台日志监控
│   │   ├── network.py      # 网络请求分析
│   │   ├── performance.py  # 性能追踪器
│   │   ├── dom.py          # DOM 调试器
│   │   └── diagnostic.py  # 错误诊断器
│   ├── steps/             # 测试步骤模块
│   │   ├── open_site.py    # 网站访问测试
│   │   ├── test_step.py     # 基础测试步骤类
│   │   ├── custom_step.py  # 自定义测试步骤
│   │   └── validate.py    # 结果验证模块
│   ├── reporter/          # 报告生成模块
│   │   ├── formatter.py    # 报告格式化器
│   │   ├── analyzer.py     # 数据分析器
│   │   └── logger.py       # 测试日志记录
│   └── utils/             # 通用工具模块
│       ├── config.py       # 配置管理器
│       ├── timer.py        # 性能计时器
│       └── logger.py       # 日志系统
├── tests/                 # 测试和验证文件
│   ├── manual_test.md    # 手动测试指南
│   ├── unit/              # 单元测试
│   └── integration/        # 集成测试
├── docs/                  # 项目文档
│   ├── architecture.md    # 架构设计文档
│   ├── requirements.md   # 需求规格文档
│   └── api.md            # API 文档
├── cron/                  # 定时任务脚本
│   └── cronjob.sh        # Cron 执行脚本
└── scripts/               # 辅助脚本
    ├── setup.sh          # 环境设置脚本
    └── health_check.sh   # 健康检查脚本
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
# 调试模式运行
python src/main.py --debug

# 指定配置文件
python src/main.py --config path/to/config.yaml

# MCP 深度诊断模式
python src/main.py --mcp-diagnostic
```

## ⚙️ 配置说明

### config.yaml
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

### mcp_config.yaml
```yaml
mcp:
  server_url: "http://localhost:3000"
  auth_token: "your-auth-token"
  tools:
    console_messages: true
    network_requests: true
    performance_tracing: true
    dom_debug: true
```

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

1. **网站访问** - 验证页面可访问性和关键元素存在
2. **文生图测试** - 输入提示词，生成图片并验证结果
3. **图生视频测试** - 基于图片生成视频并验证结果
4. **智能诊断** - 失败时自动进行深度分析
5. **报告生成** - 生成详细的测试报告

## 📝 日志和报告

- **测试日志**: `logs/test_*.log`
- **MCP 数据**: `mcp_data/` 目录
- **错误截图**: `screenshots/` 目录
- **测试报告**: JSON 格式的结构化报告

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

- 测试成功率
- 平均执行时间
- 错误类型分布
- 性能指标趋势

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