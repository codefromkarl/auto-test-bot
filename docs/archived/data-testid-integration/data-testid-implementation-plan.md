# Data-TestId 接入实施计划

## 项目概述

为测试机器人实现基于 `data-testid` 的稳定元素定位策略，提高测试的可靠性和可维护性。

## 实施阶段

### 阶段一：基础架构搭建（第1-2周）

#### 1.1 定位器框架开发 ✅
- [x] 创建 `DataTestIdLocator` 类
- [x] 创建 `HybridLocator` 混合定位器
- [x] 实现多策略回退机制

#### 1.2 配置系统设计 ✅
- [x] 设计 `data-testid` 映射配置
- [x] 创建定位策略配置文件
- [x] 实现配置动态加载机制

#### 1.3 测试步骤重构（待完成）
- [ ] 重构 `open_site.py` 使用新的定位器
- [ ] 重构 `gen_image.py` 使用增强版定位器
- [ ] 重构 `gen_video.py` 使用增强版定位器
- [ ] 更新导航步骤使用混合定位器

### 阶段二：前端 Data-TestId 集成（第3-4周）

#### 2.1 现有页面改造
- [ ] 首页导航元素添加 `data-testid`
- [ ] AI创作页面关键元素添加 `data-testid`
- [ ] 文生图页面完整 `data-testid` 覆盖
- [ ] 图生视频页面 `data-testid` 覆盖

#### 2.2 命名规范制定
- [ ] 确立统一的命名约定
- [ ] 创建前端开发指南文档
- [ ] 建立代码审查检查清单

#### 2.3 自动化检测工具
- [ ] 开发 `data-testid` 覆盖率检测脚本
- [ ] 创建缺失 `data-testid` 报告工具
- [ ] 集成到 CI/CD 流程

### 阶段三：测试流程优化（第5-6周）

#### 3.1 测试用例更新
- [ ] 更新所有测试用例使用 `data-testid`
- [ ] 实现测试用例参数化配置
- [ ] 添加定位器验证步骤

#### 3.2 错误处理增强
- [ ] 改进元素定位失败的处理逻辑
- [ ] 实现智能重试机制
- [ ] 添加详细的诊断信息

#### 3.3 报告系统升级
- [ ] 集成 `data-testid` 覆盖率到测试报告
- [ ] 添加定位策略有效性分析
- [ ] 实现失败原因自动分析

### 阶段四：性能优化与稳定性（第7-8周）

#### 4.1 性能优化
- [ ] 优化定位器查找性能
- [ ] 实现定位器缓存机制
- [ ] 减少不必要的页面查询

#### 4.2 稳定性提升
- [ ] 增强超时处理机制
- [ ] 实现页面状态检测
- [ ] 添加网络异常恢复策略

#### 4.3 监控与告警
- [ ] 实施测试成功率监控
- [ ] 设置 `data-testid` 覆盖率告警
- [ ] 创建自动化健康检查

## 详细实施步骤

### 步骤1：创建定位器初始化模块

```python
# src/locator/__init__.py
from .data_testid_locator import DataTestIdLocator
from .hybrid_locator import HybridLocator

def create_locator(page, config):
    """创建定位器实例"""
    return HybridLocator(page, config.get('locators', {}))
```

### 步骤2：更新主程序集成

```python
# src/main.py 更新示例
from locator import create_locator

async def main():
    # ... 现有代码 ...

    # 创建定位器
    locator = create_locator(browser.page, config)

    # 传递给测试步骤
    step = EnhancedGenImageStep(browser, config, locator)
```

### 步骤3：前端 Data-TestId 添加指南

#### 3.1 识别关键交互元素

```javascript
// 需要添加 data-testid 的元素类型
const criticalElements = [
    // 导航
    'nav-home-tab', 'nav-ai-create-tab', 'nav-text-image-tab',

    // 输入
    'prompt-input', 'prompt-textarea', 'style-selector',

    // 按钮
    'generate-image-button', 'generate-video-button', 'clear-button',

    // 结果
    'image-result', 'video-result', 'loading-indicator',

    // 状态
    'error-message', 'success-message', 'toast-message'
];
```

#### 3.2 添加方法示例

```html
<!-- 导航标签 -->
<a href="#/home/dashboard" data-testid="nav-home-tab">首页</a>
<a href="#/ai-create" data-testid="nav-ai-create-tab">AI创作</a>
<a href="#/text-image" data-testid="nav-text-image-tab">文生图</a>

<!-- 输入区域 -->
<textarea
    placeholder="请输入您的创作提示词"
    data-testid="prompt-textarea"
    class="arco-textarea">
</textarea>

<!-- 生成按钮 -->
<button
    type="button"
    class="arco-btn arco-btn-primary"
    data-testid="generate-image-button"
    onclick="generateImage()">
    生成图片
</button>

<!-- 结果展示 -->
<div class="image-result" data-testid="image-result">
    <img src="..." alt="生成的图片" />
</div>
```

### 步骤4：测试流程更新

#### 4.1 配置文件更新
```yaml
# 更新测试配置使用新的定位器
steps:
  generate_image: true
  use_enhanced_locator: true
  enable_diagnostics: true

locators:
  # 使用新的定位策略
  prompt_input:
    - "[data-testid='prompt-textarea']"  # 优先使用
    - "textarea[placeholder*='提示']"    # 回退策略
    - ".arco-textarea"                   # 最后选择
```

#### 4.2 测试步骤重构
```python
# 更新测试步骤使用 HybridLocator
class GenImageStep:
    def __init__(self, browser, config, locator=None):
        self.browser = browser
        self.config = config
        # 使用增强定位器或默认定位器
        self.locator = locator or HybridLocator(browser.page)

    async def execute(self):
        # 使用定位器替代硬编码选择器
        if await self.locator.fill('prompt_input', self.test_prompt):
            # 继续执行
```

## 时间线规划

| 周次 | 主要任务 | 交付物 |
|------|----------|---------|
| 第1周 | 定位器框架开发 | DataTestIdLocator, HybridLocator |
| 第2周 | 配置系统实现 | 配置文件、配置加载器 |
| 第3周 | 首页和AI创作页面改造 | 页面 data-testid 覆盖 |
| 第4周 | 文生图和视频页面改造 | 完整页面 data-testid 覆盖 |
| 第5周 | 测试用例更新 | 更新后的测试步骤 |
| 第6周 | 错误处理和报告 | 增强的错误处理、报告系统 |
| 第7周 | 性能优化 | 定位器优化、缓存机制 |
| 第8周 | 监控和部署 | 监控系统、生产部署 |

## 风险评估与应对

### 高风险项
1. **前端开发资源紧张**
   - 应对：分阶段实施，优先关键页面
   - 备选：提供自动化添加工具

2. **现有功能回归**
   - 应对：充分测试，灰度发布
   - 备选：保留原有定位器作为回退

### 中风险项
1. **性能影响**
   - 应对：性能测试，优化查询策略
   - 备选：实现定位器缓存

2. **学习成本**
   - 应对：提供详细文档和培训
   - 备选：创建开发工具辅助

### 低风险项
1. **配置维护**
   - 应对：自动化验证和报告
   - 备选：版本控制配置文件

## 成功标准

### 技术指标
- [ ] `data-testid` 覆盖率达到 80% 以上
- [ ] 测试成功率提升至 95% 以上
- [ ] 定位器平均响应时间 < 100ms
- [ ] 测试执行时间不增加超过 10%

### 质量指标
- [ ] 定位策略有效性 > 90%
- [ ] 元素定位失败率 < 1%
- [ ] 诊断覆盖率 100%
- [ ] 文档完整性 100%

## 维护计划

### 日常维护
- 监控 `data-testid` 覆盖率
- 验证定位策略有效性
- 更新配置文件

### 定期维护（每月）
- 审查新增页面元素
- 优化定位策略
- 更新文档

### 版本发布（每季度）
- 重大功能更新
- 性能优化
- 安全加固

## 附录

### A. 相关文档
- [Data-TestId 定位策略](./data-testid-locator-strategy.md)
- [前端开发指南](./frontend-data-testid-guide.md)
- [测试用例规范](./test-case-specification.md)

### B. 工具和脚本
- [覆盖率检测脚本](../scripts/check_testid_coverage.py)
- [配置验证脚本](../scripts/validate_locators.py)
- [自动添加工具](../scripts/add_testids.py)

### C. 示例代码
- [定位器使用示例](../examples/locator_examples.py)
- [测试步骤示例](../examples/step_examples.py)
- [配置示例](../config/examples/)