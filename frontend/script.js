/**
 * NexusAI - Next-Gen Autonomous BI & Real-Time Decision Automation Platform
 * Frontend Controller & Chart.js Orchestrator
 */

// Dynamically connect to the active backend host on whatever port it is running
const API_BASE = window.location.protocol.startsWith("http")
  ? (window.location.port === "5500" || window.location.port === "3000" ? `${window.location.protocol}//${window.location.hostname}:8000` : window.location.origin)
  : "http://localhost:8000";

const STANDARD_FIELDS = [
  { key: "sales", label: "Revenue / Sales", icon: "💰", req: true },
  { key: "profit", label: "Net Profit / Margin", icon: "📈", req: false },
  { key: "quantity", label: "Units Quantity", icon: "📦", req: false },
  { key: "price", label: "Unit Price", icon: "🏷️", req: false },
  { key: "discount", label: "Discount %", icon: "✂️", req: false },
  { key: "shipping_cost", label: "Shipping / Freight", icon: "🚢", req: false },
  { key: "date", label: "Transaction Date", icon: "📅", req: true },
  { key: "customer_id", label: "Customer ID", icon: "👤", req: false },
  { key: "customer_name", label: "Customer Name", icon: "📛", req: false },
  { key: "customer_segment", label: "Customer Tier", icon: "⭐", req: false },
  { key: "product_name", label: "Product Name", icon: "📦", req: false },
  { key: "category", label: "Product Category", icon: "🗂️", req: false },
  { key: "region", label: "Region / Market", icon: "🗺️", req: false },
  { key: "city", label: "City", icon: "🏙️", req: false },
  { key: "payment_method", label: "Payment Mode", icon: "💳", req: false },
];

let state = {
  fileId: null,
  filename: "",
  allColumns: [],
  mapping: {},
  columnMeta: {},
  companyProfile: {},
  typesafeKey: localStorage.getItem("nexus_typesafe_key") || "",
  biReport: null,
  newsData: null,
  activeFilter: "all",
  charts: {},
  theme: localStorage.getItem("nexus_theme") || "nexus-classic",
  mode: localStorage.getItem("nexus_mode") || "dark"
};

const THEMES = {
  "nexus-classic": { name: "Nexus Classic", desc: "Cyber Indigo & Cyan (Original)", icon: "⚡", primary: "#38bdf8", secondary: "#6366f1", tertiary: "#a855f7" },
  "datava": { name: "Datava", desc: "Vibrant Violet & Lavender", icon: "🔮", primary: "#7c3aed", secondary: "#a78bfa", tertiary: "#f97316" },
  "nexora": { name: "Nexora", desc: "Emerald Mint & Eco-Tech", icon: "🌿", primary: "#10b981", secondary: "#34d399", tertiary: "#059669" },
  "pulseai": { name: "PulseAI", desc: "Sunset Peach & Warm Amber", icon: "🌅", primary: "#f97316", secondary: "#fb923c", tertiary: "#ea580c" },
  "cosmic-nebula": { name: "Cosmic Nebula", desc: "Electric Magenta & Cyber Pink", icon: "🌌", primary: "#ec4899", secondary: "#d946ef", tertiary: "#8b5cf6" },
  "obsidian-onyx": { name: "Obsidian Onyx", desc: "Monochrome Titanium & Slate", icon: "💎", primary: "#94a3b8", secondary: "#cbd5e1", tertiary: "#38bdf8" },
};

const $ = (id) => document.getElementById(id);

// ==========================================================================
// Initialization & Health
// ==========================================================================
document.addEventListener("DOMContentLoaded", () => {
  initThemeSystem();
  initHealthCheck();
  initUploadListeners();
  initTabNavigation();
  initModalListeners();
  initForecastControls();
  initNewsControls();

  if (state.typesafeKey) {
    $("api-key-btn-text").textContent = "TypeSafe (Connected)";
    $("btn-open-key-modal").classList.add("badge-emerald");
  }
});

// ==========================================================================
// Theme & Appearance Management (6 Themes + Dark/Light Modes)
// ==========================================================================
function initThemeSystem() {
  state.theme = localStorage.getItem("nexus_theme") || "nexus-classic";
  state.mode = localStorage.getItem("nexus_mode") || "dark";

  applyTheme(state.theme, state.mode, false);

  const themePickerBtn = $("btn-theme-picker");
  const themeMenu = $("theme-menu");

  if (themePickerBtn && themeMenu) {
    themePickerBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      const isOpen = !themeMenu.classList.contains("dropdown-hidden");
      if (isOpen) {
        closeThemeMenu();
      } else {
        openThemeMenu();
      }
    });

    document.addEventListener("click", (e) => {
      if (!themeMenu.contains(e.target) && !themePickerBtn.contains(e.target)) {
        closeThemeMenu();
      }
    });

    document.querySelectorAll(".theme-item").forEach(item => {
      item.addEventListener("click", () => {
        const selectedTheme = item.getAttribute("data-theme");
        if (selectedTheme && THEMES[selectedTheme]) {
          applyTheme(selectedTheme, state.mode);
          closeThemeMenu();
        }
      });
    });
  }

  document.querySelectorAll(".quick-pill").forEach(pill => {
    pill.addEventListener("click", () => {
      const selectedTheme = pill.getAttribute("data-pill-theme");
      if (selectedTheme && THEMES[selectedTheme]) {
        applyTheme(selectedTheme, state.mode);
      }
    });
  });

  const modeBtn = $("btn-mode-toggle");
  if (modeBtn) {
    modeBtn.addEventListener("click", () => {
      const nextMode = state.mode === "dark" ? "light" : "dark";
      applyTheme(state.theme, nextMode);
    });
  }

  const quickModeBtn = $("btn-quick-mode");
  if (quickModeBtn) {
    quickModeBtn.addEventListener("click", () => {
      const nextMode = state.mode === "dark" ? "light" : "dark";
      applyTheme(state.theme, nextMode);
    });
  }
}

function openThemeMenu() {
  const menu = $("theme-menu");
  const btn = $("btn-theme-picker");
  if (menu && btn) {
    menu.classList.remove("dropdown-hidden");
    btn.classList.add("menu-open");
    btn.setAttribute("aria-expanded", "true");
  }
}

function closeThemeMenu() {
  const menu = $("theme-menu");
  const btn = $("btn-theme-picker");
  if (menu && btn) {
    menu.classList.add("dropdown-hidden");
    btn.classList.remove("menu-open");
    btn.setAttribute("aria-expanded", "false");
  }
}

function applyTheme(themeKey, modeKey, updateCharts = true) {
  state.theme = themeKey;
  state.mode = modeKey;

  localStorage.setItem("nexus_theme", themeKey);
  localStorage.setItem("nexus_mode", modeKey);

  document.documentElement.setAttribute("data-theme", themeKey);
  document.documentElement.setAttribute("data-mode", modeKey);

  const themeInfo = THEMES[themeKey] || THEMES["nexus-classic"];

  if ($("theme-active-name")) {
    $("theme-active-name").textContent = themeInfo.name;
  }
  if ($("theme-active-dot")) {
    $("theme-active-dot").style.background = themeInfo.primary;
    $("theme-active-dot").style.boxShadow = `0 0 8px ${themeInfo.primary}`;
  }

  const modeText = modeKey === "dark" ? "Dark" : "Light";
  if ($("mode-label")) $("mode-label").textContent = modeText;
  if ($("quick-mode-text")) $("quick-mode-text").textContent = `${modeText} Mode`;
  const quickIcon = document.querySelector(".quick-mode-icon");
  if (quickIcon) {
    quickIcon.textContent = modeKey === "dark" ? "🌙" : "☀️";
  }

  document.querySelectorAll(".theme-item").forEach(item => {
    if (item.getAttribute("data-theme") === themeKey) {
      item.classList.add("active");
    } else {
      item.classList.remove("active");
    }
  });

  document.querySelectorAll(".quick-pill").forEach(pill => {
    if (pill.getAttribute("data-pill-theme") === themeKey) {
      pill.classList.add("active");
    } else {
      pill.classList.remove("active");
    }
  });

  const stop1 = $("logo-stop-1");
  const stop2 = $("logo-stop-2");
  const stop3 = $("logo-stop-3");
  if (stop1 && stop2 && stop3) {
    stop1.setAttribute("stop-color", themeInfo.primary);
    stop2.setAttribute("stop-color", themeInfo.secondary);
    stop3.setAttribute("stop-color", themeInfo.tertiary);
  }

  if (updateCharts && state.biReport) {
    renderRevenueTrendChart(state.biReport.trends);
    renderCategoryBreakdownChart(state.biReport.product_affinity ? state.biReport.product_affinity.categories : null);
    renderForecast(state.biReport.forecast);
    renderCustomerIntelligence(state.biReport.customer_intelligence);
    renderProductsAndGeo(state.biReport.product_affinity, state.biReport.geographic_breakdown);
  }
}

function hexToRgba(hex, alpha) {
  let c = hex.replace("#", "");
  if (c.length === 3) c = c.split("").map(x => x + x).join("");
  const num = parseInt(c, 16);
  const r = (num >> 16) & 255;
  const g = (num >> 8) & 255;
  const b = num & 255;
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

function getThemeChartPalette() {
  const isLight = (state.mode === "light");
  const theme = state.theme || "nexus-classic";

  const gridColor = isLight ? "rgba(0, 0, 0, 0.07)" : "rgba(255, 255, 255, 0.06)";
  const textColor = isLight ? "#475569" : "#94a3b8";
  const tooltipBg = isLight ? "#ffffff" : "#0f172a";
  const tooltipText = isLight ? "#0f172a" : "#f8fafc";
  const tooltipBorder = isLight ? "rgba(0, 0, 0, 0.12)" : "rgba(255, 255, 255, 0.12)";

  let primary = "#38bdf8";
  let secondary = "#6366f1";
  let profit = "#10b981";
  let forecastColor = "#f59e0b";
  let doughnut = ["#10b981", "#38bdf8", "#818cf8", "#c084fc", "#f59e0b", "#f43f5e"];
  let geoColors = ["#6366f1", "#10b981", "#38bdf8", "#f59e0b", "#ec4899", "#8b5cf6"];

  if (theme === "datava") {
    primary = isLight ? "#7c3aed" : "#8b5cf6";
    secondary = isLight ? "#8b5cf6" : "#a78bfa";
    profit = isLight ? "#059669" : "#10b981";
    forecastColor = "#f97316";
    doughnut = ["#8b5cf6", "#a78bfa", "#f97316", "#06b6d4", "#10b981", "#c084fc"];
    geoColors = ["#7c3aed", "#f97316", "#06b6d4", "#10b981", "#a78bfa", "#e11d48"];
  } else if (theme === "nexora") {
    primary = isLight ? "#059669" : "#10b981";
    secondary = isLight ? "#10b981" : "#34d399";
    profit = isLight ? "#047857" : "#059669";
    forecastColor = "#10b981";
    doughnut = ["#10b981", "#34d399", "#059669", "#6ee7b7", "#0284c7", "#f59e0b"];
    geoColors = ["#059669", "#10b981", "#34d399", "#0284c7", "#f59e0b", "#064e3b"];
  } else if (theme === "pulseai") {
    primary = isLight ? "#ea580c" : "#f97316";
    secondary = isLight ? "#f97316" : "#fb923c";
    profit = isLight ? "#059669" : "#10b981";
    forecastColor = "#ea580c";
    doughnut = ["#f97316", "#fb923c", "#ea580c", "#fdba74", "#06b6d4", "#10b981"];
    geoColors = ["#ea580c", "#f97316", "#fb923c", "#fdba74", "#0284c7", "#10b981"];
  } else if (theme === "cosmic-nebula") {
    primary = isLight ? "#db2777" : "#ec4899";
    secondary = isLight ? "#c026d3" : "#d946ef";
    profit = isLight ? "#059669" : "#10b981";
    forecastColor = "#d946ef";
    doughnut = ["#ec4899", "#d946ef", "#a855f7", "#6366f1", "#f43f5e", "#06b6d4"];
    geoColors = ["#ec4899", "#d946ef", "#8b5cf6", "#6366f1", "#38bdf8", "#f43f5e"];
  } else if (theme === "obsidian-onyx") {
    primary = isLight ? "#09090b" : "#f8fafc";
    secondary = isLight ? "#334155" : "#94a3b8";
    profit = isLight ? "#059669" : "#10b981";
    forecastColor = isLight ? "#475569" : "#cbd5e1";
    doughnut = isLight 
      ? ["#09090b", "#334155", "#64748b", "#94a3b8", "#0284c7", "#059669"]
      : ["#f8fafc", "#cbd5e1", "#94a3b8", "#64748b", "#38bdf8", "#10b981"];
    geoColors = isLight
      ? ["#09090b", "#334155", "#64748b", "#94a3b8", "#cbd5e1", "#0284c7"]
      : ["#f8fafc", "#cbd5e1", "#94a3b8", "#64748b", "#38bdf8", "#10b981"];
  }

  return {
    isLight,
    gridColor,
    textColor,
    tooltipBg,
    tooltipText,
    tooltipBorder,
    primary,
    secondary,
    profit,
    forecastColor,
    doughnut,
    geoColors
  };
}

async function initHealthCheck() {
  try {
    const res = await fetch(`${API_BASE}/api/health`);
    if (res.ok) {
      const data = await res.json();
      $("status-label").textContent = data.typesafe_jev_connected ? "Jev Cloud Active" : "Jev Dual-Mode Ready";
    }
  } catch (err) {
    $("status-label").textContent = "Connecting...";
  }
}

// ==========================================================================
// Data Upload & Ingestion
// ==========================================================================
function initUploadListeners() {
  const dropzone = $("dropzone");
  const fileInput = $("file-input");

  $("btn-browse-file").addEventListener("click", (e) => {
    e.stopPropagation();
    fileInput.click();
  });

  dropzone.addEventListener("click", () => fileInput.click());

  fileInput.addEventListener("change", (e) => {
    if (e.target.files.length > 0) {
      handleFileUpload(e.target.files[0]);
    }
  });

  // Drag and Drop
  ["dragenter", "dragover"].forEach(evt => {
    dropzone.addEventListener(evt, (e) => {
      e.preventDefault();
      dropzone.classList.add("dragover");
    });
  });

  ["dragleave", "drop"].forEach(evt => {
    dropzone.addEventListener(evt, (e) => {
      e.preventDefault();
      dropzone.classList.remove("dragover");
    });
  });

  dropzone.addEventListener("drop", (e) => {
    if (e.dataTransfer.files.length > 0) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  });

  // 1-Click Sample Dataset
  $("btn-load-sample").addEventListener("click", (e) => {
    e.stopPropagation();
    handleLoadSample();
  });
}

function setUploadStatus(msg, kind = "") {
  const el = $("upload-status");
  el.textContent = msg;
  el.className = "upload-status" + (kind ? " " + kind : "");
}

async function handleFileUpload(file) {
  setUploadStatus("Ingesting table & executing TypeSafe Jev schema classification...", "loading");
  const formData = new FormData();
  formData.append("file", file);
  if (state.typesafeKey) {
    formData.append("typesafe_key", state.typesafeKey);
  }

  try {
    const res = await fetch(`${API_BASE}/api/upload`, { method: "POST", body: formData });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Upload failed");

    applyUploadedMetadata(data);
    setUploadStatus(`Loaded '${file.name}' (${data.total_rows.toLocaleString()} rows, ${data.total_columns} columns)`, "ok");
  } catch (err) {
    setUploadStatus(err.message, "error");
  }
}

async function handleLoadSample() {
  setUploadStatus("Loading enterprise sample Kaggle dataset with TypeSafe Jev...", "loading");
  const formData = new FormData();
  if (state.typesafeKey) {
    formData.append("typesafe_key", state.typesafeKey);
  }

  try {
    const res = await fetch(`${API_BASE}/api/load-sample`, { method: "POST", body: formData });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Sample loading failed");

    applyUploadedMetadata(data);
    setUploadStatus("Loaded Global E-Commerce Sample Dataset (2,500 rows, 16 features)", "ok");
  } catch (err) {
    setUploadStatus(err.message, "error");
  }
}

function applyUploadedMetadata(data) {
  state.fileId = data.file_id;
  state.filename = data.filename;
  state.allColumns = data.columns;
  state.mapping = data.detected_mapping;
  state.columnMeta = data.column_meta;
  state.companyProfile = data.company_profile;

  // Show header industry context badge
  if (data.company_profile && data.company_profile.industry) {
    $("detected-industry-text").textContent = `Industry: ${data.company_profile.industry}`;
    $("company-badge-wrap").style.display = "block";
  }

  // Render schema review cards
  renderSchemaGrid();
  $("mapping-card").classList.remove("hidden");
  $("mapping-card").scrollIntoView({ behavior: "smooth" });

  // Bind Run Full Analysis Button
  $("btn-run-full-analysis").onclick = () => executeFullAnalysis();
}

// ==========================================================================
// Schema Grid Rendering
// ==========================================================================
function renderSchemaGrid() {
  const container = $("schema-grid");
  container.innerHTML = "";

  STANDARD_FIELDS.forEach(field => {
    const item = document.createElement("div");
    item.className = "schema-item";

    const mappedCol = state.mapping[field.key] || "";
    const meta = mappedCol && state.columnMeta[mappedCol] ? state.columnMeta[mappedCol] : null;
    const confidencePct = meta ? Math.round((meta.confidence || 0.9) * 100) : null;

    let optionsHtml = `<option value="">-- Not Assigned --</option>`;
    state.allColumns.forEach(col => {
      const selected = col === mappedCol ? "selected" : "";
      optionsHtml += `<option value="${col}" ${selected}>${col}</option>`;
    });

    const samples = meta && meta.samples ? meta.samples.slice(0, 3) : [];
    const samplePillsHtml = samples.map(s => `<span class="sample-pill">${escapeHtml(s)}</span>`).join("");

    item.innerHTML = `
      <div class="schema-item-header">
        <div class="field-badge">${field.icon} ${field.label}</div>
        ${confidencePct ? `<span class="confidence-badge">${confidencePct}% Match</span>` : ''}
      </div>
      <select class="schema-select" data-field="${field.key}">
        ${optionsHtml}
      </select>
      ${samples.length ? `<div class="sample-pills">${samplePillsHtml}</div>` : ''}
    `;

    const select = item.querySelector("select");
    select.addEventListener("change", () => {
      if (select.value) {
        state.mapping[field.key] = select.value;
      } else {
        delete state.mapping[field.key];
      }
    });

    container.appendChild(item);
  });
}

function renderManualMappingTable() {
  const tbody = document.querySelector("#manual-mapping-table tbody");
  tbody.innerHTML = "";

  STANDARD_FIELDS.forEach(field => {
    const tr = document.createElement("tr");
    const currentVal = state.mapping[field.key] || "";
    const meta = currentVal && state.columnMeta[currentVal] ? state.columnMeta[currentVal] : null;

    let options = `<option value="">-- Unmapped --</option>`;
    state.allColumns.forEach(c => {
      options += `<option value="${c}" ${c === currentVal ? "selected" : ""}>${c}</option>`;
    });

    tr.innerHTML = `
      <td><strong>${field.icon} ${field.label}</strong></td>
      <td>
        <select class="schema-select" data-field="${field.key}">${options}</select>
      </td>
      <td>
        <span class="badge ${meta ? 'badge-emerald' : 'badge-indigo'}">
          ${meta ? `${Math.round(meta.confidence * 100)}% (${meta.source || 'Jev'})` : 'Manual Override'}
        </span>
      </td>
    `;

    const sel = tr.querySelector("select");
    sel.addEventListener("change", () => {
      if (sel.value) state.mapping[field.key] = sel.value;
      else delete state.mapping[field.key];
    });

    tbody.appendChild(tr);
  });
}

// ==========================================================================
// Execution: Full BI & Live News Engine
// ==========================================================================
async function executeFullAnalysis() {
  if (!state.fileId) return;

  const btn = $("btn-run-full-analysis");
  btn.disabled = true;
  btn.innerHTML = `<span class="spinner" style="width:14px;height:14px;border-width:2px;display:inline-block;margin:0 6px 0 0;"></span> Computing Insights...`;

  const formData = new FormData();
  formData.append("file_id", state.fileId);
  formData.append("mapping", JSON.stringify(state.mapping));

  try {
    const res = await fetch(`${API_BASE}/api/analyze`, { method: "POST", body: formData });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Analysis computation failed");

    state.biReport = data;
    renderDashboard(data);
    $("dashboard-wrapper").classList.remove("hidden");
    $("dashboard-wrapper").scrollIntoView({ behavior: "smooth" });

    // Concurrently trigger live market news analysis
    fetchLiveNews();
  } catch (err) {
    alert("Analysis failed: " + err.message);
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"/></svg> Execute BI & Decision Engine`;
  }
}

// ==========================================================================
// Dashboard Rendering
// ==========================================================================
function renderDashboard(data) {
  // 1. Narrative Synthesis
  $("narrative-text").textContent = data.executive_narrative || "Multi-dimensional business analysis complete.";

  // 2. Summary KPIs
  const kpis = data.summary_kpis || {};
  animateValue($("kpi-revenue"), kpis.total_revenue, "$", 2);
  animateValue($("kpi-profit"), kpis.total_profit, "$", 2);
  $("kpi-margin-sub").textContent = `Net Profit Margin: ${kpis.profit_margin_pct}%`;
  animateValue($("kpi-aov"), kpis.average_order_value, "$", 2);
  animateValue($("kpi-orders"), kpis.total_orders, "", 0);
  $("kpi-units-sub").textContent = `Units Sold: ${(kpis.total_units_sold || 0).toLocaleString()}`;
  animateValue($("kpi-customers"), kpis.unique_customers, "", 0);
  $("kpi-discount").textContent = `${kpis.average_discount_pct}%`;

  // 3. Render Trend Charts
  renderRevenueTrendChart(data.trends);
  renderCategoryBreakdownChart(data.product_affinity ? data.product_affinity.categories : null);

  // 4. Render Forecast
  renderForecast(data.forecast);

  // 5. Render Customer Intelligence
  renderCustomerIntelligence(data.customer_intelligence);

  // 6. Render Products & Geography
  renderProductsAndGeo(data.product_affinity, data.geographic_breakdown);

  // 7. Render Schema mapping tab
  renderManualMappingTable();
}

function animateValue(obj, endVal, prefix = "", decimals = 0) {
  if (!obj) return;
  const num = Number(endVal) || 0;
  obj.textContent = `${prefix}${num.toLocaleString(undefined, { minimumFractionDigits: decimals, maximumFractionDigits: decimals })}`;
}

// ==========================================================================
// Chart.js Visualizations
// ==========================================================================
function destroyChart(name) {
  if (state.charts[name]) {
    state.charts[name].destroy();
    delete state.charts[name];
  }
}

function renderRevenueTrendChart(trends) {
  destroyChart("revenueTrend");
  const ctx = $("chart-revenue-trend").getContext("2d");
  if (!trends || !trends.labels || trends.labels.length === 0) return;

  const palette = getThemeChartPalette();

  const gradSales = ctx.createLinearGradient(0, 0, 0, 300);
  gradSales.addColorStop(0, hexToRgba(palette.primary, 0.45));
  gradSales.addColorStop(1, hexToRgba(palette.primary, 0.0));

  const gradProfit = ctx.createLinearGradient(0, 0, 0, 300);
  gradProfit.addColorStop(0, hexToRgba(palette.profit, 0.35));
  gradProfit.addColorStop(1, hexToRgba(palette.profit, 0.0));

  state.charts.revenueTrend = new Chart(ctx, {
    type: "line",
    data: {
      labels: trends.labels,
      datasets: [
        {
          label: "Revenue",
          data: trends.revenue,
          borderColor: palette.primary,
          backgroundColor: gradSales,
          fill: true,
          tension: 0.35,
          borderWidth: 2.5,
          pointRadius: 4,
          pointHoverRadius: 6,
          pointBackgroundColor: palette.primary
        },
        ...(trends.profit && trends.profit.length ? [{
          label: "Net Profit",
          data: trends.profit,
          borderColor: palette.profit,
          backgroundColor: gradProfit,
          fill: true,
          tension: 0.35,
          borderWidth: 2,
          pointRadius: 3,
          pointHoverRadius: 5,
          pointBackgroundColor: palette.profit
        }] : [])
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      plugins: {
        legend: { labels: { color: palette.textColor, font: { family: "Plus Jakarta Sans" } } },
        tooltip: {
          backgroundColor: palette.tooltipBg,
          titleColor: palette.tooltipText,
          bodyColor: palette.tooltipText,
          borderColor: palette.tooltipBorder,
          borderWidth: 1,
          callbacks: {
            label: (ctx) => ` ${ctx.dataset.label}: $${Number(ctx.raw).toLocaleString()}`
          }
        }
      },
      scales: {
        x: { grid: { color: palette.gridColor }, ticks: { color: palette.textColor } },
        y: {
          grid: { color: palette.gridColor },
          ticks: { color: palette.textColor, callback: (val) => `$${Number(val).toLocaleString()}` }
        }
      }
    }
  });
}

function renderCategoryBreakdownChart(catData) {
  destroyChart("categoryBreakdown");
  const ctx = $("chart-category-breakdown").getContext("2d");
  if (!catData || !catData.labels) return;

  const palette = getThemeChartPalette();

  state.charts.categoryBreakdown = new Chart(ctx, {
    type: "bar",
    data: {
      labels: catData.labels,
      datasets: [
        {
          label: "Sales Volume",
          data: catData.sales,
          backgroundColor: palette.secondary,
          borderRadius: 6
        },
        ...(catData.profit && catData.profit.length ? [{
          label: "Profit Contribution",
          data: catData.profit,
          backgroundColor: palette.profit,
          borderRadius: 6
        }] : [])
      ]
    },
    options: {
      indexAxis: "y",
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { labels: { color: palette.textColor } },
        tooltip: {
          backgroundColor: palette.tooltipBg,
          titleColor: palette.tooltipText,
          bodyColor: palette.tooltipText,
          borderColor: palette.tooltipBorder,
          borderWidth: 1,
          callbacks: {
            label: (ctx) => ` ${ctx.dataset.label}: $${Number(ctx.raw).toLocaleString()}`
          }
        }
      },
      scales: {
        x: {
          grid: { color: palette.gridColor },
          ticks: { color: palette.textColor, callback: (v) => `$${Number(v).toLocaleString()}` }
        },
        y: { grid: { display: false }, ticks: { color: palette.textColor } }
      }
    }
  });
}

function renderForecast(fc) {
  if (!fc || fc.status !== "ok") return;

  $("forecast-algo-used").textContent = fc.method;
  const growth = fc.projected_growth_pct || 0;
  $("forecast-growth-metric").textContent = `${growth >= 0 ? '+' : ''}${growth}% projected trend`;
  $("forecast-growth-metric").className = growth >= 0 ? "text-emerald" : "text-rose";

  destroyChart("forecast");
  const ctx = $("chart-forecast").getContext("2d");
  const palette = getThemeChartPalette();

  const allLabels = [...fc.history_labels, ...fc.forecast_labels];
  const historySeries = [...fc.history_values, ...Array(fc.forecast_values.length).fill(null)];

  // Connect forecast line cleanly with last actual point
  const forecastSeries = [
    ...Array(fc.history_values.length - 1).fill(null),
    fc.history_values[fc.history_values.length - 1],
    ...fc.forecast_values
  ];

  const upperSeries = [
    ...Array(fc.history_values.length - 1).fill(null),
    fc.history_values[fc.history_values.length - 1],
    ...fc.upper_bounds
  ];

  const lowerSeries = [
    ...Array(fc.history_values.length - 1).fill(null),
    fc.history_values[fc.history_values.length - 1],
    ...fc.lower_bounds
  ];

  state.charts.forecast = new Chart(ctx, {
    type: "line",
    data: {
      labels: allLabels,
      datasets: [
        {
          label: "Historical Actuals",
          data: historySeries,
          borderColor: palette.primary,
          backgroundColor: hexToRgba(palette.primary, 0.15),
          borderWidth: 2.5,
          tension: 0.3,
          pointRadius: 3
        },
        {
          label: "AI Projected Forecast",
          data: forecastSeries,
          borderColor: palette.forecastColor,
          borderDash: [5, 5],
          borderWidth: 2.5,
          tension: 0.3,
          pointRadius: 4,
          pointBackgroundColor: palette.forecastColor
        },
        {
          label: "Upper 95% Confidence",
          data: upperSeries,
          borderColor: hexToRgba(palette.forecastColor, 0.25),
          backgroundColor: hexToRgba(palette.forecastColor, 0.12),
          fill: "+1",
          pointRadius: 0,
          borderWidth: 1
        },
        {
          label: "Lower 95% Confidence",
          data: lowerSeries,
          borderColor: hexToRgba(palette.forecastColor, 0.25),
          pointRadius: 0,
          borderWidth: 1,
          fill: false
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      plugins: {
        legend: { labels: { color: palette.textColor } },
        tooltip: {
          backgroundColor: palette.tooltipBg,
          titleColor: palette.tooltipText,
          bodyColor: palette.tooltipText,
          borderColor: palette.tooltipBorder,
          borderWidth: 1,
          callbacks: {
            label: (ctx) => ctx.raw !== null ? ` ${ctx.dataset.label}: $${Number(ctx.raw).toLocaleString()}` : null
          }
        }
      },
      scales: {
        x: { grid: { color: palette.gridColor }, ticks: { color: palette.textColor } },
        y: {
          grid: { color: palette.gridColor },
          ticks: { color: palette.textColor, callback: (v) => `$${Number(v).toLocaleString()}` }
        }
      }
    }
  });

  // Populate Forecast Table
  const tbody = document.querySelector("#forecast-table tbody");
  tbody.innerHTML = "";
  fc.forecast_labels.forEach((lbl, idx) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><strong>${lbl}</strong></td>
      <td class="text-muted">$${Number(fc.lower_bounds[idx]).toLocaleString()}</td>
      <td class="text-amber"><strong>$${Number(fc.forecast_values[idx]).toLocaleString()}</strong></td>
      <td class="text-muted">$${Number(fc.upper_bounds[idx]).toLocaleString()}</td>
    `;
    tbody.appendChild(tr);
  });
}

function renderCustomerIntelligence(cust) {
  if (!cust || !cust.available) return;

  $("cust-repeat-rate").textContent = `${cust.repeat_rate_pct}%`;
  $("bar-repeat-rate").style.width = `${Math.min(100, cust.repeat_rate_pct)}%`;
  $("kpi-repeat-sub").textContent = `Repeat Rate: ${cust.repeat_rate_pct}%`;

  $("cust-pareto-share").textContent = `${cust.top_10_pct_revenue_share}%`;
  $("bar-pareto-share").style.width = `${Math.min(100, cust.top_10_pct_revenue_share)}%`;

  // Render RFM Doughnut Chart
  destroyChart("rfmDoughnut");
  const ctx = $("chart-rfm-doughnut").getContext("2d");
  const palette = getThemeChartPalette();
  const segNames = Object.keys(cust.segments);
  const segCounts = segNames.map(k => cust.segments[k].count);

  state.charts.rfmDoughnut = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: segNames,
      datasets: [{
        data: segCounts,
        backgroundColor: palette.doughnut,
        borderWidth: 2,
        borderColor: palette.isLight ? "#ffffff" : "#0f172a"
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: "right", labels: { color: palette.textColor, font: { size: 12 } } },
        tooltip: {
          backgroundColor: palette.tooltipBg,
          titleColor: palette.tooltipText,
          bodyColor: palette.tooltipText,
          borderColor: palette.tooltipBorder,
          borderWidth: 1,
          callbacks: {
            label: (ctx) => {
              const seg = cust.segments[segNames[ctx.dataIndex]];
              return ` ${ctx.label}: ${seg.count} clients ($${seg.total_revenue.toLocaleString()})`;
            }
          }
        }
      }
    }
  });

  // Top Customer Accounts Table
  const tbody = document.querySelector("#top-customers-table tbody");
  tbody.innerHTML = "";
  (cust.top_customers || []).forEach(c => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><strong>${escapeHtml(c.customer)}</strong></td>
      <td>${c.orders}</td>
      <td class="text-emerald">$${c.total_spent.toLocaleString()}</td>
      <td><span class="badge badge-indigo">${c.segment}</span></td>
    `;
    tbody.appendChild(tr);
  });
}

function renderProductsAndGeo(prod, geo) {
  const palette = getThemeChartPalette();

  // Top Products
  if (prod && prod.top_products_revenue) {
    destroyChart("topProducts");
    const ctx = $("chart-top-products").getContext("2d");
    state.charts.topProducts = new Chart(ctx, {
      type: "bar",
      data: {
        labels: prod.top_products_revenue.labels,
        datasets: [{
          label: "Total Sales",
          data: prod.top_products_revenue.values,
          backgroundColor: palette.primary,
          borderRadius: 6
        }]
      },
      options: {
        indexAxis: "y",
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: palette.tooltipBg,
            titleColor: palette.tooltipText,
            bodyColor: palette.tooltipText,
            borderColor: palette.tooltipBorder,
            borderWidth: 1,
            callbacks: { label: (c) => ` Sales: $${Number(c.raw).toLocaleString()}` }
          }
        },
        scales: {
          x: { grid: { color: palette.gridColor }, ticks: { color: palette.textColor } },
          y: { ticks: { color: palette.textColor, font: { size: 11 } } }
        }
      }
    });
  }

  // Geographic Distribution
  if (geo && geo.labels) {
    destroyChart("geoDist");
    const ctx = $("chart-geo-distribution").getContext("2d");
    state.charts.geoDist = new Chart(ctx, {
      type: "pie",
      data: {
        labels: geo.labels,
        datasets: [{
          data: geo.values,
          backgroundColor: palette.geoColors,
          borderWidth: 2,
          borderColor: palette.isLight ? "#ffffff" : "#0f172a"
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: "right", labels: { color: palette.textColor } },
          tooltip: {
            backgroundColor: palette.tooltipBg,
            titleColor: palette.tooltipText,
            bodyColor: palette.tooltipText,
            borderColor: palette.tooltipBorder,
            borderWidth: 1,
            callbacks: { label: (c) => ` ${c.label}: $${Number(c.raw).toLocaleString()}` }
          }
        }
      }
    });
  }

  // Cross-tab table
  if (geo && geo.crosstab && geo.crosstab.regions) {
    const ct = geo.crosstab;
    const thead = document.querySelector("#crosstab-table thead");
    const tbody = document.querySelector("#crosstab-table tbody");
    
    thead.innerHTML = `<tr><th>Region</th>${ct.categories.map(c => `<th>${escapeHtml(c)}</th>`).join('')}</tr>`;
    tbody.innerHTML = "";
    ct.regions.forEach((reg, rIdx) => {
      const rowVals = ct.matrix[rIdx] || [];
      const tr = document.createElement("tr");
      tr.innerHTML = `<td><strong>${escapeHtml(reg)}</strong></td>${rowVals.map(v => `<td>$${Number(v).toLocaleString()}</td>`).join('')}`;
      tbody.appendChild(tr);
    });
    $("crosstab-card").style.display = "block";
  } else {
    $("crosstab-card").style.display = "none";
  }
}

// ==========================================================================
// Live News & Strategic Decision Hub
// ==========================================================================
async function fetchLiveNews(customQuery = null) {
  const container = $("news-grid");
  container.innerHTML = `
    <div class="loading-state">
      <div class="spinner"></div>
      <p>Scanning global news wires, supply chain indicators & tariff alerts...</p>
    </div>
  `;

  const formData = new FormData();
  if (state.fileId) formData.append("file_id", state.fileId);
  if (state.companyProfile) formData.append("company_profile", JSON.stringify(state.companyProfile));
  if (customQuery) formData.append("custom_query", customQuery);

  try {
    const res = await fetch(`${API_BASE}/api/news`, { method: "POST", body: formData });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Failed to load live news");

    state.newsData = data;
    renderNewsHub(data);
  } catch (err) {
    container.innerHTML = `<div class="loading-state"><p class="text-rose">News update failed: ${err.message}</p></div>`;
  }
}

function renderNewsHub(news) {
  // 1. Posture & Counts
  const brief = news.executive_brief || {};
  $("posture-badge").textContent = brief.market_posture || "Active Market Intelligence";
  $("threats-count").textContent = brief.active_threats_count || 0;
  $("catalysts-count").textContent = brief.growth_catalysts_count || 0;
  $("news-badge-count").textContent = `${news.total_articles} Live`;

  // 2. Directives
  renderDirectives(brief.top_directives || []);

  // 3. Articles Feed
  renderArticles(news.articles || []);
}

function renderDirectives(directives) {
  const container = $("directives-grid");
  container.innerHTML = "";

  directives.forEach(dirText => {
    const div = document.createElement("div");
    div.className = "directive-card";
    div.innerHTML = `
      <div class="directive-icon">⚡</div>
      <div class="directive-text"><strong>Executive Action:</strong> ${escapeHtml(dirText)}</div>
    `;
    container.appendChild(div);
  });
}

function renderArticles(articles) {
  const container = $("news-grid");
  container.innerHTML = "";

  const filtered = state.activeFilter === "all"
    ? articles
    : articles.filter(a => a.category && a.category.includes(state.activeFilter));

  if (!filtered.length) {
    container.innerHTML = `<div class="loading-state"><p>No articles found for the selected category filter.</p></div>`;
    return;
  }

  filtered.forEach(art => {
    const card = document.createElement("div");
    card.className = "news-card";

    let badgeClass = "badge-neutral";
    if (art.sentiment === "Opportunity") badgeClass = "badge-opp";
    else if (art.sentiment === "Risk / Threat") badgeClass = "badge-risk";

    card.innerHTML = `
      <div>
        <div class="news-card-header">
          <span class="news-cat-tag">${art.category_icon || '📰'} ${art.category}</span>
          <span class="news-sentiment-badge ${badgeClass}">${art.sentiment}</span>
        </div>
        <h4 class="news-title">
          <a href="${art.link}" target="_blank" rel="noopener noreferrer">${escapeHtml(art.title)}</a>
        </h4>
        <p class="news-snippet">${escapeHtml(art.summary || "")}</p>
        ${art.executive_recommendation ? `
          <div class="news-directive-box">
            <strong>AI Operational Impact:</strong> ${escapeHtml(art.executive_recommendation)}
          </div>
        ` : ''}
      </div>
      <div class="news-footer">
        <span>${escapeHtml(art.source)}</span>
        <span>Relevance: ${art.relevance_score || 85}%</span>
      </div>
    `;

    container.appendChild(card);
  });
}

// ==========================================================================
// Control Listeners & Interactivity
// ==========================================================================
function initTabNavigation() {
  document.querySelectorAll(".tab-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
      document.querySelectorAll(".tab-pane").forEach(p => p.classList.remove("active"));

      btn.classList.add("active");
      const targetPane = $(btn.dataset.tab);
      if (targetPane) targetPane.classList.add("active");
    });
  });

  $("btn-re-analyze").addEventListener("click", () => executeFullAnalysis());
}

function initForecastControls() {
  $("btn-reforecast").addEventListener("click", async () => {
    if (!state.fileId) return;
    const target = $("forecast-metric").value;
    const periods = $("forecast-periods").value;

    const btn = $("btn-reforecast");
    btn.disabled = true;
    btn.textContent = "Computing...";

    const formData = new FormData();
    formData.append("file_id", state.fileId);
    formData.append("mapping", JSON.stringify(state.mapping));
    formData.append("target", target);
    formData.append("periods", periods);

    try {
      const res = await fetch(`${API_BASE}/api/predict`, { method: "POST", body: formData });
      const data = await res.json();
      if (!res.ok) throw new Error(data.message || "Forecast failed");
      renderForecast(data);
    } catch (err) {
      alert(err.message);
    } finally {
      btn.disabled = false;
      btn.textContent = "Run Forecast";
    }
  });
}

function initNewsControls() {
  document.querySelectorAll(".pill-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".pill-btn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      state.activeFilter = btn.dataset.filter;
      if (state.newsData) {
        renderArticles(state.newsData.articles || []);
      }
    });
  });

  $("btn-news-search").addEventListener("click", () => {
    const q = $("news-search-input").value.trim();
    if (q) fetchLiveNews(q);
  });

  $("news-search-input").addEventListener("keypress", (e) => {
    if (e.key === "Enter") {
      const q = $("news-search-input").value.trim();
      if (q) fetchLiveNews(q);
    }
  });
}

function initModalListeners() {
  const modal = $("key-modal");
  $("btn-open-key-modal").addEventListener("click", () => {
    $("input-typesafe-key").value = state.typesafeKey;
    modal.classList.remove("hidden");
  });

  $("btn-close-key-modal").addEventListener("click", () => modal.classList.add("hidden"));
  $("btn-cancel-key").addEventListener("click", () => modal.classList.add("hidden"));

  $("btn-save-key").addEventListener("click", () => {
    const key = $("input-typesafe-key").value.trim();
    state.typesafeKey = key;
    localStorage.setItem("nexus_typesafe_key", key);
    modal.classList.add("hidden");

    if (key) {
      $("api-key-btn-text").textContent = "TypeSafe (Connected)";
      $("btn-open-key-modal").classList.add("badge-emerald");
    } else {
      $("api-key-btn-text").textContent = "TypeSafe Jev";
      $("btn-open-key-modal").classList.remove("badge-emerald");
    }
  });
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
