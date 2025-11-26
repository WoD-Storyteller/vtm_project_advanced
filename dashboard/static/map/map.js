// ---- BASE MAP ----
let map = L.map("map").setView([51.27, 1.08], 10);

// You can swap for custom tiles later
L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 19,
}).addTo(map);

// ---- LAYER GROUPS ----
let layerControl = L.control.layers().addTo(map);

// ---- LOAD KML LAYERS ----
function loadKML(name, file) {
  let layer = omnivore.kml(`/static/map/layers/${file}`)
    .on("ready", function () {
      map.fitBounds(layer.getBounds());
    })
    .addTo(map);

  layerControl.addOverlay(layer, name);
}

// ---- LOAD GEOJSON LAYERS ----
function loadGeoJSON(name, file, style = { color: "red" }) {
  fetch(`/static/map/layers/${file}`)
    .then((r) => r.json())
    .then((data) => {
      let layer = L.geoJSON(data, { style }).addTo(map);
      layerControl.addOverlay(layer, name);
    });
}

// ---- LOAD YOUR LAYERS ----
// KML
loadKML("Nosferatu Tunnels", "nos_tunnels.kml");
loadKML("Sabbat Routes", "sabbat_routes.kml");

// GEOJSON
loadGeoJSON("Domains", "domains.geojson", { color: "#4a90e2" });
loadGeoJSON("SI Patrol Lines", "si_patrols.geojson", { color: "#e84118" });