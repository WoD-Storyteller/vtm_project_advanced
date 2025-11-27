import discord
from discord.ext import commands

from utils import get_guild_data
from core.havens.haven_registry import HavenRegistry
from core.havens.haven_engine import HavenEngine
from core.travel.zones_loader import ZoneRegistry
from core.havens.sheets_loader import load_sheet_havens, save_havens_file
from core.vtmv5 import character_model


class HavenCog(commands.Cog):
    """
    Player & ST Haven / Domain commands.

    Player:
      !havens                  – list your havens
      !haven here <name>       – create a haven in your current zone
      !haven create <zone> <name> – create a haven by zone key/name
      !haven info <id|name>    – show haven details
      !haven primary <id|name> – set your primary haven

    ST:
      !sync_havens             – sync havens from Google Sheet
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.zone_registry: ZoneRegistry = getattr(bot, "zone_registry", ZoneRegistry())
        self.zone_registry.load()

        self.haven_registry = HavenRegistry()
        self.engine = HavenEngine(self.haven_registry, self.zone_registry)

    # -------------------------------------------------
    # Helpers
    # -------------------------------------------------
    def _format_haven(self, haven) -> str:
        from core.travel.zones_loader import ZoneRegistry

        z_reg = self.zone_registry
        zone = z_reg.get(haven.zone_key) or z_reg.find(haven.zone_key) or None

        lines = [f"**{haven.name}** (`{haven.id}`)"]
        if zone:
            lines.append(f"Zone: {zone.name} (`{zone.key}`)")
        else:
            lines.append(f"Zone: `{haven.zone_key}`")

        lines.append(f"Owners: {', '.join(haven.owner_ids) or 'None'}")
        lines.append(f"Security: {haven.security} | Luxury: {haven.luxury}")

        d = haven.domain
        lines.append(
            "Domain – "
            f"Feeding: {d.get('feeding', 0)}, "
            f"Masq Buffer: {d.get('masquerade_buffer', 0)}, "
            f"Warding: {d.get('warding_level', 0)}, "
            f"Influence: {d.get('influence', 0)}"
        )

        if haven.rooms:
            lines.append(f"Rooms: {', '.join(haven.rooms)}")
        if haven.tags:
            lines.append(f"Tags: {', '.join(haven.tags)}")

        return "\n".join(lines)

    # -------------------------------------------------
    # Player commands
    # -------------------------------------------------
    @commands.command(name="havens")
    async def list_havens(self, ctx: commands.Context):
        """
        List all havens you have access to.
        """
        guild_data = get_guild_data(self.bot.data_store, ctx.guild.id)
        players = guild_data.get("players") or {}
        player = players.get(str(ctx.author.id))

        if not player:
            return await ctx.reply("You do not have a character sheet.")

        owns = self.engine.get_player_havens(str(ctx.author.id))
        primary = character_model.get_primary_haven_id(player)

        if not owns:
            return await ctx.reply("You do not currently own any havens.")

        lines = []
        for h in owns:
            prefix = "⭐ " if h.id == primary else "• "
            lines.append(prefix + f"**{h.name}** (`{h.id}`) in `{h.zone_key}`")

        embed = discord.Embed(
            title=f"{ctx.author.display_name}'s Havens",
            description="\n".join(lines),
            color=discord.Color.dark_gold(),
        )
        await ctx.send(embed=embed)

    @commands.command(name="haven_here")
    async def haven_here(self, ctx: commands.Context, *, name: str):
        """
        Create a haven at your current location_key.
        """
        guild_data = get_guild_data(self.bot.data_store, ctx.guild.id)
        players = guild_data.get("players") or {}
        player = players.get(str(ctx.author.id))

        if not player:
            return await ctx.reply("You do not have a character sheet.")

        character_model.ensure_character_state(player)

        zone_key = player.get("location_key") or self.zone_registry.default_zone_key()
        zone = self.zone_registry.get(zone_key) or self.zone_registry.find(zone_key)

        if not zone:
            return await ctx.reply("Your current location is not a valid zone; ask the ST to fix it first.")

        haven = self.engine.create_haven_for_player(
            player_id=str(ctx.author.id),
            name=name,
            zone_key=zone.key,
            lat=zone.latitude,
            lng=zone.longitude,
        )

        # If they have no primary haven yet, set this as primary
        if not character_model.get_primary_haven_id(player):
            character_model.set_primary_haven_id(player, haven.id)
            self.bot.save_data()

        description = self._format_haven(haven)

        embed = discord.Embed(
            title="Haven Established",
            description=description,
            color=discord.Color.dark_gold(),
        )
        await ctx.send(embed=embed)

    @commands.command(name="haven")
    async def haven_create_zone(self, ctx: commands.Context, zone: str, *, name: str):
        """
        Create a haven in a named zone (by key or fuzzy name).
        """
        guild_data = get_guild_data(self.bot.data_store, ctx.guild.id)
        players = guild_data.get("players") or {}
        player = players.get(str(ctx.author.id))

        if not player:
            return await ctx.reply("You do not have a character sheet.")

        character_model.ensure_character_state(player)

        z = self.zone_registry.find(zone)
        if not z:
            return await ctx.reply(f"Unknown zone `{zone}`.")

        haven = self.engine.create_haven_for_player(
            player_id=str(ctx.author.id),
            name=name,
            zone_key=z.key,
            lat=z.latitude,
            lng=z.longitude,
        )

        if not character_model.get_primary_haven_id(player):
            character_model.set_primary_haven_id(player, haven.id)
            self.bot.save_data()

        embed = discord.Embed(
            title="Haven Established",
            description=self._format_haven(haven),
            color=discord.Color.dark_gold(),
        )
        await ctx.send(embed=embed)

    @commands.command(name="haven_info")
    async def haven_info(self, ctx: commands.Context, *, token: str):
        """
        Show details for one haven by id or name.
        """
        haven = self.engine.get_haven_by_id_or_name(token)
        if not haven:
            return await ctx.reply(f"No haven found for `{token}`.")

        embed = discord.Embed(
            title="Haven Info",
            description=self._format_haven(haven),
            color=discord.Color.dark_gold(),
        )

        if haven.maps:
            lines = []
            for m in haven.maps:
                label = m.get("map_name") or "Map"
                url = m.get("url", "")
                mtype = m.get("type", "mymaps")
                lines.append(f"[{label}]({url}) ({mtype})")
            embed.add_field(name="Maps", value="\n".join(lines), inline=False)

        await ctx.send(embed=embed)

    @commands.command(name="haven_primary")
    async def haven_primary(self, ctx: commands.Context, *, token: str):
        """
        Set your primary haven by id or name.
        """
        guild_data = get_guild_data(self.bot.data_store, ctx.guild.id)
        players = guild_data.get("players") or {}
        player = players.get(str(ctx.author.id))

        if not player:
            return await ctx.reply("You do not have a character sheet.")

        haven = self.engine.get_haven_by_id_or_name(token)
        if not haven:
            return await ctx.reply(f"No haven found for `{token}`.")

        if str(ctx.author.id) not in haven.owner_ids:
            return await ctx.reply("You are not an owner of that haven.")

        character_model.set_primary_haven_id(player, haven.id)
        self.bot.save_data()

        await ctx.reply(f"Primary haven set to **{haven.name}** (`{haven.id}`).")

    # -------------------------------------------------
    # ST commands
    # -------------------------------------------------
    @commands.command(name="sync_havens")
    @commands.has_permissions(administrator=True)
    async def sync_havens(self, ctx: commands.Context):
        """
        Sync havens from Google Sheets and overwrite data/havens.json
        """
        async with ctx.typing():
            try:
                sheet_havens = load_sheet_havens()
                save_havens_file(sheet_havens)

                self.haven_registry.load()
                await ctx.send("✅ Havens synced from sheet and registry reloaded.")
            except Exception as e:
                await ctx.send(f"❌ Haven sync failed: `{e}`")


async def setup(bot: commands.Bot):
    await bot.add_cog(HavenCog(bot))