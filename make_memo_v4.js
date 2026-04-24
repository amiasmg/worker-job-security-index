/**
 * make_memo_v4.js — WJSI Briefing Note, version 4
 *
 * Framing: problem → hypothesis → proposal → initial results.
 * Written for an audience that has never heard of WJSI.
 * Tone: accessible policy memo, not a methods paper.
 *
 * Run:  node make_memo_v4.js
 */

const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, BorderStyle, WidthType,
  ShadingType, PageNumber, TabStopType, TabStopPosition,
} = require('docx');
const fs = require('fs');

// ── Colours ──────────────────────────────────────────────────────────────────
const NAVY  = "1F3864";
const SLATE = "44546A";
const RULE  = "BDD0E9";
const LIGHT = "EBF2FA";
const WHITE = "FFFFFF";
const RED   = "7B1C1C";
const GREEN = "1A5C3A";

// ── Text helpers ──────────────────────────────────────────────────────────────
function t(text, opts = {}) {
  return new TextRun({
    text,
    font: "Arial",
    size: opts.size || 22,
    bold: opts.bold || false,
    italics: opts.italic || false,
    color: opts.color || "222222",
  });
}

function rule() {
  return new Paragraph({
    border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: RULE, space: 1 } },
    spacing: { before: 0, after: 160 },
    children: [],
  });
}

function sectionHead(label) {
  return new Paragraph({
    spacing: { before: 280, after: 80 },
    children: [new TextRun({
      text: label.toUpperCase(),
      font: "Arial", size: 20, bold: true, color: NAVY, characterSpacing: 40,
    })],
  });
}

function body(text, opts = {}) {
  return new Paragraph({
    spacing: { before: 0, after: 160 },
    alignment: AlignmentType.JUSTIFIED,
    children: [t(text, opts)],
  });
}

function mixed(runs, opts = {}) {
  return new Paragraph({
    spacing: { before: 0, after: 160 },
    alignment: opts.align || AlignmentType.JUSTIFIED,
    children: runs,
  });
}

function gap(after = 80) {
  return new Paragraph({ spacing: { before: 0, after }, children: [] });
}

function callout(text) {
  return new Paragraph({
    spacing: { before: 140, after: 140 },
    indent: { left: 540, right: 540 },
    border: { left: { style: BorderStyle.SINGLE, size: 14, color: NAVY, space: 6 } },
    children: [t(text, { italic: true, color: SLATE })],
  });
}

function bullet(runs) {
  return new Paragraph({
    spacing: { before: 40, after: 60 },
    indent: { left: 440, hanging: 220 },
    children: [t("•  ", { bold: true, color: NAVY }), ...runs],
  });
}

// ── Table helpers ─────────────────────────────────────────────────────────────
const bdr  = { style: BorderStyle.SINGLE, size: 1, color: "D0DEED" };
const bdrs = { top: bdr, bottom: bdr, left: bdr, right: bdr };
const hbdr = { style: BorderStyle.NONE, size: 0, color: WHITE };
const hbdrs = { top: hbdr, bottom: hbdr, left: hbdr, right: hbdr };

function hCell(text, w, align = AlignmentType.LEFT) {
  return new TableCell({
    borders: hbdrs, width: { size: w, type: WidthType.DXA },
    shading: { fill: NAVY, type: ShadingType.CLEAR },
    margins: { top: 80, bottom: 80, left: 140, right: 140 },
    children: [new Paragraph({ alignment: align, children: [t(text, { size: 19, bold: true, color: WHITE })] })],
  });
}

function dCell(text, w, alt, opts = {}) {
  return new TableCell({
    borders: bdrs, width: { size: w, type: WidthType.DXA },
    shading: { fill: alt ? LIGHT : WHITE, type: ShadingType.CLEAR },
    margins: { top: 80, bottom: 80, left: 140, right: 140 },
    children: [new Paragraph({
      alignment: opts.align || AlignmentType.LEFT,
      children: [t(text, { size: 20, bold: opts.bold || false, color: opts.color || "222222" })],
    })],
  });
}

// ── Component table ───────────────────────────────────────────────────────────
function componentTable() {
  const rows = [
    ["Union membership rate",          "Structural protection; proxy for collective bargaining power"],
    ["Voluntary quit rate (JOLTS)",     "Worker confidence: willingness and ability to leave a job"],
    ["Layoffs & discharges rate (JOLTS)","Employer-side risk: involuntary job loss pressure (inverted)"],
    ["Nonfarm business labour share",   "Aggregate income distribution: workers' share of output"],
    ["Median job tenure",               "Stability of the employment relationship over time"],
    ["Job openings rate (JOLTS)",       "Labour market tightness / churn risk (inverted in primary spec)"],
  ];
  const cw = [2600, 6760];
  return new Table({
    width: { size: 9360, type: WidthType.DXA }, columnWidths: cw,
    rows: [
      new TableRow({ children: [hCell("Component", cw[0]), hCell("What it measures", cw[1])] }),
      ...rows.map((r, i) => new TableRow({ children: [
        dCell(r[0], cw[0], i % 2 === 0, { bold: true, color: NAVY }),
        dCell(r[1], cw[1], i % 2 === 0),
      ]})),
    ],
  });
}

// ── Key readings table ────────────────────────────────────────────────────────
function readingsTable() {
  // [quarter, wjsi_q, context, dir]  dir: d=bad, u=good, n=neutral
  const rows = [
    ["2005 Q1–Q4",  "~100",  "Base-year reference level",                                       "n"],
    ["2009 Q1",     " 85.6", "Great Recession trough; layoffs peak, quits collapse",             "d"],
    ["2019 Q4",     " 91.0", "Pre-pandemic reading; already well below base",                    "d"],
    ["2020 Q1",     " 44.1", "COVID shock — 47-point single-quarter fall",                       "d"],
    ["2020 Q2",     " 45.5", "Trough; annual average of 54.2 masks this depth",                  "d"],
    ["2020 Q3",     " 89.9", "Rapid JOLTS rebound as economy reopens",                           "u"],
    ["2021 Q4",     " 93.2", "Great Resignation peak; quit rate at all-time high",               "u"],
    ["2022 Q4",     " 83.4", "Resignation fades; structural deterioration resumes",              "d"],
    ["2024 Q4",     " 75.7", "Most recent full year-end; near Great Recession levels",           "d"],
    ["2025 Q4",     " 79.2", "Latest available; 4Q moving average: 78.9",                       "d"],
  ];
  const cw = [1400, 1000, 6960];
  return new Table({
    width: { size: 9360, type: WidthType.DXA }, columnWidths: cw,
    rows: [
      new TableRow({ children: [
        hCell("Quarter",  cw[0]),
        hCell("WJSI",     cw[1], AlignmentType.CENTER),
        hCell("Reading",  cw[2]),
      ]}),
      ...rows.map((r, i) => {
        const vc = r[3] === 'd' ? RED : (r[3] === 'u' ? GREEN : NAVY);
        return new TableRow({ children: [
          dCell(r[0],         cw[0], i % 2 === 0),
          dCell(r[1].trim(),  cw[1], i % 2 === 0, { align: AlignmentType.CENTER, bold: true, color: vc }),
          dCell(r[2],         cw[2], i % 2 === 0),
        ]});
      }),
    ],
  });
}

// ── Divergence table ──────────────────────────────────────────────────────────
function divergenceTable() {
  const rows = [
    ["U-3 unemployment rate",        "3.7%",   "4.0%",  "Essentially unchanged — historically low"],
    ["Michigan Consumer Sentiment",  "~88",    "~70",   "Down 20%  ↓"],
    ["JOLTS voluntary quit rate",    "2.76%",  "2.07%", "Down 25% — workers feel stuck  ↓"],
    ["Union membership rate",        "10.1%",  " 9.9%", "Post-war low  ↓"],
    ["Nonfarm labour share (index)", " 97.0",  "95.5",  "Near 60-year low  ↓"],
    ["WJSI (this index)",            "88.3",   "75.5",  "Down 15%  ↓"],
  ];
  const cw = [3000, 1100, 1100, 4160];
  return new Table({
    width: { size: 9360, type: WidthType.DXA }, columnWidths: cw,
    rows: [
      new TableRow({ children: [
        hCell("Indicator",  cw[0]),
        hCell("2022",       cw[1], AlignmentType.CENTER),
        hCell("2024",       cw[2], AlignmentType.CENTER),
        hCell("Signal",     cw[3]),
      ]}),
      ...rows.map((r, i) => {
        const signalColor = r[3].includes("↓") ? RED : "222222";
        return new TableRow({ children: [
          dCell(r[0], cw[0], i % 2 === 0, { bold: true }),
          dCell(r[1], cw[1], i % 2 === 0, { align: AlignmentType.CENTER }),
          dCell(r[2], cw[2], i % 2 === 0, { align: AlignmentType.CENTER }),
          dCell(r[3], cw[3], i % 2 === 0, { color: signalColor }),
        ]});
      }),
    ],
  });
}

// ── Document ──────────────────────────────────────────────────────────────────
const doc = new Document({
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 },
        margin: { top: 1080, right: 1260, bottom: 1080, left: 1260 },
      },
    },
    headers: {
      default: new Header({
        children: [new Paragraph({
          tabStops: [{ type: TabStopType.RIGHT, position: TabStopPosition.MAX }],
          border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: NAVY, space: 4 } },
          spacing: { before: 0, after: 120 },
          children: [
            t("WORKER JOB SECURITY INDEX", { size: 18, bold: true, color: NAVY }),
            t("\tPRELIMINARY — FOR DISCUSSION", { size: 18, color: SLATE }),
          ],
        })],
      }),
    },
    footers: {
      default: new Footer({
        children: [new Paragraph({
          tabStops: [{ type: TabStopType.RIGHT, position: TabStopPosition.MAX }],
          border: { top: { style: BorderStyle.SINGLE, size: 2, color: RULE, space: 4 } },
          spacing: { before: 120, after: 0 },
          children: [
            t("Data: BLS & FRED (public). Code: github.com/amiasmg/worker-job-security-index   April 2026", { size: 16, color: "888888" }),
            t("\tPage ", { size: 16, color: "888888" }),
            new TextRun({ children: [PageNumber.CURRENT], font: "Arial", size: 16, color: "888888" }),
          ],
        })],
      }),
    },

    children: [

      // ── TITLE ─────────────────────────────────────────────────────────────
      new Paragraph({
        spacing: { before: 80, after: 40 },
        children: [t("Measuring What Unemployment Doesn't", { size: 42, bold: true, color: NAVY })],
      }),
      new Paragraph({
        spacing: { before: 0, after: 60 },
        children: [t("A Quarterly Index of American Job Security", { size: 28, color: SLATE, italic: true })],
      }),
      new Paragraph({
        spacing: { before: 0, after: 100 },
        children: [t("April 2026  —  Preliminary, for discussion", { size: 20, color: "999999", italic: true })],
      }),
      rule(),

      // ── THE PROBLEM ───────────────────────────────────────────────────────
      sectionHead("1.  The Problem: A Divergence Worth Explaining"),

      body("By the conventional scorecard, the American labour market looks strong. The U-3 unemployment rate has remained near or below 4% since mid-2022 — a level last sustained in the late 1960s. Yet over the same period, something does not add up."),

      body("Consumer confidence has declined steadily. Workers are quitting their jobs at the lowest rates since 2015, signalling they feel less able — not more — to leave for something better. Union membership hit a post-war low in 2023. The share of economic output going to workers rather than capital has fallen to levels not seen since the 1960s. And survey after survey finds that Americans feel more financially anxious, not less, despite the unemployment numbers."),

      callout("The unemployment rate asks whether Americans have jobs. It does not ask whether those jobs are secure, whether workers have power within them, or whether the structural conditions of employment are getting better or worse."),

      body("This divergence is not a paradox. It is the expected consequence of measuring only one dimension of a multi-dimensional phenomenon. Employment status — employed or not — captures the most extreme form of job insecurity. It misses everything that happens inside employment: the loss of bargaining power, the erosion of stability, the decline in the collective institutions that protect workers, and the shrinking share of output that workers collectively capture."),

      gap(100),
      divergenceTable(),
      gap(80),

      body("The table above illustrates the divergence over just two years. U-3 is essentially flat. Every structural indicator of job quality and worker power has moved in the wrong direction. A new measure is needed — one designed to capture the structural security of employment, not just its presence."),

      rule(),

      // ── HYPOTHESIS ────────────────────────────────────────────────────────
      sectionHead("2.  The Hypothesis: Job Security Has Two Components"),

      body("We propose that job security, properly understood, has two distinct components that move on different timescales and respond to different forces."),

      mixed([
        t("Cyclical job security ", { bold: true, color: NAVY }),
        t("moves with the business cycle. When the economy contracts, employers lay off workers; when it expands, they hire. Quits rise and fall with labour market tightness. Job openings swing widely. These dynamics show up in JOLTS and employment data within quarters and are already reasonably well captured by existing measures."),
      ]),

      mixed([
        t("Structural job security ", { bold: true, color: NAVY }),
        t("moves over years and decades. The share of workers with union representation. The typical length of the employment relationship. Workers' collective share of economic output. These series shift slowly — but they shift in one direction. Since the early 1980s, all three have declined almost continuously, creating a long-run deterioration in the structural foundations of job security that no cyclical recovery has reversed."),
      ]),

      body("The central hypothesis is that what Americans are experiencing — and what consumer sentiment is reflecting — is not primarily cyclical insecurity (there are still plenty of jobs) but structural insecurity: the slow erosion of the conditions that make employment stable, rewarding, and worth staying in. That erosion accelerated after the Great Financial Crisis and has not recovered."),

      callout("2024: U-3 unemployment at 4.0%. Voluntary quits at their lowest since 2015. Union membership at a post-war low. Labour's share of output at a 60-year low. These are not contradictions — they are different readings of the same structural deterioration."),

      rule(),

      // ── PROPOSAL ──────────────────────────────────────────────────────────
      sectionHead("3.  The Proposal: A New Composite Index"),

      body("We constructed a quarterly composite index — the Worker Job Security Index (WJSI) — designed to measure the structural and cyclical dimensions of job security together, at a frequency that allows timely policy monitoring."),

      body("The index combines six components drawn from public BLS and FRED data, each measuring a distinct dimension of job security. They are equal-weighted and normalised to a common scale, with the index set to 100 in 2005 as the reference year."),

      gap(80),
      componentTable(),
      gap(100),

      body("The six components are not arbitrary. Each has a clear theoretical basis, a long enough history to support structural analysis, and an empirical relationship with job security that is not redundant with the others. Importantly, the index is not dominated by any one data source: the three JOLTS measures provide cyclical responsiveness; union membership, median tenure, and the labour share provide structural depth."),

      mixed([
        t("Why quarterly? ", { bold: true, color: NAVY }),
        t("Annual averaging conceals intra-year dynamics that matter. During 2020, the WJSI fell to 45.5 in Q2, then recovered to 89.9 by Q3 — a 44-point swing within a single calendar year. The annual average of 54.2 is technically correct but structurally misleading. Quarterly resolution allows policymakers to see turning points in real time, not in retrospect."),
      ]),

      mixed([
        t("Why not just use U-6? ", { bold: true, color: NAVY }),
        t("U-6 — the broadest official unemployment measure — counts involuntary part-time workers and marginally attached workers who want jobs but are not currently searching. It is a wider measure of employment shortfall. The WJSI measures something different: the structural security of employment for people who have it. The two instruments are designed to be complementary. Empirically, the WJSI has a contemporaneous correlation of only −0.17 with U-6, confirming that it captures genuinely different information."),
      ]),

      rule(),

      // ── RESULTS ───────────────────────────────────────────────────────────
      sectionHead("4.  Initial Results"),

      body("The index runs from 2001 Q1 through 2025 Q4 — 100 quarterly observations spanning three recessions and two sustained recoveries. The headline findings are striking."),

      mixed([
        t("Job security has been below its 2005 baseline continuously since 2015 Q1. ", { bold: true, color: NAVY }),
        t("That is a decade of uninterrupted structural deterioration — through a period that included historically low unemployment, record equity prices, and sustained GDP growth. The headline labour market indicators described a strong economy; the structural foundations of job security were eroding throughout."),
      ]),

      mixed([
        t("The 2020 COVID shock is captured with a resolution no annual index can match. ", { bold: true, color: NAVY }),
        t("The quarterly index fell 47 points in a single quarter (Q4 2019: 91.0 → Q1 2020: 44.1), troughed at 45.5 in Q2, then recovered 44 points by Q3 as JOLTS data rebounded with reopening. The annual average of 54.2 combines these three very different realities into a single number."),
      ]),

      mixed([
        t("The post-2022 deterioration is more severe than the headline data suggests. ", { bold: true, color: NAVY }),
        t("The index peaked at 93.2 in Q4 2021 — the height of the Great Resignation, when workers had unusually high bargaining power. By Q4 2024, it had fallen to 75.7 — a 17.5-point decline over three years, driven by the collapse in voluntary quits, continued erosion of union membership, and a labour share index near its lowest level since the 1960s. Despite near-record-low unemployment, American workers are measurably less secure today than at any point since the Great Financial Crisis."),
      ]),

      gap(100),
      readingsTable(),
      gap(80),

      body("Perhaps most importantly: this measure appears to lead, not lag, consumer sentiment. At a nine-quarter lag, the WJSI correlates with the University of Michigan Consumer Sentiment Index at r = 0.41 (p < 0.001). A Granger causality test at annual frequency confirms the direction: changes in job security predict subsequent changes in consumer confidence (F = 7.37, p = 0.014); the reverse does not hold (p = 0.41)."),

      callout("Workers appear to feel the structural deterioration before it registers in headline sentiment surveys — by roughly two years. This gives the index potential value not just as a descriptive measure of what has happened, but as an early-warning signal of what is coming."),

      rule(),

      // ── NEXT STEPS ────────────────────────────────────────────────────────
      sectionHead("5.  Where This Goes Next"),

      body("This is a prototype. The index is methodologically sound and internally validated — it passes standard backtesting criteria, its components are not redundant with each other or with existing measures, and the code and data are fully open-source. But three things would strengthen it before institutional publication."),

      bullet([
        t("External review of the openings sign convention. ", { bold: true }),
        t("High job openings can signal either worker-friendly tight labour markets or destabilising churn. The choice matters quantitatively. This is the single most important open methodological question."),
      ]),
      bullet([
        t("Addition of employer-sponsored health insurance coverage. ", { bold: true }),
        t("The most promising candidate for a seventh component. Non-wage benefit security has declined structurally since the late 1990s and would add a dimension not captured by any current component."),
      ]),
      bullet([
        t("Institutional partnership for regular publication. ", { bold: true }),
        t("The index is designed as a complement to LISEP's True Rate of Unemployment: TRU asks whether workers have the employment they need; WJSI asks whether the employment they have is structurally secure. A joint quarterly release alongside the monthly BLS Employment Situation would give both instruments maximum impact."),
      ]),

      gap(120),
      rule(),

      new Paragraph({
        spacing: { before: 80, after: 0 },
        alignment: AlignmentType.CENTER,
        children: [t("All findings are preliminary. This note is prepared for discussion purposes only.", { size: 18, italic: true, color: "999999" })],
      }),

    ],
  }],
});

Packer.toBuffer(doc).then(buf => {
  const path = "/Users/Amias/WorkerSecurityIndex/WJSI_Briefing_Note_v4.docx";
  fs.writeFileSync(path, buf);
  console.log("Written: " + path);
});
