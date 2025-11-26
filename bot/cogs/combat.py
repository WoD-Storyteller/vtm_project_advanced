import discord
from discord.ext import commands

from core.utils import get_guild_data
from core.combat.combat_manager import CombatManager
from core.combat.combatant_factory import CombatantFactory
from core.weapons.weapon_loader import load_weapons

manager = CombatManager()
weapons = load_weapons()


class CombatCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="combat", invoke_without_command=True)
    async def combat(self, ctx):
        await ctx.reply("Use: `!combat start <enemy>`, `!combat status`, `!combat end`")

    @combat.command(name="start")
    async def combat_start(self, ctx, enemy: str):
        guild_id = ctx.guild.id
        user_id = str(ctx.author.id)

        g_data = get_guild_data(guild_id)

        # Player data
        if user_id not in g_data["players"]:
            return await ctx.reply("You don't have a character sheet yet.")

        pc_data = g_data["players"][user_id]

        # NPC data
        if