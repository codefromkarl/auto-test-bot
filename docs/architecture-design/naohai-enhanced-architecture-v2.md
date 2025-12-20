# 闹海AIGC平台自动化测试架构增强版 v2.0

## 一、版本更新说明

基于Codex深度分析和改进建议，本版本在v1.0基础上进行了以下关键增强：

### 1.1 核心改进
- **引入跨层契约协议**：定义可序列化的"场景上下文"协议
- **AIGC能力插件化**：将异步、文件、API混编封装为独立插件
- **增强监控体系**：添加SLO指标和可视化仪表盘
- **完善迁移策略**：制定详细的兼容性矩阵和回归清单

## 二、三层架构增强设计

### 2.1 跨层契约协议

```python
# 场景上下文协议 - 确保层间解耦
class ScenarioContext:
    """跨层数据传输的标准格式"""

    def __init__(self):
        self.test_id: str = ""
        self.business_flow: str = ""
        self.test_data: Dict = {}
        self.environment: Dict = {}
        self.execution_options: Dict = {}
        self.expected_results: Dict = {}

    def to_json(self) -> str:
        """序列化为JSON，便于跨层传输"""
        return json.dumps(self.__dict__)

    @classmethod
    def from_json(cls, json_str: str):
        """从JSON反序列化"""
        data = json.loads(json_str)
        return cls(**data)
```

### 2.2 Layer 1: 业务编排层增强

**新增能力**：
```robot
*** Settings ***
Library    NaohaiAdapter    WITH NAME    adapter
Library    OperatingSystem

*** Variables ***
&{CONTEXT_TEMPLATE}    test_id=    business_flow=    test_data={}    environment={}    execution_options={}    expected_results={}

*** Keywords ***
初始化场景上下文
    [Arguments]    ${test_id}    ${business_flow}
    ${context}=    Set Variable    &{CONTEXT_TEMPLATE}
    Set To Dictionary    ${context}    test_id=${test_id}
    Set To Dictionary    ${context}    business_flow=${business_flow}
    ${json}=    adapter.序列化上下文    ${context}
    Set Suite Variable    ${SCENARIO_CONTEXT}    ${json}

执行带上下文的操作
    [Arguments]    ${keyword}    @{args}
    ${context}=    Get Suite Variable    ${SCENARIO_CONTEXT}
    ${result}=    adapter.执行关键字    ${keyword}    @{args}    context=${context}
    [Return]    ${result}
```

### 2.3 Layer 2: 适配层插件化

#### 2.3.1 AIGC能力插件接口
```python
from abc import ABC, abstractmethod

class AIGCPlugin(ABC):
    """AIGC能力插件基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        """插件名称"""
        pass

    @property
    @abstractmethod
    def capabilities(self) -> List[str]:
        """插件能力列表"""
        pass

    @abstractmethod
    async def execute(self, context: ScenarioContext, params: Dict) -> Dict:
        """执行插件功能"""
        pass
```

#### 2.3.2 异步任务插件实现
```python
class AsyncTaskPlugin(AIGCPlugin):
    """异步长任务插件"""

    @property
    def name(self) -> str:
        return "async_task"

    @property
    def capabilities(self) -> List[str]:
        return ["video_generation", "image_generation", "batch_processing"]

    async def execute(self, context: ScenarioContext, params: Dict) -> Dict:
        """智能任务观察者实现"""
        observer = TaskObserver(
            task_id=params['task_id'],
            sla_config=params.get('sla', {
                'timeout': 600,
                'retry_times': 3,
                'backoff_strategy': 'exponential'
            })
        )

        # 优先尝试事件通知
        if params.get('use_webhook', True):
            result = await observer.wait_via_webhook()
        else:
            result = await observer.wait_via_polling(interval=5)

        return {
            'status': 'completed',
            'result': result,
            'metrics': observer.get_metrics()
        }
```

#### 2.3.3 文件处理插件实现
```python
class FileProcessingPlugin(AIGCPlugin):
    """文件处理流水线插件"""

    @property
    def name(self) -> str:
        return "file_processing"

    @property
    def capabilities(self) -> List[str]:
        return ["download", "extract", "validate", "cleanup"]

    async def execute(self, context: ScenarioContext, params: Dict) -> Dict:
        """流式文件处理"""
        pipeline = FilePipeline([
            DownloadStage(max_size=params.get('max_size', 500*1024*1024)),
            ExtractStage(target_dir=params.get('extract_dir', 'temp')),
            ValidationStage(rules=params.get('rules', {})),
            CleanupStage(keep_temp=params.get('keep_temp', False))
        ])

        result = await pipeline.process(params['file_info'])
        return {
            'status': 'completed',
            'files': result.files,
            'validation_report': result.validation,
            'metrics': pipeline.get_metrics()
        }
```

### 2.4 Layer 3: 核心引擎增强

#### 2.4.1 三级定位器事件化
```python
class EventDrivenThreeTierLocator(ThreeTierLocator):
    """事件驱动的三级定位器"""

    def __init__(self, page, config):
        super().__init__(page, config)
        self.event_bus = EventBus()
        self.metrics = EnhancedMetrics()

    async def locate(self, selector_config):
        """定位并发射事件"""
        start_time = time.time()

        # L1: Gold Tier
        if result := await self._try_gold(selector_config):
            await self.event_bus.emit('locator.gold_hit', {
                'selector': selector_config,
                'result': result,
                'elapsed': time.time() - start_time
            })
            return self._enhance_result(result, 'gold')

        # L2: Silver Tier
        if result := await self._try_silver(selector_config):
            await self.event_bus.emit('locator.silver_fallback', {
                'selector': selector_config,
                'result': result,
                'elapsed': time.time() - start_time
            })
            return self._enhance_result(result, 'silver')

        # L3: Bronze Tier
        if result := await self._try_bronze(selector_config):
            await self.event_bus.emit('locator.bronze_fallback', {
                'selector': selector_config,
                'result': result,
                'elapsed': time.time() - start_time
            })
            return self._enhance_result(result, 'bronze')

        # 完全失败
        await self.event_bus.emit('locator.failure', {
            'selector': selector_config,
            'elapsed': time.time() - start_time
        })
        return None
```

## 三、增强的监控体系

### 3.1 SLO指标定义
```yaml
# monitoring/slo.yaml
slo:
  locator_performance:
    gold_hit_rate: 0.7          # 黄金级命中率 ≥ 70%
    silver_fallback_rate: 0.25    # 白银级回退率 ≤ 25%
    bronze_fallback_rate: 0.05    # 青铜级回退率 ≤ 5%
    max_single_locator_time: 2000   # 单次定位耗时 ≤ 2秒

  async_tasks:
    task_completion_rate: 0.95     # 任务完成率 ≥ 95%
    avg_wait_time: 300            # 平均等待时间 ≤ 5分钟
    timeout_rate: 0.02            # 超时率 ≤ 2%

  file_processing:
    validation_success_rate: 0.98  # 文件校验成功率 ≥ 98%
    disk_usage_efficiency: 0.8    # 磁盘使用效率 ≥ 80%
```

### 3.2 可视化仪表盘
```python
class DashboardMetrics:
    """实时仪表盘数据收集"""

    def __init__(self):
        self.metrics_db = MetricsDB()
        self.alert_system = AlertSystem()

    def collect_locator_metrics(self):
        """收集定位器指标"""
        return {
            'tier_distribution': self.metrics_db.get_tier_distribution(),
            'avg_locate_time': self.metrics_db.get_avg_locate_time(),
            'failure_patterns': self.metrics_db.get_failure_patterns(),
            'coverage_trend': self.metrics_db.get_coverage_trend()
        }

    def collect_aigc_metrics(self):
        """收集AIGC任务指标"""
        return {
            'task_completion_rate': self.metrics_db.get_completion_rate(),
            'wait_time_distribution': self.metrics_db.get_wait_time_dist(),
            'sla_compliance': self.metrics_db.get_sla_compliance()
        }

    def generate_alerts(self):
        """生成告警"""
        alerts = []

        # 检查SLO违规
        if self.metrics_db.get_gold_hit_rate() < 0.7:
            alerts.append({
                'type': 'slo_violation',
                'metric': 'gold_hit_rate',
                'value': self.metrics_db.get_gold_hit_rate(),
                'threshold': 0.7
            })

        return alerts
```

## 四、实施计划增强版

### Phase 1: 基础框架与契约（2周）
- [ ] 实现ScenarioContext协议
- [ ] 开发EventBus事件系统
- [ ] 创建NaohaiAdapter基础框架
- [ ] 实现插件管理器
- [ ] 单元测试覆盖率 ≥ 80%

### Phase 2: AIGC插件开发（3周）
- [ ] 实现AsyncTaskPlugin（含TaskObserver）
- [ ] 实现FileProcessingPlugin（含Pipeline）
- [ ] 实现APIMixingPlugin（数据准备）
- [ ] 集成测试覆盖率 ≥ 85%
- [ ] 性能基准测试

### Phase 3: 监控体系完善（2周）
- [ ] 部署MetricsDB和EventBus
- [ ] 实现Dashboard可视化
- [ ] 配置SLO告警规则
- [ ] 集成Slack/钉钉通知
- [ ] 监控数据完整性验证

### Phase 4: 渐进式迁移（3周）
- [ ] 兼容性矩阵验证（见附录A）
- [ ] 环境一致性演练（3次）
- [ ] 核心场景灰度测试（30%流量）
- [ ] 全量切换准备
- [ ] 回滚预案验证

### Phase 5: 优化与治理（持续）
- [ ] 每周SLO回顾
- [ ] 每月架构评审
- [ ] 每季度插件生态评估
- [ ] 持续性能优化

## 五、风险缓解增强

### 5.1 定位器误点风险（高）
**缓解措施**：
1. **严格唯一性检查**：L3必须count()==1才允许执行
2. **语义一致性验证**：检查元素的role/tag是否符合预期
3. **范围锚点强制**：L3必须在已知容器内执行
4. **视觉校验（可选）**：执行前截图对比

### 5.2 异步任务超时（中）
**缓解措施**：
1. **动态超时计算**：基于历史数据调整超时值
2. **指数退避重试**：失败时自动重试，间隔递增
3. **任务状态机**：完整支持排队/处理/完成/失败状态
4. **断点续传**：长任务支持暂停后恢复

### 5.3 文件处理瓶颈（中）
**缓解措施**：
1. **流式处理**：边下载边校验，减少内存占用
2. **并行处理**：多文件并行校验
3. **磁盘空间监控**：预留空间不足时提前告警
4. **临时文件清理**：自动化清理机制

## 六、兼容性矩阵

### 6.1 关键场景迁移矩阵
| 场景 | 旧方式 | 新方式 | 迁移状态 | 风险等级 |
|------|--------|--------|----------|----------|
| 视频生成 | 直接Bot调用 | Adapter AsyncTaskPlugin | Phase 2 | 低 |
| 资源包校验 | 手工验证 | FileProcessingPlugin | Phase 2 | 中 |
| 定位器使用 | MetricsHybridLocator | EventDrivenThreeTierLocator | Phase 1 | 低 |
| MCP诊断 | 手动触发 | 自动事件触发 | Phase 3 | 低 |
| CI门禁 | 硬阻断 | 软门禁+SLO | Phase 3 | 中 |

### 6.2 回归检查清单
```yaml
# migration/checklist.yaml
pre_migration:
  - [ ] 备份现有配置文件
  - [ ] 记录基线性能数据
  - [ ] 确认回滚路径可用
  - [ ] 通知相关团队计划时间

post_migration:
  - [ ] 验证核心用例通过率
  - [ ] 检查SLO指标符合预期
  - [ ] 对比性能基线无回归
  - [ ] 确认监控告警正常
  - [ ] 收集团队反馈
```

## 七、附录

### 附录A：环境一致性演练脚本
```python
# scripts/environment_consistency_check.py
async def check_environment_consistency():
    """验证新旧环境的一致性"""

    # 1. 配置对比
    old_config = load_old_config()
    new_config = load_new_config()

    # 2. 关键接口验证
    for endpoint in critical_endpoints:
        old_response = await old_client.get(endpoint)
        new_response = await new_client.get(endpoint)
        assert_same_schema(old_response, new_response)

    # 3. 性能基准对比
    old_perf = await benchmark_old_system()
    new_perf = await benchmark_new_system()

    # 4. 生成报告
    return generate_consistency_report({
        'config_diff': compare_configs(old_config, new_config),
        'api_compatibility': verify_api_compatibility(),
        'performance_delta': calculate_perf_delta(old_perf, new_perf)
    })
```

### 附录B：插件开发模板
```python
# plugins/plugin_template.py
class TemplatePlugin(AIGCPlugin):
    """插件开发模板"""

    def __init__(self):
        self.config = self.load_config()
        self.metrics = PluginMetrics()

    async def setup(self):
        """插件初始化"""
        pass

    async def cleanup(self):
        """插件清理"""
        pass

    async def health_check(self):
        """健康检查"""
        return {'status': 'healthy', 'details': {}}
```

---

**文档版本**：v2.0
**更新日期**：2025-12-17
**基于**：Codex深度分析和建议
**主要贡献**：跨层契约、插件化架构、增强监控、完善迁移策略