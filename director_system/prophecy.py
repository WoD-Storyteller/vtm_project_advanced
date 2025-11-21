from dataclasses import dataclass, field
from typing import List, Dict, Any
from .state import DirectorState, save_director_state, get_director_state

@dataclass
class DirectorProphecyThread:
    """Represents an ongoing narrative arc the Director is nudging.

    Each thread tracks:
    - id: short identifier
    - name: evocative title
    - theme: core theme (occult, politics, masquerade, etc.)
    - progress: how far along the arc is (0-100)
    - notes: freeform description for the Storyteller
    """
    id: str
    name: str
    theme: str
    progress: int = 0
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "theme": self.theme,
            "progress": self.progress,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, raw: Dict[str, Any]) -> "DirectorProphecyThread":
        return cls(
            id=str(raw.get("id")),
            name=str(raw.get("name", "")),
            theme=str(raw.get("theme", "")),
            progress=int(raw.get("progress", 0) or 0),
            notes=str(raw.get("notes", "")),
        )


def ensure_default_prophecy_threads(guild_data: dict):
    """Ensure there are at least a few default prophecy threads in the director state."""
    state = get_director_state(guild_data)
    if state.prophecy_threads:
        return state

    defaults = [
        DirectorProphecyThread(
            id="arc_occult_1",
            name="Whispers Beneath the Cobblestones",
            theme="occult",
            notes="Strange rites occur in forgotten basements and storm drains.",
        ),
        DirectorProphecyThread(
            id="arc_masq_1",
            name="Eyes in the Crowd",
            theme="masquerade",
            notes="Cameras, podcasts, conspiracy forums; the city is watching.",
        ),
        DirectorProphecyThread(
            id="arc_politics_1",
            name="Blood on the Ballot",
            theme="politics",
            notes="An election or appointment will tilt power among the Damned.",
        ),
    ]
    state.prophecy_threads = [t.to_dict() for t in defaults]
    save_director_state(guild_data, state)
    return state


def nudge_prophecy_by_theme(guild_data: dict, theme: str, amount: int = 1):
    """Increment progress on any prophecy threads sharing this theme."""
    state = get_director_state(guild_data)
    if not state.prophecy_threads:
        ensure_default_prophecy_threads(guild_data)
        state = get_director_state(guild_data)

    changed = False
    for raw in state.prophecy_threads:
        if raw.get("theme") == theme:
            raw["progress"] = int(raw.get("progress", 0)) + amount
            changed = True

    if changed:
        save_director_state(guild_data, state)
    return state
