# core/travel/sheets_loader.py
from __future__ import annotations

import json
import os
from typing import Dict, List, Any

import gspread
from dotenv import load_dotenv

# Load environment variables so this module can be used from
# bot commands, CLI, or the API server.
load_dotenv()

# Where the synced zones end up on disk.
# ZoneRegistry reads from this path.
ZONES_JSON_PATH = "data/zones.json"

# Environment configuration:
#   GOOGLE_SHEET_ID        – The spreadsheet ID for your world map / zones sheet
#   GOOGLE_SERVICE_ACCOUNT – Either:
#        * Absolute path to the service-account JSON, OR
#        * The raw JSON of the service account (single-line string)
SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
SERVICE_KEY = os.getenv("GOOGLE_SERVICE_ACCOUNT")


# ---------------------------------------------------------------------------
# Google Sheets helpers
# ---------------------------------------------------------------------------

def _get_gspread_client() -> gspread.Client:
    """
    Build a gspread client from the GOOGLE_SERVICE_ACCOUNT environment value.

    Supports two patterns:
      1) GOOGLE_SERVICE_ACCOUNT=/path/to/key.json
      2) GOOGLE_SERVICE_ACCOUNT='{"type": "service_account", ... }'
    """
    if not SERVICE_KEY:
        raise RuntimeError("GOOGLE_SERVICE_ACCOUNT is not set in environment.")

    # If the value looks like a path and exists, treat as filename
    if os.path.exists(SERVICE_KEY):
        return gspread.service_account(filename=SERVICE_KEY)

    # Otherwise assume it's JSON in the env var
    try:
        key_dict = json.loads(SERVICE_KEY)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            "GOOGLE_SERVICE_ACCOUNT is set but is neither a valid "
            "file path nor valid JSON."
        ) from exc

    return gspread.service_account_from_dict(key_dict)


def _get_worksheet(client: gspread.Client, sheet_id: str) -> gspread.Worksheet:
    """
    Returns the primary worksheet for the zones data.

    Right now we just use the first worksheet in the spreadsheet.
    If you later want to lock to a specific tab name, you can
    change this to:

        sh = client.open_by_key(sheet_id)
        return sh.worksheet("Zones")

    """
    if not sheet_id:
        raise RuntimeError("GOOGLE_SHEET_ID is not set in environment.")
    sh = client.open_by_key(sheet_id)
    # First worksheet = index 0
    return sh.get_worksheet(0)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load_sheet_zones(sheet_id: str | None = None) -> Dict[str, dict]:
    """
    Read all rows from the Google Sheet and convert them into the in-memory
    `zones` structure expected by `ZoneRegistry`.

    The sheet is expected to have (at minimum) the following column headers:

      key                – unique string ID, e.g. 'canterbury_domain'
      name               – display name
      description        – text
      tags               – comma-separated list of tags
      encounter_table    – key into encounters.json (e.g. 'urban_camarilla')

      risk_violence      – int
      risk_masquerade    – int
      risk_si            – int

      region             – region / domain label
      lat                – latitude (float)
      lng                – longitude (float)
      faction            – owning faction (string)
      hunting_risk       – int
      si_risk            – int
      travel_difficulty  – int

      map_name           – optional MyMaps / KML group name
      map_layer          – optional layer name
      map_label          – label for this zone on the map
      map_url            – URL to the map or KML

    Extra columns are ignored.
    """
    global SHEET_ID  # allow overriding via argument

    effective_sheet_id = sheet_id or SHEET_ID
    if not effective_sheet_id:
        raise RuntimeError(
            "No sheet_id provided and GOOGLE_SHEET_ID is not set. "
            "Set GOOGLE_SHEET_ID in your environment or pass sheet_id explicitly."
        )

    client = _get_gspread_client()
    ws = _get_worksheet(client, effective_sheet_id)

    # gspread returns a list[dict] keyed by header row
    rows: List[Dict[str, Any]] = ws.get_all_records()

    zones: Dict[str, dict] = {}

    for row in rows:
        # allow either "key" or "zone_key" as the header
        key_raw = row.get("key") or row.get("zone_key") or ""
        key = str(key_raw).strip()
        if not key:
            # Skip any blank lines in the sheet
            continue

        if key not in zones:
            # First time seeing this zone: create the core record
            tags_str = str(row.get("tags", "") or "")
            tags = [t.strip() for t in tags_str.split(",") if t.strip()]

            base_risk = {
                "violence": int(row.get("risk_violence", 1) or 1),
                "masquerade": int(row.get("risk_masquerade", 1) or 1),
                "si": int(row.get("risk_si", 1) or 1),
            }

            zones[key] = {
                "key": key,
                "name": row.get("name", "") or key,
                "description": row.get("description", ""),
                "tags": tags,
                "encounter_table": row.get("encounter_table", ""),
                "base_risk": base_risk,
                "region": row.get("region", ""),
                "lat": float(row.get("lat") or 0.0),
                "lng": float(row.get("lng") or 0.0),
                "faction": row.get("faction", ""),
                "hunting_risk": int(row.get("hunting_risk", 0) or 0),
                "si_risk": int(row.get("si_risk", 0) or 0),
                "travel_difficulty": int(row.get("travel_difficulty", 1) or 1),
                # This will be populated by any map rows for this zone
                "mymaps": [],
            }

        # Each row can optionally add a map entry for this zone.
        map_entry = {
            "map_name": row.get("map_name", ""),
            "layer": row.get("map_layer", ""),
            "label": row.get("map_label", ""),
            "url": row.get("map_url", ""),
        }

        if map_entry["map_name"] or map_entry["url"]:
            zones[key]["mymaps"].append(map_entry)

    return zones


def save_zones_file(zones: Dict[str, dict], path: str = ZONES_JSON_PATH) -> None:
    """
    Writes zones.json to disk as a flat list[zone].

    This is what `ZoneRegistry.load_from_json` expects.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(list(zones.values()), f, indent=4, ensure_ascii=False)


if __name__ == "__main__":
    # Simple CLI usage:
    #   python -m core.travel.sheets_loader
    # to pull from the configured sheet and write data/zones.json
    zones = load_sheet_zones()
    save_zones_file(zones)
    print(f"Synced {len(zones)} zones to {ZONES_JSON_PATH}")