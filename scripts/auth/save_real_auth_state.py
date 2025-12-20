#!/usr/bin/env python3
"""
100%正确的登录态保存方案
使用Playwright官方推荐的storageState
"""

import asyncio
import argparse
import json
import os
from pathlib import Path
import yaml
from playwright.async_api import async_playwright

async def save_real_auth_state():
    """使用Playwright官方方式保存完整登录态"""
    parser = argparse.ArgumentParser(description="保存 NowHi 真实登录态（storageState + sessionStorage）")
    parser.add_argument("--config", default="config/config.yaml", help="配置文件路径（用于读取 test.url）")
    parser.add_argument("--url", default=None, help="覆盖目标 URL（默认使用 config.test.url 或环境变量 TEST_URL）")
    parser.add_argument("--out-dir", default="scripts/auth", help="输出目录（默认：scripts/auth）")
    args = parser.parse_args()

    url = args.url or os.getenv("TEST_URL")
    if not url:
        cfg_path = Path(args.config)
        if cfg_path.exists():
            cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
            url = (cfg.get("test") or {}).get("url")
    if not url:
        raise RuntimeError("未提供 url，且无法从 config.test.url / TEST_URL 获取。")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    session_out = out_dir / "auth_session.json"
    storage_out = out_dir / "auth_state_real.json"

    async with async_playwright() as p:
        # 必须可视化来手动操作
        browser = await p.chromium.launch(headless=False)

        # 创建空context来准备
        context = await browser.new_context()
        page = await context.new_page()

        await page.goto(url)

        print("🎯 Playwright 官方登录态保存工具")
        print("=" * 60)
        print("👉 请在打开的浏览器中：")
        print("   1. 扫码登录或输入账号")
        print("   2. 点击'AI创作'菜单（关键！）")
        print("   3. 确认进入AI创作页面")
        print("   4. 看到功能列表后，按Enter键保存")
        print("=" * 60)

        # 等待用户完成登录
        input()

        # 导出 sessionStorage（你们的真实登录态：token + user_info）
        print("📦 正在导出 sessionStorage 登录态...")
        session_data = await page.evaluate("""() => ({
          token: sessionStorage.getItem('token'),
          user_info: sessionStorage.getItem('user_info'),
        })""")

        if not session_data or not session_data.get("token") or not session_data.get("user_info"):
            raise RuntimeError(
                "未获取到 sessionStorage.token / sessionStorage.user_info。"
                "请确认已完成登录且已进入需要登录的页面（建议进入 AI 创作页看到功能列表）后再保存。"
            )

        with open(session_out, "w", encoding="utf-8") as f:
            json.dump(session_data, f, ensure_ascii=False, indent=2)

        # 使用Playwright官方方法保存完整状态
        print("📸 正在保存完整登录态...")
        await context.storage_state(path=str(storage_out))

        print(f"✅ {storage_out} 已保存")
        print(f"✅ {session_out} 已保存（sessionStorage: token/user_info）")
        print("🔐 包含：")
        print("   - 所有cookies（包括httpOnly）")
        print("   - localStorage")
        print("   - sessionStorage")
        print("   - 完整的origin信息")
        print("")
        print("📌 现在你的auto-test-bot将：")
        print("   - 以真实登录用户身份运行")
        print("   - 能够看到AI创作等所有功能")
        print("   - 100%兼容Playwright格式")
        print("")
        print("📌 配置建议（config/config.yaml）：")
        print(f"   browser.storage_state: {storage_out}")
        print(f"   browser.session_state: {session_out}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(save_real_auth_state())
