# 插件开发指南

## 一、插件架构概述

闹海自动化测试系统采用插件化架构，允许独立开发和部署AIGC相关能力，而不需要修改核心框架。

### 1.1 核心概念
- **插件基类**：`AIGCPlugin` 定义标准接口
- **插件管理器**：`PluginManager` 负责生命周期管理
- **事件总线**：插件通过事件系统与框架通信

### 1.2 插件类型
| 类型 | 用途 | 示例 | 复杂度 |
|------|------|------|--------|
| 异步任务 | 长耗时操作监控 | AsyncTaskPlugin | 中 |
| 文件处理 | 下载/解压/校验 | FileProcessingPlugin | 高 |
| API编排 | 快速数据准备 | APIMixingPlugin | 中 |
| 自定义 | 特定业务逻辑 | CustomPlugin | 可变 |

## 二、开发指南

### 2.1 环境准备
```bash
# 1. 创建插件目录
mkdir plugins/my_plugin

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate

# 3. 安装依赖
pip install -r requirements-dev.txt
```

### 2.2 基础插件模板
```python
# plugins/my_plugin/my_plugin.py
from core.plugins.base import AIGCPlugin, PluginResult
from core.protocol.scenario_context import ScenarioContext
import asyncio
import logging

class MyPlugin(AIGCPlugin):
    """自定义插件示例"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.name = "my_plugin"
        self.capabilities = ["my_capability"]
        self._config = {}

    @property
    def version(self) -> str:
        """插件版本"""
        return "1.0"

    @property
    def dependencies(self) -> list:
        """插件依赖"""
        return ["other_plugin"]

    async def setup(self):
        """插件初始化"""
        self.logger.info(f"Initializing {self.name} plugin")

        # 加载配置
        self._config = self._load_config()

        # 初始化资源
        await self._init_resources()

        self.logger.info(f"{self.name} plugin initialized")

    async def cleanup(self):
        """插件清理"""
        self.logger.info(f"Cleaning up {self.name} plugin")

        # 释放资源
        await self._cleanup_resources()

        self.logger.info(f"{self.name} plugin cleaned up")

    async def health_check(self):
        """健康检查"""
        try:
            # 检查关键组件状态
            is_healthy = await self._check_health()

            return {
                'status': 'healthy' if is_healthy else 'unhealthy',
                'details': {
                    'config_valid': self._is_config_valid(),
                    'resources_available': is_healthy,
                    'version': self.version
                }
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }

    async def execute(self, context: ScenarioContext, params: dict) -> PluginResult:
        """执行插件功能"""
        self.logger.info(f"Executing {self.name} with params: {params}")

        start_time = asyncio.get_event_loop().time()

        try:
            # 验证参数
            validation_result = self._validate_params(params)
            if not validation_result.valid:
                return PluginResult(
                    status='failed',
                    error=f"参数验证失败: {validation_result.error}"
                )

            # 执行核心逻辑
            result_data = await self._execute_core_logic(context, params)

            # 收集指标
            execution_time = (asyncio.get_event_loop().time() - start_time) * 1000

            return PluginResult(
                status='completed',
                data=result_data,
                metrics={
                    'execution_time_ms': execution_time,
                    'items_processed': len(result_data) if isinstance(result_data, list) else 1
                }
            )

        except Exception as e:
            self.logger.error(f"{self.name} execution failed: {str(e)}")
            return PluginResult(
                status='failed',
                error=str(e),
                data={},
                metrics={
                    'execution_time_ms': (asyncio.get_event_loop().time() - start_time) * 1000
                }
            )

    def _load_config(self) -> dict:
        """加载插件配置"""
        config_path = f"plugins/{self.name}/config.yaml"
        try:
            with open(config_path, 'r') as f:
                import yaml
                return yaml.safe_load(f)
        except FileNotFoundError:
            self.logger.warning(f"Config file not found: {config_path}, using defaults")
            return self._get_default_config()

    def _get_default_config(self) -> dict:
        """获取默认配置"""
        return {
            'timeout': 300,
            'retry_times': 3,
            'enabled_features': ['feature1', 'feature2']
        }

    async def _init_resources(self):
        """初始化资源"""
        # 初始化连接、客户端等
        pass

    async def _cleanup_resources(self):
        """清理资源"""
        # 关闭连接、清理缓存等
        pass

    def _is_config_valid(self) -> bool:
        """检查配置有效性"""
        required_keys = ['timeout', 'retry_times']
        return all(key in self._config for key in required_keys)

    def _validate_params(self, params: dict):
        """验证参数"""
        class ValidationResult:
            def __init__(self, valid: bool, error: str = ""):
                self.valid = valid
                self.error = error

        # 验证必需参数
        if 'required_param' not in params:
            return ValidationResult(False, "Missing required_param")

        return ValidationResult(True)

    async def _execute_core_logic(self, context: ScenarioContext, params: dict):
        """执行核心逻辑"""
        # 在此实现插件的具体功能
        # 返回结果数据
        return {'result': 'success', 'data': params}
```

### 2.3 插件配置文件
```yaml
# plugins/my_plugin/config.yaml
# 插件配置
name: "my_plugin"
version: "1.0"
description: "My custom AIGC plugin"

# 默认配置
defaults:
  timeout: 300
  retry_times: 3
  batch_size: 100

# 功能开关
features:
  feature1:
    enabled: true
    config:
      param1: "value1"

  feature2:
    enabled: false
    config:
      param2: "value2"

# 依赖配置
dependencies:
  - name: "other_plugin"
    version: ">=1.0"
    optional: false

# 资源需求
resources:
  memory_mb: 512
  cpu_cores: 2
  disk_space_mb: 1024
```

## 三、高级主题

### 3.1 异步任务插件开发

#### 任务状态机
```python
from enum import Enum

class TaskState(Enum):
    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskObserver:
    """任务观察者 - 监控异步任务状态变化"""

    def __init__(self, config):
        self.config = config
        self.state_history = []
        self.metrics = {}

    async def observe_task(self, task_id: str):
        """观察任务直到完成"""
        current_state = TaskState.QUEUED

        while current_state not in [TaskState.COMPLETED, TaskState.FAILED, TaskState.CANCELLED]:
            # 获取当前状态
            new_state = await self._get_task_state(task_id)

            # 状态变化时记录
            if new_state != current_state:
                self._record_state_change(task_id, current_state, new_state)
                current_state = new_state

                # 处理状态变化
                await self._handle_state_change(task_id, new_state)

            # 等待下一次检查
            await asyncio.sleep(self.config.get('poll_interval', 5))

        # 返回最终结果
        return await self._get_task_result(task_id)

    def _record_state_change(self, task_id: str, old_state: TaskState, new_state: TaskState):
        """记录状态变化"""
        self.state_history.append({
            'task_id': task_id,
            'timestamp': datetime.now().isoformat(),
            'old_state': old_state.value,
            'new_state': new_state.value
        })

        # 发射事件
        await self.event_bus.publish('task.state_change', {
            'task_id': task_id,
            'old_state': old_state.value,
            'new_state': new_state.value,
            'history': self.state_history[-10:]
        })

    async def _handle_state_change(self, task_id: str, state: TaskState):
        """处理状态变化逻辑"""
        if state == TaskState.RUNNING:
            await self._start_metrics_collection(task_id)
        elif state in [TaskState.COMPLETED, TaskState.FAILED]:
            await self._stop_metrics_collection(task_id)
            await self._calculate_final_metrics(task_id)
```

#### 智能重试机制
```python
import math

class RetryStrategy:
    """重试策略基类"""

    def __init__(self, max_attempts: int):
        self.max_attempts = max_attempts

    def calculate_delay(self, attempt: int) -> float:
        """计算延迟时间"""
        raise NotImplementedError

class ExponentialBackoff(RetryStrategy):
    """指数退避策略"""

    def __init__(self, max_attempts: int, base_delay: float = 1.0, max_delay: float = 60.0):
        super().__init__(max_attempts)
        self.base_delay = base_delay
        self.max_delay = max_delay

    def calculate_delay(self, attempt: int) -> float:
        delay = self.base_delay * math.pow(2, attempt - 1)
        return min(delay, self.max_delay)

class LinearBackoff(RetryStrategy):
    """线性退避策略"""

    def __init__(self, max_attempts: int, delay_increment: float = 5.0):
        super().__init__(max_attempts)
        self.delay_increment = delay_increment

    def calculate_delay(self, attempt: int) -> float:
        return self.delay_increment * (attempt - 1)
```

### 3.2 文件处理插件开发

#### 流式处理管道
```python
from abc import ABC, abstractmethod
from typing import List, Any

class ProcessingStage(ABC):
    """处理阶段基类"""

    @abstractmethod
    async def process(self, data: Any, context: dict) -> Any:
        """处理数据"""
        pass

    @abstractmethod
    def get_stage_name(self) -> str:
        """获取阶段名称"""
        pass

class DownloadStage(ProcessingStage):
    """下载阶段"""

    def get_stage_name(self) -> str:
        return "download"

    async def process(self, file_info: dict, context: dict) -> dict:
        """下载文件"""
        url = file_info['url']
        local_path = file_info.get('local_path', 'temp/' + file_info['filename'])

        # 带进度显示的下载
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    total_size = int(response.headers.get('content-length', 0))
                    downloaded = 0

                    with open(local_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            f.write(chunk)
                            downloaded += len(chunk)

                            # 记录进度
                            progress = (downloaded / total_size) * 100
                            await self._emit_progress('download', progress, file_info)

        return {
            'local_path': local_path,
            'size': total_size,
            'downloaded': downloaded
        }

class ValidationStage(ProcessingStage):
    """校验阶段"""

    def __init__(self, rules: dict):
        self.rules = rules

    def get_stage_name(self) -> str:
        return "validation"

    async def process(self, file_path: dict, context: dict) -> dict:
        """验证文件"""
        validation_results = []

        # 文件存在性检查
        if not os.path.exists(file_path['local_path']):
            validation_results.append({
                'type': 'file_exists',
                'status': 'failed',
                'message': f"File not found: {file_path['local_path']}"
            })
            return {'validation_results': validation_results}

        # 文件大小检查
        actual_size = os.path.getsize(file_path['local_path'])
        expected_size = file_path.get('size', 0)

        if actual_size != expected_size:
            validation_results.append({
                'type': 'size_check',
                'status': 'failed',
                'message': f"Size mismatch: expected={expected_size}, actual={actual_size}"
            })

        # 自定义规则验证
        for rule_name, rule_config in self.rules.items():
            result = await self._apply_rule(rule_name, rule_config, file_path)
            validation_results.append(result)

        return {
            'validation_results': validation_results,
            'is_valid': all(r['status'] == 'passed' for r in validation_results)
        }
```

## 四、测试和调试

### 4.1 单元测试
```python
# tests/test_my_plugin.py
import unittest
from unittest.mock import AsyncMock, patch
from plugins.my_plugin.my_plugin import MyPlugin
from core.protocol.scenario_context import ScenarioContext

class TestMyPlugin(unittest.TestCase):
    def setUp(self):
        self.plugin = MyPlugin()
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    async def asyncSetUp(self):
        await self.plugin.setup()

    async def test_execute_success(self):
        """测试成功执行"""
        context = ScenarioContext(
            test_id="test_001",
            business_flow="test_flow"
        )
        params = {"required_param": "test_value"}

        result = await self.plugin.execute(context, params)

        self.assertEqual(result.status, 'completed')
        self.assertIn('result', result.data)

    async def test_execute_with_invalid_params(self):
        """测试无效参数"""
        context = ScenarioContext(
            test_id="test_002",
            business_flow="test_flow"
        )
        params = {}  # 缺少必需参数

        result = await self.plugin.execute(context, params)

        self.assertEqual(result.status, 'failed')
        self.assertIn('参数验证失败', result.error)

    def test_health_check(self):
        """测试健康检查"""
        result = self.loop.run_until_complete(
            self.plugin.health_check()
        )

        self.assertEqual(result['status'], 'healthy')
        self.assertIn('version', result['details'])
```

### 4.2 集成测试
```robot
# tests/integration/my_plugin_integration.robot
*** Settings ***
Resource    ../../keywords/common_keywords.resource
Variables
    ${TEST_CONFIG}    {"test_mode": "integration"}

*** Test Cases ***
插件集成测试
    [Documentation]    验证插件在完整流程中的表现
    [Tags]    integration    plugin

    # 初始化环境
    初始化测试环境

    # 创建测试上下文
    创建测试上下文    integration_test    plugin_test_flow

    # 执行插件
    ${result}=    执行插件    my_plugin
    ...    {"test_param": "test_value"}

    # 验证结果
    Should Be Equal    ${result.status}    completed
    Should Contain    ${result.data}    success
```

## 五、部署和分发

### 5.1 打包插件
```python
# setup.py
from setuptools import setup, find_packages

setup(
    name="naohai-my-plugin",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "aiohttp>=3.8.0",
        "pyyaml>=6.0",
        "robotframework>=5.0"
    ],
    entry_points={
        'naohai_plugins': [
            'my_plugin = plugins.my_plugin.my_plugin:MyPlugin'
        ]
    },
    author="Your Name",
    author_email="your.email@example.com",
    description="Custom plugin for Naohai AIGC automation",
    long_description=open('README.md').read(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)
```

### 5.2 插件仓库
```
naohai-my-plugin/
├── plugins/
│   └── my_plugin/
│       ├── __init__.py
│       ├── my_plugin.py
│       └── config.yaml
├── tests/
│   ├── unit/
│   │   └── test_my_plugin.py
│   └── integration/
│       └── my_plugin_integration.robot
├── docs/
│   ├── README.md
│   ├── CHANGELOG.md
│   └── API.md
├── examples/
│   └── basic_usage.robot
├── setup.py
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml
└── .github/
    └── workflows/
        └── ci.yml
```

## 六、最佳实践

### 6.1 错误处理
- **明确异常类型**：定义具体的异常类
- **结构化错误信息**：使用标准格式
- **提供恢复建议**：自动生成修复建议
- **记录完整上下文**：包含所有相关数据

### 6.2 性能优化
- **异步优先**：使用asyncio避免阻塞
- **资源池化**：复用连接和客户端
- **缓存策略**：合理使用内存缓存
- **批量操作**：减少网络往返

### 6.3 可观测性
- **结构化日志**：使用JSON格式便于解析
- **指标暴露**：提供详细的性能指标
- **健康检查**：实现标准健康接口
- **事件发射**：通过事件总线通信

### 6.4 安全考虑
- **输入验证**：严格验证所有输入
- **权限最小化**：只请求必要权限
- **敏感数据处理**：避免记录敏感信息
- **安全编码**：遵循安全编码规范

## 七、故障排查

### 7.1 常见问题
| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 插件加载失败 | 依赖缺失/版本冲突 | 检查requirements.txt，确保依赖版本兼容 |
| 执行超时 | 网络问题/资源不足 | 增加超时配置，检查系统资源 |
| 配置错误 | 格式错误/路径问题 | 使用配置验证工具，提供默认值 |
| 状态不同步 | 并发访问/竞态条件 | 使用锁机制，确保原子操作 |

### 7.2 调试技巧
- **启用详细日志**：设置LOG_LEVEL=DEBUG
- **使用调试器**：import pdb; pdb.set_trace()
- **事件追踪**：监听事件总线输出
- **性能分析**：使用cProfile分析瓶颈

### 7.3 联系支持
- **GitHub Issues**：在插件仓库提交问题
- **社区论坛**：在官方论坛寻求帮助
- **文档查阅**：查阅最新文档和FAQ
- **代码示例**：参考官方示例代码