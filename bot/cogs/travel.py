import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

from utils import get_guild_data
from core.travel.zones_loader import ZoneRegistry
from core.travel.travel_engine import TravelEngine
from core.travel.sheets_loader import load_sheet_zones, save_zones_file
from core.time.time_state import get_time_state, advance_time, format_time
from core.director.ai_director import _V5_DIRECTOR, _DIRECTOR_STATE

load_dotenv()


class TravelCog(commands.Cog):
    """
    Global travel + zone system.

    - !whereami                – show your current zone & maps
    - !travel <zone>           – move to another zone (updates time & Director)
    - !sync_zones              – admin: sync zones from Google Sheets
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.registry: ZoneRegistry = getattr(bot, "zone_registry", ZoneRegistry())
        self.registry.load()
        self.engine = TravelEngine(self.registry)
        # Also make available on bot for other cogs
        self.bot.zone_registry = self.registry

    # -------------------------------------------------
    # Helpers
    # -------------------------------------------------
    def _format_zone(self, zone) -> str:
        lines = [f"**{zone.name}** (`{zone.key}`)"]
        if zone.region or zone.country:
            lines.append(f"{zone.region}, {zone.country}".strip(", "))
        if zone.faction:
            lines.append(f"Faction: {zone.faction}")
        lines.append(f"Danger: {zone.danger}/5")
        risk = zone.base_risk
        lines.append(
            "Risk – "
            f"Violence: {risk.get('violence', 1)}, "
            f"Masquerade: {risk.get('masquerade', 1)}, "
            f"SI: {risk.get('si', 1)}, "
            f"Occult: {risk.get('occult', 1)}"
        )
        if zone.tags:
            lines.append(f"Tags: {', '.join(zone.tags)}")
        return "\n".join(lines)

    def _apply_travel_to_director(
        self,
        zone,
        time_info,
    ):
        """
        Rough integration of travel + time into V5 Director state.
        """
        risk = zone.base_risk

        _DIRECTOR_STATE.adjust("masquerade_pressure", risk.get("masquerade", 1))
        _DIRECTOR_STATE.adjust("violence_pressure", risk.get("violence", 1))
        _DIRECTOR_STATE.adjust("occult_pressure", risk.get("occult", 1))
        _DIRECTOR_STATE.adjust("si_pressure", risk.get("si", 1))

        if time_info.get("crossed_sunrise"):
            _DIRECTOR_STATE.adjust("masquerade_pressure", 2)
            _DIRECTOR_STATE.adjust("si_pressure", 2)
            _DIRECTOR_STATE.adjust("awareness", 2)
        elif time_info.get("near_sunrise"):
            _DIRECTOR_STATE.adjust_theme("masquerade", +1)
            _DIRECTOR_STATE.adjust("awareness", 1)

        _DIRECTOR_STATE.save()
        return _DIRECTOR_STATE.summarize()

    # -------------------------------------------------
    # Commands
    # -------------------------------------------------
    @commands.command(name="whereami")
    async def where_am_i(self, ctx: commands.Context):
        """
        Show current zone & maps.
        """
        guild_data = get_guild_data(self.bot.data_store, ctx.guild.id)
        players = guild_data.get("players") or {}
        player = players.get(str(ctx.author.id))

        if not player:
            return await ctx.reply("You do not have a character sheet.")

        key = player.get("location_key") or self.registry.default_zone_key()
        zone = self.registry.get(key) or self.registry.find(key)

        if not zone:
            return await ctx.reply("You are in an unknown void. Tell the ST to fix your location_key.")

        embed = discord.Embed(
            title="Current Zone",
            description=self._format_zone(zone),
            color=discord.Color.purple(),
        )

        if zone.mymaps:
            value_lines = []
            for m in zone.mymaps:
                label = m.get("map_name") or "Map"
                url = m.get("url") or ""
                mtype = m.get("type", "mymaps")
                value_lines.append(f"[{label}]({url}) ({mtype})")
            embed.add_field(name="Maps", value="\n".join(value_lines), inline=False)

        await ctx.send(embed=embed)

    @commands.command(name="travel")
    async def travel(self, ctx: commands.Context, *, destination: str):
        """
        Travel to another zone by key or name (fuzzy).
        """
        guild_data = get_guild_data(self.bot.data_store, ctx.guild.id)
        players = guild_data.get("players") or {}
        player = players.get(str(ctx.author.id))

        if not player:
            return await ctx.reply("You do not have a character sheet.")

        async with ctx.typing():
            result = self.engine.travel(player, destination)

            if not result["success"]:
                return await ctx.reply(result["msg"])

            zone = result["zone"]
            origin = result["origin"]
            time_cost = result["time_cost"]

            # Time progression
            ts = get_time_state(guild_data)
            time_info = advance_time(guild_data, time_cost)
            time_str = format_time(time_info["time_state"])

            director_summary = self._apply_travel_to_director(zone, time_info)

        embed = discord.Embed(
            title="Travel",
            description=result["msg"],
            color=discord.Color.dark_gold(),
        )

        embed.add_field(
            name="Time Cost",
            value=f"{time_cost} hours\nNew time: {time_str}",
            inline=False,
        )

        embed.add_field(
            name="Destination",
            value=self._format_zone(zone),
            inline=False,
        )

        city_state = director_summary
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

        if result["encounter"]:
            enc = result["encounter"]
            embed.add_field(
                name="Travel Encounter",
                value=f"{enc.get('text', 'Something happens on the road...')}\n"
                      f"Severity: {enc.get('severity', 1)}",
                inline=False,
            )

        await ctx.send(embed=embed)

    @commands.command(name="sync_zones")
    @commands.has_permissions(administrator=True)
    async def sync_zones(self, ctx: commands.Context):
        """
        Sync zones from Google Sheets and reload registry.
        """
        async with ctx.typing():
            try:
                zones = load_sheet_zones()  # uses .env defaults
                save_zones_file(zones)

                self.registry.load()
                self.bot.zone_registry = self.registry

                await ctx.send("✅ **Zones synced & reloaded successfully!**")
            except Exception as e:
                await ctx.send(f"❌ **Zone sync failed:** `{e}`")


async def setup(bot: commands.Bot):
    await bot.add_cog(TravelCog(bot))