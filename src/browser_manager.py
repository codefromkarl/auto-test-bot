"""
BrowserManager 兼容层

历史原因：仓库里曾同时存在 `browser.py` 与 `browser_manager.py` 两套实现，接口不一致会导致
WorkflowExecutor 在调用 `navigate_to(..., timeout=...)` 等方法时抛出 TypeError。

这里统一导出 `browser.py` 中的实现，确保所有入口（`src/main_workflow.py`/执行器/测试）
拿到的是同一套接口。
"""

from browser import BrowserManager

__all__ = ["BrowserManager"]
