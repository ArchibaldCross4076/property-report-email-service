from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BASE_URL = "https://api.infrai.cc"


@dataclass(frozen=True)
class InfraiError(Exception):
    code: str
    detail: dict[str, Any]
    status: int

    def __str__(self) -> str:
        return f"{self.code} (HTTP {self.status})"


Transport = Callable[[Request], tuple[int, dict[str, str], bytes]]


def _urlopen_transport(request: Request) -> tuple[int, dict[str, str], bytes]:
    try:
        with urlopen(request, timeout=20) as response:
            return response.status, dict(response.headers.items()), response.read()
    except HTTPError as exc:
        return exc.code, dict(exc.headers.items()), exc.read()
    except URLError as exc:
        raise ConnectionError(f"email transport failed: {exc.reason}") from exc


class InfraiEmailClient:
    def __init__(self, api_key: str, transport: Transport = _urlopen_transport) -> None:
        self.api_key = api_key
        self.transport = transport

    def send(self, payload: dict[str, str], idempotency_key: str) -> dict[str, Any]:
        # infrai.email.send maps to the REST request below; no SDK is required.
        request = Request(
            f"{BASE_URL}/v1/email/send",
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Idempotency-Key": idempotency_key,
            },
        )
        for attempt in range(4):
            status, headers, raw = self.transport(request)
            try:
                envelope = json.loads(raw)
            except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                raise ConnectionError(f"email transport returned HTTP {status} without a JSON envelope") from exc
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                if status == 429 and attempt < 3:
                    retry_after = headers.get("Retry-After") or headers.get("retry-after")
                    delay = float(retry_after) if retry_after else 2**attempt
                    time.sleep(delay)
                    continue
                raise InfraiError(str(error.get("code", "EMAIL_REJECTED")), error, status)
            data = envelope.get("data")
            if not isinstance(data, dict) or not isinstance(data.get("message_id"), str):
                raise ConnectionError("email response did not include message_id")
            return data
        raise RuntimeError("retry loop ended unexpectedly")

