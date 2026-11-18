// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// The lab's readings and table (lab.js; design lfphys/sources/explore_2026-11-14_design.md §2.3): an instrument rounds
// a computed value to its division and carries its declared error; derived columns propagate the error to second order,
// σ_f² = f′²σ² + ½f″²σ⁴ (an error at a stationary point too: review EX1-screens F14); one row per set-up (integrator
// D5); the table kept with its atlas's key; the law of a plot by its (x, y, model) (D4);
// the CSV carries the errors; a value with its error is written to the error's two significant digits. The cases are
// computed by hand. Run from visualizations/: node --test player/js/tests/*.test.mjs
import { test } from "node:test";
import assert from "node:assert/strict";
import { computedFor, csv, derived, fitLines, instrumentText, loadRows, placeRow, pm, reading, readingText, rowOf, setupKey, sig4, variantOf, withUnit } from "../lab.js";
import { fit } from "../fit.js";

const close = (a, b, tol, msg) => assert.ok(Math.abs(a - b) <= tol * Math.max(1, Math.abs(b)), `${msg}: ${a} vs ${b}`);
const tape = { division: 0.001, error: 0.0005 }, ruler = { division: 0.01, error: 0.005 }, prot = { division: 1, error: 0.5 };

test("an instrument rounds to its division and carries its error", () => {
  assert.deepEqual(reading(tape, 0.6774011), { v: 0.677, e: 0.0005 });
  assert.deepEqual(reading(tape, 0.67751), { v: 0.678, e: 0.0005 });
  assert.deepEqual(reading(ruler, 0.6), { v: 0.6, e: 0.005 });
  assert.deepEqual(reading(prot, 44.6), { v: 45, e: 0.5 });
  assert.deepEqual(reading({ division: 0.5 }, 1.26), { v: 1.5, e: 0.25 }, "default: half a division");
  assert.deepEqual(reading({ division: 0.01, error: 0.2 }, 0.4517), { v: 0.45, e: 0.2 }, "a stopwatch: the reaction's error");
  assert.equal(reading(tape, null), null, "nothing to read");
  assert.deepEqual(reading(tape, -0.0001), { v: 0, e: 0.0005 }, "no negative zero");
});

test("derived columns and their errors σ_f² = f′²σ² + ½f″²σ⁴", () => {
  const two = (d1, d2, s) => Math.sqrt((d1 * s) ** 2 + 0.5 * (d2 * s * s) ** 2);
  const r = { v: 0.64, e: 0.005 };
  close(derived("sqrt", r).v, 0.8, 1e-15, "√"); close(derived("sqrt", r).e, two(1 / 1.6, -1 / (4 * 0.512), 0.005), 1e-15, "σ√");
  close(derived("square", r).v, 0.4096, 1e-15, "x²"); close(derived("square", r).e, two(2 * 0.64, 2, 0.005), 1e-15, "σx²");
  const th = { v: 30, e: 0.5 }, rad = Math.PI / 180;
  close(derived("sin2", th).v, Math.sin(Math.PI / 3), 1e-15, "sin 2θ");
  close(derived("sin2", th).e, two(2 * Math.cos(Math.PI / 3) * rad, -4 * Math.sin(Math.PI / 3) * rad * rad, 0.5), 1e-15, "σ sin 2θ");
  // at the stationary point 45°: the first-order term is 0, the second gives √½·4·(π/180)²·0.25 ≈ 2.2·10⁻⁴
  close(derived("sin2", { v: 45, e: 0.5 }).e, Math.SQRT1_2 * 4 * rad * rad * 0.25, 1e-12, "σ sin 2θ at 45°");
  assert.ok(derived("sin2", { v: 45, e: 0.5 }).e > 1e-4, "never ± 0 at the maximum (F14)");
  close(derived("inverse", { v: 2, e: 0.1 }).e, two(-1 / 4, 2 / 8, 0.1), 1e-15, "σ 1/x");
  close(derived("log", { v: 2, e: 0.1 }).e, two(0.5, -0.25, 0.1), 1e-15, "σ ln x");
  assert.equal(derived("sqrt", null), null);
  assert.equal(derived("sqrt", { v: -1, e: 0 }), null, "no value where the operation has none");
});

test("a row of the step's columns from the readings; the CSV with the errors", () => {
  const cols = [{ id: "h", label: "h, m", from: "ruler" }, { id: "L", label: "L, m", from: "tape" }, { id: "sqrt_h", label: "√h", of: "h", op: "sqrt" }];
  const cols1 = rowOf(cols, { ruler: { v: 0.64, e: 0.005 }, tape: { v: 0.542, e: 0.0005 } });
  assert.deepEqual(cols1.h, { v: 0.64, e: 0.005 });
  close(cols1.sqrt_h.v, 0.8, 1e-15, "√h");
  const text = csv(cols, [{ cols: cols1 }], (c) => c.label);
  const [head, line] = text.trim().split("\n");
  assert.equal(head, '"h, m","σ h, m","L, m","σ L, m",√h,σ √h');
  assert.equal(line.split(",").length, 6);
  assert.equal(line.split(",")[2], "0.542");
});

test("a value with its error", () => {
  assert.equal(pm(0.67738, 0.0042), "0.6774 ± 0.0042");
  assert.equal(pm(45.12, 0.5), "45.12 ± 0.50");
  // an exact value (error 0): four significant digits with their zeros, no «± 0» (V52 (y))
  assert.equal(pm(2, 0), "2.000");
  assert.equal(pm(1, 0), "1.000");
  assert.equal(pm(Math.sqrt(0.2), 0), "0.4472");
  assert.equal(sig4(9.99996), "10.00", "rounded before its decimals are chosen");
  assert.equal(sig4(12.3449), "12.34");
  assert.equal(sig4(0), "0.000");
});

test("a reading to the decimals of its division or its error; a unit after a value", () => {
  assert.equal(readingText({ division: 0.01, error: 0.005 }, { v: 0.6, e: 0.005 }), "0.600 ± 0.005", "F14");
  assert.equal(readingText({ division: 0.001, error: 0.0005 }, { v: 0.524, e: 0.0005 }), "0.5240 ± 0.0005");
  assert.equal(readingText({ division: 1, error: 0.5 }, { v: 45, e: 0.5 }), "45.0 ± 0.5");
  // an exact reading: its division's decimals, no «± 0» (V52 (y)); the instrument says why instead of «error ±0»
  assert.equal(readingText({ division: 0.01, error: 0 }, { v: 0.2, e: 0 }), "0.20");
  assert.equal(readingText({ division: 0.01, error: 0 }, { v: 1, e: 0 }), "1.00");
  const stand = instrumentText({ division: 0.01, error: 0, unit: "m", error_note: "the stand sets the chute's height at its marks" });
  assert.equal(stand, "division 0.01\u00a0m; exact: the stand sets the chute's height at its marks");
  assert.ok(!stand.includes("±"));
  assert.equal(instrumentText({ division: 0.01, error: 0, unit: "m" }), "division 0.01\u00a0m; exact");
  assert.equal(instrumentText({ division: 0.001, error: 0.0005, unit: "m" }), "division 0.001\u00a0m, error ±0.0005\u00a0m");
  assert.equal(withUnit("41.9", "°"), "41.9°", "no space before the degree sign (F16)");
  assert.equal(withUnit("0.677", "m"), "0.677\u00a0m");
});

test("one row per set-up: a repeat replaces its row (integrator D5)", () => {
  const row = (h, L) => ({ values: { h_m: h }, cols: { L: { v: L, e: 0.0005 } } });
  let t1 = placeRow([], row(0.6, 0.524));
  assert.deepEqual([t1.n, t1.replaced, t1.rows.length], [1, false, 1]);
  t1 = placeRow(t1.rows, row(0.8, 0.605));
  t1 = placeRow(t1.rows, row(0.6, 0.524));
  assert.deepEqual([t1.n, t1.replaced, t1.rows.length], [1, true, 2], "the repeat replaced row 1");
  assert.equal(setupKey({ b: 1, a: 2 }), setupKey({ a: 2, b: 1 }), "the order of the controls does not matter");
  assert.notEqual(setupKey({ a: true }), setupKey({ a: 1 }));
});

test("the table is kept with its atlas's key: another key's rows are dropped (review EX1-screens F4)", () => {
  const store = new Map(), S = { getItem: (k) => store.get(k) ?? null, setItem: (k, v) => store.set(k, v), removeItem: (k) => store.delete(k) };
  S.setItem("k", JSON.stringify({ key: "aaa", rows: [{ values: {} }] }));
  assert.equal(loadRows(S, "k", "aaa").rows.length, 1);
  assert.deepEqual(loadRows(S, "k", "bbb"), { rows: [], dropped: 1 });
  assert.equal(store.has("k"), false);
  S.setItem("k", JSON.stringify([{ values: {} }, { values: {} }]));  // the format before the key: dropped
  assert.deepEqual(loadRows(S, "k", "aaa"), { rows: [], dropped: 2 });
});

test("«Computed for this bench»: the step's laws with the world's values, by id or <step>/<law> on a shared atlas (EX2 §5 F6 (d), F9)", () => {
  const laws = [{ x: "sqrt_h", y: "L", model: "line0", quantity: "slope", label: "k = L / √h", unit: "m^(1/2)", reference: "k_horizontal" }];
  const refs = { k_horizontal: { value: 0.67737, unit: "m^(1/2)", label: "k = v₀·√(2/g)", how: "closed form" } };
  const out = computedFor({ id: "heights", laws }, refs, (id) => ({ sqrt_h: "√h", L: "L" }[id]));
  assert.equal(out.length, 1);
  assert.equal(out[0].text, "slope of L against √h: 0.67737\u00a0m^(1/2); k = v₀·√(2/g)");
  assert.equal(out[0].how, "closed form");
  assert.equal(computedFor({ id: "heights", laws }, {}).length, 0, "no reference: nothing listed");
  const shared = computedFor({ id: "throws", shared: true, laws }, { "throws/k_horizontal": refs.k_horizontal });
  assert.equal(shared.length, 1, "on an Explore screen's atlas the reference is <step>/<law>");
});

test("the fit's output: parameters with the declared σ, χ², dof, χ²/dof, p, the Birge ratio, the scaled σ on its own line; no verdict (EX2 §5 F6 (c))", () => {
  const x = [0, 1, 2, 3, 4], y = [1.0, 3.1, 4.9, 7.2, 8.8];
  const r = fit(x, y, null, x.map(() => 0.1), "line");
  const L = fitLines(r, "line", false);
  assert.equal(L.length, 3);
  assert.ok(L[0].startsWith("line: a = ") && L[0].includes(`b = ${pm(r.params.b, r.sigmaDeclared.b)}`), L[0]);
  assert.ok(/^χ² = .*, dof = 3, χ²\/dof = .*, p = .*, Birge ratio √\(χ²\/dof\) = /.test(L[1]), L[1]);
  assert.ok(L[2].startsWith("σ scaled by the Birge ratio: ") && L[2].includes(pm(r.params.b, r.sigmaScaled.b)), L[2]);
  assert.equal(fitLines(r, "line", true).length, 1, "at school the parameters with their errors only");
  const ok = fit([1, 2, 3], [2, 4, 6.01], null, [0.1, 0.1, 0.1], "line0");
  assert.equal(fitLines(ok, "line0", false).length, 2, "χ²/dof ≤ 1: no scaled line");
  const none = fit(x, y, null, null, "line");
  assert.equal(fitLines(none, "line", false)[1], "(no declared errors: the σ come from the scatter of the points)");
  assert.ok(!fitLines(r, "line", false).join(" ").match(/✓|✗|agree/), "no verdict");
});

test("the teacher's variant: found by its id, only in a task sheet (EX2 §5 F8 (b))", () => {
  const ws = { variants: [{ id: "a", values: { s1: { h_m: 0.6 } } }] };
  assert.equal(variantOf(ws, "a").values.s1.h_m, 0.6);
  assert.equal(variantOf(ws, "b"), null);
  assert.equal(variantOf({ ...ws, ex1: true }, "a"), null, "EX1's worksheet (the transition) has no such variants");
  assert.equal(variantOf(ws, null), null);
});

test("a trace's short label, a moment with its zone, a readout with its trailing zeros (review EX1-screens F8, EX1-worlds F11, F17)", async () => {
  const { diffText, readoutText, when } = await import("../explore.js");
  const C = [{ param: "h_m", label: "Launch height", unit: "m" }, { param: "v0", label: "Launch speed", unit: "m/s" }, { param: "angle_deg", label: "Launch angle", unit: "°" }];
  assert.equal(diffText(C, { h_m: 10, v0: 10, angle_deg: 0 }, { h_m: 10, v0: 15, angle_deg: 0 }), "Launch speed 10 m/s", "only what differs");
  assert.equal(diffText(C, { h_m: 1, v0: 5, angle_deg: 30 }, { h_m: 1, v0: 5, angle_deg: 45 }), "Launch angle 30°", "no space before °");
  assert.equal(diffText(C, { h_m: 1, v0: 5, angle_deg: 30 }, { h_m: 1, v0: 5, angle_deg: 30 }), "", "the same set-up: no label");
  assert.equal(when("2026-11-17T15:16:08+00:00"), "2026-11-17 15:16:08 UTC");
  assert.equal(when("2026-11-17T15:16:08.123Z"), "2026-11-17 15:16:08 UTC");
  assert.equal(when("2026-11-17T18:16:08+03:00"), "2026-11-17 18:16:08 UTC+03:00");
  assert.equal(readoutText(23.9), "23.90"); assert.equal(readoutText(18.512), "18.51"); assert.equal(readoutText(0.50491), "0.5049");
  assert.equal(readoutText(1.153), "1.153"); assert.equal(readoutText(0), "0.000");
});

// --- EX2 (design lfphys/sources/explore_EX2_2026-11-18_design.md §5 F1, F3–F5, F7) --------------------------------------
test("a counter reads a whole count: √N with error \"poisson\", one count for N = 0, or its exact count (F4)", () => {
  const det = { kind: "counter", division: 1, error: "poisson" };
  assert.deepEqual(reading(det, 838), { v: 838, e: Math.sqrt(838) });
  assert.deepEqual(reading(det, 0), { v: 0, e: 1 }, "a count of 0 has the error of one count");
  assert.deepEqual(reading(det, 3.0000000001), { v: 3, e: Math.sqrt(3) }, "a whole count");
  assert.equal(reading(det, -1), null, "no negative count");
  assert.equal(reading(det, null), null);
  assert.deepEqual(reading({ kind: "counter", division: 1, error: 0 }, 11), { v: 11, e: 0 }, "an exact count");
  assert.deepEqual(reading({ kind: "counter", division: 1, error: 2 }, 11), { v: 11, e: 2 });
  assert.equal(readingText(det, { v: 838, e: Math.sqrt(838) }), "838 ± 29");
  assert.equal(readingText(det, { v: 0, e: 1 }), "0 ± 1");
  assert.equal(readingText({ kind: "counter", error: 0 }, { v: 11, e: 0 }), "11");
  assert.equal(instrumentText(det), "counts; error √N (a count of 0 has the error of one count)");
  assert.equal(instrumentText({ kind: "counter", error: 0 }), "counts; an exact count");
  assert.equal(instrumentText({ kind: "counter", error: 2 }), "counts; error ±2");
});

test("a readout with the run's own error: σ from the measurable it names, the division only the display (F4)", () => {
  const E1 = { kind: "readout", division: 0.0001, error: null, sigma: "E_ab_se", unit: "" };
  assert.deepEqual(reading(E1, 0.70712, 0.0111), { v: 0.7071, e: 0.0111 });
  assert.equal(reading(E1, 0.70712, null), null, "no error yet: nothing to measure");
  assert.equal(readingText(E1, { v: 0.7071, e: 0.0111 }), "0.7071 ± 0.011");
  assert.equal(instrumentText(E1), "division 0.0001; error: the run's own standard error");
});

test("formula columns: the value and the error propagated over the earlier columns; an undefined cell says why (F5)", () => {
  const cols = [{ id: "npp", label: "N++", from: "c_pp" }, { id: "nmm", label: "N--", from: "c_mm" }, { id: "npm", label: "N+-", from: "c_pm" },
    { id: "nmp", label: "N-+", from: "c_mp" }, { id: "E", label: "E", expr: "(npp + nmm - npm - nmp) / (npp + nmm + npm + nmp)" },
    { id: "r", label: "r", expr: "sqrt(E - 1)" }];
  const det = { kind: "counter", division: 1, error: "poisson" };
  const rd = { c_pp: reading(det, 400), c_mm: reading(det, 400), c_pm: reading(det, 100), c_mp: reading(det, 100) };
  const why = {};
  const row = rowOf(cols, rd, why);
  close(row.E.v, 0.6, 1e-15, "E");
  // σ_E² = Σ (∂E/∂N σ_N)² + ½Σ (∂²E/∂N²)² σ_N⁴; ∂E/∂N++ = 2(N+- + N-+)/N², ∂E/∂N+- = −2(N++ + N--)/N², N = 1000
  const N = 1000, d1p = 2 * 200 / N ** 2, d1m = -2 * 800 / N ** 2, d2p = -4 * 200 / N ** 3, d2m = 4 * 800 / N ** 3;
  const want = Math.sqrt(2 * (d1p * 20) ** 2 + 2 * (d1m * 10) ** 2 + 0.5 * (2 * (d2p * 400) ** 2 + 2 * (d2m * 100) ** 2));
  close(row.E.e, want, 1e-12, "σ_E");
  assert.equal(row.r, null, "√ of a negative number: empty");
  assert.deepEqual(why, { r: "sqrt_negative" });
  const text = csv(cols, [{ cols: row }]);
  const line = text.trim().split("\n")[1].split(",");
  assert.deepEqual(line.slice(-2), ["", ""], "an empty cell is empty in the CSV, never «null»");
  const miss = {};
  assert.equal(rowOf(cols, { ...rd, c_pp: null }, miss).E, null);
  assert.equal(miss.E, "missing");
});

test("the screen's time scale and its label (F1): speed, «world», normal or slow, the world's own unit", async () => {
  const { speedOf, factorText, timeLabel, worldTime } = await import("../explore.js");
  assert.equal(speedOf({}, null), 1, "no speed: real time");
  assert.equal(speedOf({ speed: 5e-8 }, { speed: 3 }), 5e-8);
  assert.equal(speedOf({ speed: "world" }, { speed: 0.0083 }), 0.0083, "the point's own default speed");
  assert.equal(speedOf({ speed: "world" }, {}), 1);
  assert.equal(factorText(1.02), "real time");
  assert.equal(factorText(1 / 120), "slow motion ×120");
  assert.equal(factorText(2.5), "sped up ×2.5");
  assert.equal(factorText(5e-8), "slow motion ×2·10⁷");
  assert.equal(worldTime(2e-9, null), "2 ns");
  assert.equal(worldTime(0.0493, { units: { t_show: { unit: "GM/c³", s: 4.93e-5 } } }), "1,000\u00a0GM/c³");
  assert.equal(timeLabel({ tt: 0.5, tEnd: 2, speed: 0.25, rate: 1 }), "world 500 ms · slow motion ×4 · 2.00 s / 8.00 s");
  assert.equal(timeLabel({ tt: 0.5, tEnd: 2, speed: 0.25, rate: 0.25 }), "world 500 ms · slow motion ×16 · 2.00 s / 8.00 s", "slow: a quarter");
});

test("compound controls (F3): a value as the parameters it sets; its name; the passport names the parameters", async () => {
  const { expandValues, valueText, valueUnitText, valuesText, diffText } = await import("../explore.js");
  const D = { param: "delta", id: "delta", label: "Δ", unit: "°", values: [0, 22.5, 45], sets: { a_deg: [0, 0, 0], b_deg: [0, 22.5, 45] } };
  const M = { param: "media", id: "media", label: "Media", values: ["aw", "ag"], labels: ["air → water", "air → glass"], sets: { n0: [1, 1], ns: [1.33, 1.5] } };
  assert.deepEqual(expandValues([D, M], { delta: 22.5, media: "ag", other: 3 }), { a_deg: 0, b_deg: 22.5, n0: 1, ns: 1.5, other: 3 });
  assert.equal(valueText(M, "ag"), "air → glass");
  assert.equal(valueUnitText(D, 22.5), "22.5°");
  const params = [{ id: "a_deg", label: "a", unit: "°" }, { id: "b_deg", label: "b", unit: "°" }, { id: "n0", label: "n₀" }, { id: "ns", label: "n_s" }];
  assert.equal(valuesText([D], { delta: 22.5 }, params), "Δ 22.5° (a 0°, b 22.5°)");
  assert.equal(valuesText([M], { media: "aw" }, params), "Media air → water (n₀ 1, n_s 1.33)");
  assert.equal(diffText([D, M], { delta: 0, media: "ag" }, { delta: 22.5, media: "ag" }), "Δ 0°", "a trace names the control's value");
});

test("readouts with an error and a reference; the CSV of the shown point (F7)", async () => {
  const { measText, pointCsv } = await import("../explore.js");
  const S = { id: "S", label: "S", unit: "", sigma: "S_se", ref: "S_law", ref_label: "law" };
  assert.deepEqual(measText(S, { S: 2.8643, S_se: 0.0402, S_law: 2.8284 }), { value: "2.864 ± 0.040", ref: "(law 2.828)" });
  const adv = { id: "adv", label: "advance", unit: "°", ref: "adv_ref", ref_label: "formula" };
  assert.deepEqual(measText(adv, { adv: 52.15512, adv_ref: 52.1549 }), { value: "52.155°", ref: "(formula 52.155°)" });
  assert.deepEqual(measText({ id: "x", unit: "m" }, { x: 23.9 }), { value: "23.90\u00a0m", ref: null });
  assert.deepEqual(measText({ id: "n", unit: "" }, { n: 6 }), { value: "6", ref: null }, "a count");
  assert.deepEqual(measText({ id: "v", unit: "m/s", sigma: "e" }, { v: 3.1537, e: 0.1235 }), { value: "3.15 ± 0.12\u00a0m/s", ref: null });
  assert.deepEqual(measText(S, { S: null }), { value: null, ref: null }, "not reached");
  assert.equal(measText({ id: "x", ref: "y" }, { x: 1, y: 1 }).ref, "(reference 1.0000)", "the default label");
  const W = { frames: [{ t: 0, meta: { meas: { S: null, S_se: null, S_law: 2.83, n: 0 } } }, { t: 0.1, meta: { meas: { S: 2.9, S_se: 0.1, S_law: 2.83, n: 12 } } },
    { t: 0.2, meta: { meas: { S: 2.85, S_se: 0.07, S_law: 2.83, n: 25 } } }] };
  const ms = [S, { id: "S_se", label: "σS" }, { id: "S_law", label: "S law" }, { id: "n", label: "pairs" }];
  const text = pointCsv(W, 0.1, ms, (m) => m.label);
  assert.equal(text, "t, s,S,σ S,S law,pairs\n0,,,2.83,0\n0.1,2.9,0.1,2.83,12\n".replace("t, s", '"t, s"'));
});
