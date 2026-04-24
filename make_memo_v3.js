/**
 * make_memo_v3.js — WJSI Briefing Note, version 3
 *
 * Focus: quarterly WJSI variant.
 * Primary index table shows selected quarterly readings.
 * Annual series retained as reference for long-run comparisons.
 * No track-changes markup — clean final document.
 *
 * Run:  node make_memo_v3.js
 */

const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, HeadingLevel, BorderStyle, WidthType,
  ShadingType, PageNumber, PageBreak, TabStopType, TabStopPosition,
  LevelFormat,
} = require('docx');
const fs = require('fs');

// ── Colours ──────────────────────────────────────────────────────────────────
const NAVY  = "1F3864";
const SLATE = "44546A";
const RULE  = "BDD0E9";
const LIGHT = "EBF2FA";
const WHITE = "FFFFFF";
const GREEN = "1A5C3A";
const RED   = "7B1C1C";

// ── Text helpers ──────────────────────────────────────────────────────────────
function run(text, opts = {}) {
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

function sectionHead(text) {
  return new Paragraph({
    spacing: { before: 280, after: 80 },
    children: [new TextRun({
      text: text.toUpperCase(),
      font: "Arial", size: 20, bold: true, color: NAVY, characterSpacing: 40,
    })],
  });
}

function subHead(text) {
  return new Paragraph({
    spacing: { before: 180, after: 60 },
    children: [new TextRun({
      text,
      font: "Arial", size: 22, bold: true, color: SLATE,
    })],
  });
}

function body(text, opts = {}) {
  return new Paragraph({
    spacing: { before: 0, after: 140 },
    alignment: AlignmentType.JUSTIFIED,
    children: [run(text, opts)],
  });
}

function mixedPara(children, opts = {}) {
  return new Paragraph({
    spacing: { before: 0, after: 140 },
    alignment: opts.align || AlignmentType.JUSTIFIED,
    children,
  });
}

function smallSpace() {
  return new Paragraph({ spacing: { before: 0, after: 80 }, children: [] });
}

function callout(text) {
  return new Paragraph({
    spacing: { before: 120, after: 120 },
    indent: { left: 540, right: 540 },
    border: {
      left: { style: BorderStyle.SINGLE, size: 12, color: NAVY, space: 6 },
    },
    children: [new TextRun({ text, font: "Arial", size: 22, italics: true, color: SLATE })],
  });
}

// ── Table helpers ─────────────────────────────────────────────────────────────
const tBorder  = { style: BorderStyle.SINGLE, size: 1, color: "D0DEED" };
const tBorders = { top: tBorder, bottom: tBorder, left: tBorder, right: tBorder };
const hBorder  = { style: BorderStyle.NONE, size: 0, color: WHITE };
const hBorders = { top: hBorder, bottom: hBorder, left: hBorder, right: hBorder };

function hdrCell(text, width, align = AlignmentType.LEFT) {
  return new TableCell({
    borders: hBorders,
    width: { size: width, type: WidthType.DXA },
    shading: { fill: NAVY, type: ShadingType.CLEAR },
    margins: { top: 80, bottom: 80, left: 120, right: 120 },
    children: [new Paragraph({
      alignment: align,
      children: [new TextRun({ text, font: "Arial", size: 20, bold: true, color: WHITE })],
    })],
  });
}

function dataCell(text, width, isAlt, opts = {}) {
  return new TableCell({
    borders: tBorders,
    width: { size: width, type: WidthType.DXA },
    shading: { fill: isAlt ? LIGHT : WHITE, type: ShadingType.CLEAR },
    margins: { top: 80, bottom: 80, left: 120, right: 120 },
    children: [new Paragraph({
      alignment: opts.align || AlignmentType.LEFT,
      children: [new TextRun({
        text,
        font: "Arial", size: 20,
        bold: opts.bold || false,
        color: opts.color || "222222",
      })],
    })],
  });
}

// ── Quarterly index table ─────────────────────────────────────────────────────
function makeQuarterlyTable() {
  // [quarter_label, wjsi_q, wjsi_q_ma4, context, direction]
  // direction: 'n' neutral, 'd' down (bad), 'u' up (good)
  const rows = [
    ["2001 Q1",  "105.5", "106.2", "Pre-recession peak; labour market still strong",    "n"],
    ["2001 Q3",  "103.5", "104.0", "9/11 aftermath; index barely moves in Q3",           "d"],
    ["2005 Q2",  "100.0", "100.2", "Base-year reference quarter",                        "n"],
    ["2008 Q4",  " 94.6", " 94.7", "GFC onset; JOLTS deterioration begins",              "d"],
    ["2009 Q1",  " 85.6", " 91.3", "GFC trough — layoffs peak, quits collapse",          "d"],
    ["2019 Q4",  " 91.0", " 78.8", "Final pre-COVID reading",                            "n"],
    ["2020 Q1",  " 44.1", " 67.6", "COVID shock — quarter-on-quarter drop of 47 points", "d"],
    ["2020 Q2",  " 45.5", " 67.6", "Quarterly trough; annual average masks depth (54.2)","d"],
    ["2020 Q3",  " 89.9", " 67.9", "Rapid JOLTS rebound as economy reopens",             "u"],
    ["2021 Q4",  " 93.2", " 92.6", "Great Resignation peak; quits at all-time high",     "u"],
    ["2022 Q4",  " 83.4", " 84.1", "Post-resignation cooling begins; labour share erodes","d"],
    ["2023 Q4",  " 79.3", " 79.0", "Continued deterioration; below 2009 annual level",  "d"],
    ["2024 Q4",  " 75.7", " 79.3", "Most recent full-year end; lowest since GFC",        "d"],
    ["2025 Q4",  " 79.2", " 78.9", "Latest available reading",                           "n"],
  ];

  const colWidths = [1500, 950, 1050, 5860];

  return new Table({
    width: { size: 9360, type: WidthType.DXA },
    columnWidths: colWidths,
    rows: [
      // header
      new TableRow({ children: [
        hdrCell("Quarter",       colWidths[0]),
        hdrCell("WJSI-Q",        colWidths[1], AlignmentType.CENTER),
        hdrCell("4Q MA",         colWidths[2], AlignmentType.CENTER),
        hdrCell("Context",       colWidths[3]),
      ]}),
      // data
      ...rows.map((row, i) => {
        const isAlt = i % 2 === 0;
        const valColor = row[4] === 'd' ? RED : (row[4] === 'u' ? GREEN : NAVY);
        return new TableRow({ children: [
          dataCell(row[0], colWidths[0], isAlt),
          dataCell(row[1].trim(), colWidths[1], isAlt, { align: AlignmentType.CENTER, bold: true, color: valColor }),
          dataCell(row[2].trim(), colWidths[2], isAlt, { align: AlignmentType.CENTER, color: SLATE }),
          dataCell(row[3], colWidths[3], isAlt),
        ]});
      }),
    ],
  });
}

// ── Annual reference table ────────────────────────────────────────────────────
function makeAnnualRefTable() {
  const rows = [
    ["2001", "103.4", "Labour market holds through dot-com bust; labour share still elevated"],
    ["2005", "100.0", "Base year"],
    ["2009", " 81.2", "GFC annual average; quarterly trough (Q1) reaches 85.6"],
    ["2019", " 91.2", "Pre-COVID; incomplete recovery from GFC structural erosion"],
    ["2020", " 54.2", "Annual average masks quarterly trough of 45.5 in Q2"],
    ["2022", " 88.3", "Post-COVID partial recovery; labour share already declining"],
    ["2024", " 75.5", "Most recent full year; below 2009 trough on annual basis"],
  ];
  const colWidths = [1200, 950, 7210];
  return new Table({
    width: { size: 9360, type: WidthType.DXA },
    columnWidths: colWidths,
    rows: [
      new TableRow({ children: [
        hdrCell("Year",        colWidths[0]),
        hdrCell("WJSI (ann.)", colWidths[1], AlignmentType.CENTER),
        hdrCell("Note",        colWidths[2]),
      ]}),
      ...rows.map((row, i) => new TableRow({ children: [
        dataCell(row[0], colWidths[0], i % 2 === 0, { bold: true }),
        dataCell(row[1].trim(), colWidths[1], i % 2 === 0, { align: AlignmentType.CENTER, bold: true, color: NAVY }),
        dataCell(row[2], colWidths[2], i % 2 === 0),
      ]})),
    ],
  });
}

// ── Lead/lag table ────────────────────────────────────────────────────────────
function makeLeadLagTable() {
  const rows = [
    ["Annual WJSI (6-comp)", "Annual",    "−8 qtrs (2 yrs)", "r = 0.50, p = 0.015", "Granger F = 7.37, p = 0.014"],
    ["Quarterly WJSI",       "Quarterly", "−9 qtrs",         "r = 0.41, p < 0.001", "Consistent with annual finding"],
  ];
  const colWidths = [2000, 1200, 1600, 1800, 2760];
  return new Table({
    width: { size: 9360, type: WidthType.DXA },
    columnWidths: colWidths,
    rows: [
      new TableRow({ children: [
        hdrCell("Index",          colWidths[0]),
        hdrCell("Frequency",      colWidths[1]),
        hdrCell("Best lead lag",  colWidths[2], AlignmentType.CENTER),
        hdrCell("Pearson r / p",  colWidths[3], AlignmentType.CENTER),
        hdrCell("Note",           colWidths[4]),
      ]}),
      ...rows.map((row, i) => new TableRow({ children: [
        dataCell(row[0], colWidths[0], i % 2 === 0, { bold: true }),
        dataCell(row[1], colWidths[1], i % 2 === 0),
        dataCell(row[2], colWidths[2], i % 2 === 0, { align: AlignmentType.CENTER, bold: true, color: NAVY }),
        dataCell(row[3], colWidths[3], i % 2 === 0, { align: AlignmentType.CENTER }),
        dataCell(row[4], colWidths[4], i % 2 === 0),
      ]})),
    ],
  });
}

// ── Component table ───────────────────────────────────────────────────────────
function makeComponentTable() {
  const rows = [
    ["Union membership rate",         "BLS CPS, 1983–present (annual)",        "Annual → quarterly: linear interpolation, anchored Q2 each year",      "Structural protection"],
    ["JOLTS quits rate",              "BLS JOLTS, 2001–present (monthly)",     "Monthly → quarterly average",                                          "Worker bargaining power"],
    ["JOLTS layoffs rate (inv.)",     "BLS JOLTS, 2001–present (monthly)",     "Monthly → quarterly average, inverted",                                "Employer-side risk"],
    ["Nonfarm labour share",          "BLS PRS85006173, 1947–present (qtrly)", "Native quarterly; no aggregation needed",                              "Aggregate income distribution"],
    ["Median job tenure",             "BLS tenure supplement (biennial)",      "Biennial (odd years) → quarterly: linear interpolation, anchored Q1",  "Employment stability"],
    ["JOLTS job openings rate (inv.)", "BLS JOLTS, 2001–present (monthly)",    "Monthly → quarterly average, inverted",                                "Churn / competition risk"],
  ];
  const colWidths = [2100, 2300, 2960, 2000];
  return new Table({
    width: { size: 9360, type: WidthType.DXA },
    columnWidths: colWidths,
    rows: [
      new TableRow({ children: [
        hdrCell("Component",          colWidths[0]),
        hdrCell("Source & frequency", colWidths[1]),
        hdrCell("Quarterly treatment",colWidths[2]),
        hdrCell("Captures",           colWidths[3]),
      ]}),
      ...rows.map((row, i) => new TableRow({ children: row.map((cell, j) =>
        dataCell(cell, colWidths[j], i % 2 === 0)
      )})),
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
            new TextRun({ text: "WORKER JOB SECURITY INDEX — QUARTERLY", font: "Arial", size: 18, bold: true, color: NAVY, characterSpacing: 40 }),
            new TextRun({ text: "\tPRELIMINARY — FOR DISCUSSION", font: "Arial", size: 18, color: SLATE, characterSpacing: 20 }),
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
            new TextRun({ text: "Data: BLS, FRED & Minneapolis Fed. Code: github.com/amiasmg/worker-job-security-index  April 2026", font: "Arial", size: 16, color: "888888" }),
            new TextRun({ text: "\tPage ", font: "Arial", size: 16, color: "888888" }),
            new TextRun({ children: [PageNumber.CURRENT], font: "Arial", size: 16, color: "888888" }),
          ],
        })],
      }),
    },
    children: [

      // ── TITLE ─────────────────────────────────────────────────────────────
      new Paragraph({
        spacing: { before: 80, after: 40 },
        children: [new TextRun({ text: "Worker Job Security Index (WJSI)", font: "Arial", size: 40, bold: true, color: NAVY })],
      }),
      new Paragraph({
        spacing: { before: 0, after: 60 },
        children: [new TextRun({ text: "Quarterly Variant: Same Components, Higher Frequency", font: "Arial", size: 26, color: SLATE, italics: true })],
      }),
      new Paragraph({
        spacing: { before: 0, after: 80 },
        children: [new TextRun({ text: "Version 3  —  April 2026  —  Preliminary, for discussion", font: "Arial", size: 20, color: "888888", italics: true })],
      }),
      rule(),

      // ── EXECUTIVE SUMMARY ─────────────────────────────────────────────────
      sectionHead("Executive Summary"),

      body("The Worker Job Security Index is now available at quarterly frequency. Using the same six components as the annual index, the quarterly variant reaches into sub-annual deteriorations that annual averaging conceals — most starkly, the COVID shock in 2020 Q2 (WJSI-Q: 45.5 vs. the annual average of 54.2) and the onset of the Great Resignation recovery in 2020 Q3 (89.9, within a single quarter of reopening)."),

      body("The quarterly index preserves the leading-indicator property of the annual series. WJSI-Q leads the University of Michigan Consumer Sentiment Index by nine quarters (r = 0.41, p < 0.001), consistent with the annual two-year lead (eight quarters). The structural components — union membership and median tenure — are linearly interpolated from annual and biennial observations respectively; their inclusion maintains the index's forward-looking character compared to a JOLTS-only quarterly composite."),

      callout("Key reading: WJSI-Q at 2025 Q4 = 79.2 (4Q MA: 78.9). The index has been below its 2005 base of 100 continuously since 2015 Q1 — a decade of structural job security deterioration."),

      rule(),

      // ── 1. MOTIVATION FOR QUARTERLY ──────────────────────────────────────
      sectionHead("1.  Why Quarterly?"),

      body("Annual averaging is appropriate for tracking long-run structural trends — the gradual decline in union membership, the secular erosion of labour's income share, the multi-year arc of tenure change. But policymakers and institutional users operate on shorter cycles. Quarterly data enables three capabilities that annual data cannot support:"),

      new Paragraph({
        spacing: { before: 60, after: 60 },
        indent: { left: 360 },
        children: [run("First, ", { bold: true }), run("turning-point detection. The annual 2020 index of 54.2 masks a quarterly trough of 45.5 and an equally rapid recovery to 89.9 — all within twelve months. Annual data assigns a single value to a year that saw a 47-point intra-year swing.")],
      }),
      new Paragraph({
        spacing: { before: 60, after: 60 },
        indent: { left: 360 },
        children: [run("Second, ", { bold: true }), run("policy timing. A nine-quarter lead on consumer sentiment means the quarterly index provides an actionable signal roughly two-and-a-quarter years before deteriorating confidence registers in household survey data — a window that annual data can only approximate.")],
      }),
      new Paragraph({
        spacing: { before: 60, after: 80 },
        indent: { left: 360 },
        children: [run("Third, ", { bold: true }), run("alignment with other quarterly releases. The JOLTS program, BLS Productivity and Costs (which underpins the labour share series), GDP, and the Federal Reserve's Summary of Economic Projections all operate on a quarterly calendar. A quarterly WJSI can be updated and published alongside these releases.")],
      }),

      rule(),

      // ── 2. METHODOLOGY ────────────────────────────────────────────────────
      sectionHead("2.  Methodology"),

      subHead("2.1  Component set"),

      body("The quarterly index uses the same six components as the annual index. No components are dropped; no substitutions are made. The methodological question is how to bring each component to quarterly frequency. Three treatments apply, depending on source cadence:"),

      smallSpace(),
      makeComponentTable(),
      smallSpace(),

      body("The part-time-for-economic-reasons rate (PTER) was considered and excluded in both annual and quarterly specifications. Its correlation with U-6 (r = 0.81 in annual data) establishes structural redundancy. The quarterly WJSI is therefore genuinely differentiated from standard underemployment measures."),

      subHead("2.2  Interpolation of slow-moving structural series"),

      body("Two components — union membership (annual, CPS) and median job tenure (biennial, BLS tenure supplement) — require interpolation to reach quarterly frequency. The approach is deliberately conservative:"),

      new Paragraph({
        spacing: { before: 60, after: 60 },
        indent: { left: 360 },
        children: [
          run("Union rate: ", { bold: true }),
          run("Each annual observation is treated as the value at Q2 of its survey year (the calendar midpoint of the BLS reporting year). Linear interpolation fills the three adjacent quarters; endpoint quarters are held flat at the nearest observed value. This introduces no artificial cyclicality — the union rate moves only on the linear trend between known annual anchors."),
        ],
      }),
      new Paragraph({
        spacing: { before: 60, after: 80 },
        indent: { left: 360 },
        children: [
          run("Median tenure: ", { bold: true }),
          run("Biennial observations (published in odd years) are anchored at Q1 of each survey year. Linear interpolation over the eight-quarter gap between observations is the only defensible approach given the data cadence; the interpolated series is flagged in the output CSV. The smooth interpolation is appropriate because tenure is a genuinely slow-moving structural variable — it reflects multi-year hiring and retention patterns, not quarter-to-quarter cycles."),
        ],
      }),

      body("The effect of interpolation on the index is bounded. Because z-scores are computed over each component's full history, the linear interpolation of union and tenure produces gradual drift in their z-scores between anchor years — not artificial volatility. The JOLTS components (openings, quits, layoffs) and the natively quarterly labour share series carry all the cyclical responsiveness."),

      subHead("2.3  Construction"),

      body("Z-scores are computed over each component's full available quarterly history. Directional alignment is identical to the annual specification: layoffs, openings, and PTER (excluded) are inverted; union, quits, tenure, and labour share are positive. The equal-weighted composite is shifted so its minimum equals 1.0, then indexed so the average of 2005 Q1–Q4 equals 100. A four-quarter centred moving average (4Q MA) is published alongside the unsmoothed quarterly series."),

      rule(),

      // ── 3. KEY READINGS ───────────────────────────────────────────────────
      sectionHead("3.  Key Quarterly Readings"),

      body("The table below presents selected quarters at turning points and dates of institutional interest. Red values indicate readings below the prior-year level or a significant cyclical trough; green indicates recovery readings. The 4Q MA column is recommended for trend assessment; the unsmoothed WJSI-Q is better for detecting turning-point timing."),

      smallSpace(),
      makeQuarterlyTable(),
      smallSpace(),

      body("Three features of the quarterly series deserve emphasis:"),

      mixedPara([
        run("COVID depth and speed. ", { bold: true, color: NAVY }),
        run("The index fell 47 points in a single quarter (Q4 2019 → Q1 2020: 91.0 → 44.1) and recovered 45 points within two quarters (Q2 2020 → Q3 2020: 45.5 → 89.9). No annual index can render this arc. Annual averaging assigns the year 2020 a value of 54.2 — which is technically accurate but structurally misleading, as it conflates the trough with an already-substantial partial recovery."),
      ]),

      mixedPara([
        run("Post-2022 deterioration is sharper than the annual series suggests. ", { bold: true, color: NAVY }),
        run("The quarterly index peaked at 93.2 (Q4 2021) and had fallen to 75.7 by Q4 2024 — a decline of 17.5 index points in three years. The annual series shows a decline from 88.3 to 75.5 over the same window, which is less alarming only because the annual baseline was already lower."),
      ]),

      mixedPara([
        run("The 2009 trough is shallower in quarterly than in the JOLTS-only variants. ", { bold: true, color: NAVY }),
        run("The JOLTS-only monthly composite (Variant B) troughs at 65.4 in Q2 2009. The full six-component quarterly WJSI troughs at 85.6 in Q1 2009. This reflects the stabilising role of union membership and labour share during the GFC: both series declined only gradually during the financial crisis, moderating the composite's cyclical fall. Whether this is a feature (the index correctly reflects partial structural resilience) or a limitation (the index understates JOLTS-measured deterioration) is a design question."),
      ]),

      new Paragraph({ children: [new PageBreak()] }),

      // ── 4. ANNUAL REFERENCE ───────────────────────────────────────────────
      sectionHead("4.  Annual Index for Reference"),

      body("The annual WJSI remains the preferred series for structural trend analysis and for comparisons across the full 2001–2025 sample. For publication purposes, the two series are designed to be complementary: the annual index for long-run framing, the quarterly index for timely monitoring."),

      smallSpace(),
      makeAnnualRefTable(),
      smallSpace(),

      body("Note that the annual and quarterly values are not directly comparable at individual points because their z-score normalisation is computed separately. The annual index uses annual-average z-scores; the quarterly index uses quarterly z-scores computed over the full quarterly history. Both use 2005 = 100 as the reference level. The general direction and relative magnitude of readings are consistent across the two series."),

      rule(),

      // ── 5. LEAD / LAG ─────────────────────────────────────────────────────
      sectionHead("5.  Lead / Lag: Quarterly WJSI vs. Consumer Sentiment"),

      body("The leading-indicator property that motivates the annual WJSI is preserved — and strengthened — in the quarterly specification. Testing WJSI-Q against the University of Michigan Consumer Sentiment Index at quarterly frequency across lags from −12 to +12 quarters:"),

      smallSpace(),
      makeLeadLagTable(),
      smallSpace(),

      body("The best lead is nine quarters (r = 0.41, p < 0.001), consistent with but slightly longer than the annual two-year (eight-quarter) finding. The entire WJSI-leads region (lags −12 through −1) is positive and significant, with the correlation rising monotonically from lag −12 through lag −9 before declining — suggesting a sustained predictive window of one-to-three years rather than a single sharp lead point."),

      body("The structural interpretation is unchanged: deteriorating job security precedes deteriorating consumer confidence. The quarterly series confirms that this relationship is not an artefact of annual averaging and holds at a resolution directly comparable to the quarterly Sentiment release cycle."),

      callout("Practical implication: a reading of 78.9 (4Q MA at 2025 Q4) implies that, under the post-GFC lead relationship, consumer sentiment is likely to remain under structural pressure through 2027 Q1 absent a meaningful reversal in the underlying components."),

      rule(),

      // ── 6. WHAT THE INDEX DOES NOT CAPTURE ───────────────────────────────
      sectionHead("6.  Scope and Limitations"),

      body("The quarterly WJSI inherits the limitations of the annual specification and adds one interpolation-specific caveat:"),

      new Paragraph({
        spacing: { before: 60, after: 60 },
        indent: { left: 360 },
        children: [run("Intra-year dynamics of union and tenure are unobserved. ", { bold: true }), run("Linear interpolation between annual union anchors and biennial tenure anchors means the quarterly index cannot detect within-year inflection points in these series. If union membership fell sharply in a single quarter — which the CPS would not capture anyway — the quarterly WJSI would miss it. Users should interpret the union and tenure contributions as smooth trend estimates, not genuine quarterly observations.")],
      }),
      new Paragraph({
        spacing: { before: 60, after: 60 },
        indent: { left: 360 },
        children: [run("JOLTS data vintage lag. ", { bold: true }), run("JOLTS estimates are subject to revision, and the preliminary release lags by approximately three to four weeks. Quarterly WJSI readings for the most recent quarter should therefore be treated as provisional pending the final JOLTS revision.")],
      }),
      new Paragraph({
        spacing: { before: 60, after: 80 },
        indent: { left: 360 },
        children: [run("Labour share is released with a longer lag. ", { bold: true }), run("BLS PRS85006173 (nonfarm business labour share) is a Productivity and Costs release, published approximately 60 days after the reference quarter. The quarterly WJSI for a given quarter is therefore not fully computable until roughly two months after quarter-end; preliminary estimates can be produced using the prior quarter's labour share.")],
      }),

      body("None of these limitations affect the structural validity of the index. They are operational constraints relevant to real-time publication, not to retrospective analysis."),

      rule(),

      // ── 7. NEXT STEPS ─────────────────────────────────────────────────────
      sectionHead("7.  Next Steps"),

      body("Three workstreams remain before public release of the quarterly series:"),

      new Paragraph({
        spacing: { before: 60, after: 60 },
        indent: { left: 360 },
        children: [run("Openings sign convention. ", { bold: true }), run("The quarterly series uses the same sign convention as the annual index (high openings = mild negative, reflecting churn risk). This convention is theoretically contestable — high openings can also signal worker-friendly tight labour markets — and sensitivity tests show meaningful quantitative impact on the post-2020 trajectory. External review by labour economists is the single most important near-term methodological step.")],
      }),
      new Paragraph({
        spacing: { before: 60, after: 60 },
        indent: { left: 360 },
        children: [run("Health insurance coverage. ", { bold: true }), run("Employer-sponsored health insurance coverage was identified as the most promising seventh component. It has genuine semi-structural dynamics (declining 1999–2010, stabilising post-ACA 2014) not present in any current component. Data construction from Kaiser Family Foundation / KFF Employer Health Benefits Survey or CPS ASEC would be needed; no continuous quarterly FRED series exists.")],
      }),
      new Paragraph({
        spacing: { before: 60, after: 80 },
        indent: { left: 360 },
        children: [run("Institutional partnership. ", { bold: true }), run("The quarterly WJSI is designed for co-publication with LISEP's True Rate of Unemployment (TRU). WJSI measures the structural security of employment held; TRU measures the adequacy of employment available. Together they provide a more complete picture of American workers' labour market position than either measure alone. A joint quarterly release — calibrated to the monthly BLS Employment Situation cycle — would maximise institutional impact.")],
      }),

      rule(),

      new Paragraph({
        spacing: { before: 80, after: 0 },
        alignment: AlignmentType.CENTER,
        children: [new TextRun({
          text: "All findings are preliminary. This note is prepared for discussion purposes only.",
          font: "Arial", size: 18, italics: true, color: "888888",
        })],
      }),

    ],
  }],
});

Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync("/Users/Amias/WorkerSecurityIndex/WJSI_Briefing_Note_v3.docx", buf);
  console.log("Written: /Users/Amias/WorkerSecurityIndex/WJSI_Briefing_Note_v3.docx");
});
