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
    predator_types,
)


class VtMV5Cog(commands.Cog):
    """
    Core V5 rules interface + upgraded character-sheet helpers.

    Commands:
      Rolls & tests:
        !v5roll <dice_pool> <difficulty> [reason]
        !rouse
        !frenzy <dice_pool> <difficulty>
        !remorse

      Tracks / stats:
        !wp              - show willpower
        !stain [amount]  - add stains
        !v5stats         - show core V5 stats
        !v5sheet         - compact sheet summary

      Predator type & feeding:
        !predator [name]       - set or view Predator Type
        !predatorinfo <name>   - info on a Predator Type
        !feed <source> [amt]   - feeding with Predator rules

      Sheet creation / narrative bits:
        !v5create <name> <clan> [predator_type]
        !touchstones           - list touchstones
        !merits                - list merits
        !flaws                 - list flaws
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # -------------------------------------------------
    # Helpers
    # -------------------------------------------------

    def _get_player(self, ctx):
        """
        Returns (guild_data, player_dict or None).
        Uses the same access pattern as your other cogs:
          get_guild_data(self.bot.data_store, guild_id)
        """
        guild_data = get_guild_data(self.bot.data_store, ctx.guild.id)
        player = guild_data.get("players", {}).get(str(ctx.author.id))
        if player is None:
            return guild_data, None
        character_model.ensure_character_state(player)
        return guild_data, player

    # -------------------------------------------------
    # Sheet creation / overview
    # -------------------------------------------------

    @commands.command(name="v5create")
    async def v5create(self, ctx, name: str, clan: str, predator: str = ""):
        """
        Create or upgrade your character sheet to full V5 format.

        Usage:
          !v5create Alice Tremere alleycat
          !v5create "Jean-Luc" Ventrue bagger

        - Ensures V5 tracks (Hunger, WP, Humanity, BP, Predator, Merits/Flaws,
          Touchstones, Havens) exist.
        - Optionally sets a Predator Type by name or key.
        """
        guild_data = get_guild_data(self.bot.data_store, ctx.guild.id)
        players = guild_data.setdefault("players", {})
        pid = str(ctx.author.id)
        player = players.get(pid, {"id": pid})

        # basic meta
        player["name"] = name
        player["clan"] = clan

        predator_key = None
        predator_name = None
        if predator:
            pt = predator_types.get_predator_type(predator)
            if not pt:
                await ctx.reply(
                    f"Unknown predator type `{predator}`. Sheet created without predator type.\n"
                    f"Use `!predator` to see options."
                )
            else:
                predator_key = pt["key"]
                predator_name = pt["name"]

        character_model.bootstrap_v5_character(
            player,
            name=name,
            clan=clan,
            predator_key=predator_key,
            predator_name=predator_name,
        )

        players[pid] = player
        # Persist via bot's save hook if it exists
        save = getattr(self.bot, "save_data", None)
        if callable(save):
            save()

        predator_display = predator_name or "None"
        embed = discord.Embed(
            title="V5 Sheet Created/Updated",
            description=(
                f"**Name:** {player.get('name')}\n"
                f"**Clan:** {player.get('clan')}\n"
                f"**Predator Type:** {predator_display}"
            ),
            color=discord.Color.dark_red(),
        )
        embed.add_field(name="Hunger", value=str(character_model.get_hunger(player)), inline=True)
        embed.add_field(name="Humanity", value=str(character_model.get_humanity(player)), inline=True)
        embed.add_field(name="Blood Potency", value=str(character_model.get_blood_potency(player)), inline=True)

        await ctx.send(embed=embed)

    @commands.command(name="v5sheet")
    async def v5sheet(self, ctx):
        """
        Compact V5 sheet summary:
        - Hunger, Humanity, Stains, BP
        - Willpower track
        - Predator type
        - Counts of Merits, Flaws, Touchstones, Havens
        """
        guild_data, player = self._get_player(ctx)
        if not player:
            return await ctx.reply("You don't have a character sheet yet. Use `!v5create` first.")

        character_model.ensure_character_state(player)

        hunger_val = character_model.get_hunger(player)
        hum = character_model.get_humanity(player)
        stains = character_model.get_stains(player)
        bp = character_model.get_blood_potency(player)
        wp_block = character_model.get_willpower_block(player)
        cur_wp = character_model.current_willpower(player)
        predator_name = character_model.get_predator_type_name(player) or "None"

        merits = character_model.list_merits(player)
        flaws = character_model.list_flaws(player)
        touchstones = character_model.list_touchstones(player)
        havens = character_model.list_havens(player)

        embed = discord.Embed(
            title=f"V5 Sheet – {player.get('name', ctx.author.display_name)}",
            color=discord.Color.dark_teal(),
        )
        embed.add_field(name="Clan", value=player.get("clan", "Unknown"), inline=True)
        embed.add_field(name="Predator Type", value=predator_name, inline=True)
        embed.add_field(name="Blood Potency", value=str(bp), inline=True)

        embed.add_field(name="Hunger", value=str(hunger_val), inline=True)
        embed.add_field(name="Humanity", value=str(hum), inline=True)
        embed.add_field(name="Stains", value=str(stains), inline=True)

        embed.add_field(name="WP Max", value=str(wp_block["max"]), inline=True)
        embed.add_field(name="WP Current", value=str(cur_wp), inline=True)
        embed.add_field(
            name="WP Damage",
            value=f"Sup {wp_block['superficial']}, Agg {wp_block['aggravated']}",
            inline=True,
        )

        embed.add_field(name="Merits", value=str(len(merits)), inline=True)
        embed.add_field(name="Flaws", value=str(len(flaws)), inline=True)
        embed.add_field(name="Touchstones", value=str(len(touchstones)), inline=True)
        embed.add_field(name="Havens", value=str(len(havens)), inline=True)

        await ctx.send(embed=embed)

    @commands.command(name="touchstones")
    async def list_touchstones_cmd(self, ctx):
        """
        List all touchstones on your sheet.
        """
        guild_data, player = self._get_player(ctx)
        if not player:
            return await ctx.reply("You don't have a character sheet yet.")

        tstones = character_model.list_touchstones(player)
        if not tstones:
            return await ctx.reply("You have no recorded touchstones yet.")

        lines = []
        for ts in tstones:
            status = "💚 Alive" if ts.get("alive", True) else "🩸 Lost"
            name = ts.get("name", "Unknown")
            desc = ts.get("description", "")
            note = ts.get("note", "")
            line = f"**{name}** – {status}"
            if desc:
                line += f"\n> {desc}"
            if note:
                line += f"\n_(Note: {note})_"
            lines.append(line)

        embed = discord.Embed(
            title=f"Touchstones – {player.get('name', ctx.author.display_name)}",
            description="\n\n".join(lines),
            color=discord.Color.light_grey(),
        )
        await ctx.send(embed=embed)

    @commands.command(name="merits")
    async def list_merits_cmd(self, ctx):
        guild_data, player = self._get_player(ctx)
        if not player:
            return await ctx.reply("You don't have a character sheet yet.")

        merits = character_model.list_merits(player)
        if not merits:
            return await ctx.reply("You have no recorded merits yet.")

        lines = []
        for m in merits:
            dots = "•" * int(m.get("dots", 1))
            name = m.get("name", "Unknown")
            note = m.get("note", "")
            line = f"**{name}** ({dots})"
            if note:
                line += f" – {note}"
            lines.append(line)

        embed = discord.Embed(
            title=f"Merits – {player.get('name', ctx.author.display_name)}",
            description="\n".join(lines),
            color=discord.Color.dark_green(),
        )
        await ctx.send(embed=embed)

    @commands.command(name="flaws")
    async def list_flaws_cmd(self, ctx):
        guild_data, player = self._get_player(ctx)
        if not player:
            return await ctx.reply("You don't have a character sheet yet.")

        flaws = character_model.list_flaws(player)
        if not flaws:
            return await ctx.reply("You have no recorded flaws yet.")

        lines = []
        for f in flaws:
            dots = "•" * int(f.get("dots", 1))
            name = f.get("name", "Unknown")
            note = f.get("note", "")
            line = f"**{name}** ({dots})"
            if note:
                line += f" – {note}"
            lines.append(line)

        embed = discord.Embed(
            title=f"Flaws – {player.get('name', ctx.author.display_name)}",
            description="\n".join(lines),
            color=discord.Color.dark_orange(),
        )
        await ctx.send(embed=embed)

    # -------------------------------------------------
    # Dice & core tests
    # -------------------------------------------------

    @commands.command(name="v5roll")
    async def v5roll(self, ctx, dice_pool: int, difficulty: int, *, reason: str = ""):
        """
        Roll a V5 dice pool:
          !v5roll 6 2 punch_the_guy
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

        messy_or_bestial = res["messy_critical"] or res["bestial_failure"]
        color = discord.Color.red() if messy_or_bestial else discord.Color.dark_grey()

        embed = discord.Embed(title=title, color=color)
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
        Perform a Rouse Check for your character.
        """
        guild_data, player = self._get_player(ctx)
        if not player:
            return await ctx.reply("You don't have a character sheet yet.")

        res = hunger.rouse_check(player)
        if callable(getattr(self.bot, "save_data", None)):
            self.bot.save_data()

        embed = discord.Embed(
            title=f"Rouse Check – {player.get('name', ctx.author.display_name)}",
            color=discord.Color.dark_red(),
        )
        embed.add_field(name="Roll", value=str(res["roll"]), inline=True)
        embed.add_field(
            name="Result",
            value="Success" if res["success"] else "Failure (Hunger +1)",
            inline=True,
        )
        embed.add_field(
            name="Hunger",
            value=f"{res['old_hunger']} → {res['new_hunger']}",
            inline=False,
        )

        await ctx.send(embed=embed)

    @commands.command(name="frenzy")
    async def frenzy(self, ctx, dice_pool: int, difficulty: int):
        """
        Frenzy / Rötschreck test:
          !frenzy 5 3
        """
        guild_data, player = self._get_player(ctx)
        if not player:
            return await ctx.reply("You don't have a character sheet yet.")

        res = frenzy_mod.frenzy_test(player, dice_pool, difficulty)
        if callable(getattr(self.bot, "save_data", None)):
            self.bot.save_data()

        roll = res["result"]
        dice_str = " ".join(str(d) for d in roll["dice"])
        hunger_str = " ".join(str(d) for d in roll["hunger_dice"])

        color = discord.Color.dark_red() if res["failed"] else discord.Color.dark_green()
        embed = discord.Embed(
            title=f"Frenzy Test – {player.get('name', ctx.author.display_name)}",
            color=color,
        )
        embed.add_field(name="Dice Pool", value=str(dice_pool), inline=True)
        embed.add_field(name="Difficulty", value=str(difficulty), inline=True)
        embed.add_field(name="Hunger", value=str(character_model.get_hunger(player)), inline=True)

        embed.add_field(name="Normal Dice", value=dice_str or "—", inline=False)
        embed.add_field(name="Hunger Dice", value=hunger_str or "—", inline=False)
        embed.add_field(name="Successes", value=str(roll["successes"]), inline=True)

        state = "🐺 Frenzied!" if res["failed"] else "Calm"
        embed.add_field(name="Outcome", value=state, inline=False)

        await ctx.send(embed=embed)

    @commands.command(name="wp")
    async def show_willpower(self, ctx):
        """
        Show your Willpower track.
        """
        guild_data, player = self._get_player(ctx)
        if not player:
            return await ctx.reply("You don't have a character sheet yet.")

        wp = character_model.get_willpower_block(player)
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
        Add Stains to your Humanity track (Storyteller call).
        """
        guild_data, player = self._get_player(ctx)
        if not player:
            return await ctx.reply("You don't have a character sheet yet.")

        humanity.apply_stain(player, amount=amount)
        if callable(getattr(self.bot, "save_data", None)):
            self.bot.save_data()

        embed = discord.Embed(
            title=f"Stains Applied – {player.get('name', ctx.author.display_name)}",
            color=discord.Color.dark_red(),
        )
        embed.add_field(name="New Stains", value=str(character_model.get_stains(player)), inline=True)
        embed.add_field(name="Humanity", value=str(character_model.get_humanity(player)), inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="remorse")
    async def remorse(self, ctx):
        """
        Perform a Remorse roll for your character.
        """
        guild_data, player = self._get_player(ctx)
        if not player:
            return await ctx.reply("You don't have a character sheet yet.")

        res = humanity.remorse_roll(player)
        if callable(getattr(self.bot, "save_data", None)):
            self.bot.save_data()

        embed = discord.Embed(
            title=f"Remorse Roll – {player.get('name', ctx.author.display_name)}",
            color=discord.Color.dark_purple(),
        )
        embed.add_field(name="Dice", value=str(res["dice"]), inline=True)
        embed.add_field(name="Successes", value=str(res["successes"]), inline=True)
        embed.add_field(
            name="Result",
            value="Remorse" if res["remorse"] else "No Remorse",
            inline=True,
        )
        embed.add_field(name="Humanity", value=str(res["new_humanity"]), inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="v5stats")
    async def v5stats(self, ctx):
        """
        Show core V5 state (tracks + predator + frenzy state).
        """
        guild_data, player = self._get_player(ctx)
        if not player:
            return await ctx.reply("You don't have a character sheet yet.")

        character_model.ensure_character_state(player)

        hunger_val = character_model.get_hunger(player)
        hum = character_model.get_humanity(player)
        stains = character_model.get_stains(player)
        bp = character_model.get_blood_potency(player)
        wp = character_model.get_willpower_block(player)
        cur_wp = character_model.current_willpower(player)
        predator_name = character_model.get_predator_type_name(player) or "None"

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
        embed.add_field(name="Predator Type", value=predator_name, inline=True)
        embed.add_field(
            name="Frenzy State",
            value="🐺 Frenzied" if player.get("frenzy_state") else "Calm",
            inline=True,
        )

        await ctx.send(embed=embed)

    # -------------------------------------------------
    # Predator types & feeding
    # -------------------------------------------------

    @commands.command(name="predator")
    async def predator(self, ctx, *, name: str = ""):
        """
        View or set your Predator Type.
          !predator              -> show current
          !predator alleycat     -> set to Alleycat
        """
        guild_data, player = self._get_player(ctx)
        if not player:
            return await ctx.reply("You don't have a character sheet yet.")

        if not name:
            current = character_model.get_predator_type_name(player)
            if not current:
                return await ctx.reply(
                    "No predator type s