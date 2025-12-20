# API契约定义

## 一、跨层通信协议

### 1.1 ScenarioContext
```python
# 核心上下文协议
class ScenarioContext:
    """跨层数据传输的标准协议"""

    # 基础标识
    test_id: str          # 测试唯一标识
    business_flow: str    # 业务流程类型
    test_name: str        # 测试名称

    # 数据和配置
    test_data: Dict        # 测试数据
    environment: Dict       # 环境配置
    execution_options: Dict  # 执行选项

    # 期望结果
    expected_results: Dict  # 期望的测试结果

    # 元数据
    version: str          # 协议版本
    created_at: datetime # 创建时间
    updated_at: datetime # 更新时间
```

### 1.2 LocatorConfig
```python
# 定位器配置协议
class LocatorConfig:
    """元素定位配置"""

    # 优先级定位信息
    test_id: str         # data-testid
    name: str           # name属性
    id: str             # id属性
    label: str          # aria-label
    role: str           # role属性

    # 兜底定位
    text: str           # 文本内容
    css_selector: str    # CSS选择器
    xpath: str          # XPath表达式

    # 高级选项
    scope: str          # 查找范围
    exact_match: bool    # 精确匹配
    wait_strategy: str   # 等待策略
    timeout: int         # 超时时间(ms)
```

### 1.3 PluginResult
```python
# 插件执行结果
class PluginResult:
    """插件执行结果协议"""

    status: str          # completed/failed/timeout
    data: Dict           # 返回数据
    metrics: Dict         # 执行指标
    error: Optional[str]  # 错误信息
    warnings: List[str]    # 警告信息
```

### 1.4 TaskConfig
```python
# 异步任务配置
class TaskConfig:
    """任务配置协议"""

    task_id: str         # 任务ID
    task_type: str       # 任务类型
    task_params: Dict     # 任务参数

    # SLA配置
    sla: {
        'timeout': int,
        'retry_times': int,
        'backoff_strategy': str,
        'poll_interval': int
    }

    # 通知配置
    notification: {
        'type': str,          # webhook/polling/event
        'endpoint': str,      # 通知端点
        'auth_token': str      # 认证令牌
    }
```

## 二、事件流协议

### 2.1 事件格式
```python
class Event:
    """标准事件格式"""

    event_type: str       # 事件类型
    event_id: str        # 事件唯一ID
    timestamp: datetime   # 事件时间戳
    source: str          # 事件源
    data: Dict           # 事件数据
    correlation_id: str  # 关联ID（用于追踪）
```

### 2.2 事件类型定义
| 事件类型 | 触发条件 | 数据内容 | 处理方式 |
|---------|----------|----------|----------|
| locator.gold_hit | L1定位成功 | selector, element, elapsed | 记录成功指标 |
| locator.silver_fallback | L1失败L2成功 | selector, element, elapsed | 记录警告指标 |
| locator.bronze_fallback | L2失败L3成功 | selector, element, elapsed, warnings | 记录风险指标 |
| locator.failure | 全部失败 | selector, error, attempts | 触发诊断 |
| task.started | 任务开始 | task_id, task_type, params | 开始计时 |
| task.completed | 任务完成 | task_id, result, metrics | 记录完成 |
| task.failed | 任务失败 | task_id, error, retry_count | 触发重试 |
| file.download_started | 文件开始下载 | file_id, url, size | 预留空间 |
| file.download_completed | 文件下载完成 | file_id, path, checksum | 开始校验 |
| file.validation_failed | 文件校验失败 | file_id, error, details | 触发清理 |

## 三、配置协议

### 3.1 系统配置
```yaml
# config/system.yaml
system:
  version: "2.0"
  environment: "production"

layers:
  orchestration:
    framework: "robotframework"
    version: ">=5.0"

  adaptation:
    python_version: ">=3.8"
    async_library: "asyncio"

  execution:
    browser_engine: "playwright"
    version: ">=1.40"
```

### 3.2 插件配置
```yaml
# config/plugins.yaml
plugins:
  enabled: ["async_task", "file_processing", "api_mixing"]

  async_task:
    class: "plugins.async_task.AsyncTaskPlugin"
    config:
      default_timeout: 600
      max_concurrent: 10
      retry_strategy: "exponential"

  file_processing:
    class: "plugins.file.FileProcessingPlugin"
    config:
      temp_dir: "/tmp/test_files"
      max_file_size: 1073741824  # 1GB
      supported_formats: ["mp4", "zip", "json"]

  api_mixing:
    class: "plugins.api.APIMixingPlugin"
    config:
      base_url: "${API_BASE_URL}"
      auth_type: "bearer"
      timeout: 30
      retry_times: 3
```

### 3.3 监控配置
```yaml
# config/monitoring.yaml
monitoring:
  metrics:
    collection_interval: 10  # 秒
    retention_days: 30
    export_formats: ["json", "prometheus"]

  slo:
    locator:
      gold_hit_rate: {min: 0.7, target: 0.85}
      avg_locate_time: {max: 2000, target: 1000}

    async_task:
      completion_rate: {min: 0.95, target: 0.98}
      avg_wait_time: {max: 300, target: 180}

  alerts:
    channels: ["slack", "email", "dashboard"]
    thresholds:
      error_rate: 0.05
      response_time: 5000
```

## 四、扩展协议

### 4.1 插件扩展接口
```python
# 定义新插件必须实现的接口
class ExtendedPlugin(AIGCPlugin):
    """扩展插件接口"""

    @property
    @abstractmethod
    def dependencies(self) -> List[str]:
        """插件依赖"""
        pass

    @abstractmethod
    def get_config_schema(self) -> Dict:
        """配置模式定义"""
        pass

    @abstractmethod
    async def validate_config(self, config: Dict) -> bool:
        """配置验证"""
        pass
```

### 4.2 监控扩展接口
```python
# 监控数据提供者接口
class MetricsProvider:
    """指标提供者接口"""

    @abstractmethod
    async def collect_metrics(self) -> Dict[str, Any]:
        """收集指标"""
        pass

    @abstractmethod
    def get_metrics_schema(self) -> Dict:
        """指标模式定义"""
        pass
```

## 五、版本兼容性

### 5.1 向后兼容
- **ScenarioContext v1.x**: 自动转换到v2.0格式
- **旧插件接口**: 提供适配器模式
- **配置文件**: 支持v1.x配置自动迁移

### 5.2 版本升级策略
- **Major升级**: 需要手动迁移
- **Minor升级**: 自动兼容，新功能可选
- **Patch升级**: 仅修复bug，无功能变更

### 5.3 弃用管理
- **提前通知**: 至少2个Minor版本前通知
- **替代方案**: 提供迁移指南
- **支持期限**: 至少6个Minor版本支持