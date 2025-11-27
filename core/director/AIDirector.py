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


# Path to director_state.json (same folder as this file)
DIRECTOR_STATE_PATH = os.path.join(os.path.dirname(__file__), "director_state.json")

# Single shared DirectorState + V5-aware adapter
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

        `travelers` is expected to be either:
          - list of player dicts, or
          - list of player IDs that can be resolved from guild_data['players']

        We keep it defensive and just do our best with what's available.
        """
        if not travelers:
            # no specific PC focus; return global city state only
            return _V5_DIRECTOR.global_scene_directives()

        players_map = (guild_data.get("players") or {}) if isinstance(guild_data, dict) else {}
        primary = travelers[0]

        # If it's an ID, try to resolve
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

        Args:
          model_text:   LLM for narrative text
          model_json:   LLM for structured JSON
          guild_data:   full guild data store
          guild_id:     Discord guild id
          location_key: current location/zone key
          travelers:    list of PCs (dicts or ids)
          risk:         base risk (1–5) from travel or ST
          tags:         semantic tags for scene (["combat", "elysium", ...])
          director_state: (optional) legacy director state dict (ignored now, kept for compatibility)

        Returns:
          {
            "intro_text": str,
            "npcs": [...],
            "encounter": {...} or None,
            "quest_hook": str or "",
            "severity": int or None,
            "severity_label": str or None,
            "director_update": {...} or None,
          }
        """
        tags = tags or []

        # 1) Build V5-aware context for the scene
        director_context = AIDirector._build_director_context(guild_data, travelers)
        city_state = director_context.get("city_state", {})
        personal = director_context.get("personal", {})

        global_threat = city_state.get("global_threat", 1)
        personal_threat = personal.get("personal_threat", 1)

        # Basic severity heuristic
        severity = max(global_threat, personal_threat, int(risk or 1))
        severity_label = AIDirector._severity_label(severity)

        # 2) NPCs for this location
        try:
            npcs = await populate_location_npcs(
                model_json,
                location_key,
                guild_data,
            )
        except TypeError:
            # fallback if your populate_location_npcs has fewer parameters
            npcs = await populate_location_npcs(model_json, location_key)
        except Exception:
            npcs = []

        if npcs is None:
            npcs = []

        # 3) Optional encounter
        encounter = None
        encounter_severity = None
        encounter_reaction = None

        try:
            # Most flexible attempt: pass as much context as possible
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
            # Simpler fallback signatures if your util is older
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
            # Score severity if your util supports it
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

            # Allow legacy reaction hook to mutate director_state.json-like data
            try:
                encounter_reaction = await apply_director_reaction_from_encounter(
                    model_json=model_json,
                    director_data=_DIRECTOR_STATE.data,
                    encounter=encounter,
                    guild_data=guild_data,
                    guild_id=guild_id,
                )
                # If the legacy function mutated the dict, we persist
                _DIRECTOR_STATE.save()
            except TypeError:
                # Simpler call fallback
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

            # Adjust severity upwards if encounter is nasty
            if isinstance(encounter_severity, int):
                severity = max(severity, encounter_severity)
                severity_label = AIDirector._severity_label(severity)

        # 4) Ask the storyteller model for intro text (scene narration)
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
            # Allow intro_payload to be either string or dict
            if isinstance(intro_payload, str):
                intro_text = intro_payload
            elif isinstance(intro_payload, dict):
                intro_text = intro_payload.get("intro_text") or intro_payload.get("text") or ""
                quest_hook = intro_payload.get("quest_hook") or ""
        except TypeError:
            # older signature: (model_text, guild_data, guild_id, location_key, travelers, **kwargs)
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

        # 5) Final director snapshot
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