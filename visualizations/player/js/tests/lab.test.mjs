// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// The lab's readings and table (lab.js; design lfphys/sources/explore_2026-11-14_design.md §2.3): an instrument rounds
// a computed value to its division and carries its declared error; derived columns propagate the error as |f′(x)|·σ_x;
// the CSV carries the errors; a value with its error is written to the error's two significant digits. The cases are
// computed by hand. Run from visualizations/: node --test player/js/tests/*.test.mjs
import { test } from "node:test";
import assert from "node:assert/strict";
import { csv, derived, pm, reading, rowOf } from "../lab.js";

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

test("derived columns and their errors |f′(x)|·σ_x", () => {
  const r = { v: 0.64, e: 0.005 };
  close(derived("sqrt", r).v, 0.8, 1e-15, "√"); close(derived("sqrt", r).e, 0.005 / (2 * 0.8), 1e-15, "σ√");
  close(derived("square", r).v, 0.4096, 1e-15, "x²"); close(derived("square", r).e, 2 * 0.64 * 0.005, 1e-15, "σx²");
  const th = { v: 30, e: 0.5 };
  close(derived("sin2", th).v, Math.sin(Math.PI / 3), 1e-15, "sin 2θ");
  close(derived("sin2", th).e, 2 * Math.cos(Math.PI / 3) * Math.PI / 180 * 0.5, 1e-15, "σ sin 2θ");
  close(derived("inverse", { v: 2, e: 0.1 }).e, 0.1 / 4, 1e-15, "σ 1/x");
  close(derived("log", { v: 2, e: 0.1 }).e, 0.05, 1e-15, "σ ln x");
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
