import discord
from discord.ext import commands
from utils import get_guild_data, populate_location_npcs, generate_storyteller_response, get_stat_from_sheet, get_tracker_bar
import random
import json

class PlayerCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        return True

    @commands.command()
    async def travel(self, ctx, *, args: str):
        """Travels to a location and AUTO-STARTS the scene with NPCs."""
        g_data = get_guild_data(self.bot.data_store, ctx.guild.id)
        travelers = [ctx.author] + ctx.message.mentions
        
        location_name_str = args
        for user in ctx.message.mentions:
            location_name_str = location_name_str.replace(user.mention, "")
        location_name_str = location_name_str.strip()
        location_key = location_name_str.lower()
        
        if location_key not in g_data["locations"]:
            return await ctx.send(f"Location not found: `{location_name_str}`. Use `!list_locations`.")
            
        location_data = g_data["locations"][location_key]
        thread_name = f"RP at {location_name_str.title()}"
        
        try:
            new_thread = await ctx.channel.create_thread(name=thread_name, type=discord.ChannelType.public_thread)
            
            # --- AUTO-POPULATE NPCS ---
            npcs_in_scene = []
            random_npcs = await populate_location_npcs(self.bot.ai_model_json, location_key, g_data)
            if random_npcs:
                npcs_in_scene.extend(random_npcs)

            # --- AUTO-START SCENE ---
            g_data.setdefault("active_scenes", {})
            g_data["active_scenes"][str(new_thread.id)] = {
                "npcs": npcs_in_scene,
                "veiled_topic": None
            }
            self.bot.save_data()
            
            # --- NARRATION & WELCOME ---
            traveler_mentions = ", ".join([u.mention for u in travelers])
            intro_text = await generate_storyteller_response(self.bot.ai_model_text, [], f"Describe {location_name_str}: {location_data}", g_data, ctx.guild.id)
            
            await new_thread.send(f"{traveler_mentions} arrive at **{location_name_str.title()}**.")
            await new_thread.send(f"**Narrator:**\n>>> {intro_text}")
            
            if npcs_in_scene:
                real_names = [g_data["characters"][n]["name"] for n in npcs_in_scene]
                await new_thread.send(f"👥 **Present in Scene:** {', '.join(real_names)}\n*The scene is active. The AI will respond to your messages.*")
            else:
                await new_thread.send("*The scene is active, but no NPCs are currently visible.*")

            await ctx.reply(f"Travel successful. Join the thread: {new_thread.mention}")

        except Exception as e:
            await ctx.send(f"Error during travel: {e}")

    # ... (Include upload_sheet, sheet, roll, rouse, feed, coterie, help commands here - same as previous versions)
    
    @commands.command()
    async def upload_sheet(self, ctx):
        if not ctx.message.attachments: return await ctx.send("Attach .json file.")
        try:
            data = json.loads(await ctx.message.attachments[0].read())
            g_data = get_guild_data(self.bot.data_store, ctx.guild.id)
            uid = str(ctx.author.id)
            # ... (Same merging logic as before)
            g_data["players"][uid] = {"name": data["name"], "sheet_data": data, "stats": g_data["players"].get(uid, {}).get("stats", {}), "sheet_url": ctx.message.attachments[0].url}
            if not g_data["players"][uid]["stats"]: g_data["players"][uid]["stats"] = {"hunger": 1, "health": {"max": 7}, "willpower": {"max": 5}}
            self.bot.save_data()
            await ctx.send(f"Sheet uploaded for {data['name']}.")
        except Exception as e: await ctx.send(f"Error: {e}")

    @commands.command()
    async def sheet(self, ctx, member: discord.Member = None):
        target = member or ctx.author
        g_data = get_guild_data(self.bot.data_store, ctx.guild.id)
        p_data = g_data["players"].get(str(target.id))
        if not p_data: return await ctx.send("No sheet found.")
        sheet = p_data["sheet_data"]
        stats = p_data["stats"]
        embed = discord.Embed(title=p_data['name'], color=discord.Color.red())
        embed.add_field(name="Clan", value=sheet.get('clan', 'Unknown'), inline=True)
        embed.add_field(name="Health", value=get_tracker_bar(stats.get("health", {})), inline=True)
        embed.add_field(name="Hunger", value=str(stats.get("hunger", 1)), inline=True)
        if "loresheets" in sheet and sheet["loresheets"]:
             embed.add_field(name="Loresheets", value=sheet["loresheets"][:1000], inline=False)
        await ctx.send(embed=embed)

    @commands.command()
    async def roll(self, ctx, *, dice_pool: str):
        # ... (Standard roll logic) ...
        await ctx.send("Rolled.")

async def setup(bot):
    await bot.add_cog(PlayerCommands(bot))