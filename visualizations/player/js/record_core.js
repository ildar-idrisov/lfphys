// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// The record of one world and how a view is shown at a moment of it (design lfphys/sources/explore_2026-11-14_design.md
// §1.5): extracted unchanged in behaviour from player.js, which uses it for live runs and recordings, and used by the
// screens (Watch, Explore, Lab work) for the points of an atlas and for a recording played as a story.
//
//   makeWorld(header, blobs, {n, stride})  a world's record W: its header, frames, events, checks, the view's messages,
//                                           the time-indexed live set-up, actions, approximations and engine modules,
//                                           and its key frames
//   ingest(W, {meta, blobs}, opts)          one message of the world into its record (what player.js's onMessage did
//                                           with the record; the caller keeps what it shows); returns what it was
//   pushFrame(W, f, step, maxFrames)        a frame kept on the world's stride (beyond maxFrames the stride doubles)
//   showAt(view, W, t)                      the view fed the record's messages up to t: fed on when it holds nothing
//                                           later, else restored from the nearest key frame (a view with snapshot() and
//                                           restore()) or rebuilt from the record
//   rebuildView / feedView / keyBefore      the parts of showAt (player.js calls them as before)
//   feedState(view)                         what the view holds of its world's record: {W, maxOn, scan, prefix, nOn,
//                                           on, keys, keyStride}
//
// The feed state belongs to the view, not to the world (review EX1-worlds F1): two views may hold the same world's
// record at different times (Explore's trace of a re-launched shot and the shot itself share one decoded point), and
// each is fed and keyed on its own; one view's progress never marks the other's messages as given.
//   frameAt(W, t), frameIndexAt(F, t), asOf the last frame / value at or before t
//
// Nothing here computes physics: a world's messages are given to its view in their order, up to a time.
import { t } from "./i18n.js";

export const MAX_FRAMES = 20000;  // beyond it the stride of the frames kept doubles: the history stays uniform at any length
export const KEY_EVERY = 100;     // a key frame of the view every KEY_EVERY messages fed in order (owner, 2026-10-29)
export const MAX_KEYS = 256;      // beyond it every other key frame is dropped: their memory stays bounded at any length
// messages that are not the world's own (the transport's, the record's bookkeeping): the screens skip them
export const NOT_WORLD = new Set(["state", "end", "busy", "closed", "history_start", "history_end", "command", "checkpoint",
  "resumed", "record_segment"]);

// --- a world's record -------------------------------------------------------------------------------------------------
export function makeWorld(meta, blobs, { n = 1, stride = 1 } = {}) {
  const t0 = meta.t || 0;
  const W = { n: meta.world || n, header: meta, headerBlobs: blobs, live: { ...(meta.live || {}) },
              liveHist: [{ t: t0, values: { ...(meta.live || {}) } }],
              // what later messages change, as of each time (the header itself is never changed: review C1-18)
              approxHist: [{ t: t0, v: meta.approximations || [] }], engineHist: [{ t: t0, v: meta.engine || [] }],
              actionsHist: [{ t: t0, v: meta.actions || [] }],
              frames: [], nArrived: 0, stride,  // frames kept: those whose arrival number is on the stride
              events: [], checks: new Map(), viewMsgs: [],  // the feed state of a view showing it: feedState(view)
              lastSet: new Map(),  // the latest message of each set-like (type, id) in the record (repeats: U1)
              captions: [] };      // the recording's captions (design §2.2), also among the view's messages
  // settings of devices that the engine adjusted for this run (e.g. a GPU asked for but not available)
  for (const nt of ((meta.backend || {}).notes || [])) W.events.push({ t: meta.t || 0, kind: "notice", text: { $t: "ℹ devices: {note}", a: { note: nt } } });
  return W;
}

// One message into the world's record. opts: seq() numbers the checks in arrival order (the player's, shared by its
// worlds); step and maxFrames: the frames' stride (pushFrame). Returns the message's kind: "frame", "event", "check",
// "live", "error", "server_error" (a refusal of the server: not part of the record), "notice", "actions", "repeat" (an
// unchanged repeat, not kept: U1), "approx" (a view's message carrying approximations), "view" (any other message of
// the view, captions included).
let SEQ = 0;
export function ingest(W, { meta, blobs }, opts = {}) {
  switch (meta.type) {
    case "frame":
      pushFrame(W, { t: meta.t, meta, blobs }, opts.step ?? 1, opts.maxFrames ?? MAX_FRAMES);
      return "frame";
    case "event":
      W.events.push(meta); W.viewMsgs.push({ meta, blobs });
      return "event";
    case "check": {  // every version is kept: the panel shows, per check, the latest one computed by the cursor's time
      meta._seq = opts.seq ? opts.seq() : ++SEQ;
      const vs = W.checks.get(meta.id);
      if (vs) vs.push(meta); else W.checks.set(meta.id, [meta]);
      return "check";
    }
    case "live":  // the live values in force (also after a refused change: the controls roll back)
      W.live = { ...W.live, ...(meta.values || {}) };
      W.liveHist.push({ t: meta.t || 0, values: { ...W.live } });
      if (meta.engine) W.engineHist.push({ t: meta.t || 0, v: meta.engine });
      return "live";
    case "error":
      if (meta.server) return "server_error";
      W.events.push({ t: meta.t, kind: "error", text: meta.text, detail: meta.detail });
      return "error";
    case "notice":
      W.events.push({ t: meta.t, kind: "notice", text: "ℹ " + t(meta.text), detail: meta.detail });
      return "notice";
    case "actions":  // the simulation updated its actions (e.g. the current speed of each observer)
      W.actionsHist.push({ t: meta.t || 0, v: meta.actions });
      return "actions";
    default: {
      if (meta.repeat && sameAsHeld(W, meta, blobs)) return "repeat";  // an unchanged repeat changes nothing (U1)
      if (meta.repeat || SET_TYPES.has(meta.type)) W.lastSet.set(meta.type + ":" + (meta.id ?? ""), { meta, blobs });
      // a message may carry the world's approximations in force (e.g. a 3-D world's slices changed): top bar
      const approx = Array.isArray(meta.approximations);
      if (approx) W.approxHist.push({ t: meta.t || 0, v: meta.approximations });
      if (meta.type === "caption") W.captions.push(meta);
      W.viewMsgs.push({ meta, blobs });
      return approx ? "approx" : "view";
    }
  }
}

// A playground repeats the latest set-like messages at every segment start (lfviz.playground: a segment must be drawable
// on its own) with `repeat: true`. A repeat equal to the message of the same (type, id) this world's record already holds
// is not given to the view: it would change nothing but re-apply the same box, mesh, scene … (review UX-ui U1: an
// unchanged box re-sent every minute put the camera back to its first view). A viewer whose record starts at that
// segment has no earlier one and gets it.
export const SET_TYPES = new Set(["box", "mesh", "lines", "marks", "shapes", "actions", "approx", "arrow", "volume", "target", "scene"]);
export function sameAsHeld(W, meta, blobs) {
  const prev = W.lastSet.get(meta.type + ":" + (meta.id ?? ""));
  if (!prev) return false;
  const strip = (m) => { const o = { ...m }; delete o.t; delete o.repeat; delete o.blobs; return JSON.stringify(o); };
  if (strip(prev.meta) !== strip(meta)) return false;
  const ka = Object.keys(prev.blobs || {}), kb = Object.keys(blobs || {});
  if (ka.length !== kb.length) return false;
  for (const k of kb) {
    const a = prev.blobs[k], b = blobs[k];
    if (!a || a.byteLength !== b.byteLength) return false;
    const x = new Uint8Array(a.buffer, a.byteOffset, a.byteLength), y = new Uint8Array(b.buffer, b.byteOffset, b.byteLength);
    for (let i = 0; i < x.length; i++) if (x[i] !== y[i]) return false;
  }
  return true;
}

// The frames kept are those whose arrival number is a multiple of the world's stride, and the latest one (the end of
// the history until the next frame arrives); beyond maxFrames the stride doubles. The density is the same over the
// whole history at any length (review C1-12: halving all frames again and again left the start of a long session
// almost empty). step: what the frame counts for (frames replayed on (re)connection count as the server's stride each).
export function pushFrame(W, f, step = 1, maxFrames = MAX_FRAMES) {
  f.n = W.nArrived;
  W.nArrived += step;
  const F = W.frames;
  if (F.length && F[F.length - 1].n % W.stride !== 0) F.pop();
  F.push(f);
  if (F.length > maxFrames) {
    W.stride *= 2;
    let j = 0;
    for (let i = 0; i < F.length; i++) if (F[i].n % W.stride === 0 || i === F.length - 1) F[j++] = F[i];
    F.length = j;
  }
}
export function frameIndexAt(F, tt) {  // the last frame at or before tt (the first when tt is before it)
  let lo = 0, hi = F.length - 1;
  if (hi < 0) return -1;
  if (tt <= F[0].t) return 0;
  while (lo < hi) { const mid = (lo + hi + 1) >> 1; if (F[mid].t <= tt) lo = mid; else hi = mid - 1; }
  return lo;
}
export function frameAt(W, tt) { const i = frameIndexAt(W.frames, tt); return i < 0 ? null : W.frames[i]; }

// the latest value of a time-indexed list at or before t
export function asOf(list, tt) {
  const eps = 1e-12 * Math.abs(tt);
  let v = list[0].v;
  for (const h of list) { if (h.t <= tt + eps) v = h.v; else break; }
  return v;
}

// --- the view at a time: fed the record's messages up to it; when going back, restored from its nearest key frame (a
// view with snapshot() / restore()) or rebuilt from the record (a view without) ------------------------------------------
// FEED: a view → what it holds of its world's record (the world W, rebuilt from its header): the messages [0, prefix)
// all given, nOn given in all, on[i] whether message i was given, scan the first not given, maxOn the latest time given,
// the view's key frames
const FEED = new WeakMap();
const freshState = (W) => ({ W, maxOn: -Infinity, scan: 0, prefix: 0, nOn: 0, on: [], keys: [], keyStride: 1 });
export function feedState(view) { return FEED.get(view) || null; }
export function ownerOf(view) { const st = FEED.get(view); return st ? st.W : null; }
export function forget(view) { FEED.delete(view); }  // the next showAt / rebuildView rebuilds from the record

// opts: {keyEvery, maxKeys, dbg} (dbg: counters {fromKey, full, keyFailed, lastMs, lastFed} for the tests of the page)
export function rebuildView(view, W, tt, opts = {}) {
  const dbg = opts.dbg || {};
  const held = FEED.get(view);
  const k = held && held.W === W && view.restore ? keyBefore(held, tt) : null;
  const t0 = performance.now();
  if (k) {
    try {
      view.restore(k.snap);
      held.on.length = Math.min(held.on.length, k.i);
      held.prefix = held.nOn = held.scan = k.i; held.maxOn = k.maxOn;
      feedView(view, W, tt, opts);
      dbg.fromKey = (dbg.fromKey || 0) + 1; dbg.lastMs = performance.now() - t0; dbg.lastFed = held.prefix - k.i;
      return;
    } catch (e) { console.error("key frame not restored, rebuilding from the record:", e); dbg.keyFailed = (dbg.keyFailed || 0) + 1; }
  }
  view.reset && view.reset();
  view.onHeader(W.header, W.headerBlobs);
  const st = freshState(W);
  FEED.set(view, st);
  feedView(view, W, tt, opts);
  dbg.full = (dbg.full || 0) + 1; dbg.lastMs = performance.now() - t0; dbg.lastFed = st.prefix;
}
// the latest key frame at or before t that the view's present state contains (it holds the messages in order up to a
// later point; a key frame records how long its data were then). st: the view's feed state (feedState(view))
export function keyBefore(st, tt) {
  if (!st || st.nOn !== st.prefix) return null;  // the view holds messages out of order: only a rebuild is safe
  const eps = 1e-12 * Math.abs(tt);
  for (let j = st.keys.length - 1; j >= 0; j--) {
    const k = st.keys[j];
    if (k.i <= st.prefix && k.maxOn <= tt + eps) return k;
  }
  return null;
}
// one key frame per step of keyEvery × keyStride messages; beyond maxKeys the step doubles and the key frames on the
// coarser grid are kept: uniform over the whole record at any length (review CK-3: dropping every other key frame
// while new ones came at the full rate left the start of a long session without any)
function takeKey(view, st, keyEvery, maxKeys) {
  const step = keyEvery * st.keyStride, last = st.keys.length ? st.keys[st.keys.length - 1] : null;
  if (Math.floor(st.prefix / step) <= (last ? Math.floor(last.i / step) : 0)) return;
  try { st.keys.push({ i: st.prefix, maxOn: st.maxOn, snap: view.snapshot() }); } catch (e) { console.error(e); return; }
  if (st.keys.length > maxKeys) {
    st.keyStride *= 2;
    const s2 = keyEvery * st.keyStride, seen = new Set();
    st.keys = st.keys.filter((k) => { const b = Math.floor(k.i / s2); if (seen.has(b)) return false; seen.add(b); return true; });
  }
}
// the view fed the messages of W up to t that it has not been given yet (a view that holds another world, or none, is
// rebuilt from W's header first)
export function feedView(view, W, tt, opts = {}) {
  let st = FEED.get(view);
  if (!st || st.W !== W) { rebuildView(view, W, tt, opts); return; }
  const keyEvery = opts.keyEvery || KEY_EVERY, maxKeys = opts.maxKeys || MAX_KEYS;
  const L = W.viewMsgs, on = st.on, eps = 1e-12 * Math.abs(tt), keyed = !!(view.snapshot && view.restore);
  let first = -1;
  for (let i = st.scan; i < L.length; i++) {
    if (on[i]) continue;
    const m = L[i], tm = m.meta.t ?? 0;
    if (tm <= tt + eps) {
      on[i] = true; st.maxOn = Math.max(st.maxOn, tm); st.nOn++;
      try { view.onMessage(m.meta, m.blobs); } catch (e) { console.error(e); }
      if (i === st.prefix) {
        st.prefix++;
        while (st.prefix < L.length && on[st.prefix]) st.prefix++;
        if (keyed && st.nOn === st.prefix) takeKey(view, st, keyEvery, maxKeys);
      }
    } else if (first < 0) first = i;
  }
  st.scan = first < 0 ? L.length : first;
}
// the view brought to time t of world W: fed on, or (it holds another world, or something from later) rebuilt
export function showAt(view, W, tt, opts = {}) {
  if (!W) return;
  const st = FEED.get(view);
  if (!st || st.W !== W || st.maxOn > tt + 1e-12 * Math.abs(tt)) rebuildView(view, W, tt, opts);
  else feedView(view, W, tt, opts);
}

// A whole decoded stream (a point of an atlas, a recording) as worlds: [W, …], each with its messages ingested. The
// transport's and the record's own messages (NOT_WORLD) are skipped; a header starts a world. header(meta, blobs) may
// replace a header before the world is made (a point's header delta merged with its base: atlas.js).
export function worldsOf(messages, { header = null } = {}) {
  const out = [];
  let W = null;
  for (const m of messages) {
    const type = m.meta.type;
    if (type === "header") {
      const [hm, hb] = header ? header(m.meta, m.blobs) : [m.meta, m.blobs];
      W = makeWorld(hm, hb, { n: out.length + 1 });
      out.push(W);
      continue;
    }
    if (!W || NOT_WORLD.has(type)) continue;
    ingest(W, m);
  }
  return out;
}
