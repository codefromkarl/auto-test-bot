"""
导航到 AI创作 页（旧流程兼容）
"""

from typing import Any, Dict, Optional

from src.models.page_state import PageState, get_current_page_state


class NavigateToAICreateStep:
    def __init__(self, browser: Any, config: Optional[Dict[str, Any]] = None):
        self.browser = browser
        self.config = config or {}

    async def _verify_ai_create_page(self) -> bool:
        page = getattr(self.browser, "page", None)
        if page is None:
            return False
        state = await get_current_page_state(page)
        return state == PageState.AI_CREATE

    async def execute(self) -> Dict[str, Any]:
        # 登录校验（如果浏览器实现该方法）
        if hasattr(self.browser, "assert_logged_in"):
            ok, _, message = await self.browser.assert_logged_in()
            if not ok:
                return {"success": False, "error": message, "page_state": "UNKNOWN"}

        page = getattr(self.browser, "page", None)
        if page is None:
            return {"success": False, "error": "page not initialized", "page_state": "UNKNOWN"}

        state = await get_current_page_state(page)
        # 幂等：已在 AI_CREATE 直接成功返回
        if state == PageState.AI_CREATE:
            ok = await self._verify_ai_create_page()
            return {"success": bool(ok), "page_state": PageState.AI_CREATE.value}

        # 尝试点击导航（best-effort）
        try:
            if hasattr(page, "click"):
                await page.click('.nav-routerTo-item:has-text(\"AI创作\")', timeout=10000)
        except Exception:
            pass

        ok = await self._verify_ai_create_page()
        return {"success": bool(ok), "page_state": PageState.AI_CREATE.value if ok else "UNKNOWN"}

