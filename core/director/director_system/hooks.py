from __future__ import annotations

from .state import get_director_state, save_director_state


def apply_travel_event(guild_data, zone_key: str, result):
    state = get_director_state(guild_data)

    viol = result.director_impact.get("violence", 0)
    masq = result.director_impact.get("masquerade", 0)
    si = result.director_impact.get("second_inquisition", 0)
    occ = result.director_impact.get("occult", 0)

    state.influence["violence"] += max(0, viol - 1)
    state.influence["masquerade"] += max(0, masq - 1)
    state.influence["second_inquisition"] += si
    state.influence["occult"] += occ

    state.themes["violence"] += viol
    state.themes["masquerade"] += masq
    state.themes["occult"] += occ

    if si > 0 or masq > 0:
        state.awareness += 1

    save_director_state(guild_data, state)