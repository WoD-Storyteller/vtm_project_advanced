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

        # Create