# 03 - AIGC增强解决方案 v2.0

## 一、AIGC特性分析

### 1.1 异步长任务特征
| 特征 | 影响 | 解决方案 |
|------|------|----------|
| 耗时长(1-10分钟) | 测试执行时间不可控 | 智能轮询+动态超时 |
| 状态复杂(排队/处理/完成/失败) | 失败原因难定位 | 状态机+详细诊断 |
| 并发需求(多任务同时生成) | 资源竞争 | 任务队列+优先级管理 |

### 1.2 文件处理特征
| 特征 | 影响 | 解决方案 |
|------|------|----------|
| 文件体积大(几百MB) | 下载超时/内存不足 | 流式下载+磁盘监控 |
| 格式多样(mp4/zip/json) | 校验复杂 | 多格式校验器+插件化 |
| 完整性要求(数量/质量) | 验证标准不一 | 结构化验证+可配置规则 |

### 1.3 数据准备特征
| 特征 | 影响 | 解决方案 |
|------|------|----------|
| 依赖链长(剧本→分集→角色→场景) | UI准备耗时 | API快速造数据 |
| 数据关系复杂 | 难以维护 | DSL抽象+模板化 |
| 版本要求(多环境) | 环境不一致 | 环境矩阵+自动同步 |

## 二、插件化架构设计

### 2.1 插件接口定义
```python
class AIGCPlugin(ABC):
    """AIGC能力插件基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        """插件标识"""
        pass

    @property
    @abstractmethod
    def capabilities(self) -> List[str]:
        """支持的能力列表"""
        pass

    @abstractmethod
    async def execute(self, context: ScenarioContext, params: Dict) -> PluginResult:
        """执行插件功能"""
        pass

    async def setup(self):
        """插件初始化"""
        pass

    async def cleanup(self):
        """插件清理"""
        pass

    async def health_check(self):
        """健康检查"""
        return {'status': 'healthy'}
```

### 2.2 核心插件实现

#### 2.2.1 异步任务插件(AsyncTaskPlugin)
```python
class AsyncTaskPlugin(AIGCPlugin):
    """处理所有异步长任务的通用插件"""

    def __init__(self):
        self.observer = TaskObserver()
        self.task_registry = TaskRegistry()

    async def execute(self, context: ScenarioContext, params: Dict) -> PluginResult:
        task_config = {
            'task_id': params['task_id'],
            'task_type': params.get('task_type', 'video_generation'),
            'sla': params.get('sla', self._default_sla()),
            'notification': params.get('notification', 'webhook')
        }

        # 注册任务观察
        self.observer.register(task_config)

        # 启动任务(或监控已有任务)
        result = await self._monitor_task(task_config)

        return PluginResult(
            status=result['status'],
            data=result['data'],
            metrics=self.observer.collect_metrics()
        )

    def _default_sla(self):
        """默认SLA配置"""
        return {
            'timeout': 600,        # 10分钟
            'retry_times': 3,
            'backoff': 'exponential',
            'max_poll_interval': 30  # 最大轮询间隔
        }
```

#### 2.2.2 文件处理插件(FileProcessingPlugin)
```python
class FileProcessingPlugin(AIGCPlugin):
    """文件处理流水线插件"""

    def __init__(self):
        self.pipeline = ProcessingPipeline([
            DownloadStage(),
            ValidationStage(),
            AnalysisStage(),
            CleanupStage()
        ])

    async def execute(self, context: ScenarioContext, params: Dict) -> PluginResult:
        """执行文件处理流水线"""
        file_info = params['file_info']
        processing_config = {
            'max_size': params.get('max_size', 500 * 1024 * 1024),
            'extract_dir': params.get('extract_dir', 'temp'),
            'validation_rules': params.get('validation_rules', {}),
            'keep_temp': params.get('keep_temp', False)
        }

        # 执行流水线
        pipeline_result = await self.pipeline.process(
            file_info,
            config=processing_config
        )

        return PluginResult(
            status='completed' if pipeline_result.success else 'failed',
            data={
                'files': pipeline_result.files,
                'validation_report': pipeline_result.validation,
                'processing_metrics': pipeline_result.metrics
            }
        )
```

#### 2.2.3 API混合编排插件(APIMixingPlugin)
```python
class APIMixingPlugin(AIGCPlugin):
    """API快速数据准备插件"""

    async def execute(self, context: ScenarioContext, params: Dict) -> PluginResult:
        """通过API快速准备测试数据"""
        template_name = params['template']
        test_data = {}

        # 根据模板执行不同的数据准备流程
        if template_name == 'full_video_creation':
            test_data = await self._prepare_full_video_data()
        elif template_name == 'image_generation_only':
            test_data = await self._prepare_image_data()
        elif template_name == 'character_creation':
            test_data = await self._prepare_character_data()

        # 存储到上下文供后续使用
        context.test_data.update(test_data)

        return PluginResult(
            status='completed',
            data=test_data,
            metrics={'api_calls': self.api_client.call_count}
        )

    async def _prepare_full_video_data(self):
        """准备完整视频生成所需的所有数据"""
        # 并行创建所有依赖数据
        tasks = [
            self.api_client.create_script({...}),
            self.api_client.create_episode(...),
            self.api_client.create_character(...),
            self.api_client.create_scene(...)
        ]

        results = await asyncio.gather(*tasks)
        return self._consolidate_results(results)
```

## 三、增强的监控体系

### 3.1 SLO指标体系
```yaml
# monitoring/slo.yaml
slo:
  locator:
    gold_hit_rate: {min: 0.7, target: 0.85}
    silver_fallback_rate: {max: 0.25, target: 0.15}
    bronze_fallback_rate: {max: 0.05, target: 0.02}
    avg_locate_time: {max: 2000, target: 1000}  # ms

  async_task:
    completion_rate: {min: 0.95, target: 0.98}
    avg_wait_time: {max: 300, target: 180}  # seconds
    timeout_rate: {max: 0.02, target: 0.01}
    sla_compliance: {min: 0.9, target: 0.95}

  file_processing:
    success_rate: {min: 0.98, target: 0.995}
    avg_processing_time: {max: 60, target: 30}  # seconds
    disk_efficiency: {min: 0.8, target: 0.9}
```

### 3.2 实时监控实现
```python
class RealTimeMonitor:
    """实时监控系统"""

    def __init__(self):
        self.metrics_store = TimeSeriesDB()
        self.alert_manager = AlertManager()
        self.dashboard = Dashboard()

    async def start_monitoring(self):
        """启动监控"""
        # 定期收集指标
        asyncio.create_task(self._collect_metrics_loop())

        # 定期检查SLO
        asyncio.create_task(self._check_slo_loop())

        # 启动Web服务提供API
        await self.dashboard.start_server()

    async def _collect_metrics_loop(self):
        """指标收集循环"""
        while True:
            await asyncio.sleep(10)  # 10秒一次

            # 收集定位器指标
            locator_metrics = self.collector.get_locator_metrics()
            self.metrics_store.record('locator', locator_metrics)

            # 收集AIGC任务指标
            task_metrics = self.collector.get_task_metrics()
            self.metrics_store.record('task', task_metrics)

            # 收集文件处理指标
            file_metrics = self.collector.get_file_metrics()
            self.metrics_store.record('file', file_metrics)

    async def _check_slo_loop(self):
        """SLO检查循环"""
        while True:
            await asyncio.sleep(60)  # 1分钟一次

            slo_status = self._evaluate_slo()
            if not slo_status.all_compliant:
                alerts = self.alert_manager.generate_alerts(slo_status)
                await self._send_alerts(alerts)
```

## 四、错误处理和恢复

### 4.1 分级错误处理
```python
class ErrorRecoveryManager:
    """错误恢复管理器"""

    ERROR_RECOVERY_STRATEGIES = {
        'locator.bronze_failure': {
            'retry': True,
            'escalate': True,
            'auto_fix': ['suggest_testid', 'try_alternative_text']
        },
        'async_task.timeout': {
            'retry': True,
            'escalate': True,
            'auto_fix': ['extend_timeout', 'split_task']
        },
        'file_processing.corrupted': {
            'retry': False,
            'escalate': True,
            'auto_fix': ['re_download', 'validate_partial']
        }
    }

    async def handle_error(self, error_type: str, context: ScenarioContext):
        """处理错误"""
        strategy = self.ERROR_RECOVERY_STRATEGIES.get(error_type)

        if strategy['retry']:
            success = await self._attempt_recovery(context, strategy)
            if success:
                return {'status': 'recovered'}

        if strategy['escalate']:
            await self._escalate_to_mcp(error_type, context)

        if strategy['auto_fix']:
            fix_suggestions = await self._generate_fix_suggestions(
                strategy['auto_fix'], context
            )
            return {
                'status': 'escalated',
                'suggestions': fix_suggestions
            }
```

### 4.2 自动修复建议
```python
class AutoFixSuggester:
    """自动修复建议生成器"""

    async def suggest_locator_fix(self, failed_selector: str) -> List[str]:
        """为定位器失败生成修复建议"""
        suggestions = []

        # 基于历史数据
        similar_elements = await self._find_similar_elements(failed_selector)
        for element in similar_elements:
            suggestions.append(
                f"建议使用: [data-testid='{element['test_id']}']"
            )

        # 基于页面分析
        page_analysis = await self._analyze_page_structure()
        if page_analysis.has_unique_text:
            suggestions.append(
                f"建议使用文本定位: get_by_text('{page_analysis.unique_text}')"
            )

        return suggestions

    async def suggest_async_fix(self, task_id: str) -> List[str]:
        """为异步任务失败生成修复建议"""
        suggestions = []

        # 检查任务状态
        task_status = await self.api.get_task_status(task_id)

        if task_status == 'queued':
            suggestions.extend([
                "建议检查系统负载",
                "考虑降低任务优先级",
                "验证任务参数格式"
            ])
        elif task_status == 'failed':
            suggestions.extend([
                "建议检查输入参数",
                "验证资源配额",
                "联系系统管理员"
            ])

        return suggestions
```

## 五、性能优化策略

### 5.1 定位器性能优化
- **并行探测**：同时尝试L1和L2，取最快成功者
- **缓存机制**：成功定位结果短期缓存，避免重复查找
- **智能预算**：单次定位总时间控制在2秒内

### 5.2 异步任务优化
- **动态轮询间隔**：根据任务类型调整轮询频率
- **批量状态查询**：一次查询多个任务状态
- **预测超时**：基于历史数据预测合理超时值

### 5.3 文件处理优化
- **流式处理**：边下载边校验，减少内存占用
- **并行校验**：多文件并行验证
- **压缩传输**：支持压缩包减少传输时间