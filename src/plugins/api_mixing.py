from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional

from core.plugins.base import AIGCPlugin, PluginResult
from core.protocol.scenario_context import ScenarioContext


class _ConfigError(RuntimeError):
    pass


class _PlaceholderAPIClient:
    def __init__(self, reason: str):
        self.call_count = 0
        self._reason = reason

    async def create_script(self, payload):
        raise _ConfigError(self._reason)

    async def create_episode(self, payload):
        raise _ConfigError(self._reason)

    async def create_character(self, payload):
        raise _ConfigError(self._reason)

    async def create_scene(self, payload):
        raise _ConfigError(self._reason)


class APIMixingPlugin(AIGCPlugin):
    """
    API 混合编排插件（Phase 2 MVP）：
    - 通过模板并行调用 api_client 的多个方法，合并结果到 ScenarioContext.test_data
    - 目前只实现最小模板 full_video_creation（与设计文档一致）
    """

    name = "api_mixing"
    capabilities = ["api.prepare"]

    def __init__(self, api_client: Any):
        self.api_client = api_client

    async def execute(self, context: ScenarioContext, params: Dict[str, Any]) -> PluginResult:
        template = params.get("template")
        if not isinstance(template, str) or not template.strip():
            return PluginResult(status="failed", error="template 必须是非空字符串")

        template = template.strip()
        if template == "full_video_creation":
            payloads = params.get("payloads") or {}
            if not isinstance(payloads, dict):
                return PluginResult(status="failed", error="payloads 必须是对象(dict)")
            data = await self._prepare_full_video_data(payloads)
            context.test_data.update(data)
            return PluginResult(status="completed", data=data, metrics={"api_calls": int(getattr(self.api_client, "call_count", 0))})

        return PluginResult(status="failed", error=f"unknown template: {template}")

    async def _prepare_full_video_data(self, payloads: Dict[str, Any]) -> Dict[str, Any]:
        script_payload = payloads.get("script") or {}
        episode_payload = payloads.get("episode") or {}
        character_payload = payloads.get("character") or {}
        scene_payload = payloads.get("scene") or {}

        tasks = [
            self.api_client.create_script(script_payload),
            self.api_client.create_episode(episode_payload),
            self.api_client.create_character(character_payload),
            self.api_client.create_scene(scene_payload),
        ]

        results = await asyncio.gather(*tasks)
        merged: Dict[str, Any] = {}
        for r in results:
            if isinstance(r, dict):
                merged.update(r)
            else:
                merged.setdefault("results", []).append(r)
        return merged


def create_plugin(config: dict, services: dict) -> APIMixingPlugin:
    """
    PluginManager 工厂入口：优先使用 services['api_client']，否则给出可诊断的占位客户端。
    """
    api_client = services.get("api_client")
    if api_client is None:
        api_client = _PlaceholderAPIClient("api_mixing 需要注入 api_client（例如 Naohai API Client）")
    return APIMixingPlugin(api_client=api_client)
