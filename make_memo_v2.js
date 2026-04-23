/**
 * make_memo_v2.js — WJSI Briefing Note, version 2
 *
 * Shows track changes vs. v1 (5-component → 6-component index).
 * Red strikethrough = deleted, blue underline = inserted (standard Word convention).
 *
 * Run:  node make_memo_v2.js
 */

const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, HeadingLevel, BorderStyle, WidthType,
  ShadingType, PageNumber, PageBreak, TabStopType, TabStopPosition,
  LevelFormat, InsertedTextRun, DeletedTextRun,
} = require('docx');
const fs = require('fs');

// ── Colours ──────────────────────────────────────────────────────────────────
const NAVY   = "1F3864";
const SLATE  = "44546A";
const RULE   = "BDD0E9";
const LIGHT  = "EBF2FA";
const WHITE  = "FFFFFF";
const NEWBLUE = "1B4F8A";  // highlight colour for inserts in tables

const AUTHOR = "Amias Gerety";
const DATE   = "2026-04-23T00:00:00Z";

// ── Track-change helpers ──────────────────────────────────────────────────────
function ins(text, opts = {}) {
  return new InsertedTextRun({
    text,
    author: AUTHOR,
    date: DATE,
    font: "Arial",
    size: opts.size || 22,
    bold: opts.bold || false,
    italics: opts.italic || false,
    color: opts.color || "222222",
  });
}

function del(text, opts = {}) {
  return new DeletedTextRun({
    text,
    author: AUTHOR,
    date: DATE,
    font: "Arial",
    size: opts.size || 22,
    bold: opts.bold || false,
    italics: opts.italic || false,
    color: opts.color || "222222",
  });
}

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

// ── Layout helpers ────────────────────────────────────────────────────────────
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

function body(text, opts = {}) {
  return new Paragraph({
    spacing: { before: 0, after: 140 },
    alignment: AlignmentType.JUSTIFIED,
    children: [run(text, opts)],
  });
}

function mixedPara(children) {
  return new Paragraph({
    spacing: { before: 0, after: 140 },
    alignment: AlignmentType.JUSTIFIED,
    children,
  });
}

function smallSpace() {
  return new Paragraph({ spacing: { before: 0, after: 80 }, children: [] });
}

// ── Updated index value table (with inline track-change cells) ────────────────
function makeIndexTable() {
  const border  = { style: BorderStyle.SINGLE, size: 1, color: "D0DEED" };
  const borders = { top: border, bottom: border, left: border, right: border };
  const hBorder  = { style: BorderStyle.NONE, size: 0, color: WHITE };
  const hBorders = { top: hBorder, bottom: hBorder, left: hBorder, right: hBorder };

  // [label, old_wjsi, new_wjsi, context]
  const rows = [
    ["Year / Event",               null,    null,    "Context"],
    ["2001 — Dot-com / 9-11",      "89.8",  "103.4", "Below base; labour market disruption"],
    ["2005 — Base year",           "100.0", "100.0", "Reference level"],
    ["2009 — GFC trough",          "83.2",  "81.2",  "Layoffs spike, quits collapse, labour share falls"],
    ["2013–14 — Recovery period",  "107.9", "97.3",  "Incomplete recovery; labour share decline offsets JOLTS improvement"],
    ["2020 — COVID shock",         "51.7",  "54.2",  "Sharpest single-year deterioration on record"],
    ["2022 — Post-COVID tightening","99.1", "88.3",  "Partial recovery; labour share already eroding"],
    ["2024 — Most recent",         "86.8",  "75.5",  "Below base despite U-3 near historic lows; labour share at 60-year low"],
  ];

  return new Table({
    width: { size: 9360, type: WidthType.DXA },
    columnWidths: [2800, 1200, 5360],
    rows: rows.map((row, i) => new TableRow({
      children: [
        // Col 0: label
        new TableCell({
          borders: i === 0 ? hBorders : borders,
          width: { size: 2800, type: WidthType.DXA },
          shading: { fill: i === 0 ? NAVY : (i % 2 === 0 ? LIGHT : WHITE), type: ShadingType.CLEAR },
          margins: { top: 80, bottom: 80, left: 120, right: 120 },
          children: [new Paragraph({
            children: [new TextRun({ text: row[0], font: "Arial", size: i === 0 ? 20 : 20,
              bold: i === 0, color: i === 0 ? WHITE : "222222" })],
          })],
        }),
        // Col 1: WJSI value — show old (deleted) and new (inserted) if changed
        new TableCell({
          borders: i === 0 ? hBorders : borders,
          width: { size: 1200, type: WidthType.DXA },
          shading: { fill: i === 0 ? NAVY : (i % 2 === 0 ? LIGHT : WHITE), type: ShadingType.CLEAR },
          margins: { top: 80, bottom: 80, left: 120, right: 120 },
          children: [new Paragraph({
            alignment: AlignmentType.CENTER,
            children: i === 0
              ? [new TextRun({ text: "WJSI", font: "Arial", size: 20, bold: true, color: WHITE })]
              : (row[1] === row[2]
                  ? [new TextRun({ text: row[2], font: "Arial", size: 20, bold: true, color: NAVY })]
                  : [
                      del(row[1], { size: 20, bold: true, color: "888888" }),
                      run("  ", { size: 20 }),
                      ins(row[2], { size: 20, bold: true, color: NEWBLUE }),
                    ]
              ),
          })],
        }),
        // Col 2: context
        new TableCell({
          borders: i === 0 ? hBorders : borders,
          width: { size: 5360, type: WidthType.DXA },
          shading: { fill: i === 0 ? SLATE : (i % 2 === 0 ? LIGHT : WHITE), type: ShadingType.CLEAR },
          margins: { top: 80, bottom: 80, left: 120, right: 120 },
          children: [new Paragraph({
            children: [new TextRun({ text: row[3], font: "Arial", size: 20,
              bold: i === 0, color: i === 0 ? WHITE : "222222" })],
          })],
        }),
      ],
    })),
  });
}

// ── Correlation table (unchanged) ─────────────────────────────────────────────
function makeCorrTable() {
  const border  = { style: BorderStyle.SINGLE, size: 1, color: "D0DEED" };
  const borders = { top: border, bottom: border, left: border, right: border };
  const hBorder  = { style: BorderStyle.NONE, size: 0, color: WHITE };
  const hBorders = { top: hBorder, bottom: hBorder, left: hBorder, right: hBorder };

  const rows = [
    ["Indicator", "r (lag 0)", "Interpretation"],
    ["U-6 underemployment", "−0.15", "Not redundant with broadest unemployment measure"],
    ["U-3 unemployment", "−0.24", "Not redundant with headline unemployment"],
    ["Real GDP growth", "+0.66", "Meaningful business-cycle co-movement (expected)"],
    ["Michigan Consumer Sentiment (contemporaneous)", "+0.41", "Moderate contemporaneous; see lead/lag finding below"],
  ];

  return new Table({
    width: { size: 9360, type: WidthType.DXA },
    columnWidths: [3500, 900, 4960],
    rows: rows.map((row, i) => new TableRow({
      children: row.map((cell, j) => new TableCell({
        borders: i === 0 ? hBorders : borders,
        width: { size: [3500, 900, 4960][j], type: WidthType.DXA },
        shading: { fill: i === 0 ? SLATE : (i % 2 === 0 ? LIGHT : WHITE), type: ShadingType.CLEAR },
        margins: { top: 80, bottom: 80, left: 120, right: 120 },
        children: [new Paragraph({
          alignment: j === 1 ? AlignmentType.CENTER : AlignmentType.LEFT,
          children: [new TextRun({ text: cell, font: "Arial", size: 20,
            bold: i === 0, color: i === 0 ? WHITE : (j === 1 ? NAVY : "222222") })],
        })],
      })),
    })),
  });
}

// ── Component list item helper ────────────────────────────────────────────────
function componentItem(label, source, desc, isNew = false) {
  const children = isNew
    ? [
        ins(label + "  ", { bold: true, color: NAVY }),
        ins(source + "  ", { italic: true, color: SLATE }),
        ins(desc),
      ]
    : [
        run(label + "  ", { bold: true, color: NAVY }),
        run(source + "  ", { italic: true, color: SLATE }),
        run(desc),
      ];
  return new Paragraph({
    spacing: { before: 60, after: 60 },
    indent: { left: 360 },
    children,
  });
}

// ── Document ──────────────────────────────────────────────────────────────────
const doc = new Document({
  numbering: {
    config: [{
      reference: "nums",
      levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.",
        alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 540, hanging: 360 } },
                 run: { font: "Arial", size: 22, color: "222222" } } }],
    }],
  },
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
            new TextRun({ text: "WORKER JOB SECURITY INDEX", font: "Arial", size: 18, bold: true, color: NAVY, characterSpacing: 40 }),
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
            new TextRun({ text: "Data: BLS, FRED & Minneapolis Fed. All sources publicly available. Code: github.com/amiasmg/worker-job-security-index  April 2026", font: "Arial", size: 16, color: "888888" }),
            new TextRun({ text: "\tPage ", font: "Arial", size: 16, color: "888888" }),
            new TextRun({ children: [PageNumber.CURRENT], font: "Arial", size: 16, color: "888888" }),
          ],
        })],
      }),
    },
    children: [

      // ── TITLE BLOCK ────────────────────────────────────────────────────────
      new Paragraph({
        spacing: { before: 80, after: 40 },
        children: [new TextRun({ text: "Worker Job Security Index (WJSI)", font: "Arial", size: 40, bold: true, color: NAVY })],
      }),
      new Paragraph({
        spacing: { before: 0, after: 60 },
        children: [new TextRun({ text: "A New Composite Measure of Structural Job Security", font: "Arial", size: 26, color: SLATE, italics: true })],
      }),
      new Paragraph({
        spacing: { before: 0, after: 80 },
        children: [
          new TextRun({ text: "Version 2 — ", font: "Arial", size: 20, color: SLATE }),
          ins("6-component framework. ", { size: 20, bold: true }),
          del("5-component framework.", { size: 20 }),
          new TextRun({ text: "  Track changes shown relative to v1.", font: "Arial", size: 20, italics: true, color: "888888" }),
        ],
      }),
      rule(),

      // ── 1. BACKGROUND ──────────────────────────────────────────────────────
      sectionHead("1.  Background & Motivation"),

      body("Headline unemployment statistics — U-3 and even the broader U-6 — measure whether Americans have jobs. They do not measure how secure those jobs are, whether workers have meaningful power to leave them, or whether the structural conditions underlying employment have deteriorated even as the headline numbers look healthy."),

      body("This gap matters. Between 2022 and 2024, the U-3 unemployment rate remained at or below 4% — a level historically associated with a strong labour market. Yet over the same period, the voluntary quit rate fell from 2.76% to 2.07% (a 25% decline), union membership hit a post-war low of 9.9%, and median job tenure began declining. Workers were employed, but increasingly stuck rather than secure."),

      // NEW sentence about labour share — shown as insertion
      mixedPara([
        ins("Macro-level income distribution tells the same story. Between 2000 and 2024, the nonfarm business labour share of income declined from approximately 111 to 97 on a 2012 = 100 index — its lowest level since the 1960s, indicating workers were collectively capturing a shrinking fraction of economic output even before accounting for job quality or security at the individual level."),
      ]),

      body("The Worker Job Security Index (WJSI) is designed to capture this distinction. It is a composite annual index that measures the structural conditions governing job security — not just employment status — for American wage and salary workers, benchmarked to 2005 = 100 and currently available from 2001 to present."),

      rule(),

      // ── 2. HYPOTHESIS ──────────────────────────────────────────────────────
      sectionHead("2.  Hypothesis"),

      body("The WJSI rests on a straightforward premise: job security is multi-dimensional and cannot be adequately captured by any single statistic. A worker is more secure when they have the structural protection of collective bargaining; the confidence and ability to voluntarily leave a job; a labour market where employers are not actively reducing headcount; reasonable stability of tenure; an openings environment that does not generate excessive churn; and — in aggregate — a labour market in which workers' collective share of economic output is not being eroded."),

      body("A secondary hypothesis — which the data partially supports — is that changes in structural job security precede changes in consumer confidence. Workers feel insecure before that insecurity registers in headline sentiment surveys. If this lead relationship holds, the WJSI has potential value as an early-warning indicator, not merely a descriptive one."),

      rule(),

      // ── 3. LITERATURE ──────────────────────────────────────────────────────
      sectionHead("3.  Literature Context"),

      body("The inadequacy of headline unemployment as a welfare measure is well-established. Krueger et al. (2017) documented the significance of labour force non-participation beyond the headline rate. Bernhardt et al. (2001) and Weil (2014, The Fissured Workplace) established that job quality — not just availability — has deteriorated structurally since the 1980s. Farber (2008, 2015) documented the long-run decline in job stability and tenure, particularly for male workers."),

      body("The quit rate as a proxy for worker bargaining power has been formalised by Daly, Hobijn, and Wiles (2012, San Francisco Fed) and features in Moscarini and Postel-Vinay's (2012) work on employer-size wage cyclicality. The WJSI brings this alongside tenure and union coverage into a single composite."),

      // NEW paragraph on labour share literature — shown as insertion
      mixedPara([
        ins("The secular decline in labour's share of income adds a further dimension. Elsby, Hobijn and Şahin (2013, Brookings Papers) documented the global nature of the decline and its acceleration post-2000, attributing it partly to offshoring and capital-labour substitution. More recently, the Minneapolis Federal Reserve (Working Paper 800, 2024) found that the U.S. labour share is now at its lowest level since the Great Depression — roughly five percentage points below 1929. Connecting labour share to worker bargaining power directly motivates its inclusion in the WJSI as a sixth structural component."),
      ]),

      body("LISEP's True Rate of Unemployment (TRU) is the closest institutional analogue. Where TRU expands the employment/unemployment boundary to capture those who want full-time work but cannot obtain it, the WJSI measures the security and structural quality of employment for those who have it. The two instruments are designed to be complementary: TRU asks whether workers have the employment they need; WJSI asks whether the employment they have is structurally secure."),

      rule(),

      // ── 4. METHODOLOGY ─────────────────────────────────────────────────────
      sectionHead("4.  Methodology"),

      mixedPara([
        run("The WJSI is an equal-weighted composite of "),
        del("five"),
        ins("six"),
        run(" annually-averaged components sourced from public BLS and FRED data. Each component is z-scored over its full available history and directionally aligned so that a higher score always means greater security."),
      ]),

      smallSpace(),

      componentItem(
        "1.  Union membership rate",
        "(BLS, 1983–present)",
        "Collective bargaining coverage as a proxy for structural worker protection."
      ),
      componentItem(
        "2.  JOLTS quits rate",
        "(BLS, 2001–present)",
        "Share of workers voluntarily leaving jobs — the standard proxy for worker bargaining power and labour market confidence."
      ),
      componentItem(
        "3.  JOLTS layoffs & discharges rate",
        "(BLS, 2001–present, inverted)",
        "Employer-initiated separations. Inverted so lower layoffs = higher security."
      ),
      componentItem(
        "4.  Median job tenure",
        "(BLS tenure supplement, biennial, interpolated)",
        "Stability of the employment relationship over time."
      ),
      // NEW component 5 — labour share
      componentItem(
        "5.  Nonfarm business labour share",
        "(BLS PRS85006173, 1947–present)",
        "Workers' aggregate share of nonfarm output, indexed to 2012 = 100. Higher share = greater collective economic security. Source: Minneapolis Fed WP 800.",
        true  // isNew
      ),
      // Component 6 (was 5) — openings — show renumber as track change
      new Paragraph({
        spacing: { before: 60, after: 60 },
        indent: { left: 360 },
        children: [
          del("5.  "),
          ins("6.  "),
          run("JOLTS job openings rate  ", { bold: true, color: NAVY }),
          run("(BLS, 2001–present)  ", { italic: true, color: SLATE }),
          run("High openings are treated as a mild negative in the primary specification, reflecting churn risk. Sensitivity analysis tests both sign conventions."),
        ],
      }),

      smallSpace(),

      // Updated JOLTS weight note — track changes
      mixedPara([
        ins("The addition of labour share reduces the JOLTS survey weight from 3/5 (60%) to 3/6 (50%), addressing a methodological concern about over-reliance on a single survey source. "),
      ]),

      body("One component considered and excluded is the part-time-for-economic-reasons rate. Including it produced a correlation of r = 0.81 with U-6 — structural redundancy, since U-6 directly counts involuntary part-time workers. Excluding it reduces the WJSI–U-6 correlation to r = 0.15, establishing genuine differentiation."),

      // NEW: rejected candidates note — insertion
      mixedPara([
        ins("A systematic candidate-component analysis tested and eliminated four further series on empirical grounds: the productivity-pay ratio (r = −0.97 with labour share; redundant), employer-to-employer job transitions (r = +0.73 with labour share; partially redundant), mean unemployment duration (confirmed lagging indicator — adding it reduced the +2yr sentiment lead from r = 0.50 to r = 0.09), and temporary help employment share (coincident indicator; peak correlation with sentiment at lag 0 with no forward-looking content). This analysis strengthens confidence in the 6-component specification."),
      ]),

      new Paragraph({ children: [new PageBreak()] }),

      // ── 5. BACKTESTING ─────────────────────────────────────────────────────
      sectionHead("5.  Backtesting & Validation"),

      mixedPara([
        run("The index passes three of five primary validation tests: it falls during the "),
        run("2008–09 financial crisis and the 2020 COVID shock, and its most recent reading (2024: "),
        del("86.8"),
        ins("75.5"),
        run(") sits below the base year, consistent with the structural deterioration thesis. "),
        ins("Two tests change character in the 6-component specification: the 2001 value (now 103.4 vs. the prior 89.8) sits above base, reflecting the genuinely higher labour share of that period; and the 2019 pre-COVID value (91.2) does not recover to the prior near-parity level, consistent with the secular labour share decline since 2000."),
      ]),

      smallSpace(),
      makeIndexTable(),
      smallSpace(),

      mixedPara([
        run("The 2022–2024 divergence is the central finding. ", { bold: true, color: NAVY }),
        run("Headline employment statistics describe a strong labour market; the WJSI is deteriorating. The proximate drivers are the collapse in voluntary quits (down 25% from their 2022 peak), continued erosion of union membership to record lows, a decline in median tenure, "),
        ins("and a labour share index at its lowest reading since the 1960s "),
        run("— all structural rather than cyclical signals."),
      ]),

      sectionHead("Differentiation from existing measures"),

      body("The WJSI has been tested against six external indicators across the full 2001–2025 sample:"),

      smallSpace(),
      makeCorrTable(),
      smallSpace(),

      body("Five alternative weighting schemes (union-heavy, JOLTS-focused, no-openings, and structural-only) all correlate above r = 0.80 with the equal-weight baseline, confirming that the index shape is not an artefact of weighting choices."),

      sectionHead("Lead/lag structure — the key finding"),

      mixedPara([
        run("The WJSI appears to lead the University of Michigan Consumer Sentiment Index by approximately two years. At a two-year lead, the Pearson correlation "),
        del("rises to r = 0.45 (p = 0.033)"),
        ins("rises to r = 0.50 (p = 0.015)"),
        run(". More importantly, a formal Granger causality test — which controls for Michigan Sentiment's own autocorrelation — yields F = 7.37, p = 0.014. The reverse direction (sentiment leading WJSI) is not significant (p = 0.41). "),
        ins("The addition of the labour share component strengthened this lead relationship relative to the prior 5-component specification (r = 0.45), suggesting that macro income distribution carries independent forward-looking information about consumer confidence."),
      ]),

      body("This finding requires qualification and should not be overstated. It does not survive permutation-based multiple-testing correction across all nine lags examined (familywise p = 0.16), and it is not present in pre-2008 data alone (r = 0.30, p = 0.25). Rolling-window analysis shows the relationship emerging and stabilising in the post-GFC environment: the 2007–2017 window alone yields r = 0.78. Leave-one-out cross-validation confirms marginal but positive out-of-sample predictive power (LOO R² = 0.097)."),

      body("The most defensible framing is: in the post-2008 structural environment, deteriorating job security has preceded deteriorating consumer confidence by approximately two years. This is a post-GFC behavioural finding rather than a long-run structural one — but it is a finding worth monitoring and, given the Granger result, difficult to dismiss."),

      rule(),

      // ── 6. NEXT STEPS ──────────────────────────────────────────────────────
      sectionHead("6.  Next Steps & Partnership Rationale"),

      body("The index is methodologically complete at the prototype stage. Three areas warrant development before public release."),

      body("The openings rate sign convention is theoretically contestable — high openings can signal either worker-friendly tight labour markets or destabilising churn — and the choice materially affects the lead/lag result. Resolving this through consultation with labour economists is the single most important near-term task."),

      body("The legacy series (union + tenure only, 1983–2000) shows a striking long-run structural decline — from approximately 280 in 1983 to 66 in 2000 — but this series uses only two components and has not been independently validated. It warrants separate treatment before publication."),

      // NEW next step — employer health insurance
      mixedPara([
        ins("A seventh candidate component — employer-sponsored health insurance coverage — was identified but not yet incorporated. The series has semi-structural dynamics (declining 1999–2010, stabilising post-ACA) that would add non-wage benefit security to the framework. It requires data construction from Kaiser Family Foundation or CPS ASEC sources; no clean long-run FRED series exists. This represents the most promising near-term addition."),
      ]),

      body("Finally, the index would benefit from LISEP's institutional platform, BLS relationships, and data infrastructure for annual updates. A natural collaboration would involve LISEP adopting the WJSI as a companion to TRU, with joint publication of both indices as complementary instruments in an expanded picture of American worker wellbeing: one measuring access to adequate employment, the other measuring the structural security of employment held."),

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
  fs.writeFileSync("/Users/Amias/WorkerSecurityIndex/WJSI_Briefing_Note_v2.docx", buf);
  console.log("Written: /Users/Amias/WorkerSecurityIndex/WJSI_Briefing_Note_v2.docx");
});
