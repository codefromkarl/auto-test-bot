#!/usr/bin/env python3
"""
调试导航元素
"""

import asyncio
import logging
import sys
import os

# 添加src目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from browser import BrowserManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def debug_navigation():
    """调试页面导航元素"""
    config = {
        'browser': {
            'headless': False,
            'timeout': 30000,
            'viewport': {'width': 1920, 'height': 1080}
        }
    }

    browser = BrowserManager(config)

    try:
        await browser.initialize()
        logger.info("浏览器初始化成功")

        # 加载登录状态
        auth_state_file = "auth_state.json"
        if os.path.exists(auth_state_file):
            logger.info("加载登录状态")
        else:
            logger.info("未找到登录状态文件，使用空状态")

        test_url = "http://115.29.232.120/nowhi/index.html#/home/dashboard"
        logger.info(f"正在访问: {test_url}")

        success = await browser.navigate_to(test_url)
        if not success:
            logger.error("无法访问网站")
            return

        await asyncio.sleep(5)

        # 获取页面文本内容
        try:
            page_text = await browser.page.evaluate("() => document.body.innerText")
            if page_text:
                logger.info("=== 页面完整文本 ===")
                lines = page_text.split('\n')
                for i, line in enumerate(lines[:20]):  # 只显示前20行
                    logger.info(f"{i+1:2}: {line}")
        except Exception as e:
            logger.error(f"获取页面文本失败: {e}")

        # 搜索所有可能的导航文本
        navigation_texts = [
            "AI创作", "创作", "AI工具", "工具",
            "generate", "create", "ai", "AI",
            "文生图", "图生视频", "text-image", "image-video"
        ]

        logger.info("=== 搜索导航文本 ===")
        for text in navigation_texts:
            try:
                count = await browser.page.get_by_text(text).count()
                if count > 0:
                    logger.info(f"✅ 找到 '{text}': {count}个")
            except Exception as e:
                logger.debug(f"搜索 '{text}' 失败: {e}")

        # 检查所有可点击的元素
        logger.info("=== 检查可点击元素 ===")

        # 检查所有按钮
        buttons = await browser.page.locator("button").count()
        logger.info(f"按钮元素数量: {buttons}")

        # 检查所有链接
        links = await browser.page.locator("a").count()
        logger.info(f"链接元素数量: {links}")

        # 检查包含"AI"或"创作"的元素
        ai_elements = await browser.page.locator("[class*='ai'], [class*='create'], [class*='tool']").count()
        logger.info(f"包含AI/创作/工具的元素: {ai_elements}")

        # 等待用户确认
        input("按Enter键继续...")

    except Exception as e:
        logger.error(f"调试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await browser.close()
        logger.info("浏览器已关闭")

if __name__ == "__main__":
    asyncio.run(debug_navigation())