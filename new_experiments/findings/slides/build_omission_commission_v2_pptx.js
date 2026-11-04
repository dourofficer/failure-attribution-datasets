// Version 2 of the omission -> commission deck, in plain vocabulary: gap -> carry-on -> fill-in.
// Numbers come from omission_commission_v2_stats.json (run omission_commission_v2_stats.py first).
// Usage: node build_omission_commission_v2_pptx.js omission_commission_v2.pptx
const path = require("path");
const pptxgen = require("pptxgenjs");
const { applyTheme } = require("/dataDisk/home/thanhdo/.claude-personal/skills/synced/d34f2cba-6383-4e15-b07d-90e2e3b106f6_3cac4ae6-fa7c-4812-ac46-3d0de7f247f9/pptx/scripts/apply_theme.js");
const ST = require(path.join(__dirname, "omission_commission_v2_stats.json"));

const OUT = process.argv[2] || path.join(__dirname, "omission_commission_v2.pptx");
const THEME = {
  name: "Gap Carry-on Fill-in",
  headFontFace: "Arial",
  bodyFontFace: "Arial",
  colors: { // Google Slides "Simple Light"
    dk1: "000000", lt1: "FFFFFF", dk2: "595959", lt2: "EEEEEE",
    accent1: "4285F4", accent2: "212121", accent3: "78909C",
    accent4: "FFAB40", accent5: "0097A7", accent6: "EEFF41",
    hlink: "0097A7", folHlink: "0097A7",
  },
};
// white slides throughout; text near-black, Google blue as the one accent, light-grey boxes
const K = {
  dark: "212121", card: "F3F3F3", ink: "212121", muted: "595959", faint: "757575",
  orange: "1967D2", orangeLt: "1967D2", blue: "1967D2", blueLt: "1967D2", gray: "78909C", grayLt: "BDBDBD",
  onDark: "212121", onDarkMuted: "595959", white: "FFFFFF", panel: "F3F3F3", rowA: "F8F9FA",
};
// one colour per chain step, used for the cards, the table headers and the example markers
const STEP = {
  GAP: { name: "Gap", dot: "E8710A", lt: "B3540A", tint: "FEF1E6", ink: "B3540A" },
  CARRY: { name: "Carry-on", dot: "78909C", lt: "455A64", tint: "ECEFF1", ink: "455A64" },
  FILL: { name: "Fill-in", dot: "4285F4", lt: "1967D2", tint: "E8F0FE", ink: "1967D2" },
  LABEL: { name: "Label", dot: "212121", lt: "212121", tint: "EEEEEE", ink: "212121" },
};

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.333 x 7.5
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "Gap, carry-on, fill-in (v2)";

const W = 13.333, M = 0.6, CW = W - 2 * M;
const pct = (a, b) => `${Math.round((100 * a) / b)}%`;
const fmt = (n) => n.toLocaleString("en-US");

pres.defineSlideMaster({
  title: "STATEMENT",
  background: { color: K.white },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: M, y: 0.8, w: CW, h: 0.8, fontFace: "Arial", fontSize: 30, bold: false, color: "000000", margin: 0, valign: "top" }, text: "" } },
  ],
  slideNumber: { x: W - M - 0.8, y: 6.95, w: 0.8, h: 0.3, fontFace: "Arial", fontSize: 11, color: K.faint, align: "right" },
});
pres.defineSlideMaster({
  title: "LIGHT_TITLE_ONLY",
  background: { color: K.white },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: M, y: 0.45, w: CW, h: 0.7, fontFace: "Arial", fontSize: 30, bold: false, color: "000000", margin: 0, valign: "top" }, text: "" } },
  ],
  slideNumber: { x: W - M - 0.8, y: 6.95, w: 0.8, h: 0.3, fontFace: "Arial", fontSize: 11, color: K.faint, align: "right" },
});

function footer(slide, text, color) {
  slide.addText(text, { x: M, y: 6.95, w: CW - 1.0, h: 0.3, fontSize: 11, color, margin: 0, isTextBox: true, objectName: "source" });
}

// ---------- Slide 1: the phenomenon ----------
pres.addSection({ title: "Phenomenon" });
{
  const s = pres.addSlide({ masterName: "STATEMENT", sectionTitle: "Phenomenon" });
  s.addText("GAP → CARRY-ON → FILL-IN", { x: M, y: 0.45, w: CW, h: 0.3, fontSize: 13, bold: true, charSpacing: 2, color: K.orangeLt, margin: 0, isTextBox: true, objectName: "eyebrow" });
  s.addText("One failure, several defensible error steps", { placeholder: "title" });
  s.addText("Information the task needs never arrives; the run goes on anyway, and a later step supplies the missing piece without evidence.",
    { x: M, y: 1.65, w: CW, h: 0.6, fontSize: 18, color: K.muted, margin: 0, isTextBox: true, objectName: "lead" });

  const cards = [
    { n: "1", st: STEP.GAP, head: "GAP", desc: "Information the task needs never reaches the agent.",
      sub: "Nothing looks wrong at that step: it is something that did not happen.", kinds: "never looked for · lookup failed · handed off, never done · on screen, not read" },
    { n: "2", st: STEP.CARRY, head: "CARRY-ON (OFTEN)", desc: "A step proceeds as if the information had arrived, e.g. a plan update saying “gathered”, or a check that verifies only the arithmetic.",
      sub: "Turns the gap into a commitment.", kinds: "" },
    { n: "3", st: STEP.FILL, head: "FILL-IN", desc: "A step supplies the missing piece with no evidence behind it.",
      sub: "Visible: a claim nothing in the run supports.", kinds: "guessed value · made-up fact · misread page · action with no basis" },
  ];
  const arrowW = 0.4, gap = 0.15, cardW = (CW - 2 * arrowW - 4 * gap) / 3, y0 = 2.4, h = 3.4;
  cards.forEach((c, i) => {
    const x = M + i * (cardW + arrowW + 2 * gap);
    s.addShape(pres.shapes.RECTANGLE, { x, y: y0, w: cardW, h, rectRadius: 0.12, fill: { color: K.card }, line: { color: K.card }, objectName: "card " + c.head });
    s.addText(c.n, { shape: pres.shapes.OVAL, x: x + 0.28, y: y0 + 0.28, w: 0.5, h: 0.5, fill: { color: c.st.dot }, color: K.white, fontSize: 18, bold: true,
      align: "center", valign: "middle", margin: 0, isTextBox: true, objectName: "badge " + c.n });
    s.addText(c.head, { x: x + 0.95, y: y0 + 0.28, w: cardW - 1.15, h: 0.5, fontSize: 15, bold: true, charSpacing: 1, color: c.st.lt, valign: "middle", margin: 0, isTextBox: true, objectName: "card head " + c.n });
    const runs = [
      { text: c.desc, options: { fontSize: 15, color: K.onDark, breakLine: true, paraSpaceAfter: 8 } },
      { text: c.sub, options: { fontSize: 14, color: K.onDarkMuted, breakLine: !!c.kinds, paraSpaceAfter: 8 } },
    ];
    if (c.kinds) runs.push({ text: c.kinds, options: { fontSize: 14, italic: true, color: K.onDarkMuted } });
    s.addText(runs, { x: x + 0.28, y: y0 + 1.0, w: cardW - 0.56, h: h - 1.2, valign: "top", margin: 0, isTextBox: true, objectName: "card text " + c.n });
    if (i < 2) s.addShape(pres.shapes.RIGHT_ARROW, { x: x + cardW + gap, y: y0 + h / 2 - 0.15, w: arrowW, h: 0.3, fill: { color: K.grayLt }, line: { color: K.grayLt }, objectName: "arrow " + i });
  });
  s.addText("Annotators label different steps of the chain, so exact-step scoring can mark a correct diagnosis wrong.",
    { x: M, y: 5.95, w: CW, h: 0.8, fontSize: 20, bold: true, color: K.dark, margin: 0, isTextBox: true, objectName: "takeaway" });
  footer(s, "Called omission → acceptance → commission in new_experiments/findings/hypotheses.md (X3, §2b)", K.faint);
  s.addNotes("The chain has three steps. Gap: information the task needs never reaches the agent (it was never looked for, the lookup failed, it was handed to another agent who never did it, or it was on screen and not read). Carry-on: a step proceeds as if the information had arrived; this step is often present but not always, and it can come before or after the fill-in. Fill-in: a step supplies the missing piece with no evidence (a guessed value, a made-up fact, a misread page, an action with no basis). The gap is a non-event, so nothing in that step's own text looks wrong; the fill-in is visible. Each of the three is a defensible answer to 'where is the error', and different datasets label different ones.");
}

// ---------- Slide 2: procedure ----------
pres.addSection({ title: "Method" });
{
  const s = pres.addSlide({ masterName: "LIGHT_TITLE_ONLY", sectionTitle: "Method" });
  s.addText("How the numbers were produced", { placeholder: "title" });

  const y0 = 1.35, h = 3.15, arrowW = 0.35, g = 0.15;
  const colW = (CW - 2 * arrowW - 4 * g) / 3;
  const boxes = [
    { head: "INPUT, per failed run", dark: false, items: [
      "The task",
      "The reference (correct) answer",
      "The system’s final output",
      "The whole trajectory, steps numbered (up to 100k tokens)",
    ], foot: "Not given: the dataset’s error label" },
    { head: "CLASSIFIER", dark: true, items: [
      "Qwen3.8-27B, thinking on",
      "One fixed prompt that defines gap, carry-on and fill-in",
      "Reads the whole run, then answers in JSON",
    ], foot: "new_experiments/inspect/oc_classify.py" },
    { head: "OUTPUT", dark: false, items: [
      "The missing information",
      "Gap step and its kind",
      "Carry-on step, if any",
      "Fill-in step and its kind",
      "Shape: chain / gap only / fill-in only / other",
    ], foot: "" },
  ];
  boxes.forEach((b, i) => {
    const x = M + i * (colW + arrowW + 2 * g);
    const bg = b.dark ? STEP.FILL.tint : K.panel, head = K.blue, ink = K.ink, mut = K.muted;
    s.addShape(pres.shapes.RECTANGLE, { x, y: y0, w: colW, h, rectRadius: 0.1, fill: { color: bg }, line: { color: bg }, objectName: "box " + b.head });
    s.addText(b.head, { x: x + 0.25, y: y0 + 0.2, w: colW - 0.5, h: 0.35, fontSize: 14, bold: true, charSpacing: 1, color: head, margin: 0, isTextBox: true, objectName: "box head " + i });
    s.addText(b.items.map((t, k) => ({ text: t, options: { bullet: true, breakLine: k < b.items.length - 1, paraSpaceAfter: 5 } })),
      { x: x + 0.25, y: y0 + 0.65, w: colW - 0.5, h: h - 1.2, fontSize: 14, color: ink, valign: "top", margin: 0, isTextBox: true, objectName: "box items " + i });
    if (b.foot) s.addText(b.foot, { x: x + 0.25, y: y0 + h - 0.6, w: colW - 0.5, h: 0.45, fontSize: 13, italic: true, color: mut, margin: 0, isTextBox: true, objectName: "box foot " + i });
    if (i < 2) s.addShape(pres.shapes.RIGHT_ARROW, { x: x + colW + g, y: y0 + h / 2 - 0.15, w: arrowW, h: 0.3, fill: { color: K.grayLt }, line: { color: K.grayLt }, objectName: "arrow " + i });
  });

  const y1 = y0 + h + 0.25, h1 = 6.8 - y1, w1 = (CW - 0.3) / 2;
  const lower = [
    { head: "SCORING AGAINST THE DATASET’S LABEL", items: [
      "Only runs with the chain are scored",
      "“Next to” = within ±1 step",
      "Steps checked separately: a label can count twice",
      "MP-Bench: earliest step flagged by ≥2 of 3 annotators",
    ] },
    { head: "COVERAGE AND LIMITS", items: [
      "All labelled runs: Who&When, MP-Bench, TraceElephant",
      "Random samples of 120 / 150: SymTrace / AgentHallu",
      `Unparsed outputs dropped (0–${Math.max(...ST.selected.map((r) => r.unparsed))} per dataset)`,
      "One model, one prompt; checked by hand on 3 runs",
    ] },
  ];
  lower.forEach((b, i) => {
    const x = M + i * (w1 + 0.3);
    s.addShape(pres.shapes.RECTANGLE, { x, y: y1, w: w1, h: h1, rectRadius: 0.1, fill: { color: K.white }, line: { color: "DDDDDD", width: 1 }, objectName: "lower box " + i });
    s.addText(b.head, { x: x + 0.25, y: y1 + 0.18, w: w1 - 0.5, h: 0.32, fontSize: 13, bold: true, charSpacing: 1, color: K.gray, margin: 0, isTextBox: true, objectName: "lower head " + i });
    s.addText(b.items.map((t, k) => ({ text: t, options: { bullet: true, breakLine: k < b.items.length - 1, paraSpaceAfter: 3 } })),
      { x: x + 0.2, y: y1 + 0.55, w: w1 - 0.4, h: h1 - 0.7, fontSize: 14, color: K.ink, valign: "top", margin: 0, isTextBox: true, objectName: "lower items " + i });
  });
  footer(s, "Statistics: new_experiments/findings/slides/omission_commission_v2_stats.py over results/omission_commission/llm_*.jsonl", K.faint);
  s.addNotes("The classifier is label-blind: it never sees the step the dataset blames. It is given the task, the reference answer, the final output and the complete step-numbered trajectory (each step capped at 6,000 characters, the whole run at 100k tokens), and returns the missing information, the gap step and its kind, the carry-on step if any, the fill-in step and its kind, and the overall shape. A run has the chain when both a gap and a fill-in are found. Scoring then compares the dataset's own label with each of the three steps separately, allowing one step either side. Because the columns are checked separately, a label between two adjacent steps counts for both; the 'any' column counts each run once. The main limit is validation: the classifier's step placements were checked by hand on three runs only.");
}

// ---------- Slide 3: statistics ----------
pres.addSection({ title: "Evidence" });
{
  const s = pres.addSlide({ masterName: "LIGHT_TITLE_ONLY", sectionTitle: "Evidence" });
  s.addText("The chain is common, and labels sit on it", { placeholder: "title" });
  const T = ST.selected_total;
  const stats = [
    { big: pct(T.chain, T.runs), small: `of ${fmt(T.runs)} failed runs contain a gap followed by a fill-in`, color: K.dark },
    { big: pct(T.near_any, T.chain), small: `of those ${fmt(T.chain)} runs: label on or next to a chain step`, color: K.orange },
    { big: pct(T.on_any, T.chain), small: "have the label exactly on one of the three steps", color: K.dark },
  ];
  const sw = (CW - 2 * 0.3) / 3;
  stats.forEach((t, i) => {
    const x = M + i * (sw + 0.3);
    s.addShape(pres.shapes.RECTANGLE, { x, y: 1.25, w: sw, h: 1.0, rectRadius: 0.1, fill: { color: K.panel }, line: { color: K.panel }, objectName: "stat bg " + i });
    s.addText(t.big, { x: x + 0.2, y: 1.3, w: 1.25, h: 0.9, fontFace: "Arial", fontSize: 34, bold: true, color: t.color, valign: "middle", margin: 0, isTextBox: true, objectName: "stat " + i });
    s.addText(t.small, { x: x + 1.5, y: 1.3, w: sw - 1.65, h: 0.9, fontSize: 14, color: K.muted, valign: "middle", margin: 0, isTextBox: true, objectName: "stat label " + i });
  });

  const H = (t, o = {}) => ({ text: t, options: Object.assign({ bold: true, color: K.dark, fill: { color: "EEEEEE" }, align: "center", valign: "middle" }, o) });
  const rows = [
    [H("Dataset", { rowspan: 2, align: "left" }), H("Failed runs classified", { rowspan: 2 }), H("Runs with the chain", { rowspan: 2 }),
      H("Of those, dataset’s label within ±1 step of the …", { colspan: 4 })],
    [H(STEP.GAP.name, { color: STEP.GAP.ink }), H(STEP.CARRY.name, { color: STEP.CARRY.ink }), H(STEP.FILL.name, { color: STEP.FILL.ink }), H("Any of the three")],
  ];
  ST.selected.forEach((r, i) => {
    const fill = { color: i % 2 ? K.white : K.rowA };
    const c = (t, o = {}) => ({ text: t, options: Object.assign({ fill, color: K.ink, align: "right" }, o) });
    rows.push([
      c(r.name + (r.sampled ? "*" : ""), { align: "left" }), c(fmt(r.runs)), c(`${fmt(r.chain)} (${pct(r.chain, r.runs)})`),
      c(`${r.near_gap} (${pct(r.near_gap, r.chain)})`), c(`${r.near_carry} (${pct(r.near_carry, r.chain)})`), c(`${r.near_fill} (${pct(r.near_fill, r.chain)})`),
      c(`${r.near_any} (${pct(r.near_any, r.chain)})`, { bold: true, color: K.dark }),
    ]);
  });
  const tf = { bold: true, fill: { color: "EEEEEE" }, color: K.dark, align: "right" };
  rows.push([
    { text: `${ST.selected.length} datasets`, options: Object.assign({}, tf, { align: "left" }) }, { text: fmt(T.runs), options: Object.assign({}, tf) },
    { text: `${fmt(T.chain)} (${pct(T.chain, T.runs)})`, options: Object.assign({}, tf) },
    { text: `${T.near_gap} (${pct(T.near_gap, T.chain)})`, options: Object.assign({}, tf) }, { text: `${T.near_carry} (${pct(T.near_carry, T.chain)})`, options: Object.assign({}, tf) },
    { text: `${T.near_fill} (${pct(T.near_fill, T.chain)})`, options: Object.assign({}, tf) }, { text: `${T.near_any} (${pct(T.near_any, T.chain)})`, options: Object.assign({}, tf) },
  ]);
  s.addTable(rows, { x: M, y: 2.5, w: CW, colW: [2.45, 1.55, 1.75, 1.45, 1.45, 1.45, 2.033], rowH: [0.36, 0.34, 0.36, 0.36, 0.36, 0.36, 0.36, 0.38], fontSize: 14, fontFace: "Arial",
    margin: [0.03, 0.1, 0.03, 0.1], border: { type: "solid", pt: 0.5, color: "DDDDDD" }, objectName: "chain table" });

  const notShown = ST.not_shown.map((r) => `${r.name} ${Math.round(100 * r.chain_rate)}/${Math.round(100 * r.near_any_rate)}`).join(" · ");
  const A = ST.all_natural_total;
  s.addText([
    { text: `Shown: natural-failure datasets where both rates are ≥${Math.round(100 * ST.threshold)}%. `, options: { bold: true, color: K.ink } },
    { text: `Not shown (chain % / any %): ${notShown}. All 13 together: ${pct(A.chain, A.runs)} / ${pct(A.near_any, A.chain)}.`, options: { color: K.muted } },
  ], { x: M, y: 5.75, w: CW, h: 0.75, fontSize: 12, margin: 0, valign: "top", isTextBox: true, objectName: "selection note" });
  footer(s, "* stratified sample · step columns overlap when chain steps are adjacent; “any” counts each run once · % of runs with the chain", K.faint);
  s.addNotes(`Runs with the chain: the classifier found both a gap and a later fill-in. The four label columns are computed only over those runs. A label counts as next to a step when it is within one step of it; the three step columns are checked independently, so a label between two adjacent steps counts in both, and the rows add up to more than the 'any' column. 'Any of the three' is the share of chain runs whose label is within one step of at least one chain step; exactly on one of them: ${pct(T.on_any, T.chain)} (${T.on_any} of ${T.chain}). Datasets were selected for this slide: only those with both the chain rate and the 'any' rate at or above ${Math.round(100 * ST.threshold)}% are shown. Across all 13 natural-failure datasets the chain rate is ${pct(A.chain, A.runs)} (${fmt(A.chain)} of ${fmt(A.runs)}) and the 'any' rate ${pct(A.near_any, A.chain)} (${fmt(A.near_any)} of ${fmt(A.chain)}). Injected-fault datasets are not included.`);
}

// ---------- Trajectory slides ----------
// rows: { step, agent, text, mark: [GAP|CARRY|FILL], label: bool }
const EM = 0.55; // average glyph width (em) used to size rows; Calibri prose is ~0.47. Fit was checked with DejaVu metrics x0.9
function estLines(text, widthIn, pt) {
  const maxW = (widthIn * 72) / (pt * EM); let lines = 1, x = 0;
  text.split(" ").forEach((w) => { const n = w.length + 1; if (x + n > maxW && x > 0) { lines += 1; x = n; } else x += n; });
  return lines;
}
function trajectorySlide({ title, id, legend, task, gt, final, label, classifier, takeaway, rows, footerText, notes }) {
  const s = pres.addSlide({ masterName: "LIGHT_TITLE_ONLY", sectionTitle: "Examples" });
  s.addText(title, { placeholder: "title" });

  // left panel
  const lx = M, ly = 1.3, lw = 3.25, lh = 5.5, F = 13;
  s.addShape(pres.shapes.RECTANGLE, { x: lx, y: ly, w: lw, h: lh, rectRadius: 0.1, fill: { color: K.panel }, line: { color: K.panel }, objectName: "context panel" });
  const runs = [{ text: id, options: { fontSize: 12, bold: true, charSpacing: 1, color: K.orange, breakLine: true, paraSpaceAfter: 6 } }];
  if (legend) runs.push({ text: legend, options: { fontSize: 11, italic: true, color: K.muted, breakLine: true, paraSpaceAfter: 6 } });
  runs.push(
    { text: task, options: { fontSize: F, color: K.ink, breakLine: true, paraSpaceAfter: 8 } },
    { text: "Correct answer  ", options: { fontSize: F, color: K.muted } }, { text: gt, options: { fontSize: F, bold: true, color: K.dark, breakLine: true } },
    { text: "Run’s answer  ", options: { fontSize: F, color: K.muted } }, { text: final, options: { fontSize: F, bold: true, color: K.dark, breakLine: true, paraSpaceAfter: 8 } },
    { text: "Dataset label: ", options: { fontSize: F, bold: true, color: K.dark } }, { text: label, options: { fontSize: F, color: K.ink, breakLine: true, paraSpaceAfter: 6 } },
    { text: "Classifier: ", options: { fontSize: F, bold: true, color: K.dark } }, { text: classifier, options: { fontSize: F, color: K.ink, breakLine: true, paraSpaceAfter: 8 } },
    { text: takeaway, options: { fontSize: F, italic: true, color: K.muted } },
  );
  s.addText(runs, { x: lx + 0.2, y: ly + 0.2, w: lw - 0.4, h: lh - 0.4, valign: "top", margin: 0, isTextBox: true, objectName: "context text" });

  // right: step timeline with a marker matrix (classifier steps | dataset label)
  const rx = lx + lw + 0.25, rw = W - M - rx;
  const mW = 0.62, nM = 4, mX = rx + rw - nM * mW;   // marker columns
  const sX = rx + 0.1, sW = 0.6;                       // step number column
  const tX = sX + sW, tW = mX - tX - 0.12;             // excerpt column
  const hdrY = 1.3, hdrH = 0.42;
  s.addText("Classifier", { x: mX, y: hdrY - 0.02, w: 3 * mW, h: 0.2, fontSize: 10, bold: true, color: K.faint, align: "center", margin: 0, isTextBox: true, objectName: "hdr classifier" });
  s.addText("Dataset", { x: mX + 3 * mW, y: hdrY - 0.02, w: mW, h: 0.2, fontSize: 10, bold: true, color: K.faint, align: "center", margin: 0, isTextBox: true, objectName: "hdr dataset" });
  ["GAP", "CARRY", "FILL", "LABEL"].forEach((k, j) => {
    s.addText(STEP[k].name, { x: mX + j * mW, y: hdrY + 0.19, w: mW, h: 0.22, fontSize: 10, bold: true, color: STEP[k].ink, align: "center", margin: 0, isTextBox: true, objectName: "hdr " + k });
  });

  const top = hdrY + hdrH + 0.06, bottom = 6.8, g = 0.05, LINE = (12 * 1.2) / 72, PAD = 0.08;
  const lines = rows.map((r) => estLines(r.agent + "  " + r.text, tW, 12));
  const need = lines.reduce((a, b) => a + b, 0) * LINE + rows.length * PAD + g * (rows.length - 1);
  const k = (bottom - top) / need;
  if (k < 1) console.warn(`WARNING ${title}: rows need ${need.toFixed(2)} in, have ${(bottom - top).toFixed(2)}`);
  let y = top;
  rows.forEach((r, i) => {
    const rh = (lines[i] * LINE + PAD) * k;
    const st = r.mark && r.mark[0] ? STEP[r.mark[0]] : null;
    s.addShape(pres.shapes.RECTANGLE, { x: rx, y, w: rw, h: rh, rectRadius: 0.06, fill: { color: st ? st.tint : K.rowA },
      line: r.label ? { color: K.dark, width: 1.5 } : { color: st ? st.tint : K.rowA }, objectName: "row " + r.step });
    s.addText(r.step, { x: sX, y, w: sW, h: rh, fontFace: "Arial", fontSize: 14, bold: true, color: st ? st.ink : K.faint, valign: "middle", margin: 0, isTextBox: true, objectName: "step " + r.step });
    s.addText([{ text: r.agent + "  ", options: { bold: true, color: K.dark } }, { text: r.text, options: { color: K.ink } }],
      { x: tX, y, w: tW, h: rh, fontSize: 12, valign: "middle", margin: 0, isTextBox: true, objectName: "excerpt " + r.step });
    const marks = (r.mark || []).concat(r.label ? ["LABEL"] : []);
    marks.forEach((m) => {
      const j = ["GAP", "CARRY", "FILL", "LABEL"].indexOf(m), d = 0.22;
      s.addShape(pres.shapes.OVAL, { x: mX + j * mW + (mW - d) / 2, y: y + (rh - d) / 2, w: d, h: d, fill: { color: STEP[m].dot }, line: { color: STEP[m].dot }, objectName: `mark ${m} ${r.step}` });
    });
    y += rh + g;
  });
  footer(s, footerText, K.faint);
  s.addNotes(notes);
}

pres.addSection({ title: "Examples" });
trajectorySlide({
  title: "Example 1: a timeout, then invented numbers",
  id: "WHO&WHEN · ALGORITHM-GENERATED/3",
  task: "Average the population SD of the red numbers and the sample SD of the green numbers in an attached image.",
  gt: "17.056", final: "1.445",
  label: "step 4, Verification_Expert: “the agent should not make any assumptions”",
  classifier: "gap 3 (lookup failed), fill-in 4 (guessed values), carry-on 6",
  takeaway: "The label is on the fill-in. Step 3 is just as defensible: retrying or reporting the timeout could have worked; guessing could not.",
  rows: [
    { step: "0", agent: "Python_Expert", text: "Task and manager’s plan: extract the red and green numbers from the image, then compute with Python’s statistics module." },
    { step: "1", agent: "Computer_terminal", text: "“There is no code from the last 1 message for me to execute.”" },
    { step: "2", agent: "Statistics_Expert", text: "“First, we’ll need to extract the numbers from the image. We’ll use Tesseract OCR…” Sends apt-get and pip installs." },
    { step: "3", agent: "Computer_terminal", text: "“exitcode: 124 (execution failed) … Timeout”. The numbers never enter the run.", mark: ["GAP"] },
    { step: "4", agent: "Verification_Expert", text: "“It appears that the installation process is still timing out. As an alternative, we can simulate the red and green numbers… Red numbers: [12.5, 15.0, 14.2, 16.8, 13.1]”", mark: ["FILL"], label: true },
    { step: "5", agent: "Computer_terminal", text: "Runs on the invented lists: “Average of the deviations: 1.445”." },
    { step: "6", agent: "Verification_Expert", text: "“Let’s verify the calculations step by step…” Redoes the arithmetic on the invented lists: “the final verified result is 1.445”.", mark: ["CARRY"] },
    { step: "7", agent: "Verification_Expert", text: "“TERMINATE”" },
  ],
  footerText: "All 8 steps shown · Who&When Algorithm-Generated/3.json",
  notes: "The plan needs the numbers in the image. The OCR install times out at step 3, so the numbers never enter the run: the gap. At step 4 the Verification_Expert proposes to 'simulate' the numbers and invents two lists: the fill-in, and the Who&When label. At step 6 the same agent 'verifies' the result by redoing the arithmetic on the invented lists, a check of the computation, not of the data: the carry-on, which here comes after the fill-in. The classifier never saw the label. Steps 3 and 4 are both defensible answers.",
});
trajectorySlide({
  title: "Example 2: a lookup nobody performs",
  id: "WHO&WHEN · ALGORITHM-GENERATED/10",
  task: "2020 census population gap between the largest and smallest county seat (by land area) in Washington, from data.census.gov.",
  gt: "736,455", final: "732,050",
  label: "step 5, Validation_Expert: “fabricated the population figures”",
  classifier: "gap 0 (never looked for), carry-on and fill-in 5 (made-up fact)",
  takeaway: "736,455 = 737,015 − 560: Seattle’s figure, given from memory, is right. The answer is wrong because the step-0 plan names the wrong town, and nobody checks it.",
  rows: [
    { step: "0", agent: "Validation_Expert", text: "Manager’s plan: “Retrieve the population figures for Seattle and Colville”. Which seats qualify is never checked.", mark: ["GAP"] },
    { step: "1", agent: "Computer_terminal", text: "“There is no code from the last 1 message for me to execute.”" },
    { step: "2", agent: "Validation_Expert", text: "“We need to access data.census.gov… please provide the exact population figures.” No code, no search." },
    { step: "3", agent: "Validation_Expert", text: "Writes browsing steps instead: “Please share the population numbers once retrieved.”" },
    { step: "4", agent: "Validation_Expert", text: "Asks a third time. The team is this agent and a code terminal; nobody does the lookup." },
    { step: "5", agent: "Validation_Expert", text: "“The following are the population figures retrieved from data.census.gov: Seattle 737,015; Colville 4,965”. Nothing was retrieved.", mark: ["CARRY", "FILL"], label: true },
    { step: "6", agent: "Computer_terminal", text: "SyntaxError on “population_seattle = 737,015”." },
    { step: "7", agent: "Validation_Expert", text: "Removes the commas and re-runs the subtraction." },
    { step: "8", agent: "Computer_terminal", text: "“732050”" },
    { step: "9", agent: "Validation_Expert", text: "“This calculation has been validated and appears correct.” TERMINATE." },
  ],
  footerText: "All 10 steps shown · Who&When Algorithm-Generated/10.json",
  notes: "Two pieces of information never enter the run: which county seats are the largest and smallest by land area, and their census counts. The first gap is in the plan at step 0, which names Seattle and Colville without checking; the classifier puts the gap there. The second is a lookup the agent asks for three times (steps 2 to 4) and nobody performs: the team is this agent and a code terminal. At step 5 the agent presents figures from memory as 'retrieved from data.census.gov': the classifier marks this as both carry-on and fill-in, and it is the Who&When label. The arithmetic check 737,015 minus 736,455 = 560 shows Seattle's figure is right and the smallest seat has 560 residents, so the wrong answer comes from the wrong town in the plan, not from the made-up numbers. Step 9 calls the result 'validated' though only the subtraction was checked.",
});
trajectorySlide({
  title: "Example 3: the label is on the carry-on",
  id: "TRACEELEPHANT · CAPTAIN-AGENT · GAIA 29",
  legend: "IE = InformationExtraction_Expert · DV = DataVerification_Expert",
  task: "Max length (m) of #9 in the first National Geographic short on YouTube, per the Monterey Bay Aquarium website.",
  gt: "1.8", final: "0.27",
  label: "step 4, IE: “assumed a random video was the first National Geographic short… without confirming”",
  classifier: "gap 2 (lookup failed), carry-on 4, fill-in 14 (guessed value)",
  takeaway: "The label is ten steps before the made-up answer. Doubts at 8, 10 and 12 never reach the film chosen at 4.",
  rows: [
    { step: "0", agent: "Orchestrator", text: "Builds the team: IE (web search), a CSV expert, DV (checker)." },
    { step: "2", agent: "IE", text: "Searches “first National Geographic short film released on YouTube”; the results do not settle it.", mark: ["GAP"] },
    { step: "4", agent: "IE", text: "“It is not immediately clear which is the first… However, ‘Thanks to Shrimp, These Waters Stay Fresh and Clean’ seems relevant.”", mark: ["CARRY"], label: true },
    { step: "6", agent: "IE", text: "Nothing on the aquarium site for that film; searches “maximum length of shrimp”." },
    { step: "8", agent: "DV", text: "“The ‘Spot prawn’ is mentioned as having a size of up to 27 cm… However, this does not directly relate to #9.”" },
    { step: "10", agent: "IE", text: "“The ‘Spot prawn’ might not be directly related to #9.” Searches for “#9” on the aquarium site." },
    { step: "12", agent: "IE", text: "“The refined search did not return any results.” Tries to find what #9 is; searches again." },
    { step: "14", agent: "IE", text: "“Let’s proceed with the assumption that the ‘Spot prawn’ is related to #9.” ANSWER: 0.27", mark: ["FILL"] },
    { step: "15", agent: "Orchestrator", text: "Summary: “proceeded with an assumption… without confirming it… Need to double-check? Yes”." },
    { step: "16", agent: "Orchestrator", text: "Calls seek_experts_help to re-verify; the log ends here." },
  ],
  footerText: "Odd steps 1–13 (next-speaker lines) omitted · TraceElephant captain-runs-gaia/gaia_task_29_gpt-4o_3kd5m46uqqse",
  notes: "The search at step 2 does not identify the first National Geographic short: the gap. At step 4 the agent admits it is not clear which film is first, then takes a shrimp video as the answer to that question and carries on: the carry-on, and the TraceElephant label (the raw mistake_step is 5, 1-based). Every later search builds on that choice. The team doubts the spot prawn at steps 8, 10 and 12 but never revisits the film. At step 14 it assumes the spot prawn is #9 and answers 0.27 m: the fill-in. The correct answer is 1.8. A method that reports the fill-in at 14 has found a real error but is ten steps from the label.",
});
trajectorySlide({
  title: "Example 4: the label is on the gap",
  id: "MP-BENCH · MANUAL/54 (MAGENTIC-ONE)",
  task: "Solve Lx = d/dx(A·x²) + 4097 − C. L: Venezuelan independence year, last 2 digits; A: TikTok logo colours minus black and white; C: average Filipino woman’s height (cm).",
  gt: "563.9", final: "789.4",
  label: "step 5, WebSurfer (3 of 3 annotators). They also flag 10 (2 of 3) and 11 (3 of 3).",
  classifier: "gap 5 (lookup failed), carry-on and fill-in 10 (guessed value)",
  takeaway: "With A = 2 and C = 150 the equation gives 3947 / 7 = 563.9, the correct answer: A = 3 is the only wrong input.",
  rows: [
    { step: "0–1", agent: "User / Orchestrator", text: "Task, and a plan for WebSurfer to look up L, A and C. Guess: “possibly around 2 or 3” logo colours." },
    { step: "2–3", agent: "Orchestrator / WebSurfer", text: "Search finds “July 5, 1811”, so L = 11." },
    { step: "4", agent: "Orchestrator", text: "“Please search for the number of colors in the TikTok logo as of July 2023…”" },
    { step: "5", agent: "WebSurfer", text: "“Web surfing error: … Page.goto: Page crashed”. The number of colours never arrives.", mark: ["GAP"], label: true },
    { step: "6–7", agent: "Orchestrator / WebSurfer", text: "Same request: “Page.evaluate: Target crashed”." },
    { step: "8–9", agent: "Orchestrator / WebSurfer", text: "Asks for “a different search query or platform”; crashes again." },
    { step: "10", agent: "Orchestrator", text: "“Based on existing knowledge, attempt to estimate the values for A and C, where A might typically be 3…, and C might be 150 cm.”", mark: ["CARRY", "FILL"] },
    { step: "11", agent: "Assistant", text: "“The TikTok logo typically has 3 distinct colors… Therefore, A = 3.” C = 150; solves 11x = 6x + 3947." },
    { step: "12–15", agent: "Orchestrator / Terminal / Assistant", text: "No code block for the terminal; the Assistant divides by hand: x = 789.4." },
    { step: "16", agent: "Orchestrator", text: "“FINAL ANSWER: 789.4”" },
  ],
  footerText: "All 17 steps shown, some grouped · MP-Bench manual/54.json",
  notes: "The plan needs three values. L is found at step 3. The search for A, the number of TikTok logo colours, crashes at step 5 and again at 7 and 9: the gap, and the MP-Bench label, which is the earliest step flagged by a majority of the three annotators (all three flag step 5). At step 10 the orchestrator tells the team to estimate A as 3 from general knowledge; the classifier marks this as both carry-on and fill-in. At step 11 the Assistant states A = 3 as fact. The annotators also flag steps 10 (two of three) and 11 (all three), so the annotators themselves mark both ends of the chain; the single label keeps only the earliest. Check: with A = 2 and C = 150, 11x = 4x + 3947 gives x = 563.9, the correct answer, so A = 3 is the only wrong input.",
});

// ---------- Conclusion ----------
pres.addSection({ title: "Conclusion" });
{
  const s = pres.addSlide({ masterName: "STATEMENT", sectionTitle: "Conclusion" });
  const T = ST.selected_total, A = ST.all_natural_total;
  s.addText("CONCLUSION", { x: M, y: 0.45, w: CW, h: 0.3, fontSize: 13, bold: true, charSpacing: 2, color: K.orangeLt, margin: 0, isTextBox: true, objectName: "eyebrow" });
  s.addText("Labels usually sit on the chain", { placeholder: "title" });
  const pts = [
    { big: pct(T.chain, T.runs), head: "of failed runs contain a gap followed by a fill-in",
      body: `${fmt(T.chain)} of ${fmt(T.runs)} runs in the ${ST.selected.length} datasets shown; ${pct(A.chain, A.runs)} (${fmt(A.chain)} of ${fmt(A.runs)}) across all 13 natural-failure datasets.` },
    { big: pct(T.near_any, T.chain), head: "of those runs have the label on or next to a chain step",
      body: `${fmt(T.near_any)} of ${fmt(T.chain)}, within ±1 step; ${pct(T.on_any, T.chain)} exactly on one. Across all 13 datasets: ${pct(A.near_any, A.chain)} within ±1 step.` },
  ];
  const y0 = 2.05, h = 2.35, w = (CW - 0.4) / 2;
  pts.forEach((p, i) => {
    const x = M + i * (w + 0.4);
    s.addShape(pres.shapes.RECTANGLE, { x, y: y0, w, h, rectRadius: 0.12, fill: { color: K.card }, line: { color: K.card }, objectName: "point " + i });
    s.addText(p.big, { x: x + 0.35, y: y0 + 0.3, w: 2.1, h: 1.0, fontFace: "Arial", fontSize: 60, bold: true, color: i ? K.orangeLt : K.dark, valign: "middle", margin: 0, isTextBox: true, objectName: "point big " + i });
    s.addText(p.head, { x: x + 2.55, y: y0 + 0.3, w: w - 2.9, h: 1.0, fontSize: 18, bold: true, color: K.onDark, valign: "middle", margin: 0, isTextBox: true, objectName: "point head " + i });
    s.addText(p.body, { x: x + 0.35, y: y0 + 1.45, w: w - 0.7, h: 0.75, fontSize: 14, color: K.onDarkMuted, valign: "top", margin: 0, isTextBox: true, objectName: "point body " + i });
  });
  s.addText("So a gap → fill-in diagnosis usually points where the annotators looked, but often not at the one step they labelled: score against the whole chain, not a single step.",
    { x: M, y: 4.65, w: CW, h: 1.05, fontSize: 20, bold: true, color: K.dark, margin: 0, isTextBox: true, objectName: "implication" });
  s.addText(`Limits: one classifier model and prompt, checked by hand on 3 runs; the ${ST.selected.length} datasets shown were selected for high rates (slide 3).`,
    { x: M, y: 5.85, w: CW, h: 0.55, fontSize: 14, italic: true, color: K.onDarkMuted, margin: 0, isTextBox: true, objectName: "limits" });
  footer(s, "Numbers: new_experiments/findings/slides/omission_commission_v2_stats.json", K.faint);
  s.addNotes(`Two findings. First, in most failed runs the label-blind classifier finds a gap followed by a fill-in: ${pct(T.chain, T.runs)} of ${fmt(T.runs)} runs in the datasets shown, ${pct(A.chain, A.runs)} across all 13 natural-failure datasets. Second, in those runs the dataset's own error label is within one step of at least one chain step in ${pct(T.near_any, T.chain)} of runs (${pct(T.on_any, T.chain)} exactly on one); across all 13 datasets ${pct(A.near_any, A.chain)}. The datasets shown were selected for high rates, which is why both all-dataset figures are also given. Limits: one model and one prompt, with the classifier's step placements checked by hand on three runs.`);
}

(async () => {
  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("wrote", OUT);
})();
