from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, Optional
from urllib.parse import parse_qs, urlparse
import threading

from .service import MonitoringService


_INDEX_HTML = """<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>NowHi Monitoring</title>
    <style>
      body { font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial; margin: 24px; }
      .grid { display: grid; grid-template-columns: 1fr; gap: 16px; max-width: 980px; }
      pre { background: #0b1020; color: #e7eaff; padding: 12px; border-radius: 8px; overflow: auto; }
      .card { border: 1px solid #e5e7eb; border-radius: 10px; padding: 12px; }
      h1 { margin: 0 0 12px; }
      .muted { color: #6b7280; }
      .row { display: flex; gap: 12px; flex-wrap: wrap; align-items: center; }
      input { padding: 6px 8px; border: 1px solid #d1d5db; border-radius: 8px; }
      button { padding: 6px 10px; border: 1px solid #d1d5db; border-radius: 8px; background: #fff; cursor: pointer; }
    </style>
  </head>
  <body>
    <h1>NowHi Monitoring</h1>
    <div class="muted">实时刷新（默认 2s）：SLO / Alerts / Metrics</div>
    <div class="grid">
      <div class="card">
        <div class="row">
          <div>Domain:</div>
          <input id="domain" value="task" />
          <button onclick="refreshAll()">Refresh</button>
        </div>
      </div>
      <div class="card">
        <h3>SLO</h3>
        <pre id="slo"></pre>
      </div>
      <div class="card">
        <h3>Alerts</h3>
        <pre id="alerts"></pre>
      </div>
      <div class="card">
        <h3>Metrics</h3>
        <pre id="metrics"></pre>
      </div>
    </div>
    <script>
      async function getJson(path) {
        const res = await fetch(path);
        return await res.json();
      }
      async function refreshAll() {
        const domain = document.getElementById('domain').value || 'task';
        const [slo, alerts, metrics] = await Promise.all([
          getJson('/api/slo'),
          getJson('/api/alerts'),
          getJson('/api/metrics?domain=' + encodeURIComponent(domain)),
        ]);
        document.getElementById('slo').textContent = JSON.stringify(slo, null, 2);
        document.getElementById('alerts').textContent = JSON.stringify(alerts, null, 2);
        document.getElementById('metrics').textContent = JSON.stringify(metrics, null, 2);
      }
      refreshAll();
      setInterval(refreshAll, 2000);
    </script>
  </body>
</html>
"""


class MonitoringDashboardServer:
    """
    Phase 3 Week7 MVP：零依赖 Dashboard/API。
    - GET /: 简单 HTML
    - GET /api/slo: 当前 SLO 状态
    - GET /api/alerts: 当前告警列表
    - GET /api/metrics?domain=task: 指定 domain 的记录
    """

    def __init__(self, *, service: MonitoringService, host: str = "127.0.0.1", port: int = 8080):
        self._service = service
        self.host = host
        self.port = port
        self._httpd: Optional[ThreadingHTTPServer] = None
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        handler_cls = self._make_handler()
        httpd = ThreadingHTTPServer((self.host, self.port), handler_cls)
        self._httpd = httpd
        # update port when binding to 0
        self.port = int(httpd.server_address[1])
        self._thread = threading.Thread(target=httpd.serve_forever, name="monitoring-dashboard", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if self._httpd:
            try:
                self._httpd.shutdown()
            except Exception:
                pass
            try:
                self._httpd.server_close()
            except Exception:
                pass
        if self._thread:
            self._thread.join(timeout=2)
        self._httpd = None
        self._thread = None

    def _make_handler(self):
        service = self._service

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):  # noqa: N802
                parsed = urlparse(self.path)
                path = parsed.path
                qs = parse_qs(parsed.query or "")

                if path == "/":
                    self._send_html(_INDEX_HTML)
                    return

                if path == "/api/slo":
                    snapshot = service.evaluate_now()
                    slo_status = snapshot["slo_status"]
                    payload = {
                        "all_compliant": slo_status.all_compliant,
                        "details": slo_status.details,
                        "violations": slo_status.violations,
                    }
                    self._send_json(payload)
                    return

                if path == "/api/alerts":
                    snapshot = service.evaluate_now()
                    self._send_json(snapshot["alerts"])
                    return

                if path == "/api/metrics":
                    domain = (qs.get("domain") or ["events"])[0]
                    self._send_json(service.metrics_db.query(domain))
                    return

                self.send_response(404)
                self.end_headers()

            def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
                # keep tests quiet
                return

            def _send_json(self, payload: Any) -> None:
                raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)

            def _send_html(self, html: str) -> None:
                raw = html.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)

        return Handler

