from __future__ import annotations

import os
from typing import Dict, Any, List, Optional

from utils import (
    generate_storyteller_response,
    generate_random_encounter,
    score_encounter_severity,
    apply_director_reaction_from_encounter,
    populate_location_npcs,
)

from core.vtmv5 import character_model
from core.director.state import DirectorState
from core.director.director import V5DirectorAdapter


# Path to V5-aware director_state.json (separate from legacy director_system)
DIRECTOR_STATE_PATH = os.path.join(os.path.dirname(__file__), "director_state.json")

# Shared DirectorState + V5 adapter, importable by other modules (hunting, travel, etc.)
_DIRECTOR_STATE = DirectorState(DIRECTOR_STATE_PATH)
_V5_DIRECTOR = V5DirectorAdapter(_DIRECTOR_STATE)


class AIDirector:
    """
    High-level AI Director orchestrator.

    This class:
      - Pulls V5 context (Humanity, Stains, Hunger, Predator Type, Merits/Flaws, Touchstones)
      - Reads global director_state.json via DirectorState
      - Calls your AI helpers (generate_storyteller_response, generate_random_encounter, etc.)
      - Returns a unified scene payload:

        {
          "intro_text": str,
          "npcs": [...],
          "encounter": {...} or None,
          "quest_hook": str or "",
          "severity": int or None,        # 1–5
          "severity_label": str or None,  # "low", "guarded", "tense", "critical", "apocalyptic"
          "director_update": {...},       # updated director state snapshot
        }
    """

    @staticmethod
    def _severity_label(level: int) -> str:
        if level <= 1:
            return "low"
        elif level == 2:
            return "guarded"
        elif level == 3:
            return "tense"
        elif level == 4:
            return "critical"
        else:
            return "apocalyptic"

    @staticmethod
    def _build_director_context(
        guild_data: Dict[str, Any],
        travelers: List[Any],
    ) -> Dict[str, Any]:
        """
        Build a V5-aware director context based on the first traveling character.
        """
        if not travelers:
            return _V5_DIRECTOR.global_scene_directives()

        players_map = (guild_data.get("players") or {}) if isinstance(guild_data, dict) else {}
        primary = travelers[0]

        if not isinstance(primary, dict):
            primary = players_map.get(str(primary), {})

        character_model.ensure_character_state(primary)
        return _V5_DIRECTOR.scene_directives_for_player(primary)

    @staticmethod
    async def generate_scene(
        model_text,
        model_json,
        guild_data: Dict[str, Any],
        guild_id: int,
        location_key: str,
        travelers: List[Any],
        risk: int = 2,
        tags: Optional[List[str]] = None,
        director_state: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Unified scene-generation engine.
        """
        tags = tags or []

        director_context = AIDirector._build_director_context(guild_data, travelers)
        city_state = director_context.get("city_state", {})
        personal = director_context.get("personal", {})

        global_threat = city_state.get("global_threat", 1)
        personal_threat = personal.get("personal_threat", 1)

        severity = max(global_threat, personal_threat, int(risk or 1))
        severity_label = AIDirector._severity_label(severity)

        # 2) NPCs
        try:
            npcs = await populate_location_npcs(
                model_json,
                location_key,
                guild_data,
            )
        except TypeError:
            try:
                npcs = await populate_location_npcs(model_json, location_key)
            except Exception:
                npcs = []
        except Exception:
            npcs = []

        if npcs is None:
            npcs = []

        # 3) Encounter
        encounter = None
        encounter_severity = None
        encounter_reaction = None

        try:
            encounter = await generate_random_encounter(
                model_json=model_json,
                guild_data=guild_data,
                guild_id=guild_id,
                location_key=location_key,
                travelers=travelers,
                director_context=director_context,
                tags=tags,
            )
        except TypeError:
            try:
                encounter = await generate_random_encounter(
                    model_json,
                    location_key,
                    guild_data,
                )
            except Exception:
                encounter = None
        except Exception:
            encounter = None

        if encounter:
            try:
                encounter_severity = score_encounter_severity(
                    encounter,
                    director_context,
                )
            except TypeError:
                try:
                    encounter_severity = score_encounter_severity(encounter)
                except Exception:
                    encounter_severity = None

            try:
                encounter_reaction = await apply_director_reaction_from_encounter(
                    model_json=model_json,
                    director_data=_DIRECTOR_STATE.data,
                    encounter=encounter,
                    guild_data=guild_data,
                    guild_id=guild_id,
                )
                _DIRECTOR_STATE.save()
            except TypeError:
                try:
                    encounter_reaction = await apply_director_reaction_from_encounter(
                        _DIRECTOR_STATE.data,
                        encounter,
                        guild_data,
                        guild_id,
                    )
                    _DIRECTOR_STATE.save()
                except Exception:
                    encounter_reaction = None
            except Exception:
                encounter_reaction = None

            if isinstance(encounter_severity, int):
                severity = max(severity, encounter_severity)
                severity_label = AIDirector._severity_label(severity)

        # 4) Storyteller intro text
        quest_hook = ""
        intro_text = ""

        prompt_context = {
            "guild_id": guild_id,
            "location_key": location_key,
            "travelers": travelers,
            "npcs": npcs,
            "encounter": encounter,
            "severity": severity,
            "severity_label": severity_label,
            "director_context": director_context,
            "tags": tags,
        }

        try:
            intro_payload = await generate_storyteller_response(
                model_text=model_text,
                context=prompt_context,
            )
            if isinstance(intro_payload, str):
                intro_text = intro_payload
            elif isinstance(intro_payload, dict):
                intro_text = intro_payload.get("intro_text") or intro_payload.get("text") or ""
                quest_hook = intro_payload.get("quest_hook") or ""
        except TypeError:
            try:
                intro_payload = await generate_storyteller_response(
                    model_text,
                    guild_data,
                    guild_id,
                    location_key,
                    travelers,
                    npcs=npcs,
                    encounter=encounter,
                    severity=severity,
                    severity_label=severity_label,
                    tags=tags,
                )
                if isinstance(intro_payload, str):
                    intro_text = intro_payload
                elif isinstance(intro_payload, dict):
                    intro_text = intro_payload.get("intro_text") or intro_payload.get("text") or ""
                    quest_hook = intro_payload.get("quest_hook") or ""
            except Exception:
                intro_text = "The night moves, but the Director cannot find the words."
                quest_hook = ""
        except Exception:
            intro_text = "The night moves, but the Director cannot find the words."
            quest_hook = ""

        director_update = _DIRECTOR_STATE.summarize()

        return {
            "intro_text": intro_text,
            "npcs": npcs,
            "encounter": encounter,
            "quest_hook": quest_hook,
            "severity": severity,
            "severity_label": severity_label,
            "director_update": director_update,
            "encounter_reaction": encounter_reaction,
        }