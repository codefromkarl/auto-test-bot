#!/usr/bin/env python3
"""
环境验证脚本 - 测试前检查环境就绪状态
"""

import sys
import requests
import time
from pathlib import Path

def check_environment():
    """检查测试环境是否就绪"""
    issues = []

    # 检查网站可达性
    try:
        response = requests.get('http://115.29.232.120/nowhi/index.html', timeout=10)
        if response.status_code == 200:
            print("✅ 网站可达性检查通过")
        else:
            issues.append(f"网站响应异常: {response.status_code}")
    except requests.exceptions.RequestException as e:
        issues.append(f"网络连接失败: {e}")

    # 检查依赖
    try:
        import playwright
        print("✅ Playwright依赖检查通过")
    except ImportError:
        issues.append("Playwright未安装：pip install playwright")

    # 检查配置文件
    config_files = [
        'config/config.yaml',
        'config/mcp_config.yaml'
    ]
    for config_file in config_files:
        if not Path(config_file).exists():
            issues.append(f"配置文件缺失: {config_file}")

    if issues:
        print("\n❌ 环境检查发现问题：")
        for issue in issues:
            print(f"  - {issue}")
        return False

    print("\n✅ 环境检查通过，可以开始测试")
    return True

if __name__ == "__main__":
    if not check_environment():
        sys.exit(1)