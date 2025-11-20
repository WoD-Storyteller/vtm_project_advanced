import discord
from discord.ext import commands
from utils import get_guild_data
import json
import os
import shlex

class StorytellerCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        if not ctx.guild: return False
        if await self.bot.is_owner(ctx.author): return True
        g_data = get_guild_data(self.bot.data_store, ctx.guild.id)
        if g_data.get("admin_channel_id") and str(ctx.channel.id) != g_data["admin_channel_id"]:
            await ctx.send("Use admin channel.", delete_after=5)
            return False
        return True

    @commands.command()
    async def spawn(self, ctx, template_name: str, count: int = 1):
        """Spawns NPCs from antagonists.json."""
        if not os.path.exists("antagonists.json"):
            return await ctx.send("No `antagonists.json` file found.")
        
        with open("antagonists.json", "r") as f:
            db = json.load(f)
        
        if template_name not in db:
            return await ctx.send(f"Template `{template_name}` not found. Options: {', '.join(db.keys())}")
        
        g_data = get_guild_data(self.bot.data_store, ctx.guild.id)
        data = db[template_name]
        names = []
        
        for i in range(count):
            name = f"{data['name']} {i+1}"
            g_data["characters"][name.lower()] = {
                "name": name,
                "bio": data["bio"],
                "stats": data["stats"],
                "attributes": data.get("attributes", {}),
                "disciplines": data.get("disciplines", {}),
                "is_temporary": True
            }
            names.append(name)
            
        self.bot.save_data()
        await ctx.send(f"⚠️ **Spawned:** {', '.join(names)}")

    @commands.command()
    async def set_location_npc_count(self, ctx, name: str, min_c: int, max_c: int):
        g_data = get_guild_data(self.bot.data_store, ctx.guild.id)
        if name.lower() not in g_data["locations"]: return await ctx.send("Location not found.")
        g_data.setdefault("location_settings", {})[name.lower()] = {"min": min_c, "max": max_c}
        self.bot.save_data()
        await ctx.send(f"✅ **{name}**: Will spawn {min_c}-{max_c} random NPCs on entry.")

    @commands.command()
    async def list_location_settings(self, ctx):
        g_data = get_guild_data(self.bot.data_store, ctx.guild.id)
        settings = g_data.get("location_settings", {})
        msg = "**Auto-Population Settings:**\n" + "\n".join([f"{k.title()}: {v['min']}-{v['max']}" for k,v in settings.items()])
        await ctx.send(msg)
    
    # ... Standard commands included for completeness ...
    @commands.command()
    async def create(self, ctx, name: str, *, bio: str):
        g_data = get_guild_data(self.bot.data_store, ctx.guild.id)
        g_data["characters"][name.lower()] = {
            "name": name, "bio": bio, "avatar": "", "prefix": "", "suffix": "",
            "stats": {"hunger": 1, "health": {"max": 7, "superficial": 0, "aggravated": 0}, "willpower": {"max": 5, "superficial": 0, "aggravated": 0}},
            "examples": []
        }
        self.bot.save_data()
        await ctx.send(f"🩸 **{name}** embraced (NPC).")

    @commands.command()
    async def setavatar(self, ctx, name: str, url: str):
        g_data = get_guild_data(self.bot.data_store, ctx.guild.id)
        if name.lower() in g_data["characters"]:
            g_data["characters"][name.lower()]["avatar"] = url
            self.bot.save_data()
            await ctx.send(f"🖼️ Avatar set for **{name}**.")
        else:
            await ctx.send("NPC not found.")
    
    @commands.command()
    async def add_location(self, ctx, name: str, *, description: str):
        g_data = get_guild_data(self.bot.data_store, ctx.guild.id)
        g_data["locations"][name.lower()] = description
        self.bot.save_data()
        await ctx.send(f"✅ **Location Added:** `{name}`")

    @commands.command()
    async def del_location(self, ctx, *, name: str):
        g_data = get_guild_data(self.bot.data_store, ctx.guild.id)
        if name.lower() in g_data["locations"]:
            del g_data["locations"][name.lower()]
            self.bot.save_data()
            await ctx.send(f"🗑️ **Location Removed:** `{name}`")
        else:
            await ctx.send("Location not found.")

    @commands.command()
    async def batch_upload_npcs(self, ctx):
        if not ctx.message.attachments: return await ctx.send("Attach .json file.")
        try:
            npc_list = json.loads(await ctx.message.attachments[0].read())
            g_data = get_guild_data(self.bot.data_store, ctx.guild.id)
            count = 0
            for npc in npc_list:
                g_data["characters"][npc["name"].lower()] = {
                    "name": npc["name"], "bio": npc["bio"],
                    "avatar": npc.get("avatar", ""), "prefix": npc.get("prefix", ""), "suffix": npc.get("suffix", ""),
                    "stats": npc.get("stats", {"hunger": 1, "health": {"max": 7}, "willpower": {"max": 5}}),
                    "examples": npc.get("examples", [])
                }
                count += 1
            self.bot.save_data()
            await ctx.send(f"✅ Batch Import: {count} NPCs.")
        except Exception as e: await ctx.send(f"Error: {e}")

async def setup(bot):
    await bot.add_cog(StorytellerCommands(bot))