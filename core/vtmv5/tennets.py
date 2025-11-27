from __future__ import annotations

from typing import Dict, Any, List


def get_chronicle_tenets(guild_data: Dict[str, Any]) -> List[str]:
    return guild_data.get("chronicle_tenets", [])


def set_chronicle_tenets(guild_data: Dict[str, Any], tenets: List[str]):
    guild_data["chronicle_tenets"] = list(tenets)


def get_convictions(player: Dict[str, Any]) -> List[str]:
    return player.get("convictions", [])


def set_convictions(player: Dict[str, Any], convictions: List[str]):
    player["convictions"] = list(convictions)