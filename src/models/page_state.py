"""
页面状态管理模块
定义页面状态枚举和识别函数
"""

from enum import Enum
from typing import Optional
from urllib.parse import urlsplit
from playwright.async_api import Page


class PageState(Enum):
    """页面状态枚举"""
    HOME = "HOME"                    # 首页 / 营销页
    AI_CREATE = "AI_CREATE"            # AI创作总览页
    TEXT_TO_IMAGE = "TEXT_TO_IMAGE"    # 文生图页
    IMAGE_TO_VIDEO = "IMAGE_TO_VIDEO"   # 图生视频页
    UNKNOWN = "UNKNOWN"                # 未知页面


async def is_home_page(page: Page) -> bool:
    """
    判断是否为首页

    Args:
        page: Playwright页面对象

    Returns:
        bool: 是否为首页
    """
    try:
        url = page.url
        parsed = urlsplit(url)
        fragment = parsed.fragment or ""

        # 优先用路由片段判断：避免仅因包含 index.html 就误判为 HOME
        # 例如：index.html#/ai-create/index/story-list 不是首页
        if fragment.startswith("/home") or fragment.startswith("/dashboard"):
            # 明确的首页路由，直接判定为 HOME（避免页面特征尚未渲染时误判 UNKNOWN）
            return True
        url_match = fragment in ("", "/")

        # 不是 HOME 路由时，如果明显是其他业务路由，直接判定非首页（防止特征元素误导）
        non_home_prefixes = ("/ai-create", "/ai/", "/create", "/work", "/tutorial", "/more")
        if fragment.startswith(non_home_prefixes):
            return False

        # 检查页面特征元素（作为兜底）
        found_elements = 0

        try:
            # 检查NowHi logo（多种可能的文本）
            nowhi_variants = ["NowHi", "nowhi", "NOWHI"]
            logo = False
            for variant in nowhi_variants:
                if await page.get_by_text(variant).count() > 0:
                    logo = True
                    break
            if logo:
                found_elements += 1
        except:
            pass

        try:
            # 检查导航栏（包括可能的变体）
            nav_selectors = ["nav", ".nav", ".navigation", "[role='navigation']"]
            nav = False
            for selector in nav_selectors:
                if await page.locator(selector).count() > 0:
                    nav = True
                    break
            if nav:
                found_elements += 1
        except:
            pass

        try:
            # 检查首页特有的欢迎文案
            welcome_variants = ["欢迎", "Welcome", "dashboard", "首页"]
            welcome_text = False
            for variant in welcome_variants:
                if await page.get_by_text(variant).count() > 0:
                    welcome_text = True
                    break
            if welcome_text:
                found_elements += 1
        except:
            pass

        try:
            # 检查是否有主要内容区域
            main_content = await page.locator("main").count() > 0 or \
                           await page.locator(".main").count() > 0 or \
                           await page.locator(".content").count() > 0
            if main_content:
                found_elements += 1
        except:
            pass

        # HOME 路由（fragment 为空或根）：要求至少找到 1 个特征元素，防止空白页/错误页误判
        if url_match:
            return found_elements >= 1

        # 非 HOME 路由：不再仅凭通用特征元素误判为首页
        return False

    except Exception:
        return False


async def get_current_page_state(page: Page) -> PageState:
    """
    获取当前页面状态

    Args:
        page: Playwright页面对象

    Returns:
        PageState: 当前页面状态
    """
    # 按优先级检查页面状态
    if await is_home_page(page):
        return PageState.HOME
    elif await is_ai_create_page(page):
        return PageState.AI_CREATE
    elif await is_text_to_image_page(page):
        return PageState.TEXT_TO_IMAGE
    elif await is_image_to_video_page(page):
        return PageState.IMAGE_TO_VIDEO
    else:
        return PageState.UNKNOWN


def get_page_state_info(state: PageState) -> dict:
    """
    获取页面状态信息

    Args:
        state: 页面状态

    Returns:
        dict: 页面状态信息
    """
    info_map = {
        PageState.HOME: {
            "name": "首页",
            "description": "网站首页/营销页面",
            "expected_url_patterns": ["#/home/dashboard", "#/", "/home", "/dashboard"],
            "key_elements": ["NowHi", "导航栏", "欢迎文案"]
        },
        PageState.AI_CREATE: {
            "name": "AI创作页",
            "description": "AI功能总览页面",
            "expected_url_patterns": ["#/ai/create", "/ai-create", "create"],
            "key_elements": ["AI创作标题", "功能卡片", "文生图入口"]
        },
        PageState.TEXT_TO_IMAGE: {
            "name": "文生图页",
            "description": "文本生成图片功能页面",
            "expected_url_patterns": ["#/ai/text-image", "/text-to-image", "text-image"],
            "key_elements": ["文生图标题", "提示词输入框", "生成图片按钮"]
        },
        PageState.IMAGE_TO_VIDEO: {
            "name": "图生视频页",
            "description": "图片生成视频功能页面",
            "expected_url_patterns": ["#/ai/image-video", "/image-to-video", "image-video"],
            "key_elements": ["图生视频标题", "图片上传区域", "生成视频按钮"]
        },
        PageState.UNKNOWN: {
            "name": "未知页面",
            "description": "无法识别的页面状态",
            "expected_url_patterns": [],
            "key_elements": []
        }
    }

    return info_map.get(state, info_map[PageState.UNKNOWN])


# 页面状态转换规则
VALID_TRANSITIONS = {
    PageState.HOME: [PageState.AI_CREATE],
    PageState.AI_CREATE: [PageState.TEXT_TO_IMAGE, PageState.IMAGE_TO_VIDEO],
    PageState.TEXT_TO_IMAGE: [PageState.AI_CREATE],  # 可以返回
    PageState.IMAGE_TO_VIDEO: [PageState.AI_CREATE],  # 可以返回
    PageState.UNKNOWN: []  # 未知状态不能转换
}


def is_valid_transition(from_state: PageState, to_state: PageState) -> bool:
    """
    检查页面状态转换是否有效

    Args:
        from_state: 源页面状态
        to_state: 目标页面状态

    Returns:
        bool: 转换是否有效
    """
    return to_state in VALID_TRANSITIONS.get(from_state, [])


class PreconditionError(Exception):
    """页面前置条件错误"""
    def __init__(self, message: str, current_state: PageState, expected_state: PageState):
        self.message = message
        self.current_state = current_state
        self.expected_state = expected_state
        super().__init__(self.message)


# 简化版的识别函数
async def is_ai_create_page(page: Page) -> bool:
    """判断是否为AI创作总览页"""
    try:
        url = page.url
        # 实际路由形态可能为：#/ai-create/index/...
        url_patterns = ["#/ai-create", "#/ai/create", "/ai-create"]
        url_match = any(pattern in url for pattern in url_patterns)

        # 检查页面特征元素
        try:
            ai_title = await page.get_by_text("AI创作").count() > 0
        except:
            ai_title = False

        try:
            story_flow = await page.get_by_text("剧本列表").count() > 0
        except:
            story_flow = False

        try:
            cards = await page.locator("[class*='card']").count() >= 2
        except:
            cards = False

        try:
            text_to_image = await page.get_by_text("文生图").count() > 0
        except:
            text_to_image = False

        return url_match and (ai_title or story_flow or cards or text_to_image)
    except Exception:
        return False


async def is_text_to_image_page(page: Page) -> bool:
    """判断是否为文生图页面"""
    try:
        url = page.url
        url_patterns = ["#/ai/text-image", "/text-to-image", "text-image"]
        url_match = any(pattern in url for pattern in url_patterns)

        # 检查页面特征元素
        try:
            title = await page.get_by_text("文生图").count() > 0
        except:
            title = False

        try:
            prompt_input = await page.get_by_placeholder("提示词", exact=True).count() > 0
            if not prompt_input:
                # 尝试其他可能的placeholder
                prompt_input = await page.get_by_placeholder("请输入", exact=True).count() > 0
        except:
            prompt_input = False

        try:
            generate_btn = await page.get_by_role("button", name="生成图片").count() > 0
        except:
            generate_btn = False

        # 真实站点路由可能调整（例如从“AI工具”入口进入），此时仅依赖 url_match 会误判 UNKNOWN。
        # 若已出现强特征（提示词输入框 + 生成按钮），则视为文生图页。
        strong_signal = prompt_input and generate_btn
        return (url_match and (title or prompt_input or generate_btn)) or strong_signal
    except Exception:
        return False


async def is_image_to_video_page(page: Page) -> bool:
    """判断是否为图生视频页面"""
    try:
        url = page.url
        url_patterns = ["#/ai/image-video", "/image-to-video", "image-video"]
        url_match = any(pattern in url for pattern in url_patterns)

        # 检查页面特征元素
        try:
            title = await page.get_by_text("图生视频").count() > 0
        except:
            title = False

        try:
            upload_area = await page.get_by_text("上传图片").count() > 0
        except:
            upload_area = False

        try:
            generate_btn = await page.get_by_role("button", name="生成视频").count() > 0
        except:
            generate_btn = False

        return url_match and (title or upload_area or generate_btn)
    except Exception:
        return False
