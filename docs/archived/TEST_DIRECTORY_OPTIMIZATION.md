# 测试目录优化方案

## 一、目标结构

```
project/
├── tests/                    # 单元测试和集成测试
│   ├── unit/             # 单元测试
│   ├── integration/        # 集成测试
│   └── e2e/             # 端到端测试
├── test_artifacts/            # 测试产物（统一命名）
│   ├── reports/           # 标准报告
│   ├── screenshots/        # 截图文件
│   └── logs/             # 测试日志
├── config/
│   ├── test_config.yaml     # 测试配置
│   └── ci_config.yaml      # CI配置
└── scripts/
    └── run_tests.py        # 统一测试入口
```

## 二、具体实施计划

### Phase 1: 清理现有目录（立即执行）
1. **重组 tests/ 目录**
   - `tests/unit/` - 保留核心模块单元测试
   - `tests/integration/` - 保留架构集成测试
   - `tests/e2e/` - 保留端到端测试
   - 删除重复/过时的测试文件

2. **统一测试产物**
   - 创建 `test_artifacts/` 目录
   - 迁移 `reports/` → `test_artifacts/reports/`
   - 迁移 `test_reports/` → `test_artifacts/reports/`
   - 统一截图存储到 `test_artifacts/screenshots/`

3. **清理配置文件**
   - 合并重复配置
   - 标准化配置格式
   - 删除无用配置

### Phase 2: 建立测试规范（1-2周）
1. **文件命名规范**
   - 报告：`test_{suite}_{timestamp}.{json|html}`
   - 截图：`test_{scenario}_{timestamp}.png`
   - 日志：`test_{timestamp}.log`

2. **测试分类标准**
   - 单元测试：`tests/unit/test_*.py`
   - 集成测试：`tests/integration/test_*.py`
   - 端到端：`tests/e2e/test_*.py`

3. **CI集成**
   - 配置文件路径标准化
   - 测试报告自动收集
   - 失败截图自动保存

### Phase 3: 优化工具链（2-3周）
1. **统一测试入口**
   - 创建 `scripts/run_tests.py` 统一入口
   - 支持按类型、标签运行测试
   - 集成报告生成和收集

2. **监控和度量**
   - 测试覆盖率统计
   - 性能基准测试
   - 历史趋势分析

## 三、清理清单

### 立即删除（高风险）
- [ ] `test_reports/` 中的200+个历史报告
- [ ] `reports/` 中的临时文件
- [ ] `tests/` 中重复的测试文件
- [ ] 过时的配置文件

### 备份后删除（中风险）
- [ ] 保留最近1周的测试报告
- [ ] 保留关键配置文件备份
- [ ] 文档化迁移过程

## 四、执行优先级

### 🚨 高优先级（立即执行）
1. 清理 test_reports/ 历史文件
2. 创建 test_artifacts/ 目录结构
3. 迁移当前 reports/ 内容

### 🟡 中优先级（本周）
1. 重组 tests/ 目录
2. 标准化配置文件
3. 更新 CI 脚本

### 🟢 低优先级（下周）
1. 优化测试工具链
2. 建立监控仪表板
3. 完善文档

## 五、成功标准

- [ ] tests/ 目录结构清晰，无重复
- [ ] test_artifacts/ 目录建立并使用
- [ ] CI/CD 正常运行
- [ ] 团队了解新的测试流程
- [ ] 测试报告可追溯、可对比

---

**预期收益**：
- 🎯 测试效率提升 30%
- 📊 报告质量显著改善
- 🚀 CI/CD 稳定性提高
- 👥 团队协作更清晰