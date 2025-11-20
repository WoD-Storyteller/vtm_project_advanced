from typing import Dict, Any, List
from .state import DirectorState, get_director_state, save_director_state

THEMES_FROM_TYPES = {
    "combat": "violence",
    "social": "politics",
    "investigation": "mystery",
    "supernatural": "occult",
    "masquerade": "masquerade",
}

def apply_encounter_to_director(guild_data: Dict[str, Any], encounter: Dict[str, Any]):
    """Update director awareness/influence/themes based on a single encounter.

    This is intended to be called whenever an encounter is logged.
    """
    if not encounter:
        return

    state = get_director_state(guild_data)
    etype = (encounter.get("type") or "").lower()
    severity = int(encounter.get("severity") or 0)
    tags: List[str] = [str(t).lower() for t in encounter.get("tags", [])]

    # Bump base awareness by severity
    if severity > 0:
        state.awareness += max(1, severity // 2)

    # Thematic bump
    base_theme = THEMES_FROM_TYPES.get(etype)
    if base_theme:
        state.bump_theme(base_theme, max(1, severity))

    if "masquerade" in etype or "masquerade" in tags:
        state.bump_theme("masquerade", max(1, severity))
        state.bump_influence("masquerade", max(1, severity))

    if "supernatural" in etype or "occult" in tags or "ritual" in tags:
        state.bump_theme("occult", max(1, severity))
        state.bump_influence("occult", max(1, severity - 1))

    if "si" in tags or "second inquisition" in tags:
        state.bump_theme("second_inquisition", max(1, severity))
        state.bump_influence("second_inquisition", max(1, severity))

    # clamp awareness
    state.clamp_awareness(0, 10)
    save_director_state(guild_data, state)


def director_night_tick(guild_data: Dict[str, Any]):
    """Advance the Director's city-scale logic by one 'night'.

    - Slightly cools or heats themes
    - Gently shifts influence
    - Can be used to spawn prophecy events (handled elsewhere)
    """
    state = get_director_state(guild_data)
    # Cool down all themes slightly to avoid runaway explosion
    cooled = {}
    for k, v in state.themes.items():
        nv = v - 1 if v > 0 else v
        cooled[k] = nv
    state.themes = cooled

    # Awareness naturally drifts towards 1-3
    if state.awareness > 3:
        state.awareness -= 1
    elif state.awareness < 1:
        state.awareness += 1

    state.clamp_awareness(0, 10)
    save_director_state(guild_data, state)
    return state
