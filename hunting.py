import discord
from discord.ext import commands
from utils import get_guild_data, get_stat_from_sheet, generate_hunt_victim
import random

PREDATOR_POOLS = {
    "alleycat": ("strength", "brawl"),
    "bagger": ("intelligence", "streetwise"),
    "blood leech": None, 
    "cleaver": ("manipulation", "subterfuge"),
    "consensualist": ("manipulation", "persuasion"),
    "farmer": ("composure", "animal_ken"),
    "osiris": ("manipulation", "subterfuge"),
    "sandman": ("dexterity", "stealth"),
    "scene queen": ("manipulation", "persuasion"),
    "siren": ("charisma", "subterfuge"),
    "extortionist": ("manipulation", "intimidation"),
    "graverobber": ("wits", "larceny"),
    "pursuer": ("stamina", "streetwise"),
    "trapdoor": ("dexterity", "stealth")
}

class HuntingCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    async def cog_check(self, ctx):
        return True

    @commands.command(name="hunt_victim")
    async def hunt_victim(self, ctx, *, location: str):
        """Generates a random mortal victim."""
        g_data = get_guild_data(self.bot.data_store, ctx.guild.id)
        player_data = g_data.get("players", {}).get(str(ctx.author.id))

        async with ctx.typing():
            victim_data = await generate_hunt_victim(self.bot.ai_model_json, location, player_data)
            if not victim_data:
                return await ctx.send("The AI could not generate a victim. Please try again.")
            
            embed = discord.Embed(title=f"Hunting at... {location}", description=victim_data['description'], color=discord.Color.dark_red())
            embed.add_field(name="Blood Resonance", value=victim_data['resonance'], inline=False)
            embed.set_footer(text=f"A new victim for {ctx.author.display_name}")
            await ctx.send(embed=embed)

    @commands.command(name="hunt")
    async def hunt(self, ctx):
        """Rolls your default Predator Type hunting pool."""
        g_data = get_guild_data(self.bot.data_store, ctx.guild.id)
        player_id = str(ctx.author.id)

        if player_id not in g_data.get("players", {}): return await ctx.send("Register first.")
        sheet = g_data["players"][player_id]["sheet_data"]
        ptype = sheet.get("predator", "unknown").lower()
        
        if ptype not in PREDATOR_POOLS or not PREDATOR_POOLS[ptype]:
             return await ctx.send(f"Predator type '{ptype}' requires manual play.")
             
        pool = PREDATOR_POOLS[ptype]
        dice = get_stat_from_sheet(sheet, pool[0]) + get_stat_from_sheet(sheet, pool[1])
        difficulty = g_data.get("hunting_difficulty", 4)
        
        rolls = [random.randint(1, 10) for _ in range(dice)]
        successes = sum(1 for r in rolls if r >= 6) + (sum(1 for r in rolls if r == 10)//2)*2
        
        embed = discord.Embed(title=f"Hunt: {ptype.title()}", color=discord.Color.red())
        embed.add_field(name="Pool", value=f"{pool[0].title()} + {pool[1].title()} ({dice})")
        embed.add_field(name="Result", value=f"{successes} Successes (Diff {difficulty})")
        
        if successes >= difficulty: embed.description = "**SUCCESS:** You feed safely."
        else: embed.description = "**FAILURE:** You find nothing or trouble finds you."
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(HuntingCommands(bot))