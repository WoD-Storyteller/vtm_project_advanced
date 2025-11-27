import discord
from discord.ext import commands

from utils import get_guild_data, generate_hunt_victim
from core.vtmv5.hunting_engine import HuntingEngine
from core.vtmv5 import character_model
from core.travel.zones_loader import ZoneRegistry


class HuntingCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.engine = HuntingEngine()

    async def cog_check(self, ctx):
        # You can later lock this to certain channels/roles
        return True

    # ----------------------------------------------------
    # !hunt_victim – keep your original flavour tool
    # ----------------------------------------------------
    @commands.command(name="hunt_victim")
    async def hunt_victim(self, ctx, *, location: str):
        """
        Generates a random mortal victim for narrative hunting scenes.
        Uses your existing generate_hunt_victim AI helper.
        """
        g_data = get_guild_data(self.bot.data_store, ctx.guild.id)
        player_data = g_data.get("players", {}).get(str(ctx.author.id))

        async with ctx.typing():
            victim_data = await generate_hunt_victim(
                getattr(self.bot, "ai_model_json", None),
                location,
                player_data,
            )

        if not victim_data:
            return await ctx.reply("I couldn't generate a victim right now.")

        # Try to be flexible about victim_data structure
        if isinstance(victim_data, str):
            desc = victim_data
            name = "Unfortunate Mortal"
        elif isinstance(victim_data, dict):
            name = victim_data.get("name", "Unfortunate Mortal")
            desc = victim_data.get("description", "") or victim_data.get("blurb", "")
        else:
            name = "Unfortunate Mortal"
            desc = str(victim_data)

        embed = discord.Embed(
            title=f"Hunt Victim – {name}",
            description=desc,
            color=discord.Color.dark_red(),
        )
        await ctx.send(embed=embed)

    # ----------------------------------------------------
    # !hunt – V5 Predator-aware hunting + feeding
    # ----------------------------------------------------
    @commands.command(name="hunt")
    async def hunt(self, ctx):
        """
        Perform a Predator-type–aware V5 hunting roll
        in your current zone, applying hunger changes
        via the V5 feeding engine.
        """
        g_data = get_guild_data(self.bot.data_store, ctx.guild.id)
        player = g_data.get("players", {}).get(str(ctx.author.id))

        if not player:
            return await ctx.reply("You don't have a character sheet yet.")

        character_model.ensure_character_state(player)

        # Resolve current zone
        loc_key = player.get("location_key")
        registry = getattr(self.bot, "zone_registry", None)
        if registry is None:
            registry = ZoneRegistry()
            registry.load()
            self.bot.zone_registry = registry

        zone = registry.get(loc_key) or registry.get(registry.default_zone_key())
        if not zone:
            return await ctx.reply("You seem to be nowhere… I can't find your current hunting zone.")

        # Run the engine
        result = self.engine.hunt(player, zone)
        self.bot.save_data()

        dice_res = result["dice_result"]
        feeding = result["feeding_result"]

        normal_dice_str = " ".join(str(d) for d in dice_res["dice"])
        hunger_dice_str = " ".join(str(d) for d in dice_res["hunger_dice"])

        embed = discord.Embed(
            title=f"Hunt – {player.get('name', ctx.author.display_name)}",
            color=discord.Color.dark_red(),
        )

        embed.add_field(name="Zone", value=f"{result['zone_name']} (`{result['zone_key']}`)", inline=False)
        embed.add_field(name="Predator Type", value=result["predator_type"] or "None", inline=True)
        embed.add_field(name="Dice Pool", value=str(result["dice_pool"]), inline=True)
        embed.add_field(name="Hunger Before", value=str(result["hunger_before"]), inline=True)

        embed.add_field(
            name="Dice Rolled",
            value=f"Normal: {normal_dice_str or '—'}\nHunger: {hunger_dice_str or '—'}",
            inline=False,
        )

        notes = []
        notes.append(f"Successes: {dice_res['successes']}")
        if dice_res["critical_pairs"] > 0:
            notes.append(f"Critical pairs: {dice_res['critical_pairs']}")
        if dice_res["messy_critical"]:
            notes.append("💥 Messy Critical")
        if dice_res["bestial_failure"]:
            notes.append("🐺 Bestial Failure")
        if dice_res["total_success"]:
            notes.append("✅ You successfully feed.")
        else:
            notes.append("❌ You fail to find a safe vessel.")

        embed.add_field(name="Roll Outcome", value="\n".join(notes), inline=False)

        # Feeding result
        feed_notes = feeding.get("notes") or []
        feed_notes_str = "\n".join(feed_notes) if feed_notes else "—"

        embed.add_field(
            name="Feeding",
            value=(
                f"Source: {feeding['source']}\n"
                f"Hunger: {feeding['old_hunger']} → {feeding['new_hunger']}"
            ),
            inline=False,
        )
        embed.add_field(
            name="Predator Rules",
            value=feed_notes_str,
            inline=False,
        )

        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(HuntingCommands(bot))