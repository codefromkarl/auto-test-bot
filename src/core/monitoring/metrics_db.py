from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional


@dataclass
class MetricRecord:
    domain: str
    timestamp: str
    data: Dict[str, Any]


class MetricsDB:
    """
    最小 MetricsDB（Phase 3 MVP）：
    - 内存存储
    - 可选 JSONL 持久化（追加写；启动时回放）
    """

    def __init__(self, persist_path: Optional[str] = None):
        self._lock = Lock()
        self._records_by_domain: Dict[str, List[MetricRecord]] = {}
        self._persist_path = Path(persist_path) if persist_path else None

        if self._persist_path:
            self._persist_path.parent.mkdir(parents=True, exist_ok=True)
            if self._persist_path.exists():
                self._load_from_jsonl(self._persist_path)

    def record(self, domain: str, data: Dict[str, Any], timestamp: Optional[str] = None) -> None:
        if not isinstance(domain, str) or not domain.strip():
            raise ValueError("domain 必须是非空字符串")
        if not isinstance(data, dict):
            raise ValueError("data 必须是对象(dict)")

        ts = timestamp or datetime.now().isoformat()
        rec = MetricRecord(domain=domain, timestamp=ts, data=dict(data))

        with self._lock:
            self._records_by_domain.setdefault(domain, []).append(rec)
            if self._persist_path:
                self._append_jsonl(self._persist_path, rec)

    def query(self, domain: str) -> List[Dict[str, Any]]:
        with self._lock:
            records = list(self._records_by_domain.get(domain, []))
        return [{"domain": r.domain, "timestamp": r.timestamp, "data": dict(r.data)} for r in records]

    def count_event_type(self, domain: str, event_type: str) -> int:
        if not isinstance(event_type, str) or not event_type.strip():
            return 0
        with self._lock:
            records = self._records_by_domain.get(domain, [])
            return sum(1 for r in records if str(r.data.get("event_type") or "") == event_type)

    def _append_jsonl(self, path: Path, rec: MetricRecord) -> None:
        payload = {"domain": rec.domain, "timestamp": rec.timestamp, "data": rec.data}
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")

    def _load_from_jsonl(self, path: Path) -> None:
        try:
            text = path.read_text(encoding="utf-8")
        except Exception:
            return
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except Exception:
                continue
            if not isinstance(payload, dict):
                continue
            domain = payload.get("domain")
            timestamp = payload.get("timestamp")
            data = payload.get("data")
            if not isinstance(domain, str) or not isinstance(timestamp, str) or not isinstance(data, dict):
                continue
            rec = MetricRecord(domain=domain, timestamp=timestamp, data=data)
            self._records_by_domain.setdefault(domain, []).append(rec)

