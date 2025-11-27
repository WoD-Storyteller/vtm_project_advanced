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
                    f"Masquerade: {city_state.get('masquerade_pressure', 0)}\n"
                    f"Violence: {city_state.get('violence_pressure', 0)}\n"
                    f"Occult: {city_state.get('occult_pressure', 0)}\n"
                    f"SI: {city_state.get('si_pressure', 0)}\n"
                    f"Politics: {city_state.get('political_pressure', 0)}\n"
                    f"Threat Level: {city_state.get('global_threat', 1)}"
                ),
                inline=False,
            )
        except Exception:
            pass

        # Personal state (if available)
        personal = director_update.get("personal")
        if personal:
            embed.add_field(
                name="Personal State",
                value=(
                    f"Humanity: {personal.get('humanity')}\n"
                    f"Stains: {personal.get('stains')}\n"
                    f"Hunger: {personal.get('hunger')}\n"
                    f"Predator Type: {personal.get('predator_type')}\n"
                    f"Alive Touchstones: {', '.join(personal.get('touchstones_alive', [])) or 'None'}\n"
                    f"Dead Touchstones: {', '.join(personal.get('touchstones_dead', [])) or 'None'}"
                ),
                inline=False,
            )

        return embed

    # --------------------------------------------------------
    # Player-triggered scene
    # --------------------------------------------------------
    @commands.command(name="scene")
    async def generate_player_scene(self, ctx):
        """
        Players request a normal scene in their current location.
        """
        guild_data = get_guild_data(self.bot.data_store, ctx.guild.id)
        players = guild_data.get("players") or {}
        player = players.get(str(ctx.author.id))

        if not player:
            return await ctx.reply("You do not have a character sheet.")

        location_key = player.get("location_key")
        if not location_key:
            return await ctx.reply("You are not currently located anywhere.")

        async with ctx.typing():
            try:
                scene = await AIDirector.generate_scene(
                    model_text=self.bot.ai_model_text,
                    model_json=self.bot.ai_model_json,
                    guild_data=guild_data,
                    guild_id=ctx.guild.id,
                    location_key=location_key,
                    travelers=[player],
                    risk=2,
                )
            except Exception:
                traceback.print_exc()
                return await ctx.reply("Scene generation failed.")

        embed = await self.build_scene_embed(ctx, scene)
        await ctx.send(embed=embed)

    # --------------------------------------------------------
    # Storyteller command – manual scene
    # --------------------------------------------------------
    @commands.command(name="stscene")
    @commands.has_permissions(administrator=True)
    async def generate_storyteller_scene(self, ctx, severity: int = 2):
        """
        ST triggers a scene manually.
        """
        guild_data = get_guild_data(self.bot.data_store, ctx.guild.id)

        # If ST wants to run a scene without players, we use global directives
        travelers = []

        async with ctx.typing():
            try:
                scene = await AIDirector.generate_scene(
                    model_text=self.bot.ai_model_text,
                    model_json=self.bot.ai_model_json,
                    guild_data=guild_data,
                    guild_id=ctx.guild.id,
                    location_key="elysium",  # safe default
                    travelers=travelers,
                    risk=severity,
                )
            except Exception:
                traceback.print_exc()
                return await ctx.reply("Scene generation failed.")

        embed = await self.build_scene_embed(ctx, scene)
        await ctx.send(embed=embed)

    # --------------------------------------------------------
    # Storyteller force scene with custom tags
    # --------------------------------------------------------
    @commands.command(name="stforce")
    @commands.has_permissions(administrator=True)
    async def generate_forced_scene(self, ctx, severity: int, *, tags: str = ""):
        """
        ST forces a scene with custom semantic tags.

        Example:
          !stforce 4 combat,ritual,anarch
        """
        guild_data = get_guild_data(self.bot.data_store, ctx.guild.id)
        tags_list = [t.strip() for t in tags.split(",") if t.strip()]

        async with ctx.typing():
            try:
                scene = await AIDirector.generate_scene(
                    model_text=self.bot.ai_model_text,
                    model_json=self.bot.ai_model_json,
                    guild_data=guild_data,
                    guild_id=ctx.guild.id,
                    location_key="unknown",
                    travelers=[],
                    risk=severity,
                    tags=tags_list,
                )
            except Exception:
                traceback.print_exc()
                return await ctx.reply("Forced scene generation failed.")

        embed = await self.build_scene_embed(ctx, scene)
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(StorytellerCog(bot))