from __future__ import annotations

from typing import Optional

from .state import get_director_state, save_director_state


def apply_combat_event(
    guild_data: dict,
    outcome: str,
    severity: int,
    attacker: str,
    defender: str,
    chaos: Optional[str] = None,
):
    """
    Lightweight adaptor between combat events and the Director state.

    Args:
        guild_data: this guild's data dict (from get_guild_data)
        outcome: string outcome from the dice system:
                 "success", "fail", "messy_critical",
                 "bestial_failure", "bestial_success", etc.
        severity: rough magnitude of the event (e.g. damage or successes)
        attacker: name of attacking combatant
        defender: name of defending combatant
        chaos: optional bestial complication string
    """
    if not outcome:
        return

    state = get_director_state(guild_data)

    # Ensure keys exist
    state.influence.setdefault("violence", 0)
    state.influence.setdefault("masquerade", 0)
    state.themes.setdefault("violence", 0)
    state.themes.setdefault("masquerade", 0)

    o = outcome.lower()
    sev = max(1, int(severity))

    # Baseline: any successful hit nudges violence
    if o not in ("fail", "bestial_failure"):
        state.themes["violence"] += sev

    # Messy Critical: big spike in violence and Masquerade risk
    if o == "messy_critical":
        state.influence["violence"] += 2
        state.influence["masquerade"] += 1
        state.themes["violence"] += sev
        state.themes["masquerade"] += 1
        state.awareness += 1

    # Bestial Failure: Masquerade screw-ups and ugly outcomes
    elif o == "bestial_failure":
        state.influence["masquerade"] += 2
        state.themes["masquerade"] += max(1, sev // 2)
        state.awareness += 1

    # Bestial Success: you win, but the Beast shows
    elif o == "bestial_success":
        state.influence["violence"] += 1
        state.influence["masquerade"] += 1
        state.themes["violence"] += sev
        state.themes["masquerade"] += 1
        state.awareness += 1

    # Plain success (no explicit Beast event)
    elif o == "success":
        state.influence["violence"] += 1

    # Optional: if chaos text exists, treat it as a soft Masquerade bump
    if chaos:
        state.themes["masquerade"] += 1

    # Nudge awareness into a sane band if clamp is available
    if hasattr(state, "clamp_awareness"):
        try:
            state.clamp_awareness(0, 10)
        except TypeError:
            # If signature differs, ignore and move on
            pass

    save_director_state(guild_data, state)