// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// The atlas in the browser (atlas.js; design lfphys/sources/explore_2026-11-14_design.md §1.3–§1.5, §3.4): flattening
// and its inverse, snapping, the neighbours, the LRU, the header merge, and the toy world's built atlases
// (tests/site_worlds/recordings/s98_atlas_toy, made by tests/site_worlds/make_fixture.py) read through a fetch of the
// files: every computed point decodes (its quantised path too), its merged header carries its grid values, the refused
// point says why, a point is fetched once, and the prefetch asks only for neighbours.
// Run from visualizations/: node --test player/js/tests/*.test.mjs
import { test } from "node:test";
import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { LRU, flatIndex, gridIndex, mergeHeader, neighbours, openAtlas, snap } from "../atlas.js";
import { frameAt, showAt } from "../record_core.js";

const REC = new URL("../../../tests/site_worlds/recordings/", import.meta.url);
const index = JSON.parse(readFileSync(new URL("s98_atlas_toy/index.json", REC), "utf-8"));
const log = [];
// a fetch of the recordings' folder (the server's /recordings/<world>/…)
async function fakeFetch(u) {
  const path = decodeURIComponent(String(u).replace(/^\/recordings\//, ""));
  log.push(path);
  const f = new URL(path, REC);
  if (!existsSync(f)) return new Response("{}", { status: 404, statusText: "Not Found" });
  return new Response(readFileSync(f), { status: 200 });
}
const C = [{ param: "h_m", values: [0, 1], default: 1 }, { param: "angle_deg", values: [0, 30, 60], default: 0 }];

test("flattening is row-major with the last control fastest; off-grid values are refused", () => {
  assert.equal(flatIndex(C, { h_m: 0, angle_deg: 0 }), 0);
  assert.equal(flatIndex(C, { h_m: 0, angle_deg: 60 }), 2);
  assert.equal(flatIndex(C, { h_m: 1, angle_deg: 30 }), 4);
  assert.equal(flatIndex(C, {}), 3, "defaults");
  assert.throws(() => flatIndex(C, { h_m: 0.5 }));
  assert.equal(gridIndex({ values: [false, true] }, true), 1);
  assert.equal(gridIndex({ values: [0, 1] }, true), -1, "true is not 1");
});

test("snapping to the nearest grid value; neighbours ±1 along each control", () => {
  assert.equal(snap(C[1], 44), 30);
  assert.equal(snap(C[1], 46), 60);
  assert.equal(snap(C[1], -5), 0);
  assert.deepEqual(neighbours(C, { h_m: 0, angle_deg: 30 }), [{ h_m: 1, angle_deg: 30 }, { h_m: 0, angle_deg: 0 }, { h_m: 0, angle_deg: 60 }]);
});

test("the LRU keeps at most n points and m bytes, the newest always", () => {
  const L = new LRU(2, 100);
  L.set("a", 1, 10); L.set("b", 2, 10); L.get("a"); L.set("c", 3, 10);
  assert.deepEqual([...L.map.keys()], ["a", "c"], "b was the least recently used");
  L.set("d", 4, 200);
  assert.deepEqual([...L.map.keys()], ["d"], "over the byte budget: only the newest");
});

test("the header merge: {...base, ...delta}, $drop and $drop_blobs, a full header as it is", () => {
  const base = [{ type: "header", a: 1, b: { x: 1 }, c: 3, blobs: [] }, { u: 1, v: 2 }];
  const [m, b] = mergeHeader(base, [{ type: "header", $delta: true, b: { y: 2 }, $drop: ["c"], $drop_blobs: ["v"] }, { w: 3 }]);
  assert.deepEqual(m, { type: "header", a: 1, b: { y: 2 } });
  assert.deepEqual(b, { u: 1, w: 3 });
  const full = [{ type: "header", z: 1 }, {}];
  assert.equal(mergeHeader(base, full)[0], full[0]);
});

test("the toy world's atlases: every point decodes, its header carries its values, the refusal says why", async () => {
  assert.ok(index.atlases.length >= 2);
  for (const entry of index.atlases) {
    const A = await openAtlas("s98_atlas_toy", entry, { fetchImpl: fakeFetch });
    assert.equal(A.manifest.points.length, A.controls.reduce((n, c) => n * c.values.length, 1));
    for (let i = 0; i < A.manifest.points.length; i++) {
      const values = A.valuesOf(i);
      assert.equal(A.index(values), i);
      const p = await A.point(values);
      if (A.manifest.points[i][2] !== 0) {
        assert.equal(p.state, "refused");
        assert.ok(p.refusal && p.refusal.$t, "the refusal is a text");
        continue;
      }
      assert.equal(p.state, "computed");
      const h = p.W.header;
      for (const [k, v] of Object.entries({ ...A.manifest.fixed, ...values })) assert.equal(h.params[k], v, `${entry.id} p${i} ${k}`);
      assert.ok(!("$delta" in h), "no $-keys in a merged header");
      assert.ok(h.measurables && h.measurables.length, "the base's keys are there");
      assert.ok(p.W.frames.length > 5 && p.tEnd > 0);
      assert.ok(p.W.events.some((e) => e.kind === "landing"), "the landing event");
      assert.ok(p.W.checks.size >= 2, "the checks");
      const traj = p.W.viewMsgs.filter((m) => m.meta.type === "traj");
      assert.ok(traj.length && traj.every((m) => m.blobs.s instanceof Float32Array), "the quantised path decodes to floats");
      assert.ok(!p.W.viewMsgs.some((m) => m.meta.type === "story") || entry.id !== "explore", "the dropped type is absent");
      // the last frame's landing range against the landing event's (both computed by the run; the path is quantised,
      // the event is full precision)
      const last = frameAt(p.W, p.tEnd);
      assert.equal(last.meta.meas.range, p.W.events.find((e) => e.kind === "landing").data.L);
    }
  }
});

test("a point is fetched once; the prefetch asks only for its neighbours, two at a time", async () => {
  const entry = index.atlases.find((a) => a.id === "explore");
  const A = await openAtlas("s98_atlas_toy", entry, { fetchImpl: fakeFetch });
  await A.point({ h_m: 1, angle_deg: 0 });
  await A.point({ h_m: 1, angle_deg: 0 });
  assert.equal(A.requested.length, 1);
  A.prefetch({ h_m: 1, angle_deg: 0 });
  assert.ok(A.active <= 2);
  await new Promise((r) => setTimeout(r, 200));
  // the neighbours of (1 m, 0°): (0 m, 0°) is refused (no file), (1 m, 30°) is p4
  const want = new Set([A.manifest.points[4][0]]);
  assert.deepEqual(new Set(A.requested.slice(1)), want);
});

test("a view fed a point up to a time holds only what the run had emitted by then", async () => {
  const entry = index.atlases.find((a) => a.id === "explore");
  const A = await openAtlas("s98_atlas_toy", entry, { fetchImpl: fakeFetch });
  const p = await A.point({ h_m: 1, angle_deg: 30 });
  const seen = [];
  const view = { reset() { seen.length = 0; }, onHeader() {}, onMessage(m) { seen.push(m.t ?? 0); } };
  showAt(view, p.W, 0.2);
  assert.ok(seen.length && seen.every((x) => x <= 0.2 + 1e-12));
  const n02 = seen.length;
  showAt(view, p.W, p.tEnd);
  assert.ok(seen.length > n02);
  showAt(view, p.W, 0.2);  // back: rebuilt from the record
  assert.equal(seen.length, n02);
});

test("(server) a live point: its bytes decoded and labelled; a refusal is a refused point with the world's text", async () => {
  const entry = index.atlases.find((a) => a.id === "explore");
  const p4 = JSON.parse(readFileSync(new URL(`s98_atlas_toy/${entry.file}`, REC), "utf-8")).points[4][0];
  const bytes = readFileSync(new URL(`s98_atlas_toy/atlas/explore/${p4}`, REC));
  const posts = [];
  const fx = async (u, init) => {
    if (init && init.method === "POST") {
      posts.push([String(u), JSON.parse(init.body)]);
      const body = JSON.parse(init.body);
      if (body.values.h_m === 0) return new Response(JSON.stringify({ error: { $t: "no flight" }, hint: { $t: "raise it" } }), { status: 400 });
      return new Response(bytes, { status: 200, headers: { "X-LF-Source": "computed", "X-LF-Key": "k" } });
    }
    return fakeFetch(u);
  };
  const A = await openAtlas("s98_atlas_toy", entry, { fetchImpl: fx });
  const p = await A.live({ h_m: 1, angle_deg: 45 });
  assert.equal(p.state, "computed"); assert.equal(p.live, true); assert.equal(p.source, "computed");
  assert.ok(p.W.frames.length > 5);
  assert.equal(posts[0][0], "/api/atlas/s98_atlas_toy/explore/point");
  assert.deepEqual(posts[0][1], { values: { h_m: 1, angle_deg: 45 } });
  await A.live({ h_m: 1, angle_deg: 45 });
  assert.equal(posts.length, 1, "cached");
  const r = await A.live({ h_m: 0, angle_deg: 10 });
  assert.equal(r.state, "refused");
  assert.deepEqual(r.refusal, { $t: "{text}. What to change: {hint}", a: { text: { $t: "no flight" }, hint: { $t: "raise it" } } });
});
