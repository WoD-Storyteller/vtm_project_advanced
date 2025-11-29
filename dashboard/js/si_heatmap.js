async function loadSIHeatMap() {
  const res = await fetch('/map/zones');
  const data = await res.json();
  if (!data.ok) {
    alert('Failed to load zones');
    return;
  }

  const zones = data.zones || [];
  const container = document.getElementById('si_heatmap');
  container.innerHTML = '';

  zones.forEach(z => {
    const si = z.si_risk || 0;

    // color grading
    const color =
      si >= 7 ? '#ff0000' :
      si >= 5 ? '#ff7700' :
      si >= 3 ? '#ffaa00' :
      si >= 1 ? '#ffff00' : '#00ff00';

    const div = document.createElement('div');
    div.className = 'si_zone';
    div.style.background = color;
    div.style.padding = '8px';
    div.style.margin = '4px';
    div.style.borderRadius = '6px';

    div.innerHTML = `<strong>${z.name}</strong><br>SI Risk: ${si}`;
    container.appendChild(div);
  });
}
