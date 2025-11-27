from __future__ import annotations

from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse

from core.travel.zones_loader import ZoneRegistry
from utils import get_guild_data
from director_system.state import get_director_state

router = APIRouter()


def get_zone_registry(request: Request) -> ZoneRegistry:
    return request.app.state.zone_registry


@router.get("/api/map/zones")
async def api_map_zones(request: Request, registry: ZoneRegistry = Depends(get_zone_registry)):
    """
    Returns all zones as a lightweight JSON for map display.
    Fog-of-war can be implemented later by filtering based on user/session.
    """
    zones = []
    for z in registry.list():
        zones.append({
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
        })
    return JSONResponse(zones)


@router.get("/api/map/players")
async def api_map_players(request: Request):
    """
    Returns player markers for the map.
    Each player's marker is placed at the center of their current zone.
    """
    app = request.app
    # assume single-guild for dashboard, or choose a default guild id
    guild_id = app.state.default_guild_id

    g_data = get_guild_data(app.state.data_store, guild_id)
    registry: ZoneRegistry = app.state.zone_registry

    markers = []
    for pid, pdata in g_data.get("players", {}).items():
        loc_key = pdata.get("location_key") or registry.default_zone_key()
        zone = registry.get(loc_key)
        if not zone:
            continue

        markers.append({
            "player_id": pid,
            "name": pdata.get("name", f"Player {pid}"),
            "zone_key": zone.key,
            "zone_name": zone.name,
            "lat": zone.lat,
            "lng": zone.lng,
            "clan": pdata.get("clan", "Unknown"),
            "faction": pdata.get("faction", zone.faction or "Unknown"),
        })

    return JSONResponse(markers)


@router.get("/api/map/state")
async def api_map_state(request: Request):
    """
    Returns Director state relevant to global threats / heatmaps.
    """
    app = request.app
    guild_id = app.state.default_guild_id
    g_data = get_guild_data(app.state.data_store, guild_id)
    state = get_director_state(g_data)

    return JSONResponse({
        "awareness": getattr(state, "awareness", 0),
        "influence": state.influence,
        "themes": state.themes,
    })