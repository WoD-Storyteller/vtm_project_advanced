import discord
from discord.ext import commands
from utils import get_guild_data, get_player_data, get_stat_from_sheet, check_channel_lock, rouse_check, has_power
import random

PUBLIC_COMMANDS = [
    '!help', '!register_player', '!unregister_player',
    '!upload_sheet', '!sheet', '!rouse', '!feed', '!coterie',
    '!list_locations', '!travel',
    '!hunt', '!hunt_victim', '!quests', '!boons', '!roll', '!spend_wp',
    # Disciplines
    '!awe', '!daunt', '!feral_weapons', '!shadow_cloak', '!arms_of_ahriman',
    '!heightened_senses', '!soaring_leap', '!prowess', '!lightning_strike',
    '!corrosive_vitae', '!extinguish_vitae', '!blink', '!eyes_of_the_beast',
    '!majesty', '!touch_of_oblivion'
]
SCENE_COMMANDS = ['!scene_start', '!scene_end', '!st']

class DisciplineCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        return await check_channel_lock(self.bot, ctx, PUBLIC_COMMANDS, SCENE_COMMANDS)

    async def activate_buff(self, ctx, name, buff_key, buff_data, discipline):
        g_data = get_guild_data(self.bot.data_store, ctx.guild.id)
        player_data = get_player_data(g_data, str(ctx.author.id))
        if not player_data: return await ctx.send("Register first.")
        
        rating = get_stat_from_sheet(player_data.get("sheet_data", {}), discipline)
        if rating == 0: return await ctx.send(f"You do not have {discipline.title()}.")
        
        rouse_msg = await rouse_check(player_data, self.bot.save_data)
        player_data.setdefault("buffs", {})
        player_data["buffs"][buff_key] = buff_data
        self.bot.save_data()
        await ctx.send(f"**{player_data['name']}** activates {name}.{rouse_msg}")

    @commands.command()
    async def awe(self, ctx): await self.activate_buff(ctx, "Awe", "presence_awe", {"dice": "presence"}, "presence")
    @commands.command()
    async def daunt(self, ctx): await self.activate_buff(ctx, "Daunt", "presence_daunt", {"dice": "presence"}, "presence")
    @commands.command()
    async def majesty(self, ctx): await self.activate_buff(ctx, "Majesty", "presence_majesty", {"auto_fail": True}, "presence")
    @commands.command()
    async def feral_weapons(self, ctx): await self.activate_buff(ctx, "Feral Weapons", "feral_weapons", {"damage": 2}, "protean")
    @commands.command()
    async def shadow_cloak(self, ctx): await self.activate_buff(ctx, "Shadow Cloak", "shadow_cloak", {"dice": 2}, "oblivion")
    @commands.command()
    async def arms_of_ahriman(self, ctx): await self.activate_buff(ctx, "Arms of Ahriman", "arms_of_ahriman", {"grapple": True}, "oblivion")
    @commands.command()
    async def touch_of_oblivion(self, ctx): await self.activate_buff(ctx, "Touch of Oblivion", "touch_oblivion", {"damage": 3}, "oblivion")
    @commands.command()
    async def lightning_strike(self, ctx): await self.activate_buff(ctx, "Lightning Strike", "lightning_strike", {"difficulty": -2}, "celerity")
    @commands.command()
    async def prowess(self, ctx): await self.activate_buff(ctx, "Prowess", "prowess", {"damage": "potence"}, "potence")
    @commands.command()
    async def heightened_senses(self, ctx): await self.activate_buff(ctx, "Heightened Senses", "heightened_senses", {"dice": "auspex"}, "auspex")

    # Simple response commands for narrative effects
    @commands.command()
    async def soaring_leap(self, ctx): await ctx.send(f"**{ctx.author.display_name}** leaps an inhuman distance.")
    @commands.command()
    async def blink(self, ctx): await ctx.send(f"**{ctx.author.display_name}** moves instantly to a new location.")
    @commands.command()
    async def corrosive_vitae(self, ctx): await ctx.send(f"**{ctx.author.display_name}**'s blood becomes acid.")
    @commands.command()
    async def sense_the_unseen(self, ctx): await ctx.send(f"**{ctx.author.display_name}** focuses their sight on the hidden.")

async def setup(bot):
    await bot.add_cog(DisciplineCommands(bot))