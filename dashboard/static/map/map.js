// --- BASE MAP INITIALIZATION ---

let map = L.map("map").setView([20, 0], 2); // world-ish default view

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 19,
}).addTo(map);

// --- LAYERS ---

let zoneLayerGroup = L.layerGroup().addTo(map);
let playerLayerGroup = L.layerGroup().addTo(map);
let huntingHeatLayer = null;
let siHeatLayer = null;

let zonesData = [];
let playersData = [];
let directorState = null;

// --- UTILS ---

function factionColor(faction) {
  if (!faction) return "#888";
  const f = faction.toLowerCase();
  if (f.includes("camarilla")) return "#4a90e2";
  if (f.includes("anarch")) return "#e94e77";
  if (f.includes("sabbat")) return "#900c3f";
  if (f.includes("si") || f.includes("second inquisition") || f.includes("pentex"))
    return "#ffcc00";
  return "#aaaaaa";
}

function passesFactionFilter(faction) {
  const f = (faction || "other").toLowerCase();
  if (f.includes("camarilla") && !document.getElementById("filter_camarilla").checked)
    return false;
  if (f.includes("anarch") && !document.getElementById("filter_anarch").checked)
    return false;
  if (f.includes("sabbat") && !document.getElementById("filter_sabbat").checked)
    return false;
  if (
    (f.includes("si") || f.includes("second inquisition") || f.includes("pentex")) &&
    !document.getElementById("filter_si").checked
  )
    return false;

  if (
    !(
      f.includes("camarilla") ||
      f.includes("anarch") ||
      f.includes("sabbat") ||
      f.includes("si") ||
      f.includes("second inquisition") ||
      f.includes("pentex")
    )
  ) {
    if (!document.getElementById("filter_other").checked) return false;
  }

  return true;
}

// --- RENDERING FUNCTIONS ---

function renderZones() {
  zoneLayerGroup.clearLayers();

  zonesData.forEach((z) => {
    if (!z.lat || !z.lng) return;
    if (!passesFactionFilter(z.faction)) return;

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
    if (!passesFactionFilter(p.faction)) return;

    const color = factionColor(p.faction);

    const marker = L.circleMarker([p.lat, p.lng], {
      radius: 5,
      color: color,
      fillColor: color,
      fillOpacity: 0.9,
    });

    marker.bindPopup(
      `<strong>${p.name}</strong><br/>
       Clan: ${p.clan || "Unknown"}<br/>
       Faction: ${p.faction || "Unknown"}<br/>
       Zone: ${p.zone_name || "Unknown"}`
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

function renderSiHeat() {
  if (siHeatLayer) {
    map.removeLayer(siHeatLayer);
    siHeatLayer = null;
  }

  const toggle = document.getElementById("toggle_si_heat");
  if (!toggle || !toggle.checked) return;

  const points = [];
  zonesData.forEach((z) => {
    if (!z.lat || !z.lng) return;
    if (z.si_risk && z.si_risk > 0) {
      // Base intensity from zone si_risk (1–5)
      let baseIntensity = Math.min(1, z.si_risk / 5);

      // Optionally scale by global Second Inquisition pressure from Director state
      let globalMultiplier = 1.0;
      if (
        directorState &&
        directorState.themes &&
        typeof directorState.themes.second_inquisition === "number"
      ) {
        const siTheme = directorState.themes.second_inquisition;
        // Rough scaling: every 20 points of SI theme adds +0.2 intensity (capped at +1)
        globalMultiplier += Math.min(1.0, siTheme / 20.0);
      }

      const intensity = Math.min(1, baseIntensity * globalMultiplier);
      points.push([z.lat, z.lng, intensity]);
    }
  });

  if (points.length > 0) {
    siHeatLayer = L.heatLayer(points, { radius: 30, blur: 22 }).addTo(map);
  }
}

// --- DATA LOADING ---

async function loadZones() {
  try {
    const res = await fetch("/api/map/zones");
    zonesData = await res.json();
    renderZones();
    renderHuntingHeat();
    renderSiHeat();
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
    directorState = state || null;
    // You can also display this in a UI widget later.
    console.log("Director state:", directorState);
    // Refresh SI heat layer in case global SI pressure changed
    renderSiHeat();
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
document.getElementById("toggle_si_heat").addEventListener("change", () => {
  renderSiHeat();
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