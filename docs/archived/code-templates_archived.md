# 代码模板和示例（已归档）

## ⚠️ 状态更新

**原状态**：代码模板和示例文档
**当前状态**：✅ **已归档，内容已被新架构体系替代**

---

## 🎯 替代文档

### 当前有效文档
- **[03-aigc-enhanced-solution.md](./03-aigc-enhanced-solution.md)** - AIGC增强解决方案v2.0
- **[04-implementation-details.md](./04-implementation-details.md)** - 具体实现细节
- **[plugin-development.md](./plugin-development.md)** - 插件开发指南

### 主要变更
1. **架构升级**：从v1.0升级到v2.0三层架构
2. **模板体系**：建立了更完整的开发模板体系
3. **最佳实践**：基于实际项目经验建立的开发指南

---

## 📋 历史内容归档

本文档原有的模板和示例内容已被以下新文档替代和增强：

| 原内容 | 新替代文档 | 状态 |
|---------|------------|------|
| 插件开发模板 | [plugin-development.md](./plugin-development.md) | ✅ 已升级 |
| 代码示例 | [04-implementation-details.md](./04-implementation-details.md) | ✅ 已完善 |
| API契约 | [api-contracts.md](./api-contracts.md) | ✅ 已标准化 |

---

## 🎉 结论

### 架构演进成功
原有的v1.0模板和示例已成功升级为v2.0架构体系：
- ✅ **更完整**：涵盖插件开发、API设计、监控体系
- ✅ **更规范**：基于实际项目经验建立的标准化流程
- ✅ **更实用**：提供了具体的实现细节和最佳实践

### 建议后续关注
请参考新架构体系文档：
1. **插件开发**：使用新的[plugin-development.md](./plugin-development.md)
2. **实现细节**：参考[04-implementation-details.md](./04-implementation-details.md)
3. **API设计**：遵循[api-contracts.md](./api-contracts.md)

**归档时间**：2025-12-18
**状态**：✅ 已被v2.0架构体系完全替代

    async def cleanup(self):
        """插件清理"""
        print(f"Plugin {self.name} cleanup complete")

    async def health_check(self):
        """健康检查"""
        return {'status': 'healthy'}

    async def execute(self, context: ScenarioContext, params: dict) -> PluginResult:
        """执行插件功能"""
        try:
            # 实现具体逻辑
            result_data = await self._do_work(context, params)

            return PluginResult(
                status='completed',
                data=result_data,
                metrics={
                    'execution_time': 1000,
                    'items_processed': len(result_data)
                }
            )
        except Exception as e:
            return PluginResult(
                status='failed',
                error=str(e),
                data={}
            )

    async def _do_work(self, context: ScenarioContext, params: dict) -> dict:
        """实际工作逻辑"""
        # 在此实现插件功能
        pass
```

### 1.2 异步任务插件模板
```python
# plugins/async_task_template.py
from core.plugins.base import AIGCPlugin, PluginResult
import aiohttp
import asyncio

class CustomAsyncTaskPlugin(AIGCPlugin):
    """异步任务插件模板"""

    def __init__(self):
        self.api_client = None
        self.observer = None

    @property
    def name(self) -> str:
        return "custom_async_task"

    @property
    def capabilities(self) -> list:
        return ["async_execution", "status_monitoring"]

    async def setup(self):
        """初始化API客户端"""
        self.api_client = aiohttp.ClientSession()
        self.observer = TaskObserver()

    async def execute(self, context: ScenarioContext, params: dict) -> PluginResult:
        """执行异步任务"""
        task_config = {
            'task_type': params.get('task_type'),
            'task_params': params.get('task_params', {}),
            'timeout': params.get('timeout', 600),
            'retry_times': params.get('retry_times', 3)
        }

        # 提交任务
        task_id = await self._submit_task(task_config)

        # 监控任务直到完成
        result = await self.observer.wait_for_completion(
            task_id,
            timeout=task_config['timeout']
        )

        return PluginResult(
            status='completed' if result['status'] == 'success' else 'failed',
            data=result,
            metrics=self.observer.get_metrics()
        )

    async def _submit_task(self, config: dict) -> str:
        """提交异步任务"""
        api_url = config.get('api_url')
        payload = {
            'type': config['task_type'],
            'parameters': config['task_params']
        }

        async with self.api_client.post(api_url, json=payload) as response:
            if response.status == 200:
                data = await response.json()
                return data.get('task_id')
            else:
                raise Exception(f"Task submission failed: {response.status}")
```

## 二、Robot Framework关键字模板

### 2.1 基础关键字模板
```robot
# keywords/common_keywords.resource
*** Settings ***
Library    NaohaiAdapterV2
Library    Collections
Library    String

*** Variables ***
${CONTEXT_TEMPLATE}    test_id=    business_flow=    test_data={}    execution_options={}

*** Keywords ***
初始化测试上下文
    [Arguments]    ${test_id}    ${business_flow}
    [Documentation]    创建标准测试上下文
    ${context}=    Set Variable    &{CONTEXT_TEMPLATE}
    Set To Dictionary    ${context}    test_id=${test_id}
    Set To Dictionary    ${context}    business_flow=${business_flow}
    ${json}=    序列化上下文    ${context}
    Set Suite Variable    ${SCENARIO_CONTEXT}    ${json}
    [Return]    ${json}

执行带验证的操作
    [Arguments]    ${keyword}    @{args}
    [Documentation]    执行关键字并验证结果
    ${result}=    执行关键字    ${keyword}    @{args}

    # 验证状态
    ${result_dict}=    Evaluate    json.loads('${result}')
    Should Be Equal    ${result_dict['status']}    completed

    # 记录指标
    ${metrics}=    Set Variable    ${result_dict['metrics']}
    Log    Metrics: ${metrics}

    [Return]    ${result_dict['data']}

智能等待元素
    [Arguments]    ${selector}    ${timeout}=30
    [Documentation]    智能等待元素出现

    # 轮询检查
    FOR    ${i}    IN RANGE    ${timeout}
        ${visible}=    检查元素可见性    ${selector}
        IF    ${visible}
            Log    Element ${selector} is visible after ${i}s
            BREAK
        END
        Sleep    1s
    END

    # 超时处理
    Fail    Element ${selector} not visible after ${timeout}s

批量验证多个元素
    [Arguments]    @{selectors}
    [Documentation]    批量验证元素列表
    ${results}=    Create List

    FOR    ${selector}    IN    @{selectors}
        ${visible}=    检查元素可见性    ${selector}
        ${result}=    Create Dictionary
        ...    selector=${selector}
        ...    visible=${visible}
        Append To List    ${results}    ${result}
    END

    [Return]    ${results}
```

### 2.2 AIGC场景关键字模板
```robot
# keywords/aigc_keywords.resource
*** Settings ***
Resource    common_keywords.resource
Library    DateTime

*** Keywords ***
生成视频并等待完成
    [Arguments]    ${prompt}    ${model}=v2.0    ${timeout}=600
    [Documentation]    生成视频并等待完成

    # 提交生成任务
    ${task_params}=    Create Dictionary
    ...    prompt=${prompt}
    ...    model=${model}
    ...    resolution=1080P

    ${result}=    执行插件    async_task
    ...    task_type=video_generation
    ...    task_params=${task_params}
    ...    timeout=${timeout}

    # 验证结果
    ${result_dict}=    Evaluate    json.loads('${result}')
    Should Be Equal    ${result_dict['status']}    completed

    ${video_url}=    Set Variable    ${result_dict['data']['video_url']}
    [Return]    ${video_url}

下载并验证资源包
    [Arguments]    ${download_url}    ${expected_files}=1
    [Documentation]    下载资源包并验证完整性

    # 执行文件处理插件
    ${file_params}=    Create Dictionary
    ...    url=${download_url}
    ...    expected_count=${expected_files}
    ...    validate_content=true

    ${result}=    执行插件    file_processing
    ...    action=download_and_validate
    ...    params=${file_params}

    # 验证结果
    ${result_dict}=    Evaluate    json.loads('${result}')
    Should Be Equal    ${result_dict['status']}    completed

    ${file_list}=    Set Variable    ${result_dict['data']['files']}
    [Return]    ${file_list}
```

## 三、配置文件模板

### 3.1 系统配置模板
```yaml
# config/system_template.yaml
# 系统配置模板
app:
  name: "闹海AIGC自动化测试"
  version: "2.0"
  environment: "${ENVIRONMENT:production}"

# 浏览器配置
browser:
  engine: "playwright"
  headless: "${HEADLESS:true}"
  viewport:
    width: 1920
    height: 1080
  timeout:
    default: 30000
    navigation: 60000

# 执行引擎配置
execution:
  python_version: ">=3.8"
  asyncio_policy: "uvloop"
  max_concurrent_tasks: 10

# 日志配置
logging:
  level: "INFO"
  format: "json"
  outputs:
    - "console"
    - "file:logs/test.log"

# 监控配置
monitoring:
  enabled: true
  metrics_interval: 10
  alert_webhook: "${ALERT_WEBHOOK_URL}"

# 插件配置
plugins:
  directory: "plugins/"
  auto_load: true
  enabled:
    - "async_task"
    - "file_processing"
    - "api_mixing"
```

### 3.2 插件配置模板
```yaml
# plugins/async_task_config.yaml
# 异步任务插件配置
async_task:
  # 任务类型映射
  task_types:
    video_generation:
      endpoint: "/api/v1/generate/video"
      method: "POST"
      timeout: 600
      retry_times: 3
      backoff_factor: 2

    image_generation:
      endpoint: "/api/v1/generate/image"
      method: "POST"
      timeout: 120
      retry_times: 2
      backoff_factor: 1.5

  # 状态检查
  status_check:
    endpoint: "/api/v1/task/status"
    method: "GET"
    interval: 5
    max_checks: 600

  # 结果获取
  result:
    endpoint: "/api/v1/task/result"
    method: "GET"
    timeout: 30

# 通知配置
notification:
  webhook:
    enabled: true
    url: "${WEBHOOK_URL}"
    auth_token: "${WEBHOOK_AUTH_TOKEN}"
    retry_times: 3
```

## 四、测试用例模板

### 4.1 基础测试模板
```robot
# tests/templates/basic_test_template.robot
*** Settings ***
Resource    ../keywords/common_keywords.resource
Resource    ../keywords/aigc_keywords.resource
Library    String
Library    Collections

Suite Setup    初始化测试环境
Suite Teardown    清理测试环境
Test Setup    创建测试上下文    ${SUITE_NAME}    basic_flow
Test Teardown    记录测试结果

*** Variables ***
${TEST_DATA}    {}  # 测试数据
${EXPECTED_RESULTS}    {}  # 期望结果

*** Test Cases ***
基本元素定位测试
    [Documentation]    验证三级定位器功能
    [Tags]    locator    smoke

    ${test_id}=    Set Variable    basic_locator_test

    # 测试L1定位
    ${result}=    智能点击    submit_button
    Should Contain    ${result}    tier_used=gold

    # 测试L2定位
    ${result}=    智能点击    cancel_button    fallback={"name":"cancel"}
    Should Contain    ${result}    tier_used=silver

    # 测试L3定位
    ${result}=    智能点击    close_modal    fallback={"text":"关闭"}
    Should Contain    ${result}    tier_used=bronze
```

### 4.2 AIGC场景测试模板
```robot
# tests/templates/aigc_test_template.robot
*** Settings ***
Resource    ../keywords/aigc_keywords.resource
Resource    ../keywords/common_keywords.resource
Library    DateTime

Suite Setup    初始化测试环境    config/aigc_test_config.yaml
Suite Teardown    清理测试环境

*** Test Cases ***
视频生成完整流程测试
    [Documentation]    测试视频生成的完整流程
    [Tags]    video    e2e    critical

    # 准备测试数据
    ${context_json}=    创建测试上下文
    ...    video_generation_e2e
    ...    video_creation_flow

    ${test_data}=    Set Variable
    ...    prompt=一只可爱的小猫咪在花园玩耍
    ...    model=v2.0
    ...    resolution=1080P
    ...    expected_duration=300

    # 执行视频生成
    ${video_url}=    生成视频并等待完成
    ...    ${test_data.prompt}
    ...    ${test_data.model}
    ...    ${test_data.timeout}

    # 验证视频URL
    Should Not Be Empty    ${video_url}
    Should Match Regexp    ${video_url}    https?://.*/video/.*

    # 测试视频下载
    ${result}=    下载并验证资源包
    ...    ${video_url}
    ...    expected_files=1

    # 验证下载结果
    Should Be Equal    ${result.status}    completed
    Should Contain    ${result.files}    video.mp4

批量视频生成测试
    [Documentation]    测试并发视频生成
    [Tags]    video    batch    performance

    ${prompts}=    Create List
    ...    一只猫
    ...    一条狗
    ...    一只鸟

    ${results}=    Create List

    FOR    ${prompt}    IN    @{prompts}
        ${video_url}=    生成视频并等待完成
        ...    ${prompt}
        ...    v2.0
        ...    300
        Append To List    ${results}    ${video_url}
    END

    # 验证全部生成成功
    Length Should Be    ${results}    3

    # 验证生成时间在合理范围内
    # 这里可以添加时间验证逻辑
```

## 五、部署脚本模板

### 5.1 安装脚本模板
```bash
#!/bin/bash
# scripts/install.sh
set -e

echo "🚀 安装闹海自动化测试v2.0..."

# 检查Python版本
python_version=$(python3 --version 2>&1 | grep -oP '\d+\.\d+')
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python版本不足，需要>=3.8，当前版本: $python_version"
    exit 1
fi

echo "✅ Python版本检查通过: $python_version"

# 安装依赖
echo "📦 安装Python依赖..."
pip install -r requirements.txt

# 安装Playwright浏览器
echo "🌐 安装Playwright浏览器..."
playwright install chromium firefox webkit

# 创建必要目录
echo "📁 创建目录结构..."
mkdir -p logs
mkdir -p reports
mkdir -p temp
mkdir -p data

# 设置权限
chmod +x scripts/*.sh
chmod -R 755 logs reports temp

echo "✅ 安装完成！"
echo "📖 使用说明："
echo "  - 配置文件: config/system.yaml"
echo "  - 运行测试: python -m robot tests/"
echo "  - 查看报告: reports/"
```

### 5.2 部署脚本模板
```bash
#!/bin/bash
# scripts/deploy.sh
set -e

ENVIRONMENT=${1:-production}
VERSION=${2:-latest}

echo "🚀 部署闹海自动化测试到 $ENVIRONMENT 环境..."

# 备份当前版本
echo "💾 备份当前版本..."
if [ -d "/opt/naohai-autotest" ]; then
    cp -r /opt/naohai-autotest /opt/naohai-autotest.backup.$(date +%Y%m%d_%H%M%S)
fi

# 停止现有服务
echo "⏹ 停止现有服务..."
systemctl stop naohai-autotest || true

# 部署新版本
echo "📦 部署新版本..."
cp -r . /opt/naohai-autotest

# 更新配置
echo "⚙️ 更新配置..."
cp config/${ENVIRONMENT}.yaml /opt/naohai-autotest/config/system.yaml

# 安装依赖
echo "📦 安装依赖..."
cd /opt/naohai-autotest
pip install -r requirements.txt

# 启动服务
echo "🚀 启动服务..."
systemctl start naohai-autotest
systemctl enable naohai-autotest

# 验证部署
echo "✅ 验证部署..."
sleep 10

if systemctl is-active --quiet naohai-autotest; then
    echo "✅ 部署成功！服务已启动"
else
    echo "❌ 部署失败，服务未启动"
    echo "📋 查看日志: journalctl -u naohai-autotest"
    exit 1
fi

echo "🎉 部署完成！"
echo "📍 部署位置: /opt/naohai-autotest"
echo "🌐 监控地址: http://localhost:8080/dashboard"
```

## 六、开发环境配置

### 6.1 Docker开发环境
```dockerfile
# Dockerfile.dev
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# 安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 安装Playwright
RUN playwright install chromium
RUN playwright install-deps

# 复制源码
COPY . .

# 设置环境变量
ENV PYTHONPATH=/app
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# 暴露端口
EXPOSE 8080

# 启动命令
CMD ["python", "-m", "http.server", "8080"]
```

### 6.2 Docker Compose开发环境
```yaml
# docker-compose.dev.yml
version: '3.8'

services:
  naohai-autotest:
    build:
      context: .
      dockerfile: Dockerfile.dev
    volumes:
      - ./docs:/app/docs
      - ./tests:/app/tests
      - ./config:/app/config
      - ./logs:/app/logs
    ports:
      - "8080:8080"
    environment:
      - ENVIRONMENT=development
      - HEADLESS=false
      - LOG_LEVEL=DEBUG

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus

volumes:
  redis_data:
```

## 七、快速生成命令

### 7.1 创建新插件
```bash
#!/bin/bash
# scripts/create_plugin.sh

PLUGIN_NAME=${1:-new_plugin}

echo "🔧 创建新插件: $PLUGIN_NAME"

# 创建插件目录
mkdir -p plugins/$PLUGIN_NAME

# 生成插件文件
cat > plugins/$PLUGIN_NAME/__init__.py << EOF
"""
$PLUGIN_NAME plugin for Naohai AIGC Automation
"""

from .$PLUGIN_NAME import $PLUGIN_NAMEPlugin

__version__ = "1.0"
__plugin_name__ = "$PLUGIN_NAME"
EOF

cat > plugins/$PLUGIN_NAME/$PLUGIN_NAME.py << EOF
from core.plugins.base import AIGCPlugin, PluginResult
from core.protocol.scenario_context import ScenarioContext

class $PLUGIN_NAMEPlugin(AIGCPlugin):
    """$PLUGIN_NAME plugin implementation"""

    @property
    def name(self) -> str:
        return "$PLUGIN_NAME"

    @property
    def capabilities(self) -> list:
        return ["capability1", "capability2"]

    async def setup(self):
        """Setup plugin"""
        pass

    async def cleanup(self):
        """Cleanup plugin"""
        pass

    async def execute(self, context: ScenarioContext, params: dict) -> PluginResult:
        """Execute plugin logic"""
        # TODO: Implement plugin logic here
        return PluginResult(
            status='completed',
            data={},
            metrics={}
        )
EOF

echo "✅ 插件创建完成: plugins/$PLUGIN_NAME"
echo "📝 请编辑 plugins/$PLUGIN_NAME/$PLUGIN_NAME.py 实现具体逻辑"
```

### 7.2 生成测试用例
```bash
#!/bin/bash
# scripts/generate_test.sh

TEST_NAME=${1:-new_test}
SUITE=${2:-general}

echo "🧪 生成测试用例: $TEST_NAME"

# 创建测试文件
cat > tests/$SUITE/${TEST_NAME}.robot << EOF
*** Settings ***
Resource    ../keywords/common_keywords.resource
Resource    ../keywords/aigc_keywords.resource

Suite Setup    初始化测试环境
Suite Teardown    清理测试环境
Test Setup    创建测试上下文    \${TEST_NAME}    $SUITE\_flow

*** Test Cases ***
${TEST_NAME}测试
    [Documentation]    自动生成的测试用例
    [Tags]    auto-generated    $SUITE

    # TODO: 实现测试逻辑
    Fail    测试用例待实现

EOF

echo "✅ 测试用例生成完成: tests/$SUITE/${TEST_NAME}.robot"
echo "📝 请编辑测试文件实现具体测试逻辑"
```