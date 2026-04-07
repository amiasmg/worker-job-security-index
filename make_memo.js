const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, HeadingLevel, BorderStyle, WidthType,
  ShadingType, PageNumber, PageBreak, TabStopType, TabStopPosition,
  LevelFormat
} = require('docx');
const fs = require('fs');

// ── Colours ──────────────────────────────────────────────────────────────────
const NAVY   = "1F3864";
const SLATE  = "44546A";
const RULE   = "BDD0E9";
const LIGHT  = "EBF2FA";
const WHITE  = "FFFFFF";

// ── Helpers ───────────────────────────────────────────────────────────────────
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
      font: "Arial",
      size: 20,
      bold: true,
      color: NAVY,
      characterSpacing: 40,
    })],
  });
}

function body(text, opts = {}) {
  return new Paragraph({
    spacing: { before: 0, after: 140 },
    alignment: AlignmentType.JUSTIFIED,
    children: [new TextRun({
      text,
      font: "Arial",
      size: 22,
      color: opts.color || "222222",
      bold: opts.bold || false,
      italics: opts.italic || false,
    })],
  });
}

function bodySentences(...runs) {
  return new Paragraph({
    spacing: { before: 0, after: 140 },
    alignment: AlignmentType.JUSTIFIED,
    children: runs.map(r =>
      new TextRun({ font: "Arial", size: 22, color: "222222", ...r })
    ),
  });
}

function smallSpace() {
  return new Paragraph({ spacing: { before: 0, after: 80 }, children: [] });
}

// ── Key-data table ─────────────────────────────────────────────────────────────
function makeIndexTable() {
  const border = { style: BorderStyle.SINGLE, size: 1, color: "D0DEED" };
  const borders = { top: border, bottom: border, left: border, right: border };
  const hBorder = { style: BorderStyle.NONE, size: 0, color: WHITE };
  const hBorders = { top: hBorder, bottom: hBorder, left: hBorder, right: hBorder };

  const rows = [
    ["Year / Event", "WJSI", "Context"],
    ["2001 — Dot-com / 9-11", "89.8", "Below base; labour market disruption"],
    ["2005 — Base year", "100.0", "Reference level"],
    ["2009 — GFC trough", "83.2", "Layoffs spike, quits collapse"],
    ["2013–14 — Recovery peak", "107.9", "Layoffs fall, tenure rises"],
    ["2020 — COVID shock", "51.7", "Sharpest single-year deterioration on record"],
    ["2022 — Post-COVID tightening", "99.1", "Near full recovery"],
    ["2024 — Most recent", "86.8", "Below base despite U-3 near historic lows"],
  ];

  return new Table({
    width: { size: 9360, type: WidthType.DXA },
    columnWidths: [2800, 1000, 5560],
    rows: rows.map((row, i) => new TableRow({
      children: row.map((cell, j) => new TableCell({
        borders: i === 0 ? hBorders : borders,
        width: { size: [2800, 1000, 5560][j], type: WidthType.DXA },
        shading: { fill: i === 0 ? NAVY : (i % 2 === 0 ? LIGHT : WHITE), type: ShadingType.CLEAR },
        margins: { top: 80, bottom: 80, left: 120, right: 120 },
        children: [new Paragraph({
          alignment: j === 1 ? AlignmentType.CENTER : AlignmentType.LEFT,
          children: [new TextRun({
            text: cell,
            font: "Arial",
            size: i === 0 ? 20 : 20,
            bold: i === 0 || j === 1,
            color: i === 0 ? WHITE : (j === 1 ? NAVY : "222222"),
          })],
        })],
      })),
    })),
  });
}

// ── Correlation table ─────────────────────────────────────────────────────────
function makeCorrTable() {
  const border = { style: BorderStyle.SINGLE, size: 1, color: "D0DEED" };
  const borders = { top: border, bottom: border, left: border, right: border };
  const hBorder = { style: BorderStyle.NONE, size: 0, color: WHITE };
  const hBorders = { top: hBorder, bottom: hBorder, left: hBorder, right: hBorder };

  const rows = [
    ["Indicator", "r (lag 0)", "Interpretation"],
    ["U-6 underemployment", "−0.15", "Not redundant with broadest unemployment measure"],
    ["U-3 unemployment", "−0.24", "Not redundant with headline unemployment"],
    ["Real GDP growth", "+0.66", "Meaningful business-cycle co-movement (expected)"],
    ["Michigan Consumer Sentiment (contemporaneous)", "+0.15", "Weak contemporaneous; see lead/lag finding below"],
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
          children: [new TextRun({
            text: cell,
            font: "Arial",
            size: 20,
            bold: i === 0,
            color: i === 0 ? WHITE : (j === 1 ? NAVY : "222222"),
          })],
        })],
      })),
    })),
  });
}

// ── Document ──────────────────────────────────────────────────────────────────
const doc = new Document({
  numbering: {
    config: [{
      reference: "nums",
      levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
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
            new TextRun({ text: "Data: BLS & FRED. All sources publicly available. Code available on request.  April 2026", font: "Arial", size: 16, color: "888888" }),
            new TextRun({ text: "\tPage ", font: "Arial", size: 16, color: "888888" }),
            new TextRun({ children: [PageNumber.CURRENT], font: "Arial", size: 16, color: "888888" }),
          ],
        })],
      }),
    },
    children: [

      // ── TITLE BLOCK ──────────────────────────────────────────────────────────
      new Paragraph({
        spacing: { before: 80, after: 40 },
        children: [new TextRun({ text: "Worker Job Security Index (WJSI)", font: "Arial", size: 40, bold: true, color: NAVY })],
      }),
      new Paragraph({
        spacing: { before: 0, after: 60 },
        children: [new TextRun({ text: "A New Composite Measure of Structural Job Security", font: "Arial", size: 26, color: SLATE, italics: true })],
      }),
      rule(),

      // ── 1. BACKGROUND ────────────────────────────────────────────────────────
      sectionHead("1.  Background & Motivation"),

      body("Headline unemployment statistics — U-3 and even the broader U-6 — measure whether Americans have jobs. They do not measure how secure those jobs are, whether workers have meaningful power to leave them, or whether the structural conditions underlying employment have deteriorated even as the headline numbers look healthy."),

      body("This gap matters. Between 2022 and 2024, the U-3 unemployment rate remained at or below 4% — a level historically associated with a strong labour market. Yet over the same period, the voluntary quit rate fell from 2.76% to 2.07% (a 25% decline), union membership hit a post-war low of 9.9%, and median job tenure began declining. Workers were employed, but increasingly stuck rather than secure."),

      body("The Worker Job Security Index (WJSI) is designed to capture this distinction. It is a composite annual index that measures the structural conditions governing job security — not just employment status — for American wage and salary workers, benchmarked to 2005 = 100 and currently available from 2001 to present."),

      rule(),

      // ── 2. HYPOTHESIS ────────────────────────────────────────────────────────
      sectionHead("2.  Hypothesis"),

      body("The WJSI rests on a straightforward premise: job security is multi-dimensional and cannot be adequately captured by any single statistic. A worker is more secure when they have the structural protection of collective bargaining; the confidence and ability to voluntarily leave a job; a labour market where employers are not actively reducing headcount; reasonable stability of tenure; and an openings environment that does not generate excessive churn."),

      body("A secondary hypothesis — which the data partially supports — is that changes in structural job security precede changes in consumer confidence. Workers feel insecure before that insecurity registers in headline sentiment surveys. If this lead relationship holds, the WJSI has potential value as an early-warning indicator, not merely a descriptive one."),

      rule(),

      // ── 3. LITERATURE ────────────────────────────────────────────────────────
      sectionHead("3.  Literature Context"),

      body("The inadequacy of headline unemployment as a welfare measure is well-established. Krueger et al. (2017) documented the significance of labour force non-participation beyond the headline rate. Bernhardt et al. (2001) and Weil (2014, The Fissured Workplace) established that job quality — not just availability — has deteriorated structurally since the 1980s. Farber (2008, 2015) documented the long-run decline in job stability and tenure, particularly for male workers."),

      body("The quit rate as a proxy for worker bargaining power has been formalised by Daly, Hobijn, and Wiles (2012, San Francisco Fed) and features in Moscarini and Postel-Vinay's (2012) work on employer-size wage cyclicality. The WJSI brings this alongside tenure and union coverage into a single composite."),

      body("LISEP's True Rate of Unemployment (TRU) is the closest institutional analogue. Where TRU expands the employment/unemployment boundary to capture those who want full-time work but cannot obtain it, the WJSI measures the security and structural quality of employment for those who have it. The two instruments are designed to be complementary: TRU asks whether workers have the employment they need; WJSI asks whether the employment they have is structurally secure."),

      rule(),

      // ── 4. METHODOLOGY ───────────────────────────────────────────────────────
      sectionHead("4.  Methodology"),

      body("The WJSI is an equal-weighted composite of five annually-averaged components sourced from public BLS data. Each component is z-scored over its full available history and directionally aligned so that a higher score always means greater security."),

      smallSpace(),

      ...[
        ["1.  Union membership rate", "(BLS, 1983–present)", "Collective bargaining coverage as a proxy for structural worker protection."],
        ["2.  JOLTS quits rate", "(BLS, 2001–present)", "Share of workers voluntarily leaving jobs — the standard proxy for worker bargaining power and labour market confidence."],
        ["3.  JOLTS layoffs & discharges rate", "(BLS, 2001–present, inverted)", "Employer-initiated separations. Inverted so lower layoffs = higher security."],
        ["4.  Median job tenure", "(BLS tenure supplement, biennial, interpolated)", "Stability of the employment relationship over time."],
        ["5.  JOLTS job openings rate", "(BLS, 2001–present)", "High openings are treated as a mild negative in the primary specification, reflecting churn risk. Sensitivity analysis tests both sign conventions."],
      ].map(([label, source, desc]) =>
        new Paragraph({
          spacing: { before: 60, after: 60 },
          indent: { left: 360 },
          children: [
            new TextRun({ text: label + "  ", font: "Arial", size: 22, bold: true, color: NAVY }),
            new TextRun({ text: source + "  ", font: "Arial", size: 22, color: SLATE, italics: true }),
            new TextRun({ text: desc, font: "Arial", size: 22, color: "222222" }),
          ],
        })
      ),

      smallSpace(),

      body("One component considered and excluded is the part-time-for-economic-reasons rate. Including it produced a correlation of r = 0.81 with U-6 — structural redundancy, since U-6 directly counts involuntary part-time workers. Excluding it reduces the WJSI–U-6 correlation to r = 0.15, establishing genuine differentiation."),

      new Paragraph({ children: [new PageBreak()] }),

      // ── 5. BACKTESTING ───────────────────────────────────────────────────────
      sectionHead("5.  Backtesting & Validation"),

      body("The index passes all five primary validation tests: it falls during the 2001 recession, the 2008–09 financial crisis, and the 2020 COVID shock; it recovers after each; and its most recent reading (2024: 86.8) sits below the base year, consistent with the structural deterioration thesis."),

      smallSpace(),
      makeIndexTable(),
      smallSpace(),

      bodySentences(
        { text: "The 2022–2024 divergence is the central finding. ", bold: true, color: NAVY },
        { text: "Headline employment statistics describe a strong labour market; the WJSI is deteriorating. The proximate drivers are the collapse in voluntary quits (down 25% from their 2022 peak), continued erosion of union membership to record lows, and a decline in median tenure — all structural rather than cyclical signals." }
      ),

      sectionHead("Differentiation from existing measures"),

      body("The WJSI has been tested against six external indicators across the full 2001–2025 sample:"),

      smallSpace(),
      makeCorrTable(),
      smallSpace(),

      body("Five alternative weighting schemes (union-heavy, JOLTS-focused, no-openings, and structural-only) all correlate above r = 0.80 with the equal-weight baseline, confirming that the index shape is not an artefact of weighting choices."),

      sectionHead("Lead/lag structure — the key finding"),

      bodySentences(
        { text: "The WJSI appears to lead the University of Michigan Consumer Sentiment Index by approximately two years. " },
        { text: "At a two-year lead, the Pearson correlation rises to r = 0.45 (p = 0.033). More importantly, a formal Granger causality test — which controls for Michigan Sentiment's own autocorrelation — yields F = 7.37, p = 0.014. The reverse direction (sentiment leading WJSI) is not significant (p = 0.41)." }
      ),

      body("This finding requires qualification and should not be overstated. It does not survive permutation-based multiple-testing correction across all nine lags examined (familywise p = 0.16), and it is not present in pre-2008 data alone (r = 0.30, p = 0.25). Rolling-window analysis shows the relationship emerging and stabilising in the post-GFC environment: the 2007–2017 window alone yields r = 0.78. Leave-one-out cross-validation confirms marginal but positive out-of-sample predictive power (LOO R² = 0.097)."),

      body("The most defensible framing is: in the post-2008 structural environment, deteriorating job security has preceded deteriorating consumer confidence by approximately two years. This is a post-GFC behavioural finding rather than a long-run structural one — but it is a finding worth monitoring and, given the Granger result, difficult to dismiss."),

      rule(),

      // ── 6. NEXT STEPS ────────────────────────────────────────────────────────
      sectionHead("6.  Next Steps & Partnership Rationale"),

      body("The index is methodologically complete at the prototype stage. Three areas warrant development before public release."),

      body("The openings rate sign convention is theoretically contestable — high openings can signal either worker-friendly tight labour markets or destabilising churn — and the choice materially affects the lead/lag result. Resolving this through consultation with labour economists is the single most important near-term task."),

      body("The legacy series (union + tenure only, 1983–2000) shows a striking long-run structural decline — from approximately 280 in 1983 to 66 in 2000 — but this series uses only two components and has not been independently validated. It warrants separate treatment before publication."),

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
  fs.writeFileSync("/Users/Amias/WorkerSecurityIndex/WJSI_Briefing_Note.docx", buf);
  console.log("Written: /Users/Amias/WorkerSecurityIndex/WJSI_Briefing_Note.docx");
});
