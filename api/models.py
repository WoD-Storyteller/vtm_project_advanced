# api/models.py
from datetime import datetime
from enum import Enum
from typing import List

from pydantic import BaseModel


class Role(str, Enum):
    player = "player"
    st = "st"


class AlertSeverity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class User(BaseModel):
    id: str
    display_name: str
    roles: List[Role]


class Alert(BaseModel):
    id: str
    title: str
    message: str
    severity: AlertSeverity
    tag: str
    timestamp: datetime
    read: bool
    role: Role


class AlertCreate(BaseModel):
    title: str
    message: str
    severity: AlertSeverity = AlertSeverity.medium
    tag: str = "PLAYER"
    role: Role


class OAuthRequest(BaseModel):
    code: str
    redirect_uri: str
