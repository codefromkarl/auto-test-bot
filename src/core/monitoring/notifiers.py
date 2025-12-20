from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


class AlertNotifier:
    def send(self, alerts: List[Dict[str, Any]]) -> None:
        raise NotImplementedError


class FileAlertNotifier(AlertNotifier):
    """
    最小落盘告警：JSONL 追加写，用于 CI/本地留痕与后续集成。
    """

    def __init__(self, *, path: str):
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def send(self, alerts: List[Dict[str, Any]]) -> None:
        if not alerts:
            return
        with self._path.open("a", encoding="utf-8") as f:
            for alert in alerts:
                f.write(json.dumps(alert, ensure_ascii=False) + "\n")


class WebhookAlertNotifier(AlertNotifier):
    """
    Webhook 告警：在运行环境启用；单测不触网。
    """

    def __init__(self, *, url: str, timeout_seconds: float = 3.0, headers: Optional[Dict[str, str]] = None):
        self._url = url
        self._timeout = timeout_seconds
        self._headers = headers or {"Content-Type": "application/json"}

    def send(self, alerts: List[Dict[str, Any]]) -> None:
        if not alerts:
            return
        import requests

        requests.post(self._url, json={"alerts": alerts}, timeout=self._timeout, headers=self._headers)

