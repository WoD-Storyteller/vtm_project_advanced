let map = L.map("map").setView([20, 0], 2); // world view

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 19,
}).addTo(map);

let zoneLayerGroup = L.layerGroup().addTo(map);
let playerLayerGroup = L.layerGroup().addTo(map);
let huntingHeatLayer = null;

let zonesData = [];
let playersData = [];

// faction -> color
function factionColor(f) {
  if (!f) return "#7f8c8d";
  f = f.toLowerCase();
  if (f.includes("camarilla")) return "#2980b9";
  if (f.includes("anarch")) return "#e67e22";
  if (f.includes("sabbat")) return "#c0392b";
  if (f.includes("ministry")) return "#8e44ad";
  if (f.includes("hecata")) return "#16a085";
  if (f.includes("thin")) return "#f1c40f";
  if (f.includes("si") || f.includes("inquisition") || f.includes("pentex")) return "#e74c3c";
  return "#7f8c8d";
}

function passesFactionFilter(z) {
  const f = (z.faction || "").toLowerCase();
  const tags = (z.tags || []).map(t => t.toLowerCase());

  const camOn = document.getElementById("filter_camarilla").checked;
  const anaOn = document.getElementById("filter_anarch").checked;
  const sabOn = document.getElementById("filter_sabbat").checked;
  const siOn  = document.getElementById("filter_si").checked;
  const othOn = document.getElementById("filter_other").checked;

  const isCam = f.includes("camarilla");
  const isAn  = f.includes("anarch");
  const isSab = f.includes("sabbat");
  const isSi  = f.includes("si") || f.includes("inquisition") || f.includes("pentex");

  if (isCam && !camOn) return false;
  if (isAn  && !anaOn) return false;
  if (isSab && !sabOn) return false;
  if (isSi  && !siOn)  return false;
  if (!isCam && !isAn && !isSab && !isSi && !othOn) return false;

  return true;
}

function renderZones() {
  zoneLayerGroup.clearLayers();

  zonesData.forEach(z => {
    if (!z.lat || !z.lng) return;
    if (!passesFactionFilter(z)) return;

    const color = factionColor(z.faction);
    const marker = L.circleMarker([z.lat, z.lng], {
      radius: 6,
      color: color,
      fillColor: color,
      fillOpacity: 0.8,
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

  playersData.forEach(p => {
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
  zonesData.forEach(z => {
    if (!z.lat || !z.lng) return;
    if (z.hunting_risk && z.hunting_risk > 0) {
      // heatmap values are [lat, lng, intensity 0-1]
      points.push([z.lat, z.lng, Math.min(1, z.hunting_risk / 5)]);
    }
  });

  if (points.length > 0) {
    huntingHeatLayer = L.heatLayer(points, { radius: 25, blur: 15 }).addTo(map);
  }
}

// --- Fetch data from API --- //

async function loadZones() {
  const res = await fetch("/api/map/zones");
  zonesData = await res.json();
  renderZones();
  renderHuntingHeat();
}

async function loadPlayers() {
  const res = await fetch("/api/map/players");
  playersData = await res.json();
  renderPlayers();
}

async function loadDirectorState() {
  const res = await fetch("/api/map/state");
  const state = await res.json();
  // You can use this later to animate some global threat indicators in UI
  console.log("Director state:", state);
}

// Attach filter listeners
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

// initial load
loadZones();
loadPlayers();
loadDirectorState();

// periodic refresh (pseudo real-time)
setInterval(() => {
  loadPlayers();
  loadDirectorState();
}, 15000);