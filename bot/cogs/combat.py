import discord
from discord.ext import commands

from core.utils import get_guild_data
from core.combat.combat_manager import CombatManager
from core.combat.combatant_factory import CombatantFactory
from core.combat.frenzy_system import FrenzySystem
from core.weapons.weapon_loader import load_weapons

manager = CombatManager()
weapons = load_weapons()


class CombatCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="combat", invoke_without_command=True)
    async def combat(self, ctx: commands.Context):
        await ctx.reply("Use: `!combat start <enemy>`, `!combat status`, `!combat end`")

    @combat.command(name="start")
    async def combat_start(self, ctx: commands.Context, *, enemy: str):
        guild_id = ctx.guild.id
        user_id = str(ctx.author.id)

        g_data = get_guild_data(guild_id)

        if "players" not in g_data or user_id not in g_data["players"]:
            return await ctx.reply("You don't have a character sheet yet.")

        if "npcs" not in g_data or enemy not in g_data["npcs"]:
            return await ctx.reply(f"NPC '{enemy}' does not exist.")

        pc_data = g_data["players"][user_id]
        npc_data = g_data["npcs"][enemy]

        pc = CombatantFactory.from_player(user_id, pc_data)
        npc = CombatantFactory.from_npc(enemy, npc_data)

        session = manager.start_session(ctx.channel.id)
        session.add_combatant(pc)
        session.add_combatant(npc)
        session.build_initiative()

        order = ", ".join(session.turn_order)
        await ctx.send(
            f"🩸 Combat started between **{pc.name}** and **{npc.name}**.\n"
            f"Initiative order: {order}\n"
            f"First turn: **{session.current_actor()}**"
        )

    @commands.command(name="attack")
    async def attack(self, ctx: commands.Context, target: str, *, weapon_name: str = "Fists"):
        session = manager.get_session(ctx.channel.id)
        if not session:
            return await ctx.reply("No combat running in this channel.")

        engine = session.engine
        attacker_name = ctx.author.display_name

        if attacker_name not in engine.combatants:
            return await ctx.reply("You are not in this combat.")

        weapon_key = weapon_name.lower()
        if weapon_key not in weapons:
            return await ctx.reply(f"Unknown weapon: `{weapon_name}`")

        weapon = weapons[weapon_key]

        try:
            result = engine.attack(attacker_name, target, weapon)
        except ValueError as e:
            return await ctx.reply(str(e))

        dice = result["dice"]
        lines = [
            f"**{result['attacker']}** attacks **{result['defender']}** with **{result['weapon']}**",
            f"🎲 Dice Pool: {dice['pool']} (Hunger: {dice['hunger']})",
            f"Normal rolls: {dice['normal_rolls']}",
            f"Hunger rolls: {dice['hunger_rolls']}",
            f"Successes: **{dice['successes']}** (`{dice['outcome']}`)",
            f"Net successes (after defense): {result['net_successes']}",
        ]

        if result["damage"] > 0:
            dr = result["damage_report"]
            lines.append(
                f"Damage: **{result['damage']} {result['damage_type']}** "
                f"(S:+{dr['applied_superficial']} A:+{dr['applied_aggravated']})"
            )
            lines.append(
                f"{result['defender']} HP → "
                f"S:{dr['remaining_hp_superficial']} "
                f"A:{dr['remaining_hp_aggravated']}"
            )
        else:
            lines.append("No damage inflicted.")

        if dice["outcome"] == "messy_critical":
            lines.append("💥 **Messy Critical!** The Beast takes control of the success.")
        elif dice["outcome"] == "bestial_failure":
            lines.append("😈 **Bestial Failure!** You lose control in a terrible way.")

        if result["defender_defeated"]:
            lines.append(f"☠️ **{result['defender']} is defeated!**")

        await ctx.send("\n".join(lines))

        # Frenzy notification
        if FrenzySystem.is_frenzied(attacker_name):
            await ctx.send(
                f"😡 **{attacker_name} is in Frenzy!** They must continue to attack "
                f"until calmed or the scene ends."
            )

        # advance turn
        actor = session.next_turn()
        if actor:
            await ctx.send(f"➡️ Next turn: **{actor}**")

    @combat.command(name="status")
    async def combat_status(self, ctx: commands.Context):
        session = manager.get_session(ctx.channel.id)
        if not session:
            return await ctx.reply("No active combat.")
        lines = session.engine.status()
        await ctx.send("**Combat Status:**\n" + "\n".join(lines))

    @combat.command(name="end")
    async def combat_end(self, ctx: commands.Context):
        manager.end_session(ctx.channel.id)
        await ctx.send("Combat ended in this channel.")

    @commands.command(name="calm")
    @commands.has_permissions(manage_guild=True)
    async def calm(self, ctx: commands.Context, *, target: str):
        """
        ST/Mod tool: end frenzy for a given combatant.
        """
        if FrenzySystem.is_frenzied(target):
            FrenzySystem.clear_frenzy(target)
            await ctx.send(f"🧘 **{target} is calmed. Frenzy ends.**")
        else:
            await ctx.send(f"{target} is not currently frenzied.")


async def setup(bot):
    await bot.add_cog(CombatCog(bot))