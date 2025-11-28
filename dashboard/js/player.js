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
    console.error("autoLoginSession error", e);
    return null;
  }
}

function getUserId() {
  const params = new URLSearchParams(window.location.search);
  return params.get("user_id");
}

function getUsername() {
  const params = new URLSearchParams(window.location.search);
  return params.get("username") || "Unknown";
}

function getMode() {
  const params = new URLSearchParams(window.location.search);
  return params.get("mode") || "player";
}

function getAvatar() {
  const params = new URLSearchParams(window.location.search);
  return params.get("avatar") || "";
}

function setupUserBanner() {
  const banner = document.getElementById("user_banner");
  const username = getUsername();
  const mode = getMode();
  banner.textContent = `${username} – ${mode === "st" ? "Storyteller" : "Player"} Mode`;

  const avatarUrl = getAvatar();
  const avatarImg = document.getElementById("avatar_img");
  if (avatarUrl) {
    avatarImg.src = avatarUrl;
  }
}

function setupRoleSwitch() {
  const switchDiv = document.getElementById("role_switch");
  const mode = getMode();
  let link;
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

// ------------- Portrait Upload -------------

async function uploadPortrait() {
  if (!currentUserId || !currentCharacterId) {
    alert("No character selected.");
    return;
  }
  const fileInput = document.getElementById("portrait_input");
  if (!fileInput.files || !fileInput.files[0]) {
    alert("Choose an image first.");
    return;
  }
  const formData = new FormData();
  formData.append("file", fileInput.files[0]);

  const res = await fetch(`/player/${currentUserId}/characters/${currentCharacterId}/portrait`, {
    method: "POST",
    body: formData,
  });
  const data = await res.json();
  if (!data.ok) {
    alert("Error uploading portrait");
    return;
  }
  document.getElementById("portrait_img").src = data.url;
}

// ------------- Globals -------------

let currentUserId = null;
let currentCharacterId = null;
let currentCharacter = null;

// ------------- Character List -------------

async function loadCharacterList() {
  if (!currentUserId) return;
  const res = await fetch(`/player/${currentUserId}/characters`);
  const data = await res.json();
  if (!data.ok) {
    console.error("Error loading character list", data);
    return;
  }
  const select = document.getElementById("char_list");
  select.innerHTML = "";
  (data.characters || []).forEach(char => {
    const opt = document.createElement("option");
    opt.value = char.id;
    opt.textContent = char.name || `Character ${char.id}`;
    select.appendChild(opt);
  });
  if ((data.characters || []).length > 0) {
    currentCharacterId = data.characters[0].id;
    select.value = currentCharacterId;
    await loadCharacter(currentCharacterId);
  }
  select.addEventListener("change", async () => {
    currentCharacterId = select.value;
    await loadCharacter(currentCharacterId);
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
    health: { max: 3, superficial: 0, aggravated: 0 },
    willpower: { max: 3, superficial: 0, aggravated: 0 },
    hunger: 1,
    humanity: 7,
    stains: 0,
    blood_potency: 1,
    merits: [],
    flaws: [],
    convictions: [],
    touchstones: [],
    xp: { total: 0, spent: 0, unspent: 0, log: [] },
    inventory_text: "",
    boons_text: "",
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

  // Basics
  document.getElementById("input_name").value = c.name || "";
  document.getElementById("input_clan").value = c.clan || "";
  document.getElementById("input_gen").value = c.generation || "";
  document.getElementById("input_concept").value = c.concept || "";
  document.getElementById("input_predator").value = c.predator_type || "";
  document.getElementById("input_chronicle").value = c.chronicle || "";
  document.getElementById("input_sire").value = c.sire || "";
  document.getElementById("input_ambitions").value = c.ambitions || "";

  // Attributes
  const attrs = c.attributes || {};
  const attrIds = ["strength","dexterity","stamina","charisma","manipulation","composure","intelligence","wits","resolve"];
  attrIds.forEach(a => {
    const el = document.getElementById("attr_" + a);
    if (el) el.value = attrs[a] || 0;
  });

  // Skills
  const skills = c.skills || {};
  SKILLS.forEach(skill => {
    const el = document.getElementById("skill_" + skill);
    if (el) el.value = skills[skill] || 0;
  });

  // Disciplines
  renderDisciplines(c.disciplines || []);

  // Health / Willpower / Hunger / Humanity / Blood Potency
  const health = c.health || { max: 3, superficial: 0, aggravated: 0 };
  document.getElementById("health_max").value = health.max || 0;
  document.getElementById("health_sup").value = health.superficial || 0;
  document.getElementById("health_agg").value = health.aggravated || 0;

  const wp = c.willpower || { max: 3, superficial: 0, aggravated: 0 };
  document.getElementById("wp_max").value = wp.max || 0;
  document.getElementById("wp_sup").value = wp.superficial || 0;
  document.getElementById("wp_agg").value = wp.aggravated || 0;

  document.getElementById("hunger").value = c.hunger != null ? c.hunger : 1;
  const humanityInput = document.getElementById("humanity");
  if (humanityInput) humanityInput.value = c.humanity != null ? c.humanity : 7;
  const stainsInput = document.getElementById("stains");
  if (stainsInput) stainsInput.value = c.stains != null ? c.stains : 0;
  const bpInput = document.getElementById("blood_potency");
  if (bpInput) bpInput.value = c.blood_potency != null ? c.blood_potency : 1;

  // XP
  const xp = c.xp || { total: 0, spent: 0, unspent: 0, log: [] };
  document.getElementById("xp_total").value = xp.total || 0;
  document.getElementById("xp_spent").value = xp.spent || 0;
  document.getElementById("xp_unspent").value = xp.unspent || 0;
  document.getElementById("xp_log").value = (xp.log || []).join("\n");

  // Inventory / Boons
  document.getElementById("input_inventory").value = c.inventory_text || "";
  document.getElementById("input_boons").value = c.boons_text || "";

  // V5 narrative fields
  const meritsArea = document.getElementById("merits_text");
  const flawsArea = document.getElementById("flaws_text");
  const convArea = document.getElementById("convictions_text");
  const tsArea = document.getElementById("touchstones_text");

  if (meritsArea) {
    const merits = c.merits || [];
    meritsArea.value = merits.map(m => {
      const dots = m.dots != null ? m.dots : "";
      const t = m.type || "";
      const note = m.note || "";
      return [m.name || "", dots, t, note].join(" | ");
    }).join("\n");
  }

  if (flawsArea) {
    const flaws = c.flaws || [];
    flawsArea.value = flaws.map(f => {
      const dots = f.dots != null ? f.dots : "";
      const t = f.type || "";
      const note = f.note || "";
      return [f.name || "", dots, t, note].join(" | ");
    }).join("\n");
  }

  if (convArea) {
    const convs = c.convictions || [];
    convArea.value = convs.map(cv => cv.text || "").join("\n");
  }

  if (tsArea) {
    const tstones = c.touchstones || [];
    tsArea.value = tstones.map(ts => {
      const alive = ts.alive === false ? "dead" : "alive";
      return [ts.name || "", ts.role || "", alive].join(" | ");
    }).join("\n");
  }
}

function readCharacterForm() {
  const c = currentCharacter || {};

  // Basics
  c.name = document.getElementById("input_name").value || "";
  c.clan = document.getElementById("input_clan").value || "";
  c.generation = parseInt(document.getElementById("input_gen").value || "0", 10) || 0;
  c.concept = document.getElementById("input_concept").value || "";
  c.predator_type = document.getElementById("input_predator").value || "";
  c.chronicle = document.getElementById("input_chronicle").value || "";
  c.sire = document.getElementById("input_sire").value || "";
  c.ambitions = document.getElementById("input_ambitions").value || "";

  // Attributes
  const attrIds = ["strength","dexterity","stamina","charisma","manipulation","composure","intelligence","wits","resolve"];
  const attrs = {};
  attrIds.forEach(a => {
    const el = document.getElementById("attr_" + a);
    attrs[a] = parseInt(el.value || "0", 10) || 0;
  });
  c.attributes = attrs;

  // Skills
  const skills = {};
  SKILLS.forEach(skill => {
    const el = document.getElementById("skill_" + skill);
    skills[skill] = parseInt(el.value || "0", 10) || 0;
  });
  c.skills = skills;

  // Health / Willpower / Hunger / Humanity / Blood Potency
  c.health = {
    max: parseInt(document.getElementById("health_max").value || "0", 10) || 0,
    superficial: parseInt(document.getElementById("health_sup").value || "0", 10) || 0,
    aggravated: parseInt(document.getElementById("health_agg").value || "0", 10) || 0
  };

  c.willpower = {
    max: parseInt(document.getElementById("wp_max").value || "0", 10) || 0,
    superficial: parseInt(document.getElementById("wp_sup").value || "0", 10) || 0,
    aggravated: parseInt(document.getElementById("wp_agg").value || "0", 10) || 0
  };

  c.hunger = parseInt(document.getElementById("hunger").value || "0", 10) || 0;

  const humanityInput = document.getElementById("humanity");
  if (humanityInput) {
    c.humanity = parseInt(humanityInput.value || "0", 10) || 0;
  }
  const stainsInput = document.getElementById("stains");
  if (stainsInput) {
    c.stains = parseInt(stainsInput.value || "0", 10) || 0;
  }
  const bpInput = document.getElementById("blood_potency");
  if (bpInput) {
    c.blood_potency = parseInt(bpInput.value || "0", 10) || 0;
  }

  // XP
  const xp = c.xp || {};
  xp.total = parseInt(document.getElementById("xp_total").value || "0", 10) || 0;
  xp.spent = parseInt(document.getElementById("xp_spent").value || "0", 10) || 0;
  xp.unspent = parseInt(document.getElementById("xp_unspent").value || "0", 10) || 0;
  xp.log = (document.getElementById("xp_log").value || "")
    .split("\n")
    .map(l => l.trim())
    .filter(l => l.length > 0);
  c.xp = xp;

  // Inventory / Boons
  c.inventory_text = document.getElementById("input_inventory").value || "";
  c.boons_text = document.getElementById("input_boons").value || "";

  // V5 narrative fields from textareas
  const meritsArea = document.getElementById("merits_text");
  if (meritsArea) {
    const meritsLines = meritsArea.value.split("\n").map(l => l.trim()).filter(l => l.length > 0);
    c.merits = meritsLines.map(line => {
      const parts = line.split("|").map(p => p.trim());
      return {
        name: parts[0] || "",
        dots: parts[1] ? (parseInt(parts[1], 10) || 0) : 0,
        type: parts[2] || "general",
        note: parts[3] || ""
      };
    });
  }

  const flawsArea = document.getElementById("flaws_text");
  if (flawsArea) {
    const flawsLines = flawsArea.value.split("\n").map(l => l.trim()).filter(l => l.length > 0);
    c.flaws = flawsLines.map(line => {
      const parts = line.split("|").map(p => p.trim());
      return {
        name: parts[0] || "",
        dots: parts[1] ? (parseInt(parts[1], 10) || 0) : 0,
        type: parts[2] || "general",
        note: parts[3] || ""
      };
    });
  }

  const convArea = document.getElementById("convictions_text");
  if (convArea) {
    const convLines = convArea.value.split("\n").map(l => l.trim()).filter(l => l.length > 0);
    c.convictions = convLines.map(text => ({ text }));
  }

  const tsArea = document.getElementById("touchstones_text");
  if (tsArea) {
    const tsLines = tsArea.value.split("\n").map(l => l.trim()).filter(l => l.length > 0);
    c.touchstones = tsLines.map(line => {
      const parts = line.split("|").map(p => p.trim());
      const status = (parts[2] || "alive").toLowerCase();
      return {
        name: parts[0] || "",
        role: parts[1] || "",
        alive: !(status === "dead" || status === "false" || status === "0")
      };
    });
  }

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
      list.splice(idx, 1);
      renderDisciplines(list);
    });

    wrap.appendChild(nameInput);
    wrap.appendChild(levelInput);
    wrap.appendChild(powersInput);
    wrap.appendChild(removeBtn);
    container.appendChild(wrap);
  });
}

function addDiscipline() {
  if (!currentCharacter) currentCharacter = {};
  currentCharacter.disciplines = currentCharacter.disciplines || [];
  currentCharacter.disciplines.push({
    name: "",
    level: 0,
    powers: []
  });
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
  const note = document.getElementById("xp_add_note").value || "";
  if (!amount) {
    alert("Enter XP amount.");
    return;
  }
  const payload = { amount, note };
  const res = await fetch(`/player/${currentUserId}/characters/${currentCharacterId}/xp`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  const data = await res.json();
  if (!data.ok) {
    alert("Error adding XP");
    return;
  }
  currentCharacter = data.character;
  fillCharacterForm();
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
  if (!currentUserId) {
    alert("No user.");
    return;
  }
  const subject = document.getElementById("req_subject").value || "";
  const detail = document.getElementById("req_detail").value || "";
  const payload = { subject, detail, user_id: currentUserId };
  const res = await fetch("/request", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  const data = await res.json();
  document.getElementById("req_status").textContent = JSON.stringify(data, null, 2);
}

// ------------- Init -------------

document.addEventListener("DOMContentLoaded", async () => {
  const session = await autoLoginSession();
  currentUserId = getUserId();
  if (!currentUserId && session) {
    currentUserId = session.sub;
  }
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
  document.getElementById("upload_portr