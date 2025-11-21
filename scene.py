import discord
from discord.ext import commands
from utils import get_guild_data, generate_storyteller_response, generate_scene_response, send_as_character
import random
import asyncio

# --- COMMAND LISTS FOR FILTERING ---
# We must define these here for the cog_check
PUBLIC_COMMANDS = [
    '!help', '!register_player', '!unregister_player',
    '!upload_sheet', '!sheet', '!rouse', '!feed', '!coterie',
    '!list_locations', '!travel',
    '!hunt', '!quests', '!boons'
]
SCENE_COMMANDS = [
    '!scene_start', '!scene_end', '!st'
]

class SceneCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        if not ctx.guild: return False
        
        # Admin commands are checked in their own cog
        if await self.bot.is_owner(ctx.author):
            return True

        g_data = get_guild_data(self.bot.data_store, ctx.guild.id)
        admin_channel_id = g_data.get("admin_channel_id")
        command = ctx.message.content.split(" ")[0].lower()

        if command in PUBLIC_COMMANDS:
            return True
        
        if command in ['!set_admin_channel', '!unset_admin_channel']:
            return ctx.author.guild_permissions.administrator

        if admin_channel_id:
            if str(ctx.channel.id) == admin_channel_id:
                return True # All ST commands allowed in admin channel
            elif command in SCENE_COMMANDS:
                return True # Scene commands allowed in any channel
            else:
                # Restricted ST command in non-admin channel
                await ctx.message.reply(f"This command can only be used in <#{admin_channel_id}>.", delete_after=10, silent=True)
                return False
        
        return True # No admin channel set, allow all commands

    @commands.command()
    async def st(self, ctx, *, prompt: str):
        g_data = get_guild_data(self.bot.data_store, ctx.guild.id)
        async with ctx.typing():
            history = [m async for m in ctx.channel.history(limit=10) if m.id != ctx.message.id]
            history.reverse()
            resp = await generate_storyteller_response(self.bot.ai_model_text, history, prompt, g_data, ctx.guild.id)
            await ctx.send(f"**Narrator:**\n>>> {resp}")

    @commands.command()
    async def scene_start(self, ctx, *, args: str):
        g_data = get_guild_data(self.bot.data_store, ctx.guild.id)
        cid = str(ctx.channel.id)
        
        try:
            parts = args.split(" ")
            npcs = []
            prompt_parts = []
            for part in parts:
                if part.lower() in g_data["characters"]:
                    npcs.append(part.lower())
                else:
                    prompt_parts.append(part)
            
            scene_prompt = " ".join(prompt_parts) if prompt_parts else "The scene begins."
            
            if not npcs:
                return await ctx.send("You must include at least one valid NPC name.\nUsage: `!scene_start [NPC1] [NPC2]... [Optional Scene Prompt]`")

            if cid in g_data["active_scenes"]:
                return await ctx.send(f"A scene is already active in this channel. Type `!scene_end` to stop it first.")

            g_data["active_scenes"][cid] = npcs
            self.bot.save_data()

            char_list_str = ", ".join([g_data['characters'][n]['name'] for n in npcs])
            await ctx.send(f"--- **Scene Started** ---\n**Active NPCs:** {char_list_str}\nAll messages in this channel are now In-Character. Type `!scene_end` to stop.")
            
            # Post the opening ST message
            history = [m async for m in ctx.channel.history(limit=5) if m.id != ctx.message.id]
            history.reverse()
            st_response = await generate_storyteller_response(self.bot.ai_model_text, history, scene_prompt, g_data, ctx.guild.id)
            await ctx.send(f"**Narrator:**\n>>> {st_response}")
            
        except Exception as e:
            await ctx.send(f"Error starting scene: {e}\nUsage: `!scene_start [NPC1] [NPC2]... [Optional Scene Prompt]`")

    @commands.command()
    async def scene_end(self, ctx):
        g_data = get_guild_data(self.bot.data_store, ctx.guild.id)
        cid = str(ctx.channel.id)
        if cid in g_data["active_scenes"]:
            del g_data["active_scenes"][cid]
            self.bot.save_data()
            await ctx.send("--- **Scene Ended** ---\nAI characters are now silent. You can type OOC.")
        else:
            await ctx.send("No scene is active in this channel.")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot: return
        if message.content.startswith("!"): return
        if not message.guild: return
        
        g_data = get_guild_data(self.bot.data_store, message.guild.id)
        cid = str(message.channel.id)
        
        if cid in g_data["active_scenes"]:
            async with message.channel.typing():
                active_npcs = g_data["active_scenes"][cid]
                history = [m async for m in message.channel.history(limit=20) if m.id != message.id]
                history.reverse()
                history.append(message) # Add the triggering message
                
                responses = await generate_scene_response(self.bot.ai_model_json, history, active_npcs, g_data, message.guild.id)
                
                if not responses:
                    return # AI decided no one should speak
                
                for char_name_key, dialogue in responses.items():
                    char_name_key = char_name_key.lower()
                    if char_name_key in g_data["characters"]:
                        c_data = g_data["characters"][char_name_key]
                        prefix = c_data.get("prefix", "")
                        suffix = c_data.get("suffix", "")
                        final_text = f"{prefix}{dialogue}{suffix}"
                        
                        await send_as_character(self.bot, message.channel, c_data['name'], c_data.get('avatar', ''), final_text)
                        await asyncio.sleep(random.uniform(0.5, 1.5))
                    else:
                        print(f"AI tried to make unknown character speak: {char_name_key}")

async def setup(bot):
    await bot.add_cog(SceneCommands(bot))


