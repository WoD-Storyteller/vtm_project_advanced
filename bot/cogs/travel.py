import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

from utils import get_guild_data
from core.travel.zones_loader import ZoneRegistry
from core.travel.travel_engine import TravelEngine
from core.travel.sheets_loader import load_sheet_zones, save_zones_file
from core.time.time_state import get_time_state, advance_time, format_time
from director_system.hooks import apply_travel_event

load_dotenv()


class TravelCog(commands.Cog):
    """
    Global travel + time system.

    Commands:
      !zones              - list known zones
      !whereami           - show current zone + map links
      !travel <dest>      - travel to another zone (advancing time)
      !time               - show chronicle time (night/hour)
      !zones_sync         - (admin) sync zones from Google Sheets
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # ZoneRegistry is attached to bot in main.py:
        #   bot.zone_registry = ZoneRegistry(); bot.zone_registry.load()
        self.registry: ZoneRegistry = bot.zone_registry
        self.engine = TravelEngine(self.registry)

    # --------------------------------------------------
    # HELPERS
    # --------------------------------------------------

    def _get_player(self, ctx):
        guild_data = get_guild_data(self.bot.data_store, ctx.guild.id)
        player = guild_data.get("players", {}).get(str(ctx.author.id))
        return guild_data, player

    # --------------------------------------------------
    # COMMANDS
    # --------------------------------------------------

    @commands.command(name="zones")
    async def zones(self, ctx: commands.Context):
        """
        List major zones (world-wide) loaded from zones.json.
        """
        zs = self.registry.list()
        if not zs:
            return await ctx.reply("No zones loaded. Ask your Storyteller to run `!zones_sync`.")

        lines = []
        for z in zs:
            tag_str = ", ".join(z.tags) if z.tags else "no tags"
            lines.append(f"`{z.key}` – **{z.name}** ({tag_str})")

        desc = "\n".join(lines[:100])  # hard cap for sanity
        embed = discord.Embed(
            title="Known Zones",
            description=desc,
            color=discord.Color.dark_gold(),
        )
        await ctx.send(embed=embed)

    @commands.command(name="whereami")
    async def whereami(self, ctx: commands.Context):
        """
        Show your character's current location and related map links.
        """
        guild_data, player = self._get_player(ctx)
        if not player:
            return await ctx.reply("You don't have a character sheet yet.")

        loc_key = player.get("location_key") or self.registry.default_zone_key()
        zone = self.registry.get(loc_key) or self.registry.get(self.registry.default_zone_key())

        embed = discord.Embed(
            title=f"{player.get('name', ctx.author.display_name)} – Current Location",
            description=f"**{zone.name}**\n\n{zone.description}",
            color=discord.Color.blurple(),
        )
        embed.add_field(name="Region", value=zone.region or "Unknown", inline=True)
        embed.add_field(name="Faction", value=zone.faction or "Unknown", inline=True)

        if zone.mymaps:
            for entry in zone.mymaps[:5]:
                embed.add_field(
                    name=f"📍 {entry.get('map_name')}",
                    value=(
                        f"Layer: `{entry.get('layer')}`\n"
                        f"Label: `{entry.get('label')}`\n"
                        f"[Open Map]({entry.get('url')})"
                    ),
                    inline=False,
                )

        await ctx.send(embed=embed)

    @commands.command(name="time")
    async def show_time(self, ctx: commands.Context):
        """
        Show the current in-game time (night/hour).
        """
        guild_data, _ = self._get_player(ctx)
        ts = get_time_state(guild_data)
        text = format_time(ts)
        self.bot.save_data()
        await ctx.reply(f"🕒 In-game time: **{text}**")

    @commands.command(name="travel")
    async def travel(self, ctx: commands.Context, *, destination: str):
        """
        Travel your character to another zone (by key or name fragment).
        Advances in-game time based on zone travel_difficulty.
        """
        guild_data, player = self._get_player(ctx)
        if not player:
            return await ctx.reply("You don't have a character sheet yet.")

        # Run travel engine
        result = self.engine.travel(player, destination)
        if not result["success"]:
            return await ctx.reply(result["msg"])

        dest = result["zone"]
        origin = result["origin"]
        encounter = result["encounter"]
        time_cost = result["time_cost"]

        # Advance time for the guild
        time_info = advance_time(guild_data, time_cost)
        ts = time_info["time_state"]
        time_str = format_time(ts)

        # Director hook
        apply_travel_event(guild_data, dest, encounter, time_info)

        # Persist data
        self.bot.save_data()

        # Build response
        desc_lines = [
            f"{result['msg']}",
            f"Travel time: **{time_cost}h**",
            f"Current in-game time: **{time_str}**",
        ]

        if time_info.get("near_sunrise") and not time_info.get("crossed_sunrise"):
            desc_lines.append("⚠ The horizon is paling. Sunrise is getting close.")
        if time_info.get("crossed_sunrise"):
            desc_lines.append("☀ You have pushed past sunrise. This is extremely dangerous.")

        if encounter:
            desc_lines.append("")
            desc_lines.append(f"**Encounter:** {encounter['text']} (Severity {encounter['severity']})")

        embed = discord.Embed(
            title=f"Travel – {player.get('name', ctx.author.display_name)}",
            description="\n".join(desc_lines),
            color=discord.Color.dark_teal(),
        )

        await ctx.send(embed=embed)

    @commands.command(name="zones_sync")
    @commands.has_permissions(administrator=True)
    async def zones_sync(self, ctx: commands.Context):
        """
        Sync zones from Google Sheets → zones.json → reload registry.
        Uses GOOGLE_SHEET_ID and GOOGLE_SERVICE_ACCOUNT from .env
        """
        await ctx.send("🔄 Syncing zones from Google Sheets…")

        try:
            zones = load_sheet_zones()  # uses .env defaults
            save_zones_file(zones)

            # Reload registry
            self.registry.load()
            self.bot.zone_registry = self.registry

            await ctx.send("✅ **Zones synced & reloaded successfully!**")
        except Exception as e:
            await ctx.send(f"❌ **Zone sync failed:** `{e}`")


async def setup(bot: commands.Bot):
    await bot.add_cog(TravelCog(bot))