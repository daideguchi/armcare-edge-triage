const colors = {
  urgent_care: "#C94B4B",
  access_support: "#2E8B7B",
  paperwork: "#5A6F9B",
  routine_followup: "#A66A2D",
};

const labelText = (value) => String(value).replaceAll("_", " ");
const number = (value, digits = 1) => Number(value).toFixed(digits);
const compactRate = (value) => {
  if (value >= 1_000_000) return `${number(value / 1_000_000, 1)}M/s`;
  if (value >= 1_000) return `${number(value / 1_000, 1)}K/s`;
  return `${Math.round(value)}/s`;
};

function render(data) {
  document.getElementById("platform").textContent = `${data.platform.machine} / ${data.platform.mac_model || "Arm device"} / ${data.platform.numpy}`;
  document.getElementById("speedup").textContent = `${number(data.speedup, 1)}x`;
  document.getElementById("optimized-latency").textContent = `${number(data.optimized.median_ms, 2)} ms`;
  document.getElementById("accuracy").textContent = `${number(data.optimized.accuracy * 100, 1)}%`;
  document.getElementById("memory").textContent = `${number(data.memory.reduction_percent, 1)}%`;
  document.getElementById("throughput").textContent = compactRate(data.optimized.tickets_per_second);
  document.getElementById("baseline-name").textContent = data.baseline.name;
  document.getElementById("optimized-name").textContent = data.optimized.name;
  document.getElementById("dataset").textContent = `${data.dataset.samples.toLocaleString()} tickets`;
  document.getElementById("boundary").textContent = data.claim_boundary;

  const tickets = document.getElementById("tickets");
  tickets.innerHTML = "";
  data.sample_tickets.slice(0, 8).forEach((ticket) => {
    const item = document.createElement("article");
    item.className = "ticket";
    item.innerHTML = `
      <i style="background:${colors[ticket.queue] || "#2E8B7B"}"></i>
      <div>
        <strong>${labelText(ticket.queue)}</strong>
        <p>${ticket.message}</p>
      </div>
    `;
    tickets.appendChild(item);
  });

  const counts = data.dataset.class_counts;
  const max = Math.max(...Object.values(counts));
  const bars = document.getElementById("bars");
  bars.innerHTML = "";
  Object.entries(counts).forEach(([name, count]) => {
    const row = document.createElement("div");
    row.className = "bar-row";
    row.innerHTML = `
      <div class="bar-label">${labelText(name)}</div>
      <div class="bar-track"><div class="bar-fill" style="width:${(count / max) * 100}%; background:${colors[name] || "#2E8B7B"}"></div></div>
      <div class="bar-value">${count}</div>
    `;
    bars.appendChild(row);
  });

  const chips = document.getElementById("class-chips");
  chips.innerHTML = "";
  data.dataset.classes.forEach((name) => {
    const chip = document.createElement("span");
    chip.className = "chip";
    chip.style.background = colors[name] || "#2E8B7B";
    chip.textContent = labelText(name);
    chips.appendChild(chip);
  });
}

async function boot() {
  if (window.ARMCARE_BENCHMARK) {
    render(window.ARMCARE_BENCHMARK);
    return;
  }
  const response = await fetch("./benchmark.json");
  render(await response.json());
}

boot().catch((error) => {
  document.body.dataset.error = String(error);
  console.error(error);
});
