# vtm_project_advanced/core/alerts_client.py

import os
import logging
from typing import Literal, Optional

import requests

log = logging.getLogger(__name__)

ALERTS_API_BASE = os.getenv("ALERTS_API_BASE", "http://localhost:8000")


Severity = Literal["low", "medium", "high", "critical"]
Role = Literal["player", "st"]


def send_alert(
    *,
    title: str,
    message: str,
    role: Role,
    severity: Severity = "medium",
    tag: str = "PLAYER",
    token: Optional[str] = None,
) -> None:
    """
    Fire-and-forget helper for the bot to create an alert on the API.

    Example:
        send_alert(
            title="Masquerade Risk",
            message="Feeding scene got messy in Margate.",
            role="st",
            severity="critical",
            tag="ST",
        )
    """
    url = f"{ALERTS_API_BASE}/alerts"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    payload = {
        "title": title,
        "message": message,
        "severity": severity,
        "tag": tag,
        "role": role,
    }

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=5)
        if resp.status_code != 200:
            log.warning(
                "Failed to send alert (%s): %s", resp.status_code, resp.text
            )
    except Exception as e:
        log.exception("Error sending alert to API: %s", e)
