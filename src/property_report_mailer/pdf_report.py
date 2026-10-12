from __future__ import annotations

from .models import ReportEmailRequest


def report_lines(request: ReportEmailRequest) -> list[str]:
    open_requests = [item for item in request.maintenance_requests if item.status.lower() != "closed"]
    overdue = [item for item in open_requests if item.due_on < request.as_of]
    due_inspections = [item for item in request.inspection_reminders if item.due_on <= request.as_of]

    lines = [
        f"{request.property_name} property report",
        f"As of {request.as_of.isoformat()}",
        f"Action needed: {len(overdue)} overdue maintenance, {len(due_inspections)} inspections due",
        "Maintenance requests",
    ]
    lines.extend(
        f"[{('ACTION' if item in overdue else 'OPEN')}] {item.unit} - {item.summary} - due {item.due_on}"
        for item in open_requests
    )
    lines.append("Tenant documents")
    lines.extend(f"{item.tenant} - {item.name} - {item.status}" for item in request.tenant_documents)
    lines.append("Inspection reminders")
    lines.extend(
        f"[{('ACTION' if item in due_inspections else 'UPCOMING')}] {item.unit} - {item.inspection} - {item.due_on}"
        for item in request.inspection_reminders
    )
    return lines


def _pdf_text(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def generate_pdf(request: ReportEmailRequest) -> bytes:
    commands = ["BT", "/F1 10 Tf", "50 760 Td", "14 TL"]
    for index, line in enumerate(report_lines(request)):
        clipped = line.encode("ascii", "replace").decode("ascii")[:100]
        if index:
            commands.append("T*")
        commands.append(f"({_pdf_text(clipped)}) Tj")
    commands.append("ET")
    stream = "\n".join(commands).encode("ascii")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
        b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    document = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for number, obj in enumerate(objects, 1):
        offsets.append(len(document))
        document.extend(f"{number} 0 obj\n".encode("ascii") + obj + b"\nendobj\n")
    xref = len(document)
    document.extend(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode("ascii"))
    for offset in offsets[1:]:
        document.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    document.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode("ascii")
    )
    return bytes(document)

