# deploy test
import discord
import google.generativeai as genai
import json
import os
import asyncio
import random

DATA_FILE = "vtm_data.json"
LORE_DIR = "lore_files"

def load_data_from_file():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"Error: {DATA_FILE} is corrupted. Starting fresh.")
            return {}
    return {}

def save_data(data_store):
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump(data_store, f, indent=4)
    except Exception as e:
        print(f"CRITICAL: Failed to save data! {e}")

def get_guild_data(data_store, guild_id):
    guild_id_str = str(guild_id)
    if guild_id_str not in data_store:
        data_store[guild_id_str] = default_guild_data()
        save_data(data_store)
    
    guild_data = data_store[guild_id_str]
    guild_data.setdefault("players", {})
    guild_data.setdefault("characters", {})
    guild_data.setdefault("active_scenes", {})
    guild_data.setdefault("admin_channel_id", None)
    guild_data.setdefault("locations", {})
    guild_data.setdefault("boons", [])
    guild_data.setdefault("quests", [])
    guild_data.setdefault("combat_tracker", {})
    guild_data.setdefault("hunting_difficulty", 4)
    guild_data.setdefault("location_settings", {})
    
    migrate_quests(guild_data, guild_id_str, data_store)
    migrate_character_stats(guild_data, guild_id_str, data_store)
    return guild_data

def default_guild_data():
    return {
        "characters": {}, "lore": "The city is calm.", "scene": "Unknown location.",
        "quests": [], "boons": [], "masquerade": "Stable", "lore_files": [],
        "active_scenes": {}, "players": {}, "admin_channel_id": None,
        "locations": {}, "combat_tracker": {}, "hunting_difficulty": 4,
        "location_settings": {}
    }

def migrate_quests(guild_data, guild_id_str, data_store):
    if "quests" in guild_data and len(guild_data["quests"]) > 0:
        if isinstance(guild_data["quests"][0], str):
            new_quests = []
            for q_str in guild_data["quests"]:
                new_quests.append({
                    "objective": q_str, "giver": "Unknown", "reward_text": "Unknown",
                    "status": "Active", "reward_boon": None, "xp_reward": 0
                })
            guild_data["quests"] = new_quests
            save_data(data_store)
        for q in guild_data["quests"]:
            q.setdefault("xp_reward", 0)

def migrate_character_stats(guild_data, guild_id_str, data_store):
    migrated = False
    all_chars = list(guild_data.get("players", {}).values()) + list(guild_data.get("characters", {}).values())
    
    for char in all_chars:
        if "stats" not in char: char["stats"] = {}
        if "health" not in char["stats"] or isinstance(char["stats"]["health"], str):
            migrated = True
            stamina = char.get("attributes", {}).get("stamina", 1)
            char["stats"]["health"] = {"max": stamina + 3, "superficial": 0, "aggravated": 0}
        if "willpower" not in char["stats"] or isinstance(char["stats"]["willpower"], str):
            migrated = True
            composure = char.get("attributes", {}).get("composure", 1)
            resolve = char.get("attributes", {}).get("resolve", 1)
            char["stats"]["willpower"] = {"max": composure + resolve, "superficial": 0, "aggravated": 0}
        char.setdefault("disciplines", {})
        char.setdefault("buffs", {})
        char.setdefault("examples", [])
        char.setdefault("generation", 13)
        char["stats"].setdefault("hunger", 1)

    if migrated:
        save_data(data_store)

def get_guild_lore_dir(guild_id):
    guild_lore_path = os.path.join(LORE_DIR, str(guild_id))
    os.makedirs(guild_lore_path, exist_ok=True)
    return guild_lore_path

async def send_as_character(bot, channel, char_name, avatar_url, text):
    try:
        webhooks = await channel.webhooks()
        webhook = discord.utils.get(webhooks, user=bot.user)
        if not webhook:
            webhook = await channel.create_webhook(name="Storyteller AI Proxy")
        await webhook.send(content=text, username=char_name, avatar_url=avatar_url or discord.utils.MISSING)
    except Exception as e:
        await channel.send(f"**{char_name}:** {text}")

def get_combined_lore(guild_data, guild_id):
    manual_lore = guild_data.get("lore", "")
    file_lore_parts = []
    guild_lore_path = get_guild_lore_dir(guild_id)
    for filename in guild_data.get("lore_files", []):
        filepath = os.path.join(guild_lore_path, filename)
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    file_lore_parts.append(f"--- SOURCE: {filename} ---\n{f.read()}")
            except: pass
    combined_files = "\n\n".join(file_lore_parts)
    return f"--- MANUAL CONTEXT ---\n{manual_lore}\n\n--- UPLOADED SOURCES ---\n{combined_files}"

def build_chat_log(history):
    log = ""
    for m in history:
        if not m.content.startswith("!"): log += f"{m.author.display_name}: {m.content}\n"
    return log

async def generate_storyteller_response(model, history, prompt, guild_data, gid):
    global_lore = get_combined_lore(guild_data, gid)
    scene = guild_data.get("scene", "")
    system_prompt = (
        "You are the Storyteller (Game Master) for a Vampire: The Masquerade chronicle.\n"
        "Goal: Describe the scene, set the mood (Gothic/Punk/Noir), and adjudicate rules.\n"
        f"Location: {scene}\nLORE: {global_lore}\n"
        "INSTRUCTIONS: Vividly describe sights, sounds, and smells. Be atmospheric."
    )
    chat_log = build_chat_log(history)
    try:
        response = await model.generate_content_async(system_prompt + "\n\n" + chat_log + f"\n(ST Prompt: {prompt})")
        return response.text.strip()
    except Exception as e:
        return f"*(AI Error: {str(e)})*"

async def generate_scene_response(model, history, active_scene, guild_data, gid):
    global_lore = get_combined_lore(guild_data, gid)
    scene = guild_data.get("scene", "")
    
    char_profiles = ""
    for char_name in active_scene.get("npcs", []):
        if char_name not in guild_data["characters"]: continue
        char_data = guild_data["characters"][char_name]
        stats = char_data.get("stats", {"hunger": 1})
        char_profiles += f"- {char_data['name']} (Hunger: {stats.get('hunger', 1)}): {char_data['bio']}\n"
        for ex in char_data.get("examples", []):
            char_profiles += f'  - "{ex}"\n'

    veiled_topic = active_scene.get("veiled_topic")
    
    system_prompt = (
        "You are the Storyteller AI, directing a roleplay scene.\n"
        f"Scene: {scene}\nLore: {global_lore}\nActive NPCs:\n{char_profiles}\n"
        "Task: Generate a response from ONE OR MORE active characters. Decide who speaks. Format as JSON: {\"char_name\": \"dialogue\"}.\n"
    )
    if veiled_topic:
        system_prompt += f"\nSAFETY WARNING: A player is uncomfortable with: {veiled_topic}. Immediately change the subject."

    json_schema = {"type": "OBJECT", "properties": {}, "additionalProperties": {"type": "STRING"}}
    generation_config = genai.types.GenerationConfig(response_mime_type="application/json", response_schema=json_schema)
    
    chat_history = build_chat_log(history)
    try:
        response = await model.generate_content_async(system_prompt + "\n\nCHAT:\n" + chat_history, generation_config=generation_config)
        if veiled_topic: active_scene["veiled_topic"] = None
        return json.loads(response.text)
    except: return {}

async def generate_hunt_victim(model, location, player_data):
    clan = player_data.get("sheet_data", {}).get("clan", "Unknown") if player_data else "Unknown"
    animalism = player_data.get("sheet_data", {}).get("disciplines", {}).get("animalism", 0) if player_data else 0
    
    prompt = (
        "You are a Storyteller AI. A player is hunting for blood.\n"
        f"Location: {location}\nHunter Clan: {clan}\nAnimalism: {animalism}\n"
        "Generate a JSON object with 'description' (2-3 sentences, dark, moral complication) and 'resonance' (Phlegmatic, Melancholic, Choleric, Sanguine, or Animal)."
    )
    if animalism > 0: prompt += " You can offer an Animal victim."
    
    json_schema = {"type": "OBJECT", "properties": {"description": {"type": "STRING"},"resonance": {"type": "STRING"}}}
    generation_config = genai.types.GenerationConfig(response_mime_type="application/json", response_schema=json_schema)
    try:
        response = await model.generate_content_async(prompt, generation_config=generation_config)
        return json.loads(response.text)
    except: return None

# --- NPC POPULATION ---
async def populate_location_npcs(model, location_name, guild_data):
    """Checks min/max settings and generates random NPCs."""
    key = location_name.lower()
    settings = guild_data.get("location_settings", {}).get(key)
    
    if not settings: return []
    
    min_npcs = settings.get("min", 0)
    max_npcs = settings.get("max", 0)
    if min_npcs == 0: return []
    
    count = random.randint(min_npcs, max_npcs)
    new_npcs = []
    
    templates = {}
    if os.path.exists("antagonists.json"):
        with open("antagonists.json", "r") as f: templates = json.load(f)
    
    for i in range(count):
        if templates and random.random() > 0.5:
            t_key = random.choice(list(templates.keys()))
            t_data = templates[t_key]
            unique_name = f"{t_data['name']} {i+1}"
            guild_data["characters"][unique_name.lower()] = {
                "name": unique_name,
                "bio": t_data["bio"],
                "stats": t_data["stats"],
                "is_temporary": True
            }
            new_npcs.append(unique_name.lower())
        else:
            prompt = f"Generate a random background NPC for a Vampire: The Masquerade scene in {location_name}. JSON with 'name' (string) and 'bio' (string)."
            json_schema = {"type": "OBJECT", "properties": {"name": {"type": "STRING"}, "bio": {"type": "STRING"}}}
            generation_config = genai.types.GenerationConfig(response_mime_type="application/json", response_schema=json_schema)
            try:
                response = await model.generate_content_async(prompt, generation_config=generation_config)
                data = json.loads(response.text)
                unique_name = f"{data['name']} (Random {i})"
                guild_data["characters"][unique_name.lower()] = {
                    "name": unique_name,
                    "bio": data['bio'],
                    "stats": {"hunger": 1},
                    "is_temporary": True
                }
                new_npcs.append(unique_name.lower())
            except: pass

    return new_npcs

# ... (Stats helpers) ...
def get_tracker_bar(tracker_data):
    max_val = tracker_data.get("max", 5)
    agg = tracker_data.get("aggravated", 0)
    sup = tracker_data.get("superficial", 0)
    empty = "□"; superficial_char = "■"; aggravated_char = "X"
    filled_agg = aggravated_char * agg
    filled_sup = superficial_char * sup
    empty_count = max_val - (agg + sup)
    if empty_count < 0: empty_count = 0
    bar = filled_agg + filled_sup + (empty * empty_count)
    return f"[{bar}]"

def get_buff_value(sheet, key): return sheet.get("buffs", {}).get(key)

def get_stat_from_sheet(sheet, stat_name):
    stat_name = stat_name.lower()
    if stat_name in sheet.get("attributes", {}): return sheet["attributes"][stat_name]
    if stat_name in sheet.get("skills", {}): return sheet["skills"][stat_name]
    for disc_name, level in sheet.get("disciplines", {}).items():
        if disc_name.lower() == stat_name: return level
    return 0

async def rouse_check(char_data, save_func=None):
    roll = random.randint(1, 10)
    msg = f" (Rouse Check: {roll})."
    if roll < 6:
        stats = char_data.get("stats", {})
        if stats.get("hunger", 1) < 5:
            stats["hunger"] = stats.get("hunger", 1) + 1
            msg += " **Hunger increases!**"
        else:
            msg += " **Hunger 5! Test for Frenzy!**"
        if save_func: save_func()
    return msg

def has_power(player_data, discipline, power_name):
    sheet = player_data.get("sheet_data", {})
    disc_level = get_stat_from_sheet(sheet, discipline)
    return disc_level > 0 # Simplified check for now

async def check_channel_lock(bot, ctx, public_cmds, scene_cmds):
    if not ctx.guild: return False
    if await bot.is_owner(ctx.author): return True
    g_data = get_guild_data(bot.data_store, ctx.guild.id)
    admin_id = g_data.get("admin_channel_id")
    cmd = ctx.command.name
    if f"!{cmd}" in public_cmds: return True
    if f"!{cmd}" in scene_cmds:
        if admin_id and str(ctx.channel.id) == admin_id: return False
        return True
    if admin_id and str(ctx.channel.id) != admin_id:
        await ctx.send(f"Use <#{admin_id}>.", delete_after=5)
        return False
    return True

def get_player_data(guild_data, user_id):
    return guild_data.get("players", {}).get(user_id)