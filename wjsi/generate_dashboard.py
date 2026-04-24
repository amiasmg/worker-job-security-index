"""
generate_dashboard.py — Build a self-contained interactive HTML dashboard for WJSI.

Outputs:
    outputs/wjsi_dashboard.html   (open in any browser, no server needed)

Two main panels:
  1. Index & Components  — toggle each component on/off, switch z-scores ↔ raw values
  2. WJSI vs. Comparators — dual-axis overlay against U-3, U-6, LISEP TRU, Michigan Sentiment

Period toggle: Annual / Quarterly

Run after construct.py and construct_quarterly.py:
    python generate_dashboard.py
"""

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

OUT   = Path("outputs")
RAW   = Path("data/raw")
CLEAN = Path("data/clean")
OUT.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _nn(v):
    """Float NaN/Inf → None for JSON; preserve everything else."""
    if v is None:
        return None
    try:
        if math.isnan(v) or math.isinf(v):
            return None
    except TypeError:
        pass
    return v


def to_list(series):
    return [_nn(v) for v in series]


def fred_to_annual(filename, value_col):
    p = RAW / filename
    if not p.exists():
        return {}
    df = pd.read_csv(p)
    df["date"]  = pd.to_datetime(df["date"])
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df["year"]  = df["date"].dt.year
    ann = df.groupby("year")["value"].mean().reset_index()
    return dict(zip(ann["year"].astype(int), ann["value"]))


def fred_to_quarterly(filename, value_col):
    p = RAW / filename
    if not p.exists():
        return {}
    df = pd.read_csv(p)
    df["date"]  = pd.to_datetime(df["date"])
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df["year"]  = df["date"].dt.year
    df["quarter"] = df["date"].dt.quarter
    qtr = df.groupby(["year", "quarter"])["value"].mean().reset_index()
    return {(int(r.year), int(r.quarter)): r["value"] for _, r in qtr.iterrows()}


def load_lisep_tru_annual():
    """
    Load LISEP TRU from data/raw/lisep_tru.csv.
    Accepts either FRED-style (date, tru) monthly/quarterly or (year, tru) annual format.
    Returns {year: avg_tru_pct}.
    """
    p = RAW / "lisep_tru.csv"
    if not p.exists():
        return {}
    df = pd.read_csv(p)
    df.columns = df.columns.str.lower().str.strip()
    val_col = next((c for c in df.columns if c not in ("date", "year", "quarter")), None)
    if not val_col:
        return {}
    df[val_col] = pd.to_numeric(df[val_col], errors="coerce")
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
        df["year"] = df["date"].dt.year
    elif "year" not in df.columns:
        return {}
    ann = df.groupby("year")[val_col].mean().reset_index()
    return dict(zip(ann["year"].astype(int), ann[val_col]))


def load_lisep_tru_quarterly():
    """
    Load LISEP TRU → quarterly averages.
    Accepts FRED-style (date, tru) monthly or (year, quarter, tru) quarterly format.
    Returns {(year, quarter): avg_tru_pct}.
    """
    p = RAW / "lisep_tru.csv"
    if not p.exists():
        return {}
    df = pd.read_csv(p)
    df.columns = df.columns.str.lower().str.strip()
    val_col = next((c for c in df.columns if c not in ("date", "year", "quarter")), None)
    if not val_col:
        return {}
    df[val_col] = pd.to_numeric(df[val_col], errors="coerce")
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
        df["year"]    = df["date"].dt.year
        df["quarter"] = df["date"].dt.quarter
    elif "year" not in df.columns or "quarter" not in df.columns:
        return {}
    qtr = df.groupby(["year", "quarter"])[val_col].mean().reset_index()
    return {(int(r.year), int(r.quarter)): r[val_col] for _, r in qtr.iterrows()}


# ---------------------------------------------------------------------------
# Load and package data
# ---------------------------------------------------------------------------

def build_annual_payload():
    ann = pd.read_csv(OUT / "wjsi_annual.csv")
    ann["year"] = ann["year"].astype(int)

    u3_map   = fred_to_annual("unrate_fred.csv",               "u3")
    u6_map   = fred_to_annual("u6_fred.csv",                   "u6")
    sent_map = fred_to_annual("michigan_sentiment_fred.csv",   "sentiment")
    tru_map  = load_lisep_tru_annual()

    component_meta = {
        "union_z":       {"label": "Union membership rate",              "raw": "union_rate",    "raw_label": "Union rate (%)"},
        "openings_z":    {"label": "Job openings rate (inverted)",        "raw": "openings_rate", "raw_label": "Openings rate (%)"},
        "quits_z":       {"label": "Quits rate",                         "raw": "quits_rate",    "raw_label": "Quits rate (%)"},
        "layoffs_z":     {"label": "Layoffs rate (inverted)",             "raw": "layoffs_rate",  "raw_label": "Layoffs rate (%)"},
        "tenure_z":      {"label": "Median tenure",                      "raw": "median_tenure", "raw_label": "Median tenure (years)"},
        "labor_share_z": {"label": "Nonfarm labor share (PRS85006173)",  "raw": "labor_share",   "raw_label": "Labor share (index, 2012=100)"},
    }

    # Load raw component values from clean files for the annual series
    jolts   = pd.read_csv(CLEAN / "jolts_annual.csv")[["year","openings_rate","quits_rate","layoffs_rate"]]
    jolts["year"] = jolts["year"].astype(int)
    tenure  = pd.read_csv(CLEAN / "tenure_annual.csv")[["year","median_tenure"]]
    tenure["year"] = tenure["year"].astype(int)
    union   = pd.read_csv(CLEAN / "union_rate.csv")[["year","union_rate"]]
    union["year"] = union["year"].astype(int)
    ls      = pd.read_csv(CLEAN / "labor_share_annual.csv")[["year","labor_share"]]
    ls["year"] = ls["year"].astype(int)

    raw_merged = (ann[["year"]]
                  .merge(jolts,  on="year", how="left")
                  .merge(tenure, on="year", how="left")
                  .merge(union,  on="year", how="left")
                  .merge(ls,     on="year", how="left"))

    years = to_list(ann["year"])

    components = {}
    for z_col, meta in component_meta.items():
        z_data   = to_list(ann[z_col]) if z_col in ann.columns else [None]*len(years)
        raw_col  = meta["raw"]
        raw_data = to_list(raw_merged[raw_col]) if raw_col in raw_merged.columns else [None]*len(years)
        components[z_col] = {
            "label":     meta["label"],
            "raw_label": meta["raw_label"],
            "z":         z_data,
            "raw":       raw_data,
        }

    return {
        "years":      years,
        "wjsi":       to_list(ann["wjsi"]),
        "components": components,
        "comparators": {
            "u3":        {"label": "U-3 Unemployment (%)",        "inverted": True,  "data": [_nn(u3_map.get(y))   for y in ann["year"]]},
            "u6":        {"label": "U-6 Underemployment (%)",     "inverted": True,  "data": [_nn(u6_map.get(y))   for y in ann["year"]]},
            "tru":       {"label": "LISEP True Rate of Unemp. (%)","inverted": True,  "data": [_nn(tru_map.get(y))  for y in ann["year"]] if tru_map else None},
            "sentiment": {"label": "Michigan Consumer Sentiment", "inverted": False, "data": [_nn(sent_map.get(y)) for y in ann["year"]]},
        },
    }


def build_quarterly_payload():
    q = pd.read_csv(OUT / "wjsi_quarterly.csv")
    q["year"]    = q["year"].astype(int)
    q["quarter"] = q["quarter"].astype(int)

    u3_map   = fred_to_quarterly("unrate_fred.csv",             "u3")
    u6_map   = fred_to_quarterly("u6_fred.csv",                 "u6")
    sent_map = fred_to_quarterly("michigan_sentiment_fred.csv", "sentiment")
    tru_map  = load_lisep_tru_quarterly()

    component_meta = {
        "union_z":       {"label": "Union membership rate (interp.)",     "raw": "union_rate",    "raw_label": "Union rate (%)"},
        "openings_z":    {"label": "Job openings rate (inverted)",         "raw": "openings_rate", "raw_label": "Openings rate (%)"},
        "quits_z":       {"label": "Quits rate",                          "raw": "quits_rate",    "raw_label": "Quits rate (%)"},
        "layoffs_z":     {"label": "Layoffs rate (inverted)",              "raw": "layoffs_rate",  "raw_label": "Layoffs rate (%)"},
        "tenure_z":      {"label": "Median tenure (interp.)",             "raw": "median_tenure", "raw_label": "Median tenure (years)"},
        "labor_share_z": {"label": "Nonfarm labor share (PRS85006173)",   "raw": "labor_share",   "raw_label": "Labor share (index, 2012=100)"},
    }

    periods = [f"{int(r.year)} Q{int(r.quarter)}" for _, r in q.iterrows()]
    ydec    = to_list(q["ydec"])

    components = {}
    for z_col, meta in component_meta.items():
        z_data   = to_list(q[z_col]) if z_col in q.columns else [None]*len(periods)
        raw_col  = meta["raw"]
        raw_data = to_list(q[raw_col]) if raw_col in q.columns else [None]*len(periods)
        components[z_col] = {
            "label":     meta["label"],
            "raw_label": meta["raw_label"],
            "z":         z_data,
            "raw":       raw_data,
        }

    keys = [(int(r.year), int(r.quarter)) for _, r in q.iterrows()]

    return {
        "periods":    periods,
        "ydec":       ydec,
        "wjsi_q":     to_list(q["wjsi_q"]),
        "wjsi_q_ma4": to_list(q["wjsi_q_ma4"]),
        "components": components,
        "comparators": {
            "u3":        {"label": "U-3 Unemployment (%)",         "inverted": True,  "data": [_nn(u3_map.get(k))   for k in keys]},
            "u6":        {"label": "U-6 Underemployment (%)",      "inverted": True,  "data": [_nn(u6_map.get(k))   for k in keys]},
            "tru":       {"label": "LISEP True Rate of Unemp. (%)","inverted": True,  "data": [_nn(tru_map.get(k))  for k in keys] if tru_map else None},
            "sentiment": {"label": "Michigan Consumer Sentiment",  "inverted": False, "data": [_nn(sent_map.get(k)) for k in keys]},
        },
    }


# ---------------------------------------------------------------------------
# HTML template
# ---------------------------------------------------------------------------

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Worker Job Security Index — Dashboard</title>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js" charset="utf-8"></script>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: "Segoe UI", Arial, sans-serif; background: #f0f2f5; color: #222; }

.header {
  background: linear-gradient(135deg, #1f4e79, #2980b9);
  color: white; padding: 22px 36px;
}
.header h1 { font-size: 1.55rem; font-weight: 700; letter-spacing: 0.02em; }
.header p  { font-size: 0.88rem; opacity: 0.82; margin-top: 4px; }

.toolbar {
  background: white; border-bottom: 1px solid #dde3ea;
  padding: 12px 36px; display: flex; align-items: center; gap: 24px;
  flex-wrap: wrap;
}
.toolbar-label { font-size: 0.8rem; color: #666; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; }

.btn-group { display: flex; gap: 0; border-radius: 6px; overflow: hidden; border: 1.5px solid #c8d3df; }
.btn-group button {
  background: white; border: none; padding: 6px 18px; font-size: 0.85rem;
  cursor: pointer; color: #444; transition: background 0.15s;
}
.btn-group button:not(:last-child) { border-right: 1.5px solid #c8d3df; }
.btn-group button.active { background: #1f4e79; color: white; font-weight: 600; }
.btn-group button:hover:not(.active) { background: #eef2f7; }

.container { max-width: 1300px; margin: 0 auto; padding: 24px 24px 48px; display: flex; flex-direction: column; gap: 28px; }

.card {
  background: white; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.07);
  padding: 24px 28px;
}
.card h2 { font-size: 1.05rem; font-weight: 700; color: #1f4e79; margin-bottom: 16px; }

/* --- Component controls --- */
.comp-layout { display: flex; gap: 20px; }
.comp-sidebar {
  width: 210px; flex-shrink: 0; display: flex; flex-direction: column; gap: 10px;
}
.comp-sidebar h3 { font-size: 0.78rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: #888; margin-bottom: 2px; }
.comp-chart { flex: 1; min-width: 0; }

.toggle-row { display: flex; gap: 8px; margin-bottom: 4px; }

.check-list { display: flex; flex-direction: column; gap: 6px; }
.check-item { display: flex; align-items: center; gap: 8px; cursor: pointer; padding: 5px 8px; border-radius: 5px; transition: background 0.12s; user-select: none; }
.check-item:hover { background: #f0f4fa; }
.check-item input[type=checkbox] { display: none; }
.swatch {
  width: 14px; height: 14px; border-radius: 3px; border: 2px solid transparent;
  flex-shrink: 0; transition: opacity 0.15s;
}
.check-item.off .swatch { opacity: 0.25; }
.check-item.off .item-label { opacity: 0.4; }
.item-label { font-size: 0.82rem; line-height: 1.3; }

.divider { border: none; border-top: 1px solid #e8ecf0; margin: 6px 0; }

/* --- Comparator controls --- */
.comp-btn-row { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 16px; }
.comp-btn {
  padding: 7px 16px; border-radius: 20px; border: 1.5px solid #c8d3df;
  background: white; font-size: 0.83rem; cursor: pointer; color: #444;
  transition: all 0.15s;
}
.comp-btn:hover:not(.disabled) { border-color: #1f4e79; color: #1f4e79; }
.comp-btn.active { background: #1f4e79; color: white; border-color: #1f4e79; font-weight: 600; }
.comp-btn.disabled { opacity: 0.4; cursor: default; }

.note { font-size: 0.75rem; color: #888; margin-top: 10px; font-style: italic; }

/* --- Plotly override --- */
.js-plotly-plot .plotly { border-radius: 8px; }
</style>
</head>
<body>

<div class="header">
  <h1>Worker Job Security Index (WJSI) — Interactive Dashboard</h1>
  <p>Equal-weighted composite of 6 labour-market components &nbsp;|&nbsp; Base year 2005 = 100 &nbsp;|&nbsp; Data: BLS &amp; FRED</p>
</div>

<div class="toolbar">
  <span class="toolbar-label">Period</span>
  <div class="btn-group">
    <button id="btn-annual" class="active" onclick="setPeriod('annual')">Annual</button>
    <button id="btn-quarterly" onclick="setPeriod('quarterly')">Quarterly</button>
  </div>
</div>

<div class="container">

  <!-- ====== SECTION 1: Components ====== -->
  <div class="card">
    <h2>Index &amp; Components</h2>
    <div class="comp-layout">

      <div class="comp-sidebar">
        <h3>Show on chart</h3>

        <div class="toggle-row">
          <div class="btn-group" style="font-size:0.78rem">
            <button id="btn-zscore" class="active" onclick="setDisplay('z')">Z-scores</button>
            <button id="btn-raw" onclick="setDisplay('raw')">Raw values</button>
          </div>
        </div>

        <hr class="divider">

        <div class="check-list" id="check-list">
          <!-- injected by JS -->
        </div>
      </div>

      <div class="comp-chart">
        <div id="chart-components" style="height:420px"></div>
      </div>
    </div>
    <p class="note">
      WJSI shown as index (2005=100) on the right axis. Components shown as z-scores or raw values on the left axis.
      Union rate and median tenure are linearly interpolated from annual/biennial observations in the quarterly view.
    </p>
  </div>

  <!-- ====== SECTION 2: Comparators ====== -->
  <div class="card">
    <h2>WJSI vs. External Indicators</h2>
    <div class="comp-btn-row" id="comp-btn-row">
      <!-- injected by JS -->
    </div>
    <div id="chart-comparator" style="height:380px"></div>
    <p class="note" id="comp-note"></p>
  </div>

</div><!-- /container -->

<script>
// =========================================================
// EMBEDDED DATA
// =========================================================
const ANNUAL    = __ANNUAL__;
const QUARTERLY = __QUARTERLY__;

// =========================================================
// STATE
// =========================================================
let period      = 'annual';    // 'annual' | 'quarterly'
let displayMode = 'z';         // 'z' | 'raw'
let activeComp  = 'u3';        // active comparator key
let compVisible = {};          // z_col -> bool

// Component display config
const COMP_DEFS = [
  { key: 'wjsi',         label: 'WJSI Index',              color: '#1f4e79',  isIndex: true },
  { key: 'openings_z',   label: 'Job Openings (inv.)',      color: '#e67e22'  },
  { key: 'quits_z',      label: 'Quits Rate',              color: '#27ae60'  },
  { key: 'layoffs_z',    label: 'Layoffs (inv.)',           color: '#c0392b'  },
  { key: 'labor_share_z',label: 'Labor Share',              color: '#8e44ad'  },
  { key: 'union_z',      label: 'Union Membership',        color: '#16a085'  },
  { key: 'tenure_z',     label: 'Median Tenure',           color: '#2c3e50'  },
];

// NBER recession shading (decimal years)
const RECESSIONS = [
  [2001.17, 2001.83],
  [2007.92, 2009.42],
  [2020.08, 2020.33],
];

function recessionShapes(xaxis='x') {
  return RECESSIONS.map(([x0, x1]) => ({
    type: 'rect', x0, x1, y0: 0, y1: 1,
    xref: xaxis, yref: 'paper',
    fillcolor: '#b0b8c1', opacity: 0.18, line: { width: 0 }, layer: 'below',
  }));
}

// =========================================================
// INIT — build checkboxes and render both charts
// =========================================================
window.addEventListener('DOMContentLoaded', () => {
  COMP_DEFS.forEach(d => compVisible[d.key] = true);
  buildCheckboxes();
  buildComparatorButtons();
  renderComponents();
  renderComparator();
});

// =========================================================
// CONTROLS
// =========================================================
function setPeriod(p) {
  period = p;
  document.getElementById('btn-annual').classList.toggle('active', p === 'annual');
  document.getElementById('btn-quarterly').classList.toggle('active', p === 'quarterly');
  renderComponents();
  renderComparator();
}

function setDisplay(mode) {
  displayMode = mode;
  document.getElementById('btn-zscore').classList.toggle('active', mode === 'z');
  document.getElementById('btn-raw').classList.toggle('active', mode === 'raw');
  renderComponents();
}

function toggleComp(key) {
  compVisible[key] = !compVisible[key];
  document.getElementById('ci-' + key).classList.toggle('off', !compVisible[key]);
  renderComponents();
}

function setActiveComp(key) {
  activeComp = key;
  document.querySelectorAll('.comp-btn').forEach(b => {
    b.classList.toggle('active', b.dataset.comp === key);
  });
  renderComparator();
}

// =========================================================
// BUILD CHECKBOX SIDEBAR
// =========================================================
function buildCheckboxes() {
  const list = document.getElementById('check-list');
  list.innerHTML = '';
  COMP_DEFS.forEach(d => {
    const item = document.createElement('div');
    item.className = 'check-item';
    item.id = 'ci-' + d.key;
    item.onclick = () => toggleComp(d.key);
    item.innerHTML = `
      <div class="swatch" style="background:${d.color}; border-color:${d.color}"></div>
      <span class="item-label">${d.label}</span>`;
    list.appendChild(item);
  });
}

// =========================================================
// BUILD COMPARATOR BUTTONS
// =========================================================
function buildComparatorButtons() {
  const row = document.getElementById('comp-btn-row');
  const data = period === 'annual' ? ANNUAL : QUARTERLY;
  const comps = [
    { key: 'u3',        label: 'U-3 Unemployment' },
    { key: 'u6',        label: 'U-6 Underemployment' },
    { key: 'tru',       label: 'LISEP TRU' },
    { key: 'sentiment', label: 'Michigan Sentiment' },
  ];
  row.innerHTML = '';
  comps.forEach(c => {
    const avail = data.comparators[c.key] && data.comparators[c.key].data !== null;
    const btn = document.createElement('button');
    btn.className = 'comp-btn' + (c.key === activeComp ? ' active' : '') + (!avail ? ' disabled' : '');
    btn.dataset.comp = c.key;
    btn.textContent = c.label + (!avail ? ' (data pending)' : '');
    if (avail) btn.onclick = () => setActiveComp(c.key);
    row.appendChild(btn);
  });
}

// =========================================================
// CHART 1 — Components
// =========================================================
function renderComponents() {
  const d = period === 'annual' ? ANNUAL : QUARTERLY;
  const xs = period === 'annual' ? d.years : d.ydec;

  const traces = [];

  // Component traces (left y-axis)
  COMP_DEFS.filter(def => !def.isIndex).forEach(def => {
    if (!compVisible[def.key]) return;
    const comp = d.components[def.key];
    if (!comp) return;
    const ydata = displayMode === 'z' ? comp.z : comp.raw;
    const yname = displayMode === 'z' ? def.label + ' (z)' : comp.raw_label;

    traces.push({
      x: xs, y: ydata,
      name: def.label,
      type: 'scatter', mode: 'lines',
      line: { color: def.color, width: 1.7 },
      yaxis: 'y',
      hovertemplate: `<b>${def.label}</b><br>%{x}: %{y:.2f}<extra></extra>`,
    });
  });

  // WJSI trace (right y-axis)
  if (compVisible['wjsi']) {
    const wjsiY = period === 'annual' ? d.wjsi : d.wjsi_q;
    const wjsiMA = period === 'quarterly' ? d.wjsi_q_ma4 : null;

    if (period === 'quarterly' && wjsiMA) {
      // Raw quarterly (faint)
      traces.push({
        x: xs, y: wjsiY,
        name: 'WJSI (quarterly)',
        type: 'scatter', mode: 'lines',
        line: { color: '#1f4e79', width: 0.8, dash: 'dot' },
        yaxis: 'y2', opacity: 0.35,
        showlegend: false,
        hovertemplate: `<b>WJSI</b><br>%{x}: %{y:.1f}<extra></extra>`,
      });
      // 4Q MA (bold)
      traces.push({
        x: xs, y: wjsiMA,
        name: 'WJSI (4Q MA)',
        type: 'scatter', mode: 'lines',
        line: { color: '#1f4e79', width: 2.5 },
        yaxis: 'y2',
        hovertemplate: `<b>WJSI 4Q MA</b><br>%{x}: %{y:.1f}<extra></extra>`,
      });
    } else {
      traces.push({
        x: xs, y: wjsiY,
        name: 'WJSI Index',
        type: 'scatter', mode: 'lines+markers',
        line: { color: '#1f4e79', width: 2.5 },
        marker: { size: 5 },
        yaxis: 'y2',
        hovertemplate: `<b>WJSI</b><br>%{x}: %{y:.1f}<extra></extra>`,
      });
    }
  }

  const yAxisTitle = displayMode === 'z' ? 'Z-score' : 'Raw value';

  const layout = {
    margin: { t: 20, r: 80, b: 50, l: 60 },
    paper_bgcolor: 'white', plot_bgcolor: 'white',
    legend: { orientation: 'h', y: -0.18, x: 0, font: { size: 11 } },
    xaxis: {
      title: period === 'annual' ? 'Year' : 'Quarter',
      gridcolor: '#e8ecf0', zeroline: false,
      tickformat: period === 'annual' ? 'd' : '.2f',
    },
    yaxis: {
      title: yAxisTitle,
      gridcolor: '#e8ecf0', zeroline: true, zerolinecolor: '#bbb', zerolinewidth: 1,
    },
    yaxis2: {
      title: 'WJSI (2005=100)',
      overlaying: 'y', side: 'right',
      gridcolor: 'rgba(0,0,0,0)',
      zeroline: false,
    },
    shapes: recessionShapes(),
    hovermode: 'x unified',
    font: { family: 'Segoe UI, Arial, sans-serif', size: 12 },
  };

  // Add base-year reference line
  layout.shapes.push({
    type: 'line', x0: xs[0], x1: xs[xs.length-1], y0: 100, y1: 100,
    xref: 'x', yref: 'y2',
    line: { color: '#1f4e79', width: 1, dash: 'dash' },
  });

  Plotly.react('chart-components', traces, layout, { responsive: true, displayModeBar: false });
}

// =========================================================
// CHART 2 — Comparators
// =========================================================
function renderComparator() {
  buildComparatorButtons();  // refresh button states

  const d = period === 'annual' ? ANNUAL : QUARTERLY;
  const xs = period === 'annual' ? d.years : d.ydec;
  const wjsiY = period === 'annual' ? d.wjsi : d.wjsi_q_ma4;
  const compMeta = d.comparators[activeComp];

  const noteEl = document.getElementById('comp-note');

  if (!compMeta || compMeta.data === null) {
    noteEl.textContent = activeComp === 'tru'
      ? 'LISEP TRU data not yet loaded. Add data/raw/lisep_tru.csv (columns: year, quarter [optional], tru) and re-run generate_dashboard.py.'
      : 'Data not available for this indicator.';
    Plotly.react('chart-comparator', [], {
      margin: { t: 20, r: 80, b: 50, l: 60 },
      annotations: [{ text: 'Data not available', xref: 'paper', yref: 'paper', x: 0.5, y: 0.5, showarrow: false, font: { size: 18, color: '#aaa' } }],
    }, { responsive: true, displayModeBar: false });
    return;
  }

  noteEl.textContent = compMeta.inverted
    ? `${compMeta.label} is shown on an inverted right axis so that both series move upward when job security improves.`
    : `${compMeta.label} is shown on the right axis.`;

  // Compute Pearson r (ignoring nulls)
  const pairs = xs.map((x, i) => [wjsiY[i], compMeta.data[i]]).filter(([a,b]) => a != null && b != null);
  let rLabel = '';
  if (pairs.length >= 5) {
    const n = pairs.length;
    const meanA = pairs.reduce((s,[a])=>s+a,0)/n;
    const meanB = pairs.reduce((s,[,b])=>s+b,0)/n;
    const num   = pairs.reduce((s,[a,b])=>s+(a-meanA)*(b-meanB),0);
    const denA  = Math.sqrt(pairs.reduce((s,[a])=>s+(a-meanA)**2,0));
    const denB  = Math.sqrt(pairs.reduce((s,[,b])=>s+(b-meanB)**2,0));
    const r     = num / (denA * denB);
    rLabel = `  |  Pearson r = ${r.toFixed(3)} (contemporaneous, n=${n})`;
  }
  noteEl.textContent += rLabel;

  const traces = [
    {
      x: xs, y: wjsiY,
      name: period === 'annual' ? 'WJSI (annual)' : 'WJSI (4Q MA)',
      type: 'scatter', mode: period === 'annual' ? 'lines+markers' : 'lines',
      line: { color: '#1f4e79', width: 2.5 },
      marker: { size: 5 },
      yaxis: 'y',
      hovertemplate: `<b>WJSI</b><br>%{x}: %{y:.1f}<extra></extra>`,
    },
    {
      x: xs, y: compMeta.data,
      name: compMeta.label,
      type: 'scatter', mode: 'lines',
      line: { color: '#c0392b', width: 2, dash: 'dash' },
      yaxis: 'y2',
      hovertemplate: `<b>${compMeta.label}</b><br>%{x}: %{y:.1f}<extra></extra>`,
    },
  ];

  const layout = {
    margin: { t: 20, r: 80, b: 50, l: 60 },
    paper_bgcolor: 'white', plot_bgcolor: 'white',
    legend: { orientation: 'h', y: -0.18, x: 0, font: { size: 11 } },
    xaxis: {
      title: period === 'annual' ? 'Year' : 'Quarter',
      gridcolor: '#e8ecf0', zeroline: false,
      tickformat: period === 'annual' ? 'd' : '.2f',
    },
    yaxis: {
      title: 'WJSI (2005=100)',
      gridcolor: '#e8ecf0', zeroline: false,
    },
    yaxis2: {
      title: compMeta.label,
      overlaying: 'y', side: 'right',
      autorange: compMeta.inverted ? 'reversed' : true,
      gridcolor: 'rgba(0,0,0,0)',
    },
    shapes: recessionShapes(),
    hovermode: 'x unified',
    font: { family: 'Segoe UI, Arial, sans-serif', size: 12 },
  };

  Plotly.react('chart-comparator', traces, layout, { responsive: true, displayModeBar: false });
}
</script>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Generate
# ---------------------------------------------------------------------------

def generate():
    print("Loading annual data...")
    annual = build_annual_payload()
    print(f"  Annual: {len(annual['years'])} years, "
          f"comparators: {[k for k,v in annual['comparators'].items() if v['data'] is not None]}")

    print("Loading quarterly data...")
    quarterly = build_quarterly_payload()
    print(f"  Quarterly: {len(quarterly['periods'])} quarters, "
          f"comparators: {[k for k,v in quarterly['comparators'].items() if v['data'] is not None]}")

    annual_json    = json.dumps(annual,    separators=(',', ':'))
    quarterly_json = json.dumps(quarterly, separators=(',', ':'))

    html = HTML_TEMPLATE \
        .replace('__ANNUAL__',    annual_json) \
        .replace('__QUARTERLY__', quarterly_json)

    out_path = OUT / "wjsi_dashboard.html"
    out_path.write_text(html, encoding="utf-8")
    size_kb = out_path.stat().st_size / 1024
    print(f"\nSaved: {out_path}  ({size_kb:.0f} KB)")
    print("Open in any browser — no server required.")

    tru_present = (RAW / "lisep_tru.csv").exists()
    if not tru_present:
        print("\nNote: LISEP TRU data not found (data/raw/lisep_tru.csv).")
        print("  Add a CSV with columns: year, tru  (annual) or year, quarter, tru (quarterly)")
        print("  then re-run this script to include TRU in the comparator panel.")


if __name__ == "__main__":
    generate()
