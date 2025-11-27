// --- BASE MAP INITIALIZATION ---

let map = L.map("map").setView([20, 0], 2); // world-ish default view

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 19,
}).addTo(map);

// --- LAYERS ---

let zoneLayerGroup = L.layerGroup().addTo(map);
let playerLayerGroup = L.layerGroup().addTo(map);
let huntingHeatLayer = null;

let zonesData = [];
let playersData = [];

// --- HELPERS ---

function factionColor(f) {
  if (!f) return "#7f8c8d";
  f = f.toLowerCase();
  if (f.includes("camarilla")) return "#2980b9";
  if (f.includes("anarch")) return "#e67e22";
  if (f.includes("sabbat")) return "#c0392b";
  if (f.includes("ministry")) return "#8e44ad";
  if (f.includes("hecata")) return "#16a085";
  if (f.includes("thin")) return "#f1c40f";
  if (f.includes("si") || f.includes("inquisition") || f.includes("pentex"))
    return "#e74c3c";
  return "#7f8c8d";
}

function passesFactionFilter(z) {
  const f = (z.faction || "").toLowerCase();
  const tags = (z.tags || []).map((t) => t.toLowerCase());

  const camOn = document.getElementById("filter_camarilla").checked;
  const anaOn = document.getElementById("filter_anarch").checked;
  const sabOn = document.getElementById("filter_sabbat").checked;
  const siOn = document.getElementById("filter_si").checked;
  const othOn = document.getElementById("filter_other").checked;

  const isCam = f.includes("camarilla") || tags.includes("camarilla");
  const isAn = f.includes("anarch") || tags.includes("anarch");
  const isSab = f.includes("sabbat") || tags.includes("sabbat");
  const isSi =
    f.includes("si") ||
    f.includes("inquisition") ||
    f.includes("pentex") ||
    tags.includes("si") ||
    tags.includes("second_inquisition");

  if (isCam && !camOn) return false;
  if (isAn && !anaOn) return false;
  if (isSab && !sabOn) return false;
  if (isSi && !siOn) return false;
  if (!isCam && !isAn && !isSab && !isSi && !othOn) return false;

  return true;
}

// --- RENDERING FUNCTIONS ---

function renderZones() {
  zoneLayerGroup.clearLayers();

  zonesData.forEach((z) => {
    if (!z.lat || !z.lng) return;
    if (!passesFactionFilter(z)) return;

    const color = factionColor(z.faction);
    const marker = L.circleMarker([z.lat, z.lng], {
      radius: 6,
      color: color,
      fillColor: color,
      fillOpacity: 0.85,
    });

    const desc = z.description || "";
    const tags = (z.tags || []).join(", ");

    marker.bindPopup(
      `<strong>${z.name}</strong><br/>
       Region: ${z.region || "Unknown"}<br/>
       Faction: ${z.faction || "Unknown"}<br/>
       Tags: ${tags}<br/><br/>
       ${desc}`
    );

    zoneLayerGroup.addLayer(marker);
  });
}

function renderPlayers() {
  playerLayerGroup.clearLayers();

  if (!document.getElementById("toggle_players").checked) return;

  playersData.forEach((p) => {
    if (!p.lat || !p.lng) return;

    const marker = L.marker([p.lat, p.lng], {
      title: p.name,
    });

    marker.bindPopup(
      `<strong>${p.name}</strong><br/>
       Clan: ${p.clan || "Unknown"}<br/>
       Faction: ${p.faction || "Unknown"}<br/>
       Zone: ${p.zone_name}`
    );

    playerLayerGroup.addLayer(marker);
  });
}

function renderHuntingHeat() {
  if (huntingHeatLayer) {
    map.removeLayer(huntingHeatLayer);
    huntingHeatLayer = null;
  }

  if (!document.getElementById("toggle_hunting").checked) return;

  const points = [];
  zonesData.forEach((z) => {
    if (!z.lat || !z.lng) return;
    if (z.hunting_risk && z.hunting_risk > 0) {
      const intensity = Math.min(1, z.hunting_risk / 5);
      points.push([z.lat, z.lng, intensity]);
    }
  });

  if (points.length > 0) {
    huntingHeatLayer = L.heatLayer(points, { radius: 25, blur: 18 }).addTo(map);
  }
}

// --- DATA LOADING ---

async function loadZones() {
  try {
    const res = await fetch("/api/map/zones");
    zonesData = await res.json();
    renderZones();
    renderHuntingHeat();
  } catch (err) {
    console.error("Failed to load zones:", err);
  }
}

async function loadPlayers() {
  try {
    const res = await fetch("/api/map/players");
    playersData = await res.json();
    renderPlayers();
  } catch (err) {
    console.error("Failed to load players:", err);
  }
}

async function loadDirectorState() {
  try {
    const res = await fetch("/api/map/state");
    const state = await res.json();
    // You can use this later to display global threat level etc.
    console.log("Director state:", state);
  } catch (err) {
    console.error("Failed to load director state:", err);
  }
}

// --- FILTER HOOKS ---

document.getElementById("filter_camarilla").addEventListener("change", () => {
  renderZones();
});
document.getElementById("filter_anarch").addEventListener("change", () => {
  renderZones();
});
document.getElementById("filter_sabbat").addEventListener("change", () => {
  renderZones();
});
document.getElementById("filter_si").addEventListener("change", () => {
  renderZones();
});
document.getElementById("filter_other").addEventListener("change", () => {
  renderZones();
});
document.getElementById("toggle_hunting").addEventListener("change", () => {
  renderHuntingHeat();
});
document.getElementById("toggle_players").addEventListener("change", () => {
  renderPlayers();
});

// --- INITIAL LOAD & POLLING ---

loadZones();
loadPlayers();
loadDirectorState();

// Refresh players + director state periodically (pseudo real-time)
setInterval(() => {
  loadPlayers();
  loadDirectorState();
}, 15000);