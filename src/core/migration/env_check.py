from __future__ import annotations

import sys
from typing import Any, Dict, Tuple


def check_environment(*, min_python: Tuple[int, int] = (3, 8)) -> Dict[str, Any]:
    major, minor = min_python
    py_ok = (sys.version_info.major, sys.version_info.minor) >= (major, minor)
    report: Dict[str, Any] = {
        "python": {"ok": py_ok, "version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"},
    }

    # Optional: Playwright version if installed
    try:
        import playwright  # type: ignore

        report["playwright"] = {"ok": True, "version": getattr(playwright, "__version__", "unknown")}
    except Exception:
        report["playwright"] = {"ok": False, "version": "not_installed"}

    return report

