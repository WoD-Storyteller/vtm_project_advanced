import discord
from discord.ext import commands

from core.combat.combat_manager import CombatManager
from core.combat.advanced_combat_engine import Combatant
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
    async def combat_start(self, ctx, *, enemy: str):
        session = manager.start_session(ctx.channel.id)

        # TODO: pull real stats from your character data
        pc = Combatant(
            name=ctx.author.display_name,
            is_vampire=True,
            attributes={"strength": 3, "dexterity": 3},
            skills={"melee": 2, "firearms": 2},
        )
        npc = Combatant(
            name=enemy,
            is_vampire=False,
            attributes={"strength": 2, "dexterity": 2},
            skills={"melee": 1, "firearms": 1},
            max_hp=7,
        )

        session.add_combatant(pc)
        session.add_combatant(npc)
        session.build_initiative()

        order = ", ".join(session.turn_order)
        await ctx.send(
            f"Combat started between **{pc.name}** and **{enemy}**.\n"
            f"Initiative order: {order}\n"
            f"First turn: **{session.current_actor()}**"
        )

    @commands.command(name="attack")
    async def attack(self, ctx, target: str, *, weapon_name: str = "Fists"):
        session = manager.get_session(ctx.channel.id)
        if not session:
            return await ctx.reply("No active combat in this channel.")

        engine = session.engine
        attacker_name = ctx.author.display_name

        if attacker_name not in engine.combatants:
            return await ctx.reply("You are not part of this combat.")

        w = weapons.get(weapon_name.lower())
        if not w:
            return await ctx.reply(f"Unknown weapon: `{weapon_name}`")

        try:
            result = engine.attack(attacker_name, target, w)
        except ValueError as e:
            return await ctx.reply(str(e))

        dice = result["dice"]
        msg = [
            f"**{result['attacker']}** attacks **{result['defender']}** with **{result['weapon']}**",
            f"Pool: {dice['pool']} (Hunger: {dice['hunger']})",
            f"Normal rolls: {dice['normal_rolls']}",
            f"Hunger rolls: {dice['hunger_rolls']}",
            f"Successes: **{dice['successes']}** (Outcome: `{dice['outcome']}`)",
            f"Net successes (after defense): {result['net_successes']}",
        ]

        if result["damage"] > 0:
            dr = result["damage_report"]
            msg.append(
                f"Damage: **{result['damage']} {result['damage_type']}** "
                f"(S: +{dr['applied_superficial']}, A: +{dr['applied_aggravated']})"
            )
            msg.append(
                f"{result['defender']} HP now: S {dr['remaining_hp_superficial']} / "
                f"A {dr['remaining_hp_aggravated']}"
            )
        else:
            msg.append("No damage dealt.")

        if result["defender_defeated"]:
            msg.append(f"💀 **{result['defender']} is defeated.**")

        # Optional: flag messy/bestial with extra line
        if dice["outcome"] == "messy_critical":
            msg.append("💥 Messy Critical! The Beast takes hold – collateral damage is likely.")
        elif dice["outcome"] == "bestial_failure":
            msg.append("😈 Bestial Failure! You lose control in a terrible way.")

        await ctx.send("\n".join(msg))

        # advance turn
        actor = session.next_turn()
        await ctx.send(f"Next acting character: **{actor}**")

    @combat.command(name="status")
    async def combat_status(self, ctx):
        session = manager.get_session(ctx.channel.id)
        if not session:
            return await ctx.reply("No active combat.")
        lines = session.engine.status()
        await ctx.send("**Combat Status:**\n" + "\n".join(lines))

    @combat.command(name="end")
    async def combat_end(self, ctx):
        manager.end_session(ctx.channel.id)
        await ctx.send("Combat ended in this channel.")

async def setup(bot):
    await bot.add_cog(CombatCog(bot))