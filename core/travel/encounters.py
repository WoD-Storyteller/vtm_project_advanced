from __future__ import annotations

import random
from typing import Dict, List, Optional


class Encounter:
    def __init__(
        self,
        eid: str,
        name: str,
        kind: str,
        tags: List[str],
        base_severity: int,
        summary: str,
    ):
        self.id = eid
        self.name = name
        self.kind = kind
        self.tags = tags
        self.base_severity = base_severity
        self.summary = summary


ENCOUNTER_TABLES: Dict[str, List[Encounter]] = {}


def _add(table: str, enc: Encounter):
    ENCOUNTER_TABLES.setdefault(table, []).append(enc)


# Canterbury / Camarilla

_add(
    "urban_camarilla",
    Encounter(
        eid="can_cam_ghoul_watch",
        name="Primogen's Ghoul",
        kind="npc",
        tags=["camarilla", "politics"],
        base_severity=2,
        summary="A Camarilla ghoul watches your movements too closely.",
    )
)

_add(
    "urban_camarilla",
    Encounter(
        eid="can_cam_patrol",
        name="Camarilla Patrol",
        kind="npc",
        tags=["camarilla", "security"],
        base_severity=3,
        summary="A small coterie questions your presence in their streets.",
    )
)

# Margate — Anarch Cult

_add(
    "anarch_cult",
    Encounter(
        eid="mar_cult_rite",
        name="Bonfire Rite",
        kind="event",
        tags=["anarch", "cult", "masquerade"],
        base_severity=3,
        summary="A wild rite teeters between revel and riot.",
    )
)


# Folkestone — Sabbat

_add(
    "sabbat_front",
    Encounter(
        eid="fol_sabbat_pack",
        name="Sabbat Scout Pack",
        kind="npc",
        tags=["sabbat", "violence", "warfront"],
        base_severity=4,
        summary="A shovelhead pack sizes you up.",
    )
)


# Dover — Hecata

_add(
    "hecata_necropolis",
    Encounter(
        eid="dov_hec_path",
        name="Silent Funeral Cortege",
        kind="npc",
        tags=["hecata", "occult"],
        base_severity=3,
        summary="A procession of dead and living moves past in eerie silence.",
    )
)


# Thin-Blood Industrial

_add(
    "thin_blood_industrial",
    Encounter(
        eid="tb_heist",
        name="Rail Heist",
        kind="event",
        tags=["thin_blood", "violence"],
        base_severity=4,
        summary="Thin-bloods hijack a freight shipment.",
    )
)


# Ministry Corridor

_add(
    "ministry_corridor",
    Encounter(
        eid="min_smuggling",
        name="Smuggling Run",
        kind="event",
        tags=["ministry", "crime", "masquerade"],
        base_severity=3,
        summary="Cargo moves with more than mundane danger.",
    )
)


# Nosferatu Tunnels

_add(
    "nosferatu_tunnels",
    Encounter(
        eid="nos_broker",
        name="Nosferatu Info-Broker",
        kind="npc",
        tags=["nosferatu", "information"],
        base_severity=2,
        summary="Secrets traded in dripping dark tunnels.",
    )
)


# Chunnel — Endgame

_add(
    "chunnel_endgame",
    Encounter(
        eid="chun_sabbat_ops",
        name="Sabbat Logistics Node",
        kind="npc",
        tags=["sabbat", "endgame", "warfront"],
        base_severity=5,
        summary="You glimpse preparations for something catastrophic.",
    )
)


def roll_encounter(table_key: str, danger_bonus: int = 0) -> Optional[Encounter]:
    table = ENCOUNTER_TABLES.get(table_key, [])
    if not table:
        return None

    weighted = []
    for enc in table:
        weighted.extend([enc] * (enc.base_severity + danger_bonus))

    return random.choice(weighted)