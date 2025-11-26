# core/director/AIDirector.py

from pathlib import Path
import json

from core.utils import load_json, save_json
from core.director.director_system.prophecy import resolve_prophecy
from core.director.director_system.npc_generator import generate_npcs


class AIDirector:
    """
    Central AI storytelling engine.
    Tracks awareness, themes, prophecy threads, encounters, etc.
    """

    def __init__(self):
        self.state_file = "director_state.json"
        self.state = load_json(self.state_file, default=self._default_state())

    def _default_state(self):
        return {
            "awareness": 0,
            "influence": {
                "masquerade": 0,
                "violence": 0,
                "occult": 0,
                "politics": 0,
                "second_inquisition": 0
            },
            "themes": {
                "violence": 5,
                "occult": 5,
                "masquerade": 5,
                "politics": 5,
                "mystery": 5
            },
            "prophecy_threads": []
        }

    def save(self):
        save_json(self.state_file, self.state)

    # --------------------
    # SCENE GENERATION
    # --------------------

    def generate_scene(self, location: str, travelers=None, risk: int = 2):
        travelers = travelers or []

        npcs = generate_npcs(location, count=2)
        prophecy = resolve_prophecy(self.state)

        scene_text = (
            f"You arrive at **{location}**.\n"
            f"Two figures are nearby: {', '.join(npcs)}.\n"
            f"Prophecy whispers: {prophecy}\n"
        )

        return {
            "intro_text": scene_text,
            "npcs": npcs,
            "prophecy": prophecy,
            "severity": risk
        }
