import discord
from discord.ext import commands
from core.combat import CombatEngine, Combatant

class CombatCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.combat_sessions = {}

    @commands.group(name="combat", invoke_without_command=True)
    async def combat(self, ctx):
        await ctx.reply("Use: !combat start, !combat end")

    @combat.command(name="start")
    async def combat_start(self, ctx, *, enemy):
        engine = CombatEngine()
        pc = Combatant(ctx.author.display_name)
        npc = Combatant(enemy, npc=True)
        engine.add_combatant(pc)
        engine.add_combatant(npc)
        self.combat_sessions[ctx.channel.id] = engine
        await ctx.send(f"Combat started between **{pc.name}** and **{enemy}**.")

    @commands.command(name="attack")
    async def attack(self, ctx, *, target):
        engine = self.combat_sessions.get(ctx.channel.id)
        if not engine:
            return await ctx.reply("No combat active.")
        log = engine.attack(ctx.author.display_name, target)
        await ctx.send("\n".join(log))

    @combat.command(name="end")
    async def combat_end(self, ctx):
        self.combat_sessions.pop(ctx.channel.id, None)
        await ctx.send("Combat ended.")

async def setup(bot):
    await bot.add_cog(CombatCog(bot))