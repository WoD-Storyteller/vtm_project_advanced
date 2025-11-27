from __future__ import annotations

import random
from typing import Dict, Any, Optional


# -------------------------------------------------------
# BASIC TEMPLATE ENCOUNTER TABLES
# Expand these freely or load from JSON if preferred.
# -------------------------------------------------------

ENCOUNTER_TABLES = {
    "urban_camarilla": [
        {"text": "A watchful Camarilla coterie tailing the PCs.", "severity": 2},
        {"text": "A ghoul courier rushing through the streets.", "severity": 1},
        {"text": "A primogen agent testing your loyalty.", "severity": 3},
    ],

    "anarch_cult": [
        {"text": "A screaming revel of the Dreaming Shore.", "severity": 3},
        {"text": "Lost soul begging for salvation.", "severity": 1},
        {"text": "Cult prophet whispering doom.", "severity": 4},
    ],

    "sabbat_front": [
        {"text": "A Sabbat pack scouting for bodies.", "severity": 4},
        {"text": "A shovelhead testing the waters.", "severity": 3},
        {"text": "The laughter of a Bishop's envoy.", "severity": 5},
    ],

    "elysium": [
        {"text": "Harpy gossip dripping like poison.", "severity": 1},
        {"text": "Keeper's assistant seeking favors.", "severity": 2},
    ],

    "thin_blood_industrial": [
        {"text": "Thin-blood chemists experimenting.", "severity": 2},
        {"text": "A frantic courier offering a dubious serum.", "severity": 3},
    ],

    "ministry_corridor": [
        {"text": "Whispers of Set echo down hollow halls.", "severity": 2},
        {"text": "A smuggler's ritual gone wrong.", "severity": 3},
    ],

    "hecata_necropolis": [
        {"text": "A pale figure beckons from a tunnel.", "severity": 3},
        {"text": "Ghostly echo of past sins.", "severity": 2},
    ],

    "nosferatu_tunnels": [
        {"text": "A Nos sentry lurking in darkness.", "severity": 2},
        {"text": "A flooded chamber full of whispers.", "severity": 3},
    ],

    "chunnel_endgame": [
        {"text": "A Pentex strike team approaching.", "severity": 4},
        {"text": "Sabbat ritual lights the tunnels red.", "severity": 5},
    ],
}


# -------------------------------------------------------
# FUNCTIONS
# -------------------------------------------------------

def roll_encounter(enc_table: str) -> Optional[Dict[str, Any]]:
    """
    Returns a random encounter dict:
      { "text": str, "severity": int }
    """
    table = ENCOUNTER_TABLES.get(enc_table)
    if not table:
        return None
    return random.choice(table)


def is_encounter_triggered(base_risk: Dict[str, int]) -> bool:
    """
    Rolls against violence/masquerade/SI risk.
    If any exceed a threshold, encounters may occur.
    """
    risk_pool = (
        base_risk.get("violence", 1)
        + base_risk.get("masquerade", 1)
        + base_risk.get("si", 1)
    )

    chance = min(90, risk_pool * 10)
    roll = random.randint(1, 100)
    return roll <= chance