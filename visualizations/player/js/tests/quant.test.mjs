// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// Quantised blobs (server/lfviz/protocol.py "Quantised blobs"; design lfphys/sources/explore_2026-11-14_design.md §1.3):
// api.js decode gives bit for bit the float32 values Python's protocol.dequantize gives, on the shared fixture
// tests/site_worlds/quant/cases.lfrec (every encoding: u8 and u16, lin and sqrt, one range and per-column ranges, NaN
// codes, a quantised blob next to a float one) with its expected bit patterns in cases.json (tests/site_worlds/
// make_fixture.py). Run from visualizations/: node --test player/js/tests/*.test.mjs
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dequantize, readStream } from "../api.js";

const dir = new URL("../../../tests/site_worlds/quant/", import.meta.url);
const bytes = readFileSync(new URL("cases.lfrec", dir));
const expected = JSON.parse(readFileSync(new URL("cases.json", dir), "utf-8"));
const hex = (f32) => Array.from(new Uint32Array(f32.buffer, f32.byteOffset, f32.length), (x) => x.toString(16).padStart(8, "0"));

test("every quantised case of the shared fixture decodes bit for bit as protocol.dequantize", async () => {
  const msgs = await readStream(bytes);
  assert.equal(msgs.length, expected.length);
  let quantised = 0;
  msgs.forEach((m, i) => {
    const e = expected[i];
    assert.equal(m.meta.case, e.case);
    for (const [name, b] of Object.entries(e.blobs)) {
      const a = m.blobs[name];
      const n = b.shape.reduce((x, y) => x * y, 1);
      assert.equal(a.length, n, `${e.case} ${name}: length`);
      if (b.dtype === "float32") {
        assert.ok(a instanceof Float32Array, `${e.case} ${name}: a Float32Array`);
        assert.deepEqual(hex(a), b.bits, `${e.case} ${name}: bits`);
        if ((m.meta.blobs || []).find((d) => d.name === name).q) quantised++;
      } else assert.deepEqual(Array.from(a), b.values, `${e.case} ${name}: values`);
    }
  });
  assert.ok(quantised >= 8, "the fixture's quantised blobs were all read");
  const encs = new Set(msgs.flatMap((m) => (m.meta.blobs || []).filter((d) => d.q).map((d) => `${d.dtype} ${d.q.enc}${Array.isArray(d.q.hi) ? " col" : ""}${d.q.nan ? " nan" : ""}`)));
  for (const k of ["u1 lin", "u2 lin", "u1 sqrt", "u2 sqrt", "u2 lin col", "u2 lin nan"]) assert.ok([...encs].some((x) => x.startsWith(k)), `the fixture covers ${k}: ${[...encs]}`);
});

test("dequantize: the formulas by hand (lin per column, sqrt, NaN code)", () => {
  const lin = dequantize(new Uint16Array([0, 65535, 32768, 65535]), "u2", { enc: "lin", lo: [-1, 10], hi: [1, 20] }, [2, 2]);
  assert.deepEqual(Array.from(lin), [-1, 20, Math.fround(-1 + (32768 / 65535) * 2), 20]);
  const sq = dequantize(new Uint8Array([0, 255, 128]), "u1", { enc: "sqrt", lo: 0, hi: 4 }, [3]);
  assert.deepEqual(Array.from(sq), [0, 4, Math.fround(4 * ((128 / 255) * (128 / 255)))]);
  const nan = dequantize(new Uint8Array([255, 254, 0]), "u1", { enc: "lin", lo: 0, hi: 1, nan: true }, [3]);
  assert.ok(Number.isNaN(nan[0]));
  assert.equal(nan[1], 1);
  assert.equal(nan[2], 0);
  assert.throws(() => dequantize(new Float32Array(2), "f4", { enc: "lin", lo: 0, hi: 1 }, [2]));
});
