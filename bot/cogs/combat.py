import discord
from discord.ext import commands

from utils import get_guild_data
from core.combat.combat_manager import CombatManager
from core.combat.combatant_factory import CombatantFactory
from core.combat.frenzy_system import FrenzySystem
from director_system.hooks import apply_combat_event
from core.weapons.weapon_loader import load_weapons


manager = CombatManager()
weapons = load_weapons()


class CombatCog(commands.Cog):
    """
    Advanced V5 combat interface for Discord.

    Commands:
      !combat start <npc_name>
      !attack <target_name> [weapon]
      !reload <weapon>
      !combat status
      !combat end
      !calm <character_name>   (ST only, ends frenzy)
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.group(name="combat", invoke_without_command=True)
    async def combat_group(self, ctx: commands.Context):
        await ctx.reply("Use: `!combat start <enemy>`, `!combat status`, `!combat end`")

    @combat_group.command(name="start")
    async def combat_start(self, ctx: commands.Context, *, enemy: str):
        """Start combat between your character and a named NPC."""
        g_data = get_guild_data(self.bot.data_store, ctx.guild.id)
        user_id = str(ctx.author.id)

        if "players" not in g_data or user_id not in g_data["players"]:
            return await ctx.reply("You don't have a character sheet yet.")

        if "npcs" not in g_data or enemy not in g_data["npcs"]:
            return await ctx.reply(f"NPC '{enemy}' does not exist in this guild data.")

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
        """
        Make an attack roll using your character against a target in this combat.
        """
        session = manager.get_session(ctx.channel.id)
        if not session:
            return await ctx.reply("No combat is running in this channel.")

        engine = session.engine

        # Load guild & player to get the *character name* (not Discord nickname)
        g_data = get_guild_data(self.bot.data_store, ctx.guild.id)
        user_id = str(ctx.author.id)
        player = g_data.get("players", {}).get(user_id)
        if not player:
            return await ctx.reply("You don't have a character sheet yet.")

        attacker_name = player.get("name", ctx.author.display_name)

        if attacker_name not in engine.combatants:
            return await ctx.reply(
                f"Your character **{attacker_name}** is not part of this combat."
            )

        key = weapon_name.lower()
        if key not in weapons:
            return await ctx.reply(f"Unknown weapon: `{weapon_name}`")

        weapon = weapons[key]

        # Ammo check for ranged
        ok, remaining = session.use_ammo(attacker_name, weapon)
        if not ok:
            return await ctx.reply(
                f"🔫 **Click.** {attacker_name} is out of ammo for **{weapon['name']}**.\n"
                f"Use `!reload {weapon['name']}` first."
            )

        try:
            result = engine.attack(attacker_name, target, weapon)
        except ValueError as e:
            return await ctx.reply(str(e))

        dice = result["dice"]
        # Support both dict-style and object-style DiceResult
        if isinstance(dice, dict):
            outcome = dice.get("outcome")
            pool = dice.get("pool")
            hunger = dice.get("hunger")
            normal_rolls = dice.get("normal_rolls")
            hunger_rolls = dice.get("hunger_rolls")
            successes = dice.get("successes")
            bestial_chaos = dice.get("bestial_chaos")
        else:
            outcome = getattr(dice, "outcome", None)
            if hasattr(outcome, "value"):
                outcome = outcome.value
            pool = getattr(dice, "pool", None)
            hunger = getattr(dice, "hunger", None)
            normal_rolls = getattr(dice, "normal_rolls", [])
            hunger_rolls = getattr(dice, "hunger_rolls", [])
            successes = getattr(dice, "successes", None)
            bestial_chaos = getattr(dice, "bestial_chaos", None)

        lines = [
            f"**{result['attacker']}** attacks **{result['defender']}** with **{weapon['name']}**",
            f"🎲 Dice Pool: {pool} (Hunger: {hunger})",
            f"Normal rolls: {normal_rolls}",
            f"Hunger rolls: {hunger_rolls}",
            f"Successes: **{successes}** (`{outcome}`)",
            f"Net successes (after defense): {result.get('net_successes')}",
        ]

        dmg = result.get("damage", 0)
        dr = result.get("damage_report") or {}
        if dmg > 0:
            lines.append(
                f"Damage: **{dmg} {result.get('damage_type', 'superficial')}** "
                f"(S:+{dr.get('applied_superficial', 0)} "
                f"A:+{dr.get('applied_aggravated', 0)})"
            )
            lines.append(
                f"{result['defender']} HP → "
                f"S:{dr.get('remaining_hp_superficial', '?')} "
                f"A:{dr.get('remaining_hp_aggravated', '?')}"
            )
        else:
            lines.append("No damage inflicted.")

        # Outcome flags
        outcome_str = (outcome or "").lower()
        if outcome_str == "messy_critical":
            lines.append("💥 **Messy Critical!** The Beast rides your success.")
        elif outcome_str == "bestial_failure":
            lines.append("😈 **Bestial Failure!** You lose control in a terrible way.")
        elif outcome_str == "bestial_success":
            lines.append("😬 **Bestial Success!** The Beast twists your victory.")
            if bestial_chaos:
                lines.append(f"⚠️ Complication: *{bestial_chaos}*")

        if result.get("defender_defeated") or result.get("defeated"):
            lines.append(f"☠️ **{result['defender']} is defeated!**")

        # Ammo line for ranged
        if weapon.get("type") == "ranged":
            lines.append(f"🔫 Ammo remaining in **{weapon['name']}**: {remaining}")

        await ctx.send("\n".join(lines))

        # Frenzy notice (if tracked)
        if FrenzySystem.is_frenzied(attacker_name):
            await ctx.send(
                f"😡 **{attacker_name} is in Frenzy!** They must keep attacking until calmed or combat ends."
            )

        # Director hook (Masquerade / Violence tracking)
        severity = max(1, int(dmg)) if dmg is not None else 1
        apply_combat_event(
            guild_data=g_data,
            outcome=outcome_str,
            severity=severity,
            attacker=attacker_name,
            defender=result["defender"],
            chaos=bestial_chaos,
        )
        # Persist updated director state and any other changes
        self.bot.save_data()

        # Advance turn
        actor = session.next_turn()
        if actor:
            await ctx.send(f"➡️ Next turn: **{actor}**")

    @combat_group.command(name="status")
    async def combat_status(self, ctx: commands.Context):
        """Show HP/Hunger status of all combatants in this channel."""
        session = manager.get_session(ctx.channel.id)
        if not session:
            return await ctx.reply("No active combat in this channel.")
        lines = session.engine.status()
        await ctx.send("**Combat Status:**\n" + "\n".join(lines))

    @combat_group.command(name="end")
    async def combat_end(self, ctx: commands.Context):
        """End combat in this channel."""
        manager.end_session(ctx.channel.id)
        await ctx.send("Combat ended in this channel.")

    @commands.command(name="reload")
    async def reload(self, ctx: commands.Context, *, weapon_name: str):
        """Reload a ranged weapon used by your character."""
        session = manager.get_session(ctx.channel.id)
        if not session:
            return await ctx.reply("No active combat to reload in.")

        key = weapon_name.lower()
        if key not in weapons:
            return await ctx.reply(f"Unknown weapon: `{weapon_name}`")

        weapon = weapons[key]
        g_data = get_guild_data(self.bot.data_store, ctx.guild.id)
        user_id = str(ctx.author.id)
        player = g_data.get("players", {}).get(user_id)
        if not player:
            return await ctx.reply("You don't have a character sheet yet.")

        attacker_name = player.get("name", ctx.author.display_name)
        new_count = session.reload(attacker_name, weapon)
        if new_count < 0:
            return await ctx.reply("You can't reload a melee weapon.")

        await ctx.send(
            f"🔄 **{weapon['name']}** reloaded to {new_count} rounds for **{attacker_name}**."
        )

    @commands.command(name="calm")
    @commands.has_permissions(manage_guild=True)
    async def calm(self, ctx: commands.Context, *, target: str):
        """
        ST/Mod tool: end frenzy for a given combatant (by character name).
        """
        if FrenzySystem.is_frenzied(target):
            FrenzySystem.clear_frenzy(target)
            self.bot.save_data()
            await ctx.send(f"🧘 **{target} is calmed. Frenzy ends.**")
        else:
            await ctx.send(f"{target} is not currently frenzied.")


async def setup(bot: commands.Bot):
    await bot.add_cog(CombatCog(bot))