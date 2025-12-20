#!/usr/bin/env python3
"""
详细调试页面内容
"""

import asyncio
import logging
import sys
import os

# 添加src目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from browser import BrowserManager

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def debug_page_detailed():
    """详细调试页面内容"""
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

        test_url = "http://115.29.232.120/nowhi/index.html#/home/dashboard"
        logger.info(f"正在访问: {test_url}")

        success = await browser.navigate_to(test_url)
        if not success:
            logger.error("无法访问网站")
            return

        await asyncio.sleep(5)  # 等待页面完全加载

        # 获取页面基本信息
        url = await browser.get_page_url()
        title = await browser.get_page_title()
        logger.info(f"当前URL: {url}")
        logger.info(f"页面标题: {title}")

        # 获取页面所有文本
        logger.info("=== 页面完整文本内容 ===")
        try:
            body_text = await browser.page.evaluate("() => document.body.innerText")
            if body_text:
                print(f"\n页面文本内容（前1000字符）:\n{body_text[:1000]}\n")

                # 搜索关键词
                keywords = ["NowHi", "nowhi", "欢迎", "Welcome", "dashboard", "首页", "导航", "nav"]
                found_keywords = []
                for keyword in keywords:
                    if keyword.lower() in body_text.lower():
                        found_keywords.append(keyword)

                logger.info(f"找到的关键词: {found_keywords}")
            else:
                logger.warning("页面文本为空")
        except Exception as e:
            logger.error(f"获取页面文本失败: {e}")

        # 获取页面HTML结构
        logger.info("=== 页面HTML结构分析 ===")
        try:
            # 检查各种可能的元素
            elements_to_check = [
                ("NowHi文本", "text=NowHi"),
                ("nowhi文本", "text=nowhi"),
                ("欢迎文本", "text=欢迎"),
                ("Welcome文本", "text=Welcome"),
                ("dashboard文本", "text=dashboard"),
                ("首页文本", "text=首页"),
                ("nav元素", "nav"),
                (".nav元素", ".nav"),
                (".navigation元素", ".navigation"),
                ("[role='navigation']", "[role='navigation']"),
                ("header元素", "header"),
                (".header元素", ".header"),
                ("main元素", "main"),
                (".main元素", ".main"),
                (".content元素", ".content"),
                (".container元素", ".container")
            ]

            for element_name, selector in elements_to_check:
                try:
                    count = await browser.page.locator(selector).count()
                    if count > 0:
                        logger.info(f"✅ {element_name}: {count} 个")
                        # 获取第一个元素的文本
                        if selector.startswith("text="):
                            text = await browser.page.get_by_text(selector.replace("text=", "")).first.text_content()
                            logger.info(f"   文本内容: {text[:100] if text else '空'}")
                        else:
                            text = await browser.page.locator(selector).first.text_content()
                            logger.info(f"   文本内容: {text[:100] if text else '空'}")
                    else:
                        logger.info(f"❌ {element_name}: 0 个")
                except Exception as e:
                    logger.info(f"⚠️ {element_name}: 检查失败 - {e}")

        except Exception as e:
            logger.error(f"分析HTML结构失败: {e}")

        # 获取所有class名称
        logger.info("=== 页面class名称 ===")
        try:
            class_names = await browser.page.evaluate("""
                () => {
                    const elements = document.querySelectorAll('[class]');
                    const classes = new Set();
                    elements.forEach(el => {
                        el.className.split(' ').forEach(cls => {
                            if(cls.trim()) classes.add(cls.trim());
                        });
                    });
                    return Array.from(classes).sort();
                }
            """)

            # 显示相关的class名称
            relevant_classes = [cls for cls in class_names if any(keyword in cls.lower() for keyword in
                               ['nav', 'header', 'main', 'content', 'container', 'dashboard', 'home', 'nowhi'])]

            logger.info(f"相关的class名称: {relevant_classes}")
            logger.info(f"所有class名称数量: {len(class_names)}")

        except Exception as e:
            logger.error(f"获取class名称失败: {e}")

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
    asyncio.run(debug_page_detailed())