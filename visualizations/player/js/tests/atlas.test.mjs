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
import { readStream } from "../api.js";

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
      // a compound control's value is the parameters it sets (EX2 §5 F3: the manifest records its sets)
      const params = { ...values };
      for (const c of A.controls.filter((x) => x.sets)) {
        const k = c.values.indexOf(params[c.param]);
        delete params[c.param];
        for (const [q, list] of Object.entries(c.sets)) params[q] = list[k];
      }
      for (const [k, v] of Object.entries({ ...A.manifest.fixed, ...params })) assert.equal(h.params[k], v, `${entry.id} p${i} ${k}`);
      assert.ok(!("$delta" in h), "no $-keys in a merged header");
      assert.ok(h.measurables && h.measurables.length, "the base's keys are there");
      assert.ok(p.W.frames.length > 5 && p.tEnd > 0);
      const landed = p.W.events.some((e) => e.kind === "landing");
      // a stop by counted events may end a point before its landing (EX2 §5 F2: «Throws» stops at six ticks)
      const early = A.manifest.stop.events && !landed && p.W.events.filter((e) => e.kind === "tick").length >= A.manifest.stop.events.tick;
      assert.ok(landed || early, "the landing event, or the counted stop before it");
      if (early) { assert.equal(p.speed, 1, "the world's default speed from the point's state message (EX2 §5 F1)"); continue; }
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

// EX2 §5 F10, §7: a point whose blobs are in the atlas's pool, decoded with the pool, equals the same point packed
// without it (tests/site_worlds/quant/pool_point.lfpt.gz: make_fixture.py writes it with headless.unpool, and
// tests/test_atlas.py checks it against the committed fixture); without the pool it cannot be read
test("a pooled point decoded with the atlas's pool equals the same point packed without it", async () => {
  const Q = new URL("../../../tests/site_worlds/quant/", import.meta.url);
  const pc = JSON.parse(readFileSync(new URL("pool_point.json", Q), "utf-8"));
  const entry = index.atlases.find((a) => a.id === pc.atlas);
  log.length = 0;
  const A = await openAtlas("s98_atlas_toy", entry, { fetchImpl: fakeFetch });
  assert.ok(A.pool && A.pool.size >= 1, "the pool is read with the manifest");
  assert.equal(log.filter((x) => x.endsWith(A.manifest.pool.file)).length, 1, "fetched once");
  const pooled = new Uint8Array(readFileSync(new URL(`s98_atlas_toy/atlas/${pc.atlas}/${A.manifest.points[pc.point][0]}`, REC)));
  const a = await readStream(pooled, A.pool);
  const b = await readStream(new Uint8Array(readFileSync(new URL("pool_point.lfpt.gz", Q))));
  await assert.rejects(readStream(pooled), /pool/, "without the pool a pooled point cannot be read");
  assert.equal(a.length, b.length);
  const desc = (d) => JSON.stringify({ name: d.name, dtype: d.dtype, shape: d.shape, nbytes: d.nbytes, q: d.q ?? null });
  let resolved = 0;
  for (let k = 0; k < a.length; k++) {
    const { blobs: ma, ...ra } = a[k].meta, { blobs: mb, ...rb } = b[k].meta;
    assert.deepEqual(ra, rb, `message ${k}: the same meta`);
    assert.deepEqual((ma || []).map(desc), (mb || []).map(desc), `message ${k}: the same blobs`);
    resolved += (ma || []).filter((d) => d.pool).length;
    assert.ok(!(mb || []).some((d) => d.pool), "the unpooled point names no pool");
    for (const name of Object.keys(b[k].blobs)) {
      assert.equal(a[k].blobs[name].constructor, b[k].blobs[name].constructor, name);
      assert.deepEqual(Array.from(a[k].blobs[name]), Array.from(b[k].blobs[name]), `message ${k} blob ${name}`);
    }
  }
  assert.ok(resolved >= 1, "the point has a pooled blob");
  // through the atlas: the point's merged header carries the pooled blob, decoded
  const p = await A.point(A.valuesOf(pc.point));
  assert.equal(p.state, "computed");
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

// integrator D13: a packed header names its base file ("$base", the base's sha256): merged only against that base; a
// live point packed against another base is asked again with "full_header": true; the point carries its own passport
// (X-LF-Source, X-LF-Key, X-LF-Code, X-LF-Made); any other error than a refusal says the server's text in the viewer's
// language (review EX1-screens F7: t(error), not the English "text")
test("(server) a live point's own passport; another base asks for the full header; a 429 in the viewer's language", async () => {
  const entry = index.atlases.find((a) => a.id === "explore");
  const mf = JSON.parse(readFileSync(new URL(`s98_atlas_toy/${entry.file}`, REC), "utf-8"));
  const bytes = readFileSync(new URL(`s98_atlas_toy/atlas/explore/${mf.points[4][0]}`, REC));
  const posts = [];
  let busy = false;
  const fx = async (u, init) => {
    if (init && init.method === "POST") {
      const body = JSON.parse(init.body);
      posts.push(body);
      if (busy) return new Response(JSON.stringify({ error: { $t: "the server computes other points now; try again in a moment" }, text: "ENGLISH ONLY" }), { status: 429, statusText: "Too Many Requests" });
      return new Response(bytes, { status: 200, headers: { "X-LF-Source": "cache", "X-LF-Key": "abc", "X-LF-Code": "c0de", "X-LF-Made": "2026-11-17T15:16:08+00:00" } });
    }
    return fakeFetch(u);
  };
  const A = await openAtlas("s98_atlas_toy", entry, { fetchImpl: fx });
  assert.equal(A.baseMatches({ $delta: true }), true, "no $base: an older packing, merged as before");
  assert.equal(A.baseMatches({ $delta: true, $base: mf.base.sha256 }), true);
  assert.equal(A.baseMatches({ $delta: true, $base: "f".repeat(64) }), mf.base.sha256 ? false : true);
  assert.equal(A.baseMatches({ type: "header" }), true, "a full header");
  const [m] = mergeHeader(A.base, [{ type: "header", $delta: true, $base: "x", q: 1 }, {}]);
  assert.ok(!("$base" in m) && m.q === 1, "$base dropped like $delta");
  // the first reply packed against another base: asked again with the full header
  const orig = A.baseMatches.bind(A);
  A.baseMatches = (meta) => (posts.length > 1 ? orig(meta) : false);
  const p = await A.live({ h_m: 1, angle_deg: 40 });
  assert.equal(posts.length, 2);
  assert.deepEqual(posts[1], { values: { h_m: 1, angle_deg: 40 }, full_header: true });
  assert.deepEqual([p.source, p.key, p.code, p.made], ["cache", "abc", "c0de", "2026-11-17T15:16:08+00:00"]);
  A.baseMatches = orig;
  busy = true;
  await assert.rejects(A.live({ h_m: 1, angle_deg: 41 }), (e) => e.status === 429 && e.message === "the server computes other points now; try again in a moment");
});

// review EX1-worlds F1: the feed state belongs to the view. A re-launched shot and its trace share one decoded point;
// two views of it at different times each hold exactly the messages up to their own time, however their feeding
// interleaves (before: the shared marks on W made each view rebuild the other's record every frame, a fan of lines)
test("two views of one world at different times: each fed its own messages, no rebuild by the other", async () => {
  const entry = index.atlases.find((a) => a.id === "explore");
  const A = await openAtlas("s98_atlas_toy", entry, { fetchImpl: fakeFetch });
  const p = await A.point({ h_m: 1, angle_deg: 30 });
  const mk = () => { const v = { seen: [], resets: 0, reset() { v.seen.length = 0; v.resets++; }, onHeader() {}, onMessage(m) { v.seen.push(m.t ?? 0); } }; return v; };
  const trace = mk(), shot = mk();
  const T = p.tEnd, n = (tt) => p.W.viewMsgs.filter((m) => (m.meta.t ?? 0) <= tt + 1e-12).length;
  for (let k = 0; k <= 20; k++) {  // the trace at its end, the new shot flying: fed in turns every frame
    showAt(trace, p.W, T);
    showAt(shot, p.W, (T * k) / 20);
    assert.equal(trace.seen.length, n(T), `the trace holds the whole flight (k ${k})`);
    assert.equal(shot.seen.length, n((T * k) / 20), `the shot holds its flight so far (k ${k})`);
  }
  assert.equal(trace.resets, 1, "the trace was built once");
  assert.equal(shot.resets, 1, "the shot was built once and fed on");
  assert.deepEqual([...shot.seen].sort(), [...trace.seen].sort(), "at the end both hold the same messages");
});
