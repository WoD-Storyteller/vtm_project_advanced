import discord
from discord.ext import commands

from utils import get_guild_data
from core.vtmv5 import character_model, merits_flaws, humanity


class VtMCharacterCog(commands.Cog):
    """
    Extended V5 character sheet management.

    Commands (player-facing):
      !merits                 – list your Merits
      !add_merit <name> <dots> [type] [note...]
      !remove_merit <name>

      !flaws                  – list your Flaws
      !add_flaw <name> <dots> [type] [note...]
      !remove_flaw <name>

      !convictions            – list your Convictions
      !add_conviction <text>
      !remove_conviction <index>

      !touchstones            – list your Touchstones
      !add_touchstone <name> <role>
      !kill_touchstone <name> [deliberate: yes/no]
      !remove_touchstone <name>
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # --------------------------------------------------
    # Helpers
    # --------------------------------------------------

    def _get_player(self, ctx):
        """
        Mirror of VtMV5Cog._get_player – uses the shared data_store.
        """
        guild_data = get_guild_data(self.bot.data_store, ctx.guild.id)
        player = guild_data.get("players", {}).get(str(ctx.author.id))
        if player is None:
            return guild_data, None
        character_model.ensure_character_state(player)
        return guild_data, player

    async def _require_player(self, ctx):
        guild_data, player = self._get_player(ctx)
        if not player:
            await ctx.reply("You don't have a character sheet yet.")
            return None, None
        return guild_data, player

    # --------------------------------------------------
    # Merits
    # --------------------------------------------------

    @commands.command(name="merits")
    async def list_merits_cmd(self, ctx: commands.Context):
        guild_data, player = await self._require_player(ctx)
        if not player:
            return

        merits = character_model.list_merits(player)
        if not merits:
            return await ctx.reply("You currently have no recorded Merits.")

        lines = []
        for m in merits:
            dots = "•" * int(m.get("dots", 1))
            mtype = m.get("type", "general")
            note = m.get("note", "")
            line = f"**{m.get('name', 'Unnamed')}** ({dots}, {mtype})"
            if note:
                line += f" – {note}"
            lines.append(line)

        embed = discord.Embed(
            title=f"Merits – {player.get('name', ctx.author.display_name)}",
            description="\n".join(lines)[:4096],
            color=discord.Color.dark_green(),
        )
        await ctx.send(embed=embed)

    @commands.command(name="add_merit")
    async def add_merit_cmd(
        self,
        ctx: commands.Context,
        name: str,
        dots: int,
        mtype: str = "general",
        *,
        note: str = "",
    ):
        guild_data, player = await self._require_player(ctx)
        if not player:
            return

        # Try to match a registered merit first
        reg = merits_flaws.get_merit(name)
        if reg:
            name = reg["name"]
            dots = reg.get("dots", dots)
            mtype = reg.get("category", mtype)
            tags = reg.get("tags", [])
        else:
            tags = []

        character_model.add_merit(
            player,
            name=name,
            dots=dots,
            m_type=mtype,
            tags=tags,
            note=note,
        )
        self.bot.save_data()

        await ctx.reply(f"✅ Merit **{name} ({dots})** added/updated.")

    @commands.command(name="remove_merit")
    async def remove_merit_cmd(self, ctx: commands.Context, *, name: str):
        guild_data, player = await self._require_player(ctx)
        if not player:
            return

        character_model.remove_merit(player, name)
        self.bot.save_data()
        await ctx.reply(f"✅ Merit **{name}** removed (if it existed).")

    # --------------------------------------------------
    # Flaws
    # --------------------------------------------------

    @commands.command(name="flaws")
    async def list_flaws_cmd(self, ctx: commands.Context):
        guild_data, player = await self._require_player(ctx)
        if not player:
            return

        flaws = character_model.list_flaws(player)
        if not flaws:
            return await ctx.reply("You currently have no recorded Flaws.")

        lines = []
        for f in flaws:
            dots = "•" * int(f.get("dots", 1))
            ftype = f.get("type", "general")
            note = f.get("note", "")
            line = f"**{f.get('name', 'Unnamed')}** ({dots}, {ftype})"
            if note:
                line += f" – {note}"
            lines.append(line)

        embed = discord.Embed(
            title=f"Flaws – {player.get('name', ctx.author.display_name)}",
            description="\n".join(lines)[:4096],
            color=discord.Color.dark_red(),
        )
        await ctx.send(embed=embed)

    @commands.command(name="add_flaw")
    async def add_flaw_cmd(
        self,
        ctx: commands.Context,
        name: str,
        dots: int,
        ftype: str = "general",
        *,
        note: str = "",
    ):
        guild_data, player = await self._require_player(ctx)
        if not player:
            return

        reg = merits_flaws.get_flaw(name)
        if reg:
            name = reg["name"]
            dots = reg.get("dots", dots)
            ftype = reg.get("category", ftype)
            tags = reg.get("tags", [])
        else:
            tags = []

        character_model.add_flaw(
            player,
            name=name,
            dots=dots,
            f_type=ftype,
            tags=tags,
            note=note,
        )
        self.bot.save_data()

        await ctx.reply(f"✅ Flaw **{name} ({dots})** added/updated.")

    @commands.command(name="remove_flaw")
    async def remove_flaw_cmd(self, ctx: commands.Context, *, name: str):
        guild_data, player = await self._require_player(ctx)
        if not player:
            return

        character_model.remove_flaw(player, name)
        self.bot.save_data()
        await ctx.reply(f"✅ Flaw **{name}** removed (if it existed).")

    # --------------------------------------------------
    # Convictions
    # --------------------------------------------------

    @commands.command(name="convictions")
    async def list_convictions_cmd(self, ctx: commands.Context):
        guild_data, player = await self._require_player(ctx)
        if not player:
            return

        convs = character_model.list_convictions(player)
        if not convs:
            return await ctx.reply("You currently have no recorded Convictions.")

        lines = [f"{idx+1}. {c.get('text', '')}" for idx, c in enumerate(convs)]
        embed = discord.Embed(
            title=f"Convictions – {player.get('name', ctx.author.display_name)}",
            description="\n".join(lines)[:4096],
            color=discord.Color.gold(),
        )
        await ctx.send(embed=embed)

    @commands.command(name="add_conviction")
    async def add_conviction_cmd(self, ctx: commands.Context, *, text: str):
        guild_data, player = await self._require_player(ctx)
        if not player:
            return

        character_model.add_conviction(player, text=text)
        self.bot.save_data()
        await ctx.reply("✅ Conviction added.")

    @commands.command(name="remove_conviction")
    async def remove_conviction_cmd(self, ctx: commands.Context, index: int):
        guild_data, player = await self._require_player(ctx)
        if not player:
            return

        # user sees 1-based index; we store 0-based
        character_model.remove_conviction(player, index - 1)
        self.bot.save_data()
        await ctx.reply(f"✅ Conviction #{index} removed (if it existed).")

    # --------------------------------------------------
    # Touchstones
    # --------------------------------------------------

    @commands.command(name="touchstones")
    async def list_touchstones_cmd(self, ctx: commands.Context):
        guild_data, player = await self._require_player(ctx)
        if not player:
            return

        tstones = character_model.list_touchstones(player)
        if not tstones:
            return await ctx.reply("You currently have no recorded Touchstones.")

        lines = []
        for ts in tstones:
            name = ts.get("name", "Unnamed")
            role = ts.get("role", "")
            alive = ts.get("alive", True)
            status = "🟢 Alive" if alive else "⚫ Dead"
            if role:
                lines.append(f"**{name}** – {role} ({status})")
            else:
                lines.append(f"**{name}** ({status})")

        embed = discord.Embed(
            title=f"Touchstones – {player.get('name', ctx.author.display_name)}",
            description="\n".join(lines)[:4096],
            color=discord.Color.purple(),
        )
        await ctx.send(embed=embed)

    @commands.command(name="add_touchstone")
    async def add_touchstone_cmd(
        self,
        ctx: commands.Context,
        name: str,
        *,
        role: str = "",
    ):
        guild_data, player = await self._require_player(ctx)
        if not player:
            return

        character_model.add_touchstone(player, name=name, role=role)
        self.bot.save_data()
        await ctx.reply(f"✅ Touchstone **{name}** added as '{role}'.")

    @commands.command(name="kill_touchstone")
    async def kill_touchstone_cmd(
        self,
        ctx: commands.Context,
        name: str,
        deliberate: str = "yes",
    ):
        """
        Mark a touchstone as dead and apply Stains.

        Usage:
          !kill_touchstone Alice
          !kill_touchstone Alice no   (for non-deliberate / tragic loss)
        """
        guild_data, player = await self._require_player(ctx)
        if not player:
            return

        deliberate_flag = str(deliberate).lower() not in ("no", "false", "0")
        humanity.apply_touchstone_loss(player, name=name, deliberate=deliberate_flag)
        self.bot.save_data()

        if deliberate_flag:
            msg = (
                f"Touchstone **{name}** marked dead. "
                "This deliberate loss inflicts extra Stains."
            )
        else:
            msg = (
                f"Touchstone **{name}** marked dead. "
                "Stains applied for tragic loss."
            )
        await ctx.reply(f"⚫ {msg}")

    @commands.command(name="remove_touchstone")
    async def remove_touchstone_cmd(self, ctx: commands.Context, *, name: str):
        guild_data, player = await self._require_player(ctx)
        if not player:
            return

        character_model.remove_touchstone(player, name)
        self.bot.save_data()
        await ctx.reply(f"✅ Touchstone **{name}** removed (if it existed).")


async def setup(bot: commands.Bot):
    await bot.add_cog(VtMCharacterCog(bot))