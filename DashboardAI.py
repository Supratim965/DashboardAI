import html
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
OUTPUT_REP_CSV = OUTPUT_DATA_DIR / "top_sales_reps.csv"
OUTPUT_YEAR_CSV = OUTPUT_DATA_DIR / "yearly_summary.csv"

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
MONTH_ORDER = {month: index for index, month in enumerate(MONTHS, start=1)}
PALETTE = ["#0f766e", "#f59e0b", "#dc2626", "#2563eb", "#7c3aed", "#16a34a", "#ea580c", "#0891b2"]


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


def format_currency(value):
    return f"${value:,.0f}"


def format_number(value):
    if isinstance(value, float):
        if value.is_integer():
            return f"{int(value):,}"
        return f"{value:,.2f}"
    return f"{value:,}"


def build_line_chart(title, labels, values):
    width = 640
    height = 320
    left = 60
    right = 24
    top = 24
    bottom = 46
    inner_width = width - left - right
    inner_height = height - top - bottom
    max_value = max(max(values), 1.0)

    points = []
    label_nodes = []
    grid_nodes = []
    value_nodes = []
    for step in range(5):
        tick_value = max_value * step / 4
        y = top + inner_height - (tick_value / max_value) * inner_height
        grid_nodes.append(
            f'<line x1="{left}" y1="{y:.1f}" x2="{width - right}" y2="{y:.1f}" />'
            f'<text x="{left - 10}" y="{y + 4:.1f}">{html.escape(format_currency(tick_value))}</text>'
        )

    for index, (label, value) in enumerate(zip(labels, values)):
        x = left + (inner_width / max(len(values) - 1, 1)) * index
        y = top + inner_height - (value / max_value) * inner_height
        points.append((x, y))
        label_nodes.append(f'<text x="{x:.1f}" y="{height - 16}" class="axis-label">{html.escape(str(label))}</text>')
        value_nodes.append(f'<text x="{x:.1f}" y="{max(y - 12, 14):.1f}" class="value-label">{html.escape(format_currency(value))}</text>')

    path = " ".join(f"{'M' if index == 0 else 'L'} {x:.1f} {y:.1f}" for index, (x, y) in enumerate(points))
    area = path + f" L {points[-1][0]:.1f} {top + inner_height:.1f} L {points[0][0]:.1f} {top + inner_height:.1f} Z"
    circles = "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" />' for x, y in points)

    return f"""
    <article class="panel">
      <h3>{html.escape(title)}</h3>
      <svg viewBox="0 0 {width} {height}" class="chart" role="img" aria-label="{html.escape(title)}">
        <defs>
          <linearGradient id="trendArea" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="rgba(15, 118, 110, 0.38)" />
            <stop offset="100%" stop-color="rgba(15, 118, 110, 0.02)" />
          </linearGradient>
        </defs>
        <g class="grid">{''.join(grid_nodes)}</g>
        <path d="{area}" fill="rgba(15, 118, 110, 0.14)"></path>
        <path d="{path}" fill="none" stroke="#0f766e" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"></path>
        <g class="line-points">{circles}</g>
        <g class="value-labels">{''.join(value_nodes)}</g>
        <g class="labels">{''.join(label_nodes)}</g>
      </svg>
    </article>
    """


def build_horizontal_bar_chart(title, labels, values, formatter):
    width = 520
    row_height = 52
    height = 56 + len(values) * row_height
    left = 148
    right = 28
    bar_height = 24
    max_value = max(max(values), 1.0)

    bars = []
    for index, (label, value) in enumerate(zip(labels, values)):
        y = 26 + index * row_height
        bar_width = (value / max_value) * (width - left - right)
        color = PALETTE[index % len(PALETTE)]
        bars.append(
            f'<text x="12" y="{y + 16:.1f}" class="bar-label">{html.escape(str(label))}</text>'
            f'<rect x="{left}" y="{y:.1f}" width="{bar_width:.1f}" height="{bar_height}" rx="12" fill="{color}" />'
            f'<text x="{left + bar_width + 10:.1f}" y="{y + 16:.1f}" class="bar-value">{html.escape(formatter(value))}</text>'
        )

    return f"""
    <article class="panel">
      <h3>{html.escape(title)}</h3>
      <svg viewBox="0 0 {width} {height}" class="chart" role="img" aria-label="{html.escape(title)}">
        {''.join(bars)}
      </svg>
    </article>
    """


def build_donut_chart(title, labels, values):
    total = float(sum(values)) or 1.0
    cursor = 0.0
    segments = []
    legend_items = []
    for index, (label, value) in enumerate(zip(labels, values)):
        share = float(value) / total
        next_cursor = cursor + share * 100
        color = PALETTE[index % len(PALETTE)]
        segments.append(f"{color} {cursor:.2f}% {next_cursor:.2f}%")
        legend_items.append(
            "<div class=\"legend-item\">"
            f"<span class=\"legend-swatch\" style=\"background:{color}\"></span>"
            f"<span>{html.escape(str(label))}</span>"
            f"<strong>{share * 100:.1f}%</strong>"
            "</div>"
        )
        cursor = next_cursor

    return f"""
    <article class="panel">
      <h3>{html.escape(title)}</h3>
      <div class="donut-wrap">
        <div class="donut-chart" style="background: conic-gradient({', '.join(segments)});">
          <div class="donut-hole">
            <span>Total</span>
            <strong>{html.escape(format_currency(total))}</strong>
          </div>
        </div>
        <div class="legend">{''.join(legend_items)}</div>
      </div>
    </article>
    """


def build_table(headers, rows):
    header_html = "".join(f"<th>{html.escape(str(header))}</th>" for header in headers)
    body_rows = []
    for row in rows:
        cells = "".join(f"<td>{html.escape(str(cell))}</td>" for cell in row)
        body_rows.append(f"<tr>{cells}</tr>")
    return (
        "<table><thead><tr>"
        + header_html
        + "</tr></thead><tbody>"
        + "".join(body_rows)
        + "</tbody></table>"
    )


def render_dashboard(df):
    df = df.copy()
    df["Month Order"] = df["Month"].map(MONTH_ORDER)
    df["Period"] = df["Year"].astype(str) + "-" + df["Month"]

    monthly_sales = (
        df.groupby(["Year", "Month", "Month Order"], as_index=False)["Net Sales ($)"]
        .sum()
        .sort_values(["Year", "Month Order"])
    )
    trend_labels = (monthly_sales["Year"].astype(str) + " " + monthly_sales["Month"]).tolist()
    trend_values = monthly_sales["Net Sales ($)"].tolist()

    category_share = (
        df.groupby("Category", as_index=False)["Net Sales ($)"]
        .sum()
        .sort_values("Net Sales ($)", ascending=False)
    )
    region_profit = (
        df.groupby("Region", as_index=False)["Profit ($)"]
        .sum()
        .sort_values("Profit ($)", ascending=False)
    )
    customer_satisfaction = (
        df.groupby("Customer Type", as_index=False)["Customer Satisfaction"]
        .mean()
        .sort_values("Customer Satisfaction", ascending=False)
    )
    top_reps = (
        df.groupby("Sales Rep", as_index=False)
        .agg({
            "Net Sales ($)": "sum",
            "Profit ($)": "sum",
            "Units Sold": "sum",
        })
        .sort_values("Net Sales ($)", ascending=False)
        .head(6)
    )
    yearly_summary = (
        df.groupby("Year", as_index=False)
        .agg({
            "Net Sales ($)": "sum",
            "Profit ($)": "sum",
            "Units Sold": "sum",
            "Customer Satisfaction": "mean",
        })
        .sort_values("Year")
    )
    top_products = (
        df.groupby(["Product", "Category"], as_index=False)
        .agg({
            "Net Sales ($)": "sum",
            "Profit ($)": "sum",
            "Units Sold": "sum",
        })
        .sort_values("Net Sales ($)", ascending=False)
        .head(8)
    )

    total_net_sales = float(df["Net Sales ($)"].sum())
    total_profit = float(df["Profit ($)"].sum())
    total_units = int(df["Units Sold"].sum())
    avg_margin = float(df["Profit Margin (%)"].mean())
    avg_satisfaction = float(df["Customer Satisfaction"].mean())
    best_region = region_profit.iloc[0]

    hero_cards = [
        ("Net Sales", format_currency(total_net_sales), "After discounts across all orders"),
        ("Profit", format_currency(total_profit), f"{(total_profit / total_net_sales) * 100:.1f}% of net sales"),
        ("Units Sold", format_number(total_units), "Total units moved"),
        ("Avg Margin", f"{avg_margin:.1f}%", "Average profit margin"),
        ("Satisfaction", f"{avg_satisfaction:.2f}/5", "Average customer rating"),
        ("Top Region", str(best_region["Region"]), f"{format_currency(float(best_region['Profit ($)']))} profit"),
    ]
    hero_cards_html = "".join(
        "<div class=\"card\">"
        f"<div class=\"eyebrow\">{html.escape(label)}</div>"
        f"<div class=\"metric\">{html.escape(value)}</div>"
        f"<div class=\"metric-note\">{html.escape(note)}</div>"
        "</div>"
        for label, value, note in hero_cards
    )

    top_rep_rows = [
        [
            row["Sales Rep"],
            format_currency(float(row["Net Sales ($)"])),
            format_currency(float(row["Profit ($)"])),
            format_number(int(row["Units Sold"])),
        ]
        for _, row in top_reps.iterrows()
    ]
    year_rows = [
        [
            int(row["Year"]),
            format_currency(float(row["Net Sales ($)"])),
            format_currency(float(row["Profit ($)"])),
            format_number(int(row["Units Sold"])),
            f"{float(row['Customer Satisfaction']):.2f}/5",
        ]
        for _, row in yearly_summary.iterrows()
    ]
    product_rows = [
        [
            row["Product"],
            row["Category"],
            format_currency(float(row["Net Sales ($)"])),
            format_currency(float(row["Profit ($)"])),
            format_number(int(row["Units Sold"])),
        ]
        for _, row in top_products.iterrows()
    ]

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Executive Sales Command Center</title>
  <style>
    :root {{
      --ink: #182126;
      --muted: #5d6a72;
      --gold: #d6a54b;
      --teal: #0f766e;
      --amber: #f59e0b;
      --cream: #f8f2e8;
      --panel: rgba(255, 251, 245, 0.84);
      --line: rgba(24, 33, 38, 0.12);
      --shadow: 0 26px 70px rgba(24, 33, 38, 0.16);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Trebuchet MS", "Segoe UI Variable Text", sans-serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, rgba(214, 165, 75, 0.22), transparent 28%),
        radial-gradient(circle at top right, rgba(15, 118, 110, 0.22), transparent 30%),
        linear-gradient(145deg, #f8f2e8 0%, #f3f4ef 56%, #e8f0ee 100%);
      min-height: 100vh;
    }}
    .shell {{
      max-width: 1280px;
      margin: 0 auto;
      padding: 34px 20px 60px;
    }}
    .hero, .panel, .card {{
      background: var(--panel);
      border: 1px solid rgba(255,255,255,0.82);
      border-radius: 28px;
      box-shadow: var(--shadow);
      backdrop-filter: blur(14px);
    }}
    .hero {{
      position: relative;
      overflow: hidden;
      padding: 34px;
    }}
    .hero::after {{
      content: "";
      position: absolute;
      width: 320px;
      height: 320px;
      right: -70px;
      bottom: -120px;
      border-radius: 999px;
      background: radial-gradient(circle, rgba(214, 165, 75, 0.24), rgba(214, 165, 75, 0.02));
    }}
    h1, h2, h3 {{
      margin: 0;
      font-family: "Palatino Linotype", "Book Antiqua", Georgia, serif;
    }}
    h1 {{
      font-size: clamp(2.4rem, 4vw, 4.2rem);
      line-height: 0.92;
      max-width: 11ch;
    }}
    h2 {{
      font-size: 1.9rem;
    }}
    h3 {{
      font-size: 1.24rem;
      margin-bottom: 12px;
    }}
    .eyebrow {{
      color: var(--muted);
      font-size: 0.78rem;
      letter-spacing: 0.14em;
      text-transform: uppercase;
    }}
    .hero-copy, .panel-copy {{
      max-width: 64ch;
      margin: 16px 0 0;
      color: var(--muted);
      line-height: 1.65;
    }}
    .kpis {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 16px;
      margin-top: 24px;
    }}
    .card {{
      padding: 18px 18px 16px;
    }}
    .metric {{
      margin-top: 8px;
      font-size: 1.9rem;
      font-weight: 700;
    }}
    .metric-note {{
      margin-top: 6px;
      color: var(--muted);
      font-size: 0.92rem;
    }}
    .grid {{
      display: grid;
      grid-template-columns: 1.25fr 0.95fr;
      gap: 18px;
      margin-top: 22px;
    }}
    .grid.three {{
      grid-template-columns: repeat(3, minmax(0, 1fr));
    }}
    .panel {{
      padding: 22px;
    }}
    .chart {{
      width: 100%;
      height: auto;
      display: block;
    }}
    .chart .grid line {{
      stroke: rgba(24, 33, 38, 0.10);
      stroke-width: 1;
    }}
    .chart .grid text, .axis-label, .bar-label {{
      fill: var(--muted);
      font-size: 11px;
    }}
    .axis-label, .value-label {{
      text-anchor: middle;
    }}
    .value-label, .bar-value {{
      fill: var(--ink);
      font-size: 11px;
      font-weight: 700;
    }}
    .line-points circle {{
      fill: #ffffff;
      stroke: var(--teal);
      stroke-width: 3;
    }}
    .donut-wrap {{
      display: grid;
      gap: 18px;
      align-items: center;
      justify-items: center;
    }}
    .donut-chart {{
      width: min(300px, 72vw);
      aspect-ratio: 1;
      border-radius: 50%;
      display: grid;
      place-items: center;
      box-shadow: inset 0 0 0 1px rgba(255,255,255,0.35);
    }}
    .donut-hole {{
      width: 56%;
      aspect-ratio: 1;
      border-radius: 50%;
      background: rgba(255, 251, 245, 0.96);
      display: grid;
      place-items: center;
      text-align: center;
      box-shadow: inset 0 0 0 1px rgba(24, 33, 38, 0.08);
    }}
    .donut-hole span {{
      color: var(--muted);
      font-size: 0.82rem;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }}
    .donut-hole strong {{
      font-size: 1.65rem;
      line-height: 1;
    }}
    .legend {{
      width: 100%;
      display: grid;
      gap: 10px;
    }}
    .legend-item {{
      display: grid;
      grid-template-columns: 14px 1fr auto;
      gap: 10px;
      align-items: center;
      padding: 10px 12px;
      border-radius: 14px;
      background: rgba(255,255,255,0.56);
      border: 1px solid rgba(24, 33, 38, 0.07);
    }}
    .legend-swatch {{
      width: 14px;
      height: 14px;
      border-radius: 999px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin-top: 10px;
      font-size: 0.95rem;
    }}
    th, td {{
      padding: 12px 14px;
      border-bottom: 1px solid var(--line);
      text-align: left;
      vertical-align: top;
    }}
    th {{
      background: rgba(15, 118, 110, 0.08);
      color: var(--muted);
      font-size: 0.82rem;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }}
    .footer-note {{
      margin-top: 14px;
      color: var(--muted);
      font-size: 0.92rem;
    }}
    @media (max-width: 980px) {{
      .grid, .grid.three {{
        grid-template-columns: 1fr;
      }}
      .hero {{
        padding: 26px;
      }}
    }}
  </style>
</head>
<body>
  <div class="shell">
    <section class="hero">
      <div class="eyebrow">Executive Sales Command Center</div>
      <h1>High-value sales performance, margin, and momentum</h1>
      <p class="hero-copy">This dashboard is generated directly from the synthetic enterprise sales dataframe in your code. It focuses on revenue quality, profitability, commercial execution, and customer sentiment across years, regions, products, and sales reps.</p>
      <div class="kpis">{hero_cards_html}</div>
    </section>

    <section class="grid">
      {build_line_chart("Net Sales Trend by Month", trend_labels, trend_values)}
      {build_donut_chart("Category Revenue Mix", category_share["Category"].tolist(), category_share["Net Sales ($)"].tolist())}
    </section>

    <section class="grid three">
      {build_horizontal_bar_chart("Regional Profit Contribution", region_profit["Region"].tolist(), region_profit["Profit ($)"].tolist(), format_currency)}
      {build_horizontal_bar_chart("Customer Satisfaction by Segment", customer_satisfaction["Customer Type"].tolist(), customer_satisfaction["Customer Satisfaction"].tolist(), lambda value: f"{value:.2f}/5")}
      {build_horizontal_bar_chart("Top Sales Reps by Net Sales", top_reps["Sales Rep"].tolist(), top_reps["Net Sales ($)"].tolist(), format_currency)}
    </section>

    <section class="grid">
      <article class="panel">
        <h3>Top Sales Reps</h3>
        {build_table(["Sales Rep", "Net Sales", "Profit", "Units Sold"], top_rep_rows)}
      </article>
      <article class="panel">
        <h3>Yearly Summary</h3>
        {build_table(["Year", "Net Sales", "Profit", "Units Sold", "Avg Satisfaction"], year_rows)}
      </article>
    </section>

    <section class="grid">
      <article class="panel">
        <h3>Best-Selling Products</h3>
        {build_table(["Product", "Category", "Net Sales", "Profit", "Units Sold"], product_rows)}
      </article>
      <article class="panel">
        <h3>Data Footprint</h3>
        <p class="panel-copy">The generated dataset contains {len(df):,} rows across {len(df.columns)} fields. Raw exports are written to <code>dashboard_exports</code>, and this same page is mirrored to <code>docs/index.html</code> for GitHub Pages publishing.</p>
        {build_table(
            ["Field", "Meaning"],
            [
                ["Net Sales ($)", "Revenue after the applied discount"],
                ["Profit ($)", "Net sales minus estimated cost"],
                ["Profit Margin (%)", "Profit as a percentage of net sales"],
                ["Customer Satisfaction", "Synthetic 1-5 customer rating"],
                ["Customer Type", "Retail, Corporate, Government, or SMB account"],
            ],
        )}
        <div class="footer-note">Rerun the script after changing the dataframe definition to rebuild the entire dashboard.</div>
      </article>
    </section>
  </div>
</body>
</html>
"""


df = build_sales_dataframe()
OUTPUT_DATA_DIR.mkdir(exist_ok=True)
df.to_csv(OUTPUT_DATA_CSV, index=False)

top_reps_export = (
    df.groupby("Sales Rep", as_index=False)
    .agg({"Net Sales ($)": "sum", "Profit ($)": "sum", "Units Sold": "sum"})
    .sort_values("Net Sales ($)", ascending=False)
)
top_reps_export.to_csv(OUTPUT_REP_CSV, index=False)

year_summary_export = (
    df.groupby("Year", as_index=False)
    .agg({
        "Net Sales ($)": "sum",
        "Profit ($)": "sum",
        "Units Sold": "sum",
        "Customer Satisfaction": "mean",
    })
    .sort_values("Year")
)
year_summary_export.to_csv(OUTPUT_YEAR_CSV, index=False)

html_output = render_dashboard(df)
OUTPUT_HTML.write_text(html_output, encoding="utf-8")
OUTPUT_SITE_DIR.mkdir(exist_ok=True)
OUTPUT_SITE_HTML.write_text(html_output, encoding="utf-8")
OUTPUT_NOJEKYLL.write_text("", encoding="utf-8")

print(f"Dataset generated: {len(df):,} rows x {len(df.columns)} columns")
print(f"HTML dashboard saved: {OUTPUT_HTML.resolve()}")
print(f"Shareable site entry saved: {OUTPUT_SITE_HTML.resolve()}")
print(f"Dataset CSV saved: {OUTPUT_DATA_CSV.resolve()}")
