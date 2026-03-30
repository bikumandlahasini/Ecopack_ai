// Auto-dismiss alerts
document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".alert-auto").forEach(el => {
    setTimeout(() => el.classList.add("fade"), 3000);
    setTimeout(() => el.remove(), 3500);
  });

  // Animate stat numbers
  document.querySelectorAll(".stat-number[data-val]").forEach(el => {
    const target = parseFloat(el.dataset.val);
    const isFloat = el.dataset.val.includes(".");
    let current = 0;
    const step = target / 40;
    const timer = setInterval(() => {
      current += step;
      if (current >= target) { current = target; clearInterval(timer); }
      el.textContent = isFloat ? current.toFixed(1) : Math.floor(current);
    }, 30);
  });
});

// Render bar chart for top materials
function renderBarChart(canvasId, labels, data) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;
  new Chart(ctx, {
    type: "bar",
    data: {
      labels,
      datasets: [{
        label: "Recommendations",
        data,
        backgroundColor: "rgba(25,135,84,0.8)",
        borderColor: "#198754",
        borderWidth: 1,
        borderRadius: 6,
      }]
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
      scales: {
        y: { beginAtZero: true, grid: { color: "#f0f0f0" } },
        x: { grid: { display: false } }
      }
    }
  });
}

// Render line chart for last 7 days
function renderLineChart(canvasId, labels, data) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;
  new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [{
        label: "Recommendations",
        data,
        borderColor: "#198754",
        backgroundColor: "rgba(25,135,84,0.1)",
        borderWidth: 2,
        pointBackgroundColor: "#198754",
        pointRadius: 5,
        fill: true,
        tension: 0.4,
      }]
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
      scales: {
        y: { beginAtZero: true, grid: { color: "#f0f0f0" } },
        x: { grid: { display: false } }
      }
    }
  });
}
