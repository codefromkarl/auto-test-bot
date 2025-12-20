#!/usr/bin/env python3
"""
Inspect NowHi video editor page to stabilize "generate video" E2E selectors.

Collects:
- URL + login status
- Key elements for "视频编辑" page
- Candidate buttons with text containing "生成/开始/制作"
- Candidate video/result elements
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# Ensure project root is importable
PROJECT_ROOT = Path(__file__).resolve().parents[2]
import sys
src_path = str(PROJECT_ROOT / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)
root_path = str(PROJECT_ROOT)
if root_path not in sys.path:
    sys.path.insert(1, root_path)

from utils import ConfigLoader, setup_logging
from browser import BrowserManager


async def _collect_elements(page, selector: str, limit: int = 30) -> List[Dict[str, Any]]:
    loc = page.locator(selector)
    count = await loc.count()
    out: List[Dict[str, Any]] = []
    for i in range(min(int(count), int(limit))):
        el = loc.nth(i)
        try:
            info = await el.evaluate(
                """(node) => {
  const rect = node.getBoundingClientRect();
  const attrs = {};
  for (const a of node.attributes || []) attrs[a.name] = a.value;
  return {
    tag: node.tagName,
    id: node.id || null,
    className: node.className || null,
    role: node.getAttribute('role'),
    disabled: node.disabled === true ? true : null,
    attrs,
    bbox: { x: rect.x, y: rect.y, w: rect.width, h: rect.height },
    text: (node.innerText || node.textContent || '').trim().slice(0, 200),
  };
}"""
            )
            out.append(info)
        except Exception as e:
            out.append({"error": str(e)})
    return out


async def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect NowHi video editor selectors")
    parser.add_argument("--config", default="config/e2e_remote_workflow_config.yaml", help="配置文件路径")
    parser.add_argument("--output-dir", default="test_artifacts/selector_inspect", help="输出目录")
    parser.add_argument("--url", default=None, help="覆盖目标 URL（默认使用 config.test.url 或 TEST_URL）")
    args = parser.parse_args()

    cfg = ConfigLoader(args.config).load_config()
    setup_logging(cfg.get("logging", {}))

    if args.url:
        os.environ["TEST_URL"] = args.url

    browser = BrowserManager(cfg)
    ok = await browser.initialize()
    if not ok:
        raise RuntimeError("浏览器初始化失败")

    page = browser.page
    assert page is not None

    async def click_first(selectors: List[str], timeout_ms: int = 30000) -> bool:
        for sel in selectors:
            try:
                await page.locator(sel).first.click(timeout=timeout_ms)
                return True
            except Exception:
                continue
        return False

    # Navigate to story list (prefer config.test.url / TEST_URL which may already include hash route)
    test_url = os.getenv("TEST_URL") or cfg.get("test", {}).get("url")
    await browser.navigate_to(test_url, timeout=cfg.get("test", {}).get("page_load_timeout", 120000))
    await browser.wait_for_selector("body", state="visible", timeout=cfg.get("test", {}).get("element_timeout", 30000))

    login_status = await browser.get_login_status()

    # Ensure story list visible (route may already be story-list)
    await browser.wait_for_selector("text=剧本列表", state="visible", timeout=60000)

    # Open first story card
    await browser.wait_for_selector("div.list-item:not(.add-item)", state="visible", timeout=60000)
    await click_first(["div.list-item:not(.add-item)"], timeout_ms=30000)

    # Enter video editor directly from story detail (current UI top steps)
    await click_first(
        ['.step-item:has-text("视频编辑")', '.step-text:has-text("视频编辑")', 'text=视频编辑'],
        timeout_ms=30000,
    )

    # Collect evidence
    data: Dict[str, Any] = {
        "timestamp": datetime.now().isoformat(),
        "url": await browser.get_page_url(),
        "login_status": login_status,
    }

    data["counts"] = {}
    for sel in ["video", "button", "input", "textarea", ".step-item", ".step-text"]:
        try:
            data["counts"][sel] = int(await page.locator(sel).count())
        except Exception as e:
            data["counts"][sel] = {"error": str(e)}

    # Candidate buttons: any element that looks clickable and contains target keywords
    keywords = ["生成", "开始", "制作", "提交", "确认"]
    candidates: Dict[str, Any] = {}
    for kw in keywords:
        candidates[kw] = await _collect_elements(
            page,
            f'button:has-text("{kw}"), [role=button]:has-text("{kw}"), a:has-text("{kw}")',
            limit=40,
        )
    data["button_candidates"] = candidates

    # Candidate result areas
    data["video_candidates"] = await _collect_elements(page, "video, .result-video, .video-item, .video-fragment", limit=40)
    data["page_markers"] = await _collect_elements(page, ".video-editor, .video-creation-page, .editor, .creation", limit=20)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_json = out_dir / f"nowhi_video_editor_{stamp}.json"
    out_png = out_dir / f"nowhi_video_editor_{stamp}.png"
    out_json.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    await browser.take_screenshot(str(out_png), timeout=60000, full_page=False)

    print(str(out_json))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
