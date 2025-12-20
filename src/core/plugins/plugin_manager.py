from __future__ import annotations

import asyncio
import importlib.util
import inspect
from pathlib import Path
from types import ModuleType
from typing import Any, Callable, Dict, List, Optional, Union
from uuid import uuid4

from core.protocol.scenario_context import ScenarioContext

from .base import AIGCPlugin, PluginResult


class PluginLoadError(RuntimeError):
    pass


class PluginManager:
    """插件管理器：负责加载、执行、卸载插件。"""

    def __init__(self, plugin_dir: Union[Path, str]):
        self.plugin_dir = Path(str(plugin_dir))
        self._plugins: Dict[str, AIGCPlugin] = {}
        self._load_order: List[str] = []

    async def load_plugins(
        self,
        enabled_modules: Optional[List[str]] = None,
        plugin_configs: Optional[Dict[str, Dict[str, Any]]] = None,
        services: Optional[Dict[str, Any]] = None,
    ) -> None:
        if not self.plugin_dir.exists():
            raise PluginLoadError(f"插件目录不存在: {self.plugin_dir}")
        if not self.plugin_dir.is_dir():
            raise PluginLoadError(f"插件目录不是文件夹: {self.plugin_dir}")

        plugin_configs = plugin_configs or {}
        services = services or {}

        enabled_set = None
        if enabled_modules is not None:
            enabled_set = {str(m).strip() for m in enabled_modules if isinstance(m, str) and str(m).strip()}

        modules = self._discover_modules(self.plugin_dir, enabled_set)
        discovered: List[AIGCPlugin] = []
        for mod_path in modules:
            module = self._load_module_from_path(mod_path)
            discovered.extend(self._instantiate_plugins_from_module(module, mod_path.stem, plugin_configs, services))

        by_name: Dict[str, AIGCPlugin] = {}
        for plugin in discovered:
            if not plugin.name or not isinstance(plugin.name, str):
                raise PluginLoadError("插件必须定义非空 name")
            if plugin.name in by_name:
                raise PluginLoadError(f"插件 name 重复: {plugin.name}")
            by_name[plugin.name] = plugin

        self._validate_dependencies(by_name)
        order = self._toposort(by_name)

        self._plugins = by_name
        self._load_order = order

        for name in order:
            await self._plugins[name].setup()

    async def unload_plugins(self) -> None:
        for name in reversed(self._load_order):
            plugin = self._plugins.get(name)
            if plugin is None:
                continue
            try:
                await plugin.cleanup()
            except Exception:
                continue
        self._plugins.clear()
        self._load_order.clear()

    def get_plugin(self, name: str) -> Optional[AIGCPlugin]:
        return self._plugins.get(name)

    def list_plugins(self) -> Dict[str, Dict[str, Any]]:
        return {
            name: {
                "capabilities": list(getattr(plugin, "capabilities", []) or []),
                "healthy": bool(plugin.health_check()),
                "dependencies": list(getattr(plugin, "dependencies", []) or []),
            }
            for name, plugin in self._plugins.items()
        }

    async def execute_plugin(self, name: str, context: ScenarioContext, params: Dict[str, Any]) -> PluginResult:
        plugin = self.get_plugin(name)
        if not plugin:
            raise KeyError(f"插件不存在: {name}")
        result = plugin.execute(context, params)
        if asyncio.iscoroutine(result):
            return await result
        # 理论上 execute 应该是 async，但为了容错允许返回非 coroutine
        return result  # type: ignore[return-value]

    def _discover_modules(self, plugin_dir: Path, enabled_set: Optional[set]) -> List[Path]:
        paths: List[Path] = []
        for path in sorted(plugin_dir.glob("*.py")):
            if path.name.startswith("_") or path.name == "__init__.py":
                continue
            if enabled_set is not None and path.stem not in enabled_set:
                continue
            paths.append(path)
        return paths

    def _load_module_from_path(self, path: Path) -> ModuleType:
        module_name = f"dynamic_plugins.{path.stem}.{uuid4().hex}"
        spec = importlib.util.spec_from_file_location(module_name, str(path))
        if spec is None or spec.loader is None:
            raise PluginLoadError(f"无法加载插件模块: {path}")
        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)  # type: ignore[union-attr]
        except Exception as exc:
            raise PluginLoadError(f"加载插件模块失败: {path}: {exc}") from exc
        return module

    def _instantiate_plugins_from_module(
        self,
        module: ModuleType,
        module_key: str,
        plugin_configs: Dict[str, Dict[str, Any]],
        services: Dict[str, Any],
    ) -> List[AIGCPlugin]:
        plugins: List[AIGCPlugin] = []

        # Prefer module-level factory if present: create_plugin(config, services) -> AIGCPlugin
        factory = getattr(module, "create_plugin", None)
        if callable(factory):
            try:
                cfg = plugin_configs.get(module_key, {}) or {}
                instance = factory(cfg, services)
            except Exception as exc:
                raise PluginLoadError(f"create_plugin 失败: {module_key}: {exc}") from exc
            if not isinstance(instance, AIGCPlugin):
                raise PluginLoadError(f"create_plugin 必须返回 AIGCPlugin: {module_key}")
            return [instance]

        for _, obj in vars(module).items():
            if not inspect.isclass(obj):
                continue
            if obj is AIGCPlugin:
                continue
            if not issubclass(obj, AIGCPlugin):
                continue
            try:
                plugins.append(obj())  # type: ignore[call-arg]
            except Exception as exc:
                raise PluginLoadError(f"实例化插件失败: {obj}: {exc}") from exc
        return plugins

    def _validate_dependencies(self, plugins: Dict[str, AIGCPlugin]) -> None:
        for name, plugin in plugins.items():
            deps = list(getattr(plugin, "dependencies", []) or [])
            missing = [d for d in deps if d not in plugins]
            if missing:
                raise PluginLoadError(f"插件 {name} 依赖缺失: {missing}")

    def _toposort(self, plugins: Dict[str, AIGCPlugin]) -> List[str]:
        remaining: Dict[str, List[str]] = {
            name: list(getattr(plugin, "dependencies", []) or []) for name, plugin in plugins.items()
        }
        order: List[str] = []
        while remaining:
            ready = sorted([name for name, deps in remaining.items() if not deps])
            if not ready:
                cycle = ", ".join(sorted(remaining.keys()))
                raise PluginLoadError(f"插件依赖存在环: {cycle}")
            for name in ready:
                order.append(name)
                remaining.pop(name, None)
                for deps in remaining.values():
                    if name in deps:
                        deps.remove(name)
        return order
