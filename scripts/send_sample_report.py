from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from property_report_mailer.infrai_email import InfraiEmailClient
from property_report_mailer.models import ReportEmailRequest
from property_report_mailer.report_sender import send_property_report


def main() -> None:
    api_key = os.environ.get("INFRAI_API_KEY")
    recipient = os.environ.get("REPORT_EMAIL_TO")
    if not api_key or not recipient:
        raise SystemExit("Set INFRAI_API_KEY and REPORT_EMAIL_TO")
    request = ReportEmailRequest.from_dict(
        {
            "report_id": "harbor-2026-09-05",
            "property_name": "Harbor Court",
            "recipient": recipient,
            "as_of": "2026-09-05",
            "maintenance_requests": [
                {"request_id": "MR-104", "unit": "2B", "summary": "Leaking tap", "due_on": "2026-09-04", "status": "open"}
            ],
            "tenant_documents": [{"tenant": "A. Chen", "name": "Insurance certificate", "status": "received"}],
            "inspection_reminders": [{"unit": "4A", "inspection": "Smoke alarm", "due_on": "2026-09-12"}],
        }
    )
    result = send_property_report(request, InfraiEmailClient(api_key))
    print(f"sent message_id={result.message_id} action_count={result.action_count}")


if __name__ == "__main__":
    main()
