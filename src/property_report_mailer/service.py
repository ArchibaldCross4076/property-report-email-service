from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from .infrai_email import InfraiEmailClient, InfraiError
from .models import ReportEmailRequest
from .report_sender import send_property_report


class PropertyReportHandler(BaseHTTPRequestHandler):
    def _reply(self, status: int, value: dict[str, Any]) -> None:
        body = json.dumps(value).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:
        if self.path != "/reports/email":
            self._reply(404, {"error": "route not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            request = ReportEmailRequest.from_dict(json.loads(self.rfile.read(length)))
            api_key = os.environ.get("INFRAI_API_KEY")
            if not api_key:
                raise ValueError("INFRAI_API_KEY is required")
            result = send_property_report(request, InfraiEmailClient(api_key))
            self._reply(202, {"message_id": result.message_id, "action_count": result.action_count})
        except (ValueError, KeyError, json.JSONDecodeError) as exc:
            self._reply(400, {"error": str(exc)})
        except InfraiError as exc:
            status = exc.status if 400 <= exc.status < 500 else 502
            self._reply(status, {"error": exc.code})
        except ConnectionError as exc:
            self._reply(502, {"error": str(exc)})


def main() -> None:
    port = int(os.environ.get("PORT", "8080"))
    print(f"Property report service listening on http://127.0.0.1:{port}")
    ThreadingHTTPServer(("127.0.0.1", port), PropertyReportHandler).serve_forever()


if __name__ == "__main__":
    main()

