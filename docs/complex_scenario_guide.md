# 复杂场景测试指南

## 📋 概述

复杂场景测试是闹海测试系统的核心能力之一，专注于验证系统在真实、复杂环境下的表现。本指南详细介绍了如何编写、执行和优化复杂场景测试。

## 🎯 测试目标

### 1. 多项目管理测试
验证系统在同时处理多个项目时的：
- **数据隔离性**：确保不同项目间数据不会互相影响
- **切换性能**：项目间切换的响应时间和资源消耗
- **并发安全**：同时操作多个项目时的系统稳定性
- **状态持久化**：项目状态的正确保存和恢复

### 2. 并发操作测试
模拟多用户或复杂操作场景：
- **多用户并发**：100+并发用户同时操作系统
- **数据冲突处理**：并发编辑时的冲突解决机制
- **性能压力测试**：高负载下的系统响应能力
- **资源竞争处理**：资源共享和竞争的管理

### 3. 数据完整性测试
确保复杂操作后数据的正确性：
- **数据一致性**：复杂操作后数据保持一致
- **事务完整性**：操作的事务性保证
- **错误回滚**：失败时的数据回滚能力
- **状态同步**：多组件间状态同步的正确性

## 🛠️ 测试框架集成

### 工作流文件结构

复杂场景测试工作流位于 `workflows/resilience/` 目录下：

```yaml
workflow:
  name: "test_name"
  description: "测试描述"
  version: "v1.0"
  timeout: 600000  # 10分钟超时
  
  suite_setup:
    - action: "setup_common_environment"
      
  phases:
    - name: "phase_name"
      description: "阶段描述"
      steps:
        - action: "specific_action"
          parameters: {...}
          
  success_criteria:
    - "成功条件1"
    - "成功条件2"
    
  error_recovery:
    strategies:
      - name: "strategy_name"
        trigger_conditions: [...]
```

### 核心组件说明

#### 1. Suite Setup
全局初始化步骤，在所有阶段执行前运行：
```yaml
suite_setup:
  - action: "open_site"
    url: "${test.url}"
  - action: "navigate_to_ai_create"
  - action: "initialize_test_data"
```

#### 2. Phases
测试阶段，每个阶段可以包含多个步骤：
```yaml
phases:
  - name: "data_isolation_test"
    description: "数据隔离验证测试"
    steps:
      - action: "create_multiple_projects"
        project_count: 5
      - action: "verify_data_isolation"
        check_cross_contamination: true
```

#### 3. Success Criteria
测试成功的判断标准：
```yaml
success_criteria:
  - "所有项目创建成功"
  - "数据隔离验证通过"
  - "性能指标在可接受范围内"
```

#### 4. Error Recovery
错误处理和恢复策略：
```yaml
error_recovery:
  strategies:
    - name: "cleanup_on_failure"
      trigger_conditions: ["data_corruption"]
      actions: ["cleanup_test_data", "restore_baseline"]
```

## 📝 编写复杂场景测试

### 1. 多项目管理测试示例

```yaml
workflow:
  name: "multi_project_stress_test"
  description: "多项目管理压力测试"
  
  phases:
    - name: "create_multiple_projects"
      steps:
        - action: "create_project_batch"
          projects:
            - name: "测试项目_01"
              type: "video_production"
            - name: "测试项目_02"
              type: "script_writing"
            - name: "测试项目_03"
              type: "collaborative_editing"
          
        - action: "verify_project_creation"
          expected_count: 3
          
    - name: "test_project_switching"
      steps:
        - action: "perform_rapid_switching"
          switch_cycles: 50
          measure_performance: true
          
        - action: "verify_switching_performance"
          max_acceptable_time: 2000  # 2秒
```

### 2. 并发操作测试示例

```yaml
workflow:
  name: "concurrent_operations_test"
  description: "并发操作测试"
  
  phases:
    - name: "setup_concurrent_environment"
      steps:
        - action: "create_shared_workspace"
          workspace_name: "并发测试空间"
          
        - action: "simulate_multiple_users"
          user_count: 10
          
    - name: "execute_concurrent_operations"
      steps:
        - action: "perform_concurrent_edits"
          operations:
            - user: "user_1"
              action: "edit_script"
              target: "第一集"
            - user: "user_2" 
              action: "modify_character"
              target: "主角"
            - user: "user_3"
              action: "update_scene"
              target: "场景A"
          
        - action: "verify_conflict_resolution"
          expected_resolution: "auto_merge"
```

### 3. 数据完整性测试示例

```yaml
workflow:
  name: "data_integrity_test"
  description: "数据完整性验证测试"
  
  phases:
    - name: "establish_baseline"
      steps:
        - action: "create_data_checkpoint"
          checkpoint_name: "integrity_baseline"
          
    - name: "perform_complex_operations"
      steps:
        - action: "execute_complex_workflow"
          operations:
            - "create_project"
            - "add_multiple_episodes"
            - "upload_media_files"
            - "generate_ai_content"
            - "export_project"
          
        - action: "introduce_controlled_errors"
          error_types: ["network_timeout", "server_busy"]
          
    - name: "verify_integrity"
      steps:
        - action: "compare_with_checkpoint"
          checkpoint: "integrity_baseline"
          expected_changes:
            added: ["projects", "episodes", "media"]
            modified: ["timestamps", "metadata"]
            deleted: []
```

## 🔧 高级配置选项

### 1. 性能基准测试

```yaml
performance_testing:
  baseline:
    response_time_threshold: 2000  # ms
    memory_usage_threshold: 512   # MB
    cpu_usage_threshold: 80       # %
    
  stress_testing:
    concurrent_users: [10, 50, 100]
    duration_per_level: 300       # seconds
    ramp_up_time: 30              # seconds
```

### 2. 数据隔离配置

```yaml
data_isolation:
  isolation_level: "strict"  # strict, moderate, relaxed
  
  verification_points:
    - project_data
    - user_preferences
    - session_state
    - temporary_files
    
  cleanup_strategy:
    automatic_cleanup: true
    cleanup_delay: 300        # seconds
    preserve_on_failure: true
```

### 3. 并发控制

```yaml
concurrency_control:
  max_concurrent_operations: 50
  operation_timeout: 30000    # ms
  retry_strategy: "exponential_backoff"
  
  conflict_resolution:
    auto_merge: true
    manual_intervention_required: ["critical_conflicts"]
    fallback_strategy: "last_writer_wins"
```

## 📊 监控和报告

### 1. 性能监控指标

```yaml
monitoring:
  metrics:
    performance:
      - response_time
      - throughput
      - resource_usage
      - error_rate
      
    business:
      - operation_success_rate
      - data_consistency_score
      - user_experience_index
```

### 2. 报告配置

```yaml
reporting:
  include_performance_analysis: true
  include_resource_utilization: true
  include_data_integrity_analysis: true
  include_recommendations: true
  
  output_formats: ["json", "html", "markdown"]
  export_path: "reports/complex_scenarios/"
```

## 🚀 最佳实践

### 1. 测试设计原则

- **真实性**：模拟真实用户场景
- **可重复性**：确保测试结果可重复
- **可扩展性**：支持不同规模的测试
- **可维护性**：易于理解和修改

### 2. 数据管理

```yaml
data_management:
  isolation:
    use_separate_contexts: true
    cleanup_after_test: true
    
  generation:
    dynamic_data: true
    realistic_data: true
    avoid_hardcoded_values: true
```

### 3. 错误处理

```yaml
error_handling:
  graceful_degradation: true
  detailed_logging: true
  automatic_recovery: true
  user_friendly_messages: true
```

### 4. 性能优化

- **并行执行**：利用并行化提高测试效率
- **智能等待**：避免固定等待时间
- **资源管理**：及时释放不需要的资源
- **缓存策略**：合理使用缓存减少重复操作

## 📈 成功指标

### 1. 质量指标
- 测试覆盖率 > 90%
- 缺陷发现率提升 > 40%
- 回归测试通过率 > 95%

### 2. 性能指标
- 平均响应时间 < 2秒
- 并发处理能力 > 100用户
- 资源使用率 < 80%

### 3. 可靠性指标
- 测试稳定性 > 95%
- 错误恢复成功率 > 90%
- 数据一致性验证通过率 > 99%

## 🛠️ 故障排查

### 常见问题和解决方案

1. **数据隔离失败**
   - 检查测试上下文配置
   - 验证清理机制是否正常工作
   - 确认数据生成策略

2. **并发测试不稳定**
   - 调整并发参数
   - 增加等待时间
   - 优化同步机制

3. **性能测试结果异常**
   - 检查基准环境
   - 验证监控指标
   - 分析资源使用情况

4. **数据一致性验证失败**
   - 确认数据变更路径
   - 检查事务边界
   - 验证并发控制机制

## 📚 参考资源

- [测试数据管理最佳实践](test_data_management_best_practices.md)
- [边界条件测试指南](boundary_condition_guide.md)
- [架构设计文档](architecture-design/README.md)
- [网络模拟器使用指南](network_simulator_guide.md)