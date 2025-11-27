from __future__ import annotations

from typing import Any, Dict, Optional

from director_system.state import get_director_state, save_director_state


def _ensure_director_basics(state: Any):
    """
    Ensure influence/themes/awareness keys exist.
    """
    if not hasattr(state, "influence"):
        state.influence = {}
    if not hasattr(state, "themes"):
        state.themes = {}
    if not hasattr(state, "awareness"):
        state.awareness = 0

    state.influence.setdefault("violence", 0)
    state.influence.setdefault("masquerade", 0)
    state.influence.setdefault("occult", 0)
    state.influence.setdefault("politics", 0)
    state.influence.setdefault("second_inquisition", 0)

    state.themes.setdefault("violence", 0)
    state.themes.setdefault("masquerade", 0)
    state.themes.setdefault("occult", 0)
    state.themes.setdefault("politics", 0)
    state.themes.setdefault("mystery", 0)


def apply_combat_event(
    guild_data: Dict[str, Any],
    outcome: str,
    severity: int,
    messy: bool = False,
    bestial: bool = False,
):
    """
    Example combat hook (kept minimal so it doesn't break your existing stuff).
    You can expand with more detailed combat outcome mapping.
    """
    state = get_director_state(guild_data)
    _ensure_director_basics(state)

    sev = max(1, int(severity))

    if messy:
        state.influence["violence"] += sev
        state.influence["masquerade"] += 1
        state.themes["violence"] += sev
        state.themes["masquerade"] += 1
        state.awareness += 1
    elif bestial:
        state.influence["masquerade"] += 2
        state.themes["masquerade"] += sev
        state.awareness += 1
    else:
        # normal success/fail just nudges violence
        if outcome.lower() in ("hit", "success", "win"):
            state.influence["violence"] += 1
            state.themes["violence"] += sev

    save_director_state(guild_data, state)


def apply_travel_event(
    guild_data: Dict[str, Any],
    zone,
    encounter: Optional[Dict[str, Any]],
    time_info: Dict[str, Any],
):
    """
    Hook travel outcomes into Director state.

    zone: Zone
    encounter: {text, severity} or None
    time_info result from advance_time:
       {
         "time_state": ...,
         "crossed_sunrise": bool,
         "near_sunrise": bool
       }
    """
    state = get_director_state(guild_data)
    _ensure_director_basics(state)

    sev = 0
    if encounter:
        sev = int(encounter.get("severity", 1))

    # Base impact from encounters by zone risk
    if encounter:
        # Violence-heavy tables
        if "sabbat" in (zone.tags or []) or "warfront" in (zone.tags or []):
            state.influence["violence"] += sev
            state.themes["violence"] += sev

        # Masquerade risk for urban/crowded/etc.
        if "urban" in (zone.tags or []) or "masquerade" in (zone.tags or []):
            state.influence["masquerade"] += max(1, sev - 1)
            state.themes["masquerade"] += 1

        # SI / Pentex tags
        if "second_inquisition" in (zone.tags or []) or "si" in (zone.tags or []) \
           or "pentex" in (zone.tags or []):
            state.influence["second_inquisition"] += sev
            state.awareness += 1

        # Occult stuff
        if "occult" in (zone.tags or []) or "mystery" in (zone.tags or []):
            state.influence["occult"] += 1
            state.themes["occult"] += 1

    # Sunrise risk
    if time_info.get("crossed_sunrise"):
        # Doing anything past sunrise is BAD
        state.influence["masquerade"] += 2
        state.influence["second_inquisition"] += 2
        state.themes["masquerade"] += 2
        state.awareness += 2
    elif time_info.get("near_sunrise"):
        # Near sunrise = tension rises
        state.themes["masquerade"] += 1
        state.awareness += 1

    save_director_state(guild_data, state)