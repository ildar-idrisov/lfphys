// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// An atlas in the browser (design lfphys/sources/explore_2026-11-14_design.md §1.3–§1.5, §3.4, §3.7, §3.8): the computed
// points of an Explore screen or of a lab step on the grid of its controls, each a short recording of the world's own
// run, loaded on demand from the files site/atlas.py wrote (the manifest site/atlas.py documents), decoded (quantised
// blobs too: api.js), its header rebuilt from the screen's base header, and ingested into a world's record
// (record_core.js) that the world's own view draws. Nothing between grid points is computed or interpolated here: a
// value off the grid is either refused (the site) or computed by the server (POST /api/atlas/<world>/<atlas>/point).
//
//   openAtlas(world, entry, {base}) the manifest, the base header and the pool (the blobs the points share, EX2 §5 F10)
//                                  of an index entry ({id, file, …} of index.json's
//                                  "atlases"), its files relative to `base` (by default this server's or this site's
//                                  recordings/<world>/; the public site's on a server without a current local atlas,
//                                  integrator D11): an Atlas
//   atlas.point(values)            Promise of a point {i, values, state "computed" | "refused", refusal, W, live, speed,
//                                  …} (speed: the world's default speed, from the point's first state message):
//                                  from the LRU, else fetched (one request per point; at most two prefetches at a time)
//   atlas.prefetch(values)         its neighbours (±1 along every control), at low priority
//   atlas.live(values, seed)       (server) the point computed by the server for any values: the same bytes a site build
//                                  makes; a refusal comes back as a refused point with the world's text. The point
//                                  carries its own passport (integrator D13): source (X-LF-Source: atlas | cache |
//                                  computed), key (X-LF-Key), code (X-LF-Code) and made (X-LF-Made, with its zone)
//
// A packed point's header is a delta against the atlas's base file, named by "$base" (the sha256 of that file): it is
// merged only when "$base" is this manifest's base.sha256; a live point that does not match is asked again with
// "full_header": true (a full header, no delta); an atlas point that does not match is an error (integrator D13).
//   flatIndex, gridIndex, snap, neighbours, mergeHeader, LRU: the parts (atlas.test.mjs)
import { MODE, apiError, readPool, readStream, url } from "./api.js";
import { worldsOf } from "./record_core.js";

export const LRU_POINTS = 24, LRU_BYTES = 40e6, PREFETCH_AT_ONCE = 2;

// --- the grid ---------------------------------------------------------------------------------------------------------
// the index of a value among a control's values: the same type first (true is not 1), then equal; -1 when off the grid
export function gridIndex(control, v) {
  const vals = control.values;
  let k = vals.findIndex((x) => typeof x === typeof v && x === v);
  if (k < 0) k = vals.findIndex((x) => x === v || (typeof x === "number" && typeof v === "number" && Math.abs(x - v) <= 1e-12 * Math.max(1, Math.abs(x))));
  return k;
}
// the flattened index of a grid point: row-major over the controls in their order, the last control fastest (site/atlas.py
// flat_index); a control without a value takes its default; throws when a value is off the grid
export function flatIndex(controls, values) {
  let i = 0;
  for (const c of controls) {
    const v = c.param in values ? values[c.param] : c.default;
    const k = gridIndex(c, v);
    if (k < 0) throw new Error(`${c.param} = ${v} is not on the grid`);
    i = i * c.values.length + k;
  }
  return i;
}
// the grid value nearest to v (numbers); any other value as it is when on the grid, else the default
export function snap(control, v) {
  const vals = control.values;
  if (typeof v === "number" && vals.every((x) => typeof x === "number")) {
    let best = vals[0];
    for (const x of vals) if (Math.abs(x - v) < Math.abs(best - v)) best = x;
    return best;
  }
  return gridIndex(control, v) >= 0 ? vals[gridIndex(control, v)] : control.default;
}
export const defaults = (controls) => Object.fromEntries(controls.map((c) => [c.param, c.default ?? c.values[0]]));
export const onGrid = (controls, values) => controls.every((c) => gridIndex(c, c.param in values ? values[c.param] : c.default) >= 0);
// the grid points one step away along each control (the prefetch)
export function neighbours(controls, values) {
  const out = [];
  for (const c of controls) {
    const k = gridIndex(c, values[c.param]);
    if (k < 0) continue;
    for (const d of [-1, 1]) if (k + d >= 0 && k + d < c.values.length) out.push({ ...values, [c.param]: c.values[k + d] });
  }
  return out;
}

// A point's full header from the base header and its delta (lfviz.headless.merge_header): {...base, ...delta} without the
// $-keys and the keys in $drop; the blobs: the base's without $drop_blobs, then the delta's. A header without "$delta"
// is a full header.
export function mergeHeader(base, delta) {
  const [bm, bb] = base, [dm, db] = delta;
  if (!dm.$delta) { if (!("$base" in dm)) return [dm, db]; const m = { ...dm }; delete m.$base; return [m, db]; }
  const meta = {};
  for (const [k, v] of Object.entries(bm)) if (k !== "blobs") meta[k] = v;
  for (const [k, v] of Object.entries(dm)) if (k !== "blobs") meta[k] = v;
  for (const k of [...(dm.$drop || []), "$delta", "$drop", "$drop_blobs", "$base"]) delete meta[k];
  const dropB = new Set(dm.$drop_blobs || []);
  const blobs = {};
  for (const [k, v] of Object.entries(bb || {})) if (!dropB.has(k)) blobs[k] = v;
  Object.assign(blobs, db || {});
  return [meta, blobs];
}

// --- a least-recently-used cache of decoded points: at most n points and m bytes (the arrays' bytes) -------------------
export class LRU {
  constructor(maxItems = LRU_POINTS, maxBytes = LRU_BYTES) { this.maxItems = maxItems; this.maxBytes = maxBytes; this.map = new Map(); this.bytes = 0; }
  get(k) { const e = this.map.get(k); if (!e) return undefined; this.map.delete(k); this.map.set(k, e); return e.v; }
  has(k) { return this.map.has(k); }
  set(k, v, size = 0) {
    if (this.map.has(k)) { this.bytes -= this.map.get(k).size; this.map.delete(k); }
    this.map.set(k, { v, size }); this.bytes += size;
    for (const [key, e] of this.map) {
      if (this.map.size <= this.maxItems && this.bytes <= this.maxBytes) break;
      if (key === k) continue;  // the newest stays
      this.map.delete(key); this.bytes -= e.size;
    }
  }
  get size() { return this.map.size; }
}

function sizeOf(msgs) {
  let n = 0;
  for (const m of msgs) { n += 256; for (const b of Object.values(m.blobs || {})) n += b.byteLength || 0; }
  return n;
}

// --- an atlas -----------------------------------------------------------------------------------------------------------
// entry: the world's index.json "atlases" item; its file relative to the world's folder of the recordings
export async function openAtlas(world, entry, { fetchImpl = (...a) => fetch(...a), base = null } = {}) {
  const mfUrl = (base || url(`recordings/${world}/`)) + entry.file;
  const dir = mfUrl.slice(0, mfUrl.lastIndexOf("/") + 1);
  const r = await fetchImpl(mfUrl);
  if (!r.ok) throw Object.assign(new Error(`${r.status} ${r.statusText}`), { status: r.status });
  const manifest = await r.json();
  const rb = await fetchImpl(dir + manifest.base.file);
  if (!rb.ok) throw Object.assign(new Error(`${rb.status} ${rb.statusText}`), { status: rb.status });
  const bmsgs = await readStream(new Uint8Array(await rb.arrayBuffer()));
  const bh = bmsgs.find((m) => m.meta.type === "header");
  if (!bh) throw new Error("the atlas's base has no header");
  let pool = null;  // the blobs the points share, fetched once per atlas (EX2 §5 F10)
  if (manifest.pool) {
    const rp = await fetchImpl(dir + manifest.pool.file);
    if (!rp.ok) throw Object.assign(new Error(`${rp.status} ${rp.statusText}`), { status: rp.status });
    pool = await readPool(new Uint8Array(await rp.arrayBuffer()));
  }
  const A = new Atlas(world, entry, manifest, dir, [bh.meta, bh.blobs], fetchImpl);
  A.pool = pool;
  return A;
}

export class Atlas {
  constructor(world, entry, manifest, dir, base, fetchImpl = (...a) => fetch(...a)) {
    Object.assign(this, { world, entry, manifest, dir, base, fetchImpl });  // a function, not window.fetch as a method
    this.id = manifest.atlas || entry.id;
    this.controls = manifest.controls;
    this.cache = new LRU();
    this.pending = new Map();  // key → Promise of a point being loaded
    this.queue = [];           // prefetches waiting: [values]
    this.active = 0;           // prefetches loading now
    this.requested = [];       // the point files asked for, in order (the tests' network log)
  }
  get defaults() { return defaults(this.controls); }
  index(values) { return flatIndex(this.controls, values); }
  // the grid values of a point's index (inverse of flatIndex)
  valuesOf(i) {
    const out = {};
    for (let j = this.controls.length - 1; j >= 0; j--) {
      const c = this.controls[j], n = c.values.length;
      out[c.param] = c.values[i % n]; i = Math.floor(i / n);
    }
    return out;
  }
  // a point's entry without loading it: {i, values, state, refusal, file, bytes_gz}
  info(values) {
    const i = this.index(values), [file, bytes, state] = this.manifest.points[i];
    const refusal = state >= 1 ? (this.manifest.refusals || [])[state - 1] : null;
    return { i, values: this.valuesOf(i), file, bytes_gz: bytes, state: state === 0 ? "computed" : "refused", refusal };
  }
  point(values, { prefetch = false } = {}) {
    const inf = this.info(values);
    if (inf.state === "refused" || !inf.file) return Promise.resolve({ ...inf, W: null, live: false });
    const key = "p" + inf.i;
    const hit = this.cache.get(key);
    if (hit) return Promise.resolve(hit);
    if (this.pending.has(key)) return this.pending.get(key);
    const p = (async () => {
      this.requested.push(inf.file);
      const r = await this.fetchImpl(this.dir + inf.file, prefetch ? { priority: "low" } : {});
      if (!r.ok) throw Object.assign(new Error(`${r.status} ${r.statusText}`), { status: r.status });
      const pt = await this.build(inf, new Uint8Array(await r.arrayBuffer()), { live: false, source: "atlas" });
      this.cache.set(key, pt, pt.size);
      return pt;
    })().finally(() => this.pending.delete(key));
    this.pending.set(key, p);
    return p;
  }
  // does a packed header belong to this atlas's base file? (a full header, or a delta without "$base" as written
  // before ATLAS_VERSION 2, always does)
  baseMatches(meta) {
    if (!meta || !meta.$delta || meta.$base === undefined) return true;
    const want = this.manifest.base && this.manifest.base.sha256;
    return !want || meta.$base === want;
  }
  // a point's bytes → the point: its messages, its header merged with the base, one world's record. A header packed
  // against another base: null (live: asked again with the full header) or an error (an atlas point)
  async build(inf, bytes, extra, { mismatch = "throw" } = {}) {
    const msgs = await readStream(bytes, this.pool || null);
    const h = msgs.find((m) => m.meta.type === "header");
    if (h && !this.baseMatches(h.meta)) {
      if (mismatch === "null") return null;
      throw new Error("the point was packed against another base of this atlas");
    }
    const worlds = worldsOf(msgs, { header: (m, b) => mergeHeader(this.base, [m, b]) });
    if (!worlds.length) throw new Error("the point has no header");
    const W = worlds[0];
    const F = W.frames;
    // the world's own default speed (world seconds per played second), from the point's first state message: a screen
    // whose speed is "world" plays the point at it (EX2 §5 F1)
    const st = msgs.find((m) => m.meta.type === "state");
    const speed = st && Number(st.meta.speed) > 0 ? Number(st.meta.speed) : null;
    return { ...inf, ...extra, W, speed, size: sizeOf(msgs), tEnd: F.length ? F[F.length - 1].t : 0, bytes_gz: bytes.byteLength };
  }
  // the neighbours of a point, at low priority, at most PREFETCH_AT_ONCE at a time; a newer prefetch replaces the queue
  prefetch(values) {
    this.queue = neighbours(this.controls, values).filter((v) => {
      const inf = this.info(v);
      return inf.state === "computed" && !this.cache.has("p" + inf.i) && !this.pending.has("p" + inf.i);
    });
    this.pump();
  }
  pump() {
    while (this.active < PREFETCH_AT_ONCE && this.queue.length) {
      const v = this.queue.shift();
      this.active++;
      this.point(v, { prefetch: true }).catch(() => {}).finally(() => { this.active--; this.pump(); });
    }
  }
  // (server) a point computed live for any values (design §3.7); an on-grid value without a seed comes from the atlas
  async live(values, seed = null) {
    if (MODE !== "server") throw new Error("live points need a server");
    const key = "live:" + JSON.stringify(values) + ":" + (seed ?? "");
    const hit = this.cache.get(key);
    if (hit) return hit;
    const inf = { i: null, values: { ...values }, file: null, seed };
    const ask = (full) => this.fetchImpl(url(`api/atlas/${encodeURIComponent(this.world)}/${encodeURIComponent(this.id)}/point`), {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ values, ...(seed === null ? {} : { seed }), ...(full ? { full_header: true } : {}) }) });
    let pt = null;
    for (const full of [false, true]) {
      const r = await ask(full);
      if (!r.ok) {
        const j = await r.json().catch(() => ({}));
        // the world's refusal, as a manifest's refusals are written (lfviz: "{text}. What to change: {hint}")
        const refusal = j.hint ? { $t: "{text}. What to change: {hint}", a: { text: j.error, hint: j.hint } } : j.error || null;
        if (r.status === 400) return { ...inf, state: "refused", refusal, W: null, live: true };
        // any other status: the server's text in the viewer's language (review EX1-screens F7: a 429 on a Russian page)
        throw Object.assign(apiError(j, `${r.status} ${r.statusText}`), { status: r.status });
      }
      const H = (k) => r.headers.get(k) || null;
      pt = await this.build(inf, new Uint8Array(await r.arrayBuffer()), {
        state: "computed", refusal: null, live: true, source: H("X-LF-Source") || "computed", key: H("X-LF-Key"),
        code: H("X-LF-Code"), made: H("X-LF-Made") }, { mismatch: full ? "throw" : "null" });
      if (pt) break;  // else: packed against another base (a rebuilt atlas): asked again with the full header
    }
    this.cache.set(key, pt, pt.size);
    return pt;
  }
}
