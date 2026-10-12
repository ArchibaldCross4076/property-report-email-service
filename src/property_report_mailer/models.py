from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Sequence


def _date(value: Any, field: str) -> date:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be an ISO date")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field} must be an ISO date") from exc


@dataclass(frozen=True)
class MaintenanceRequest:
    request_id: str
    unit: str
    summary: str
    due_on: date
    status: str

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "MaintenanceRequest":
        return cls(
            request_id=str(value["request_id"]),
            unit=str(value["unit"]),
            summary=str(value["summary"]),
            due_on=_date(value["due_on"], "due_on"),
            status=str(value["status"]),
        )


@dataclass(frozen=True)
class TenantDocument:
    tenant: str
    name: str
    status: str

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "TenantDocument":
        return cls(tenant=str(value["tenant"]), name=str(value["name"]), status=str(value["status"]))


@dataclass(frozen=True)
class InspectionReminder:
    unit: str
    inspection: str
    due_on: date

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "InspectionReminder":
        return cls(
            unit=str(value["unit"]),
            inspection=str(value["inspection"]),
            due_on=_date(value["due_on"], "due_on"),
        )


@dataclass(frozen=True)
class ReportEmailRequest:
    report_id: str
    property_name: str
    recipient: str
    as_of: date
    maintenance_requests: Sequence[MaintenanceRequest]
    tenant_documents: Sequence[TenantDocument]
    inspection_reminders: Sequence[InspectionReminder]

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "ReportEmailRequest":
        required = {"report_id", "property_name", "recipient", "as_of"}
        missing = sorted(required - value.keys())
        if missing:
            raise ValueError(f"missing fields: {', '.join(missing)}")
        return cls(
            report_id=str(value["report_id"]),
            property_name=str(value["property_name"]),
            recipient=str(value["recipient"]),
            as_of=_date(value["as_of"], "as_of"),
            maintenance_requests=tuple(
                MaintenanceRequest.from_dict(item) for item in value.get("maintenance_requests", [])
            ),
            tenant_documents=tuple(
                TenantDocument.from_dict(item) for item in value.get("tenant_documents", [])
            ),
            inspection_reminders=tuple(
                InspectionReminder.from_dict(item) for item in value.get("inspection_reminders", [])
            ),
        )
