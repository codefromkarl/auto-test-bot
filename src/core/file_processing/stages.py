from __future__ import annotations

import hashlib
import os
from pathlib import Path
import shutil
from typing import Any, Dict, List

from .pipeline import ProcessingStage


class DownloadStage(ProcessingStage):
    def get_stage_name(self) -> str:
        return "download"

    async def process(self, file_info: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(file_info, dict):
            raise ValueError("file_info 必须是对象(dict)")

        cfg = context.get("config", {}) or {}
        base_temp_dir = Path(str(cfg.get("base_temp_dir") or "temp"))
        base_temp_dir.mkdir(parents=True, exist_ok=True)

        filename = file_info.get("filename") or "file.bin"
        local_path = file_info.get("local_path")
        content_bytes = file_info.get("content_bytes")
        source_path = file_info.get("source_path")

        if local_path:
            path = Path(str(local_path))
            if not path.exists():
                raise FileNotFoundError(f"local_path 不存在: {path}")
            resolved = str(path)
        else:
            path = base_temp_dir / str(filename)
            if content_bytes is not None:
                if not isinstance(content_bytes, (bytes, bytearray)):
                    raise ValueError("content_bytes 必须是 bytes")
                path.write_bytes(bytes(content_bytes))
            elif source_path is not None:
                src = Path(str(source_path))
                if not src.exists():
                    raise FileNotFoundError(f"source_path 不存在: {src}")
                shutil.copyfile(str(src), str(path))
            else:
                raise ValueError("file_info 需要提供 local_path/content_bytes/source_path 之一")
            resolved = str(path)

        size = os.path.getsize(resolved)
        context.setdefault("files", []).append({"local_path": resolved, "size": size, "filename": str(filename)})
        return {"local_path": resolved, "size": size, "filename": str(filename)}


class ValidationStage(ProcessingStage):
    def get_stage_name(self) -> str:
        return "validation"

    async def process(self, file_meta: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        cfg = context.get("config", {}) or {}
        rules = cfg.get("validation_rules", {}) or {}
        if not isinstance(rules, dict):
            raise ValueError("validation_rules 必须是对象(dict)")

        local_path = file_meta.get("local_path")
        if not local_path:
            raise ValueError("缺少 local_path")

        results: List[Dict[str, Any]] = []

        path = Path(str(local_path))
        if not path.exists():
            results.append({"type": "file_exists", "status": "failed", "message": f"File not found: {path}"})
            context["validation"] = {"validation_results": results, "is_valid": False}
            return file_meta

        if "size_equals" in rules:
            expected = int(rules["size_equals"])
            actual = path.stat().st_size
            if actual != expected:
                results.append(
                    {
                        "type": "size_equals",
                        "status": "failed",
                        "message": f"Size mismatch: expected={expected}, actual={actual}",
                    }
                )
            else:
                results.append({"type": "size_equals", "status": "passed", "message": "ok"})

        if "sha256" in rules:
            expected_hash = str(rules["sha256"])
            actual_hash = hashlib.sha256(path.read_bytes()).hexdigest()
            if actual_hash != expected_hash:
                results.append(
                    {"type": "sha256", "status": "failed", "message": "Checksum mismatch", "actual": actual_hash}
                )
            else:
                results.append({"type": "sha256", "status": "passed", "message": "ok"})

        is_valid = all(r.get("status") == "passed" for r in results) if results else True
        context["validation"] = {"validation_results": results, "is_valid": is_valid}
        return file_meta


class CleanupStage(ProcessingStage):
    def get_stage_name(self) -> str:
        return "cleanup"

    async def process(self, file_meta: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        cfg = context.get("config", {}) or {}
        keep_temp = bool(cfg.get("keep_temp", False))
        local_path = file_meta.get("local_path")
        if not local_path:
            return file_meta

        path = Path(str(local_path))
        if keep_temp:
            exists = path.exists()
            self._mark_exists(context, str(path), exists)
            return file_meta

        if path.exists():
            try:
                path.unlink()
            except Exception:
                pass

        self._mark_exists(context, str(path), path.exists())
        return file_meta

    def _mark_exists(self, context: Dict[str, Any], local_path: str, exists: bool) -> None:
        files = context.get("files", []) or []
        for entry in files:
            if entry.get("local_path") == local_path:
                entry["exists_after_cleanup"] = exists
                return

