const API_BASE = "http://localhost:8000";

function gid() {
  return document.getElementById("guild_id").value.trim();
}

function setStatus(msg) {
  document.getElementById("status").textContent = msg;
}

async function loadAll() {
  const guildId = gid();
  if (!guildId) {
    alert("Enter Guild ID");
    return;
  }
  setStatus("Loading...");
  try {
    await Promise.all([
      loadPlayers(guildId),
      loadQuests(guildId),
      loadScenes(guildId),
      loadEncounters(guildId),
      loadContinuity(guildId),
    ]);
    setStatus("Loaded");
  } catch (err) {
    console.error(err);
    setStatus("Error");
  }
}

async function loadPlayers(guildId) {
  const res = await fetch(`${API_BASE}/guild/${guildId}/players`);
  const data = await res.json();
  const tbody = document.querySelector("#players_table tbody");
  tbody.innerHTML = "";
  if (!data.ok) return;
  for (const p of data.players) {
    const tr = document.createElement("tr");
    const stats = p.stats || {};
    const health = stats.health
      ? `${stats.health.superficial || 0}/${stats.health.aggravated || 0}/${stats.health.max || 0}`
      : "";
    const will = stats.willpower
      ? `${stats.willpower.superficial || 0}/${stats.willpower.aggravated || 0}/${stats.willpower.max || 0}`
      : "";
    tr.innerHTML = `
      <td>${p.name || "?"}</td>
      <td>${p.clan || "?"}</td>
      <td>${stats.hunger ?? ""}</td>
      <td>${health}</td>
      <td>${will}</td>
    `;
    tbody.appendChild(tr);
  }
}

async function loadQuests(guildId) {
  const res = await fetch(`${API_BASE}/guild/${guildId}/quests`);
  if (!res.ok) return;
  const data = await res.json();
  const tbody = document.querySelector("#quests_table tbody");
  tbody.innerHTML = "";
  if (!data.ok) return;
  for (const q of data.quests) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${q.id || ""}</td>
      <td>${q.title || ""}</td>
      <td>${q.status || ""}</td>
      <td>${q.summary || ""}</td>
    `;
    tbody.appendChild(tr);
  }
}

async function loadScenes(guildId) {
  const res = await fetch(`${API_BASE}/guild/${guildId}/scenes`);
  if (!res.ok) return;
  const data = await res.json();
  const tbody = document.querySelector("#scenes_table tbody");
  tbody.innerHTML = "";
  if (!data.ok) return;
  for (const s of data.scenes) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${s.id || ""}</td>
      <td>${s.title || ""}</td>
      <td>${s.status || ""}</td>
      <td>${s.location_key || ""}</td>
    `;
    tbody.appendChild(tr);
  }
}

async function loadEncounters(guildId) {
  const res = await fetch(`${API_BASE}/guild/${guildId}/encounters`);
  if (!res.ok) return;
  const data = await res.json();
  const tbody = document.querySelector("#encounters_table tbody");
  tbody.innerHTML = "";
  if (!data.ok) return;
  for (const e of data.encounters) {
    const sev = e.severity != null
      ? `${e.severity} (${e.severity_label || ""})`
      : "";
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${e.title || ""}</td>
      <td>${e.location || ""}</td>
      <td>${e.type || ""}</td>
      <td>${sev}</td>
      <td>${e.time || ""}</td>
    `;
    tbody.appendChild(tr);
  }
}

async function loadContinuity(guildId) {
  const res = await fetch(`${API_BASE}/guild/${guildId}/continuity`);
  if (!res.ok) return;
  const data = await res.json();
  const tbody = document.querySelector("#continuity_table tbody");
  tbody.innerHTML = "";
  if (!data.ok) return;
  for (const ev of data.events) {
    const themes = (ev.themes || []).join(", ");
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${ev.title || ""}</td>
      <td>${ev.location_key || ""}</td>
      <td>${ev.status || ""}</td>
      <td>${themes}</td>
      <td>${ev.timestamp || ""}</td>
    `;
    tbody.appendChild(tr);
  }
}

function setupTabs() {
  const buttons = document.querySelectorAll(".tab-btn");
  const panels = document.querySelectorAll(".panel");
  buttons.forEach(btn => {
    btn.addEventListener("click", () => {
      buttons.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      const target = btn.dataset.panel;
      panels.forEach(p => {
        p.classList.toggle("visible", p.id === target);
      });
    });
  });
}

window.addEventListener("DOMContentLoaded", () => {
  document.getElementById("load_btn").addEventListener("click", loadAll);
  setupTabs();
});
