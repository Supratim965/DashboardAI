import json
from pathlib import Path
import random

import numpy as np
import pandas as pd

OUTPUT_HTML = Path("ai_dashboard.html")
OUTPUT_SITE_DIR = Path("docs")
OUTPUT_SITE_HTML = OUTPUT_SITE_DIR / "index.html"
OUTPUT_NOJEKYLL = OUTPUT_SITE_DIR / ".nojekyll"
OUTPUT_DATA_DIR = Path("dashboard_exports")
OUTPUT_DATA_CSV = OUTPUT_DATA_DIR / "sales_performance_dataset.csv"

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def build_sales_dataframe():
    np.random.seed(42)
    random.seed(42)

    n = 1000
    regions = ["North", "South", "East", "West", "Central"]
    products = ["Laptop", "Phone", "Tablet", "Monitor", "Keyboard", "Mouse", "Headset", "Webcam", "Printer", "Router"]
    reps = ["Alice", "Bob", "Carol", "David", "Eva", "Frank", "Grace", "Henry", "Iris", "Jack"]
    categories = {
        "Laptop": "Electronics",
        "Phone": "Electronics",
        "Tablet": "Electronics",
        "Monitor": "Peripherals",
        "Keyboard": "Peripherals",
        "Mouse": "Peripherals",
        "Headset": "Peripherals",
        "Webcam": "Peripherals",
        "Printer": "Office",
        "Router": "Networking",
    }
    unit_prices = {
        "Laptop": 999,
        "Phone": 699,
        "Tablet": 499,
        "Monitor": 349,
        "Keyboard": 89,
        "Mouse": 49,
        "Headset": 149,
        "Webcam": 99,
        "Printer": 299,
        "Router": 129,
    }

    years = np.random.choice([2023, 2024, 2025], n)
    months = np.random.choice(MONTHS, n)
    regions_selected = np.random.choice(regions, n)
    products_selected = np.random.choice(products, n)
    reps_selected = np.random.choice(reps, n)
    units = np.random.randint(1, 50, n)
    prices = np.array([unit_prices[product] * np.random.uniform(0.85, 1.15) for product in products_selected]).round(2)
    sales = (units * prices).round(2)
    discounts = np.random.choice([0, 0, 0, 0.05, 0.1, 0.15], n)
    net_sales = (sales * (1 - discounts)).round(2)
    costs = (net_sales * np.random.uniform(0.45, 0.65, n)).round(2)
    profit = (net_sales - costs).round(2)
    margin = ((profit / net_sales) * 100).round(2)
    customer_types = np.random.choice(["Retail", "Corporate", "Government", "SMB"], n, p=[0.4, 0.35, 0.1, 0.15])
    satisfaction = np.random.choice([1, 2, 3, 4, 5], n, p=[0.05, 0.1, 0.2, 0.35, 0.3])

    return pd.DataFrame({
        "Year": years,
        "Month": months,
        "Region": regions_selected,
        "Sales Rep": reps_selected,
        "Product": products_selected,
        "Category": [categories[product] for product in products_selected],
        "Customer Type": customer_types,
        "Units Sold": units,
        "Unit Price ($)": prices,
        "Gross Sales ($)": sales,
        "Discount (%)": (discounts * 100).astype(int),
        "Net Sales ($)": net_sales,
        "Cost ($)": costs,
        "Profit ($)": profit,
        "Profit Margin (%)": margin,
        "Customer Satisfaction": satisfaction,
    })


def build_html(dataset_json):
    template = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Interactive Sales Command Center</title>
  <style>
    :root {
      --ink: #192227;
      --muted: #5f6d75;
      --teal: #0f766e;
      --teal-2: #34d399;
      --amber: #f59e0b;
      --red: #dc2626;
      --blue: #2563eb;
      --gold: #d6a54b;
      --paper: rgba(255, 251, 245, 0.84);
      --line: rgba(25, 34, 39, 0.12);
      --shadow: 0 26px 70px rgba(25, 34, 39, 0.15);
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "Trebuchet MS", "Segoe UI Variable Text", sans-serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, rgba(214, 165, 75, 0.20), transparent 26%),
        radial-gradient(circle at top right, rgba(15, 118, 110, 0.20), transparent 28%),
        linear-gradient(145deg, #f8f2e8 0%, #f3f4ef 55%, #e7f0ee 100%);
      min-height: 100vh;
    }
    .shell {
      max-width: 1320px;
      margin: 0 auto;
      padding: 32px 20px 64px;
    }
    .hero, .panel, .card, .filter-card {
      background: var(--paper);
      border: 1px solid rgba(255,255,255,0.82);
      border-radius: 28px;
      box-shadow: var(--shadow);
      backdrop-filter: blur(14px);
    }
    .hero {
      position: relative;
      overflow: hidden;
      padding: 32px;
    }
    .hero::after {
      content: "";
      position: absolute;
      width: 340px;
      height: 340px;
      right: -80px;
      bottom: -140px;
      border-radius: 999px;
      background: radial-gradient(circle, rgba(214, 165, 75, 0.22), rgba(214, 165, 75, 0.02));
    }
    h1, h2, h3 {
      margin: 0;
      font-family: "Palatino Linotype", "Book Antiqua", Georgia, serif;
    }
    h1 {
      font-size: clamp(2.4rem, 4vw, 4.25rem);
      line-height: 0.92;
      max-width: 11ch;
    }
    h2 {
      font-size: 1.7rem;
      margin-bottom: 6px;
    }
    h3 {
      font-size: 1.18rem;
      margin-bottom: 12px;
    }
    .eyebrow {
      color: var(--muted);
      font-size: 0.78rem;
      letter-spacing: 0.14em;
      text-transform: uppercase;
    }
    .hero-copy, .panel-copy {
      color: var(--muted);
      line-height: 1.65;
    }
    .hero-copy {
      max-width: 64ch;
      margin: 16px 0 0;
    }
    .filters {
      display: grid;
      grid-template-columns: repeat(6, minmax(0, 1fr));
      gap: 14px;
      margin-top: 22px;
    }
    .filter-card {
      padding: 14px;
      border-radius: 20px;
    }
    .filter-card label {
      display: block;
      margin-bottom: 8px;
      color: var(--muted);
      font-size: 0.78rem;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }
    .filter-card select,
    .filter-card input,
    .filter-card button {
      width: 100%;
      border: 1px solid rgba(25, 34, 39, 0.12);
      border-radius: 14px;
      padding: 10px 12px;
      background: rgba(255,255,255,0.74);
      color: var(--ink);
      font: inherit;
    }
    .filter-card button {
      cursor: pointer;
      background: linear-gradient(135deg, #0f766e, #0d9488);
      border: 0;
      color: #fff;
      font-weight: 700;
      margin-top: 22px;
    }
    .active-summary {
      margin-top: 16px;
      color: var(--muted);
      font-size: 0.95rem;
    }
    .kpis {
      display: grid;
      grid-template-columns: repeat(6, minmax(0, 1fr));
      gap: 16px;
      margin-top: 24px;
    }
    .card {
      padding: 18px 18px 16px;
    }
    .metric {
      margin-top: 8px;
      font-size: 1.95rem;
      font-weight: 700;
    }
    .metric-note {
      margin-top: 6px;
      color: var(--muted);
      font-size: 0.92rem;
    }
    .grid {
      display: grid;
      gap: 18px;
      margin-top: 22px;
    }
    .grid.two {
      grid-template-columns: 1.2fr 0.8fr;
    }
    .grid.three {
      grid-template-columns: repeat(3, minmax(0, 1fr));
    }
    .panel {
      padding: 22px;
    }
    .chart {
      width: 100%;
      height: auto;
      display: block;
    }
    .chart .grid-line {
      stroke: rgba(25, 34, 39, 0.10);
      stroke-width: 1;
    }
    .chart .grid-label,
    .chart .axis-label,
    .chart .bar-label {
      fill: var(--muted);
      font-size: 11px;
    }
    .chart .value-label,
    .chart .bar-value {
      fill: var(--ink);
      font-size: 11px;
      font-weight: 700;
    }
    .donut-wrap {
      display: grid;
      gap: 18px;
      align-items: center;
      justify-items: center;
    }
    .donut-chart {
      width: min(300px, 72vw);
      aspect-ratio: 1;
      border-radius: 50%;
      display: grid;
      place-items: center;
      box-shadow: inset 0 0 0 1px rgba(255,255,255,0.35);
    }
    .donut-hole {
      width: 56%;
      aspect-ratio: 1;
      border-radius: 50%;
      background: rgba(255, 251, 245, 0.96);
      display: grid;
      place-items: center;
      text-align: center;
      box-shadow: inset 0 0 0 1px rgba(25, 34, 39, 0.08);
    }
    .donut-hole span {
      color: var(--muted);
      font-size: 0.82rem;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }
    .donut-hole strong {
      font-size: 1.65rem;
      line-height: 1;
    }
    .legend {
      width: 100%;
      display: grid;
      gap: 10px;
    }
    .legend-item {
      display: grid;
      grid-template-columns: 14px 1fr auto;
      gap: 10px;
      align-items: center;
      padding: 10px 12px;
      border-radius: 14px;
      background: rgba(255,255,255,0.56);
      border: 1px solid rgba(25, 34, 39, 0.07);
    }
    .legend-swatch {
      width: 14px;
      height: 14px;
      border-radius: 999px;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 10px;
      font-size: 0.95rem;
    }
    th, td {
      padding: 12px 14px;
      border-bottom: 1px solid var(--line);
      text-align: left;
      vertical-align: top;
    }
    th {
      background: rgba(15, 118, 110, 0.08);
      color: var(--muted);
      font-size: 0.82rem;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }
    .empty-state {
      padding: 36px 18px;
      text-align: center;
      color: var(--muted);
    }
    .footer-note {
      margin-top: 14px;
      color: var(--muted);
      font-size: 0.92rem;
    }
    @media (max-width: 1180px) {
      .filters,
      .kpis {
        grid-template-columns: repeat(3, minmax(0, 1fr));
      }
    }
    @media (max-width: 920px) {
      .grid.two,
      .grid.three,
      .filters,
      .kpis {
        grid-template-columns: 1fr;
      }
      .hero {
        padding: 24px;
      }
    }
  </style>
</head>
<body>
  <div class="shell">
    <section class="hero">
      <div class="eyebrow">Interactive Sales Command Center</div>
      <h1>Filter, slice, and interrogate sales performance live</h1>
      <p class="hero-copy">This dashboard runs entirely in your browser from the embedded dataframe. Change the filters and every KPI, chart, and table will recalculate instantly.</p>

      <div class="filters">
        <div class="filter-card">
          <label for="yearFilter">Year</label>
          <select id="yearFilter"></select>
        </div>
        <div class="filter-card">
          <label for="regionFilter">Region</label>
          <select id="regionFilter"></select>
        </div>
        <div class="filter-card">
          <label for="categoryFilter">Category</label>
          <select id="categoryFilter"></select>
        </div>
        <div class="filter-card">
          <label for="customerTypeFilter">Customer Type</label>
          <select id="customerTypeFilter"></select>
        </div>
        <div class="filter-card">
          <label for="monthFilter">Month</label>
          <select id="monthFilter"></select>
        </div>
        <div class="filter-card">
          <label for="searchFilter">Search Product / Rep</label>
          <input id="searchFilter" type="text" placeholder="Phone, Alice, Router..." />
        </div>
      </div>
      <div class="filters" style="grid-template-columns: 180px;">
        <div class="filter-card">
          <button id="resetFilters">Reset Filters</button>
        </div>
      </div>
      <div id="activeSummary" class="active-summary"></div>

      <div class="kpis">
        <div class="card"><div class="eyebrow">Net Sales</div><div id="kpiNetSales" class="metric"></div><div id="kpiNetSalesNote" class="metric-note"></div></div>
        <div class="card"><div class="eyebrow">Profit</div><div id="kpiProfit" class="metric"></div><div id="kpiProfitNote" class="metric-note"></div></div>
        <div class="card"><div class="eyebrow">Units Sold</div><div id="kpiUnits" class="metric"></div><div id="kpiUnitsNote" class="metric-note"></div></div>
        <div class="card"><div class="eyebrow">Avg Margin</div><div id="kpiMargin" class="metric"></div><div id="kpiMarginNote" class="metric-note"></div></div>
        <div class="card"><div class="eyebrow">Satisfaction</div><div id="kpiSatisfaction" class="metric"></div><div id="kpiSatisfactionNote" class="metric-note"></div></div>
        <div class="card"><div class="eyebrow">Orders</div><div id="kpiOrders" class="metric"></div><div id="kpiOrdersNote" class="metric-note"></div></div>
      </div>
    </section>

    <section class="grid two">
      <article class="panel">
        <h2>Net Sales Trend</h2>
        <p class="panel-copy">Monthly momentum updates based on the current filter state.</p>
        <div id="trendChart"></div>
      </article>
      <article class="panel">
        <h2>Revenue Mix by Category</h2>
        <p class="panel-copy">Where revenue is concentrated after filters are applied.</p>
        <div id="categoryDonut"></div>
      </article>
    </section>

    <section class="grid three">
      <article class="panel">
        <h2>Regional Profit</h2>
        <p class="panel-copy">Profit pool allocation across regions.</p>
        <div id="regionProfitChart"></div>
      </article>
      <article class="panel">
        <h2>Top Sales Reps</h2>
        <p class="panel-copy">Leading reps by filtered net sales.</p>
        <div id="repChart"></div>
      </article>
      <article class="panel">
        <h2>Customer Satisfaction</h2>
        <p class="panel-copy">Average score by customer type.</p>
        <div id="satisfactionChart"></div>
      </article>
    </section>

    <section class="grid two">
      <article class="panel">
        <h2>Top Products</h2>
        <p class="panel-copy">Best commercial performers under the current filters.</p>
        <div id="topProductsTable"></div>
      </article>
      <article class="panel">
        <h2>Yearly Summary</h2>
        <p class="panel-copy">Rollup metrics by year for the selected slice.</p>
        <div id="yearSummaryTable"></div>
        <div class="footer-note">The dashboard is self-contained and mirrored to <code>docs/index.html</code> for GitHub Pages.</div>
      </article>
    </section>
  </div>

  <script>
    const rawData = __DATASET__;
    const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
    const monthOrder = Object.fromEntries(months.map((month, index) => [month, index]));
    const palette = ["#0f766e", "#f59e0b", "#dc2626", "#2563eb", "#7c3aed", "#16a34a", "#ea580c", "#0891b2"];

    const controls = {
      year: document.getElementById("yearFilter"),
      region: document.getElementById("regionFilter"),
      category: document.getElementById("categoryFilter"),
      customerType: document.getElementById("customerTypeFilter"),
      month: document.getElementById("monthFilter"),
      search: document.getElementById("searchFilter"),
      reset: document.getElementById("resetFilters")
    };

    function formatCurrency(value) {
      return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(value || 0);
    }

    function formatNumber(value) {
      return new Intl.NumberFormat("en-US", { maximumFractionDigits: 2 }).format(value || 0);
    }

    function formatPercent(value) {
      return `${formatNumber(value)}%`;
    }

    function groupBy(items, keyFn, valueFn) {
      const map = new Map();
      for (const item of items) {
        const key = keyFn(item);
        const current = map.get(key) || 0;
        map.set(key, current + valueFn(item));
      }
      return map;
    }

    function escapeHtml(value) {
      return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#39;");
    }

    function optionValues(field) {
      const values = [...new Set(rawData.map(row => row[field]))];
      if (field === "Month") {
        return values.sort((a, b) => monthOrder[a] - monthOrder[b]);
      }
      return values.sort();
    }

    function fillSelect(select, values) {
      select.innerHTML = `<option value="All">All</option>` + values.map(value => `<option value="${escapeHtml(value)}">${escapeHtml(value)}</option>`).join("");
    }

    function initializeControls() {
      fillSelect(controls.year, optionValues("Year"));
      fillSelect(controls.region, optionValues("Region"));
      fillSelect(controls.category, optionValues("Category"));
      fillSelect(controls.customerType, optionValues("Customer Type"));
      fillSelect(controls.month, months);

      Object.values(controls).forEach(control => {
        if (control && control.tagName !== "BUTTON") {
          control.addEventListener("input", renderDashboard);
          control.addEventListener("change", renderDashboard);
        }
      });

      controls.reset.addEventListener("click", () => {
        controls.year.value = "All";
        controls.region.value = "All";
        controls.category.value = "All";
        controls.customerType.value = "All";
        controls.month.value = "All";
        controls.search.value = "";
        renderDashboard();
      });
    }

    function getFilteredData() {
      const search = controls.search.value.trim().toLowerCase();
      return rawData.filter(row => {
        if (controls.year.value !== "All" && String(row["Year"]) !== controls.year.value) return false;
        if (controls.region.value !== "All" && row["Region"] !== controls.region.value) return false;
        if (controls.category.value !== "All" && row["Category"] !== controls.category.value) return false;
        if (controls.customerType.value !== "All" && row["Customer Type"] !== controls.customerType.value) return false;
        if (controls.month.value !== "All" && row["Month"] !== controls.month.value) return false;
        if (search) {
          const haystack = `${row["Product"]} ${row["Sales Rep"]}`.toLowerCase();
          if (!haystack.includes(search)) return false;
        }
        return true;
      });
    }

    function setActiveSummary(rows) {
      const filters = [];
      [["Year", controls.year.value], ["Region", controls.region.value], ["Category", controls.category.value], ["Customer Type", controls.customerType.value], ["Month", controls.month.value]].forEach(([label, value]) => {
        if (value !== "All") filters.push(`${label}: ${value}`);
      });
      if (controls.search.value.trim()) filters.push(`Search: ${controls.search.value.trim()}`);
      const filterText = filters.length ? filters.join(" | ") : "No filters applied";
      document.getElementById("activeSummary").textContent = `${rows.length.toLocaleString()} orders in view. ${filterText}.`;
    }

    function updateKpis(rows) {
      const netSales = rows.reduce((sum, row) => sum + row["Net Sales ($)"], 0);
      const profit = rows.reduce((sum, row) => sum + row["Profit ($)"], 0);
      const units = rows.reduce((sum, row) => sum + row["Units Sold"], 0);
      const avgMargin = rows.length ? rows.reduce((sum, row) => sum + row["Profit Margin (%)"], 0) / rows.length : 0;
      const avgSatisfaction = rows.length ? rows.reduce((sum, row) => sum + row["Customer Satisfaction"], 0) / rows.length : 0;
      const avgOrderValue = rows.length ? netSales / rows.length : 0;

      document.getElementById("kpiNetSales").textContent = formatCurrency(netSales);
      document.getElementById("kpiNetSalesNote").textContent = `${formatCurrency(avgOrderValue)} average order value`;
      document.getElementById("kpiProfit").textContent = formatCurrency(profit);
      document.getElementById("kpiProfitNote").textContent = `${formatPercent(netSales ? (profit / netSales) * 100 : 0)} of net sales`;
      document.getElementById("kpiUnits").textContent = formatNumber(units);
      document.getElementById("kpiUnitsNote").textContent = rows.length ? `${formatNumber(units / rows.length)} units per order` : "No rows selected";
      document.getElementById("kpiMargin").textContent = formatPercent(avgMargin);
      document.getElementById("kpiMarginNote").textContent = "Average filtered margin";
      document.getElementById("kpiSatisfaction").textContent = `${formatNumber(avgSatisfaction)}/5`;
      document.getElementById("kpiSatisfactionNote").textContent = "Average customer score";
      document.getElementById("kpiOrders").textContent = formatNumber(rows.length);
      document.getElementById("kpiOrdersNote").textContent = `${formatNumber(new Set(rows.map(row => row["Sales Rep"])).size)} reps represented`;
    }

    function emptyMarkup(message) {
      return `<div class="empty-state">${escapeHtml(message)}</div>`;
    }

    function renderLineChart(containerId, title, points) {
      const container = document.getElementById(containerId);
      if (!points.length) {
        container.innerHTML = emptyMarkup("No trend data for the current filter selection.");
        return;
      }

      const width = 640;
      const height = 320;
      const left = 60;
      const right = 24;
      const top = 24;
      const bottom = 46;
      const innerWidth = width - left - right;
      const innerHeight = height - top - bottom;
      const maxValue = Math.max(...points.map(point => point.value), 1);

      const grid = [];
      for (let i = 0; i < 5; i += 1) {
        const tick = maxValue * i / 4;
        const y = top + innerHeight - (tick / maxValue) * innerHeight;
        grid.push(`<line class="grid-line" x1="${left}" y1="${y.toFixed(1)}" x2="${width - right}" y2="${y.toFixed(1)}"></line>`);
        grid.push(`<text class="grid-label" x="${left - 10}" y="${(y + 4).toFixed(1)}" text-anchor="end">${escapeHtml(formatCurrency(tick))}</text>`);
      }

      const coords = points.map((point, index) => {
        const x = left + (innerWidth / Math.max(points.length - 1, 1)) * index;
        const y = top + innerHeight - (point.value / maxValue) * innerHeight;
        return { ...point, x, y };
      });

      const linePath = coords.map((point, index) => `${index === 0 ? "M" : "L"} ${point.x.toFixed(1)} ${point.y.toFixed(1)}`).join(" ");
      const areaPath = `${linePath} L ${coords[coords.length - 1].x.toFixed(1)} ${(top + innerHeight).toFixed(1)} L ${coords[0].x.toFixed(1)} ${(top + innerHeight).toFixed(1)} Z`;
      const circles = coords.map(point => `<circle cx="${point.x.toFixed(1)}" cy="${point.y.toFixed(1)}" r="5" fill="#fff" stroke="#0f766e" stroke-width="3"></circle>`).join("");
      const axis = coords.map(point => `<text class="axis-label" x="${point.x.toFixed(1)}" y="${height - 16}" text-anchor="middle">${escapeHtml(point.label)}</text>`).join("");
      const values = coords.map(point => `<text class="value-label" x="${point.x.toFixed(1)}" y="${Math.max(point.y - 12, 14).toFixed(1)}" text-anchor="middle">${escapeHtml(formatCurrency(point.value))}</text>`).join("");

      container.innerHTML = `
        <svg viewBox="0 0 ${width} ${height}" class="chart" role="img" aria-label="${escapeHtml(title)}">
          <g>${grid.join("")}</g>
          <path d="${areaPath}" fill="rgba(15, 118, 110, 0.14)"></path>
          <path d="${linePath}" fill="none" stroke="#0f766e" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"></path>
          <g>${circles}</g>
          <g>${values}</g>
          <g>${axis}</g>
        </svg>
      `;
    }

    function renderBarChart(containerId, items, formatter) {
      const container = document.getElementById(containerId);
      if (!items.length) {
        container.innerHTML = emptyMarkup("No grouped data for the current filter selection.");
        return;
      }

      const width = 520;
      const rowHeight = 52;
      const height = 56 + items.length * rowHeight;
      const left = 150;
      const right = 28;
      const maxValue = Math.max(...items.map(item => item.value), 1);

      const rows = items.map((item, index) => {
        const y = 26 + index * rowHeight;
        const barWidth = (item.value / maxValue) * (width - left - right);
        const color = palette[index % palette.length];
        return `
          <text class="bar-label" x="12" y="${(y + 16).toFixed(1)}">${escapeHtml(item.label)}</text>
          <rect x="${left}" y="${y.toFixed(1)}" width="${barWidth.toFixed(1)}" height="24" rx="12" fill="${color}"></rect>
          <text class="bar-value" x="${(left + barWidth + 10).toFixed(1)}" y="${(y + 16).toFixed(1)}">${escapeHtml(formatter(item.value))}</text>
        `;
      }).join("");

      container.innerHTML = `<svg viewBox="0 0 ${width} ${height}" class="chart">${rows}</svg>`;
    }

    function renderDonut(containerId, items) {
      const container = document.getElementById(containerId);
      if (!items.length) {
        container.innerHTML = emptyMarkup("No category mix data for the current filter selection.");
        return;
      }

      const total = items.reduce((sum, item) => sum + item.value, 0) || 1;
      let cursor = 0;
      const segments = [];
      const legend = [];
      items.forEach((item, index) => {
        const share = item.value / total;
        const next = cursor + share * 100;
        const color = palette[index % palette.length];
        segments.push(`${color} ${cursor.toFixed(2)}% ${next.toFixed(2)}%`);
        legend.push(`
          <div class="legend-item">
            <span class="legend-swatch" style="background:${color}"></span>
            <span>${escapeHtml(item.label)}</span>
            <strong>${escapeHtml(formatNumber(share * 100))}%</strong>
          </div>
        `);
        cursor = next;
      });

      container.innerHTML = `
        <div class="donut-wrap">
          <div class="donut-chart" style="background: conic-gradient(${segments.join(", ")});">
            <div class="donut-hole">
              <span>Total</span>
              <strong>${escapeHtml(formatCurrency(total))}</strong>
            </div>
          </div>
          <div class="legend">${legend.join("")}</div>
        </div>
      `;
    }

    function renderTable(containerId, headers, rows) {
      const container = document.getElementById(containerId);
      if (!rows.length) {
        container.innerHTML = emptyMarkup("No rows to display for the current filter selection.");
        return;
      }

      const head = headers.map(header => `<th>${escapeHtml(header)}</th>`).join("");
      const body = rows.map(row => `<tr>${row.map(cell => `<td>${escapeHtml(cell)}</td>`).join("")}</tr>`).join("");
      container.innerHTML = `<table><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table>`;
    }

    function aggregateTrend(rows) {
      const grouped = groupBy(rows, row => `${row["Year"]}-${row["Month"]}`, row => row["Net Sales ($)"]);
      return [...grouped.entries()]
        .map(([key, value]) => {
          const [year, month] = key.split("-");
          return { year: Number(year), month, label: `${year} ${month}`, value };
        })
        .sort((a, b) => a.year - b.year || monthOrder[a.month] - monthOrder[b.month]);
    }

    function aggregateBar(rows, key, metric, limit = 6) {
      const grouped = groupBy(rows, row => row[key], row => row[metric]);
      return [...grouped.entries()]
        .map(([label, value]) => ({ label, value }))
        .sort((a, b) => b.value - a.value)
        .slice(0, limit);
    }

    function aggregateAverage(rows, key, metric, limit = 6) {
      const grouped = new Map();
      rows.forEach(row => {
        const current = grouped.get(row[key]) || { total: 0, count: 0 };
        current.total += row[metric];
        current.count += 1;
        grouped.set(row[key], current);
      });
      return [...grouped.entries()]
        .map(([label, value]) => ({ label, value: value.count ? value.total / value.count : 0 }))
        .sort((a, b) => b.value - a.value)
        .slice(0, limit);
    }

    function buildTopProducts(rows) {
      const grouped = new Map();
      rows.forEach(row => {
        const key = `${row["Product"]}__${row["Category"]}`;
        const current = grouped.get(key) || { product: row["Product"], category: row["Category"], netSales: 0, profit: 0, units: 0 };
        current.netSales += row["Net Sales ($)"];
        current.profit += row["Profit ($)"];
        current.units += row["Units Sold"];
        grouped.set(key, current);
      });
      return [...grouped.values()]
        .sort((a, b) => b.netSales - a.netSales)
        .slice(0, 8)
        .map(item => [
          item.product,
          item.category,
          formatCurrency(item.netSales),
          formatCurrency(item.profit),
          formatNumber(item.units)
        ]);
    }

    function buildYearSummary(rows) {
      const grouped = new Map();
      rows.forEach(row => {
        const current = grouped.get(row["Year"]) || { year: row["Year"], netSales: 0, profit: 0, units: 0, satisfaction: 0, count: 0 };
        current.netSales += row["Net Sales ($)"];
        current.profit += row["Profit ($)"];
        current.units += row["Units Sold"];
        current.satisfaction += row["Customer Satisfaction"];
        current.count += 1;
        grouped.set(row["Year"], current);
      });
      return [...grouped.values()]
        .sort((a, b) => a.year - b.year)
        .map(item => [
          item.year,
          formatCurrency(item.netSales),
          formatCurrency(item.profit),
          formatNumber(item.units),
          `${formatNumber(item.count ? item.satisfaction / item.count : 0)}/5`
        ]);
    }

    function renderDashboard() {
      const rows = getFilteredData();
      setActiveSummary(rows);
      updateKpis(rows);

      renderLineChart("trendChart", "Net Sales Trend", aggregateTrend(rows));
      renderDonut("categoryDonut", aggregateBar(rows, "Category", "Net Sales ($)", 6));
      renderBarChart("regionProfitChart", aggregateBar(rows, "Region", "Profit ($)", 5), formatCurrency);
      renderBarChart("repChart", aggregateBar(rows, "Sales Rep", "Net Sales ($)", 6), formatCurrency);
      renderBarChart("satisfactionChart", aggregateAverage(rows, "Customer Type", "Customer Satisfaction", 4), value => `${formatNumber(value)}/5`);
      renderTable("topProductsTable", ["Product", "Category", "Net Sales", "Profit", "Units Sold"], buildTopProducts(rows));
      renderTable("yearSummaryTable", ["Year", "Net Sales", "Profit", "Units Sold", "Avg Satisfaction"], buildYearSummary(rows));
    }

    initializeControls();
    renderDashboard();
  </script>
</body>
</html>
"""
    return template.replace("__DATASET__", dataset_json)


df = build_sales_dataframe()
records = json.dumps(df.to_dict(orient="records"), separators=(",", ":"))
html_output = build_html(records)

OUTPUT_DATA_DIR.mkdir(exist_ok=True)
df.to_csv(OUTPUT_DATA_CSV, index=False)
OUTPUT_HTML.write_text(html_output, encoding="utf-8")
OUTPUT_SITE_DIR.mkdir(exist_ok=True)
OUTPUT_SITE_HTML.write_text(html_output, encoding="utf-8")
OUTPUT_NOJEKYLL.write_text("", encoding="utf-8")

print(f"Dataset generated: {len(df):,} rows x {len(df.columns)} columns")
print(f"Interactive HTML dashboard saved: {OUTPUT_HTML.resolve()}")
print(f"Shareable site entry saved: {OUTPUT_SITE_HTML.resolve()}")
print(f"Dataset CSV saved: {OUTPUT_DATA_CSV.resolve()}")
