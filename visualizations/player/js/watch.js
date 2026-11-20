// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// The Watch screen (design lfphys/sources/explore_2026-11-14_design.md §3.6, §2.2): a recording of a real run played as
// a story, with captions. The recording's frames were taken at its fps of played time (the script's speed and its new
// worlds are in them), so the timeline is the sequence of its frames across its worlds, played at the recorded pace
// («slow»: a quarter of it). The caption strip shows the latest caption as of the cursor: a caption is an accumulative
// message of the recording at its frame (caption {t, text, n, at, hold?}), so it keeps its place under frame thinning
// and speed changes. Its chapters are ticks on the timeline: a click jumps there, ◀◀ / ▶▶ go to the previous or next
// one. A caption with `hold` holds the playback for that many seconds when it is reached, so it can be read; any action
// of the viewer (▶/❚❚, a scrub, a chapter) ends the hold (review EX1-screens F12). The playback starts at the beginning
// and pauses at the end. «More recordings» is a select. The view is fed the recording's messages up to the frame shown
// (record_core.js); nothing is computed here.
//
// The time label states the world's time and the playback factor for every world («world 420 ms · slow motion ×10»;
// integrator D8, review EX1-worlds F4), written as Explore's (EX2 §5 F12: explore.js worldTime and factorText): the
// world's time on a human scale (ns … s), in the world's own unit when its header declares units.t_show (u34: GM/c³),
// in seconds at school («0.45 s»); the factor is the frames' own world Δt × the frames per played second × the speed
// chosen (normal / slow), «real time» within 5 % of 1, and in powers of ten from 10⁶ on («slow motion ×1.2·10⁹», not
// «×1199040767»), so that no view needs to repeat it.
//
// An optional view hook (integrator D8): view.setStory({worlds, w, fps}) is called when the world shown changes (a new
// recording or the next world of the story): `worlds` the recording's decoded worlds (record_core.js), `w` the index of
// the one shown, `fps` the recording's frames per played second. A view uses it to keep one fixed scale over the whole
// story and to draw the earlier worlds as faded traces (S03).
import { readStream, url } from "./api.js";
import { t } from "./i18n.js";
import { frameIndexAt, showAt, worldsOf } from "./record_core.js";
import { el, fill } from "./ui.js";
import { factorText, secs, worldTime } from "./explore.js";

export const SLOW = 0.25;

// «world 420 ms · slow motion ×10»: the world's time (header: the shown world's, for units.t_show; school: in seconds) and
// the playback factor (world seconds per played second r), as Explore's (EX2 §5 F12); without a rate, the time alone
export function rateText(worldT, r, header = null, school = false) {
  return [t("world {t}", { t: worldTime(worldT, header, school) }), factorText(r)].filter(Boolean).join(" · ");
}

// The story of a decoded recording: its worlds, the global sequence of their frames [{w, i}] and its captions placed
// at the frame that follows each one in the stream (the recorder writes a caption just before its frame)
export function story(messages) {
  const worlds = worldsOf(messages);
  const steps = [], caps = [];
  let w = -1, nFrames = 0;
  for (const m of messages) {
    const ty = m.meta.type;
    if (ty === "header") { w++; nFrames = 0; continue; }
    if (w < 0) continue;
    if (ty === "frame") { steps.push({ w, i: nFrames }); nFrames++; }
    else if (ty === "caption") caps.push({ ...m.meta, step: steps.length });
  }
  for (const c of caps) c.step = Math.min(c.step, Math.max(0, steps.length - 1));
  return { worlds, steps, captions: caps };
}
// the latest caption at or before step k (null before the first)
export function captionAt(captions, k) {
  let c = null;
  for (const x of captions) { if (x.step <= k) c = x; else break; }
  return c;
}

export async function create(host, kit, spec) {
  const index = kit.index || {};
  const ids = [spec.recording, ...(spec.more || [])];
  // each recording here, or (a server without it) the published site's of the same world version (integrator D11)
  const source = (id) => (kit.recordingSource ? kit.recordingSource(id)
    : { entry: (index.recordings || []).find((r) => r.id === id) || null, base: url(`recordings/${kit.world}/`) });
  const recs = ids.map((id) => { const src = source(id); return { id, entry: src.entry || null, base: src.base, fromSite: !!src.fromSite,
    spec: (kit.viz.recordings || []).find((r) => r.id === id) || null }; }).filter((r) => r.entry || r.spec);
  const V = { rec: null, story: null, pos: 0, playing: false, rate: 1, wall: 0, holdUntil: 0, held: -1, started: false, storySig: null };
  const view = kit.newView();
  const caption = el("div", { class: "dm-caption" + (kit.school ? " big" : ""), role: "status", "aria-live": "polite" });
  const stage = el("div", { class: "dm-stage" }, view.center, caption);
  const sel = recs.length > 1 ? el("select", { class: "dm-more", "aria-label": t("More recordings"), onchange: () => open(sel.value) },
    recs.map((r) => el("option", { value: r.id }, t((r.entry || r.spec).label) || r.id))) : null;
  const info = el("div", { class: "dm-watch-info muted" });
  const side = el("div", { class: "dm-side dm-watch-side" }, sel ? el("label", { class: "dm-ctl" }, el("span", { class: "dm-ctl-label" }, t("More recordings")), sel) : null, info);
  const bar = kit.transport({
    play: () => playPressed(), reset: () => go(0), scrub: (i) => go(i), rate: (r) => { V.rate = r === 1 ? 1 : SLOW; kit.self.rate = V.rate; },
    prev: () => chapter(-1), next: () => chapter(+1),
  });
  fill(host, el("div", { class: "dm-main" }, stage, side), bar.el);

  // a recording chosen: only the latest choice is shown (review R2-P F10: a slow rosette arriving after a later choice
  // of mercury played under «mercury»), and one that cannot be loaded says so (a 503 left «loading the recording…» for
  // ever and an uncaught error)
  let openSeq = 0;
  async function open(id) {
    const seq = ++openSeq;
    const r = recs.find((x) => x.id === id);
    V.playing = false;
    if (!r || !r.entry) {
      V.rec = r; V.story = null;
      caption.textContent = t("No recording yet: record it locally (site/record.py) or compute live");
      caption.hidden = false;
      kit.dirty();
      return;
    }
    caption.textContent = t("loading the recording…");
    caption.hidden = false;
    let st;
    try {
      const resp = await fetch(r.base + r.entry.file);
      if (!resp.ok) throw new Error(`${resp.status} ${resp.statusText}`);
      st = story(await readStream(new Uint8Array(await resp.arrayBuffer())));
    } catch (e) {
      if (seq !== openSeq) return;
      V.story = null; V.rec = r;
      caption.textContent = t("This recording could not be loaded: {why}", { why: e.message });
      caption.hidden = false;
      kit.dirty();
      return;
    }
    if (seq !== openSeq) return;  // a later choice came first
    if (sel && sel.value !== id) sel.value = id;
    V.story = st;
    V.rec = r; V.pos = 0; V.held = -1; V.holdUntil = 0; V.storySig = null;
    const S = V.story, n = S.steps.length;
    bar.ticks(S.captions.map((c) => ({ at: n > 1 ? c.step / (n - 1) : 0, title: t(c.text), onclick: () => go(c.step) })));
    const e = r.entry;
    fill(info, el("div", {}, t((e || {}).label)), el("div", {}, t("{s:g} s at {fps:g} frames per second", { s: e.seconds, fps: e.fps })),
      el("div", {}, t("Captions: {n:d}", { n: S.captions.length })),
      r.fromSite ? el("div", {}, t("Played from the public site: this server has no local copy (the same version of the world).")) : null);
    kit.dirty();
    V.playing = n > 1; V.wall = performance.now();  // the playback starts at the beginning
  }
  const fps = () => { const e = V.rec && V.rec.entry; return e ? (e.fps || 20) / Math.max(1, e.frame_stride || 1) : 20; };
  const curStep = () => Math.max(0, Math.min(Math.floor(V.pos + 1e-9), V.story.steps.length - 1));
  function go(k) {
    if (!V.story) return;
    V.pos = Math.max(0, Math.min(k, V.story.steps.length - 1));
    V.playing = false; V.held = curStep(); V.holdUntil = 0; kit.dirty();
  }
  function playPressed() {
    if (!V.story) return;
    V.holdUntil = 0;  // any action of the viewer ends a caption's hold (review EX1-screens F12)
    if (V.playing) { V.playing = false; kit.dirty(); return; }
    if (curStep() >= V.story.steps.length - 1) V.pos = 0;  // at the end: from the start
    V.playing = true; V.wall = performance.now(); V.held = curStep(); kit.dirty();
  }
  function chapter(d) {
    if (!V.story) return;
    const k = curStep(), C = V.story.captions;
    const target = d > 0 ? C.find((c) => c.step > k) : [...C].reverse().find((c) => c.step < k - (V.playing ? 1 : 0) && c.step < k);
    go(target ? target.step : d > 0 ? V.story.steps.length - 1 : 0);
  }

  // world seconds per played second around frame i of world W (its frames' own Δt × the frames per played second)
  function worldRate(W, i) {
    const F = W.frames, a = Math.max(0, i - 3), b = Math.min(F.length - 1, i + 3);
    if (b <= a) return null;
    const dt = (F[b].t - F[a].t) / (b - a);
    return dt > 0 ? dt * fps() * V.rate : null;
  }
  function render() {
    const S = V.story;
    if (!S || !S.steps.length) return;
    const k = curStep(), st = S.steps[k], W = S.worlds[st.w], f = W.frames[st.i];
    if (view.setStory) {  // the optional hook (integrator D8): the story's worlds, once per world shown
      const sig = `${V.rec.id}|${st.w}`;
      if (sig !== V.storySig) { V.storySig = sig; try { view.setStory({ worlds: S.worlds, w: st.w, fps: fps() }); } catch (e) { console.error(e); } }
    }
    showAt(view, W, f.t);
    kit.self.frame = f;
    try { view.render(f.meta, f.t, f.blobs); } catch (e) { console.error(e); }
    const c = captionAt(S.captions, k);
    const text = c ? t(c.text) : "";
    if (caption.textContent !== text) caption.textContent = text;
    caption.dataset.n = c ? String(c.n) : "";
    caption.hidden = !text;
    const played = k / fps(), total = (S.steps.length - 1) / fps();
    bar.update({ playing: V.playing, i: k, max: S.steps.length - 1,
      text: `${rateText(f.t, worldRate(W, st.i), W.header, !!kit.school)} · ${secs(played)} / ${secs(total)}`,
      title: t("The world's own time, how much slower or faster than real time it plays, and the position in the recording") });
  }

  const API = {
    tick(now) {
      const S = V.story;
      if (V.playing && S && now < V.holdUntil) V.wall = now;  // a caption's hold: the story waits so it can be read
      else if (V.playing && S) {
        const dt = Math.min(0.25, (now - V.wall) / 1000);
        V.wall = now;
        const before = curStep();
        V.pos += dt * fps() * V.rate;
        let k = curStep();
        // a caption with a hold reached: stop at its frame and wait
        // (a caption at the step the playback started from holds too, unless the viewer started it there: V.held)
        const hc = S.captions.find((c) => c.hold && c.step >= before && c.step <= k && c.step !== V.held);
        if (hc) { V.pos = hc.step; k = hc.step; V.held = hc.step; V.holdUntil = now + 1000 * hc.hold; }
        if (k >= S.steps.length - 1) { V.pos = S.steps.length - 1; V.playing = false; }
        if (k !== before || !V.playing) this.dirty = true;
      } else V.wall = now;
      if (this.dirty) { this.dirty = false; render(); }
    },
    show() { this.dirty = true; },
    hide() { V.playing = false; },
    key(e) {
      if (e.key === " ") { e.preventDefault(); playPressed(); }
      else if (e.key === "ArrowRight") { e.preventDefault(); if (V.story) go(curStep() + 1); }
      else if (e.key === "ArrowLeft") { e.preventDefault(); if (V.story) go(curStep() - 1); }
      else if (e.key === "Home") { e.preventDefault(); go(0); }
    },
    jumpTo(tt) {  // a time of the world shown
      if (!V.story) return;
      const k = curStep(), w = V.story.steps[k].w, W = V.story.worlds[w];
      const i = frameIndexAt(W.frames, tt);
      const g = V.story.steps.findIndex((s) => s.w === w && s.i === i);
      if (g >= 0) go(g);
    },
    drawerKey() {
      if (!V.story) return "none";
      const k = curStep(), st = V.story.steps[k], W = V.story.worlds[st.w], tt = W.frames[st.i].t;
      let n = 0;
      for (const vs of W.checks.values()) for (const x of vs) if ((x.t ?? 0) <= tt) n++;
      return `${V.rec.id}|${st.w}|${n}|${W.events.filter((e) => (e.t ?? 0) <= tt).length}`;
    },
    drawer() {
      const e = V.rec && V.rec.entry;
      if (!V.story || !e) return kit.howWeKnow({ W: null, tt: 0, empty: t("No recording yet: record it locally (site/record.py) or compute live") });
      const k = curStep(), st = V.story.steps[k], W = V.story.worlds[st.w], tt = W.frames[st.i].t;
      const ix = kit.index || {};
      const passport = [[t("Recording"), `${kit.world}/${V.rec.id}`], [t("Code"), String(e.code_hash ?? ix.code_hash ?? "")],
        [t("Recorded"), String(e.made ?? ix.made ?? "").replace("T", " ").slice(0, 19)], [t("Random seed"), e.seed],
        [t("World"), t("{n:d} of {total:d}", { n: st.w + 1, total: V.story.worlds.length })],
        [t("Played"), t("{s:g} s at {fps:g} frames per second", { s: e.seconds, fps: e.fps })]];
      return kit.howWeKnow({ W, tt, passport, note: t("A recording of a real run, made by the recorder from the world's code: it plays without computing.") });
    },
    // the world shown, as its header says it was made (review EX1-screens F13): its preset, parameters and seed
    liveBody() {
      const s0 = V.rec && (V.rec.entry || V.rec.spec);
      if (!s0) return null;
      const st = V.story && V.story.steps.length ? V.story.steps[curStep()] : null;
      const h = st ? V.story.worlds[st.w].header : null;
      if (!h) return { preset: s0.preset, seed: s0.seed ?? 1 };
      return { preset: h.preset || s0.preset, ...(h.params ? { params: { ...h.params } } : {}), seed: h.seed ?? s0.seed ?? 1 };
    },
    get state() { return V; },
  };
  window.__lfWatch = { state: V, caption: () => caption.textContent, step: () => (V.story ? curStep() : -1), rec: () => (V.rec ? V.rec.id : null) };
  if (recs.length) await open(recs[0].id);
  else caption.textContent = t("No recording yet: record it locally (site/record.py) or compute live");
  return API;
}
