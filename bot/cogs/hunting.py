import discord
from discord.ext import commands

from core.utils_bot import get_guild_data, load_data_from_file, save_data
from core.vtmv5.hunting_engine import HuntingEngine
from core.vtmv5 import character_model
from core.travel.zones_loader import ZoneRegistry
from core.director.ai_director import _V5_DIRECTOR, _DIRECTOR_STATE


class HuntingCommands(commands.Cog):
    """
    Hunting commands:
      !hunt_victim <location>  – narrative victim generator (simple)
      !hunt                    – V5 Predator-aware hunting + feeding,
                                 wired into the V5 Director.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Use global registry if bot already has one
        self.registry: ZoneRegistry = getattr(bot, "zone_registry", ZoneRegistry())
        self.registry.load()
        self.engine = HuntingEngine()

    # -------------------------------------------------
    # Simple narrative victim generator
    # -------------------------------------------------
    @commands.command(name="hunt_victim")
    async def hunt_victim(self, ctx: commands.Context, *, location: str):
        """
        Legacy/simple: generate a narrative victim for a given textual location.
        """
        guild_data = get_guild_data(self.bot.data_store, ctx.guild.id)
        text = await generate_hunt_victim(
            model=self.bot.ai_model_text,
            guild_data=guild_data,
            guild_id=ctx.guild.id,
            location=location,
            author_id=ctx.author.id,
        )
        await ctx.send(text)

    # -------------------------------------------------
    # Full V5 hunting
    # -------------------------------------------------
    @commands.command(name="hunt")
    async def hunt(self, ctx: commands.Context):
        """
        Perform a full V5-compatible hunt using HuntingEngine,
        zone data, Predator types, and update the V5 Director.
        """
        guild_data = get_guild_data(self.bot.data_store, ctx.guild.id)
        players = guild_data.get("players") or {}
        player = players.get(str(ctx.author.id))

        if not player:
            return await ctx.reply("You do not have a character sheet.")

        character_model.ensure_character_state(player)

        location_key = player.get("location_key") or self.registry.default_zone_key()
        zone = self.registry.get(location_key)

        if not zone:
            return await ctx.reply(
                f"Your current location `{location_key}` is not a valid zone."
            )

        async with ctx.typing():
            hunt_result = self.engine.hunt(player, zone)
            # Wire this hunt into the V5 Director
            directives = _V5_DIRECTOR.on_hunt(player, hunt_result, zone=zone)
            _DIRECTOR_STATE.save()

        dice_res = hunt_result["dice_result"]
        feeding = hunt_result["feeding_result"]

        messy = dice_res.get("messy_critical", False)
        bestial = dice_res.get("bestial_failure", False)
        successes = dice_res.get("successes", 0)

        title = f"Hunt in {hunt_result['zone_name']}"
        embed = discord.Embed(
            title=title,
            description="\n".join(hunt_result["notes"]),
            color=discord.Color.dark_red(),
        )

        embed.add_field(
            name="Dice Pool",
            value=f"{hunt_result['dice_pool']} dice (Hunger {hunt_result['hunger_before']})",
            inline=False,
        )
        embed.add_field(
            name="Result",
            value=(
                f"Successes: **{successes}**\n"
                f"Messy Critical: **{messy}**\n"
                f"Bestial Failure: **{bestial}**"
            ),
            inline=False,
        )
        embed.add_field(
            name="Feeding",
            value=(
                f"Source: {feeding['source']}\n"
                f"Hunger: {feeding['old_hunger']} → {feeding['new_hunger']}"
            ),
            inline=False,
        )

        # Director state snippet after this hunt
        city_state = directives.get("city_state", {})
        personal = directives.get("personal", {})

        embed.add_field(
            name="City Pressure (Director)",
            value=(
                f"Masquerade: {city_state.get('masquerade_pressure', 0)}\n"
                f"Violence: {city_state.get('violence_pressure', 0)}\n"
                f"Occult: {city_state.get('occult_pressure', 0)}\n"
                f"SI: {city_state.get('si_pressure', 0)}\n"
                f"Politics: {city_state.get('political_pressure', 0)}\n"
                f"Global Threat: {city_state.get('global_threat', 1)}"
            ),
            inline=False,
        )

        if personal:
            embed.add_field(
                name="Personal State",
                value=(
                    f"Humanity: {personal.get('humanity')}\n"
                    f"Stains: {personal.get('stains')}\n"
                    f"Hunger: {personal.get('hunger')}\n"
                    f"Predator Type: {personal.get('predator_type')}"
                ),
                inline=False,
            )

        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(HuntingCommands(bot))
