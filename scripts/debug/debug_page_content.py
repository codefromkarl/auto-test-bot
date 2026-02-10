#!/usr/bin/env python3
"""
调试页面内容和状态
实时访问目标网站并输出页面信息
"""

import asyncio
import logging
import sys
import os

# 添加src目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from browser import BrowserManager
from models.page_state import get_current_page_state, PageState

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def debug_page_content():
    """调试页面内容"""
    config = {
        'browser': {
            'headless': False,  # 显示浏览器窗口
            'timeout': 30000,
            'viewport': {'width': 1920, 'height': 1080}
        }
    }

    browser = BrowserManager(config)

    try:
        # 初始化浏览器
        await browser.initialize()
        logger.info("浏览器初始化成功")

        # 访问网站
        test_url = os.getenv("NOWHI_TEST_URL", "http://localhost:9020/nowhi/index.html#/home/dashboard")
        logger.info(f"正在访问: {test_url}")

        success = await browser.navigate_to(test_url)
        if not success:
            logger.error("无法访问网站")
            return

        # 等待页面加载
        await asyncio.sleep(3)

        # 获取页面基本信息
        url = await browser.get_page_url()
        title = await browser.get_page_title()
        logger.info(f"当前URL: {url}")
        logger.info(f"页面标题: {title}")

        # 检查页面状态
        current_state = await get_current_page_state(browser.page)
        logger.info(f"检测到的页面状态: {current_state.value}")

        # 检查关键元素
        logger.info("=== 检查首页特征元素 ===")

        # 检查NowHi文本
        nowhi_count = await browser.page.get_by_text("NowHi").count()
        logger.info(f"NowHi文本元素数量: {nowhi_count}")

        # 检查导航栏
        nav_count = await browser.page.locator("nav").count()
        logger.info(f"nav元素数量: {nav_count}")

        # 检查欢迎文本
        welcome_count = await browser.page.get_by_text("欢迎").count()
        logger.info(f"欢迎文本元素数量: {welcome_count}")

        # 获取页面主要内容
        logger.info("=== 页面主要内容 ===")

        # 获取所有文本内容（限制长度）
        try:
            body_text = await browser.page.evaluate("() => document.body.innerText")
            if body_text:
                # 只显示前500个字符
                preview = body_text[:500] + "..." if len(body_text) > 500 else body_text
                logger.info(f"页面文本预览:\n{preview}")
        except Exception as e:
            logger.error(f"获取页面文本失败: {e}")

        # 检查页面结构
        logger.info("=== 页面结构分析 ===")

        try:
            # 检查是否有主要的布局元素
            header_count = await browser.page.locator("header").count()
            main_count = await browser.page.locator("main").count()
            footer_count = await browser.page.locator("footer").count()

            logger.info(f"header元素数量: {header_count}")
            logger.info(f"main元素数量: {main_count}")
            logger.info(f"footer元素数量: {footer_count}")

            # 检查常见的类名
            common_classes = ["dashboard", "home", "container", "content", "app"]
            for class_name in common_classes:
                elements = await browser.page.locator(f"[class*='{class_name}']").count()
                if elements > 0:
                    logger.info(f"包含'{class_name}'的元素数量: {elements}")

        except Exception as e:
            logger.error(f"分析页面结构失败: {e}")

        # 检查JavaScript状态
        logger.info("=== JavaScript状态检查 ===")

        try:
            ready_state = await browser.evaluate_javascript("document.readyState")
            logger.info(f"文档就绪状态: {ready_state}")

            # 检查是否有JavaScript错误
            js_errors = await browser.evaluate_javascript("""
                if (window.errorCount !== undefined) {
                    return window.errorCount;
                }
                return 0;
            """)
            logger.info(f"JavaScript错误数量: {js_errors}")

        except Exception as e:
            logger.error(f"JavaScript状态检查失败: {e}")

        # 等待用户确认（可选）
        input("按Enter键继续...")

    except Exception as e:
        logger.error(f"调试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # 清理资源
        await browser.close()
        logger.info("浏览器已关闭")

if __name__ == "__main__":
    asyncio.run(debug_page_content())
