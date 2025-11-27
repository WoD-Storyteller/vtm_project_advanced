from __future__ import annotations

import json
import os
from typing import Dict, List

import gspread
from dotenv import load_dotenv

from .haven_model import Haven
from .haven_registry import HAVENS_JSON_PATH

load_dotenv()

HAVENS_SHEET_ID = os.getenv("GOOGLE_HAVENS_SHEET_ID")
SERVICE_KEY = os.getenv("GOOGLE_SERVICE_ACCOUNT")  # JSON string or path


def _get_gspread_client():
    if not SERVICE_KEY:
        raise RuntimeError("GOOGLE_SERVICE_ACCOUNT is not set in .env")
    key = SERVICE_KEY.strip()
    if key.startswith("{"):
        data = json.loads(key)
        return gspread.service_account_from_dict(data)
    return gspread.service_account(filename=key)


def load_sheet_havens(sheet_id: str | None = None) -> Dict[str, Haven]:
    """
    Loads havens from a Google Sheet.

    Expected columns (case-insensitive, best-effort):

      haven_id
      name
      owner_ids           (comma sep Discord IDs)
      zone_key

      lat
      lng

      security
      luxury

      feeding_domain
      masquerade_buffer
      warding_level
      influence

      rooms               (comma sep)
      tags                (comma sep)

      map_name
      map_type
      map_url

    One row per haven *map* entry; multiple rows may share same haven_id.
    """
    sheet_id = sheet_id or HAVENS_SHEET_ID
    if not sheet_id:
        raise RuntimeError("GOOGLE_HAVENS_SHEET_ID is not set in .env")

    gc = _get_gspread_client()
    sh = gc.open_by_key(sheet_id)
    ws = sh.sheet1
    rows = ws.get_all_records()

    havens: Dict[str, Haven] = {}

    for row in rows:
        raw_id = row.get("haven_id") or row.get("id")
        if not raw_id:
            continue

        haven_id = str(raw_id).strip()
        if not haven_id:
            continue

        if haven_id not in havens:
            owner_raw = row.get("owner_ids") or ""
            owner_ids = [o.strip() for o in owner_raw.split(",") if o.strip()]

            def _num(name, default=None):
                v = row.get(name)
                if v in ("", None):
                    return default
                try:
                    return float(v)
                except Exception:
                    return default

            lat = _num("lat")
            lng = _num("lng")
            security = int(row.get("security") or 1)
            luxury = int(row.get("luxury") or 1)

            domain = {
                "feeding": int(row.get("feeding_domain") or 0),
                "masquerade_buffer": int(row.get("masquerade_buffer") or 0),
                "warding_level": int(row.get("warding_level") or 0),
                "influence": int(row.get("influence") or 0),
            }

            rooms_raw = row.get("rooms") or ""
            tags_raw = row.get("tags") or ""
            rooms = [r.strip().lower() for r in rooms_raw.split(",") if r.strip()]
            tags = [t.strip().lower() for t in tags_raw.split(",") if t.strip()]

            havens[haven_id] = Haven(
                id=haven_id,
                name=row.get("name", haven_id),
                zone_key=(row.get("zone_key") or "").strip().lower(),
                owner_ids=owner_ids,
                lat=lat,
                lng=lng,
                security=security,
                luxury=luxury,
                domain=domain,
                rooms=rooms,
                tags=tags,
                maps=[],
            )

        haven = havens[haven_id]
        map_name = row.get("map_name") or ""
        map_url = row.get("map_url") or ""
        map_type = row.get("map_type") or "mymaps"

        if map_name and map_url:
            haven.maps.append(
                {
                    "map_name": map_name,
                    "url": map_url,
                    "type": map_type,
                }
            )

    return havens


def save_havens_file(havens: Dict[str, Haven], path: str = HAVENS_JSON_PATH):
    data = [h.to_dict() for h in havens.values()]
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)