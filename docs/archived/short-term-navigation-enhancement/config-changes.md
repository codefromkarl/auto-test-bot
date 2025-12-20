# 配置文件变更说明

## 概述

本文档详细说明了在 `data_testid_config.yaml` 中需要添加的配置项，以支持"加号按钮创建文生图"的业务流程。

## 新增配置项

### 1. 创建相关定位器

在现有 `locators` 部分添加以下配置：

```yaml
# 创建相关定位器
create_button:
  - "[data-testid='create-button']"
  - "[data-testid='add-button']"
  - "[data-testid='create-new']"
  - "button:has-text('+')"
  - "button[aria-label='创建']"
  - "button[aria-label='新增']"
  - ".create-btn"
  - ".add-btn"
  - ".plus-button"

creation_menu:
  - "[data-testid='creation-menu']"
  - "[data-testid='create-menu']"
  - "[data-testid='dropdown-menu']"
  - ".creation-dropdown"
  - ".create-menu"
  - "[role='menu']"

text_image_option:
  - "[data-testid='text-image-option']"
  - "[data-testid='create-text-image']"
  - "[data-testid='text-image-menu-item']"
  - "menuitem:has-text('文生图')"
  - "li:has-text('文生图')"
  - ".menu-item:has-text('文生图')"
  - "a:has-text('文生图')"

# AI工具菜单中的文生图选项
text_image_in_tools:
  - "[data-testid='text-image-in-tools']"
  - "menuitem:has-text('文生图')"
  - "a:has-text('文生图')"
  - ".tool-item:has-text('文生图')"
```

### 2. 导航序列配置

在配置文件末尾添加新的 `navigation_sequences` 部分：

```yaml
# 导航序列配置
navigation_sequences:
  create_text_image_flow:
    description: "通过创建按钮进入文生图"
    steps:
      - locator: "create_button"
        wait_after: 500  # 等待菜单展开（毫秒）
        timeout: 5000     # 元素等待超时（毫秒）
      - locator: "text_image_option"
        wait_after: 1000 # 等待页面跳转（毫秒）
        timeout: 5000    # 元素等待超时（毫秒）

  ai_tools_text_image_flow:
    description: "通过AI工具进入文生图"
    steps:
      - locator: "nav_ai_tools_tab"
        wait_after: 1000  # 等待页面加载（毫秒）
        timeout: 10000    # 元素等待超时（毫秒）
      - locator: "text_image_in_tools"
        wait_after: 1000  # 等待页面跳转（毫秒）
        timeout: 5000     # 元素等待超时（毫秒）
```

### 3. 增强现有配置

优化现有的 `nav_text_image_tab` 配置：

```yaml
nav_text_image_tab:
  # 直接导航入口（保持现有配置）
  - "[data-testid='nav-text-image-tab']"
  - "[data-testid*='text'][data-testid*='image']"
  - "a:has-text('文生图')"
  - "button:has-text('文生图')"
  - ".nav-item:has-text('文生图')"

  # 创建流程入口（新增）
  - "[data-testid='create-text-image-direct']"
  - "button:has-text('创建文生图')"
  - ".create-option:has-text('文生图')"
```

## 配置参数说明

### 等待时间参数

- `wait_after`: 操作后等待时间（毫秒）
  - 500ms: 菜单展开时间
  - 1000ms: 页面跳转时间
  - 2000ms: 页面完全加载时间

- `timeout`: 元素等待超时时间（毫秒）
  - 5000ms: 普通元素超时
  - 10000ms: 页面级元素超时

### 优先级策略

配置按照以下优先级顺序尝试：

1. **直接入口**：`nav_text_image_tab` 配置
2. **创建流程**：`create_button` + `text_image_option`
3. **AI工具兜底**：`nav_ai_tools_tab` + `text_image_in_tools`

## 配置文件示例

完整的配置文件示例请参考：
- `examples/data_testid_config_enhanced.yaml` - 完整配置示例
- `examples/minimal-config-changes.yaml` - 最小变更示例

## 验证方法

1. **语法验证**：
```bash
python -c "import yaml; yaml.safe_load(open('config/data_testid_config.yaml'))"
```

2. **加载验证**：
```python
from utils import ConfigLoader
config = ConfigLoader('config/data_testid_config.yaml')
assert config.get_navigation_sequence('create_text_image_flow') is not None
```

3. **功能验证**：
运行测试脚本验证配置是否生效：
```bash
python scripts/test_navigation_config.py
```

## 注意事项

1. **向后兼容**：所有现有配置保持不变
2. **渐进增强**：新配置为可选，不影响现有功能
3. **灵活配置**：可根据实际UI调整选择器顺序和内容

## 故障排除

### 常见问题

1. **配置格式错误**：
   - 检查YAML缩进
   - 确认引号配对
   - 验证特殊字符转义

2. **定位器不生效**：
   - 检查 data-testid 值是否正确
   - 验证选择器语法
   - 确认元素在页面中存在

3. **导航序列失败**：
   - 调整等待时间参数
   - 检查每个步骤的超时设置
   - 验证步骤顺序逻辑

### 调试技巧

1. **启用调试日志**：
```yaml
# 在配置中添加
debug:
  navigation: true
  locators: true
```

2. **逐步验证**：
```python
# 测试单个定位器
await locator.click('create_button', timeout=5000)
```

3. **检查元素状态**：
```python
# 验证元素是否可见和可点击
element = page.locator("[data-testid='create-button']")
await element.wait_for(state='visible', timeout=5000)
assert await element.is_enabled()
```

## 最后更新

2025-12-17