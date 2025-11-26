import discord
from discord.ext import commands

from core.utils import get_guild_data
from core.disciplines.loader import (
    load_disciplines,
    get_discipline,
    list_discipline_names,
    load_blood_rituals,
    find_ritual_by_name,
)


class DisciplinesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # --------- General Lists --------- #

    @commands.command(name="disciplines")
    async def list_disciplines(self, ctx: commands.Context):
        """
        Show all disciplines known in the rules library.
        """
        data = load_disciplines()
        disc_map = data.get("disciplines", {})

        if not disc_map:
            return await ctx.reply("No disciplines loaded.")

        lines = []
        for key, disc in sorted(disc_map.items()):
            lines.append(f"**{disc.get('name', key.title())}** (`{key}`) – {disc.get('summary', '')}")

        embed = discord.Embed(
            title="Available Disciplines",
            description="\n".join(lines),
            color=discord.Color.purple()
        )
        await ctx.send(embed=embed)

    @commands.command(name="powers")
    async def list_powers_for_discipline(self, ctx: commands.Context, discipline: str):
        """
        List powers for a given discipline key (e.g. !powers potence).
        """
        disc = get_discipline(discipline)
        if not disc:
            return await ctx.reply(f"Unknown discipline: `{discipline}`. Try `!disciplines`.")

        powers = disc.get("powers", [])
        if not powers:
            return await ctx.reply(f"No powers defined for `{discipline}` yet.")

        lines = []
        for p in sorted(powers, key=lambda x: int(x.get("level", 0))):
            lines.append(
                f"**[{p.get('level')}] {p.get('name')}** – {p.get('summary', '')}"
            )

        embed = discord.Embed(
            title=f"Powers – {disc.get('name')}",
            description="\n".join(lines),
            color=discord.Color.dark_purple()
        )
        await ctx.send(embed=embed)

    @commands.command(name="power")
    async def show_single_power(
        self,
        ctx: commands.Context,
        discipline: str,
        *,
        power_name_or_level: str
    ):
        """
        Show detail for a single power.
        You can use:
          !power potence 1
          !power potence Lethal Body
        """
        disc = get_discipline(discipline)
        if not disc:
            return await ctx.reply(f"Unknown discipline: `{discipline}`.")

        powers = disc.get("powers", [])
        if not powers:
            return await ctx.reply(f"No powers defined for `{discipline}`.")

        power = None

        # If numeric: treat as level
        if power_name_or_level.isdigit():
            lvl = int(power_name_or_level)
            # First power at that level
            for p in powers:
                if int(p.get("level", 0)) == lvl:
                    power = p
                    break
        else:
            # Match by name
            target = power_name_or_level.lower()
            for p in powers:
                if p.get("name", "").lower() == target:
                    power = p
                    break

        if not power:
            return await ctx.reply("Power not found. Try `!powers <discipline>` to see options.")

        embed = discord.Embed(
            title=f"{disc.get('name')} – {power.get('name')}",
            color=discord.Color.purple()
        )
        embed.add_field(name="Level", value=str(power.get("level", "?")), inline=True)
        embed.add_field(name="Type", value=power.get("type", "unknown"), inline=True)
        embed.add_field(name="Rouse Cost", value=str(power.get("rouse_cost", 0)), inline=True)

        tags = ", ".join(power.get("tags", [])) or "none"
        embed.add_field(name="Tags", value=tags, inline=False)

        embed.add_field(
            name="Summary",
            value=power.get("summary", "No description."),
            inline=False
        )

        effects = power.get("effects") or {}
        if effects:
            effect_lines = [f"- **{k}**: {v}" for k, v in effects.items()]
            embed.add_field(
                name="Mechanical Hints",
                value="\n".join(effect_lines),
                inline=False
            )

        await ctx.send(embed=embed)

    # --------- Character-specific discipline view --------- #

    @commands.command(name="mypowers")
    async def my_powers(self, ctx: commands.Context):
        """
        Show the powers tied to your sheet's disciplines.
        """
        guild_id = ctx.guild.id
        user_id = str(ctx.author.id)

        g_data = get_guild_data(guild_id)
        player = g_data.get("players", {}).get(user_id)

        if not player:
            return await ctx.reply("You don't have a character sheet yet.")

        sheet_disc = player.get("disciplines", {}) or {}
        if not sheet_disc:
            return await ctx.reply("Your sheet has no disciplines recorded.")

        rules = load_disciplines().get("disciplines", {})
        lines = []

        for disc_key, rating in sheet_disc.items():
            disc_block = rules.get(disc_key.lower())
            if not disc_block:
                lines.append(f"**{disc_key}** {rating} – (no rules entry)")
                continue

            lines.append(f"**{disc_block.get('name')}** {rating}")
            powers = [
                p for p in disc_block.get("powers", [])
                if int(p.get("level", 0)) <= int(rating)
            ]
            for p in sorted(powers, key=lambda x: int(x.get("level", 0))):
                lines.append(f"  • [L{p.get('level')}] {p.get('name')}")

        embed = discord.Embed(
            title=f"{player.get('name', ctx.author.display_name)} – Known Disciplines",
            description="\n".join(lines),
            color=discord.Color.dark_red()
        )
        await ctx.send(embed=embed)

    # --------- Blood Rituals --------- #

    @commands.command(name="rituals")
    async def list_rituals(self, ctx: commands.Context):
        """
        List all blood rituals in the library.
        """
        rituals = load_blood_rituals()
        if not rituals:
            return await ctx.reply("No blood rituals defined.")

        lines = []
        for r in sorted(rituals, key=lambda x: (int(x.get("level", 0)), x.get("name", ""))):
            lines.append(
                f"**[L{r.get('level')}] {r.get('name')}** – {r.get('summary', '')}"
            )

        embed = discord.Embed(
            title="Blood Rituals",
            description="\n".join(lines),
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

    @commands.command(name="ritual")
    async def show_ritual(self, ctx: commands.Context, *, name: str):
        """
        Show detail for a single ritual by name.
        """
        ritual = find_ritual_by_name(name)
        if not ritual:
            return await ctx.reply("Ritual not found. Try `!rituals` to list all of them.")

        embed = discord.Embed(
            title=f"{ritual.get('name')} (Level {ritual.get('level')})",
            color=discord.Color.dark_red()
        )
        embed.add_field(name="Discipline", value=ritual.get("discipline", "Blood Sorcery"), inline=True)
        embed.add_field(name="Casting Time", value=ritual.get("casting_time", "?"), inline=True)
        embed.add_field(name="Rouse Cost", value=str(ritual.get("rouse_cost", 0)), inline=True)

        embed.add_field(name="Dice Pool", value=ritual.get("dice_pool", "Storyteller"), inline=False)
        embed.add_field(name="Difficulty", value=str(ritual.get("difficulty", "?")), inline=False)

        tags = ", ".join(ritual.get("tags", [])) or "none"
        embed.add_field(name="Tags", value=tags, inline=False)

        ingredients = ritual.get("ingredients", [])
        if ingredients:
            embed.add_field(
                name="Ingredients",
                value="\n".join(f"- {i}" for i in ingredients),
                inline=False
            )

        embed.add_field(
            name="Summary",
            value=ritual.get("summary", "No description."),
            inline=False
        )

        mech = ritual.get("mechanical_effect")
        if mech:
            embed.add_field(
                name="Mechanical Effect",
                value=mech,
                inline=False
            )

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(DisciplinesCog(bot))