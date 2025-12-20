#!/usr/bin/env python3
"""
Inspect NowHi page elements to help stabilize selectors.

Purpose:
- Collect inspectable evidence (tag/class/role/attrs/bbox/text) for key tabs/buttons.
- Avoid guessing selectors when remote UI changes.
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


async def _collect_matches(page, text: str) -> List[Dict[str, Any]]:
    locator = page.locator(f'text={text}')
    count = await locator.count()
    matches: List[Dict[str, Any]] = []
    for i in range(min(count, 20)):
        el = locator.nth(i)
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
    ariaSelected: node.getAttribute('aria-selected'),
    ariaCurrent: node.getAttribute('aria-current'),
    href: node.getAttribute('href'),
    attrs,
    bbox: { x: rect.x, y: rect.y, w: rect.width, h: rect.height },
    text: (node.innerText || node.textContent || '').trim().slice(0, 200),
  };
}"""
            )
            matches.append(info)
        except Exception as e:
            matches.append({"error": str(e)})
    return matches


async def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect NowHi tab/button selectors")
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

    # Navigate
    test_url = os.getenv("TEST_URL") or cfg.get("test", {}).get("url")
    await browser.navigate_to(test_url, timeout=cfg.get("test", {}).get("page_load_timeout", 120000))
    await browser.wait_for_selector("body", state="visible", timeout=cfg.get("test", {}).get("element_timeout", 30000))

    # Login status evidence
    login_status = await browser.get_login_status()

    # Try enter AI creation (best-effort, collect evidence even if already there)
    await click_first(['.nav-routerTo-item:has-text("AI创作")', 'text=AI创作'], timeout_ms=30000)
    await browser.wait_for_selector("text=剧本列表", state="visible", timeout=60000)

    # Click first story card to open detail
    await browser.wait_for_selector("div.list-item:not(.add-item)", state="visible", timeout=60000)
    await click_first(["div.list-item:not(.add-item)"], timeout_ms=30000)

    # Switch to storyboard management (best-effort) to collect page-specific selectors
    await click_first(['.step-item:has-text("分镜管理")', '.step-text:has-text("分镜管理")', 'text=分镜管理'], timeout_ms=30000)

    # Collect evidence for key texts
    targets = ["剧本详情", "分镜管理", "视频编辑", "视频创作", "新增分镜", "新增分集", "分集", "角色", "场景"]
    data: Dict[str, Any] = {
        "timestamp": datetime.now().isoformat(),
        "url": await browser.get_page_url(),
        "login_status": login_status,
        "targets": {},
    }
    for t in targets:
        data["targets"][t] = await _collect_matches(page, t)

    # Also collect candidate tab containers
    tab_like_selectors = [
        ".tab",
        ".tab-item",
        ".tabs",
        ".step",
        ".step-item",
        ".process",
        ".process-item",
        "[role=tab]",
        "[role=tablist]",
    ]
    containers: Dict[str, Any] = {}
    for sel in tab_like_selectors:
        try:
            count = await page.locator(sel).count()
            containers[sel] = int(count)
        except Exception as e:
            containers[sel] = {"error": str(e)}
    data["container_counts"] = containers

    # Save artifacts
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = out_dir / f"nowhi_tabs_{stamp}.json"
    out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    await browser.take_screenshot(str(out_dir / f"nowhi_tabs_{stamp}.png"), timeout=60000, full_page=False)

    print(str(out_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
