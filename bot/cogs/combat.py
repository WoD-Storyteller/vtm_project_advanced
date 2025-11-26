import discord
from discord.ext import commands
from core.combat.combat_manager import CombatManager
from core.weapons.weapon_loader import load_weapons

weapons = load_weapons()
manager = CombatManager()

class CombatCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="combat")
    async def combat(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.reply("Use: !combat start <enemy>, !combat end, !attack <target> <weapon>")

    @combat.command(name="start")
    async def combat_start(self, ctx, *, enemy):
        session = manager.start(ctx.channel.id, ctx.author.display_name, enemy)
        await ctx.send(f"Combat started with **{enemy}**.")

    @commands.command(name="attack")
    async def attack(self, ctx, target, *, weapon_name):
        session = manager.get(ctx.channel.id)
        if not session:
            return await ctx.reply("No combat active.")

        weapon = weapons.get(weapon_name.lower())
        if not weapon:
            return await ctx.reply(f"Weapon not found: {weapon_name}")

        result = session.attack(ctx.author.display_name, target, weapon)
        await ctx.send(result)

    @combat.command(name="status")
    async def combat_status(self, ctx):
        session = manager.get(ctx.channel.id)
        if not session:
            return await ctx.reply("No combat active.")
        await ctx.reply(session.status())

    @combat.command(name="end")
    async def combat_end(self, ctx):
        manager.end(ctx.channel.id)
        await ctx.send("Combat ended.")

async def setup(bot):
    await bot.add_cog(CombatCog(bot))