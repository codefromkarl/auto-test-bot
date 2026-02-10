# 高级测试功能使用指南

## 📋 概述

本指南介绍闹海测试系统的高级功能，包括复杂场景测试、边界条件测试、网络模拟、测试数据管理和错误处理增强功能。这些功能为系统提供了企业级的测试能力。

## 🚀 快速开始

### 环境要求

确保系统满足以下要求：
- Python 3.8+
- Playwright 已安装
- 足够的系统资源（内存 > 4GB）

### 基础配置

1. **更新配置文件**
```yaml
# config/enhanced_test_config.yaml
test:
  timeout:
    page_load: 30000
    element_load: 5000
    network_operation: 60000
    
  enhanced_features:
    complex_scenarios: true
    boundary_testing: true
    network_simulation: true
    data_management: true
    
  resources:
    max_concurrent_operations: 50
    memory_threshold: 2048  # MB
    cpu_threshold: 80      # %
```

2. **启用高级功能**
```bash
# 启用所有高级功能
python src/main_workflow.py --config config/enhanced_test_config.yaml --enhanced-mode

# 启用特定功能
python src/main_workflow.py --config config/enhanced_test_config.yaml --feature complex-scenarios
```

## 🎯 复杂场景测试

### 1. 多项目管理测试

运行多项目管理测试：

```bash
# 执行完整的多项目管理测试
python src/main_workflow.py \
  --workflow workflows/resilience/naohai_complex_multi_project_management.yaml \
  --config config/enhanced_test_config.yaml
```

**测试内容**：
- 数据隔离验证
- 快速项目切换性能
- 并发项目操作
- 资源消耗监控

**输出结果**：
```json
{
  "test_name": "multi_project_management",
  "success": true,
  "results": {
    "data_isolation": "passed",
    "switching_performance": {
      "average_time": "1.2s",
      "max_time": "2.1s",
      "performance_degradation": "15%"
    },
    "concurrent_operations": {
      "success_rate": "98%",
      "data_conflicts": "0"
    },
    "resource_usage": {
      "memory_peak": "512MB",
      "cpu_average": "45%"
    }
  }
}
```

### 2. 并发操作测试

```bash
# 运行并发操作测试
python src/main_workflow.py \
  --workflow workflows/resilience/naohai_complex_multi_project_management.yaml \
  --phase concurrent_project_operations \
  --concurrent-users 20
```

**监控指标**：
- 并发用户数
- 操作成功率
- 响应时间分布
- 错误类型分析

### 3. 数据完整性测试

```bash
# 数据完整性验证
python src/main_workflow.py \
  --workflow workflows/resilience/naohai_complex_multi_project_management.yaml \
  --phase data_consistency_stress_test \
  --verify-integrity
```

## 🧪 边界条件测试

### 1. 输入验证边界测试

```bash
# 运行边界条件测试
python src/main_workflow.py \
  --workflow workflows/resilience/naohai_boundary_condition_stress_test.yaml \
  --config config/enhanced_test_config.yaml
```

**测试用例类型**：
- 文本长度边界（空、最小、最大、超长）
- 数值边界（最小值、最大值、溢出）
- 日期边界（最早、最晚、无效日期）
- 文件格式边界（支持、不支持、伪装）

### 2. 资源约束测试

```bash
# 内存约束测试
python src/main_workflow.py \
  --workflow workflows/resilience/naohai_boundary_condition_stress_test.yaml \
  --phase resource_constraint_test \
  --memory-limit 256

# 网络约束测试
python src/main_workflow.py \
  --workflow workflows/resilience/naohai_boundary_condition_stress_test.yaml \
  --phase resource_constraint_test \
  --network-condition slow_3g
```

**资源约束场景**：
- 内存限制：256MB、64MB、16MB
- 网络条件：3G、4G、离线、不稳定
- 存储空间：100MB、10MB、耗尽
- CPU负载：80%、90%、95%

### 3. 时间和数据量边界测试

```bash
# 时间边界测试
python src/main_workflow.py \
  --workflow workflows/resilience/naohai_boundary_condition_stress_test.yaml \
  --phase time_boundary_test

# 数据量边界测试
python src/main_workflow.py \
  --workflow workflows/resilience/naohai_boundary_condition_stress_test.yaml \
  --phase data_volume_boundary_test
```

## 🌐 网络模拟功能

### 1. 网络条件模拟

```bash
# 使用网络模拟器
from src.utils.network_simulator import network_simulator, NetworkCondition

# 设置网络条件
network_simulator.set_network_condition(NetworkCondition.SLOW_3G)

# 执行网络测试
response = network_simulator.simulate_request({
    "url": "https://example.com/api",
    "method": "GET"
})

print(f"Response time: {response['response_time']}ms")
print(f"Throughput: {response['throughput']} Kbps")
```

**预定义网络条件**：
- `NORMAL`: 10 Mbps下载，5 Mbps上传，50ms延迟
- `SLOW_3G`: 500 Kbps下载，500 Kbps上传，400ms延迟
- `FAST_3G`: 1.6 Mbps下载，750 Kbps上传，300ms延迟
- `SLOW_4G`: 4 Mbps下载，3 Mbps上传，150ms延迟
- `FAST_4G`: 10 Mbps下载，5 Mbps上传，50ms延迟
- `OFFLINE`: 无网络连接
- `UNSTABLE`: 不稳定网络（抖动大）
- `PACKET_LOSS`: 15%丢包率

### 2. 错误场景模拟

```bash
# 添加自定义错误场景
from src.utils.network_simulator import ErrorScenario, ErrorType

error_scenario = ErrorScenario(
    name="Custom Timeout",
    error_type=ErrorType.TIMEOUT_ERROR,
    trigger_conditions={"probability": 0.1},
    duration=30000
)

network_simulator.add_error_scenario(error_scenario)
```

### 3. 网络性能监控

```bash
# 获取网络统计信息
stats = network_simulator.get_network_statistics()

print(f"Total requests: {stats['total_requests']}")
print(f"Error rate: {stats['error_rate']:.2%}")
print(f"Average latency: {stats['average_latency']}ms")
print(f"Packet loss rate: {stats['packet_loss_rate']:.2%}")
```

## 📊 测试数据管理

### 1. 动态数据生成

```python
from src.utils.test_data_manager import test_data_manager

# 生成文本数据
text_data = test_data_manager.generate_dynamic_data(
    data_type="text",
    constraints={
        "min_length": 10,
        "max_length": 100,
        "include_special_chars": True
    },
    variation="normal"
)

# 生成数字数据
number_data = test_data_manager.generate_dynamic_data(
    data_type="number",
    constraints={
        "min_value": 0,
        "max_value": 100,
        "is_float": True,
        "precision": 2
    },
    variation="boundary"
)

# 生成日期数据
date_data = test_data_manager.generate_dynamic_data(
    data_type="date",
    constraints={
        "start_date": "2024-01-01",
        "end_date": "2024-12-31",
        "format": "%Y-%m-%d"
    },
    variation="normal"
)
```

### 2. 数据隔离管理

```python
# 创建隔离上下文
context_id = test_data_manager.create_isolation_context("test_scenario_1")

# 存储隔离数据
test_data_manager.store_isolated_data(context_id, "username", "test_user_001")
test_data_manager.store_isolated_data(context_id, "email", "test@example.com")

# 检索隔离数据
username = test_data_manager.retrieve_isolated_data(context_id, "username")
email = test_data_manager.retrieve_isolated_data(context_id, "email")

# 清理隔离上下文
test_data_manager.cleanup_isolation_context(context_id)
```

### 3. 数据变异功能

```python
# 数据变异
original_data = {"name": "test_user", "age": 25, "email": "test@example.com"}

mutated_data = test_data_manager.mutate_data(
    original_data=original_data,
    mutation_type="random",
    mutation_intensity=0.1
)

print(f"Original: {original_data}")
print(f"Mutated: {mutated_data}")
```

### 4. 测试数据套件生成

```python
# 生成测试数据套件
data_specifications = [
    {
        "name": "user_profile",
        "type": "text",
        "constraints": {"min_length": 5, "max_length": 50},
        "variations": ["normal", "boundary", "edge"]
    },
    {
        "name": "user_age",
        "type": "number",
        "constraints": {"min_value": 18, "max_value": 100},
        "variations": ["normal", "boundary", "invalid"]
    }
]

test_suite = test_data_manager.generate_test_data_suite(data_specifications)
print(f"Generated test suite: {test_suite['suite_id']}")
```

## 🛡️ 增强错误处理

### 1. 智能重试机制

```yaml
# 在工作流中配置重试策略
error_handling:
  retry_configuration:
    default_max_retries: 3
    default_initial_delay: 1000
    max_backoff_delay: 30000
    backoff_multiplier: 2.0
    
  retry_strategies:
    network_timeout: "exponential_backoff"
    rate_limit: "linear_backoff"
    server_error: "exponential_backoff"
    client_error: "no_retry"
```

### 2. 优雅降级

```yaml
# 降级级别配置
degradation_levels:
  - level: "minimal"
    preserved_features: ["core_functionality", "user_data"]
    
  - level: "moderate"
    preserved_features: ["core_functionality", "user_data", "basic_ui"]
    
  - level: "severe"
    preserved_features: ["user_data_preservation", "emergency_exit"]
```

### 3. 用户友好的错误处理

```bash
# 运行错误处理测试
python src/main_workflow.py \
  --workflow workflows/resilience/naohai_enhanced_error_handling_test.yaml \
  --phase user_friendly_error_handling
```

## 📈 监控和报告

### 1. 实时监控

```python
# 添加监控回调
def monitoring_callback(event_type, data):
    if event_type == "request_completed":
        print(f"Request completed in {data['response_time']}ms")
    elif event_type == "error_occurred":
        print(f"Error: {data['error_type']}")

network_simulator.add_monitoring_callback(monitoring_callback)
```

### 2. 生成报告

```bash
# 生成详细测试报告
python src/main_workflow.py \
  --workflow workflows/resilience/naohai_boundary_condition_stress_test.yaml \
  --report-format html \
  --report-path reports/enhanced_test_report.html
```

**报告内容包括**：
- 测试执行概览
- 性能指标分析
- 错误统计和分析
- 边界条件覆盖情况
- 改进建议

### 3. 数据导出

```python
# 导出测试数据
test_data_manager.export_test_data(
    context_id="test_context_1",
    export_path="test_data_export.json"
)

# 导入测试数据
imported_context = test_data_manager.import_test_data("test_data_import.json")
```

## 🛠️ 高级配置

### 1. 性能调优

```yaml
# config/performance_config.yaml
performance:
  optimization:
    enable_parallel_execution: true
    max_parallel_tasks: 5
    cache_enabled: true
    cache_ttl: 3600
    
  thresholds:
    response_time_warning: 2000  # ms
    response_time_critical: 5000  # ms
    memory_usage_warning: 1024   # MB
    cpu_usage_warning: 80        # %
```

### 2. 自定义网络配置

```python
# 创建自定义网络配置
from src.utils.network_simulator import NetworkProfile

custom_profile = NetworkProfile(
    name="Custom Slow Network",
    download_throughput=1000,  # 1 Mbps
    upload_throughput=500,     # 500 Kbps
    latency=800,               # 800ms
    packet_loss_rate=0.05,     # 5%
    jitter=300                 # 300ms
)

network_simulator.current_profile = custom_profile
```

### 3. 测试环境配置

```yaml
# config/test_environment.yaml
environment:
  browser:
    headless: false
    viewport_width: 1920
    viewport_height: 1080
    
  timeouts:
    default: 30000
    navigation: 60000
    element_load: 5000
    
  data:
    cleanup_after_test: true
    preserve_on_failure: true
    backup_before_test: true
```

## 🚀 最佳实践

### 1. 测试执行策略

```bash
# 分阶段执行测试
# 1. 冒烟测试
python src/main_workflow.py --phase smoke_test

# 2. 功能测试
python src/main_workflow.py --phase functional_test

# 3. 边界条件测试
python src/main_workflow.py --phase boundary_test

# 4. 压力测试
python src/main_workflow.py --phase stress_test
```

### 2. 资源管理

- **内存管理**：定期清理测试数据，避免内存泄漏
- **并发控制**：合理设置并发数，避免系统过载
- **资源监控**：实时监控资源使用情况

### 3. 错误处理

- **分类处理**：根据错误类型选择合适的处理策略
- **用户友好**：提供清晰的错误信息和恢复指导
- **自动恢复**：尽可能实现自动恢复机制

### 4. 数据管理

- **数据隔离**：确保测试数据不会互相影响
- **动态生成**：避免硬编码测试数据
- **数据清理**：测试完成后及时清理数据

## 📚 故障排查

### 常见问题

1. **测试执行超时**
   ```bash
   # 检查超时配置
   grep -n "timeout" config/enhanced_test_config.yaml
   
   # 增加超时时间
   python src/main_workflow.py --timeout 600000
   ```

2. **内存不足**
   ```bash
   # 检查内存使用
   python src/main_workflow.py --monitor-memory
   
   # 减少并发数
   python src/main_workflow.py --max-concurrent 2
   ```

3. **网络模拟失败**
   ```bash
   # 检查网络配置
   python -c "from src.utils.network_simulator import network_simulator; print(network_simulator.current_profile)"
   
   # 重置网络配置
   python src/main_workflow.py --reset-network
   ```

## 📚 参考资源

- [复杂场景测试指南](complex_scenario_guide.md)
- [边界条件测试指南](boundary_condition_guide.md)
- [测试数据管理最佳实践](test_data_management_best_practices.md)
- [架构设计文档](architecture-design/README.md)
- [Chrome DevTools MCP 使用指南](chrome-devtools-mcp-guide.md)