# Data-TestId 集成快速开始

## 🚀 5分钟快速体验

### 1. 验证基础定位功能
```bash
# 使用度量定位器测试示例页面
PYTHONPATH=src python -c "
import asyncio
from playwright.async_api import async_playwright
from locator.metrics_hybrid_locator import MetricsHybridLocator

async def demo():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto('file://$(pwd)/docs/data-testid-integration/test_data_testid_example.html')

        locator = MetricsHybridLocator(page)
        element = await locator.locate('generate_image_button')

        print(f'定位成功: {element is not None}')
        print(f'命中率: {locator.get_metrics()[\"data_testid_hit_rate\"]}%')

        await browser.close()

asyncio.run(demo())
"
```

### 2. 运行完整集成测试
```bash
# 运行集成测试（会打开浏览器，可观察到定位过程）
PYTHONPATH=src python scripts/test_data_testid_integration.py --config config/main_config_with_testid.yaml
```

### 3. 验证 CI 门禁
```bash
# 生成覆盖率报告并验证门禁
PYTHONPATH=src python scripts/validate_testid_coverage.py --report reports/testid_coverage_gen_image_v2.json
```

## 📋 前端团队协作

### 必须添加的 data-testid（B 流程）
```html
<!-- 导航标签 -->
<a href="#/ai-create" data-testid="nav-ai-create-tab">AI创作</a>
<a href="#/text-image" data-testid="nav-text-image-tab">文生图</a>

<!-- 输入区域 -->
<textarea data-testid="prompt-textarea" placeholder="请输入提示词..."></textarea>

<!-- 操作按钮 -->
<button data-testid="generate-image-button" onclick="generateImage()">生成图片</button>

<!-- 状态指示器 -->
<div data-testid="loading-indicator" style="display:none;">加载中...</div>

<!-- 结果展示 -->
<div data-testid="image-result">
  <img data-testid="generated-image" />
</div>

<!-- 错误消息 -->
<div data-testid="error-message" style="display:none;"></div>
```

### PR 检查清单
- [ ] 新增交互元素是否添加了 `data-testid`
- [ ] `data-testid` 命名是否符合短横线（kebab-case）规范
- [ ] 是否更新了 `config/required_testids.yaml`
- [ ] 运行本地测试验证覆盖率

## ⚙️ 配置使用

### 使用新配置文件
```yaml
# 在测试步骤中
from locator.metrics_hybrid_locator import MetricsHybridLocator

# 创建带度量的定位器
locator = MetricsHybridLocator(page, config.get('locators', {}))

# 使用定位器（自动记录策略）
success = await locator.click('generate_image_button')

# 获取度量数据
metrics = locator.get_metrics()
print(f"data-testid 命中率: {metrics['data_testid_hit_rate']}%")
```

### 集成到现有步骤
```python
# 在步骤的 __init__ 中
self.locator = MetricsHybridLocator(browser.page, config.get('locators', {}))

# 替换原有的定位逻辑
# 旧代码：
# element = await self.browser.page.locator("#generate-image-btn")

# 新代码：
# element = await self.locator.locate('generate_image_button')
```

## 📊 报告查看

### 覆盖率报告位置
```bash
# HTML 报告（可视化查看）
open reports/testid_coverage_gen_image_v2.html

# JSON 报告（程序化处理）
cat reports/testid_coverage_gen_image_v2.json | jq '.data_testid_hit_rate'
```

### 关键指标说明
- **data-testid_hit_rate**: data-testid 命中率，目标 ≥ 80%
- **fallback_rate**: 回退策略使用率，目标 ≤ 20%
- **required_testids_coverage**: 关键路径覆盖率，目标 100%

## 🛠️ 常见问题解决

### Q: 定位器找不到元素？
A: 检查以下几点：
1. 元素是否真的在页面中
2. data-testid 拼写是否正确
3. 元素是否被其他元素遮挡

### Q: data-testid 命中率低？
A: 可能的原因：
1. 前端未添加对应的 data-testid
2. data-testid 命名不一致
3. 优先级配置错误

### Q: CI 验证失败？
A: 检查步骤：
1. 运行测试并生成报告
2. 检查覆盖率是否达标
3. 查看具体的失败原因

## 🔗 相关文档

- [实施计划](./data-testid-implementation-plan.md)
- [定位策略](./data-testid-locator-strategy.md)
- [方案总结](./data-testid-solution-summary.md)
- [实施总结](./implementation-summary.md)

## 💡 最佳实践

### 命名规范
```
{feature}-{component}-{action/state}

示例：
- nav-ai-create-tab
- prompt-textarea
- generate-image-button
- loading-indicator
- error-message
```

### 配置管理
```yaml
# 优先级排序
locators:
  element_name:
    - "[data-testid='优先的']"     # 第一选择
    - "稳定的CSS选择器"          # 回退选择
    - "文本定位"                # 最后选择
```

### 度量驱动
1. **定期检查**：每周查看覆盖率趋势
2. **及时响应**：覆盖率下降立即修复
3. **持续改进**：基于数据优化定位策略

---

**开始使用**：按照上述步骤，5分钟内即可体验到 data-testid 集成带来的稳定性和可度量性提升！
