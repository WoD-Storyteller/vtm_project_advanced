from __future__ import annotations

from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse

from core.travel.zones_loader import ZoneRegistry
from utils import get_guild_data
from director_system.state import get_director_state

router = APIRouter()


def get_zone_registry(request: Request) -> ZoneRegistry:
    """
    Dependency to access the global ZoneRegistry stored on the app.
    Make sure you set `app.state.zone_registry` in your main FastAPI app.
    """
    return request.app.state.zone_registry


@router.get("/api/map/zones")
async def api_map_zones(
    request: Request,
    registry: ZoneRegistry = Depends(get_zone_registry),
):
    """
    Returns all zones as a lightweight JSON list for the map viewer.

    Each zone object:
    {
      "key": str,
      "name": str,
      "description": str,
      "tags": [str],
      "region": str,
      "lat": float,
      "lng": float,
      "faction": str,
      "hunting_risk": int,
      "si_risk": int
    }
    """
    zones = []
    for z in registry.list():
        zones.append(
            {
                "key": z.key,
                "name": z.name,
                "description": z.description,
                "tags": z.tags,
                "region": z.region,
                "lat": z.lat,
                "lng": z.lng,
                "faction": z.faction,
                "hunting_risk": z.hunting_risk,
                "si_risk": z.si_risk,
            }
        )
    return JSONResponse(zones)


@router.get("/api/map/players")
async def api_map_players(request: Request):
    """
    Returns player markers for the map.

    Each marker:
    {
      "player_id": str,
      "name": str,
      "zone_key": str,
      "zone_name": str,
      "lat": float,
      "lng": float,
      "clan": str,
      "faction": str
    }

    Assumes:
      - `app.state.default_guild_id` is set to a guild ID
      - `app.state.data_store` compatible with get_guild_data
      - `app.state.zone_registry` is a ZoneRegistry
    """
    app = request.app
    guild_id = getattr(app.state, "default_guild_id", None)
    if guild_id is None:
        return JSONResponse([], status_code=200)

    registry: ZoneRegistry = app.state.zone_registry
    data_store = app.state.data_store

    g_data = get_guild_data(data_store, guild_id)

    markers = []
    for pid, pdata in g_data.get("players", {}).items():
        loc_key = pdata.get("location_key") or registry.default_zone_key()
        zone = registry.get(loc_key)
        if not zone:
            continue

        markers.append(
            {
                "player_id": pid,
                "name": pdata.get("name", f"Player {pid}"),
                "zone_key": zone.key,
                "zone_name": zone.name,
                "lat": zone.lat,
                "lng": zone.lng,
                "clan": pdata.get("clan", "Unknown"),
                "faction": pdata.get("faction", zone.faction or "Unknown"),
            }
        )

    return JSONResponse(markers)


@router.get("/api/map/state")
async def api_map_state(request: Request):
    """
    Returns Director state relevant to global threats / heatmaps.

    Response:
    {
      "awareness": int,
      "influence": {...},
      "themes": {...}
    }
    """
    app = request.app
    guild_id = getattr(app.state, "default_guild_id", None)
    if guild_id is None:
        return JSONResponse(
            {"awareness": 0, "influence": {}, "themes": {}},
            status_code=200,
        )

    data_store = app.state.data_store
    g_data = get_guild_data(data_store, guild_id)
    state = get_director_state(g_data)

    return JSONResponse(
        {
            "awareness": getattr(state, "awareness", 0),
            "influence": state.influence,
            "themes": state.themes,
        }
    )