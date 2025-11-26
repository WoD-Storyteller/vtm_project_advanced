from __future__ import annotations

import json
from typing import Dict
import gspread

ZONES_JSON_PATH = "data/zones.json"


def load_sheet_zones(sheet_id="vtm_map" credentials_path="/opt/vtm_bot/bot/configs/just-sunrise-398717-bf23770e7b50.json") -> Dict[str, dict]:
    """
    Loads zone data from a Google Sheet and builds a zones.json structure.

    Expected columns:

    key, name, description, tags,
    encounter_table,
    risk_violence, risk_masquerade, risk_si,
    map_name, map_layer, map_label, map_url

    Multiple rows may share the same `key` to define multiple MyMaps layers.
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

        # Create new zone entry
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
                "mymaps": [],
            }

        # Add My Maps entry
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