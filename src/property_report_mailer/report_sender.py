from __future__ import annotations

import base64
import html
from dataclasses import dataclass
from typing import Any, Protocol

from .models import ReportEmailRequest
from .pdf_report import generate_pdf, report_lines


class EmailSender(Protocol):
    def send(self, payload: dict[str, str], idempotency_key: str) -> dict[str, Any]:
        raise NotImplementedError


@dataclass(frozen=True)
class SendResult:
    message_id: str
    action_count: int


def send_property_report(request: ReportEmailRequest, email: EmailSender) -> SendResult:
    lines = report_lines(request)
    action_count = sum("[ACTION]" in line for line in lines)
    encoded_pdf = base64.b64encode(generate_pdf(request)).decode("ascii")
    filename = f"property-report-{request.report_id}.pdf"
    report_link = f"data:application/pdf;base64,{encoded_pdf}"
    body = (
        f"<h1>{html.escape(request.property_name)} report</h1>"
        f"<p>{action_count} item(s) need attention as of {request.as_of.isoformat()}.</p>"
        f'<p><a href="{report_link}" download="{html.escape(filename)}">Download {html.escape(filename)}</a></p>'
    )
    data = email.send(
        {"to": request.recipient, "subject": f"{request.property_name} property report", "html": body},
        idempotency_key=f"property-report:{request.report_id}",
    )
    return SendResult(message_id=data["message_id"], action_count=action_count)
