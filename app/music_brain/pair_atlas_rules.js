// The console's own rules, run in node for the offline pair atlas (app/music_brain/pair_atlas.py).
// Nothing is re-implemented here: the browser modules are required unmodified, the way app/sim does.
// stdin: {tracks: {id: {bar, anchor, bars: {drums: [], bass: [], vocals: [], other: []}}}, jobs: [...]}
// stdout: {results: [...]} (one per job, same order). Job kinds:
//   {kind: "hold", a, b, aT, bT, gap, keyScore, roomBars, barS, barA, barB, bRap, aVox, bVox}
//        -> stem-moves core.holdPlan (merge -> hold -> transition feasibility)
//   {kind: "recipe", o} -> autopilot core.decideRecipe(o, tempoRule) (o.mashupFits is a bool here)
//   {kind: "peak", p}   -> dj-mind core.peakTransition(p) (double drop / drop swap)
//   {kind: "camelot", a, b} / {kind: "lock", aEff, bBpm} -> parity probes for the tests
"use strict";
const path = require("path");
const S = path.join(__dirname, "..", "ui", "static");
const ap = require(path.join(S, "autopilot.js"));
const tempoRule = require(path.join(S, "tempo-rule.js"));
const sm = require(path.join(S, "stem-moves.js"));
const dm = require(path.join(S, "dj-mind.js"));

function barsFrom(track, songT, n) {
  // per-bar stem RMS starting at the bar that holds songT (the grid the Python side cached)
  const i0 = Math.max(0, Math.round((songT - track.anchor) / track.bar));
  const out = {};
  for (const name of ["drums", "bass", "vocals", "other"]) out[name] = (track.bars[name] || []).slice(i0, i0 + n);
  return out;
}

function hold(tracks, j) {
  const A = tracks[j.a], B = tracks[j.b];
  if (!A || !B || !A.bars || !B.bars) return { ok: false, gate: "stems", reason: "stem energy unmeasured", tried: [] };
  const n = Math.max(1, Math.min(sm.HOLD_MAX_PHRASES, Math.floor((j.roomBars - 10) / 8))) * 8 + 10;
  const eA = barsFrom(A, j.aT, n), eB = barsFrom(B, j.bT, n);
  const hp = sm.holdPlan({
    gap: j.gap, keyScore: j.keyScore, roomBars: j.roomBars, barS: j.barS, aT: j.aT, bT: j.bT,
    barA: j.barA, barB: j.barB, bRap: !!j.bRap, eA, eB, aVox: j.aVox || [], bVox: j.bVox || [],
  });
  if (!hp.ok) return { ok: false, gate: hp.gate, reason: hp.reason, tried: hp.tried || [] };
  return {
    ok: true, M: hp.M, holdBars: hp.holdBars, holdPhrases: hp.holdPhrases,
    pick: hp.pick && { label: hp.pick.label, score: hp.pick.score, combo: hp.pick.combo },
    phases: hp.phases, tried: hp.tried || [],
  };
}

function recipe(j) {
  const o = Object.assign({}, j.o);
  const fits = !!o.mashupFits;
  o.mashupFits = () => fits;
  const r = ap.decideRecipe(o, tempoRule);
  // a move learned from studied sets replaces the recipe when the console allows it for these facts
  const learned = j.pick ? ap.learnedRecipe(j.pick, {
    recipe: r.recipe, keyScore: o.keyScore, blend: r.blend, oneSong: r.oneSong, vocalRule: r.vocalRule,
    stemsBoth: r.stemsBoth, mashupFits: fits, layer: false,
  }) : null;
  return {
    learned: learned && learned.recipe, learnedWhy: learned && learned.why,
    recipe: r.recipe, dropLayer: !!r.dropLayer, vocalRule: !!r.vocalRule, vocalShort: !!r.vocalShort,
    vocalCut: r.vocalCut || "", keyRewrite: r.keyRewrite || null, beat: !!(r.lockS && r.lockS.beat),
    why: r.lockS && r.lockS.why,
  };
}

function run(input) {
  const tracks = input.tracks || {};
  return (input.jobs || []).map((j) => {
    try {
      if (j.kind === "hold") return hold(tracks, j);
      if (j.kind === "recipe") return recipe(j);
      if (j.kind === "peak") return dm.peakTransition(Object.assign({ log: [], trackIdx: 1, now: 0 }, j.p));
      if (j.kind === "camelot") return dm.camelotScore(j.a, j.b);
      if (j.kind === "lock") return tempoRule.lockRate(j.aEff, j.bBpm);
      if (j.kind === "keysafe") return ap.keySafeRecipe(j.recipe, j.keyScore);
      if (j.kind === "energy") return ap.energyStepOk(j.cur, j.nxt, j.o || {});
      return { error: `unknown job ${j.kind}` };
    } catch (e) {
      return { error: String(e && e.message || e) };
    }
  });
}

let buf = "";
process.stdin.setEncoding("utf8");
process.stdin.on("data", (d) => { buf += d; });
process.stdin.on("end", () => {
  const out = run(JSON.parse(buf || "{}"));
  process.stdout.write(JSON.stringify({ results: out }));
});
