import discord
from discord.ext import commands

from utils import get_guild_data
from core.vtmv5 import (
    dice,
    hunger,
    willpower,
    humanity,
    frenzy as frenzy_mod,
    character_model,
)


class VtMV5Cog(commands.Cog):
    """
    Core V5 rules interface.

    Commands:
      !v5roll <dice_pool> <difficulty> [reason]
      !rouse
      !frenzy <dice_pool> <difficulty>
      !wp              - show willpower
      !stain [amount]  - add stains
      !remorse         - perform remorse roll
      !v5stats         - show core V5 stats
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ------------ helpers ------------

    def _get_player(self, ctx):
        guild_data = get_guild_data(self.bot.data_store, ctx.guild.id)
        player = guild_data.get("players", {}).get(str(ctx.author.id))
        if player is None:
            return guild_data, None
        character_model.ensure_character_state(player)
        return guild_data, player

    # ------------ commands ------------

    @commands.command(name="v5roll")
    async def v5roll(self, ctx, dice_pool: int, difficulty: int, *, reason: str = ""):
        """
        Roll a V5 dice pool:
          !v5roll 6 2 punch the guy
        """
        guild_data, player = self._get_player(ctx)
        if not player:
            return await ctx.reply("You don't have a character sheet yet.")

        hunger_val = character_model.get_hunger(player)
        res = dice.roll_pool(dice_pool=dice_pool, hunger=hunger_val, difficulty=difficulty)

        dice_str = " ".join(str(d) for d in res["dice"])
        hunger_str = " ".join(str(d) for d in res["hunger_dice"])

        title = f"V5 Roll – {player.get('name', ctx.author.display_name)}"
        if reason:
            title += f" ({reason})"

        embed = discord.Embed(
            title=title,
            color=discord.Color.red() if res["messy_critical"] or res["bestial_failure"] else discord.Color.dark_grey(),
        )
        embed.add_field(name="Dice Pool", value=str(dice_pool), inline=True)
        embed.add_field(name="Difficulty", value=str(difficulty), inline=True)
        embed.add_field(name="Hunger", value=str(hunger_val), inline=True)

        embed.add_field(name="Normal Dice", value=dice_str or "—", inline=False)
        embed.add_field(name="Hunger Dice", value=hunger_str or "—", inline=False)
        embed.add_field(name="Successes", value=str(res["successes"]), inline=True)

        notes = []
        if res["critical_pairs"] > 0:
            notes.append(f"Criticals: {res['critical_pairs']} pair(s)")
        if res["messy_critical"]:
            notes.append("💥 Messy Critical")
        if res["bestial_failure"]:
            notes.append("🐺 Bestial Failure")
        if res["total_success"]:
            notes.append("✅ Success")
        else:
            notes.append("❌ Failure")

        embed.add_field(
            name="Result",
            value="\n".join(notes),
            inline=False,
        )

        await ctx.send(embed=embed)

    @commands.command(name="rouse")
    async def rouse(self, ctx):
        """
        Perform a Rouse Check.
        """
        guild_data, player = self._get_player(ctx)
        if not player:
            return await ctx.reply("You don't have a character sheet yet.")

        res = hunger.rouse_check(player)
        self.bot.save_data()

        embed = discord.Embed(
            title=f"Rouse Check – {player.get('name', ctx.author.display_name)}",
            color=discord.Color.dark_red(),
        )
        embed.add_field(name="Roll", value=str(res["roll"]), inline=True)
        embed.add_field(
            name="Result",
            value="Success (no hunger increase)" if res["success"] else "Failure (Hunger +1)",
            inline=True,
        )
        embed.add_field(
            name="Hunger",
            value=f"{res['old_hunger']} → {res['new_hunger']}",
            inline=False,
        )
        await ctx.send(embed=embed)

    @commands.command(name="frenzy")
    async def frenzy(self, ctx, dice_pool: int, difficulty: int, *, source: str = "frenzy"):
        """
        Test for Frenzy / Rötschreck.
          !frenzy 5 3 fire
        """
        guild_data, player = self._get_player(ctx)
        if not player:
            return await ctx.reply("You don't have a character sheet yet.")

        res = frenzy_mod.frenzy_test(player, dice_pool=dice_pool, difficulty=difficulty, source=source)
        self.bot.save_data()

        r = res["result"]
        dice_str = " ".join(str(d) for d in r["dice"])
        hunger_str = " ".join(str(d) for d in r["hunger_dice"])

        embed = discord.Embed(
            title=f"Frenzy Test – {player.get('name', ctx.author.display_name)}",
            color=discord.Color.dark_red() if res["failed"] else discord.Color.dark_green(),
        )
        embed.add_field(name="Dice Pool", value=str(dice_pool), inline=True)
        embed.add_field(name="Difficulty", value=str(difficulty), inline=True)
        embed.add_field(name="Hunger", value=str(character_model.get_hunger(player)), inline=True)
        embed.add_field(name="Normal Dice", value=dice_str or "—", inline=False)
        embed.add_field(name="Hunger Dice", value=hunger_str or "—", inline=False)
        embed.add_field(name="Successes", value=str(r["successes"]), inline=True)

        status = "FAILED – The Beast takes over." if res["failed"] else "Success – You hold the Beast at bay."
        embed.add_field(name="Outcome", value=status, inline=False)

        await ctx.send(embed=embed)

    @commands.command(name="wp")
    async def show_willpower(self, ctx):
        """
        Show your Willpower track.
        """
        guild_data, player = self._get_player(ctx)
        if not player:
            return await ctx.reply("You don't have a character sheet yet.")

        wp = player["willpower"]
        cur = character_model.current_willpower(player)

        embed = discord.Embed(
            title=f"Willpower – {player.get('name', ctx.author.display_name)}",
            color=discord.Color.dark_blue(),
        )
        embed.add_field(name="Max", value=str(wp["max"]), inline=True)
        embed.add_field(name="Current", value=str(cur), inline=True)
        embed.add_field(name="Superficial", value=str(wp["superficial"]), inline=True)
        embed.add_field(name="Aggravated", value=str(wp["aggravated"]), inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="stain")
    async def add_stain(self, ctx, amount: int = 1):
        """
        Add stains to your Humanity track (Storyteller call).
        """
        guild_data, player = self._get_player(ctx)
        if not player:
            return await ctx.reply("You don't have a character sheet yet.")

        humanity.apply_stain(player, amount)
        self.bot.save_data()

        embed = discord.Embed(
            title=f"Stains – {player.get('name', ctx.author.display_name)}",
            color=discord.Color.dark_orange(),
        )
        embed.add_field(name="Humanity", value=str(character_model.get_humanity(player)), inline=True)
        embed.add_field(name="Stains", value=str(character_model.get_stains(player)), inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="remorse")
    async def remorse(self, ctx):
        """
        Perform a Remorse roll for Humanity & Stains.
        """
        guild_data, player = self._get_player(ctx)
        if not player:
            return await ctx.reply("You don't have a character sheet yet.")

        res = humanity.remorse_roll(player)
        self.bot.save_data()

        rolls_str = " ".join(str(r) for r in res["rolled"])
        embed = discord.Embed(
            title=f"Remorse Roll – {player.get('name', ctx.author.display_name)}",
            color=discord.Color.dark_purple(),
        )
        embed.add_field(name="Rolls", value=rolls_str, inline=False)
        embed.add_field(name="Successes", value=str(res["successes"]), inline=True)
        embed.add_field(
            name="Remorse?",
            value="✅ You feel remorse (keep Humanity)." if res["remorse"] else "❌ No remorse (Humanity drops).",
            inline=False,
        )
        embed.add_field(
            name="Humanity",
            value=f"{res['previous_humanity']} → {res['final_humanity']}",
            inline=True,
        )
        embed.add_field(
            name="Stains",
            value=f"{res['previous_stains']} → {res['final_stains']}",
            inline=True,
        )
        await ctx.send(embed=embed)

    @commands.command(name="v5stats")
    async def v5stats(self, ctx):
        """
        Show your V5 core stats (Hunger, Humanity, Stains, WP, BP).
        """
        guild_data, player = self._get_player(ctx)
        if not player:
            return await ctx.reply("You don't have a character sheet yet.")

        character_model.ensure_character_state(player)

        hunger_val = character_model.get_hunger(player)
        hum = character_model.get_humanity(player)
        stains = character_model.get_stains(player)
        bp = character_model.get_blood_potency(player)
        wp = player["willpower"]
        cur_wp = character_model.current_willpower(player)

        embed = discord.Embed(
            title=f"V5 Stats – {player.get('name', ctx.author.display_name)}",
            color=discord.Color.dark_teal(),
        )
        embed.add_field(name="Hunger", value=str(hunger_val), inline=True)
        embed.add_field(name="Humanity", value=str(hum), inline=True)
        embed.add_field(name="Stains", value=str(stains), inline=True)
        embed.add_field(name="Blood Potency", value=str(bp), inline=True)
        embed.add_field(name="WP Max", value=str(wp["max"]), inline=True)
        embed.add_field(name="WP Current", value=str(cur_wp), inline=True)
        embed.add_field(name="WP Superficial", value=str(wp["superficial"]), inline=True)
        embed.add_field(name="WP Aggravated", value=str(wp["aggravated"]), inline=True)
        embed.add_field(
            name="Frenzy State",
            value="🐺 Frenzied" if player.get("frenzy_state") else "Calm",
            inline=True,
        )

        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(VtMV5Cog(bot))