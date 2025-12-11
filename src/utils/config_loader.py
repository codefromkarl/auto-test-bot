"""
配置加载器
负责加载和验证配置文件
"""

import os
import yaml
import logging
from typing import Dict, Any, Optional


class ConfigLoader:
    """配置加载器"""

    def __init__(self, config_path: str = "config/config.yaml"):
        """
        初始化配置加载器

        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self.logger = logging.getLogger(__name__)
        self._config: Optional[Dict[str, Any]] = None

    def load_config(self) -> Dict[str, Any]:
        """
        加载配置文件

        Returns:
            Dict[str, Any]: 配置字典
        """
        try:
            if not os.path.exists(self.config_path):
                raise FileNotFoundError(f"配置文件不存在: {self.config_path}")

            with open(self.config_path, 'r', encoding='utf-8') as file:
                self._config = yaml.safe_load(file)

            # 验证配置
            self._validate_config()

            self.logger.info(f"配置文件加载成功: {self.config_path}")
            return self._config

        except yaml.YAMLError as e:
            self.logger.error(f"配置文件格式错误: {str(e)}")
            raise

        except Exception as e:
            self.logger.error(f"加载配置文件失败: {str(e)}")
            raise

    def _validate_config(self):
        """验证配置文件格式和必需字段"""
        if not isinstance(self._config, dict):
            raise ValueError("配置文件格式错误：根节点必须是字典")

        # 验证必需的顶级配置
        required_sections = ['test', 'browser', 'logging']
        for section in required_sections:
            if section not in self._config:
                raise ValueError(f"缺少必需的配置段: {section}")

        # 验证测试配置
        test_config = self._config.get('test', {})
        if 'url' not in test_config:
            raise ValueError("测试配置缺少 URL")

        if 'selectors' not in test_config:
            raise ValueError("测试配置缺少选择器配置")

        # 验证选择器配置
        selectors = test_config['selectors']
        required_selectors = [
            'prompt_input',
            'generate_image_button',
            'generate_video_button',
            'image_result',
            'video_result'
        ]

        for selector_name in required_selectors:
            if selector_name not in selectors:
                raise ValueError(f"缺少必需的选择器配置: {selector_name}")

            selector_list = selectors[selector_name]
            if not isinstance(selector_list, list) or len(selector_list) == 0:
                raise ValueError(f"选择器配置格式错误: {selector_name}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值

        Args:
            key: 配置键，支持点号分隔的嵌套键
            default: 默认值

        Returns:
            Any: 配置值
        """
        if not self._config:
            raise RuntimeError("配置尚未加载，请先调用 load_config()")

        keys = key.split('.')
        value = self._config

        try:
            for k in keys:
                value = value[k]
            return value

        except (KeyError, TypeError):
            return default

    def get_test_config(self) -> Dict[str, Any]:
        """获取测试配置"""
        return self.get('test', {})

    def get_browser_config(self) -> Dict[str, Any]:
        """获取浏览器配置"""
        return self.get('browser', {})

    def get_logging_config(self) -> Dict[str, Any]:
        """获取日志配置"""
        return self.get('logging', {})

    def get_mcp_config(self) -> Dict[str, Any]:
        """获取 MCP 配置"""
        return self.get('mcp', {})

    def get_retry_config(self) -> Dict[str, Any]:
        """获取重试配置"""
        return self.get('retry', {})

    def get_steps_config(self) -> Dict[str, Any]:
        """获取步骤配置"""
        return self.get('steps', {})

    def get_selectors(self) -> Dict[str, Any]:
        """获取选择器配置"""
        return self.get('test.selectors', {})

    def get_timeout(self, timeout_type: str = 'default') -> int:
        """
        获取超时配置

        Args:
            timeout_type: 超时类型 (default, element, page_load)

        Returns:
            int: 超时时间（毫秒）
        """
        timeout_key = f'test.timeout'
        if timeout_type != 'default':
            timeout_key = f'test.{timeout_type}_timeout'

        return self.get(timeout_key, 30000)

    def reload_config(self) -> Dict[str, Any]:
        """重新加载配置文件"""
        self._config = None
        return self.load_config()


class MCPConfigLoader:
    """MCP 配置加载器"""

    def __init__(self, config_path: str = "config/mcp_config.yaml"):
        """
        初始化 MCP 配置加载器

        Args:
            config_path: MCP 配置文件路径
        """
        self.config_path = config_path
        self.logger = logging.getLogger(__name__)
        self._config: Optional[Dict[str, Any]] = None

    def load_config(self) -> Dict[str, Any]:
        """
        加载 MCP 配置文件

        Returns:
            Dict[str, Any]: MCP 配置字典
        """
        try:
            if not os.path.exists(self.config_path):
                self.logger.warning(f"MCP 配置文件不存在: {self.config_path}")
                return self._get_default_config()

            with open(self.config_path, 'r', encoding='utf-8') as file:
                self._config = yaml.safe_load(file)

            # 验证配置
            self._validate_config()

            self.logger.info(f"MCP 配置文件加载成功: {self.config_path}")
            return self._config

        except yaml.YAMLError as e:
            self.logger.error(f"MCP 配置文件格式错误: {str(e)}")
            return self._get_default_config()

        except Exception as e:
            self.logger.error(f"加载 MCP 配置文件失败: {str(e)}")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认 MCP 配置"""
        return {
            'mcp_server': {
                'host': 'localhost',
                'port': 3000,
                'auth_token': '',
                'connection_timeout': 10000,
                'heartbeat_interval': 30,
                'max_reconnect_attempts': 5,
                'reconnect_delay': 5
            },
            'tools': {
                'console_messages': {'enabled': True},
                'network_requests': {'enabled': True},
                'performance_tracing': {'enabled': True},
                'dom_debug': {'enabled': True},
                'page_snapshots': {'enabled': True},
                'javascript_execution': {'enabled': True}
            },
            'data_storage': {
                'root_dir': 'mcp_data',
                'console_logs': {'enabled': True, 'retention_days': 7},
                'network_logs': {'enabled': True, 'retention_days': 7},
                'performance_traces': {'enabled': True, 'retention_days': 3},
                'dom_snapshots': {'enabled': True, 'retention_days': 1}
            },
            'monitoring': {
                'enabled': True,
                'thresholds': {
                    'page_load_time': 5000,
                    'api_response_time': 3000,
                    'js_error_count': 10,
                    'network_failure_rate': 5
                }
            },
            'logging': {
                'level': 'INFO',
                'file_path': 'logs/mcp_server.log'
            }
        }

    def _validate_config(self):
        """验证 MCP 配置文件格式"""
        if not isinstance(self._config, dict):
            raise ValueError("MCP 配置文件格式错误：根节点必须是字典")

        # 验证必需的配置段
        required_sections = ['mcp_server', 'tools']
        for section in required_sections:
            if section not in self._config:
                raise ValueError(f"MCP 配置缺少必需的配置段: {section}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取 MCP 配置值

        Args:
            key: 配置键，支持点号分隔的嵌套键
            default: 默认值

        Returns:
            Any: 配置值
        """
        if not self._config:
            self._config = self.load_config()

        keys = key.split('.')
        value = self._config

        try:
            for k in keys:
                value = value[k]
            return value

        except (KeyError, TypeError):
            return default

    def is_enabled(self) -> bool:
        """检查 MCP 是否启用"""
        return self.get('mcp_server.enabled', True)