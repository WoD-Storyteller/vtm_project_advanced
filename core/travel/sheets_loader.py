from __future__ import annotations

import json
from typing import Dict
import gspread

ZONES_JSON_PATH = "data/zones.json"


def load_sheet_zones(sheet_id: str, credentials_path: str) -> Dict[str, dict]:
    """
    Loads zone data from a Google Sheet and builds a zones.json structure.

    Expected columns:

    key, name, description, tags,
    encounter_table,
    risk_violence, risk_masquerade, risk_si,
    map_name, map_layer, map_label, map_url,
    region, lat, lng, faction, hunting_risk, si_risk
    """

    gc = gspread.service_account(filename=credentials_path)
    sh = gc.open_by_key(sheet_id)
    worksheet = sh.sheet1
    rows = worksheet.get_all_records()

    zones: Dict[str, dict] = {}

    for row in rows:
        key = row.get("key")
        if not key:
            continue

        if key not in zones:
            zones[key] = {
                "key": key,
                "name": row.get("name", ""),
                "description": row.get("description", ""),
                "tags": [t.strip() for t in row.get("tags", "").split(",") if t.strip()],
                "encounter_table": row.get("encounter_table", ""),
                "base_risk": {
                    "violence": int(row.get("risk_violence", 1)),
                    "masquerade": int(row.get("risk_masquerade", 1)),
                    "si": int(row.get("risk_si", 1)),
                },
                "region": row.get("region", ""),
                "lat": float(row.get("lat") or 0.0),
                "lng": float(row.get("lng") or 0.0),
                "faction": row.get("faction", ""),
                "hunting_risk": int(row.get("hunting_risk", 0) or 0),
                "si_risk": int(row.get("si_risk", 0) or 0),
                "mymaps": [],
            }

        map_entry = {
            "map_name": row.get("map_name", ""),
            "layer": row.get("map_layer", ""),
            "label": row.get("map_label", ""),
            "url": row.get("map_url", ""),
        }

        if map_entry["map_name"]:
            zones[key]["mymaps"].append(map_entry)

    return zones


def save_zones_file(zones: Dict[str, dict], path: str = ZONES_JSON_PATH):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(list(zones.values()), f, indent=4, ensure_ascii=False)