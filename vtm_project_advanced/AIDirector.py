import json
from typing import List
from utils import generate_storyteller_response, populate_location_npcs
from director_system.state import get_director_state, save_director_state
from director_system.engine import apply_encounter_to_director
from director_system.prophecy import nudge_prophecy_by_theme

class AIDirector:
    """Self-aware scene generator that consults a persistent DirectorState.

    This version:
    - Reads Director awareness/themes from guild_data
    - Uses that to slightly bias how 'hot' a scene feels
    - When an encounter is later attached and logged, other systems
      should call apply_encounter_to_director(...) to evolve the state.
    """

    @staticmethod
    async def generate_scene(
        model_text,
        model_json,
        guild_data,
        guild_id,
        location_key: str,
        travelers: List[object],
        risk: int = 2,
        tags=None,
    ):
        tags = tags or []
        tags_lower = [str(t).lower() for t in tags]

        # Director awareness / themes
        director = get_director_state(guild_data)
        awareness = director.awareness
        dominance_theme = None
        if director.themes:
            dominance_theme = max(director.themes.items(), key=lambda kv: kv[1])[0]

        # Build an instruction string for the model to convey the city's mood
        directive_bits = []
        directive_bits.append(f"Director awareness: {awareness}/10.")
        if dominance_theme:
            directive_bits.append(f"Dominant city theme: {dominance_theme}.")
        if tags_lower:
            directive_bits.append(f"Local tags: {', '.join(tags_lower)}.")

        directive = " ".join(directive_bits)

        # Auto-populate NPCs at this location
        npcs = await populate_location_npcs(model_json, location_key, guild_data)
        if npcs is None:
            npcs = []

        # Intro narration influenced by Director
        intro_prompt = (
            f"Describe the location '{location_key}' for Vampire: the Masquerade. "
            "Tone: gothic, moody, urban horror. 2-4 sentences, include sensory detail. "
            f"Keep in mind: {directive}"
        )
        intro_text = await generate_storyteller_response(
            model_text,
            [],
            intro_prompt,
            guild_data,
            guild_id,
        )

        # Nudge prophecy threads slightly by the dominant theme, if present
        if dominance_theme:
            nudge_prophecy_by_theme(guild_data, dominance_theme, amount=1)
            director = get_director_state(guild_data)

        save_director_state(guild_data, director)

        # This version does not itself generate the encounter; it focuses on scene tone
        # and city/self-awareness. Encounters can be generated via a separate system
        # and then passed into director_system.engine.apply_encounter_to_director.
        return {
            "intro_text": intro_text,
            "npcs": npcs,
            "encounter": None,
            "quest_hook": "",
            "severity": None,
            "severity_label": None,
            "director_update": director.to_dict(),
        }
