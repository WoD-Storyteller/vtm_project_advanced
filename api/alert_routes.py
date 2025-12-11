# vtm_project_advanced/api/alerts_routes.py

from __future__ import annotations

import json
import os
from datetime import datetime
from enum import Enum
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

ALERTS_DATA_PATH = os.getenv("ALERTS_DATA_PATH", "alerts_data.json")

router = APIRouter(prefix="/alerts", tags=["alerts"])


# -----------------------------
# Models
# -----------------------------

class AlertSeverity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class Role(str, Enum):
    player = "player"
    st = "st"


class Alert(BaseException):
    # Pydantic-like simple container
    def __init__(
        self,
        id: str,
        title: str,
        message: str,
        severity: AlertSeverity,
        tag: str,
        timestamp: datetime,
        read: bool,
        role: Role,
    ):
        self.id = id
        self.title = title
        self.message = message
        self.severity = severity
        self.tag = tag
        self.timestamp = timestamp
        self.read = read
        self.role = role

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "message": self.message,
            "severity": self.severity.value,
            "tag": self.tag,
            "timestamp": self.timestamp.isoformat(),
            "read": self.read,
            "role": self.role.value,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Alert":
        return cls(
            id=data["id"],
            title=data["title"],
            message=data["message"],
            severity=AlertSeverity(data["severity"]),
            tag=data.get("tag", "PLAYER"),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            read=bool(data.get("read", False)),
            role=Role(data["role"]),
        )


# Pydantic request models
from pydantic import BaseModel, Field


class AlertCreate(BaseModel):
    title: str
    message: str
    severity: AlertSeverity = AlertSeverity.medium
    tag: str = "PLAYER"
    role: Role


class AlertOut(BaseModel):
    id: str
    title: str
    message: str
    severity: AlertSeverity
    tag: str
    timestamp: datetime
    read: bool
    role: Role


# -----------------------------
# Simple JSON store
# -----------------------------

def _load_alerts() -> list[Alert]:
    if not os.path.exists(ALERTS_DATA_PATH):
        return []
    with open(ALERTS_DATA_PATH, "r", encoding="utf-8") as f:
        raw = json.load(f)
    items = raw.get("alerts", [])
    return [Alert.from_dict(a) for a in items]


def _save_alerts(alerts: list[Alert]) -> None:
    data = {"alerts": [a.to_dict() for a in alerts]}
    with open(ALERTS_DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _next_id(alerts: list[Alert], role: Role) -> str:
    base = f"{role.value}_"
    existing_nums = []
    for a in alerts:
        if a.id.startswith(base):
            try:
                existing_nums.append(int(a.id.split("_", 1)[1]))
            except ValueError:
                continue
    n = (max(existing_nums) + 1) if existing_nums else 1
    return f"{role.value}_{n}"


# -----------------------------
# Fake auth stub
# -----------------------------

class User(BaseModel):
    id: str
    display_name: str
    roles: list[Role] = Field(default_factory=list)


async def get_current_user() -> User:
    # TODO: replace with real JWT verification if you want.
    # For now: a demo user with both roles.
    return User(
        id="demo_discord_user",
        display_name="Omega",
        roles=[Role.player, Role.st],
    )


def _require_role(user: User, role: Role) -> None:
    if role not in user.roles:
        raise HTTPException(status_code=403, detail="User does not have this role")


# -----------------------------
# Routes
# -----------------------------

@router.get("", response_model=list[AlertOut])
async def get_alerts(
    role: Optional[Role] = Query(None),
    user: User = Depends(get_current_user),
) -> list[AlertOut]:
    alerts = _load_alerts()
    effective_role = role or Role.player
    _require_role(user, effective_role)
    filtered = [a for a in alerts if a.role == effective_role]
    filtered.sort(key=lambda a: a.timestamp, reverse=True)
    return [AlertOut(**a.to_dict()) for a in filtered]


@router.post("", response_model=AlertOut)
async def create_alert(
    payload: AlertCreate,
    user: User = Depends(get_current_user),
) -> AlertOut:
    # Only STs can create alerts
    _require_role(user, Role.st)

    alerts = _load_alerts()
    new_id = _next_id(alerts, payload.role)
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
    alerts.append(alert)
    _save_alerts(alerts)
    return AlertOut(**alert.to_dict())


@router.post("/{alert_id}/ack", response_model=AlertOut)
async def acknowledge_alert(
    alert_id: str,
    user: User = Depends(get_current_user),
) -> AlertOut:
    alerts = _load_alerts()
    matched = None
    for a in alerts:
        if a.id == alert_id:
            matched = a
            break
    if matched is None:
        raise HTTPException(status_code=404, detail="Alert not found")

    _require_role(user, matched.role)

    matched.read = True
    _save_alerts(alerts)
    return AlertOut(**matched.to_dict())
