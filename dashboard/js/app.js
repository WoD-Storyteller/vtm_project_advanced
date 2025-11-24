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
  const mode = params.get("mode") || "st";
  const username = params.get("username");
  const avatar = params.get("avatar");

  const banner = document.getElementById("user_banner");
  const avatarImg = document.getElementById("avatar_img");
  if (!banner || !userId) return;

  const roleLabel = mode === "player" ? "Player" : "Storyteller";
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
  const mode = params.get("mode") || "st";
  const switchDiv = document.getElementById("role_switch");
  if (!switchDiv) return;

  let link = "";
  if (mode === "st") {
    link = `<a href="/auth/login?mode=player" class="role-switch-link">Switch to Player View</a>`;
  } else {
    link = `<a href="/auth/login?mode=st" class="role-switch-link">Switch to Storyteller View</a>`;
  }
  switchDiv.innerHTML = link;
}

// ------------- Tabs -------------

function setupTabs() {
  const buttons = document.querySelectorAll(".tab-button");
  const panels = document.querySelectorAll(".panel");
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

function gid() {
  return document.getElementById("guild_id").value.trim();
}

// ------------- Director Panel -------------

async function loadDirector() {
  const guildId = gid();
  if (!guildId) return alert("Enter Guild ID first.");
  const res = await fetch(`/guild/${guildId}/director`);
  const data = await res.json();
  if (!data.ok) {
    alert("Error loading director");
    return;
  }
  document.getElementById("director_raw").textContent = JSON.stringify(data.director, null, 2);
  const dir = data.director || {};
  const awakened = dir.awakened ? "AWAKENED" : "asleep";
  const avatar = dir.avatar || {};
  const name = avatar.name || "(no avatar)";
  document.getElementById("director_caine_status").textContent =
    `Emissary state: ${awakened}\nAvatar: ${name}`;
}

async function apiPost(path, body, isForm = false) {
  const opts = { method: "POST" };
  if (body) {
    if (isForm) {
      opts.body = body;
    } else {
      opts.headers = { "Content-Type": "application/json" };
      opts.body = JSON.stringify(body);
    }
  }
  const res = await fetch(path, opts);
  return res.json();
}

async function awakenDirector() {
  const guildId = gid();
  if (!guildId) return alert("Enter Guild ID first.");
  const data = await apiPost(`/guild/${guildId}/director/awaken`);
  document.getElementById("director_raw").textContent = JSON.stringify(data, null, 2);
}

async function sleepDirector() {
  const guildId = gid();
  if (!guildId) return alert("Enter Guild ID first.");
  const data = await apiPost(`/guild/${guildId}/director/sleep`);
  document.getElementById("director_raw").textContent = JSON.stringify(data, null, 2);
}

async function uploadDirectorJson() {
  const guildId = gid();
  if (!guildId) return alert("Enter Guild ID first.");
  const fileInput = document.getElementById("director_json_input");
  if (!fileInput.files.length) return alert("Choose a JSON file first.");
  const formData = new FormData();
  formData.append("file", fileInput.files[0]);
  const data = await apiPost(`/guild/${guildId}/director/upload`, formData, true);
  document.getElementById("director_raw").textContent = JSON.stringify(data, null, 2);
}

// ------------- Scenes Panel -------------

async function generateScene() {
  const guildId = gid();
  if (!guildId) return alert("Enter Guild ID first.");
  const loc = document.getElementById("scene_location").value.trim();
  const travRaw = document.getElementById("scene_travelers").value.trim();
  const travelers = travRaw ? travRaw.split(",").map(s => s.trim()) : [];
  const risk = parseInt(document.getElementById("scene_risk").value || "2", 10);

  const payload = {
    location_key: loc,
    travelers,
    risk
  };
  const res = await apiPost(`/guild/${guildId}/scene/generate`, payload);
  document.getElementById("scene_result").textContent = JSON.stringify(res, null, 2);
}

// ------------- Characters Panel -------------

async function loadCharacters() {
  const guildId = gid();
  if (!guildId) return alert("Enter Guild ID first.");
  const res = await fetch(`/guild/${guildId}/characters`);
  const data = await res.json();
  document.getElementById("characters_list").textContent = JSON.stringify(data, null, 2);
}

// ------------- Requests Panel -------------

async function loadRequests() {
  const res = await fetch(`/requests`);
  const data = await res.json();
  document.getElementById("requests_list").textContent = JSON.stringify(data, null, 2);
}

async function resolveRequest() {
  const idxStr = document.getElementById("resolve_request_index").value;
  const idx = parseInt(idxStr || "-1", 10);
  if (isNaN(idx) || idx < 0) return alert("Enter a valid request index.");
  const res = await apiPost(`/requests/${idx}/resolve`);
  document.getElementById("requests_status").textContent = JSON.stringify(res, null, 2);
}

// ------------- Dice Panel -------------

async function loadDiceHistory() {
  const res = await fetch(`/dice/history`);
  const data = await res.json();
  document.getElementById("dice_history").textContent = JSON.stringify(data, null, 2);
}

// ------------- Init -------------

async function loadAll() {
  if (!gid()) return;
  await loadDirector();
}

window.addEventListener("DOMContentLoaded", async () => {
  await autoLoginSession();
  setupUserBanner();
  setupRoleSwitch();
  setupTabs();

  document.getElementById("load_all_btn").addEventListener("click", loadAll);

  document.getElementById("director_refresh_btn").addEventListener("click", loadDirector);
  document.getElementById("director_awaken_btn").addEventListener("click", awakenDirector);
  document.getElementById("director_sleep_btn").addEventListener("click", sleepDirector);
  document.getElementById("upload_director_btn").addEventListener("click", uploadDirectorJson);

  document.getElementById("generate_scene_btn").addEventListener("click", generateScene);

  document.getElementById("load_characters_btn").addEventListener("click", loadCharacters);

  document.getElementById("load_requests_btn").addEventListener("click", loadRequests);
  document.getElementById("resolve_request_btn").addEventListener("click", resolveRequest);

  document.getElementById("load_dice_btn").addEventListener("click", loadDiceHistory);
});
