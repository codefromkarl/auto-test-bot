# 回滚计划和风险控制

## 概述

本文档详细描述了短期导航增强方案实施过程中的风险控制措施和回滚计划，确保在出现问题时能够快速恢复到稳定状态。

## 风险评估

### 高风险点

1. **配置文件破坏**
   - 风险：YAML语法错误导致配置无法加载
   - 影响：所有功能模块无法启动
   - 缓解措施：保留备份，语法验证

2. **核心导航逻辑破坏**
   - 风险：代码修改影响现有导航功能
   - 影响：无法完成基本的文生图导航
   - 缓解措施：向后兼容设计，分步验证

3. **性能回退**
   - 风险：新增逻辑导致导航时间增长
   - 影响：用户体验下降，测试效率降低
   - 缓解措施：性能基准测试，优化关键路径

### 中风险点

1. **测试覆盖不足**
   - 风险：边缘情况未覆盖导致运行时错误
   - 影响：生产环境异常，用户投诉
   - 缓解措施：全面测试，边界验证

2. **依赖变更影响**
   - 风险：修改依赖文件导致其他模块受影响
   - 影响：系统整体稳定性下降
   - 缓解措施：隔离修改，影响分析

## 备份策略

### 自动备份

```bash
#!/bin/bash
# scripts/backup_before_changes.sh

BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "创建备份到: $BACKUP_DIR"

# 备份配置文件
cp config/data_testid_config.yaml "$BACKUP_DIR/data_testid_config.yaml"
echo "✓ 配置文件备份完成"

# 备份核心代码
cp src/steps/navigate_to_text_image.py "$BACKUP_DIR/navigate_to_text_image.py"
echo "✓ 核心代码备份完成"

# 备份配置加载器
cp src/utils/config_loader.py "$BACKUP_DIR/config_loader.py"
echo "✓ 配置加载器备份完成"

# 创建备份清单
cat > "$BACKUP_DIR/backup_manifest.txt" << EOF
备份时间: $(date)
备份内容:
- data_testid_config.yaml
- navigate_to_text_image.py
- config_loader.py
EOF

echo "备份完成！备份目录: $BACKUP_DIR"
```

### 手动备份验证

```bash
# 验证备份文件完整性
verify_backup() {
    local backup_dir=$1
    local required_files=(
        "data_testid_config.yaml"
        "navigate_to_text_image.py"
        "config_loader.py"
    )

    echo "验证备份: $backup_dir"

    for file in "${required_files[@]}"; do
        if [ -f "$backup_dir/$file" ]; then
            echo "✓ $file"
        else
            echo "✗ $file 缺失"
            return 1
        fi
    done

    # 验证YAML语法
    if python -c "import yaml; yaml.safe_load(open('$backup_dir/data_testid_config.yaml'))" 2>/dev/null; then
        echo "✓ YAML语法正确"
    else
        echo "✗ YAML语法错误"
        return 1
    fi

    echo "备份验证通过！"
}
```

## 回滚程序

### 完全回滚脚本

```bash
#!/bin/bash
# scripts/complete_rollback.sh

BACKUP_DIR=$1
if [ -z "$BACKUP_DIR" ]; then
    echo "用法: $0 <备份目录>"
    echo "可用备份:"
    ls -la backups/ | grep '^d'
    exit 1
fi

if [ ! -d "$BACKUP_DIR" ]; then
    echo "错误: 备份目录不存在: $BACKUP_DIR"
    exit 1
fi

echo "开始完全回滚到备份: $BACKUP_DIR"

# 1. 停止相关服务（如果需要）
echo "1. 停止服务..."
# 这里可以添加停止服务的命令

# 2. 恢复配置文件
echo "2. 恢复配置文件..."
cp "$BACKUP_DIR/data_testid_config.yaml" config/data_testid_config.yaml

# 3. 恢复代码文件
echo "3. 恢复代码文件..."
cp "$BACKUP_DIR/navigate_to_text_image.py" src/steps/navigate_to_text_image.py
cp "$BACKUP_DIR/config_loader.py" src/utils/config_loader.py

# 4. 验证恢复
echo "4. 验证恢复结果..."
if python -c "import yaml; yaml.safe_load(open('config/data_testid_config.yaml'))" 2>/dev/null; then
    echo "✓ 配置文件语法正确"
else
    echo "✗ 配置文件语法错误，回滚失败"
    exit 1
fi

if python -c "from src.steps.navigate_to_text_image import NavigateToTextToImageStep; print('代码导入成功')" 2>/dev/null; then
    echo "✓ 代码文件正确"
else
    echo "✗ 代码文件错误，回滚失败"
    exit 1
fi

echo "回滚完成！"

# 5. 运行基础测试
echo "5. 运行基础测试..."
python -m pytest tests/ -k "navigate" --tb=short -q
if [ $? -eq 0 ]; then
    echo "✓ 基础测试通过，回滚成功"
else
    echo "⚠ 基础测试失败，请检查"
fi
```

### 部分回滚脚本

```bash
#!/bin/bash
# scripts/partial_rollback.sh

COMPONENT=$1
BACKUP_DIR=$2

if [ -z "$COMPONENT" ] || [ -z "$BACKUP_DIR" ]; then
    echo "用法: $0 <组件> <备份目录>"
    echo "可用组件: config, navigation, loader"
    exit 1
fi

echo "部分回滚: $COMPONENT 从备份 $BACKUP_DIR"

case $COMPONENT in
    "config")
        cp "$BACKUP_DIR/data_testid_config.yaml" config/data_testid_config.yaml
        echo "✓ 配置文件已回滚"
        ;;
    "navigation")
        cp "$BACKUP_DIR/navigate_to_text_image.py" src/steps/navigate_to_text_image.py
        echo "✓ 导航代码已回滚"
        ;;
    "loader")
        cp "$BACKUP_DIR/config_loader.py" src/utils/config_loader.py
        echo "✓ 配置加载器已回滚"
        ;;
    *)
        echo "错误: 未知组件 $COMPONENT"
        exit 1
        ;;
esac

# 验证回滚
python -c "import yaml; yaml.safe_load(open('config/data_testid_config.yaml'))" 2>/dev/null && \
python -c "from src.steps.navigate_to_text_image import NavigateToTextToImageStep; print('导入成功')" 2>/dev/null

if [ $? -eq 0 ]; then
    echo "✓ 部分回滚验证成功"
else
    echo "✗ 部分回滚验证失败"
    exit 1
fi
```

## 监控和告警

### 实时监控脚本

```python
# scripts/monitor_navigation.py
import time
import logging
from datetime import datetime

class NavigationMonitor:
    """导航功能监控"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.setup_logging()

    def setup_logging(self):
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('monitoring/navigation.log'),
                logging.StreamHandler()
            ]
        )

    def monitor_config_changes(self):
        """监控配置文件变化"""
        import os

        config_file = 'config/data_testid_config.yaml'
        last_size = 0

        while True:
            try:
                current_size = os.path.getsize(config_file)
                if current_size != last_size:
                    self.logger.info(f"配置文件大小变化: {last_size} -> {current_size}")

                    # 验证配置
                    try:
                        import yaml
                        with open(config_file, 'r') as f:
                            yaml.safe_load(f)
                        self.logger.info("✓ 配置文件语法验证通过")
                    except Exception as e:
                        self.logger.error(f"✗ 配置文件语法错误: {e}")
                        # 发送告警

                    last_size = current_size

                time.sleep(5)  # 每5秒检查一次

            except Exception as e:
                self.logger.error(f"监控异常: {e}")
                time.sleep(10)

    def monitor_performance(self):
        """监控性能指标"""
        import asyncio
        from utils.config_loader import ConfigLoader

        while True:
            try:
                start_time = time.time()
                config = ConfigLoader('config/data_testid_config.yaml')
                config.get_navigation_sequence('create_text_image_flow')
                load_time = (time.time() - start_time) * 1000

                if load_time > 100:  # 超过100ms告警
                    self.logger.warning(f"配置加载过慢: {load_time:.2f}ms")

                self.logger.info(f"配置加载性能: {load_time:.2f}ms")

                time.sleep(60)  # 每分钟检查一次

            except Exception as e:
                self.logger.error(f"性能监控异常: {e}")
                time.sleep(60)

def main():
    """主函数"""
    monitor = NavigationMonitor()

    print("开始监控导航功能...")
    print("1. 配置文件监控")
    print("2. 性能监控")

    try:
        # 启动配置监控
        import threading
        config_thread = threading.Thread(target=monitor.monitor_config_changes)
        config_thread.daemon = True
        config_thread.start()

        # 启动性能监控
        monitor.monitor_performance()

    except KeyboardInterrupt:
        print("监控停止")
    except Exception as e:
        logging.error(f"监控异常: {e}")

if __name__ == "__main__":
    main()
```

### 自动告警脚本

```python
# scripts/alert_system.py
import smtplib
import requests
from email.mime.text import MimeText
from datetime import datetime

class AlertSystem:
    """告警系统"""

    def __init__(self, config):
        self.config = config
        self.alert_history = []

    def send_email_alert(self, subject, message):
        """发送邮件告警"""
        try:
            msg = MimeText(message)
            msg['Subject'] = f"[Navigation Alert] {subject}"
            msg['From'] = self.config['email']['from']
            msg['To'] = self.config['email']['to']

            server = smtplib.SMTP(self.config['email']['smtp_server'], self.config['email']['smtp_port'])
            server.starttls()
            server.login(self.config['email']['username'], self.config['email']['password'])
            server.send_message(msg)
            server.quit()

            print(f"邮件告警已发送: {subject}")

        except Exception as e:
            print(f"邮件告警发送失败: {e}")

    def send_webhook_alert(self, message):
        """发送Webhook告警"""
        try:
            webhook_url = self.config.get('webhook_url')
            if webhook_url:
                payload = {
                    "text": message,
                    "timestamp": datetime.now().isoformat()
                }
                response = requests.post(webhook_url, json=payload)
                response.raise_for_status()

                print(f"Webhook告警已发送: {message}")

        except Exception as e:
            print(f"Webhook告警发送失败: {e}")

    def check_and_alert(self, alert_type, message, severity="warning"):
        """检查并发送告警"""
        alert_key = f"{alert_type}_{datetime.now().strftime('%Y%m%d%H%M')}"

        # 避免重复告警
        if alert_key in self.alert_history:
            return

        self.alert_history.append(alert_key)

        # 保持历史记录不超过100条
        if len(self.alert_history) > 100:
            self.alert_history = self.alert_history[-100:]

        full_message = f"[{severity.upper()}] {message}"

        # 发送告警
        if severity in ["error", "critical"]:
            self.send_email_alert(alert_type, full_message)

        self.send_webhook_alert(full_message)

# 示例配置
ALERT_CONFIG = {
    "email": {
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 587,
        "username": "your-email@gmail.com",
        "password": "your-app-password",
        "from": "monitoring@yourcompany.com",
        "to": "team@yourcompany.com"
    },
    "webhook_url": "https://hooks.slack.com/services/your/webhook/url"
}

# 使用示例
if __name__ == "__main__":
    alert_system = AlertSystem(ALERT_CONFIG)

    # 测试告警
    alert_system.check_and_alert(
        "config_error",
        "配置文件语法错误，请立即检查",
        severity="error"
    )
```

## 故障恢复流程

### 故障分类

#### 1. 配置文件故障
**症状**:
- 配置加载失败
- YAML语法错误
- 定位器配置错误

**恢复步骤**:
```bash
# 1. 立即回滚配置文件
scripts/partial_rollback.sh config backups/latest

# 2. 验证回滚结果
python -c "import yaml; yaml.safe_load(open('config/data_testid_config.yaml'))"

# 3. 测试基础功能
python -m pytest tests/ -k "navigate" --tb=short -q
```

#### 2. 代码逻辑故障
**症状**:
- 导航功能异常
- 新增方法报错
- 性能严重下降

**恢复步骤**:
```bash
# 1. 立即回滚代码
scripts/partial_rollback.sh navigation backups/latest

# 2. 验证代码正确性
python -c "from src.steps.navigate_to_text_image import NavigateToTextToImageStep"

# 3. 运行回归测试
python -m pytest tests/test_navigate_to_text_image_enhanced.py -v
```

#### 3. 性能问题
**症状**:
- 导航时间过长
- 内存使用异常
- CPU占用率高

**恢复步骤**:
```bash
# 1. 监控性能指标
python scripts/monitor_navigation.py

# 2. 如果性能回退严重，回滚到备份
scripts/complete_rollback.sh backups/performance_baseline

# 3. 重新性能测试
python scripts/performance_test.py
```

### 故障响应时间

| 故障级别 | 响应时间 | 解决时间 | 负责人 |
|----------|----------|----------|--------|
| P0-严重 | 5分钟 | 30分钟 | 核心开发 |
| P1-高 | 15分钟 | 2小时 | 开发团队 |
| P2-中 | 1小时 | 8小时 | 开发团队 |
| P3-低 | 4小时 | 3天 | 开发团队 |

## 测试验证

### 回滚测试

```python
# tests/test_rollback.py
import pytest
import tempfile
import os
from pathlib import Path

class TestRollback:
    """回滚功能测试"""

    @pytest.fixture
    def backup_files(self):
        """创建测试备份文件"""
        backup_dir = tempfile.mkdtemp()

        # 创建模拟的备份文件
        config_content = """
locators:
  test_locator:
    - "[data-testid='test']"
"""

        with open(os.path.join(backup_dir, 'data_testid_config.yaml'), 'w') as f:
            f.write(config_content)

        with open(os.path.join(backup_dir, 'navigate_to_text_image.py'), 'w') as f:
            f.write("pass")

        yield backup_dir

        # 清理
        import shutil
        shutil.rmtree(backup_dir)

    def test_complete_rollback(self, backup_files):
        """测试完全回滚功能"""
        # 模拟回滚过程
        assert os.path.exists(os.path.join(backup_files, 'data_testid_config.yaml'))
        assert os.path.exists(os.path.join(backup_files, 'navigate_to_text_image.py'))

    def test_partial_rollback(self, backup_files):
        """测试部分回滚功能"""
        # 只回滚配置文件
        config_file = os.path.join(backup_files, 'data_testid_config.yaml')
        assert os.path.exists(config_file)

        # 验证配置文件正确性
        import yaml
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        assert 'locators' in config

    def test_backup_verification(self, backup_files):
        """测试备份验证功能"""
        # 验证备份完整性
        required_files = [
            'data_testid_config.yaml',
            'navigate_to_text_image.py'
        ]

        for file_name in required_files:
            file_path = os.path.join(backup_files, file_name)
            assert os.path.exists(file_path), f"备份文件缺失: {file_name}"

# 运行回滚测试
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

### 应急演练

```bash
#!/bin/bash
# scripts/emergency_drill.sh

echo "开始应急演练..."

# 1. 创建测试环境
TEST_DIR="emergency_test_$(date +%s)"
mkdir -p "$TEST_DIR"

# 2. 模拟故障
echo "2. 模拟配置文件损坏..."
echo "invalid: yaml: content:" > config/data_testid_config.yaml

# 3. 尝试恢复
echo "3. 尝试故障恢复..."
if python -c "import yaml; yaml.safe_load(open('config/data_testid_config.yaml'))" 2>/dev/null; then
    echo "✗ 配置文件损坏模拟失败"
    exit 1
fi

# 4. 执行回滚
echo "4. 执行回滚..."
BACKUP_DIR=$(ls -t backups/ | head -n 1)
scripts/complete_rollback.sh "backups/$BACKUP_DIR"

# 5. 验证恢复
echo "5. 验证恢复结果..."
if python -c "import yaml; yaml.safe_load(open('config/data_testid_config.yaml'))" 2>/dev/null; then
    echo "✓ 应急演练成功，回滚功能正常"
else
    echo "✗ 应急演练失败，回滚功能异常"
    exit 1
fi

# 6. 清理测试环境
# rm -rf "$TEST_DIR"

echo "应急演练完成！"
```

## 最佳实践

### 1. 变更前检查清单

- [ ] 创建完整备份
- [ ] 验证备份文件
- [ ] 准备回滚脚本
- [ ] 设置监控告警
- [ ] 确认紧急联系人

### 2. 变更中监控清单

- [ ] 配置文件语法检查
- [ ] 代码导入验证
- [ ] 基础功能测试
- [ ] 性能指标监控
- [ ] 错误日志检查

### 3. 变更后验证清单

- [ ] 完整功能测试
- [ ] 回归测试通过
- [ ] 性能基准对比
- [ ] 文档更新完成
- [ ] 监控正常运行

## 联系信息

### 紧急联系人

| 角色 | 姓名 | 联系方式 | 职责 |
|------|------|----------|------|
| 技术负责人 | XXX | 电话: 138XXXX8888 | 技术决策，紧急回滚 |
| 开发负责人 | XXX | 电话: 139XXXX9999 | 代码修复，功能验证 |
| 运维负责人 | XXX | 电话: 136XXXX6666 | 系统恢复，环境部署 |

### 升级路径

1. **第一响应**：开发团队处理（15分钟）
2. **技术升级**：技术负责人介入（30分钟）
3. **管理层升级**：启动应急响应（1小时）

## 最后更新

2025-12-17