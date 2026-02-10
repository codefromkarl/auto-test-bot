#!/usr/bin/env python3
import asyncio
import logging
import sys
import os

# 添加src目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
src_path = os.path.join(project_root, "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from src.browser import BrowserManager
from src.models.page_state import get_current_page_state, PageState

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_page_state_simple():
    config = {
        "browser": {
            "headless": True,
            "timeout": 30000,
            "viewport": {"width": 1920, "height": 1080},
        }
    }

    browser = BrowserManager(config)

    try:
        await browser.initialize()
        logger.info("浏览器初始化成功")

        test_url = os.getenv(
            "NOWHI_TEST_URL",
            "http://localhost:9020/nowhi/index.html#/home/dashboard",
        )
        logger.info(f"正在访问: {test_url}")

        success = await browser.navigate_to(test_url)
        if not success:
            logger.error("无法访问网站")
            return

        await asyncio.sleep(3)

        url = await browser.get_page_url()
        logger.info(f"当前URL: {url}")

        current_state = await get_current_page_state(browser.page)
        logger.info(f"检测到的页面状态: {current_state.value}")

        # 手动测试各种元素
        logger.info("=== 手动测试元素 ===")

        nowhi_count = await browser.page.get_by_text("NowHi").count()
        logger.info(f"NowHi文本: {nowhi_count}")

        home_count = await browser.page.get_by_text("首页").count()
        logger.info(f"首页文本: {home_count}")

        main_count = await browser.page.locator("main").count()
        logger.info(f"main元素: {main_count}")

        content_count = await browser.page.locator(".content").count()
        logger.info(f".content元素: {content_count}")

    except Exception as e:
        logger.error(f"测试过程中出现错误: {e}")
        import traceback

        traceback.print_exc()

    finally:
        await browser.close()
        logger.info("浏览器已关闭")


if __name__ == "__main__":
    asyncio.run(test_page_state_simple())
