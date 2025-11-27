from __future__ import annotations

import json
from typing import Dict
import os

import gspread
from dotenv import load_dotenv

load_dotenv()

ZONES_JSON_PATH = "data/zones.json"

SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
SERVICE_KEY = os.getenv("GOOGLE_SERVICE_ACCOUNT")  # either JSON string or path to key file


def _get_gspread_client():
    if not SERVICE_KEY:
        raise RuntimeError("GOOGLE_SERVICE_ACCOUNT is not set in .env")

    key = SERVICE_KEY.strip()
    if key.startswith("{"):
        # Treat as JSON string
        data = json.loads(key)
        return gspread.service_account_from_dict(data)
    else:
        # Treat as path to JSON credentials file
        return gspread.service_account(filename=key)


def load_sheet_zones(sheet_id: str | None = None) -> Dict[str, dict]:
    """
    Loads a Google Sheet describing zones into a dict of zone_key -> zone_data.

    Expected columns (case-insensitive, best-effort):
      key, name, region, country, faction, danger,
      lat, lng,
      base_travel_hours,
      violence_risk, masquerade_risk, si_risk, occult_risk,
      tags, neighbours,
      map_name, map_type, map_url
    """
    sheet_id = sheet_id or SHEET_ID
    if not sheet_id:
        raise RuntimeError("GOOGLE_SHEET_ID is not set in .env")

    gc = _get_gspread_client()
    sh = gc.open_by_key(sheet_id)
    ws = sh.sheet1

    rows = ws.get_all_records()

    zones: Dict[str, dict] = {}

    for row in rows:
        key = str(row.get("key") or row.get("zone_key") or "").strip().lower()
        if not key:
            continue

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
        danger = int(row.get("danger") or 2)

        base_risk = {
            "violence": int(row.get("violence_risk") or 1),
            "masquerade": int(row.get("masquerade_risk") or 1),
            "si": int(row.get("si_risk") or 1),
            "occult": int(row.get("occult_risk") or 1),
        }

        tags_raw = row.get("tags") or ""
        neighbours_raw = row.get("neighbours") or ""
        tags = [t.strip().lower() for t in tags_raw.split(",") if t.strip()]
        neighbours = [n.strip().lower() for n in neighbours_raw.split(",") if n.strip()]

        if key not in zones:
            zones[key] = {
                "key": key,
                "name": row.get("name", key),
                "region": row.get("region", ""),
                "country": row.get("country", ""),
                "faction": row.get("faction", ""),
                "danger": danger,
                "lat": lat,
                "lng": lng,
                "base_travel_hours": int(row.get("base_travel_hours") or 1),
                "base_risk": base_risk,
                "tags": tags,
                "neighbours": neighbours,
                "mymaps": [],
            }

        map_entry = {
            "map_name": row.get("map_name", ""),
            "type": row.get("map_type", "mymaps"),
            "url": row.get("map_url", ""),
        }

        if map_entry["map_name"] and map_entry["url"]:
            zones[key]["mymaps"].append(map_entry)

    return zones


def save_zones_file(zones: Dict[str, dict], path: str = ZONES_JSON_PATH):
    """
    Writes zones.json to disk from a zones dict.
    """
    # zones is dict key -> zone_dict
    with open(path, "w", encoding="utf-8") as f:
        json.dump(list(zones.values()), f, indent=4, ensure_ascii=False)