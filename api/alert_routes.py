# api/alert_routes.py
from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException

from api.auth.routes import get_current_user
from api.models import Alert, AlertCreate, AlertSeverity, Role, User

router = APIRouter()

ALERTS_DATA_PATH = os.getenv("ALERTS_DATA_PATH", "data/alerts.json")


def _load_alerts() -> Dict[str, Alert]:
    if not os.path.exists(ALERTS_DATA_PATH):
        return {}
    with open(ALERTS_DATA_PATH, "r", encoding="utf-8") as f:
        raw = json.load(f)
    alerts: Dict[str, Alert] = {}
    for aid, payload in raw.items():
        alerts[aid] = Alert(
            id=aid,
            title=payload["title"],
            message=payload["message"],
            severity=AlertSeverity(payload["severity"]),
            tag=payload.get("tag", "PLAYER"),
            timestamp=datetime.fromisoformat(payload["timestamp"]),
            read=payload.get("read", False),
            role=Role(payload["role"]),
        )
    return alerts


def _save_alerts(alerts: Dict[str, Alert]) -> None:
    os.makedirs(os.path.dirname(ALERTS_DATA_PATH), exist_ok=True)
    raw = {
        aid: {
            "title": a.title,
            "message": a.message,
            "severity": a.severity.value,
            "tag": a.tag,
            "timestamp": a.timestamp.isoformat(),
            "read": a.read,
            "role": a.role.value,
        }
        for aid, a in alerts.items()
    }
    with open(ALERTS_DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(raw, f, indent=2)


def _seed_if_empty(alerts: Dict[str, Alert]) -> None:
    if alerts:
        return

    demo = [
        Alert(
            id="p1",
            title="New Scene Assigned",
            message="Director queued a feeding scene in Canterbury.",
            severity=AlertSeverity.high,
            tag="PLAYER",
            timestamp=datetime.utcnow(),
            read=False,
            role=Role.player,
        ),
        Alert(
            id="s1",
            title="Masquerade Risk",
            message="Coteries converging on Margate hunting grounds.",
            severity=AlertSeverity.critical,
            tag="ST",
            timestamp=datetime.utcnow(),
            read=False,
            role=Role.st,
        ),
    ]
    for a in demo:
        alerts[a.id] = a


@router.get("/alerts", response_model=List[Alert])
async def list_alerts(
    role: Role,
    user: User = Depends(get_current_user),
) -> List[Alert]:
    """
    Used by the Windows app:

      GET /alerts?role=player
      GET /alerts?role=st
    """
    if role not in user.roles:
        raise HTTPException(status_code=403, detail="Forbidden for this role")

    alerts = _load_alerts()
    _seed_if_empty(alerts)
    result = [a for a in alerts.values() if a.role == role]
    # Newest first
    result.sort(key=lambda a: a.timestamp, reverse=True)
    return result


@router.post("/alerts", response_model=Alert)
async def create_alert(
    payload: AlertCreate,
    user: User = Depends(get_current_user),
) -> Alert:
    """
    Let the *bot* or your ST tools create alerts via HTTP if you want.
    For now: ST role required.
    """
    if Role.st not in user.roles:
        raise HTTPException(status_code=403, detail="Only ST can create alerts")

    alerts = _load_alerts()
    _seed_if_empty(alerts)

    new_id = f"{payload.role.value}_{len(alerts) + 1}"
    alert = Alert(
        id=new_id,
        title=payload.title,
        message=payload.message,
        severity=payload.severity,
        tag=payload.tag,
        timestamp=datetime.utcnow(),
        read=False,
        role=payload.role,
    )
    alerts[new_id] = alert
    _save_alerts(alerts)
    return alert
