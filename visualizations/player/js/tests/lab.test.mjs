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
import { csv, derived, lawOf, loadRows, placeRow, pm, reading, readingText, rowOf, setupKey, withUnit } from "../lab.js";

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
  assert.equal(pm(2, 0), "2");
});

test("a reading to the decimals of its division or its error; a unit after a value", () => {
  assert.equal(readingText({ division: 0.01, error: 0.005 }, { v: 0.6, e: 0.005 }), "0.600 ± 0.005", "F14");
  assert.equal(readingText({ division: 0.001, error: 0.0005 }, { v: 0.524, e: 0.0005 }), "0.5240 ± 0.0005");
  assert.equal(readingText({ division: 1, error: 0.5 }, { v: 45, e: 0.5 }), "45.0 ± 0.5");
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

test("the law of a plot: only the step's laws' own (x, y, model) (integrator D4)", () => {
  const laws = [{ x: "sin2", y: "L", model: "line0", reference: "v2_over_g" }, { x: "theta", y: "L", model: "quadratic", reference: "max45" }];
  assert.equal(lawOf(laws, "sin2", "L", "line0").reference, "v2_over_g");
  assert.equal(lawOf(laws, "theta", "L", "quadratic").reference, "max45");
  assert.equal(lawOf(laws, "theta", "L", "line0"), null, "the right axes with another fit");
  assert.equal(lawOf(laws, "h", "L", "line0"), null, "other axes");
  assert.equal(lawOf([], "sin2", "L", "line0"), null);
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
