# 闹海测试流程机器可读定义

## 概述

闹海测试是一个基于Workflow-First架构的端到端自动化测试系统，主要用于验证AI创作平台的完整功能链路。

## 核心阶段（按执行顺序）

### 1. 环境准备阶段 (Environment Preparation)
- **输入**：
  - `config/config.yaml` - 系统主配置文件
  - `auth_session.json` - 认证会话文件
  - 本地服务运行在端口 9020
  - 测试环境URL配置
- **输出**：
  - `environment_ready` (boolean) - 环境是否就绪
  - `browser_initialized` (boolean) - 浏览器是否初始化成功
  - `auth_validated` (boolean) - 认证是否有效
- **关键检查点**：
  - 本地服务连通性检查
  - 浏览器实例可用性检查
  - 用户登录状态验证
- **失败类型**：
  - `auth_failure` - 认证失败或token过期
  - `service_unavailable` - 本地服务9020未启动
  - `config_invalid` - 配置文件缺失或格式错误
  - `browser_init_failed` - 浏览器初始化失败
- **是否可并行**：**否**（必须串行，环境准备是后续所有阶段的前提）
- **预估耗时**：15-30秒

### 2. 工作流解析阶段 (Workflow Parsing)
- **输入**：
  - `workflows/fc/*.yaml` - 具体的测试工作流文件
  - 环境配置参数（超时、重试等）
- **输出**：
  - `parsed_stages` (list) - 解析后的阶段列表
  - `execution_plan` (object) - 包含所有步骤的执行计划
  - `resource_requirements` (object) - 所需资源清单
- **关键检查点**：
  - YAML文件语法正确性
  - Action定义有效性验证
  - 参数占位符完整性检查
- **失败类型**：
  - `workflow_file_not_found` - 工作流文件不存在
  - `yaml_syntax_error` - YAML语法错误
  - `action_not_supported` - 包含不支持的动作类型
  - `parameter_missing` - 必需参数缺失
- **是否可并行**：**否**（解析工作流本身是串行逻辑）
- **预估耗时**：2-5秒

### 3. 用例执行阶段 (Test Execution)
- **输入**：
  - `parsed_stages` - 已解析的阶段列表
  - `execution_plan` - 详细执行计划
  - 可用的浏览器实例
- **输出**：
  - `case_results` (list) - 每个测试用例的执行结果
  - `execution_traces` (list) - 详细的执行轨迹
  - `artifacts` (object) - 生成的截图、日志等文件
- **关键检查点**：
  - 每个Action的执行状态
  - 页面元素状态变化
  - 业务断言结果
- **失败类型**：
  - `element_not_found` - 页面元素定位失败
  - `timeout_unexpected` - 操作超时
  - `assertion_failed` - 业务断言失败
  - `browser_crash` - 浏览器崩溃
  - `page_load_failed` - 页面加载失败
- **是否可并行**：**部分可并行**
  - **可并行维度**：多个独立的workflow文件（workflow级别并行）
  - **不可并行**：单个workflow内的phases和steps（存在时序依赖）
  - **并行策略**：建议在workflow级别并行，避免复杂的依赖管理
- **预估耗时**：2-10分钟（取决于用例复杂度）

### 4. 结果汇总阶段 (Result Aggregation)
- **输入**：
  - `case_results` - 所有测试用例结果
  - `execution_traces` - 执行轨迹
  - `artifacts` - 生成文件清单
- **输出**：
  - `final_report` - 最终测试报告（JSON/HTML/Excel格式）
  - `summary_metrics` - 汇总指标（成功率、耗时等）
  - `recommendations` - 基于结果的优化建议
- **关键检查点**：
  - 数据完整性验证
  - 报告格式正确性
  - 指标计算准确性
- **失败类型**：
  - `report_generation_failed` - 报告生成失败
  - `data_corruption` - 结果数据损坏
  - `file_write_error` - 文件写入权限或空间问题
- **是否可并行**：**否**（汇总必须是串行操作）
- **预估耗时**：5-15秒

## 失败边界定义 (Failure Boundaries)

### 严重级别：Critical (立即停止所有执行)
- `service_unavailable` - 本地服务不可用
- `browser_crash` - 浏览器崩溃
- `config_invalid` - 配置文件错误

### 严重级别：High (重试3次后停止)
- `auth_failure` - 认证失败
- `workflow_file_not_found` - 工作流文件缺失

### 严重级别：Medium (继续执行后续用例)
- `element_not_found` - 页面元素缺失
- `timeout_unexpected` - 操作超时
- `assertion_failed` - 业务断言失败

### 严重级别：Low (记录但不影响执行)
- `report_generation_failed` - 报告生成失败
- `file_write_error` - 非关键文件写入失败

## 并行执行策略

### ✅ 推荐并行点
- **Workflow级别**：多个独立的workflow文件可以并行执行
- **Case级别**：如果workflow之间完全独立，可以在case级别并行

### ❌ 不推荐并行点
- **Phase级别**：workflow内的phases存在依赖关系
- **Step级别**：steps通常是时序敏感的
- **Action级别**：原子操作不应该并行

### 🔧 并行配置建议
```yaml
parallel_execution:
  enabled: true
  level: "workflow"  # 推荐，避免复杂依赖
  max_concurrent_workflows: 3
  sharding_strategy: "file_based"  # 按文件分配
```

## 环境依赖清单

### 必需的外部依赖
- 本地服务运行在 `localhost:9020`
- 可访问的测试环境URL
- 有效的认证会话文件

### 必需的系统资源
- 内存：至少2GB空闲
- 磁盘：至少1GB可用空间（用于截图和日志）
- 网络：稳定的互联网连接

### 可选依赖
- 截图目录 `screenshots/` (自动创建)
- 报告输出目录 `reports/` (自动创建)

## 监控和可观测性

### 关键指标
- 各阶段执行时间
- 成功率统计
- 失败类型分布
- 资源使用情况

### 日志级别建议
- **INFO**：正常的执行流程
- **WARN**：可恢复的错误或重试
- **ERROR**：严重失败需要人工介入
- **DEBUG**：详细的执行轨迹（仅调试时启用）

## 版本兼容性

- **Python**：3.8+
- **Playwright**：1.40+
- **Workflow Schema**：v2.0
- **配置格式**：YAML 1.2

---

*此文档应与代码实现保持同步，任何流程变更都需要更新此定义。*