import discord
from discord.ext import commands
import traceback

from core.director.ai_director import AIDirector
from utils import get_guild_data


class StorytellerCog(commands.Cog):
    """
    Master Storyteller command set.

    Commands:
      !scene        – Players request a new scene in their current location
      !stscene      – Storyteller manually triggers a scene
      !stforce      – Force a scene with custom risk/tags
    """

    def __init__(self, bot):
        self.bot = bot

    async def build_scene_embed(self, ctx, scene):
        """
        Unified embed builder for scene results.
        """
        intro = scene.get("intro_text") or "No intro text."
        npcs = scene.get("npcs") or []
        encounter = scene.get("encounter")
        quest_hook = scene.get("quest_hook") or ""
        severity = scene.get("severity") or 1
        severity_label = scene.get("severity_label") or "low"
        director_update = scene.get("director_update") or {}

        embed = discord.Embed(
            title=f"Scene – Severity {severity} ({severity_label})",
            description=intro,
            color=discord.Color.dark_red(),
        )

        # NPCs
        if npcs:
            npc_text = "\n".join(f"• {n}" for n in npcs)
            embed.add_field(name="NPCs Present", value=npc_text, inline=False)

        # Encounter
        if encounter:
            enc_name = encounter.get("name", "Unknown Encounter")
            enc_desc = encounter.get("description", "")
            embed.add_field(
                name=f"Encounter – {enc_name}",
                value=enc_desc or "—",
                inline=False,
            )

        # Quest Hook
        if quest_hook:
            embed.add_field(
                name="Quest Hook",
                value=quest_hook,
                inline=False,
            )

        # V5 Director State Summary
        try:
            city_state = director_update.get("city_state", {})
            embed.add_field(
                name="City Pressure",
                value=(