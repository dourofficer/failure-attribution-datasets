const pptxgen = require("pptxgenjs");
const { applyTheme } = require("/dataDisk/home/thanhdo/.claude-personal/skills/synced/d34f2cba-6383-4e15-b07d-90e2e3b106f6_3cac4ae6-fa7c-4812-ac46-3d0de7f247f9/pptx/scripts/apply_theme.js");

const OUT = process.argv[2];
const THEME = {
  name: "Omission Commission",
  headFontFace: "Cambria",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "1B2430", lt1: "FFFFFF", dk2: "2D3748", lt2: "F1F4F7",
    accent1: "A8521A", accent2: "2F5D9E", accent3: "5F6B7A",
    accent4: "F2A866", accent5: "9DBDF0", accent6: "B8C2CE",
    hlink: "2F5D9E", folHlink: "5F6B7A",
  },
};
const K = {
  dark: "1B2430", card: "263241", ink: "2D3748", muted: "4A5568", faint: "5A6472",
  orange: "A8521A", orangeLt: "F2A866", blue: "2F5D9E", blueLt: "9DBDF0", gray: "5F6B7A", grayLt: "B8C2CE",
  onDark: "E8ECF0", onDarkMuted: "AEB8C4", white: "FFFFFF", panel: "F1F4F7",
};
const PILL = {
  OMISSION: { fill: "F6E3D3", color: "8A4110" },
  COMMISSION: { fill: "DCE6F5", color: "234A80" },
  ACCEPTANCE: { fill: "E3E6EA", color: "3F4955" },
  LABEL: { fill: K.dark, color: K.white },
};
const ROWFILL = { OMISSION: "FBF0E6", COMMISSION: "EAF1FA", ACCEPTANCE: "EEF0F3", none: "F7F8FA" };

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.333 x 7.5
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "Omission → Commission";

const W = 13.333, M = 0.6, CW = W - 2 * M;

pres.defineSlideMaster({
  title: "DARK_STATEMENT",
  background: { color: K.dark },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: M, y: 0.8, w: CW, h: 0.8, fontFace: "Cambria", fontSize: 40, bold: true, color: "F7F6F2", margin: 0, valign: "top" }, text: "" } },
  ],
  slideNumber: { x: W - M - 0.8, y: 6.95, w: 0.8, h: 0.3, fontFace: "Calibri", fontSize: 11, color: "8E9AA8", align: "right" },
});
pres.defineSlideMaster({
  title: "LIGHT_TITLE_ONLY",
  background: { color: K.white },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: M, y: 0.45, w: CW, h: 0.7, fontFace: "Cambria", fontSize: 32, bold: true, color: K.dark, margin: 0, valign: "top" }, text: "" } },
  ],
  slideNumber: { x: W - M - 0.8, y: 6.95, w: 0.8, h: 0.3, fontFace: "Calibri", fontSize: 11, color: K.faint, align: "right" },
});

function footer(slide, text, color) {
  slide.addText(text, { x: M, y: 6.95, w: CW - 1.0, h: 0.3, fontSize: 11, color, margin: 0, isTextBox: true, objectName: "source" });
}
function pill(slide, label, x, y, w) {
  const p = PILL[label];
  slide.addText(label, { shape: pres.shapes.ROUNDED_RECTANGLE, rectRadius: 0.14, x, y, w, h: 0.3, fill: { color: p.fill }, color: p.color,
    fontSize: 11, bold: true, charSpacing: 1, align: "center", valign: "middle", margin: 0, isTextBox: true, objectName: "pill " + label });
}

// ---------- Slide 1: the phenomenon ----------
pres.addSection({ title: "Phenomenon" });
{
  const s = pres.addSlide({ masterName: "DARK_STATEMENT", sectionTitle: "Phenomenon" });
  s.addText("OMISSION → COMMISSION", { x: M, y: 0.45, w: CW, h: 0.3, fontSize: 13, bold: true, charSpacing: 2, color: K.orangeLt, margin: 0, isTextBox: true, objectName: "eyebrow" });
  s.addText("One failure, two defensible error steps", { placeholder: "title" });
  s.addText("A required item never arrives; a later step fills the gap with a claim nothing supports.",
    { x: M, y: 1.65, w: CW, h: 0.5, fontSize: 18, color: "BFC8D2", margin: 0, isTextBox: true, objectName: "lead" });

  const cards = [
    { n: "1", head: "OMISSION", accent: K.orangeLt, desc: "A required fact, page, tool result or constraint never enters the agent’s working state.",
      sub: "Invisible in the step’s own text.", kinds: "never sought · attempt failed · delegated, not done · visible, not extracted" },
    { n: "2", head: "ACCEPTANCE (OFTEN)", accent: K.grayLt, desc: "A later step carries on as if the item had arrived, e.g. an orchestrator ledger saying “gathered”.",
      sub: "Turns the gap into a commitment.", kinds: "" },
    { n: "3", head: "COMMISSION", accent: K.blueLt, desc: "A step asserts a value or takes an action that no observation supports.",
      sub: "Visible: an unsupported claim.", kinds: "assumed values · fabricated fact · misread evidence · action without basis" },
  ];
  const arrowW = 0.4, gap = 0.15, cardW = (CW - 2 * arrowW - 4 * gap) / 3, y0 = 2.45, h = 3.2;
  cards.forEach((c, i) => {
    const x = M + i * (cardW + arrowW + 2 * gap);
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: y0, w: cardW, h, rectRadius: 0.12, fill: { color: K.card }, line: { color: K.card }, objectName: "card " + c.head });
    s.addText(c.n, { shape: pres.shapes.OVAL, x: x + 0.28, y: y0 + 0.28, w: 0.5, h: 0.5, fill: { color: c.accent }, color: K.dark, fontSize: 18, bold: true,
      align: "center", valign: "middle", margin: 0, isTextBox: true, objectName: "badge " + c.n });
    s.addText(c.head, { x: x + 0.95, y: y0 + 0.28, w: cardW - 1.15, h: 0.5, fontSize: 15, bold: true, charSpacing: 1, color: c.accent, valign: "middle", margin: 0, isTextBox: true });
    const runs = [
      { text: c.desc, options: { fontSize: 15, color: K.onDark, breakLine: true, paraSpaceAfter: 8 } },
      { text: c.sub, options: { fontSize: 13, color: K.onDarkMuted, breakLine: !!c.kinds, paraSpaceAfter: 8 } },
    ];
    if (c.kinds) runs.push({ text: c.kinds, options: { fontSize: 13, italic: true, color: K.onDarkMuted } });
    s.addText(runs, { x: x + 0.28, y: y0 + 1.0, w: cardW - 0.56, h: h - 1.2, valign: "top", margin: 0, isTextBox: true, objectName: "card text " + c.n });
    if (i < 2) s.addShape(pres.shapes.RIGHT_ARROW, { x: x + cardW + gap, y: y0 + h / 2 - 0.15, w: arrowW, h: 0.3, fill: { color: "6B7888" }, line: { color: "6B7888" }, objectName: "arrow " + i });
  });
  s.addText("Annotators pick either end; single-step scoring marks the other end wrong.",
    { x: M, y: 5.95, w: CW, h: 0.5, fontSize: 20, bold: true, color: "F7F6F2", margin: 0, isTextBox: true, objectName: "takeaway" });
  footer(s, "Source: new_experiments/findings/hypotheses.md, X3 and §2b", "8E9AA8");
  s.addNotes("The chain: omission (a required item never enters the run), often an acceptance step (a later step proceeds as if it had), then commission (a step fills the gap with an unsupported claim). The omission is a non-event, so a scorer that reads one step at a time cannot see it. The commission is visible, but most label conventions do not put the label there. Each end is a defensible answer to “where is the error”, so teams split, and exact-step scoring penalises a method that finds the other end.");
}

// ---------- Slide 2: statistics ----------
pres.addSection({ title: "Evidence" });
{
  const s = pres.addSlide({ masterName: "LIGHT_TITLE_ONLY", sectionTitle: "Evidence" });
  s.addText("How often the pair occurs, and where labels land", { placeholder: "title" });

  const stats = [
    { big: "71%", small: "of 1,535 classified failed runs have the omission → commission pair", color: K.dark },
    { big: "61%", small: "contain a real fabrication, not only a forced final answer", color: K.dark },
    { big: "40% vs 7%", small: "of pairs: label on the omission end vs on the commission end", color: K.orange },
  ];
  const sw = (CW - 2 * 0.3) / 3;
  stats.forEach((t, i) => {
    const x = M + i * (sw + 0.3);
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 1.25, w: sw, h: 0.95, rectRadius: 0.1, fill: { color: K.panel }, line: { color: K.panel }, objectName: "stat bg " + i });
    const bw = i === 2 ? 2.1 : 1.2;
    s.addText(t.big, { x: x + 0.2, y: 1.3, w: bw, h: 0.85, fontFace: "Cambria", fontSize: i === 2 ? 26 : 34, bold: true, color: t.color, valign: "middle", margin: 0, isTextBox: true, objectName: "stat " + i });
    s.addText(t.small, { x: x + 0.35 + bw, y: 1.3, w: sw - 0.5 - bw, h: 0.85, fontSize: 13, color: K.muted, valign: "middle", margin: 0, isTextBox: true, objectName: "stat label " + i });
  });

  const hdr = (t, color) => ({ text: t, options: { bold: true, color: color || K.white, fill: { color: K.dark }, align: "right", valign: "middle" } });
  const rows = [[
    { text: "Dataset", options: { bold: true, color: K.white, fill: { color: K.dark }, align: "left", valign: "middle" } },
    hdr("Failed runs classified"), hdr("Pair shape"), hdr("Pair with real fabrication"),
    hdr("Label on omission end", K.orangeLt), hdr("Label on commission end", K.blueLt), hdr("GT never observed"),
  ]];
  const data = [
    ["AgentRx", "73", "59 (81%)", "33 (45%)", "13 (22%)", "9 (15%)", "58% of 12"],
    ["TraceElephant", "213", "173 (81%)", "167 (78%)", "54 (31%)", "16 (9%)", "86% of 119"],
    ["SearchAuditBench*", "149", "119 (80%)", "91 (61%)", "31 (26%)", "13 (11%)", "72% of 713"],
    ["TRAIL", "144", "114 (79%)", "113 (78%)", "36 (32%)", "5 (4%)", "64% of 77"],
    ["Who&When", "183", "142 (78%)", "110 (60%)", "70 (49%)", "9 (6%)", "95% of 134"],
    ["MP-Bench", "273", "197 (72%)", "143 (52%)", "99 (50%)", "7 (4%)", "84% of 195"],
    ["LongRCA*", "118", "78 (66%)", "76 (64%)", "10 (13%)", "6 (8%)", "–"],
    ["SymTrace*", "120", "70 (58%)", "68 (57%)", "52 (74%)", "2 (3%)", "93% of 59"],
    ["AgentHallu*", "144", "80 (56%)", "69 (48%)", "59 (74%)", "1 (1%)", "84% of 204"],
    ["TrajErrBench*", "118", "64 (54%)", "62 (53%)", "18 (28%)", "5 (8%)", "–"],
  ];
  data.forEach((r, i) => {
    const fill = { color: i % 2 ? K.white : "F6F7F9" };
    rows.push(r.map((v, j) => ({ text: v, options: { fill, color: K.ink, align: j ? "right" : "left" } })));
  });
  rows.push(["All ten", "1,535", "1,096 (71%)", "932 (61%)", "442 (40%)", "73 (7%)", ""].map((v, j) =>
    ({ text: v, options: { bold: true, fill: { color: "DCE3EA" }, color: K.dark, align: j ? "right" : "left" } })));
  s.addTable(rows, { x: M, y: 2.4, w: CW, colW: [2.35, 1.5, 1.6, 1.8, 1.65, 1.65, 1.58], rowH: 0.31, fontSize: 12, fontFace: "Calibri",
    margin: [0.03, 0.1, 0.03, 0.1], border: { type: "solid", pt: 0.5, color: "DDE1E6" }, objectName: "pair table" });
  s.addText("Minority where the failure is acting, not knowing: AgentErrorBench 89 / 198 (45%), MemTrace 24 / 45 (53%), HORIZON 6 / 120 (5%).",
    { x: M, y: 6.42, w: CW, h: 0.35, fontSize: 13, color: K.muted, margin: 0, isTextBox: true, objectName: "minority note" });
  footer(s, "* sample of 118–150 · label columns: within ±1 step, % of pairs · GT: substring check over tool outputs, % of checkable runs", K.faint);
  s.addNotes("Instrument: a label-blind classifier (Qwen3.8-27B, thinking on, prompt in inspect/oc_classify.py) sees the task, ground truth, final output and whole trajectory, but not the dataset’s label. It returns the omission, acceptance and commission steps and the overall shape. Starred datasets are stratified samples (seed 0); the rest are every labelled failed run. “Pair with real fabrication” removes pairs whose only commission is a forced final answer in the last two steps of an exhausted run. Label columns: the dataset’s primary label within ±1 step of the omission step (checked first), or of the commission step only (not also near the omission or acceptance). The remaining pairs have the label on the acceptance step or on none of the three. GT never observed: share of checkable failed runs where the ground-truth string appears in no tool or environment output. Caveats: one model and prompt; the classifier is checked against only three hand-read cases; the GT check has no control on successful runs, and derived answers (counts, combinations) would not appear in observations even in a successful run. Source: results/omission_commission/llm_*.jsonl and inspect/oc_provenance_table.py.");
}

// ---------- Trajectory slides ----------
function trajectorySlide({ title, id, task, gt, final, label, classifier, takeaway, rows, footerText, notes }) {
  const s = pres.addSlide({ masterName: "LIGHT_TITLE_ONLY", sectionTitle: "Examples" });
  s.addText(title, { placeholder: "title" });
  // left panel
  const lx = M, ly = 1.3, lw = 3.9, lh = 5.45;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: lx, y: ly, w: lw, h: lh, rectRadius: 0.1, fill: { color: K.panel }, line: { color: K.panel }, objectName: "context panel" });
  s.addText([
    { text: id, options: { fontSize: 13, bold: true, charSpacing: 1, color: K.orange, breakLine: true, paraSpaceAfter: 8 } },
    { text: task, options: { fontSize: 14, color: K.ink, breakLine: true, paraSpaceAfter: 10 } },
    { text: "Ground truth  ", options: { fontSize: 14, color: K.muted } }, { text: gt, options: { fontSize: 14, bold: true, color: K.dark, breakLine: true } },
    { text: "Final answer  ", options: { fontSize: 14, color: K.muted } }, { text: final, options: { fontSize: 14, bold: true, color: K.dark, breakLine: true, paraSpaceAfter: 10 } },
    { text: "Dataset label: ", options: { fontSize: 14, bold: true, color: K.dark } }, { text: label, options: { fontSize: 14, color: K.ink, breakLine: true, paraSpaceAfter: 6 } },
    { text: "Classifier: ", options: { fontSize: 14, bold: true, color: K.dark } }, { text: classifier, options: { fontSize: 14, color: K.ink, breakLine: true, paraSpaceAfter: 10 } },
    { text: takeaway, options: { fontSize: 14, italic: true, color: K.muted } },
  ], { x: lx + 0.25, y: ly + 0.25, w: lw - 0.5, h: lh - 0.5, valign: "top", margin: 0, isTextBox: true, objectName: "context text" });

  // right timeline
  const rx = 4.8, rw = W - M - rx, top = 1.3, bottom = 6.75, g = 0.1;
  const rh = (bottom - top - g * (rows.length - 1)) / rows.length;
  rows.forEach((r, i) => {
    const y = top + i * (rh + g);
    const tag = r.tags && r.tags[0] ? r.tags[0] : "none";
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: rx, y, w: rw, h: rh, rectRadius: 0.08, fill: { color: ROWFILL[tag] }, line: { color: ROWFILL[tag] }, objectName: "row " + r.step });
    s.addText(r.step, { x: rx + 0.15, y: y + 0.08, w: 0.6, h: 0.35, fontFace: "Cambria", fontSize: 16, bold: true, color: tag === "none" ? K.faint : PILL[tag].color, margin: 0, isTextBox: true, objectName: "step " + r.step });
    s.addText([{ text: r.agent + "  ", options: { bold: true, color: K.dark } }, { text: r.text, options: { color: K.ink } }],
      { x: rx + 0.8, y: y + 0.06, w: rw - 0.8 - 1.65, h: rh - 0.12, fontSize: 13, valign: "middle", margin: 0, isTextBox: true, objectName: "excerpt " + r.step });
    (r.tags || []).forEach((t, k) => {
      const n = r.tags.length, ph = 0.3, pg = 0.06;
      const py = y + (rh - (n * ph + (n - 1) * pg)) / 2 + k * (ph + pg);
      pill(s, t, rx + rw - 1.55, py, 1.4);
    });
  });
  footer(s, footerText, K.faint);
  s.addNotes(notes);
}

pres.addSection({ title: "Examples" });
trajectorySlide({
  title: "Example 1: a timeout, then assumed numbers",
  id: "WHO&WHEN · AG/3",
  task: "Average the population SD of the red numbers and the sample SD of the green numbers in an attached image.",
  gt: "17.056", final: "1.445",
  label: "step 4, Verification_Expert",
  classifier: "omission 3 (attempt failed) → commission 4 (unjustified assumption); acceptance 6",
  takeaway: "Step 3 is equally defensible: retrying or reporting the failure could succeed; guessing cannot.",
  rows: [
    { step: "0", agent: "Python_Expert", text: "Task and manager’s plan: read the red and green numbers off the image, then compute." },
    { step: "2", agent: "Statistics_Expert", text: "“Extract the numbers from the image… use Tesseract OCR”; sends apt-get and pip installs." },
    { step: "3", agent: "Computer_terminal", text: "“exitcode: 124 (execution failed) … Timeout”. The numbers never enter the run.", tags: ["OMISSION"] },
    { step: "4", agent: "Verification_Expert", text: "“…still timing out… we can simulate the red and green numbers… Red: [12.5, 15.0, 14.2, 16.8, 13.1]”", tags: ["COMMISSION", "LABEL"] },
    { step: "5", agent: "Computer_terminal", text: "Runs on the assumed lists: “Average of the deviations: 1.445”" },
    { step: "6", agent: "Verification_Expert", text: "“Let’s verify the calculations step by step…” Re-checks the arithmetic, never the data.", tags: ["ACCEPTANCE"] },
    { step: "7", agent: "Verification_Expert", text: "“TERMINATE”" },
  ],
  footerText: "Step 1 (terminal: “no code to execute”) omitted · Who&When Algorithm-Generated/3.json",
  notes: "A clean attempt-failed → unjustified-assumption pair. The plan at step 2 needs the numbers from the image; the OCR install times out at step 3, so the numbers never enter the run. At step 4 the Verification_Expert says it will “simulate” the numbers and invents two lists. Who&When labels step 4 (reason: “the agent should not make any assumptions”). The classifier, which never sees that label, puts the omission at 3, the commission at 4 and an acceptance at 6, where the same agent “verifies” the arithmetic on the invented lists: a check of the computation, not of the data. Either 3 or 4 is a defensible answer to “where is the error”.",
});
trajectorySlide({
  title: "Example 2: a lookup nobody performs",
  id: "WHO&WHEN · AG/10",
  task: "2020 population gap between the largest and smallest county seat (by land area) in Washington, from data.census.gov.",
  gt: "736,455", final: "732,050",
  label: "step 5, Validation_Expert",
  classifier: "omission 0 (never sought) → commission 5 (fabricated fact)",
  takeaway: "The ground truth implies a 560-person seat, so Colville, fixed in the plan at step 0, is the wrong town.",
  rows: [
    { step: "0", agent: "Validation_Expert", text: "Manager’s plan: “Retrieve the population figures for Seattle and Colville”. Which seats qualify is never checked.", tags: ["OMISSION"] },
    { step: "2", agent: "Validation_Expert", text: "Plan: “access data.census.gov to gather… figures for Seattle and Colville”. No tool call follows." },
    { step: "3–4", agent: "Validation_Expert", text: "Asks twice: “Please share the population numbers once retrieved.” No one in the team can browse." },
    { step: "5", agent: "Validation_Expert", text: "“The following are the population figures retrieved from data.census.gov: Seattle 737,015; Colville 4,965”. Nothing was retrieved.", tags: ["COMMISSION", "LABEL"] },
    { step: "6–8", agent: "Terminal / Validation_Expert", text: "SyntaxError on “737,015”; fixed; prints 732050." },
    { step: "9", agent: "Validation_Expert", text: "“This calculation has been validated and appears correct.” TERMINATE." },
  ],
  footerText: "Step 1 (terminal: “no code to execute”) omitted · Who&When Algorithm-Generated/10.json",
  notes: "Two things never enter the run: which county seats are largest and smallest by land area, and their census counts. The first gap is already in the manager’s plan at step 0, which names Seattle and Colville without checking. The second is delegated at steps 3–4 to a lookup that nobody in the team can perform. At step 5 the agent presents figures from memory as “retrieved from data.census.gov”: the commission, and the Who&When label (reason: “fabricated the population figures”). The classifier puts the omission at 0 (never sought) and both acceptance and commission at 5. Arithmetic check: 737,015 − 736,455 = 560, so the ground truth implies a smallest seat of 560 residents, not Colville’s 4,965. Step 9 claims the result “has been validated” though only the subtraction was checked.",
});

(async () => {
  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("wrote", OUT);
})();
