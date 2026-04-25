import html
from pathlib import Path
import re

import pandas as pd
from openpyxl import load_workbook

INPUT_FILE = Path("dashboard.xlsx")
OUTPUT_HTML = Path("ai_dashboard.html")
OUTPUT_SITE_DIR = Path("docs")
OUTPUT_SITE_HTML = OUTPUT_SITE_DIR / "index.html"
OUTPUT_NOJEKYLL = OUTPUT_SITE_DIR / ".nojekyll"
OUTPUT_DATA_DIR = Path("dashboard_exports")
OUTPUT_DATA_INDEX = OUTPUT_DATA_DIR / "dataset_index.csv"
OUTPUT_SUGGESTIONS_CSV = OUTPUT_DATA_DIR / "dashboard_suggestions.csv"

PREFERRED_LABEL_NAMES = ("month", "date", "day", "category", "region", "name", "label", "segment", "type")
PALETTE = ["#0f766e", "#f59e0b", "#dc2626", "#2563eb", "#7c3aed", "#16a34a", "#ea580c", "#0891b2"]
IGNORED_SHEET_NAMES = {"dashboard"}


def slugify(value):
    slug = re.sub(r"[^a-z0-9]+", "-", str(value).lower()).strip("-")
    return slug or "dataset"


def format_value(value):
    if isinstance(value, float):
        if value.is_integer():
            return f"{int(value):,}"
        return f"{value:,.2f}"
    if isinstance(value, int):
        return f"{value:,}"
    return str(value)


def escape_cell(value):
    if pd.isna(value):
        return ""
    return html.escape(format_value(value))


def sample_dataframes():
    return {
        "Sample Sales": pd.DataFrame({
            "Month": ["Jan", "Feb", "Mar", "Apr"],
            "Sales": [100, 150, 120, 180],
            "Region": ["North", "South", "North", "South"],
        })
    }


def get_manual_dataframes():
    # Add custom in-memory dataframes here when needed.
    return {}


def first_non_empty_row(rows):
    for row in rows:
        if any(value not in (None, "") for value in row):
            return row
    return None


def looks_like_header(row):
    filled = [value for value in row if value not in (None, "")]
    if len(filled) < 2:
        return False
    return all(isinstance(value, str) for value in filled)


def build_dataframe_from_rows(rows):
    non_empty_rows = [list(row) for row in rows if any(value not in (None, "") for value in row)]
    if not non_empty_rows:
        return pd.DataFrame()

    header_row = first_non_empty_row(non_empty_rows)
    if header_row is None:
        return pd.DataFrame()

    max_columns = max(len(row) for row in non_empty_rows)
    normalized_rows = [row + [None] * (max_columns - len(row)) for row in non_empty_rows]

    if looks_like_header(header_row):
        headers = []
        for index, value in enumerate(normalized_rows[0], start=1):
            label = str(value).strip() if value not in (None, "") else f"Column {index}"
            headers.append(label)
        data_rows = normalized_rows[1:]
    else:
        headers = [f"Column {index}" for index in range(1, max_columns + 1)]
        data_rows = normalized_rows

    df = pd.DataFrame(data_rows, columns=headers)
    df = df.dropna(axis=0, how="all").dropna(axis=1, how="all")
    return df.reset_index(drop=True)


def load_workbook_dataframes():
    if not INPUT_FILE.exists():
        return {}

    workbook = load_workbook(INPUT_FILE, data_only=True)
    datasets = {}
    for sheet_name in workbook.sheetnames:
        if sheet_name.strip().lower() in IGNORED_SHEET_NAMES:
            continue
        sheet = workbook[sheet_name]
        rows = list(sheet.iter_rows(values_only=True))
        df = build_dataframe_from_rows(rows)
        if not df.empty:
            datasets[sheet_name] = df
    return datasets


def normalize_dataframe(df):
    normalized = df.copy()
    normalized.columns = [str(column).strip() or f"Column {index + 1}" for index, column in enumerate(normalized.columns)]
    normalized = normalized.dropna(axis=0, how="all").dropna(axis=1, how="all").reset_index(drop=True)
    for column in normalized.columns:
        if normalized[column].dtype == object:
            normalized[column] = normalized[column].map(lambda value: value.strip() if isinstance(value, str) else value)
    return normalized


def get_dataframes():
    datasets = {}
    datasets.update(load_workbook_dataframes())
    datasets.update(get_manual_dataframes())

    normalized = {}
    for name, df in datasets.items():
        clean_df = normalize_dataframe(df)
        if not clean_df.empty:
            normalized[name] = clean_df
    return normalized or sample_dataframes()


def numeric_columns(df):
    numeric = []
    for column in df.columns:
        converted = pd.to_numeric(df[column], errors="coerce")
        if converted.notna().sum() > 0:
            numeric.append(column)
    return numeric


def categorical_columns(df, excluded=None):
    excluded = set(excluded or [])
    return [column for column in df.columns if column not in excluded]


def choose_primary_metric(df):
    candidates = []
    for column in numeric_columns(df):
        series = pd.to_numeric(df[column], errors="coerce").dropna()
        if series.empty:
            continue
        score = (series.notna().sum(), float(series.abs().sum()), float(series.std(ddof=0) or 0.0))
        candidates.append((score, column))
    if not candidates:
        return None
    return max(candidates)[1]


def choose_label_column(df, excluded=None):
    excluded = set(excluded or [])
    candidates = []
    for column in categorical_columns(df, excluded):
        unique_count = df[column].dropna().astype(str).nunique()
        if unique_count < 2:
            continue
        preference = 1 if any(token in column.lower() for token in PREFERRED_LABEL_NAMES) else 0
        candidates.append(((preference, -abs(unique_count - min(len(df), 6))), column))
    if candidates:
        return max(candidates)[1]
    for column in df.columns:
        if column not in excluded:
            return column
    return None


def build_bar_series(df):
    metric_column = choose_primary_metric(df)
    if metric_column is None:
        return None

    label_column = choose_label_column(df, excluded={metric_column})
    metric_series = pd.to_numeric(df[metric_column], errors="coerce")

    if label_column is None:
        labels = [f"Row {index + 1}" for index in range(len(df))]
        chart_df = pd.DataFrame({"label": labels, "value": metric_series}).dropna()
    else:
        chart_df = pd.DataFrame({
            "label": df[label_column].astype(str),
            "value": metric_series,
        }).dropna()
        chart_df = chart_df.groupby("label", as_index=False)["value"].sum()

    if chart_df.empty:
        return None

    chart_df = chart_df.sort_values("value", ascending=False).head(12)
    return {
        "title": f"{metric_column} by {label_column or 'Row'}",
        "labels": chart_df["label"].tolist(),
        "values": chart_df["value"].tolist(),
        "metric_column": metric_column,
        "label_column": label_column or "Row",
    }


def build_donut_series(df):
    metric_column = choose_primary_metric(df)
    label_column = choose_label_column(df, excluded={metric_column} if metric_column else set())
    if label_column is None:
        return None

    label_series = df[label_column].astype(str)
    if label_series.nunique() < 2:
        return None

    if metric_column is not None:
        metric_series = pd.to_numeric(df[metric_column], errors="coerce")
        chart_df = pd.DataFrame({"label": label_series, "value": metric_series}).dropna()
        if chart_df.empty:
            return None
        chart_df = chart_df.groupby("label", as_index=False)["value"].sum()
        title = f"{metric_column} share by {label_column}"
    else:
        chart_df = label_series.value_counts().reset_index()
        chart_df.columns = ["label", "value"]
        title = f"Record share by {label_column}"

    chart_df = chart_df.sort_values("value", ascending=False)
    if len(chart_df) > 6:
        top_rows = chart_df.head(5).copy()
        remainder = chart_df.iloc[5:]["value"].sum()
        chart_df = pd.concat(
            [top_rows, pd.DataFrame([{"label": "Other", "value": remainder}])],
            ignore_index=True,
        )

    return {
        "title": title,
        "labels": chart_df["label"].tolist(),
        "values": chart_df["value"].tolist(),
        "label_column": label_column,
        "metric_column": metric_column,
    }


def build_dataset_suggestions(name, df, bar_series, donut_series):
    suggestions = []
    if bar_series is not None:
        suggestions.append(
            f"Bar chart: compare {bar_series['metric_column']} across {bar_series['label_column']} for {name}."
        )
    if donut_series is not None:
        suggestions.append(
            f"Distribution chart: show how {donut_series['metric_column'] or 'records'} split by {donut_series['label_column']} in {name}."
        )
    suggestions.append(f"Detail table: keep the first rows of {name} visible for quick inspection.")
    return suggestions[:3]


def build_table(headers, rows):
    header_html = "".join(f"<th>{html.escape(str(header))}</th>" for header in headers)
    body_rows = []
    for row in rows:
        cells = "".join(f"<td>{escape_cell(cell)}</td>" for cell in row)
        body_rows.append(f"<tr>{cells}</tr>")
    return (
        "<table><thead><tr>"
        + header_html
        + "</tr></thead><tbody>"
        + "".join(body_rows)
        + "</tbody></table>"
    )


def build_bar_chart(chart_id, title, labels, values):
    chart_width = 560
    chart_height = 280
    left = 56
    right = 18
    top = 22
    bottom = 42
    inner_width = chart_width - left - right
    inner_height = chart_height - top - bottom
    max_value = max(max(float(value) for value in values), 1.0)
    slot_width = inner_width / max(len(values), 1)
    bar_width = min(52, slot_width * 0.58)

    grid_lines = []
    bars = []
    value_labels = []
    axis_labels = []

    for step in range(5):
        grid_value = max_value * step / 4
        y = top + inner_height - (grid_value / max_value) * inner_height
        grid_lines.append(
            f'<line x1="{left}" y1="{y:.1f}" x2="{chart_width - right}" y2="{y:.1f}" />'
            f'<text x="{left - 10}" y="{y + 4:.1f}">{html.escape(format_value(grid_value))}</text>'
        )

    for index, (label, value) in enumerate(zip(labels, values), start=0):
        x = left + slot_width * index + (slot_width - bar_width) / 2
        height = (float(value) / max_value) * inner_height
        y = top + inner_height - height
        label_x = x + bar_width / 2
        bars.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_width:.1f}" height="{height:.1f}" rx="14" />')
        value_labels.append(
            f'<text x="{label_x:.1f}" y="{max(y - 10, 16):.1f}" class="value-label">{html.escape(format_value(float(value)))}</text>'
        )
        axis_labels.append(
            f'<text x="{label_x:.1f}" y="{chart_height - 14}" class="axis-label">{html.escape(str(label))}</text>'
        )

    return f"""
    <article class="panel">
      <h3>{html.escape(title)}</h3>
      <svg viewBox="0 0 {chart_width} {chart_height}" class="sales-chart" role="img" aria-label="{html.escape(title)}">
        <defs>
          <linearGradient id="{chart_id}" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#34d399" />
            <stop offset="100%" stop-color="#0f766e" />
          </linearGradient>
        </defs>
        <g class="grid">{''.join(grid_lines)}</g>
        <g class="bars" style="fill:url(#{chart_id})">{''.join(bars)}</g>
        <g class="value-labels">{''.join(value_labels)}</g>
        <g class="labels">{''.join(axis_labels)}</g>
      </svg>
    </article>
    """


def build_donut_chart(title, labels, values):
    total = float(sum(values)) or 1.0
    cursor = 0.0
    segments = []
    legend_items = []
    for index, (label, value) in enumerate(zip(labels, values), start=0):
        share = float(value) / total
        next_cursor = cursor + share * 100
        color = PALETTE[(index - 1) % len(PALETTE)]
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
            <strong>{html.escape(format_value(total))}</strong>
          </div>
        </div>
        <div class="legend">{''.join(legend_items)}</div>
      </div>
    </article>
    """


def build_dataset_context(name, df):
    bar_series = build_bar_series(df)
    donut_series = build_donut_series(df)
    preview_df = df.head(8).fillna("")
    suggestions = build_dataset_suggestions(name, df, bar_series, donut_series)

    stats = [
        {"label": "Rows", "value": len(df), "note": f"{len(df.columns)} columns"},
        {"label": "Numeric Columns", "value": len(numeric_columns(df)), "note": "Fields usable for aggregation"},
        {"label": "Categories", "value": len(categorical_columns(df)), "note": "Non-metric grouping fields"},
    ]

    primary_metric = choose_primary_metric(df)
    if primary_metric is not None:
        numeric_series = pd.to_numeric(df[primary_metric], errors="coerce").dropna()
        stats.append({
            "label": f"Primary Metric",
            "value": format_value(float(numeric_series.sum())),
            "note": f"Total {primary_metric}",
        })

    return {
        "name": name,
        "slug": slugify(name),
        "dataframe": df,
        "stats": stats,
        "bar_series": bar_series,
        "donut_series": donut_series,
        "suggestions": suggestions,
        "preview_table": build_table(preview_df.columns.tolist(), preview_df.values.tolist()),
    }


def render_html_dashboard(dataset_contexts):
    total_rows = sum(len(context["dataframe"]) for context in dataset_contexts)
    total_columns = sum(len(context["dataframe"].columns) for context in dataset_contexts)
    hero_cards = [
        ("Datasets", len(dataset_contexts), "Detected and rendered automatically"),
        ("Rows", total_rows, "Across all included dataframes"),
        ("Columns", total_columns, "Combined schema width"),
    ]

    hero_cards_html = "".join(
        "<div class=\"card\">"
        f"<div class=\"eyebrow\">{html.escape(label)}</div>"
        f"<div class=\"metric\">{html.escape(format_value(value))}</div>"
        f"<div class=\"metric-note\">{html.escape(note)}</div>"
        "</div>"
        for label, value, note in hero_cards
    )

    dataset_sections = []
    for context in dataset_contexts:
        stat_cards = "".join(
            "<div class=\"card compact\">"
            f"<div class=\"eyebrow\">{html.escape(stat['label'])}</div>"
            f"<div class=\"metric small\">{html.escape(format_value(stat['value']))}</div>"
            f"<div class=\"metric-note\">{html.escape(stat['note'])}</div>"
            "</div>"
            for stat in context["stats"]
        )

        chart_panels = []
        if context["bar_series"] is not None:
            chart_panels.append(
                build_bar_chart(
                    f"bar-gradient-{context['slug']}",
                    context["bar_series"]["title"],
                    context["bar_series"]["labels"],
                    context["bar_series"]["values"],
                )
            )
        if context["donut_series"] is not None:
            chart_panels.append(
                build_donut_chart(
                    context["donut_series"]["title"],
                    context["donut_series"]["labels"],
                    context["donut_series"]["values"],
                )
            )
        if not chart_panels:
            chart_panels.append(
                "<article class=\"panel\"><h3>No chartable structure detected</h3>"
                "<p class=\"panel-copy\">This dataset does not have enough numeric or grouping information for a chart, so only the preview table is shown.</p></article>"
            )

        suggestion_items = "".join(f"<li>{html.escape(item)}</li>" for item in context["suggestions"])
        dataset_sections.append(
            f"""
            <section class="dataset-section">
              <div class="dataset-header">
                <div>
                  <div class="eyebrow">Dataset</div>
                  <h2>{html.escape(context["name"])}</h2>
                </div>
              </div>
              <div class="kpis compact-grid">{stat_cards}</div>
              <div class="grid">{''.join(chart_panels)}</div>
              <div class="dataset-lower">
                <article class="panel">
                  <h3>Suggested Views</h3>
                  <ol>{suggestion_items}</ol>
                </article>
                <article class="panel">
                  <h3>Data Preview</h3>
                  {context["preview_table"]}
                </article>
              </div>
            </section>
            """
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AI Multi-Dataframe Dashboard</title>
  <style>
    :root {{
      --ink: #182126;
      --muted: #5d6a72;
      --panel: rgba(255, 252, 247, 0.86);
      --line: rgba(24, 33, 38, 0.12);
      --shadow: 0 24px 60px rgba(24, 33, 38, 0.12);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Trebuchet MS", "Segoe UI Variable Text", sans-serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, rgba(15, 118, 110, 0.20), transparent 32%),
        radial-gradient(circle at top right, rgba(245, 158, 11, 0.22), transparent 26%),
        linear-gradient(160deg, #f9f3ea 0%, #f1efe8 55%, #e8f1ef 100%);
      min-height: 100vh;
    }}
    .shell {{
      max-width: 1220px;
      margin: 0 auto;
      padding: 36px 20px 56px;
    }}
    .hero, .panel, .card {{
      background: var(--panel);
      border: 1px solid rgba(255,255,255,0.8);
      border-radius: 24px;
      box-shadow: var(--shadow);
      backdrop-filter: blur(14px);
    }}
    .hero {{
      padding: 32px;
      overflow: hidden;
      position: relative;
    }}
    .hero::after {{
      content: "";
      position: absolute;
      inset: auto -90px -110px auto;
      width: 280px;
      height: 280px;
      border-radius: 999px;
      background: rgba(15, 118, 110, 0.10);
    }}
    h1, h2, h3 {{
      font-family: "Palatino Linotype", "Book Antiqua", Georgia, serif;
      margin: 0;
    }}
    h1 {{
      font-size: clamp(2.1rem, 4vw, 3.8rem);
      line-height: 0.95;
      max-width: 10ch;
    }}
    h2 {{
      font-size: 2rem;
    }}
    h3 {{
      font-size: 1.2rem;
      margin-bottom: 12px;
    }}
    .hero p, .panel-copy {{
      color: var(--muted);
      line-height: 1.6;
    }}
    .hero p {{
      max-width: 62ch;
      margin: 16px 0 0;
    }}
    .eyebrow {{
      color: var(--muted);
      font-size: 0.78rem;
      letter-spacing: 0.12em;
      text-transform: uppercase;
    }}
    .kpis {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 16px;
      margin-top: 24px;
    }}
    .compact-grid {{
      margin-top: 18px;
    }}
    .card {{
      padding: 18px 18px 16px;
    }}
    .card.compact {{
      padding: 16px;
    }}
    .metric {{
      margin-top: 8px;
      font-size: 1.9rem;
      font-weight: 700;
    }}
    .metric.small {{
      font-size: 1.45rem;
    }}
    .metric-note {{
      margin-top: 6px;
      color: var(--muted);
      font-size: 0.92rem;
    }}
    .dataset-section {{
      margin-top: 24px;
    }}
    .dataset-header {{
      display: flex;
      align-items: end;
      justify-content: space-between;
      gap: 16px;
      margin-bottom: 10px;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 18px;
      margin-top: 18px;
    }}
    .dataset-lower {{
      display: grid;
      grid-template-columns: 0.85fr 1.15fr;
      gap: 18px;
      margin-top: 18px;
    }}
    .panel {{
      padding: 22px;
    }}
    .sales-chart {{
      width: 100%;
      height: auto;
      display: block;
    }}
    .sales-chart .grid line {{
      stroke: rgba(24, 33, 38, 0.10);
      stroke-width: 1;
    }}
    .sales-chart .grid text {{
      fill: var(--muted);
      font-size: 11px;
      text-anchor: end;
    }}
    .sales-chart .axis-label {{
      fill: var(--muted);
      font-size: 12px;
      text-anchor: middle;
    }}
    .sales-chart .value-label {{
      fill: var(--ink);
      font-size: 11px;
      font-weight: 700;
      text-anchor: middle;
    }}
    .donut-wrap {{
      display: grid;
      gap: 18px;
      align-items: center;
      justify-items: center;
    }}
    .donut-chart {{
      width: min(280px, 70vw);
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
      background: rgba(255, 251, 246, 0.92);
      display: grid;
      place-items: center;
      text-align: center;
      box-shadow: inset 0 0 0 1px rgba(24, 33, 38, 0.08);
    }}
    .donut-hole span {{
      color: var(--muted);
      font-size: 0.85rem;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }}
    .donut-hole strong {{
      font-size: 1.6rem;
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
      background: rgba(255,255,255,0.58);
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
      background: rgba(15, 118, 110, 0.09);
      font-size: 0.82rem;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--muted);
    }}
    ol {{
      margin: 10px 0 0;
      padding-left: 22px;
    }}
    li {{
      margin-bottom: 10px;
      line-height: 1.45;
    }}
    @media (max-width: 960px) {{
      .grid, .dataset-lower {{
        grid-template-columns: 1fr;
      }}
      .hero {{
        padding: 24px;
      }}
    }}
  </style>
</head>
<body>
  <div class="shell">
    <section class="hero">
      <div class="eyebrow">Shareable HTML Dashboard</div>
      <h1>Generalized multi-dataframe dashboard</h1>
      <p>This page is generated from every detected dataframe. Update the dataframe definitions or workbook sheets, rerun the script, and the dashboard layout will rebuild around the new structure automatically.</p>
      <div class="kpis">{hero_cards_html}</div>
    </section>
    {''.join(dataset_sections)}
  </div>
</body>
</html>
"""


def export_dataset_files(dataset_contexts):
    OUTPUT_DATA_DIR.mkdir(exist_ok=True)
    dataset_index_rows = []
    suggestion_rows = []
    for context in dataset_contexts:
        csv_path = OUTPUT_DATA_DIR / f"{context['slug']}.csv"
        context["dataframe"].to_csv(csv_path, index=False)
        dataset_index_rows.append({
            "Dataset": context["name"],
            "Rows": len(context["dataframe"]),
            "Columns": len(context["dataframe"].columns),
            "CSV File": csv_path.name,
        })
        for suggestion in context["suggestions"]:
            suggestion_rows.append({"Dataset": context["name"], "Suggestion": suggestion})

    pd.DataFrame(dataset_index_rows).to_csv(OUTPUT_DATA_INDEX, index=False)
    pd.DataFrame(suggestion_rows).to_csv(OUTPUT_SUGGESTIONS_CSV, index=False)


datasets = get_dataframes()
dataset_contexts = [build_dataset_context(name, df) for name, df in datasets.items()]
html_output = render_html_dashboard(dataset_contexts)

export_dataset_files(dataset_contexts)
OUTPUT_HTML.write_text(html_output, encoding="utf-8")
OUTPUT_SITE_DIR.mkdir(exist_ok=True)
OUTPUT_SITE_HTML.write_text(html_output, encoding="utf-8")
OUTPUT_NOJEKYLL.write_text("", encoding="utf-8")

print("Datasets included:")
for context in dataset_contexts:
    print(f"- {context['name']}: {len(context['dataframe'])} rows, {len(context['dataframe'].columns)} columns")

print(f"HTML dashboard saved: {OUTPUT_HTML.resolve()}")
print(f"Shareable site entry saved: {OUTPUT_SITE_HTML.resolve()}")
print(f"Dataset index saved: {OUTPUT_DATA_INDEX.resolve()}")
print(f"Suggestions CSV saved: {OUTPUT_SUGGESTIONS_CSV.resolve()}")
