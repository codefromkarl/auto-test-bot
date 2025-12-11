"""
日志配置和管理
"""

import logging
import logging.handlers
import os
from typing import Dict, Any


class ColoredFormatter(logging.Formatter):
    """彩色日志格式化器"""

    # ANSI 颜色代码
    COLORS = {
        'DEBUG': '\033[36m',      # 青色
        'INFO': '\033[32m',       # 绿色
        'WARNING': '\033[33m',    # 黄色
        'ERROR': '\033[31m',      # 红色
        'CRITICAL': '\033[35m',   # 紫色
        'RESET': '\033[0m'        # 重置
    }

    def format(self, record):
        """格式化日志记录"""
        # 添加颜色
        if record.levelname in self.COLORS:
            record.levelname = (
                f"{self.COLORS[record.levelname]}{record.levelname}"
                f"{self.COLORS['RESET']}"
            )

        return super().format(record)


def setup_logging(config: Dict[str, Any]):
    """
    设置日志配置

    Args:
        config: 日志配置字典
    """
    # 获取配置参数
    level = config.get('level', 'INFO').upper()
    format_str = config.get(
        'format',
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_path = config.get('file_path', 'logs/test_bot.log')
    max_file_size = config.get('max_file_size', 10) * 1024 * 1024  # MB to bytes
    backup_count = config.get('backup_count', 5)
    console_output = config.get('console_output', True)

    # 确保日志目录存在
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    # 获取根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level))

    # 清除现有处理器
    root_logger.handlers.clear()

    # 创建格式化器
    plain_formatter = logging.Formatter(format_str)
    colored_formatter = ColoredFormatter(format_str)

    # 文件处理器（带轮转）
    file_handler = logging.handlers.RotatingFileHandler(
        file_path,
        maxBytes=max_file_size,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(getattr(logging, level))
    file_handler.setFormatter(plain_formatter)
    root_logger.addHandler(file_handler)

    # 控制台处理器
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, level))
        console_handler.setFormatter(colored_formatter)
        root_logger.addHandler(console_handler)

    # 设置第三方库的日志级别
    logging.getLogger('playwright').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    获取指定名称的日志记录器

    Args:
        name: 日志记录器名称

    Returns:
        logging.Logger: 日志记录器实例
    """
    return logging.getLogger(name)


class TestLogger:
    """测试专用日志记录器"""

    def __init__(self, test_name: str = "auto_test"):
        """
        初始化测试日志记录器

        Args:
            test_name: 测试名称
        """
        self.test_name = test_name
        self.logger = logging.getLogger(f"test.{test_name}")
        self.step_counter = 0

    def start_test(self, description: str):
        """
        开始测试

        Args:
            description: 测试描述
        """
        self.logger.info(f"🚀 开始测试: {description}")

    def start_step(self, step_name: str):
        """
        开始测试步骤

        Args:
            step_name: 步骤名称
        """
        self.step_counter += 1
        self.logger.info(f"📍 步骤 {self.step_counter}: {step_name}")

    def step_success(self, step_name: str, details: str = ""):
        """
        步骤成功

        Args:
            step_name: 步骤名称
            details: 详细信息
        """
        message = f"✅ 步骤成功: {step_name}"
        if details:
            message += f" - {details}"
        self.logger.info(message)

    def step_failure(self, step_name: str, error: str):
        """
        步骤失败

        Args:
            step_name: 步骤名称
            error: 错误信息
        """
        self.logger.error(f"❌ 步骤失败: {step_name} - {error}")

    def step_warning(self, step_name: str, warning: str):
        """
        步骤警告

        Args:
            step_name: 步骤名称
            warning: 警告信息
        """
        self.logger.warning(f"⚠️  步骤警告: {step_name} - {warning}")

    def end_test(self, success: bool, details: str = ""):
        """
        结束测试

        Args:
            success: 测试是否成功
            details: 详细信息
        """
        if success:
            message = f"🎉 测试完成: {self.test_name}"
            if details:
                message += f" - {details}"
            self.logger.info(message)
        else:
            message = f"💥 测试失败: {self.test_name}"
            if details:
                message += f" - {details}"
            self.logger.error(message)

    def log_info(self, message: str):
        """记录信息"""
        self.logger.info(f"ℹ️  {message}")

    def log_error(self, message: str):
        """记录错误"""
        self.logger.error(f"🔥 {message}")

    def log_warning(self, message: str):
        """记录警告"""
        self.logger.warning(f"⚠️  {message}")

    def log_debug(self, message: str):
        """记录调试信息"""
        self.logger.debug(f"🔍 {message}")


def create_test_logger(test_name: str) -> TestLogger:
    """
    创建测试日志记录器

    Args:
        test_name: 测试名称

    Returns:
        TestLogger: 测试日志记录器实例
    """
    return TestLogger(test_name)