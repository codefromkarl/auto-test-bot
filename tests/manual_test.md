# 手动测试指南

本文档提供了手动测试自动化测试机器人的详细指南。

## 📋 目录

1. [环境准备](#环境准备)
2. [本地测试步骤](#本地测试步骤)
3. [配置文件说明](#配置文件说明)
4. [故障排查](#故障排查)
5. [测试场景](#测试场景)

## 🔧 环境准备

### 系统要求

- **操作系统**: Windows 10+, macOS 10.14+, Linux (Ubuntu 18.04+)
- **Python**: 3.8 或更高版本
- **内存**: 至少 4GB RAM
- **存储**: 至少 2GB 可用空间
- **浏览器**: Chrome/Chromium (最新版本)

### Python 环境配置

1. **安装 Python 3.8+**
   ```bash
   # Windows (使用 Chocolatey)
   choco install python

   # macOS (使用 Homebrew)
   brew install python@3.8

   # Linux (Ubuntu/Debian)
   sudo apt update
   sudo apt install python3 python3-pip python3-venv
   ```

2. **创建虚拟环境**
   ```bash
   cd auto-test-bot
   python -m venv venv

   # Windows
   venv\\Scripts\\activate

   # macOS/Linux
   source venv/bin/activate
   ```

3. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

4. **安装 Playwright 浏览器**
   ```bash
   python -m playwright install
   ```

## 🧪 本地测试步骤

### 1. 基础配置测试

#### 配置文件准备
```bash
# 复制配置文件模板
cp config/config.yaml.example config/config.yaml
cp config/mcp_config.yaml.example config/mcp_config.yaml
```

#### 编辑配置文件
编辑 `config/config.yaml`：
```yaml
test:
  url: "https://your-test-site.com"  # 替换为实际测试网站
  timeout: 30000
  test_prompt: "一只可爱的猫咪在花园里玩耍"

steps:
  open_site: true
  generate_image: true
  generate_video: true

browser:
  type: "chromium"
  headless: false  # 设置为 false 以观察浏览器操作

logging:
  level: "INFO"
  console_output: true
```

### 2. 运行基础测试

#### 无 MCP 监控模式
```bash
# 基础测试
python src/main.py

# 调试模式
python src/main.py --debug
```

#### 启用 MCP 监控模式
```bash
# 启用 MCP 深度诊断
python src/main.py --mcp-diagnostic
```

#### 指定配置文件
```bash
python src/main.py --config path/to/your/config.yaml
```

### 3. 单步测试

#### 仅测试网站访问
创建 `test_open_site.py`:
```python
import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.browser import BrowserManager
from src.utils import ConfigLoader, setup_logging

async def test_open_site():
    # 加载配置
    config_loader = ConfigLoader("config/config.yaml")
    config = config_loader.load_config()

    # 设置日志
    setup_logging(config.get('logging', {}))
    logger = logging.getLogger(__name__)

    # 初始化浏览器
    browser = BrowserManager(config)
    if not await browser.initialize():
        logger.error("浏览器初始化失败")
        return False

    try:
        # 访问网站
        test_url = config.get('test', {}).get('url')
        if await browser.navigate_to(test_url):
            logger.info("网站访问成功")

            # 检查关键元素
            selectors = config.get('test', {}).get('selectors', {})
            for element_name, selector_list in selectors.items():
                if element_name in ['prompt_input', 'generate_image_button']:
                    for selector in selector_list:
                        if await browser.wait_for_element(selector, timeout=5000):
                            logger.info(f"找到元素 {element_name}: {selector}")
                            break
                    else:
                        logger.warning(f"未找到元素 {element_name}")

            return True
        else:
            logger.error("网站访问失败")
            return False

    finally:
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_open_site())
```

运行测试：
```bash
python test_open_site.py
```

### 4. 手动端到端测试

#### 完整测试流程检查清单

- [ ] **网站访问测试**
  - [ ] 网站能够正常打开
  - [ ] 页面加载完成，无 JavaScript 错误
  - [ ] 关键 DOM 元素存在（输入框、按钮等）
  - [ ] 页面响应正常

- [ ] **文生图测试**
  - [ ] 找到提示词输入框
  - [ ] 能够输入测试提示词
  - [ ] 找到并点击生成图片按钮
  - [ ] 等待图片生成完成（注意：这可能需要较长时间）
  - [ ] 生成的图片能够显示或获取到图片 URL

- [ ] **图生视频测试**
  - [ ] 基于已生成的图片操作
  - [ ] 找到并点击生成视频按钮
  - [ ] 等待视频生成完成（通常比图片生成时间更长）
  - [ ] 生成的视频能够显示或获取到视频 URL

- [ ] **结果验证**
  - [ ] 所有步骤执行状态正确
  - [ ] 生成的内容 URL 格式正确
  - [ ] 测试报告正确生成
  - [ ] 性能指标在合理范围内

## ⚙️ 配置文件说明

### 主配置文件 (config/config.yaml)

#### 必需配置项
```yaml
test:
  url: "https://your-test-site.com"     # 测试网站 URL
  timeout: 30000                          # 超时时间（毫秒）
  test_prompt: "测试提示词"                # 测试用的提示词

steps:
  open_site: true                        # 是否执行网站访问测试
  generate_image: true                   # 是否执行文生图测试
  generate_video: true                   # 是否执行图生视频测试

selectors:
  prompt_input: ["#prompt-input"]         # 提示词输入框选择器
  generate_image_button: ["#generate-btn"]  # 生成图片按钮选择器
  generate_video_button: ["#video-btn"]   # 生成视频按钮选择器
  image_result: [".image-result"]         # 图片结果选择器
  video_result: [".video-result"]         # 视频结果选择器
```

#### 可选配置项
```yaml
browser:
  type: "chromium"                       # 浏览器类型
  headless: true                          # 无头模式
  viewport:
    width: 1920
    height: 1080

logging:
  level: "INFO"
  file_path: "logs/test_bot.log"
  console_output: true

reporting:
  output_dir: "reports"
  format: "both"                           # json, html, both
  include_screenshots: true
```

### MCP 配置文件 (config/mcp_config.yaml)

#### MCP 服务器配置
```yaml
mcp_server:
  enabled: true                           # 启用 MCP 监控
  host: "localhost"
  port: 3000
  connection_timeout: 10000

tools:
  console_messages:
    enabled: true
  network_requests:
    enabled: true
  performance_tracing:
    enabled: true
  dom_debug:
    enabled: true
```

## 🐛 故障排查

### 常见问题及解决方案

#### 1. 浏览器启动失败
**错误信息**: `浏览器初始化失败`

**解决方案**:
```bash
# 重新安装 Playwright 浏览器
python -m playwright install

# 检查浏览器版本
python -m playwright --version

# 更新浏览器
python -m playwright install --force
```

#### 2. 找不到 DOM 元素
**错误信息**: `未找到元素: prompt_input`

**解决方案**:
- 检查网站是否已完全加载
- 验证选择器是否正确
- 尝试使用不同的选择器格式
- 检查元素是否在 iframe 中

#### 3. 图片/视频生成超时
**错误信息**: `生成失败或超时`

**解决方案**:
- 增加超时时间配置
- 检查后端服务状态
- 验证测试提示词是否合适
- 查看网络请求是否正常

#### 4. MCP 监控不工作
**错误信息**: `MCP 监控已禁用` 或连接失败

**解决方案**:
- 检查 MCP 服务器是否运行
- 验证端口配置是否正确
- 检查防火墙设置
- 确认 MCP 依赖是否正确安装

#### 5. 配置文件格式错误
**错误信息**: `配置文件格式错误`

**解决方案**:
```bash
# 验证 YAML 格式
python -c "import yaml; yaml.safe_load(open('config/config.yaml'))"

# 使用在线 YAML 验证工具
# https://yamlchecker.com/
```

### 调试技巧

#### 1. 启用详细日志
```yaml
logging:
  level: "DEBUG"
  console_output: true
```

#### 2. 使用非无头模式观察执行
```yaml
browser:
  headless: false
```

#### 3. 添加断点调试
在关键位置添加：
```python
import pdb; pdb.set_trace()
```

#### 4. 截图调试
在失败时自动截图：
```yaml
screenshots:
  enabled: true
  capture_on:
    - "step_failure"
    - "test_complete"
```

## 📊 测试场景

### 1. 正常流程测试
- 验证完整的"文生图 → 图生视频"流程
- 确保所有步骤都能成功执行
- 检查生成的结果质量

### 2. 错误场景测试
- 网站无法访问
- 输入无效提示词
- 服务器错误响应
- 超时场景处理

### 3. 性能测试
- 页面加载时间测试
- 生成时间测试
- 资源使用监控

### 4. 配置测试
- 不同选择器配置
- 不同超时设置
- 不同浏览器类型测试

### 5. 集成测试
- MCP 监控集成
- 报告生成测试
- 定时任务测试

## 📝 测试记录模板

### 测试执行记录

```markdown
## 测试执行记录

**日期**: 2024-01-01
**测试人员**: [姓名]
**测试环境**: [环境描述]

### 测试配置
- 网站 URL: [具体 URL]
- 浏览器: Chrome 120.0.0
- 超时设置: 30秒

### 执行结果
| 步骤 | 状态 | 耗时 | 备注 |
|------|------|------|------|
| 网站访问 | ✅ | 2.3s | 正常 |
| 文生图 | ✅ | 45.7s | 图片生成成功 |
| 图生视频 | ✅ | 123.5s | 视频生成成功 |
| 结果验证 | ✅ | 0.1s | 验证通过 |

### 生成内容
- 图片 URL: [URL 或 "未生成"]
- 视频 URL: [URL 或 "未生成"]

### 问题记录
- [问题描述]
- [解决方法]

### 建议
- [改进建议]
```

## 📞 获取帮助

如果遇到问题，请：

1. 查看 `logs/test_bot.log` 日志文件
2. 检查 `reports/` 目录中的测试报告
3. 参考本故障排查指南
4. 联系开发团队

---

**最后更新**: 2024-01-01
**文档版本**: 1.0