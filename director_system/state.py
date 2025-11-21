from dataclasses import dataclass, field
from typing import Dict, List, Any
import copy

@dataclass
class DirectorState:
    """Represents the 'self-aware' city-scale Director AI.

    awareness: how 'awake' the city is to trouble (0-5+)
    influence: buckets tracking pressure in different themes
    themes: running tallies per theme (violence, occult, masquerade, politics, etc.)
    prophecy_threads: long-running narrative arcs
    """
    awareness: int = 0
    influence: Dict[str, int] = field(default_factory=dict)
    themes: Dict[str, int] = field(default_factory=dict)
    prophecy_threads: List[Dict[str, Any]] = field(default_factory=list)

    def bump_theme(self, theme: str, amount: int = 1):
        theme = theme.lower()
        self.themes[theme] = self.themes.get(theme, 0) + amount

    def bump_influence(self, key: str, amount: int = 1):
        key = key.lower()
        self.influence[key] = self.influence.get(key, 0) + amount

    def clamp_awareness(self, minimum: int = 0, maximum: int = 10):
        self.awareness = max(minimum, min(maximum, self.awareness))

    @classmethod
    def from_guild(cls, guild_data: dict) -> "DirectorState":
        raw = guild_data.get("director", {})
        return cls(
            awareness=int(raw.get("awareness", 0) or 0),
            influence=copy.deepcopy(raw.get("influence", {}) or {}),
            themes=copy.deepcopy(raw.get("themes", {}) or {}),
            prophecy_threads=copy.deepcopy(raw.get("prophecy_threads", []) or []),
        )

    def to_dict(self) -> dict:
        return {
            "awareness": int(self.awareness),
            "influence": dict(self.influence),
            "themes": dict(self.themes),
            "prophecy_threads": list(self.prophecy_threads),
        }


def get_director_state(guild_data: dict) -> DirectorState:
    return DirectorState.from_guild(guild_data)


def save_director_state(guild_data: dict, state: DirectorState):
    guild_data["director"] = state.to_dict()
