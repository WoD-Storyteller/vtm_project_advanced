const API_BASE = "";

// ------------- Session & Banner -------------

async function autoLoginSession() {
  try {
    const res = await fetch("/auth/session");
    const data = await res.json();
    if (!data.ok) return null;
    const s = data.session;

    const url = new URL(window.location.href);
    url.searchParams.set("user_id", s.sub);
    url.searchParams.set("username", s.username);
    url.searchParams.set("mode", s.mode);
    url.searchParams.set("avatar", s.avatar);
    window.history.replaceState({}, "", url.toString());
    return s;
  } catch (e) {
    console.error("Session error", e);
    return null;
  }
}

function setupUserBanner() {
  const params = new URLSearchParams(window.location.search);
  const userId = params.get("user_id");
  const mode = params.get("mode") || "player";
  const username = params.get("username");
  const avatar = params.get("avatar");

  const banner = document.getElementById("user_banner");
  const avatarImg = document.getElementById("avatar_img");
  if (!banner || !userId) return;

  const roleLabel = mode === "st" ? "Storyteller" : "Player";
  let text = `Logged in as ${roleLabel} – ID ${userId}`;
  if (username) {
    text = `Logged in as ${roleLabel} – ${decodeURIComponent(username)} (ID ${userId})`;
  }
  banner.textContent = text;

  if (avatar && avatarImg) {
    avatarImg.src = decodeURIComponent(avatar);
  }
}

function setupRoleSwitch() {
  const params = new URLSearchParams(window.location.search);
  const mode = params.get("mode") || "player";
  const switchDiv = document.getElementById("role_switch");
  if (!switchDiv) return;

  let link = "";
  if (mode === "player") {
    link = `<a href="/auth/login?mode=st" class="role-switch-link">Switch to Storyteller View</a>`;
  } else {
    link = `<a href="/auth/login?mode=player" class="role-switch-link">Switch to Player View</a>`;
  }
  switchDiv.innerHTML = link;
}

function setupTabs() {
  const buttons = document.querySelectorAll(".tab-button");
  const panels = document.querySelectorAll(".tab-pane");
  buttons.forEach(btn => {
    btn.addEventListener("click", () => {
      const target = btn.dataset.target;
      buttons.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      panels.forEach(p => {
        p.classList.toggle("visible", p.id === target);
      });
    });
  });
}

// ------------- Helpers -------------

function getUserId() {
  const params = new URLSearchParams(window.location.search);
  return params.get("user_id");
}

let currentUserId = null;
let currentCharacterId = null;
let currentCharacter = null;

// ------------- Character List -------------

async function loadCharacterList() {
  currentUserId = getUserId();
  if (!currentUserId) {
    alert("No user_id found. Please log in via Discord.");
    return;
  }

  const res = await fetch(`/player/${currentUserId}/characters`);
  const data = await res.json();
  const select = document.getElementById("character_select");
  select.innerHTML = "";

  if (!data.ok) {
    console.warn("No characters found yet.");
  }

  const chars = (data.characters || []);
  chars.forEach(c => {
    const opt = document.createElement("option");
    opt.value = c.id;
    opt.textContent = `${c.name || "(Unnamed)"} [${c.clan || "?"}]`;
    select.appendChild(opt);
  });

  if (data.active) {
    select.value = data.active;
    await loadCharacter(data.active);
  } else if (chars.length > 0) {
    await loadCharacter(chars[0].id);
  }

  select.addEventListener("change", async () => {
    await loadCharacter(select.value);
  });
}

async function loadCharacter(charId) {
  if (!charId) return;
  const res = await fetch(`/player/${currentUserId}/characters/${charId}`);
  const data = await res.json();
  if (!data.ok) {
    alert("Error loading character");
    return;
  }
  currentCharacterId = charId;
  currentCharacter = data.character;
  fillCharacterForm();
}

async function createNewCharacter() {
  const name = prompt("Name of new character?", "New Kindred");
  if (!name) return;
  const payload = {
    name,
    clan: "",
    generation: 13,
    concept: "",
    predator_type: "",
    chronicle: "",
    sire: "",
    attributes: {
      strength: 1, dexterity: 1, stamina: 1,
      charisma: 1, manipulation: 1, composure: 1,
      intelligence: 1, wits: 1, resolve: 1
    },
    skills: {},
    disciplines: [],
    advantages: { backgrounds: [], merits: [], flaws: [] },
    health: { max: 3, superficial: 0, aggravated: 0 },
    willpower: { max: 3, superficial: 0, aggravated: 0 },
    hunger: 1,
    xp: { total: 0, spent: 0, unspent: 0, log: [] },
    inventory: [],
    boons: [],
    notes: ""
  };
  const res = await fetch(`/player/${currentUserId}/characters`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  const data = await res.json();
  if (!data.ok) {
    alert("Error creating character");
    return;
  }
  await loadCharacterList();
}

// ------------- Fill / Read Form -------------

const SKILLS = [
  "athletics","brawl","craft","drive","firearms","melee","larceny","stealth","survival",
  "animal_ken","etiquette","insight","intimidation","leadership","performance","persuasion","streetwise","subterfuge",
  "academics","awareness","finance","investigation","medicine","occult","politics","science","technology"
];

function buildSkillsGrid() {
  const grid = document.getElementById("skills_grid");
  grid.innerHTML = "";
  SKILLS.forEach(skill => {
    const div = document.createElement("div");
    div.className = "field";
    const label = document.createElement("label");
    label.textContent = skill.replace("_", " ");
    const input = document.createElement("input");
    input.type = "number";
    input.min = "0";
    input.max = "5";
    input.id = "skill_" + skill;
    div.appendChild(label);
    div.appendChild(input);
    grid.appendChild(div);
  });
}

function fillCharacterForm() {
  const c = currentCharacter || {};
  document.getElementById("input_name").value = c.name || "";
  document.getElementById("input_clan").value = c.clan || "";
  document.getElementById("input_gen").value = c.generation || "";
  document.getElementById("input_concept").value = c.concept || "";
  document.getElementById("input_predator").value = c.predator_type || "";
  document.getElementById("input_chronicle").value = c.chronicle || "";
  document.getElementById("input_sire").value = c.sire || "";
  document.getElementById("input_ambitions").value = c.ambitions || "";

  const attrs = c.attributes || {};
  const attrIds = ["strength","dexterity","stamina","charisma","manipulation","composure","intelligence","wits","resolve"];
  attrIds.forEach(a => {
    const el = document.getElementById("attr_" + a);
    if (el) el.value = attrs[a] || 0;
  });

  const skills = c.skills || {};
  SKILLS.forEach(s => {
    const el = document.getElementById("skill_" + s);
    if (el) el.value = skills[s] || 0;
  });

  const health = c.health || {};
  document.getElementById("health_max").value = health.max || 0;
  document.getElementById("health_sup").value = health.superficial || 0;
  document.getElementById("health_agg").value = health.aggravated || 0;

  const wp = c.willpower || {};
  document.getElementById("wp_max").value = wp.max || 0;
  document.getElementById("wp_sup").value = wp.superficial || 0;
  document.getElementById("wp_agg").value = wp.aggravated || 0;

  document.getElementById("hunger").value = c.hunger || 0;

  document.getElementById("input_inventory").value = c.inventory_text || "";
  document.getElementById("input_boons").value = c.boons_text || "";

  const xp = c.xp || {};
  document.getElementById("xp_total").value = xp.total || 0;
  document.getElementById("xp_spent").value = xp.spent || 0;
  document.getElementById("xp_unspent").value = xp.unspent || 0;
  document.getElementById("xp_log").textContent = JSON.stringify(xp.log || [], null, 2);

  renderDisciplines(c.disciplines || []);

  const portraitImg = document.getElementById("portrait_img");
  if (c.portrait_url) {
    portraitImg.src = c.portrait_url;
  } else {
    portraitImg.src = "";
  }
}

function readCharacterForm() {
  if (!currentCharacter) currentCharacter = {};
  const c = currentCharacter;
  c.name = document.getElementById("input_name").value;
  c.clan = document.getElementById("input_clan").value;
  c.generation = parseInt(document.getElementById("input_gen").value || "0", 10);
  c.concept = document.getElementById("input_concept").value;
  c.predator_type = document.getElementById("input_predator").value;
  c.chronicle = document.getElementById("input_chronicle").value;
  c.sire = document.getElementById("input_sire").value;
  c.ambitions = document.getElementById("input_ambitions").value;

  const attrs = {};
  const attrIds = ["strength","dexterity","stamina","charisma","manipulation","composure","intelligence","wits","resolve"];
  attrIds.forEach(a => {
    const el = document.getElementById("attr_" + a);
    attrs[a] = parseInt(el.value || "0", 10);
  });
  c.attributes = attrs;

  const skills = {};
  SKILLS.forEach(s => {
    const el = document.getElementById("skill_" + s);
    skills[s] = parseInt(el.value || "0", 10);
  });
  c.skills = skills;

  c.health = {
    max: parseInt(document.getElementById("health_max").value || "0", 10),
    superficial: parseInt(document.getElementById("health_sup").value || "0", 10),
    aggravated: parseInt(document.getElementById("health_agg").value || "0", 10)
  };

  c.willpower = {
    max: parseInt(document.getElementById("wp_max").value || "0", 10),
    superficial: parseInt(document.getElementById("wp_sup").value || "0", 10),
    aggravated: parseInt(document.getElementById("wp_agg").value || "0", 10)
  };

  c.hunger = parseInt(document.getElementById("hunger").value || "0", 10);

  c.inventory_text = document.getElementById("input_inventory").value;
  c.boons_text = document.getElementById("input_boons").value;

  return c;
}

// ------------- Disciplines -------------

function renderDisciplines(list) {
  const container = document.getElementById("disciplines_list");
  container.innerHTML = "";
  list.forEach((d, idx) => {
    const wrap = document.createElement("div");
    wrap.className = "field";
    const nameInput = document.createElement("input");
    nameInput.value = d.name || "";
    nameInput.placeholder = "Discipline Name";

    const levelInput = document.createElement("input");
    levelInput.type = "number";
    levelInput.min = "0";
    levelInput.max = "5";
    levelInput.value = d.level || 0;

    const powersInput = document.createElement("textarea");
    powersInput.placeholder = "Powers (one per line)";
    powersInput.value = (d.powers || []).join("\n");

    const removeBtn = document.createElement("button");
    removeBtn.textContent = "Remove";
    removeBtn.type = "button";
    removeBtn.addEventListener("click", () => {
      currentCharacter.disciplines.splice(idx, 1);
      renderDisciplines(currentCharacter.disciplines);
    });

    wrap.appendChild(nameInput);
    wrap.appendChild(levelInput);
    wrap.appendChild(powersInput);
    wrap.appendChild(removeBtn);
    container.appendChild(wrap);

    nameInput.addEventListener("input", () => { d.name = nameInput.value; });
    levelInput.addEventListener("input", () => { d.level = parseInt(levelInput.value || "0", 10); });
    powersInput.addEventListener("input", () => {
      d.powers = powersInput.value.split("\n").map(s => s.trim()).filter(Boolean);
    });
  });
}

function addDiscipline() {
  if (!currentCharacter.disciplines) currentCharacter.disciplines = [];
  currentCharacter.disciplines.push({ name: "", level: 0, powers: [] });
  renderDisciplines(currentCharacter.disciplines);
}

// ------------- Save -------------

async function saveCharacter() {
  if (!currentUserId || !currentCharacterId) {
    alert("No character selected.");
    return;
  }
  readCharacterForm();
  const res = await fetch(`/player/${currentUserId}/characters/${currentCharacterId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(currentCharacter)
  });
  const data = await res.json();
  document.getElementById("save_status").textContent = JSON.stringify(data, null, 2);
}

// ------------- XP -------------

async function addXp() {
  if (!currentUserId || !currentCharacterId) {
    alert("No character selected.");
    return;
  }
  const amount = parseInt(document.getElementById("xp_add_amount").value || "0", 10);
  const reason = document.getElementById("xp_add_reason").value;
  const session = document.getElementById("xp_add_session").value;
  const res = await fetch(`/player/${currentUserId}/characters/${currentCharacterId}/xp`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ amount, reason, session })
  });
  const data = await res.json();
  document.getElementById("xp_status").textContent = JSON.stringify(data, null, 2);
  const xp = data.xp || {};
  document.getElementById("xp_total").value = xp.total || 0;
  document.getElementById("xp_unspent").value = xp.unspent || 0;
  document.getElementById("xp_log").textContent = JSON.stringify(xp.log || [], null, 2);
}

// ------------- Rolls -------------

async function doRoll() {
  const pool = parseInt(document.getElementById("roll_pool").value || "0", 10);
  const hunger = parseInt(document.getElementById("roll_hunger").value || "0", 10);
  const payload = { pool, hunger, user_id: currentUserId };
  const res = await fetch("/roll", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  const data = await res.json();
  document.getElementById("roll_result").textContent = JSON.stringify(data, null, 2);
}

// ------------- Requests -------------

async function sendRequest() {
  const subject = document.getElementById("req_subject").value;
  const detail = document.getElementById("req_detail").value;
  if (!subject || !detail) {
    alert("Please fill subject and details.");
    return;
  }
  const res = await fetch(`/player/${currentUserId}/request`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ subject, detail })
  });
  const data = await res.json();
  document.getElementById("req_status").textContent = JSON.stringify(data, null, 2);
}

// ------------- Portrait Upload -------------

async function uploadPortrait() {
  if (!currentUserId || !currentCharacterId) {
    alert("No character selected.");
    return;
  }
  const fileInput = document.getElementById("portrait_input");
  if (!fileInput.files.length) return alert("Choose an image file first.");

  const formData = new FormData();
  formData.append("file", fileInput.files[0]);

  const res = await fetch(`/player/${currentUserId}/characters/${currentCharacterId}/portrait`, {
    method: "POST",
    body: formData
  });
  const data = await res.json();
  document.getElementById("save_status").textContent = JSON.stringify(data, null, 2);
  if (data.portrait_url) {
    document.getElementById("portrait_img").src = data.portrait_url;
  }
}

// ------------- Init -------------

window.addEventListener("DOMContentLoaded", async () => {
  await autoLoginSession();
  setupUserBanner();
  setupRoleSwitch();
  setupTabs();
  buildSkillsGrid();
  await loadCharacterList();

  document.getElementById("new_char_btn").addEventListener("click", createNewCharacter);
  document.getElementById("save_btn").addEventListener("click", saveCharacter);
  document.getElementById("add_discipline_btn").addEventListener("click", addDiscipline);
  document.getElementById("xp_add_btn").addEventListener("click", addXp);
  document.getElementById("roll_btn").addEventListener("click", doRoll);
  document.getElementById("req_send_btn").addEventListener("click", sendRequest);
  document.getElementById("upload_portrait_btn").addEventListener("click", uploadPortrait);
});
