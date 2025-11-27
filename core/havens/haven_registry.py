from __future__ import annotations

import json
import os
from typing import Dict, List, Optional

from .haven_model import Haven

HAVENS_JSON_PATH = "data/havens.json"


class HavenRegistry:
    """
    Global registry for all havens across the world.
    Backed by data/havens.json.
    """

    def __init__(self, path: str = HAVENS_JSON_PATH):
        self.path = path
        self._havens: Dict[str, Haven] = {}
        self.load()

    # -------------------------------------------------
    # IO
    # -------------------------------------------------
    def load(self):
        if not os.path.exists(self.path):
            self._havens = {}
            return

        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = []

        self._havens = {}
        for raw in data:
            try:
                haven = Haven.from_dict(raw)
                self._havens[haven.id] = haven
            except Exception:
                continue

    def save(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        data = [h.to_dict() for h in self._havens.values()]
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    # -------------------------------------------------
    # Queries
    # -------------------------------------------------
    def all(self) -> List[Haven]:
        return list(self._havens.values())

    def get(self, haven_id: str) -> Optional[Haven]:
        return self._havens.get(haven_id)

    def find_by_name(self, name: str) -> Optional[Haven]:
        p = name.lower().strip()
        for h in self._havens.values():
            if h.name.lower() == p:
                return h
        for h in self._havens.values():
            if p in h.name.lower():
                return h
        return None

    def list_for_owner(self, owner_id: str) -> List[Haven]:
        return [h for h in self._havens.values() if owner_id in h.owner_ids]

    def list_for_owner_in_zone(self, owner_id: str, zone_key: str) -> List[Haven]:
        zone_key = zone_key.lower()
        return [
            h
            for h in self._havens.values()
            if owner_id in h.owner_ids and h.zone_key.lower() == zone_key
        ]

    # -------------------------------------------------
    # Mutations
    # -------------------------------------------------
    def upsert(self, haven: Haven):
        self._havens[haven.id] = haven

    def delete(self, haven_id: str):
        if haven_id in self._havens:
            del self._havens[haven_id]