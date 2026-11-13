// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// A saved recording (gzip -9 of an LFVREC1 stream: DESIGN of the start page §4.1, §4.4) played through openRecording gives
// the player the same messages as Python's lfviz.protocol decodes from it, wrapped in history_start and history_end
// {live: false, resumable: false}; every message has its own 8-aligned ArrayBuffer. The fixture is a tiny run of the
// test world p97_osc, written by tests/make_record_fixture.py. Run from visualizations/ with Node 22 or newer:
//   node --test player/js/tests/*.test.mjs
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { gzipSync } from "node:zlib";
import { openRecording } from "../api.js";

const gz = readFileSync(new URL("./fixtures/p97_osc.lfrec.gz", import.meta.url));
const expected = JSON.parse(readFileSync(new URL("./fixtures/p97_osc.expected.json", import.meta.url), "utf-8"));

async function play(src, opts) {
  const got = [];
  let opened = 0, error = null;
  const c = openRecording(src, { onOpen: () => { opened++; }, onMessage: (m) => got.push(m), onError: (e) => { error = e; } }, opts);
  await c.done;
  return { got, opened, error };
}

const same = (m, e, i) => {
  assert.deepEqual(m.meta, e.meta, `message ${i}: meta`);
  assert.deepEqual(Object.keys(m.blobs).sort(), Object.keys(e.blobs).sort(), `message ${i}: blobs`);
  for (const [k, b] of Object.entries(e.blobs)) {
    const a = m.blobs[k];
    assert.equal(a.byteOffset % 8, 0, `message ${i} ${k}: 8-aligned`);
    assert.equal(a.length, b.shape.reduce((x, y) => x * y, 1), `message ${i} ${k}: length`);
    assert.deepEqual(Array.from(a, (x) => (Number.isNaN(x) ? null : x)), b.values, `message ${i} ${k}: values`);
  }
};

test("a gzip recording decodes to the Python codec's messages, wrapped as an ended record", async () => {
  const { got, opened, error } = await play(gz, { frameStride: 3 });
  assert.equal(error, null);
  assert.equal(opened, 1);
  assert.equal(got.length, expected.length + 2);
  assert.deepEqual(got[0].meta, { type: "history_start", frame_stride: 3, recording: true });
  assert.deepEqual(got[got.length - 1].meta, { type: "history_end", live: false, resumable: false, recording: true });
  got.slice(1, -1).forEach((m, i) => same(m, expected[i], i));
  assert.ok(expected.filter((e) => e.meta.type === "frame").length >= 20, "the fixture has frames");
  assert.ok(expected.some((e) => Object.keys(e.blobs).length), "the fixture has arrays");
  const bufs = new Set(got.slice(1, -1).flatMap((m) => Object.values(m.blobs).map((a) => a.buffer)));
  assert.equal(bufs.size, got.slice(1, -1).filter((m) => Object.keys(m.blobs).length).length, "one ArrayBuffer per message");
});

test("an inflated recording (a server that sent Content-Encoding: gzip) plays the same", async () => {
  const { gunzipSync } = await import("node:zlib");
  const { got, error } = await play(new Uint8Array(gunzipSync(gz)));
  assert.equal(error, null);
  assert.equal(got.length, expected.length + 2);
  assert.equal(got[0].meta.frame_stride, 1);
  got.slice(1, -1).forEach((m, i) => same(m, expected[i], i));
});

test("a file that is not a recording is refused", async () => {
  const { got, error } = await play(gzipSync(Buffer.from("not a recording at all")));
  assert.ok(error instanceof Error);
  assert.equal(got.length, 0);
});

test("a cut recording plays what is whole", async () => {
  const { gunzipSync } = await import("node:zlib");
  const raw = gunzipSync(gz);
  const { got, error } = await play(new Uint8Array(raw.subarray(0, raw.length - 10)));
  assert.equal(error, null);
  assert.equal(got.length, expected.length + 1);  // the last message is cut off
  assert.equal(got[got.length - 1].meta.type, "history_end");
});

test("from a URL: fetch, the progress from Content-Length", async () => {
  const saved = globalThis.fetch;
  globalThis.fetch = async () => new Response(gz, { headers: { "Content-Length": String(gz.length) } });
  try {
    const prog = [];
    const got = [];
    const c = openRecording("recordings/p97_osc/x.lfrec.gz", { onMessage: (m) => got.push(m), onProgress: (a, b) => prog.push([a, b]) });
    await c.done;
    assert.equal(got.length, expected.length + 2);
    assert.ok(prog.length >= 1 && prog[prog.length - 1][0] === gz.length && prog[prog.length - 1][1] === gz.length, JSON.stringify(prog));
  } finally { globalThis.fetch = saved; }
});
