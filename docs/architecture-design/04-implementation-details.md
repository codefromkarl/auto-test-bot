# 04 - 具体实现细节

## 一、核心类设计

### 1.1 ScenarioContext实现
```python
# core/protocol/scenario_context.py
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from datetime import datetime
import json

@dataclass
class ScenarioContext:
    """跨层数据传输的标准协议"""

    # 基础信息
    test_id: str
    business_flow: str
    test_name: str

    # 测试数据
    test_data: Dict[str, Any] = field(default_factory=dict)
    environment: Dict[str, Any] = field(default_factory=dict)
    execution_options: Dict[str, Any] = field(default_factory=dict)

    # 期望结果
    expected_results: Dict[str, Any] = field(default_factory=dict)

    # 元数据
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    version: str = "1.0"

    # 序列化方法
    def to_json(self) -> str:
        """序列化为JSON"""
        data = {
            'test_id': self.test_id,
            'business_flow': self.business_flow,
            'test_name': self.test_name,
            'test_data': self.test_data,
            'environment': self.environment,
            'execution_options': self.execution_options,
            'expected_results': self.expected_results,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'version': self.version
        }
        return json.dumps(data, indent=2, ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str) -> 'ScenarioContext':
        """从JSON反序列化"""
        data = json.loads(json_str)
        created_at = datetime.fromisoformat(data['created_at'])
        updated_at = None
        if data['updated_at']:
            updated_at = datetime.fromisoformat(data['updated_at'])

        return cls(
            test_id=data['test_id'],
            business_flow=data['business_flow'],
            test_name=data['test_name'],
            test_data=data.get('test_data', {}),
            environment=data.get('environment', {}),
            execution_options=data.get('execution_options', {}),
            expected_results=data.get('expected_results', {}),
            created_at=created_at,
            updated_at=updated_at,
            version=data.get('version', '1.0')
        )

    def update(self, **kwargs):
        """更新上下文数据"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.now()

    def merge_test_data(self, data: Dict[str, Any]):
        """合并测试数据"""
        self.test_data.update(data)
        self.updated_at = datetime.now()
```

### 1.2 事件总线实现
```python
# core/events/event_bus.py
from typing import Dict, Callable, List
from asyncio import Queue
import asyncio
from datetime import datetime

class EventBus:
    """事件总线，用于跨层通信"""

    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}
        self._event_queue = Queue()
        self._running = False

    def subscribe(self, event_type: str, callback: Callable):
        """订阅事件"""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)

    async def publish(self, event_type: str, data: Dict[str, Any]):
        """发布事件"""
        event = {
            'type': event_type,
            'data': data,
            'timestamp': datetime.now().isoformat()
        }
        await self._event_queue.put(event)

    async def start_processing(self):
        """启动事件处理"""
        self._running = True
        while self._running:
            try:
                event = await asyncio.wait_for(
                    self._event_queue.get(),
                    timeout=1.0
                )
                await self._notify_subscribers(event)
            except asyncio.TimeoutError:
                continue

    def stop(self):
        """停止事件处理"""
        self._running = False

    async def _notify_subscribers(self, event: Dict[str, Any]):
        """通知订阅者"""
        event_type = event['type']
        if event_type in self._subscribers:
            tasks = []
            for callback in self._subscribers[event_type]:
                task = asyncio.create_task(callback(event))
                tasks.append(task)

            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
```

### 1.3 插件管理器
```python
# core/plugins/plugin_manager.py
from typing import Dict, Type
import importlib
import os
from .base import AIGCPlugin

class PluginManager:
    """插件管理器"""

    def __init__(self, plugin_dir: str):
        self.plugin_dir = plugin_dir
        self._plugins: Dict[str, AIGCPlugin] = {}
        self._plugin_configs: Dict[str, Dict] = {}

    async def load_plugins(self):
        """加载所有插件"""
        for filename in os.listdir(self.plugin_dir):
            if filename.endswith('.py') and not filename.startswith('__'):
                module_name = filename[:-3]
                try:
                    module = importlib.import_module(f'plugins.{module_name}')
                    # 查找插件类
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if (isinstance(attr, type) and
                            issubclass(attr, AIGCPlugin) and
                            attr != AIGCPlugin):

                            plugin_instance = attr()
                            await plugin_instance.setup()
                            self._plugins[plugin_instance.name] = plugin_instance
                            break
                except Exception as e:
                    print(f"Failed to load plugin {module_name}: {e}")

    async def unload_plugins(self):
        """卸载所有插件"""
        for plugin in self._plugins.values():
            await plugin.cleanup()
        self._plugins.clear()

    def get_plugin(self, name: str) -> AIGCPlugin:
        """获取插件实例"""
        return self._plugins.get(name)

    def list_plugins(self) -> Dict[str, Dict]:
        """列出所有插件及其能力"""
        return {
            name: {
                'capabilities': plugin.capabilities,
                'healthy': plugin.health_check()
            }
            for name, plugin in self._plugins.items()
        }

    async def execute_plugin(self, name: str, context: ScenarioContext, params: Dict):
        """执行指定插件"""
        plugin = self.get_plugin(name)
        if not plugin:
            raise ValueError(f"Plugin not found: {name}")

        return await plugin.execute(context, params)
```

## 二、增强定位器实现

### 2.1 事件驱动三级定位器
```python
# core/locator/three_tier_locator_v2.py
from typing import Optional, Dict, Any
import time
from .base import LocatorResult
from ..events.event_bus import EventBus
from ..metrics.collector import MetricsCollector

class EventDrivenThreeTierLocator:
    """事件驱动的三级定位器增强版"""

    def __init__(self, page, config: Dict, event_bus: EventBus):
        self.page = page
        self.config = config
        self.event_bus = event_bus
        self.metrics = MetricsCollector()

        # 定位策略配置
        self.strategies = {
            'gold': self._gold_strategy,
            'silver': self._silver_strategy,
            'bronze': self._bronze_strategy
        }

    async def locate_element(self, selector_config: Dict) -> LocatorResult:
        """主定位入口，记录完整指标"""
        start_time = time.time()
        attempt_count = 0

        # 遍历策略
        for strategy_name, strategy_func in self.strategies.items():
            attempt_count += 1

            try:
                result = await strategy_func(selector_config)

                if result.success:
                    # 发射成功事件
                    await self._emit_success_event(
                        strategy_name,
                        selector_config,
                        result,
                        time.time() - start_time,
                        attempt_count
                    )

                    # 更新指标
                    self.metrics.record_success(strategy_name, result)

                    return result

            except Exception as e:
                # 继续下一策略
                continue

        # 全部失败
        failure_result = await self._handle_total_failure(selector_config, time.time() - start_time)
        await self._emit_failure_event(selector_config, failure_result, attempt_count)

        return failure_result

    async def _gold_strategy(self, config: Dict) -> LocatorResult:
        """黄金策略：data-testid"""
        if not config.get('test_id'):
            return LocatorResult(success=False, error="No test_id provided")

        selector = f"[data-testid='{config['test_id']}']"
        element = self.page.locator(selector)

        # 严格验证
        if await element.count() == 0:
            return LocatorResult(success=False, error="Element not found")
        if await element.count() > 1:
            return LocatorResult(success=False, error="Multiple elements found")
        if not await element.first.is_visible():
            return LocatorResult(success=False, error="Element not visible")

        return LocatorResult(
            success=True,
            element=element.first,
            selector=selector,
            tier='gold'
        )

    async def _silver_strategy(self, config: Dict) -> LocatorResult:
        """白银策略：稳定属性"""
        # 尝试多种稳定属性
        stable_attrs = [
            f"[name='{config.get('name', '')}']",
            f"[id='{config.get('id', '')}']",
            f"[aria-label='{config.get('label', '')}']",
            f"[role='{config.get('role', '')}[name='{config.get('name', '')}']"
        ]

        for selector in stable_attrs:
            if selector.strip("[]="):
                element = self.page.locator(selector)

                if await element.count() == 1 and await element.first.is_visible():
                    return LocatorResult(
                        success=True,
                        element=element.first,
                        selector=selector,
                        tier='silver'
                    )

        return LocatorResult(success=False, error="No stable attribute found")

    async def _bronze_strategy(self, config: Dict) -> LocatorResult:
        """青铜策略：文本兜底"""
        if not config.get('text'):
            return LocatorResult(success=False, error="No text fallback provided")

        # 使用组合定位提高准确性
        base_selector = self.page.get_by_text(config['text'])
        element_count = await base_selector.count()

        if element_count == 0:
            return LocatorResult(success=False, error="Text not found")
        if element_count > 1:
            # 尝试缩小范围
            scope = config.get('scope')
            if scope:
                scoped_elements = base_selector.locator(f'xpath=.//{scope}')
                if await scoped_elements.count() == 1:
                    return LocatorResult(
                        success=True,
                        element=scoped_elements.first,
                        selector=f"{scope} >> text='{config['text']}'",
                        tier='bronze'
                    )

            # 记录风险事件
            await self._emit_risk_event(config, element_count)

        return LocatorResult(
            success=True,
            element=base_selector.first,
            selector=f"text='{config['text']}'",
            tier='bronze',
            warning="Used text fallback - consider adding test_id"
        )

    async def _emit_success_event(self, tier: str, config: Dict, result: LocatorResult,
                                elapsed: float, attempts: int):
        """发射定位成功事件"""
        await self.event_bus.publish('locator.success', {
            'tier': tier,
            'config': config,
            'result': {
                'selector': result.selector,
                'element_type': result.element_type if hasattr(result, 'element_type') else 'unknown'
            },
            'metrics': {
                'elapsed_time': elapsed * 1000,  # ms
                'attempts': attempts
            }
        })

    async def _emit_failure_event(self, config: Dict, result: LocatorResult, attempts: int):
        """发射定位失败事件"""
        await self.event_bus.publish('locator.failure', {
            'config': config,
            'error': result.error,
            'attempts': attempts,
            'suggested_fixes': await self._suggest_fixes(config)
        })
```

## 三、NaohaiAdapter实现

### 3.1 适配器核心
```python
# libraries/naohai_adapter_v2.py
from robot.api.deco import keyword, library
from typing import Dict, Any
import asyncio
from core.protocol.scenario_context import ScenarioContext
from core.plugins.plugin_manager import PluginManager
from core.locator.three_tier_locator_v2 import EventDrivenThreeTierLocator
from core.bot import AutoTestBot

@library(scope='TEST SUITE')
class NaohaiAdapterV2:
    """增强版Naohai适配器"""

    def __init__(self):
        # 异步支持
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        # 核心组件
        self.bot: Optional[AutoTestBot] = None
        self.plugin_manager: Optional[PluginManager] = None
        self.locator: Optional[EventDrivenThreeTierLocator] = None

        # 上下文管理
        self.current_context: Optional[ScenarioContext] = None
        self.context_stack: List[ScenarioContext] = []

    @keyword("初始化闹海测试环境V2")
    def init_environment(self, config_path: str = "config/prod.yaml"):
        """初始化测试环境"""
        try:
            # 初始化Bot
            self.bot = AutoTestBot(config_path)
            self.loop.run_until_complete(self.bot.initialize())

            # 初始化事件系统
            self.bot.event_bus = EventBus()
            self.loop.create_task(self.bot.event_bus.start_processing())

            # 初始化插件管理器
            self.plugin_manager = PluginManager("plugins/")
            self.loop.run_until_complete(self.plugin_manager.load_plugins())

            # 初始化定位器
            self.locator = EventDrivenThreeTierLocator(
                self.bot.page,
                self.bot.config,
                self.bot.event_bus
            )

            # 订阅定位器事件
            self.bot.event_bus.subscribe('locator.success', self._on_locator_success)
            self.bot.event_bus.subscribe('locator.failure', self._on_locator_failure)

            self.logger.info("闹海测试环境初始化完成V2")

        except Exception as e:
            raise RuntimeError(f"初始化失败: {str(e)}")

    @keyword("创建场景上下文")
    def create_scenario_context(self, test_id: str, business_flow: str,
                            test_name: str = "", **kwargs) -> str:
        """创建场景上下文"""
        context = ScenarioContext(
            test_id=test_id,
            business_flow=business_flow,
            test_name=test_name or test_id,
            **kwargs
        )

        self.current_context = context
        self.context_stack.append(context)

        return context.to_json()

    @keyword("执行插件")
    def execute_plugin(self, plugin_name: str, params_json: str = "{}") -> str:
        """执行AIGC插件"""
        if not self.current_context:
            raise RuntimeError("No active scenario context")

        params = json.loads(params_json)
        result = self.loop.run_until_complete(
            self.plugin_manager.execute_plugin(
                plugin_name,
                self.current_context,
                params
            )
        )

        # 更新上下文
        if result.status == 'completed':
            self.current_context.test_data.update(result.data)

        return json.dumps({
            'status': result.status,
            'data': result.data,
            'metrics': result.metrics
        })

    @keyword("智能点击V2")
    def smart_click_v2(self, element_key: str, fallback_config: str = "{}") -> str:
        """增强版智能点击"""
        if not self.locator:
            raise RuntimeError("Locator not initialized")

        # 解析配置
        config = {
            'test_id': element_key
        }

        if fallback_config:
            fallback_data = json.loads(fallback_config)
            config.update(fallback_data)

        # 执行定位
        start_time = time.time()
        result = self.loop.run_until_complete(
            self.locator.locate_element(config)
        )

        elapsed = time.time() - start_time

        # 处理结果
        if result.success:
            self.loop.run_until_complete(result.element.click())
            return json.dumps({
                'success': True,
                'tier_used': result.tier,
                'selector': result.selector,
                'elapsed_ms': elapsed * 1000
            })
        else:
            # 记录失败并触发MCP
            self._trigger_mcp_diagnostic(element_key, result.error)
            raise AssertionError(f"元素定位失败: {result.error}")

    @keyword("等待异步任务完成")
    def wait_for_async_task(self, task_id: str, timeout_seconds: int = 600) -> str:
        """等待异步任务完成"""
        result = self.loop.run_until_complete(
            self.plugin_manager.execute_plugin(
                'async_task',
                self.current_context,
                {
                    'task_id': task_id,
                    'timeout': timeout_seconds,
                    'sla': self._get_task_sla()
                }
            )
        )

        return json.dumps({
            'status': result.status,
            'result': result.data,
            'metrics': result.metrics
        })

    def _on_locator_success(self, event: Dict[str, Any]):
        """定位成功事件处理"""
        tier = event['data']['tier']
        elapsed = event['data']['metrics']['elapsed_time']

        if tier == 'bronze':
            self.logger.warn(f"⚠️ 使用了青铜级定位，耗时 {elapsed:.0f}ms")
        elif tier == 'silver':
            self.logger.info(f"ℹ️ 使用了白银级定位，耗时 {elapsed:.0f}ms")

    def _on_locator_failure(self, event: Dict[str, Any]):
        """定位失败事件处理"""
        config = event['data']['config']
        fixes = event['data']['suggested_fixes']

        self.logger.error(f"定位失败: {config}")
        self.logger.info(f"修复建议: {fixes}")

        # 自动触发MCP诊断
        self._trigger_mcp_diagnostic(config['test_id'], event['data']['error'])

    def _trigger_mcp_diagnostic(self, element_key: str, error: str):
        """触发MCP诊断"""
        if self.bot and hasattr(self.bot, 'mcp_diagnostic'):
            diagnostic = self.loop.run_until_complete(
                self.bot.mcp_diagnostic.diagnose_locator_failure(
                    element_key,
                    error,
                    self.current_context
                )
            )

            # 记录诊断结果
            self.logger.info(f"MCP诊断结果: {diagnostic}")

    def _get_task_sla(self) -> Dict[str, Any]:
        """获取任务SLA配置"""
        return {
            'timeout': 600,
            'retry_times': 3,
            'backoff': 'exponential',
            'poll_interval': 5,
            'success_rate_threshold': 0.95
        }
```

## 四、监控指标收集

### 4.1 指标收集器实现
```python
# core/metrics/collector.py
from typing import Dict, List
from datetime import datetime
import statistics
from collections import defaultdict

class MetricsCollector:
    """指标收集器"""

    def __init__(self):
        self._locator_metrics: List[Dict] = []
        self._task_metrics: List[Dict] = []
        self._file_metrics: List[Dict] = []
        self._slo_metrics: Dict[str, float] = {}

    def record_locator_attempt(self, tier: str, selector: str,
                          success: bool, elapsed_ms: float):
        """记录定位器指标"""
        self._locator_metrics.append({
            'timestamp': datetime.now().isoformat(),
            'tier': tier,
            'selector': selector,
            'success': success,
            'elapsed_ms': elapsed_ms
        })

    def calculate_tier_distribution(self) -> Dict[str, float]:
        """计算各级使用率分布"""
        total = len(self._locator_metrics)
        if total == 0:
            return {'gold': 0, 'silver': 0, 'bronze': 0}

        tier_counts = defaultdict(int)
        for metric in self._locator_metrics:
            if metric.get('success', False):
                tier_counts[metric['tier']] += 1

        total_success = sum(tier_counts.values())

        return {
            tier: (count / total_success) * 100
            for tier, count in tier_counts.items()
        }

    def calculate_slo_compliance(self, slo_config: Dict) -> Dict[str, bool]:
        """计算SLO合规性"""
        tier_dist = self.calculate_tier_distribution()

        compliance = {}
        for slo_name, slo_value in slo_config.items():
            if slo_name.startswith('tier_'):
                tier_name = slo_name.split('_')[1]
                actual_value = tier_dist.get(tier_name, 0)

                if 'max' in slo_value:
                    compliance[slo_name] = actual_value <= slo_value['max']
                elif 'min' in slo_value:
                    compliance[slo_name] = actual_value >= slo_value['min']

        return compliance

    def generate_report(self) -> Dict[str, Any]:
        """生成指标报告"""
        return {
            'summary': {
                'total_locates': len(self._locator_metrics),
                'success_rate': self._calculate_success_rate(),
                'avg_locate_time': self._calculate_avg_locate_time(),
                'tier_distribution': self.calculate_tier_distribution()
            },
            'details': {
                'locator_metrics': self._locator_metrics[-100:],  # 最近100条
                'slo_compliance': self.calculate_slo_compliance({
                    'gold_min': 70,
                    'silver_max': 25,
                    'bronze_max': 5
                })
            },
            'recommendations': self._generate_recommendations()
        }

    def _calculate_success_rate(self) -> float:
        """计算成功率"""
        if not self._locator_metrics:
            return 0.0

        successful = sum(1 for m in self._locator_metrics if m.get('success', False))
        total = len(self._locator_metrics)

        return (successful / total) * 100

    def _calculate_avg_locate_time(self) -> float:
        """计算平均定位时间"""
        successful_times = [
            m['elapsed_ms']
            for m in self._locator_metrics
            if m.get('success', False)
        ]

        if not successful_times:
            return 0.0

        return statistics.mean(successful_times)

    def _generate_recommendations(self) -> List[str]:
        """生成优化建议"""
        recommendations = []
        tier_dist = self.calculate_tier_distribution()

        if tier_dist.get('bronze', 0) > 10:
            recommendations.append(
                "青铜级使用率过高(>10%)，建议增加test_id覆盖"
            )

        if tier_dist.get('silver', 0) > 30:
            recommendations.append(
                "白银级使用率较高(>30%)，建议优化元素命名规范"
            )

        avg_time = self._calculate_avg_locate_time()
        if avg_time > 2000:
            recommendations.append(
                f"平均定位时间过长({avg_time:.0f}ms)，建议优化页面加载或定位策略"
            )

        return recommendations
```