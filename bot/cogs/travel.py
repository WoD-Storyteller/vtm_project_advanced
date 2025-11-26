import discord
from discord.ext import commands

from utils import get_guild_data
from core.travel.zones_loader import ZoneRegistry
from core.travel.travel_engine import TravelEngine
from director_system.hooks import apply_travel_event


class TravelCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.registry: ZoneRegistry = bot.zone_registry
        self.engine = TravelEngine(self.registry)

    @commands.command(name="zones")
    async def zones(self, ctx):
        zs = self.registry.list()
        desc = "\n".join([f"`{z.key}` – **{z.name}**" for z in zs])
        embed = discord.Embed(title="Zones", description=desc, color=0x4a90e2)
        await ctx.send(embed=embed)

    @commands.command(name="whereami")
    async def whereami(self, ctx):
        g_data = get_guild_data(self.bot.data_store, ctx.guild.id)
        player = g_data["players"].get(str(ctx.author.id))
        if not player:
            return await ctx.reply("You don't have a character sheet.")

        loc_key = player.get("location_key") or self.registry.default_zone_key()
        zone = self.registry.get(loc_key)

        embed = discord.Embed(
            title=f"Current Location — {player.get('name')}",
            description=f"**{zone.name}**\n{zone.description}",
            color=0x00b894,
        )

        for m in zone.mymaps:
            embed.add_field(
                name=f"📍 {m.get('map_name')}",
                value=f"Layer: `{m.get('layer')}`\nLabel: `{m.get('label')}`\n[Open Map]({m.get('url')})",
                inline=False,
            )

        await ctx.send(embed=embed)

    @commands.command(name="travel")
    async def travel(self, ctx, *, destination: str):
        g_data = get_guild_data(self.bot.data_store, ctx.guild.id)
        player = g_data["players"].get(str(ctx.author.id))
        if not player:
            return await ctx.reply("No character sheet found.")

        zone = self.registry.find(destination)
        if not zone:
            return await ctx.reply("Unknown destination.")

        result = self.engine.travel(player, zone.key)
        apply_travel_event(g_data, zone.key, result)
        self.bot.save_data()

        embed = discord.Embed(
            title=f"Travel — {player.get('name')}",
            description=result.narrative,
            color=0x0984e3,
        )

        if result.encounter:
            embed.add_field(
                name="Encounter",
                value=f"**{result.encounter.name}**\n{result.encounter.summary}",
                inline=False,
            )

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(TravelCog(bot))