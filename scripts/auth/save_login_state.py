#!/usr/bin/env python3
"""
保存登录状态 - 一次性操作
"""

import asyncio
import os
from playwright.async_api import async_playwright

async def save_login_state():
    """手动登录并保存状态"""
    async with async_playwright() as p:
        # 必须使用有界面模式来手动操作
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        # 访问页面（可通过 NOWHI_TEST_URL 覆盖）
        target_url = os.getenv("NOWHI_TEST_URL", "http://localhost:9020/nowhi/index.html")
        await page.goto(target_url)

        print("🎯 登录状态保存工具")
        print("=" * 50)
        print("👉 请在打开的浏览器中完成以下步骤：")
        print("   1. 扫码或输入账号登录")
        print("   2. 确认能看到 'AI创作' 菜单项")
        print("   3. 登录成功后，回到这里按Enter键")
        print("=" * 50)

        # 等待用户操作
        input()

        # 保存登录状态
        await context.storage_state(path="auth_state.json")

        print("✅ 登录状态已保存到 auth_state.json")
        print("🔐 此文件包含你的登录态，后续测试将自动使用")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(save_login_state())
