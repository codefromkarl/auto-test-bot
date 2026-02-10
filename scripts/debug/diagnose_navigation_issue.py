#!/usr/bin/env python3
"""
诊断导航问题的详细分析工具
"""

import asyncio
import logging
import sys
import os

# 添加src目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from browser import BrowserManager
from models.page_state import get_current_page_state, PageState

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def diagnose_navigation_issue():
    """详细诊断导航问题"""
    config = {
        'browser': {
            'headless': False,
            'timeout': 60000,  # 增加超时到1分钟
            'viewport': {'width': 1920, 'height': 1080}
        }
    }

    browser = BrowserManager(config)

    try:
        await browser.initialize()
        logger.info("浏览器初始化成功")

        # 加载登录态
        auth_state_files = ["auth_state_real.json", "auth_state.json"]
        auth_state_file = None
        for file in auth_state_files:
            if os.path.exists(file):
                auth_state_file = file
                break

        if auth_state_file:
            logger.info(f"加载登录状态: {auth_state_file}")

        test_url = os.getenv("NOWHI_TEST_URL", "http://localhost:9020/nowhi/index.html")
        logger.info(f"正在访问基础URL: {test_url}")

        # 先访问基础页面，不加hash
        success = await browser.navigate_to(test_url)
        if not success:
            logger.error("无法访问基础页面")
            return

        await asyncio.sleep(5)  # 等待页面完全加载

        # 获取页面状态
        current_state = await get_current_page_state(browser.page)
        logger.info(f"当前页面状态: {current_state.value}")

        # 检查页面基本信息
        url = await browser.get_page_url()
        title = await browser.get_page_title()
        logger.info(f"当前URL: {url}")
        logger.info(f"页面标题: {title}")

        # 检查DOM元素数量
        dom_count = await browser.page.evaluate("() => document.querySelectorAll('*').length")
        logger.info(f"DOM元素总数: {dom_count}")

        # 检查是否有"AI创作"相关的元素
        navigation_texts = ["AI创作", "创作", "AI工具", "工具", "文生图", "图生视频", "功能"]

        logger.info("=== 检查导航元素 ===")
        for text in navigation_texts:
            try:
                count = await browser.page.get_by_text(text).count()
                if count > 0:
                    logger.info(f"✅ 找到 '{text}': {count}个")

                    # 获取元素的详细信息
                    element = await browser.page.get_by_text(text).first
                    try:
                        tag_name = await element.evaluate("el => el.tagName.toLowerCase()")
                        class_name = await element.evaluate("el => el.className")
                        logger.info(f"   标签: {tag_name}, 类名: {class_name}")
                    except:
                        pass
            except Exception as e:
                logger.debug(f"检查 '{text}' 失败: {e}")

        # 检查所有链接
        links = await browser.page.locator("a").count()
        logger.info(f"链接元素总数: {links}")

        # 检查按钮元素
        buttons = await browser.page.locator("button").count()
        logger.info(f"按钮元素总数: {buttons}")

        # 检查路由相关
        try:
            router_info = await browser.page.evaluate("""
                () => {
                    // 检查是否有路由相关的元素
                    const routerElements = document.querySelectorAll('[class*="router"], [class*="route"], [class*="nav"], [class*="menu"], [class*="sidebar"]');
                    return {
                        routerCount: routerElements.length,
                        routerTags: Array.from(routerElements).map(el => el.tagName),
                        routerClasses: Array.from(routerElements).map(el => el.className)
                    };
                }
            """)
            logger.info(f"路由相关元素: {router_info}")
        except Exception as e:
            logger.error(f"检查路由信息失败: {e}")

        # 检查JavaScript状态
        try:
            js_status = await browser.page.evaluate("""
                () => {
                    return {
                        readyState: document.readyState,
                        hasJQuery: typeof jQuery !== 'undefined',
                        hasVue: typeof Vue !== 'undefined',
                        hasReact: typeof React !== 'undefined',
                        urlHash: window.location.hash,
                        historyLength: window.history.length
                    };
                }
            """)
            logger.info(f"JavaScript状态: {js_status}")
        except Exception as e:
            logger.error(f"检查JS状态失败: {e}")

        # 等待用户手动检查
        logger.info("=" * 60)
        logger.info("🔍 请在浏览器中检查：")
        logger.info("1. 页面是否完全加载")
        logger.info("2. 能否看到'AI创作'或其他导航元素")
        logger.info("3. 如果是，请点击进入后按Enter继续")
        logger.info("4. 如果不是，请直接按Enter结束")
        logger.info("=" * 60)

        user_input = input()

        if user_input.strip().lower() in ['y', 'yes', '是']:
            logger.info("用户确认页面正常，继续测试...")
            # 现在尝试导航到AI创作页面
            await browser.page.wait_for_timeout(2000)  # 等待2秒

            # 尝试通过JavaScript导航
            try:
                nav_result = await browser.page.evaluate("""
                    () => {
                        // 尝试点击导航元素
                        const aiCreateLink = Array.from(document.querySelectorAll('a, button, [onclick], [class*="nav"], [class*="menu"]'))
                            .find(el => el.textContent.includes('AI') || el.textContent.includes('创作') || el.textContent.includes('工具'));

                        if (aiCreateLink) {
                            aiCreateLink.click();
                            return { success: true, element: aiCreateLink.textContent };
                        }

                        return { success: false, message: '未找到导航元素' };
                    }
                """)

                logger.info(f"JavaScript导航结果: {nav_result}")

                if nav_result.get('success'):
                    logger.info("✅ JavaScript导航成功!")
                    await asyncio.sleep(3)  # 等待页面切换

                    # 检查新页面状态
                    new_state = await get_current_page_state(browser.page)
                    new_url = await browser.get_page_url()
                    logger.info(f"新页面状态: {new_state.value}")
                    logger.info(f"新URL: {new_url}")
                else:
                    logger.error(f"JavaScript导航失败: {nav_result.get('message')}")

            except Exception as e:
                logger.error(f"JavaScript导航异常: {e}")

        else:
            logger.info("用户确认页面有问题，结束诊断")

    except Exception as e:
        logger.error(f"诊断过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await browser.close()
        logger.info("浏览器已关闭")

if __name__ == "__main__":
    asyncio.run(diagnose_navigation_issue())
