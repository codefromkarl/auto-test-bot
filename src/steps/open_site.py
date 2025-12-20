"""
网站打开步骤（旧流程兼容）
"""

from typing import Any, Dict, Optional

from models.page_state import PageState, get_current_page_state


class OpenSiteStep:
    def __init__(self, browser: Any, config: Optional[Dict[str, Any]] = None):
        self.browser = browser
        self.config = config or {}

    async def _verify_page_elements(self) -> bool:
        """
        旧流程的页面校验：允许落在 HOME 或 AI_CREATE（新版站点可能直接路由到 AI_CREATE）。
        """
        page = getattr(self.browser, "page", None)
        if page is None:
            return False

        state = await get_current_page_state(page)
        return state in (PageState.HOME, PageState.AI_CREATE)

