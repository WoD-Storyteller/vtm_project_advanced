from __future__ import annotations

import random
from typing import Dict, Any

from .character_model import (
    ensure_character_state,
    get_humanity,
    set_humanity,
    get_stains,
    set_stains,
    list_touchstones,
)
from . import merits_flaws


def apply_stain(player: Dict[str, Any], amount: int = 1):
    ensure_character_state(player)
    set_stains(player, get_stains(player) + amount)


def apply_conviction_violation(player: Dict[str, Any], severity: int = 1):
    """
    When a Conviction is violated, typically the character gains 1 or more Stains.
    """
    ensure_character_state(player)
    apply_stain(player, amount=severity)


def apply_touchstone_loss(player: Dict[str, Any], name: str, deliberate: bool = True):
    """
    Mark a touchstone dead and apply Stains depending on whether the loss was deliberate.
    """
    from . import character_model  # local import

    ensure_character_state(player)
    character_model.mark_touchstone_dead(player, name)

    # RAW is flexible; here's a solid baseline:
    # - If deliberate or clearly your fault: +2 Stains
    # - Otherwise: +1 Stain
    severity = 2 if deliberate else 1
    apply_stain(player, amount=severity)


def _remorse_pool_base(player: Dict[str, Any]) -> int:
    """
    Base dice pool for remorse:
      - Use 10 - Humanity, minimum 1, maximum 5
    """
    humanity = get_humanity(player)
    pool = max(1, min(5, 10 - humanity))
    return pool


def _remorse_modifiers_from_merits_flaws(player: Dict[str, Any]) -> int:
    """
    Returns a dice modifier for the remorse pool based on merits & flaws.
    Positive = bonus dice, Negative = penalty.
    """
    m_tags = merits_flaws.merit_tags_for_player(player)
    f_tags = merits_flaws.flaw_tags_for_player(player)

    mod = 0

    # Merits
    if "remorse_bonus" in m_tags:
        mod += 1  # feels guilt more strongly / is better at remorse
    if "stain_sensitivity" in m_tags:
        mod += 1  # more attuned to moral injury

    # Flaws
    if "remorse_penalty" in f_tags:
        mod -= 1
    if "frenzy_prone" in f_tags:
        # doesn't necessarily affect remorse dice, but we make them slightly worse at reflecting
        mod -= 0

    return mod


def _remorse_modifiers_from_touchstones(player: Dict[str, Any]) -> int:
    """
    Touchstones make remorse more likely: the more living touchstones you have,
    the easier it is to feel the weight of your actions.
    """
    tstones = list_touchstones(player)
    alive_count = sum(1 for t in tstones if t.get("alive", True))

    if alive_count == 0:
        return 0
    elif alive_count == 1:
        return 1
    elif alive_count >= 2:
        return 2


def remorse_roll(player: Dict[str, Any]) -> Dict[str, Any]:
    """
    V5-style remorse:
      - Pool roughly = (10 - Humanity), modified by merits/flaws/touchstones
      - If any success, you feel remorse: keep Humanity, clear Stains.
      - Else: lose 1 Humanity, clear Stains.

    This implementation automatically incorporates:
      - certain merits (e.g. Iron Will, Stoic, Empathetic via tags)
      - flaws (e.g. Remorseless, Cold-Blooded)
      - number of living touchstones
    """
    ensure_character_state(player)

    humanity = get_humanity(player)
    stains = get_stains(player)

    base_pool = _remorse_pool_base(player)
    mod_merits_flaws = _remorse_modifiers_from_merits_flaws(player)
    mod_touchstones = _remorse_modifiers_from_touchstones(player)

    pool = base_pool + mod_merits_flaws + mod_touchstones
    pool = max(1, min(10, pool))

    rolls = [random.randint(1, 10) for _ in range(pool)]
    successes = sum(1 for r in rolls if r >= 6)

    remorse = successes > 0

    if remorse:
        # You keep Humanity; stains are cleared.
        set_stains(player, 0)
    else:
        # Lose 1 Humanity, clear stains.
        set_humanity(player, humanity - 1)
        set_stains(player, 0)

    return {
        "rolled": rolls,
        "successes": successes,
        "remorse": remorse,
        "final_humanity": get_humanity(player),
        "final_stains": get_stains(player),
        "previous_humanity": humanity,
        "previous_stains": stains,
        "pool": pool,
        "base_pool": base_pool,