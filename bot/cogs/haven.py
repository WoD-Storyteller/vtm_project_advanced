import discord
from discord.ext import commands

from core.utils_bot import get_guild_data, load_data_from_file, save_data
from core.havens.haven_registry import HavenRegistry
from core.havens.haven_engine import HavenEngine
from core.travel.zones_loader import ZoneRegistry
from core.havens.sheets_loader import load_sheet_havens, save_havens_file
from core.vtmv5 import character_model
from core.director.ai_director import AIDirector


class HavenCog(commands.Cog):
    """
    Player & ST Haven / Domain commands.

    Player:
      !havens                     – list your havens
      !haven_here <name>          – create a haven in your current zone
      !haven <zone> <name>        – create a haven by zone key/name
      !haven_info <id|name>       – show haven details
      !haven_primary <id|name>    – set your primary haven
      !haven_rest [id|name]       – rest in your haven (WP/stains/hunger recovery)
      !havenscene [id|name]       – generate an AI scene inside your haven

    ST:
      !sync_havens                – sync havens from Google Sheet
      !haven_raid <id|name> [sev] – trigger a raid on a haven (Director + damage)
      !haven_upgrade <id|name> <stat> <delta>
                                  – tweak domain stats (security, luxury, feeding, etc.)
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

    async def _scene_embed_from_result(self, ctx: commands.Context, scene: dict, title_prefix: str = "Haven Scene"):
        intro = scene.get("intro_text") or "No intro text."
        npcs = scene.get("npcs") or []
        encounter = scene.get("encounter")
        quest_hook = scene.get("quest_hook") or ""
        severity = scene.get("severity") or 1
        severity_label = scene.get("severity_label") or "low"
        director_update = scene.get("director_update") or {}

        embed = discord.Embed(
            title=f"{title_prefix} – Severity {severity} ({severity_label})",
            description=intro,
            color=discord.Color.dark_gold(),
        )

        if npcs:
            npc_text = "\n".join(f"• {n}" for n in npcs)
            embed.add_field(name="NPCs Present", value=npc_text, inline=False)

        if encounter:
            enc_name = encounter.get("name", "Encounter")
            enc_desc = encounter.get("description", "")
            embed.add_field(
                name=f"Encounter – {enc_name}",
                value=enc_desc or "—",
                inline=False,
            )

        if quest_hook:
            embed.add_field(
                name="Quest Hook",
                value=quest_hook,
                inline=False,
            )

        city_state = director_update.get("city_state", director_update)
        if city_state:
            embed.add_field(
                name="City Pressure (Director)",
                value=(
                    f"Masquerade: {city_state.get('masquerade_pressure', 0)}\n"
                    f"Violence: {city_state.get('violence_pressure', 0)}\n"
                    f"Occult: {city_state.get('occult_pressure', 0)}\n"
                    f"SI: {city_state.get('si_pressure', 0)}\n"
                    f"Politics: {city_state.get('political_pressure', 0)}\n"
                    f"Global Threat: {city_state.get('global_threat', 1)}"
                ),
                inline=False,
            )

        return embed

    def _resolve_player_and_haven(
        self,
        ctx: commands.Context,
        token: str | None,
    ):
        """
        Helper: get guild_data, player dict, and a Haven reference.
        If token is None, falls back to primary haven, then first owned.
        """
        guild_data = get_guild_data(self.bot.data_store, ctx.guild.id)
        players = guild_data.get("players") or {}
        player = players.get(str(ctx.author.id))
        if not player:
            return guild_data, None, None

        character_model.ensure_character_state(player)

        # Resolve haven
        haven = None
        if token:
            haven = self.engine.get_haven_by_id_or_name(token)

        if not haven:
            primary_id = character_model.get_primary_haven_id(player)
            if primary_id:
                haven = self.haven_registry.get(primary_id)

        if not haven:
            # fall back to any owned haven
            owned = self.engine.get_player_havens(str(ctx.author.id))
            if owned:
                haven = owned[0]

        return guild_data, player, haven

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

    @commands.command(name="haven_rest")
    async def haven_rest(self, ctx: commands.Context, token: str | None = None):
        """
        Rest in a haven:
          - Recovers superficial Willpower (luxury-based)
          - May reduce a stain
          - May reduce hunger if domain feeding is strong
          - Applies shelter effects to Director
        If no token is given, uses your primary haven (or first owned).
        """
        guild_data, player, haven = self._resolve_player_and_haven(ctx, token)

        if not player:
            return await ctx.reply("You do not have a character sheet.")
        if not haven:
            return await ctx.reply("You do not own any havens yet.")

        result = self.engine.rest_in_haven(player, haven)
        # Persist changes to player data
        self.bot.save_data()

        city = result.get("director", {})

        desc_lines = [
            f"You take time to rest in **{haven.name}**.",
            "",
            f"Willpower: {result['willpower_before']} → {result['willpower_after']} "
            f"(superficial {result['superficial_before']} → {result['superficial_after']})",
            f"Stains: {result['stains_before']} → {result['stains_after']}",
            f"Hunger: {result['hunger_before']} → {result['hunger_after']}",
        ]

        embed = discord.Embed(
            title="Rest in Haven",
            description="\n".join(desc_lines),
            color=discord.Color.green(),
        )

        embed.add_field(
            name="City Pressure (Director)",
            value=(
                f"Masquerade: {city.get('masquerade_pressure', 0)}\n"
                f"Violence: {city.get('violence_pressure', 0)}\n"
                f"Occult: {city.get('occult_pressure', 0)}\n"
                f"SI: {city.get('si_pressure', 0)}\n"
                f"Politics: {city.get('political_pressure', 0)}\n"
                f"Global Threat: {city.get('global_threat', 1)}"
            ),
            inline=False,
        )

        await ctx.send(embed=embed)

    @commands.command(name="havenscene")
    async def haven_scene(self, ctx: commands.Context, token: str | None = None):
        """
        Generate an AI-driven scene inside one of your havens.
        If no token is provided, uses your primary haven (or first owned).
        """
        guild_data, player, haven = self._resolve_player_and_haven(ctx, token)

        if not player:
            return await ctx.reply("You do not have a character sheet.")
        if not haven:
            return await ctx.reply("You do not own any havens yet.")

        zone = self.zone_registry.get(haven.zone_key) or self.zone_registry.find(haven.zone_key)
        location_key = zone.key if zone else haven.zone_key

        # Risk is generally lower in a secure haven; more chaotic if low security.
        base_risk = 2
        risk = max(1, base_risk - (haven.security // 2))

        async with ctx.typing():
            scene = await AIDirector.generate_scene(
                model_text=self.bot.ai_model_text,
                model_json=self.bot.ai_model_json,
                guild_data=guild_data,
                guild_id=ctx.guild.id,
                location_key=location_key,
                travelers=[player],
                risk=risk,
                tags=["haven", "safehouse"],
            )

        embed = await self._scene_embed_from_result(ctx, scene, title_prefix=f"Haven Scene – {haven.name}")
        await ctx.send(embed=embed)

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

    @commands.command(name="haven_raid")
    @commands.has_permissions(administrator=True)
    async def haven_raid(self, ctx: commands.Context, token: str, severity: int = 3):
        """
        Storyteller: trigger a raid on a haven.
        - Increases Director pressures
        - Damages haven security / warding / influence
        """
        haven = self.engine.get_haven_by_id_or_name(token)
        if not haven:
            return await ctx.reply(f"No haven found for `{token}`.")

        result = self.engine.apply_raid(haven, severity=severity)
        h = result["haven"]
        city = result["director"]

        embed = discord.Embed(
            title=f"Haven Raid – Severity {result['severity']}",
            description=f"**{h['name']}** (`{h['id']}`) has been attacked.",
            color=discord.Color.red(),
        )

        embed.add_field(
            name="New Haven State",
            value=(
                f"Security: {h['security']}\n"
                f"Warding: {h['domain'].get('warding_level', 0)}\n"
                f"Influence: {h['domain'].get('influence', 0)}"
            ),
            inline=False,
        )

        embed.add_field(
            name="City Pressure (Director)",
            value=(
                f"Masquerade: {city.get('masquerade_pressure', 0)}\n"
                f"Violence: {city.get('violence_pressure', 0)}\n"
                f"Occult: {city.get('occult_pressure', 0)}\n"
                f"SI: {city.get('si_pressure', 0)}\n"
                f"Politics: {city.get('political_pressure', 0)}\n"
                f"Global Threat: {city.get('global_threat', 1)}"
            ),
            inline=False,
        )

        await ctx.send(embed=embed)

    @commands.command(name="haven_upgrade")
    @commands.has_permissions(administrator=True)
    async def haven_upgrade(self, ctx: commands.Context, token: str, stat: str, delta: int):
        """
        Storyteller: tweak a haven's domain stats.

        stat can be:
          - security
          - luxury
          - feeding
          - masquerade_buffer
          - warding
          - influence
        """
        haven = self.engine.get_haven_by_id_or_name(token)
        if not haven:
            return await ctx.reply(f"No haven found for `{token}`.")

        new_haven = self.engine.upgrade_domain(haven, stat, delta)

        embed = discord.Embed(
            title="Haven Upgraded",
            description=self._format_haven(new_haven),
            color=discord.Color.blue(),
        )
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(HavenCog(bot))
