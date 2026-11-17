// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// The Explore screen (design lfphys/sources/explore_2026-11-14_design.md §3.4): the world's own view of a point of the
// screen's atlas, chosen by 2–5 controls whose sliders stop only at the computed grid values (on a server they also
// move between them, and a released off-grid value is computed live: §3.7). Every launched shot keeps its own launch
// time on one shared playback clock, so up to `traces` earlier shots fly or lie on the ground together, faded. What is
// shown at a time is the frame of the point at or before it, and the view holds exactly the point's messages up to that
// frame: nothing is computed or interpolated in the browser.
//
//   time "flight"   ▶ Launch starts the armed point at t = 0; "buildup": the cursor is the point's time and a change
//                   keeps it; "none": the point at its end, no time bar
//   acts "next"     a change arms the next point: the view shows the new set-up at once, earlier shots go on as traces;
//                   "now": the shown point is replaced and the cursor kept
import { openAtlas, snap, gridIndex } from "./atlas.js";
import { t } from "./i18n.js";
import { frameAt, frameIndexAt, showAt } from "./record_core.js";
import { el, fill, fmt, num } from "./ui.js";

export const SLOW = 0.25;  // the «slow» speed: a quarter of real time
// a time of the world on the time bar, in seconds (school: «0.45 s», never «451.6 ms»)
export const secs = (x) => `${fmt(x, ".2f")}\u00a0${t("s")}`;

// --- labels and values ------------------------------------------------------------------------------------------------
export function controlLabel(c) {
  const label = t(c.label), unit = c.unit ? t(c.unit) : "";
  return unit && !label.includes(unit) ? t("{label}, {unit}", { label, unit }) : label;
}
export function valueText(c, v) {
  if (typeof v === "boolean") return v ? t("on") : t("off");
  if (typeof v === "number") return fmt(v, ".4g");
  return t(v);
}
// a value with its control's unit («1 m», «30°»: no space before the degree sign)
export function valueUnitText(c, v) {
  const u = c.unit ? t(c.unit) : "";
  return `${valueText(c, v)}${typeof v === "number" && u ? (u === "°" ? u : "\u00a0" + u) : ""}`;
}
// a short label of a point's values («h 1 m, angle 30°»), for the passport
export function valuesText(controls, values) {
  return controls.map((c) => `${t(c.label)} ${valueUnitText(c, values[c.param])}`).join(", ");
}
// a trace's label: only the values that differ from the point shown («Launch speed 10 m/s»; review EX1-worlds F11,
// EX1-screens F8), empty for the same set-up
export function diffText(controls, values, now) {
  return controls.filter((c) => now && values[c.param] !== now[c.param]).map((c) => `${t(c.label)} ${valueUnitText(c, values[c.param])}`).join(", ");
}
// a moment with its zone, as the server writes it (ISO 8601): «2026-11-17 15:16:08 UTC», «… UTC+03:00»
export function when(iso) {
  const m = /^(\d{4}-\d\d-\d\d)[T ](\d\d:\d\d:\d\d)(?:\.\d+)?(Z|[+-]\d\d:?\d\d)?$/.exec(String(iso || ""));
  if (!m) return iso ? String(iso) : "—";
  const z = !m[3] ? "" : m[3] === "Z" || /^[+-]00:?00$/.test(m[3]) ? " UTC" : ` UTC${m[3]}`;
  return `${m[1]} ${m[2]}${z}`;
}
// a readout to 4 significant digits with its trailing zeros («23.90 m» next to «18.51 m»; review EX1-worlds F17)
export function readoutText(v) {
  if (!Number.isFinite(v)) return "—";
  const d = v === 0 ? 3 : Math.max(0, Math.min(6, 3 - Math.floor(Math.log10(Math.abs(v)))));
  return fmt(v, `.${d}f`);
}

// A control of a grid (site/atlas.py manifest "controls" with the catalogue's label, unit, kind; registry.screens_of):
// slider (detents at the grid values only; on a server free between them), toggle or select (one button per value).
// onPick(value, {final}) is called when a value is chosen. Returns {el, set(value), disable(on)}.
export function controlRow(c, value, onPick, { server = false } = {}) {
  const head = el("div", { class: "dm-ctl-head" }, el("span", { class: "dm-ctl-label" }, controlLabel(c)), el("output", { class: "dm-ctl-val mono" }, ""));
  const out = head.lastChild;
  const row = el("div", { class: "dm-ctl", "data-param": c.param }, head);
  const vals = c.values;
  let cur = value;
  if (c.kind === "toggle" || c.kind === "select" || !vals.every((x) => typeof x === "number")) {
    const seg = el("div", { class: "dm-seg dm-ctl-seg", role: "group", "aria-label": controlLabel(c) }, vals.map((v) => el("button", {
      "data-value": JSON.stringify(v), "aria-pressed": "false", onclick: () => onPick(v, { final: true }) }, valueText(c, v))));
    row.append(seg);
    return {
      el: row,
      set(v) {
        cur = v; out.textContent = valueText(c, v);
        for (const b of seg.children) { const on = JSON.parse(b.dataset.value) === v; b.classList.toggle("on", on); b.setAttribute("aria-pressed", String(on)); }
      },
      disable(on) { for (const b of seg.children) b.disabled = on; },
    };
  }
  const lo = vals[0], hi = vals[vals.length - 1];
  const gaps = vals.slice(1).map((v, i) => v - vals[i]).filter((g) => g > 0);
  const fine = server && gaps.length ? Math.min(...gaps) / 20 : null;
  // the site: the slider's positions are the grid's indices (a value between detents cannot be chosen); a server: the
  // value itself in fine steps, snapped to a detent near it, any other value computed live when released
  const input = fine ? el("input", { type: "range", class: "dm-slider", min: lo, max: hi, step: fine, "aria-label": controlLabel(c) })
    : el("input", { type: "range", class: "dm-slider", min: 0, max: vals.length - 1, step: 1, "aria-label": controlLabel(c) });
  // a value within a tenth of the local step of a detent (the gap to its neighbour on that side) snaps to it (RULES §10;
  // review EX1-screens F18: the smallest gap of the control snapped only within 0.1 m between 5 and 10 m)
  const valueOf = () => {
    if (!fine) return vals[Number(input.value)];
    const x = Number(input.value), near = snap(c, x), k = vals.indexOf(near);
    const side = x >= near ? vals[k + 1] : vals[k - 1];
    const gap = side === undefined ? Math.min(...gaps) : Math.abs(side - near);
    if (Math.abs(near - x) <= 0.1 * gap + 1e-12 * Math.abs(near)) return near;
    return Number(x.toPrecision(3));
  };
  const valueSay = (v) => { const tx = valueUnitText(c, v); input.setAttribute("aria-valuetext", tx); return tx; };  // F10: the value, not the index
  input.oninput = () => { const v = valueOf(); out.textContent = valueText(c, v); valueSay(v); out.classList.toggle("dm-off-grid", gridIndex(c, v) < 0); };
  input.onchange = () => onPick(valueOf(), { final: true });
  // the detents: a tap on one chooses it (touch: the thumb need not be dragged). Out of the tab order: the slider is the
  // keyboard's way (review EX1-screens F10); their hit area is 44 px high and as wide as the gap to the neighbours (F15)
  const pos = (v, i) => 100 * (fine ? (v - lo) / (hi - lo || 1) : i / Math.max(1, vals.length - 1));
  const ticks = el("div", { class: "dm-detents" }, vals.map((v, i) => {
    const gapPct = Math.min(i > 0 ? pos(v, i) - pos(vals[i - 1], i - 1) : Infinity, i < vals.length - 1 ? pos(vals[i + 1], i + 1) - pos(v, i) : Infinity);
    const b = el("button", {
      class: "dm-detent", tabindex: "-1", "aria-pressed": "false", style: { left: `${pos(v, i).toFixed(3)}%` },
      title: valueText(c, v), "aria-label": valueUnitText(c, v), onclick: () => onPick(v, { final: true }) },
    vals.length <= 12 || i % Math.ceil(vals.length / 10) === 0 || i === vals.length - 1 ? valueText(c, v) : "");
    b.style.setProperty("--gap", Number.isFinite(gapPct) ? gapPct.toFixed(3) : "100");
    return b;
  }));
  row.append(el("div", { class: "dm-slider-box" }, input, ticks));
  return {
    el: row,
    set(v) {
      cur = v;
      const k = gridIndex(c, v);
      input.value = String(fine ? v : Math.max(0, k));
      out.textContent = valueText(c, v);
      valueSay(v);
      out.classList.toggle("dm-off-grid", k < 0);
      for (const [i, b] of [...ticks.children].entries()) { b.classList.toggle("on", i === k); b.setAttribute("aria-pressed", String(i === k)); }
    },
    disable(on) { input.disabled = on; for (const b of ticks.children) b.disabled = on; },
    get value() { return cur; },
  };
}

// a launched shot at or past its end (within a rounding of the clock: a scrub to the last frame is its end)
export const ended = (shot, clock) => shot.launchedAt !== null && shot.launchedAt !== undefined && clock - shot.launchedAt >= shot.pt.tEnd - 1e-9;

// --- a shot on the shared clock -------------------------------------------------------------------------------------------
// shot: {pt (atlas point), launchedAt (clock value, null: not launched), label}; its local time on the clock
export function localT(shot, clock) {
  if (!shot || !shot.pt || !shot.pt.W) return 0;
  if (shot.launchedAt === null || shot.launchedAt === undefined) return 0;
  return Math.max(0, Math.min(shot.pt.tEnd, clock - shot.launchedAt));
}

export async function create(host, kit, spec) {
  const src = kit.atlasSource ? kit.atlasSource(spec.atlas)
    : { why: t("No atlas of this screen yet: it is built with the site (site/atlas.py).") };
  if (!src.entry) {
    fill(host, el("div", { class: "page dm-missing" }, el("p", {}, src.why),
      kit.server ? el("p", { class: "muted" }, t("“▶ Compute live” at the top runs the same set-up on this server.")) : null));
    return { liveBody: () => ({ preset: spec.preset, params: { ...spec.fixed } }) };
  }
  const A = await openAtlas(kit.world, src.entry, { base: src.base });
  // the manifest's grid with the catalogue's labels, units and kinds (registry.screens_of)
  A.controls = A.controls.map((c) => ({ ...((spec.controls || []).find((x) => x.param === c.param) || {}), ...c }));
  const timeMode = spec.time || "flight", acts = spec.acts || "next", maxTraces = Math.max(0, spec.traces || 0);
  const E = { values: { ...A.defaults }, cur: null, traces: [], clock: 0, playing: false, rate: 1, wall: 0, loading: 0,
    sig: "", tracesSig: "", refused: null, seq: 0, live: null };
  const view = kit.newView();
  const stage = el("div", { class: "dm-stage" }, view.center);
  const refusedBox = el("div", { class: "dm-refusal", role: "status", hidden: true });
  const loadingBox = el("div", { class: "dm-loading", hidden: true }, t("loading…"));
  stage.append(el("div", { class: "dm-stage-note" }, refusedBox));
  // readouts: the measurables the world declares in its header, shown once the time has reached them («—» before)
  const readBox = el("div", { class: "dm-readouts" });
  const ctls = A.controls.map((c) => {
    const r = controlRow(c, E.values[c.param], (v) => pick(c, v), { server: kit.server });
    r.set(E.values[c.param]);
    return r;
  });
  // overlays the view declares, those the screen names; their defaults the view's
  const ovl = (view.overlays || []).filter((o) => !spec.overlays || !spec.overlays.length || spec.overlays.includes(o.id));
  const ovBox = ovl.length ? el("details", { class: "dm-overlays", open: !matchMedia("(max-width: 999px)").matches },
    el("summary", {}, t("Show")), ovl.map((o) => {
      const cb = el("input", { type: "checkbox", checked: !!o.default, "data-overlay": o.id, onchange: () => view.setOverlay && view.setOverlay(o.id, cb.checked) });
      return el("label", { class: "dm-check" }, cb, " ", t(o.label));
    })) : null;
  const clearBtn = maxTraces ? el("button", { class: "dm-clear", onclick: () => { E.traces = []; kit.dirty(); } }, t("Clear traces")) : null;
  const anotherBtn = kit.server && timeMode === "buildup" ? el("button", { title: t("Compute this point again on the server with the next random seed: another sample of the same statistics"),
    onclick: () => another() }, t("Another sample")) : null;
  // a law control (standard worlds only; never at school, registry) changes the physics: flagged as the live player does
  const modBox = el("div", { class: "dm-mod", hidden: true });
  const side = el("div", { class: "dm-side" }, modBox,
    el("div", { class: "dm-ctls" }, ctls.map((r) => r.el)), loadingBox,
    el("div", { class: "dm-refusal-side", role: "status" }),
    ovBox, readBox, el("div", { class: "row" }, clearBtn, anotherBtn));
  const sideRefusal = side.querySelector(".dm-refusal-side");
  const bar = timeMode === "none" ? null : kit.transport({
    launchLabel: timeMode === "flight" ? t("▶ Launch") : "▶",
    play: () => playPressed(), reset: () => resetPressed(), scrub: (i) => scrub(i), rate: (r) => { E.rate = r === 1 ? 1 : SLOW; kit.self.rate = E.rate; },
  });
  fill(host, el("div", { class: "dm-main" }, stage, side), bar ? bar.el : null);
  // the readouts: in the side column on a desktop, over the view's corner on a phone (design §3.2)
  const narrow = matchMedia("(max-width: 999px)");
  const placeReadouts = () => { if (narrow.matches) stage.append(readBox); else side.insertBefore(readBox, side.lastChild); };
  placeReadouts();
  narrow.addEventListener("change", placeReadouts);

  // --- points --------------------------------------------------------------------------------------------------------
  async function load(values) {
    const seq = ++E.seq;
    const slow = setTimeout(() => { if (seq === E.seq) loadingBox.hidden = false; }, 300);
    try {
      const onGridNow = A.controls.every((c) => gridIndex(c, values[c.param]) >= 0);
      const pt = onGridNow ? await A.point(values) : await A.live(values, E.seed ?? null);
      if (seq !== E.seq) return null;  // a newer choice came first
      if (onGridNow) A.prefetch(values);
      return pt;
    } catch (e) {
      if (seq === E.seq) showRefusal(t("This point could not be loaded: {why}", { why: e.message }));
      return null;
    } finally { clearTimeout(slow); if (seq === E.seq) loadingBox.hidden = true; }
  }
  function showRefusal(text) {
    E.refused = text;
    refusedBox.textContent = text || ""; refusedBox.hidden = !text;
    sideRefusal.textContent = text || "";
    kit.dirty();
  }
  async function pick(c, v) {
    E.values = { ...E.values, [c.param]: v };
    for (const [j, r] of ctls.entries()) r.set(E.values[A.controls[j].param]);
    const pt = await load(E.values);
    if (!pt) return;
    if (pt.state === "refused") { showRefusal(t(pt.refusal)); return; }
    showRefusal(null);
    setPoint(pt);
  }
  function setPoint(pt) {
    const old = E.cur;
    if (acts === "now" || timeMode !== "flight") {
      const keep = old ? localT(old, E.clock) : 0;
      if (old && old.pt !== pt) pushTrace(old);
      E.cur = { pt, launchedAt: timeMode === "none" ? E.clock - pt.tEnd : E.clock - Math.min(keep, pt.tEnd), label: valuesText(A.controls, pt.values) };
    } else {
      if (old && old.launchedAt !== null) pushTrace(old);  // a launched shot goes on as a trace
      E.cur = { pt, launchedAt: null, label: valuesText(A.controls, pt.values) };
    }
    kit.dirty();
  }
  function pushTrace(shot) {
    if (!maxTraces) return;
    E.traces.push(shot);
    while (E.traces.length > maxTraces) E.traces.shift();
  }
  async function another() {
    E.seed = (E.seed ?? A.manifest.seed ?? 1) + 1;
    const pt = await A.live(E.values, E.seed).catch((e) => { showRefusal(e.message); return null; });
    if (pt && pt.state === "computed") setPoint(pt);
  }

  // --- time ----------------------------------------------------------------------------------------------------------
  const flying = () => [E.cur, ...E.traces].some((s) => s && s.launchedAt !== null && s.pt && s.pt.W && !ended(s, E.clock));
  function playPressed() {
    if (E.refused || !E.cur || !E.cur.pt.W) return;
    if (E.playing) { E.playing = false; kit.dirty(); return; }
    if (timeMode === "flight") {
      const c = E.cur;
      if (c.launchedAt === null) c.launchedAt = E.clock;
      else if (ended(c, E.clock)) {  // landed: launch the armed point again
        pushTrace(c);
        E.cur = { ...c, launchedAt: E.clock };
      }
    } else if (ended(E.cur, E.clock)) E.cur.launchedAt = E.clock;  // at its end: from the start
    E.playing = true; E.wall = performance.now(); kit.dirty();
  }
  function resetPressed() {
    E.playing = false;
    if (E.cur) E.cur.launchedAt = timeMode === "flight" ? null : E.clock;
    kit.dirty();
  }
  function scrub(i) {
    const c = E.cur;
    if (!c || !c.pt.W) return;
    const f = c.pt.W.frames[Math.max(0, Math.min(i, c.pt.W.frames.length - 1))];
    if (c.launchedAt === null) c.launchedAt = E.clock;
    E.clock = c.launchedAt + f.t;  // the shared clock moves: the traces move with it
    E.playing = false; kit.dirty();
  }
  function stepFrame(d) {
    const c = E.cur;
    if (!c || !c.pt.W) return;
    const F = c.pt.W.frames, i = frameIndexAt(F, localT(c, E.clock));
    scrub(Math.max(0, Math.min(F.length - 1, i + d)));
  }

  // --- drawing -------------------------------------------------------------------------------------------------------
  const traceViews = new WeakMap();  // a point's world → a second instance of the view fed its messages (a trace)
  function traceList() {
    const n = E.traces.length;
    return E.traces.filter((s) => s.pt && s.pt.W).map((s, k) => {
      const tl = timeMode === "flight" ? localT(s, E.clock) : localT(E.cur, E.clock);
      const f = frameAt(s.pt.W, tl);
      const tt = f ? f.t : 0;
      let tv = traceViews.get(s.pt.W);
      if (!tv) { tv = kit.newView({ requestRender: () => {} }); traceViews.set(s.pt.W, tv); }
      showAt(tv, s.pt.W, tt);
      s.pt.W.view = tv;  // a view may draw a trace from the trace's own view (design §2.4: W, a decoded world)
      const diff = diffText(A.controls, s.pt.values, E.cur ? E.cur.pt.values : null);
      const label = s.pt.live ? (diff ? `${diff} · ${t("computed live")}` : t("computed live")) : diff;
      return { key: `${s.pt.i}:${s.launchedAt}:${label}`, label, live: !!s.pt.live, W: s.pt.W, t: tt, alpha: 0.6 * (k + 1) / (n + 1) };
    });
  }
  function render() {
    const c = E.cur;
    if (!c || !c.pt || !c.pt.W) return;
    const W = c.pt.W, F = W.frames;
    const tl = timeMode === "none" ? c.pt.tEnd : localT(c, E.clock);
    const i = frameIndexAt(F, tl), f = F[i] || null;
    const tt = f ? f.t : 0;
    const traces = maxTraces ? traceList() : [];
    const tsig = traces.map((x) => `${x.key}@${x.t}`).join("|");
    if (tsig !== E.tracesSig && view.setTraces) { E.tracesSig = tsig; view.setTraces(traces); }
    showAt(view, W, tt);
    kit.self.frame = f;
    if (f) { try { view.render(f.meta, f.t, f.blobs); } catch (e) { console.error(e); } }
    // modified physics: the shown point's own declaration (its header's modifications), at the controls and in the bar
    const mods = W.header.modifications || [];
    const val = (v) => (typeof v === "number" ? num(v) : t(v));
    modBox.hidden = !mods.length;
    if (mods.length) modBox.textContent = t("MODIFIED PHYSICS:") + " " + mods.map((m) => t("{label}: {value} (accepted: {standard})", { label: t(m.label), value: val(m.value), standard: val(m.standard) })).join("; ");
    for (const [j, r] of ctls.entries()) r.el.classList.toggle("dm-law", !!A.controls[j].law && mods.length > 0);
    document.body.classList.toggle("dm-modified", mods.length > 0);
    // readouts
    const ms = (W.header.measurables || []).filter((m) => (spec.readouts || []).includes(m.id));
    const meas = (f && f.meta.meas) || {};
    fill(readBox, ms.map((m) => el("div", { class: "dm-readout", "data-readout": m.id }, el("span", {}, t(m.label)),
      el("b", { class: "mono" }, meas[m.id] === null || meas[m.id] === undefined ? "—"
        : `${readoutText(meas[m.id])}${m.unit ? "\u00a0" + t(m.unit) : ""}`))));
    if (bar) {
      const launched = c.launchedAt !== null;
      bar.update({ playing: E.playing, i: Math.max(0, i), max: Math.max(0, F.length - 1),
        text: `${secs(tt)} / ${secs(c.pt.tEnd)}`, canPlay: !E.refused, why: E.refused || "",
        launch: timeMode === "flight" && (!launched || ended(c, E.clock)) });
    }
  }

  const API = {
    tick(now) {
      if (E.playing) {
        const dt = Math.min(0.25, (now - E.wall) / 1000);
        E.wall = now;
        E.clock += dt * E.rate;
        if (timeMode === "flight" ? !flying() : ended(E.cur, E.clock)) E.playing = false;  // flight: until every shot has landed
        this.dirty = true;
      } else E.wall = now;
      if (this.dirty) { this.dirty = false; render(); }
    },
    show() { this.dirty = true; },
    hide() { E.playing = false; },
    key(e) {
      if (e.key === " ") { e.preventDefault(); playPressed(); }
      else if (e.key === "ArrowRight") { e.preventDefault(); stepFrame(+1); }
      else if (e.key === "ArrowLeft") { e.preventDefault(); stepFrame(-1); }
      else if (e.key === "Home") { e.preventDefault(); resetPressed(); }
    },
    jumpTo(tt) { if (E.cur && E.cur.pt.W) scrub(frameIndexAt(E.cur.pt.W.frames, tt)); },
    drawerKey() {
      const c = E.cur, W = c && c.pt.W;
      if (!W) return "none";
      const tt = (frameAt(W, timeMode === "none" ? c.pt.tEnd : localT(c, E.clock)) || {}).t ?? 0;
      let n = 0;
      for (const vs of W.checks.values()) for (const x of vs) if ((x.t ?? 0) <= tt) n++;
      return `${c.pt.i}|${c.pt.live}|${c.pt.key}|${n}|${W.events.filter((e) => (e.t ?? 0) <= tt).length}`;
    },
    drawer() {
      const c = E.cur, pt = c && c.pt, W = pt && pt.W;
      const tt = W ? (frameAt(W, timeMode === "none" ? pt.tEnd : localT(c, E.clock)) || {}).t ?? 0 : 0;
      const m = A.manifest;
      // a live point's passport is its own (integrator D13): its key, the code that computed it and when, and where the
      // server took it from; an atlas point's is the atlas's
      let passport, note;
      if (pt && pt.live) {
        passport = [[t("Point"), valuesText(A.controls, pt.values)], [t("Point's key"), pt.key || "—"], [t("Code"), pt.code || "—"],
          [t("Random seed"), pt.seed ?? m.seed], [t("Computed"), when(pt.made)], [t("Atlas"), m.atlas]];
        note = pt.source === "cache" ? t("Computed live on this server earlier, at {at}, and taken from its cache.", { at: when(pt.made) })
          : pt.source === "atlas" ? t("This value is on the atlas's grid: the server gave the atlas's point, computed when the atlas was built ({at}).", { at: when(pt.made) })
          : t("Computed live on this server at {at}.", { at: when(pt.made) });
      } else {
        passport = [[t("Point"), pt ? valuesText(A.controls, pt.values) : "—"], [t("Point's index"), pt && pt.i !== null ? `${pt.i} / ${m.points.length}` : "—"],
          [t("Atlas"), `${m.atlas} · ${t("key")} ${m.key}`], [t("Code"), m.code_hash], [t("Random seed"), pt && pt.seed ? pt.seed : m.seed],
          [t("The atlas was built"), when((A.entry || {}).made ?? m.made)]];
        if (src.fromSite) passport.push([t("From"), t("the public site")]);
        note = t("Computed by the engine when the site was built: every slider position is such a point; nothing between them is drawn.");
      }
      return kit.howWeKnow({ W, tt, passport, note });
    },
    liveBody() { return { preset: m0().preset, params: { ...(m0().fixed || {}), ...E.values } }; },
    get state() { return E; },
  };
  const m0 = () => A.manifest;
  window.__lfExplore = window.__lfExplore || {};
  window.__lfExplore[spec.id] = { atlas: A, state: E, values: () => ({ ...E.values }), point: () => (E.cur ? E.cur.pt : null) };
  // the first point: the defaults
  const first = await load(E.values);
  if (first && first.state === "computed") setPoint(first);
  else if (first) showRefusal(t(first.refusal));
  return API;
}
