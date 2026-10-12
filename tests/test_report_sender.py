from property_report_mailer.models import ReportEmailRequest
from property_report_mailer.report_sender import send_property_report


class RecordingEmail:
    def __init__(self) -> None:
        self.payload: dict[str, str] = {}
        self.idempotency_key = ""

    def send(self, payload: dict[str, str], idempotency_key: str) -> dict[str, str]:
        self.payload = payload
        self.idempotency_key = idempotency_key
        return {"message_id": "msg_123"}


def test_report_counts_only_overdue_open_work_and_due_inspections() -> None:
    request = ReportEmailRequest.from_dict(
        {
            "report_id": "cedar-42",
            "property_name": "Cedar House",
            "recipient": "manager@example.com",
            "as_of": "2026-09-05",
            "maintenance_requests": [
                {"request_id": "1", "unit": "1A", "summary": "Boiler", "due_on": "2026-09-04", "status": "open"},
                {"request_id": "2", "unit": "1B", "summary": "Door", "due_on": "2026-09-01", "status": "closed"},
                {"request_id": "3", "unit": "2A", "summary": "Window", "due_on": "2026-09-08", "status": "open"},
            ],
            "tenant_documents": [{"tenant": "M. Diaz", "name": "Lease", "status": "signed"}],
            "inspection_reminders": [
                {"unit": "3A", "inspection": "Fire door", "due_on": "2026-09-05"},
                {"unit": "3B", "inspection": "Alarm", "due_on": "2026-09-09"},
            ],
        }
    )
    email = RecordingEmail()

    result = send_property_report(request, email)

    assert result.message_id == "msg_123"
    assert result.action_count == 2
    assert email.payload["to"] == "manager@example.com"
    assert email.payload["subject"] == "Cedar House property report"
    assert "data:application/pdf;base64," in email.payload["html"]
    assert "from" not in email.payload
    assert email.idempotency_key == "property-report:cedar-42"

