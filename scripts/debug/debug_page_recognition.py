#!/usr/bin/env python3
"""页面识别调试脚本"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
src_path = str(Path(__file__).parent / 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from browser import BrowserManager
from models.page_state import get_current_page_state, PageState


async def debug_page_recognition():
    """调试页面识别功能"""
    print("🔍 调试页面识别功能...")

    config = {
        'browser': {
            'type': 'chromium',
            'headless': True
        }
    }

    browser = BrowserManager(config)
    await browser.initialize()

    try:
        print("\n📍 访问测试页面...")
        test_url = os.getenv("NOWHI_TEST_URL", "http://localhost:9020/nowhi/index.html#/home/dashboard")
        await browser.navigate_to(test_url)

        # 等待页面加载
        await asyncio.sleep(5)

        print("\n🔍 调试页面状态识别...")

        # 获取页面基本信息
        title = await browser.page.title()
        url = await browser.get_page_url()
        print(f"页面标题: {title}")
        print(f"页面URL: {url}")

        # 调试首页识别
        from models.page_state import is_home_page
        is_home = await is_home_page(browser.page)
        print(f"是否首页: {is_home}")

        # 调试AI创作页识别
        from models.page_state import is_ai_create_page
        is_ai_create = await is_ai_create_page(browser.page)
        print(f"是否AI创作页: {is_ai_create}")

        # 调试文生图页识别
        from models.page_state import is_text_to_image_page
        is_text_image = await is_text_to_image_page(browser.page)
        print(f"是否文生图页: {is_text_image}")

        # 综合判断
        current_state = await get_current_page_state(browser.page)
        print(f"综合判断结果: {current_state.value}")

        # 获取页面的一些元素信息
        print("\n🔍 调试页面元素:")

        # 查找可能的logo
        try:
            logos = await browser.page.get_by_text("NowHi").count()
            print(f"NowHi文本数量: {logos}")
        except:
            print("NowHi文本查找失败")

        # 查找导航元素
        try:
            navs = await browser.page.locator("nav").count()
            print(f"nav元素数量: {navs}")
        except:
            print("nav元素查找失败")

        # 查找所有文本
        try:
            body_text = await browser.page.locator("body").text_content()
            print(f"页面文本长度: {len(body_text)}")
            print(f"页面文本预览: {body_text[:300]}...")
        except:
            print("页面文本获取失败")

    except Exception as e:
        print(f"调试过程出现异常: {str(e)}")
        import traceback
        traceback.print_exc()

    finally:
        await browser.close()


if __name__ == "__main__":
    asyncio.run(debug_page_recognition())
