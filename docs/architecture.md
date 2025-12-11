# 系统架构文档

本文档详细描述自动化测试机器人的系统架构、模块设计和实现细节。

## 📋 目录

1. [系统概述](#系统概述)
2. [架构设计](#架构设计)
3. [模块架构](#模块架构)
4. [数据流](#数据流)
5. [集成架构](#集成架构)
6. [部署架构](#部署架构)

## 🎯 系统概述

### 系统目标
自动化测试机器人是一个基于 Playwright + Chrome DevTools MCP 的深度监控系统，用于验证 NowHi 动漫生成系统的"文生图 → 图生视频"核心流程的可用性。

### 核心特性
- **深度监控**: 集成 Chrome DevTools MCP 进行开发者工具级别的监控
- **智能诊断**: AI Agent 原生的错误分析和诊断能力
- **混合架构**: Playwright 稳定性 + MCP 深度监控能力
- **定时执行**: 支持 Cron 定时任务，24/7 无人值守运行

### 技术栈
- **前端自动化**: Playwright (Python)
- **深度监控**: Chrome DevTools MCP
- **开发语言**: Python 3.8+
- **任务调度**: Cron + Shell
- **配置管理**: YAML
- **报告生成**: JSON + HTML

## 🏗️ 架构设计

### 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                        定时调度系统 (Cron)                     │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                    主程序 (main.py)                      │
│                                                         │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                  流程编排层                           │ │
│  │  • 协调测试步骤执行                                      │ │
│  │  • 错误处理和恢复                                        │ │
│  │  • 智能诊断触发                                         │ │
│  │  • 报告生成和保存                                       │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────┬───────────────────────────────────────┘
                      │
          ┌─────────┼─────────┐
          │         │         │
          ▼         ▼         ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│  Browser Layer  │ │    MCP Layer    │ │   Step Layer    │
│                 │ │                 │ │                 │
│ • Playwright    │ │ • Console      │ │ • OpenSite      │
│ • 浏览器管理     │ │   Monitor       │ │ • GenerateImage │
│ • 页面导航       │ │ • Network      │ │ • GenerateVideo │
│ • 元素操作       │ │   Analyzer      │ │ • Validate      │
│ • 截图功能       │ │ • Performance   │ │                 │
│                 │ │   Tracer        │ │                 │
└─────────────────┘ │ • DOM Debugger   │ └─────────────────┘
                      │ • Error         │
                      │   Diagnostic     │
                      └─────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                验证和报告层                                 │
│                                                         │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                 Reporter Layer                         │ │
│  │                                                         │ │
│  │ • ReportFormatter        • DiagnosticAnalyzer           │ │
│  │ • Result Formatting      • Error Analysis               │ │
│  │ • HTML/JSON Generation     • Recommendation             │ │
│  │ • Screenshot Integration  • Report Storage               │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                         │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                Utils Layer                              │ │
│  │                                                         │ │
│  │ • ConfigLoader            • Timer                         │ │
│  │ • MCPConfigLoader         • Performance Metrics            │ │
│  │ • Logger                  • TestLogger                     │ │
│  │ • Selectors               • File Utils                      │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 设计原则

#### 1. 分层架构
每一层职责单一，便于测试和维护：
- **Browser Layer**: 专注于浏览器基础操作
- **MCP Layer**: 专注于深度监控和诊断
- **Step Layer**: 专注于业务逻辑实现
- **Reporter Layer**: 专注于结果处理和报告

#### 2. 松耦合设计
模块间通过接口交互，支持独立开发和测试：
- 监控器可以独立启用/禁用
- 测试步骤可以独立执行
- 报告格式可以灵活配置

#### 3. 渐进式增强
- MVP 基础功能 → 高级诊断功能
- Playwright 稳定性 → MCP 深度能力
- 简单监控 → AI 辅助分析

## 🧩 模块架构

### Browser Layer (浏览器层)

#### BrowserManager
负责 Playwright 浏览器的生命周期管理。

```python
class BrowserManager:
    """浏览器管理器 - 核心功能"""

    async def initialize(self) -> bool
    async def navigate_to(self, url: str) -> bool
    async def wait_for_element(self, selector: str) -> bool
    async def click_element(self, selector: str) -> bool
    async def fill_input(self, selector: str, text: str) -> bool
    async def take_screenshot(self, filename: str) -> bool
```

**职责**:
- 浏览器实例创建和配置
- 页面导航和上下文管理
- 基础元素操作（点击、输入、等待）
- 截图和调试功能

### MCP Layer (监控层)

#### ConsoleMonitor
监控浏览器控制台输出和 JavaScript 错误。

```python
class ConsoleMonitor:
    """控制台监控器 - 深度功能"""

    def start_monitoring(self) -> None
    def stop_monitoring(self) -> Dict[str, Any]
    def add_message(self, message_data: Dict[str, Any]) -> None
    def get_javascript_errors(self) -> List[ConsoleMessage]
    def get_error_summary(self) -> Dict[str, Any]
```

#### NetworkAnalyzer
监控和分析网络请求。

```python
class NetworkAnalyzer:
    """网络分析器 - 深度功能"""

    def start_monitoring(self) -> None
    def stop_monitoring(self) -> Dict[str, Any]
    def add_request(self, request_data: Dict[str, Any]) -> None
    def get_api_requests(self) -> List[NetworkRequest]
    def get_performance_summary(self) -> Dict[str, Any]
```

#### PerformanceTracer
收集和分析性能指标。

```python
class PerformanceTracer:
    """性能追踪器 - 深度功能"""

    def start_tracing(self) -> bool
    def stop_tracing(self) -> Optional[PerformanceTrace]
    def get_performance_summary(self) -> Dict[str, Any]
    def has_performance_regression(self, baseline: Dict[str, float]) -> bool
```

#### DOMDebugger
检查和分析 DOM 结构。

```python
class DOMDebugger:
    """DOM 调试器 - 深度功能"""

    def create_snapshot(self, url: str, dom_data: Dict[str, Any]) -> Optional[DOMSnapshot]
    def find_element(self, selector: str) -> Optional[Dict[str, Any]]
    def analyze_layout_issues(self) -> Dict[str, Any]
    def get_latest_snapshot(self) -> Optional[DOMSnapshot]
```

#### ErrorDiagnostic
综合错误分析和诊断。

```python
class ErrorDiagnostic:
    """错误诊断器 - AI 辅助功能"""

    def diagnose_errors(self) -> DiagnosticReport
    def perform_root_cause_analysis(self, issues: List[Dict[str, Any]]) -> List[str]
    def generate_recommendations(self, issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]
```

### Step Layer (业务层)

#### OpenSiteStep
网站访问和基础验证。

#### GenerateImageStep
文生图流程测试。

#### GenerateVideoStep
图生视频流程测试。

#### ValidateStep
结果验证和综合判断。

### Reporter Layer (报告层)

#### ReportFormatter
格式化测试报告。

```python
class ReportFormatter:
    """报告格式化器"""

    def format_test_report(self, test_results: List[Dict[str, Any]],
                          mcp_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]
    def save_report(self, report: Dict[str, Any]) -> Dict[str, str]
    def _generate_html_report(self, report: Dict[str, Any]) -> str
```

### Utils Layer (工具层)

#### ConfigLoader
配置文件加载和验证。

#### Timer
性能计时和指标收集。

#### Logger
日志管理和格式化。

## 📊 数据流

### 执行流程数据流

```
定时触发
    │
    ▼
配置加载 ──┐──────────────┐
配置验证 │              │
    │              │
    ▼              ▼
浏览器初始化 ────┐
    │              │
    ▼              ▼
启动 MCP 监控 ──►─┐
    │              │ │
    ▼              ▼ ▼
执行测试步骤 ◄────►┘──────────────────►┐
    │              │ │
    ▼              │ ▼
停止 MCP 监控 ◄────►┘──────────────────►┐
    │              │ │
    ▼              ▼ ▼
错误诊断分析 ──►─┘──────────────────►┐
    │              │ │
    ▼              ▼ ▼
生成测试报告 ◄────────────────────────────►┘
    │
    ▼
保存报告文件
```

### 监控数据收集流

```
浏览器事件
    │
    ▼
Chrome DevTools Protocol
    │
    ▼
MCP Server
    │
    ├─► Console Events ◄─► ConsoleMonitor ◄─► 错误日志分析
    ├─► Network Events ◄─► NetworkAnalyzer ◄─► 请求分析
    ├─► Performance Events ◄─► PerformanceTracer ◄─► 性能分析
    └─► DOM Events ◄─► DOMDebugger ◄─► 结构分析
```

## 🔗 集成架构

### Playwright + MCP 混合模式

#### 职责分工
- **Playwright Layer**:
  - 稳定的浏览器操作
  - 基础元素交互
  - 页面导航控制

- **MCP Layer**:
  - 开发者工具级监控
  - 深度错误分析
  - 性能数据收集

#### 集成策略
```python
class AutoTestBot:
    async def execute_step(self, step_name: str):
        # 1. Playwright 执行基础操作
        step_result = await self.test_steps[step_name].execute()

        # 2. MCP 深度监控（在后台运行）
        if step_result['success']:
            # 成功时收集性能数据
            self._collect_performance_data()
        else:
            # 失败时触发深度诊断
            await self._trigger_deep_diagnostic()

        return step_result
```

### MCP 服务器集成

#### 连接管理
```python
class MCPConnectionManager:
    def __init__(self, config: Dict[str, Any]):
        self.server_url = config.get('mcp_server', {}).get('server_url')
        self.auth_token = config.get('mcp_server', {}).get('auth_token')
        self.connection_pool = []

    async def connect(self) -> bool:
        # 建立 WebSocket 连接
        # 验证服务器可用性
        # 设置心跳保持
        pass

    async def send_command(self, tool: str, params: Dict[str, Any]) -> Any:
        # 发送 MCP 命令
        # 等待响应
        # 错误处理和重试
        pass
```

## 🚀 部署架构

### 本地部署

```
auto-test-bot/
├── src/                    # 源代码
├── config/                 # 配置文件
├── logs/                   # 日志文件
├── reports/                # 测试报告
├── mcp_data/               # MCP 数据
├── screenshots/            # 截图文件
├── venv/                   # Python 虚拟环境
├── requirements.txt
├── cron/
│   └── cronjob.sh         # 定时任务脚本
└── README.md
```

### Docker 部署

```dockerfile
FROM python:3.9-slim

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    chromium \
    curl \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 安装 Playwright 浏览器
RUN python -m playwright install chromium
RUN python -m playwright install-deps

# 复制应用代码
COPY . /app
WORKDIR /app

# 创建必要目录
RUN mkdir -p logs reports mcp_data screenshots

# 设置权限
RUN chmod +x cron/cronjob.sh

# 暴露端口
EXPOSE 3000

# 启动命令
CMD ["python", "src/main.py"]
```

### Kubernetes 部署

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: auto-test-bot
spec:
  replicas: 1
  selector:
    matchLabels:
      app: auto-test-bot
  template:
    metadata:
      labels:
        app: auto-test-bot
    spec:
      containers:
      - name: auto-test-bot
        image: auto-test-bot:latest
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        env:
        - name: CONFIG_PATH
          value: "/app/config/config.yaml"
        volumeMounts:
        - name: config
          mountPath: /app/config
        - name: logs
          mountPath: /app/logs
        - name: reports
          mountPath: /app/reports
      volumes:
      - name: config
        configMap:
          name: auto-test-bot-config
      - name: logs
        persistentVolumeClaim:
          claimName: auto-test-bot-logs
      - name: reports
        persistentVolumeClaim:
          claimName: auto-test-bot-reports

---
apiVersion: batch/v1
kind: CronJob
metadata:
  name: auto-test-bot-cronjob
spec:
  schedule: "0 2 * * *"  # 每天凌晨 2 点
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: auto-test-bot
            image: auto-test-bot:latest
            args: ["python", "src/main.py"]
            env:
            - name: CONFIG_PATH
              value: "/app/config/config.yaml"
            restartPolicy: OnFailure
            volumeMounts:
            - name: config
              mountPath: /app/config
            - name: logs
              mountPath: /app/logs
          volumes:
          - name: config
            configMap:
              name: auto-test-bot-config
          - name: logs
            persistentVolumeClaim:
              claimName: auto-test-bot-logs
```

### 监控和运维

#### 健康检查
```python
# src/health_check.py
import asyncio
import aiohttp
import logging

class HealthChecker:
    async def check_browser_health(self) -> bool:
        """检查浏览器健康状态"""
        try:
            # 尝试创建浏览器实例
            async with async_playwright() as p:
                browser = await p.chromium.launch()
                await browser.close()
                return True
        except Exception:
            return False

    async def check_mcp_server_health(self) -> bool:
        """检查 MCP 服务器健康状态"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.mcp_server_url}/health",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    return response.status == 200
        except Exception:
            return False
```

#### 日志收集
```yaml
# 日志配置 (fluentd/conf/fluent.conf)
<source>
  @type tail
  path /app/logs/*.log
  tag auto-test-bot.*
</source>

<match>
  tag auto-test-bot.**
  @type elasticsearch
  host elasticsearch
  port 9200
  index_name auto-test-bot-logs
</match>
```

## 🔧 扩展性设计

### 新增测试步骤
1. 在 `src/steps/` 目录创建新模块
2. 继承基础步骤类
3. 实现必需的接口方法

```python
# src/steps/custom_step.py
class CustomStep(BaseStep):
    def get_step_name(self) -> str:
        return "自定义测试"

    async def execute(self) -> Dict[str, Any]:
        # 实现测试逻辑
        pass

    def validate_config(self) -> bool:
        # 验证配置
        return True
```

### 新增监控器
1. 在 `src/mcp/` 目录创建新监控器
2. 实现监控接口
3. 在主程序中集成

```python
# src/mcp/custom_monitor.py
class CustomMonitor:
    def start_monitoring(self) -> None:
        pass

    def stop_monitoring(self) -> Dict[str, Any]:
        return {}

    def add_data(self, data: Dict[str, Any]) -> None:
        pass
```

### 新增报告格式
1. 在 `src/reporter/` 创建新格式化器
2. 实现格式化接口
3. 在配置中启用新格式

这个架构设计确保了系统的可扩展性、可维护性和可测试性，为未来的功能增强奠定了坚实的基础。