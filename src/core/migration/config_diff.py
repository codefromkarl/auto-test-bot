from __future__ import annotations

from typing import Any, Dict, List


def diff_dicts(a: Any, b: Any, *, _path: str = "") -> List[Dict[str, Any]]:
    """
    递归对比两个结构（dict/list/标量），输出最小差异列表。
    """
    diffs: List[Dict[str, Any]] = []

    def join(path: str, key: str) -> str:
        return f"{path}.{key}" if path else key

    if isinstance(a, dict) and isinstance(b, dict):
        a_keys = set(a.keys())
        b_keys = set(b.keys())
        for k in sorted(a_keys - b_keys):
            diffs.append({"type": "removed", "path": join(_path, str(k)), "before": a.get(k)})
        for k in sorted(b_keys - a_keys):
            diffs.append({"type": "added", "path": join(_path, str(k)), "after": b.get(k)})
        for k in sorted(a_keys & b_keys):
            diffs.extend(diff_dicts(a.get(k), b.get(k), _path=join(_path, str(k))))
        return diffs

    if isinstance(a, list) and isinstance(b, list):
        if a != b:
            diffs.append({"type": "changed", "path": _path, "before": a, "after": b})
        return diffs

    if a != b:
        diffs.append({"type": "changed", "path": _path, "before": a, "after": b})
    return diffs

