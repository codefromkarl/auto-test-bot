"""
浏览器管理模块
负责 Playwright 浏览器的初始化、配置和基本操作（WorkflowExecutor 依赖该接口）
"""

from __future__ import annotations

import json
import logging
import os
import time
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

from playwright.async_api import async_playwright, Browser, BrowserContext, Page


class BrowserManager:
    """浏览器管理器（Workflow-First 执行器依赖）"""

    def __init__(self, config: Dict[str, Any]):
        self.full_config = config or {}
        self.config = (self.full_config.get("browser", {}) or {}) if isinstance(self.full_config, dict) else {}
        self.logger = logging.getLogger("browser")

        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

        self.session_state_path: Optional[str] = None
        self.storage_state_path: Optional[str] = None

        # 认证问题（例如 token 过期）会导致 UI 无法继续加载，从而出现长时间等待/卡住。
        # 通过监听网络响应提前识别并快速失败，给出可操作的修复指引。
        self._auth_issue: Optional[Dict[str, Any]] = None
        self._auth_session_mtime: Optional[float] = None

    def get_auth_issue(self) -> Optional[Dict[str, Any]]:
        return self._auth_issue

    def clear_auth_issue(self) -> None:
        self._auth_issue = None

    async def initialize(self) -> bool:
        try:
            self.logger.info("正在初始化浏览器...")

            self.playwright = await async_playwright().start()

            browser_type = (self.config.get("type") or "chromium").lower()
            if browser_type == "chromium":
                browser_launcher = self.playwright.chromium
            elif browser_type == "firefox":
                browser_launcher = self.playwright.firefox
            elif browser_type == "webkit":
                browser_launcher = self.playwright.webkit
            else:
                self.logger.error(f"不支持的浏览器类型: {browser_type}")
                return False

            def _env_bool(name: str) -> Optional[bool]:
                raw = os.getenv(name)
                if raw is None:
                    return None
                v = str(raw).strip().lower()
                if v in ("1", "true", "yes", "y", "on"):
                    return True
                if v in ("0", "false", "no", "n", "off"):
                    return False
                return None

            headless = self.config.get("headless", True)
            env_headless = _env_bool("BROWSER_HEADLESS")
            if env_headless is not None:
                headless = env_headless

            launch_options: Dict[str, Any] = {
                "headless": bool(headless),
                "args": self.config.get("launch_args", []) or [],
            }
            slow_mo = os.getenv("BROWSER_SLOW_MO", self.config.get("slow_mo"))
            if slow_mo is not None:
                launch_options["slow_mo"] = int(slow_mo)

            self.browser = await browser_launcher.launch(**launch_options)

            context_options: Dict[str, Any] = {
                "viewport": self.config.get("viewport", {"width": 1920, "height": 1080}),
                "user_agent": self.config.get("user_agent", "AutoTestBot/1.0 (Playwright)"),
                "ignore_https_errors": bool(self.config.get("ignore_https_errors", True)),
                "java_script_enabled": True,
                "accept_downloads": False,
            }

            storage_state_path = self.config.get("storage_state")
            if isinstance(storage_state_path, str) and storage_state_path and os.path.exists(storage_state_path):
                context_options["storage_state"] = storage_state_path
                self.storage_state_path = storage_state_path

            self.context = await self.browser.new_context(**context_options)

            # sessionStorage 注入（token/user_info）
            await self._inject_session_state()

            self.page = await self.context.new_page()

            default_timeout = int(self.config.get("default_timeout", self.full_config.get("test", {}).get("timeout", 30000)))
            self.page.set_default_timeout(default_timeout)

            # 监听网络响应，捕获 token 过期等认证问题（如 code=50008）。
            self._install_auth_response_watchers()

            self.logger.info(f"浏览器初始化成功: {browser_type}")
            return True
        except Exception as e:
            self.logger.error(f"浏览器初始化失败: {e}")
            return False

    async def _inject_session_state(self) -> bool:
        if not self.context:
            return False

        session_path = self.config.get("session_state")
        if not isinstance(session_path, str) or not session_path or not os.path.exists(session_path):
            return False

        try:
            raw = json.load(open(session_path, "r", encoding="utf-8"))
        except Exception as e:
            self.logger.warning(f"读取 session_state 失败，跳过注入: {e}")
            return False

        token = raw.get("token")
        user_info = raw.get("user_info")
        if isinstance(user_info, dict):
            user_info = json.dumps(user_info, ensure_ascii=False)

        payload = {"token": token, "user_info": user_info}
        payload_json = json.dumps(payload, ensure_ascii=False)
        script = f"""(() => {{
  try {{
    const s = {payload_json};
    if (s && s.token) sessionStorage.setItem('token', s.token);
    if (s && s.user_info) sessionStorage.setItem('user_info', s.user_info);
  }} catch (e) {{
    console.warn('auto-test-bot: session_state 注入失败', e);
  }}
}})();"""
        try:
            await self.context.add_init_script(script=script)
            self.session_state_path = session_path
            try:
                self._auth_session_mtime = os.path.getmtime(session_path)
            except Exception:
                self._auth_session_mtime = None
            self.logger.info(f"已注入 session_state: {session_path}")
            return True
        except Exception as e:
            self.logger.warning(f"注入 session_state 失败: {e}")
            return False

    def _install_auth_response_watchers(self) -> None:
        if not self.page:
            return
        try:
            self.page.on("response", lambda resp: asyncio.create_task(self._inspect_response_for_auth_issue(resp)))
        except Exception:
            return

    @staticmethod
    def _extract_auth_issue_from_payload(payload: Any) -> Optional[Dict[str, Any]]:
        """
        解析后端常见的认证错误格式（例如 { code: 50008, msg: '请求令牌已过期' }）
        返回 None 表示未识别到认证问题。
        """
        if not isinstance(payload, dict):
            return None
        code = payload.get("code")
        msg = payload.get("msg") or payload.get("message") or payload.get("error") or ""
        try:
            code_str = str(code) if code is not None else ""
        except Exception:
            code_str = ""
        msg_str = str(msg) if msg is not None else ""

        if code_str == "50008":
            return {"code": 50008, "message": msg_str or "请求令牌已过期"}
        # 兼容部分实现：没有 code 但有文案
        if ("令牌" in msg_str or "token" in msg_str.lower()) and ("过期" in msg_str or "expired" in msg_str.lower()):
            return {"code": code_str or "unknown", "message": msg_str}
        return None

    async def _inspect_response_for_auth_issue(self, response) -> None:
        if self._auth_issue is not None:
            return
        try:
            status = int(getattr(response, "status", 0) or 0)
            url = str(getattr(response, "url", "") or "")
            headers = await response.all_headers()
            content_type = str(headers.get("content-type") or "").lower()

            # 明确的 HTTP 401/403
            if status in (401, 403):
                self._auth_issue = {"code": status, "message": f"HTTP {status}（可能未登录/权限不足）", "url": url}
                self.logger.error(f"检测到认证失败: {self._auth_issue}")
                return

            # 业务错误码（通常为 200 + JSON body）
            should_try_json = ("application/json" in content_type) or ("json" in content_type) or ("/api/" in url) or (status >= 400)
            if should_try_json:
                payload = None
                try:
                    payload = await asyncio.wait_for(response.json(), timeout=2.0)
                except Exception:
                    payload = None

                issue = self._extract_auth_issue_from_payload(payload)
                if issue is not None:
                    issue["url"] = url
                    issue["status"] = status
                    self._auth_issue = issue
                    self.logger.error(f"检测到认证错误码: {self._auth_issue}")
                    return

                # 非 JSON 情况兜底：尝试抓取少量文本
                if status >= 400:
                    try:
                        text = await asyncio.wait_for(response.text(), timeout=2.0)
                        if "50008" in text or ("请求令牌" in text and "过期" in text):
                            self._auth_issue = {"code": 50008, "message": "请求令牌已过期", "url": url, "status": status}
                            self.logger.error(f"检测到认证错误文本: {self._auth_issue}")
                    except Exception:
                        return
        except Exception:
            return

    async def refresh_auth_from_disk_if_changed(self) -> bool:
        """
        尝试从磁盘重新加载 session_state（需要外部先更新 token），并刷新当前页面。
        返回 True 表示检测到文件变更并已尝试刷新。
        """
        if not self.page:
            return False
        session_path = self.config.get("session_state")
        if not isinstance(session_path, str) or not session_path or not os.path.exists(session_path):
            return False
        try:
            mtime = os.path.getmtime(session_path)
        except Exception:
            return False
        if self._auth_session_mtime is not None and mtime <= self._auth_session_mtime:
            return False

        try:
            raw = json.load(open(session_path, "r", encoding="utf-8"))
            token = raw.get("token")
            user_info = raw.get("user_info")
            if isinstance(user_info, dict):
                user_info = json.dumps(user_info, ensure_ascii=False)
            payload_json = json.dumps({"token": token, "user_info": user_info}, ensure_ascii=False)
            await self.page.evaluate(
                """(s) => {
  try {
    if (s && s.token) sessionStorage.setItem('token', s.token);
    if (s && s.user_info) sessionStorage.setItem('user_info', s.user_info);
  } catch (e) {}
}""",
                json.loads(payload_json),
            )
            self._auth_session_mtime = mtime
            self.clear_auth_issue()
            try:
                await self.page.reload(wait_until="commit", timeout=int(self.full_config.get("test", {}).get("page_load_timeout", 60000)))
            except Exception:
                pass
            self.logger.info(f"已从磁盘刷新 session_state: {session_path}")
            return True
        except Exception:
            return False

    async def raise_if_auth_expired(self) -> None:
        """
        若检测到 token 过期/认证失败，则快速抛错，避免 wait_for 长时间卡住。
        会先尝试从磁盘热加载更新后的 session_state（若文件已被外部刷新）。
        """
        if self._auth_issue is None:
            return

        # 若用户已更新 session_state 文件，则自动刷新并继续
        try:
            refreshed = await self.refresh_auth_from_disk_if_changed()
            if refreshed and self._auth_issue is None:
                return
        except Exception:
            pass

        issue = self._auth_issue or {}
        code = issue.get("code")
        message = issue.get("message") or "认证失败"
        url = issue.get("url") or ""
        hint = (
            "检测到登录态失效（例如 code=50008 请求令牌过期）。"
            "请重新生成登录态文件后重试：\n"
            "  `python scripts/auth/save_real_auth_state.py --config config/config.yaml`\n"
            "（在打开的浏览器中完成登录并进入 AI 创作页后按回车保存）"
        )
        raise RuntimeError(f"{message} (code={code}, url={url}). {hint}")

    async def navigate_to(self, url: str, timeout: Optional[int] = None) -> bool:
        if not self.page:
            return False
        try:
            self.logger.info(f"正在访问: {url}")
            page_load_timeout = int(timeout) if timeout is not None else int(self.full_config.get("test", {}).get("page_load_timeout", 60000))
            response = await self.page.goto(url, wait_until="commit", timeout=page_load_timeout)
            if response and response.status >= 400:
                self.logger.error(f"页面访问失败: HTTP {response.status}")
                return False
            self.logger.info("页面加载成功")
            return True
        except Exception as e:
            self.logger.error(f"页面导航失败: {e}")
            return False

    async def wait_for_selector(self, selector: str, state: str = "visible", timeout: Optional[int] = None) -> bool:
        if not self.page:
            return False
        try:
            wait_timeout = int(timeout) if timeout is not None else int(self.full_config.get("test", {}).get("element_timeout", 10000))
            # 使用 locator().first 避免 strict-mode 因多匹配导致失败
            await self.page.locator(selector).first.wait_for(state=state, timeout=wait_timeout)
            return True
        except Exception as e:
            self.logger.warning(f"等待选择器失败 [{selector}] state={state}: {e}")
            return False

    async def click_element(self, selector: str, timeout: Optional[int] = None) -> bool:
        if not self.page:
            return False
        try:
            # 使用 locator().first 避免 strict-mode 因多匹配导致失败
            click_timeout = int(timeout) if timeout is not None else None
            if click_timeout is None:
                await self.page.locator(selector).first.click()
            else:
                await self.page.locator(selector).first.click(timeout=click_timeout)
            return True
        except Exception as e:
            self.logger.error(f"点击元素失败 [{selector}]: {e}")
            return False

    async def fill_input(self, selector: str, text: str, timeout: Optional[int] = None) -> bool:
        if not self.page:
            return False
        try:
            # 使用 locator().first 避免 strict-mode 因多匹配导致失败
            fill_timeout = int(timeout) if timeout is not None else None
            if fill_timeout is None:
                await self.page.locator(selector).first.fill(text)
            else:
                await self.page.locator(selector).first.fill(text, timeout=fill_timeout)
            return True
        except Exception as e:
            self.logger.error(f"填充输入框失败 [{selector}]: {e}")
            return False

    async def take_screenshot(self, filename: str, timeout: Optional[int] = None, full_page: bool = True) -> bool:
        if not self.page:
            return False
        try:
            kwargs: Dict[str, Any] = {"path": filename, "full_page": bool(full_page)}
            if timeout is not None:
                kwargs["timeout"] = int(timeout)
            await self.page.screenshot(**kwargs)
            self.logger.info(f"截图已保存: {filename}")
            return True
        except Exception as e:
            self.logger.error(f"截图失败: {e}")
            return False

    async def get_page_url(self) -> str:
        return self.page.url if self.page else ""

    def get_storage_state_info(self) -> Dict[str, Any]:
        return {
            "storage_state": {"path": self.storage_state_path},
            "session_state": {"path": self.session_state_path},
        }

    async def get_login_status(self) -> Dict[str, Any]:
        """
        强验证登录状态：基于 sessionStorage.token / sessionStorage.user_info。
        """
        if not self.page:
            return {"ok": False, "reason": "page not initialized"}

        script = """() => {
  const token = sessionStorage.getItem('token');
  const raw = sessionStorage.getItem('user_info');
  if (!token || !raw) return { ok: false, reason: 'token/user_info missing' };
  let ui;
  try { ui = JSON.parse(raw); } catch { return { ok: false, reason: 'user_info not json' }; }
  const ok =
    !!ui.id &&
    (ui.enabled === true || ui.enabled === undefined) &&
    (ui.accountNonLocked === true || ui.accountNonLocked === undefined) &&
    Array.isArray(ui.authorities) && ui.authorities.length > 0;
  return {
    ok,
    reason: ok ? 'ok' : 'invalid user_info',
    user: ui.username || ui.name || null,
    id: ui.id || null,
    authCount: Array.isArray(ui.authorities) ? ui.authorities.length : 0,
  };
}"""
        try:
            status = await self.page.evaluate(script)
            return status or {"ok": False, "reason": "empty result"}
        except Exception as e:
            return {"ok": False, "reason": f"js evaluate failed: {e}"}

    async def assert_logged_in(self) -> Tuple[bool, Dict[str, Any], str]:
        status = await self.get_login_status()
        if status.get("ok") is True:
            return True, status, ""

        storage_info = self.get_storage_state_info()
        session_path = (storage_info.get("session_state") or {}).get("path")
        storage_path = (storage_info.get("storage_state") or {}).get("path")
        reason = status.get("reason")
        message = (
            "登录态无效或已过期："
            f"{reason}。"
            f"(session_state={session_path}, storage_state={storage_path}) "
            "请重新生成登录态：运行 `python save_real_auth_state.py`，"
            "完成登录并进入需要登录的页面后回车保存。"
        )
        return False, status, message

    async def close(self) -> None:
        try:
            if self.page:
                await self.page.close()
                self.page = None
        except Exception:
            pass
        try:
            if self.context:
                await self.context.close()
                self.context = None
        except Exception:
            pass
        try:
            if self.browser:
                await self.browser.close()
                self.browser = None
        except Exception:
            pass
        try:
            if self.playwright:
                await self.playwright.stop()
                self.playwright = None
        except Exception:
            pass
