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
import { isT, lang, sci, t } from "./i18n.js";
import { frameAt, frameIndexAt, showAt } from "./record_core.js";
import { el, fill, fmt, num, time } from "./ui.js";

export const SLOW = 0.25;  // the «slow» speed: a quarter of the screen's speed
// a time of the world on the time bar, in seconds (school: «0.45 s», never «451.6 ms»)
export const secs = (x) => `${fmt(x, ".2f")}\u00a0${t("s")}`;

// --- the screen's time scale (EX2 §5 F1) ------------------------------------------------------------------------------
// world seconds per played second of a screen or a step at normal speed: its `speed`, or "world" (the point's own
// default speed, from its state message: atlas.js keeps it as pt.speed), or 1 (a screen that declares none: real time)
export function speedOf(spec, pt) {
  const sp = spec ? spec.speed : undefined;
  if (typeof sp === "number" && sp > 0) return sp;
  if (sp === "world") return pt && pt.speed > 0 ? pt.speed : 1;
  return 1;
}
// how much slower or faster than real time the world plays (r: world seconds per played second), as Watch says it
// (watch.js rateText, integrator D8): «real time» within 5 %, «slow motion ×120», «sped up ×2.5»
export function factorText(r) {
  if (!(r > 0) || !Number.isFinite(r)) return "";
  if (Math.abs(r - 1) <= 0.05) return t("real time");
  const k = r < 1 ? 1 / r : r;
  // ×2.5, ×120, ×1.2·10⁶: from 10⁶ on in powers of ten (fmt's .2g switches only at 10⁷: W37, a factor of 1 200 000)
  const kk = k < 10 ? fmt(Number(k.toPrecision(2)), "") : k < 1e6 ? fmt(Math.round(k), "") : sci(k, 2);
  return r < 1 ? t("slow motion ×{k}", { k: kk }) : t("sped up ×{k}", { k: kk });
}
// a time of the world in its own unit: the header's units.t_show {unit, s: world seconds per unit} (u34: GM/c³), else
// at school in seconds («0.45 s», never «452 ms»: the EX1 design, review EX1-worlds F8), else seconds on a human scale
// (ns … s: u35's photons, u37's pairs). Watch writes its label with it too (EX2 §5 F12).
export function worldTime(tt, header, school = false) {
  const ts = header && header.units && header.units.t_show;
  if (ts && ts.s > 0 && ts.unit) return `${num(tt / ts.s, 4)}\u00a0${t(ts.unit)}`;
  return school ? secs(tt) : time(tt, 3);
}
// the time bar's label of a screen that declares its speed: «world 1 234 GM/c³ · slow motion ×289 · 3.10 s / 24.00 s»
// (the world's time, the playback factor with normal or slow, the position and the end in played seconds)
export function timeLabel({ tt, tEnd, speed, rate = 1, header = null, school = false }) {
  const f = factorText(speed * rate);
  return [t("world {t}", { t: worldTime(tt, header, school) }), f, `${secs(tt / speed)} / ${secs(tEnd / speed)}`].filter(Boolean).join(" · ");
}

// --- labels and values ------------------------------------------------------------------------------------------------
export function controlLabel(c) {
  const label = t(c.label), unit = c.unit ? t(c.unit) : "";
  return unit && !label.includes(unit) ? t("{label}, {unit}", { label, unit }) : label;
}
export function valueText(c, v) {
  if (c && Array.isArray(c.labels)) {  // a control's own names of its values («air → glass»; EX2 §5 F3)
    const k = c.values.findIndex((x) => x === v);
    if (k >= 0 && c.labels[k]) return t(c.labels[k]);
  }
  return rawValueText(v);
}
// a set-up value without a name of its own: a boolean «on» / «off», a number in the viewer's format, a T in the
// viewer's language, any other value (a select's) as it is. A select's raw value is never looked up as a msgid (review
// R2-P F9, STATUS V53 (v)): u35's polarisation "s" became «с», the msgid of seconds; a world names a select's values
// with its control's `labels`
export function rawValueText(v) {
  if (typeof v === "boolean") return v ? t("on") : t("off");
  if (typeof v === "number") return fmt(v, ".4g");
  if (isT(v)) return t(v);
  return v === null || v === undefined ? "—" : String(v);
}
// a value with its control's unit («1 m», «30°»: no space before the degree sign)
export function valueUnitText(c, v) {
  const u = c.unit ? t(c.unit) : "";
  const named = c && Array.isArray(c.labels) && c.labels[c.values.findIndex((x) => x === v)];
  return `${valueText(c, v)}${typeof v === "number" && u && !named ? (u === "°" ? u : "\u00a0" + u) : ""}`;
}
// a compound control's grid value as the parameters it sets ({param: value}); a plain control's own value
export function expandValues(controls, values) {
  const out = { ...values };
  for (const c of controls || []) {
    if (!c.sets || !(c.param in out)) continue;
    const k = c.values.findIndex((x) => x === out[c.param]);
    delete out[c.param];
    if (k < 0) continue;
    for (const [p, list] of Object.entries(c.sets)) out[p] = list[k];
  }
  return out;
}
// the parameters a compound control set, in words («a 0°, b 22.5°, a′ 45°, b′ 67.5°»), with the schema's labels and units
export function setsText(c, v, params = []) {
  const k = c.values.findIndex((x) => x === v);
  if (!c.sets || k < 0) return "";
  return Object.entries(c.sets).map(([p, list]) => {
    const d = params.find((x) => x.id === p) || { label: p, unit: "" };
    const opt = (d.options || []).find((o) => o.value === list[k]);
    return `${t(d.label)} ${opt ? t(opt.label) : valueUnitText({ unit: d.unit }, list[k])}`;
  }).join(", ");
}
// a short label of a point's values («h 1 m, angle 30°»), for the passport; with the schema's `params`, a compound
// control's value names the parameters it set too («Δ 22.5° (a 0°, b 22.5°, …)»; EX2 §5 F3)
export function valuesText(controls, values, params = null) {
  return controls.map((c) => {
    const base = `${t(c.label)} ${valueUnitText(c, values[c.param])}`;
    return params && c.sets ? `${base} (${setsText(c, values[c.param], params)})` : base;
  }).join(", ");
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
export function readoutText(v, digits = 4) {
  if (!Number.isFinite(v)) return "—";
  const d = v === 0 ? digits - 1 : Math.max(0, Math.min(8, digits - 1 - Math.floor(Math.log10(Math.abs(v)))));
  return fmt(v, `.${d}f`);
}
// the decimals a value with an error is written to: the error's two significant digits, counted after the error is
// rounded to them (0.0996 is «0.10», not «0.100»; review R2-P nits); negative for an error of 100 or more (1234 → «1200»)
export function errDecimals(e) {
  const r = Number(e.toPrecision(2));
  return Math.min(12, 1 - Math.floor(Math.log10(r)));
}
// a value and its error written to the same decimals n (errDecimals); n < 0 rounds both to 10^−n («12300 ± 1200»)
export function pmText(v, e, n = errDecimals(e)) {
  if (n >= 0) return [fmt(v, `.${n}f`), fmt(e, `.${n}f`)];
  const q = 10 ** -n, r = (x) => Math.round(x / q) * q;
  return [fmt(r(v), ".0f"), fmt(r(e), ".0f")];
}
// A readout of a measurable as its declaration says (EX2 §5 F7): {id, label, unit, sigma?, ref?, ref_label?}; sigma
// and ref name other measurables of the same frame. «S 2.864 ± 0.040 (law 2.828)», «advance per orbit 52.155°
// (formula 52.155°)»: with an error, the value and the reference to the error's two digits; with a reference only, both
// to 5 significant digits; a whole number without a unit, an error or a reference is a count («6»); else 4 significant
// digits («23.90 m»). Returns {value, ref} texts (null: not reached).
export function measText(m, meas) {
  const v = meas[m.id];
  if (v === null || v === undefined || !Number.isFinite(v)) return { value: null, ref: null };
  const u = m.unit ? t(m.unit) : "";
  const unit = (x) => (!u ? x : u === "°" ? x + u : `${x}\u00a0${u}`);
  const e = m.sigma ? meas[m.sigma] : null, r = m.ref ? meas[m.ref] : null;
  const hasE = e !== null && e !== undefined && Number.isFinite(e) && e > 0;
  const hasR = r !== null && r !== undefined && Number.isFinite(r);
  let value, ref = null;
  if (hasE) {
    const d = errDecimals(e), [vs, es] = pmText(v, e, d);
    value = unit(`${vs} ± ${es}`);
    if (hasR) ref = unit(pmText(r, e, d)[0]);
  } else if (Number.isInteger(v) && !u && !m.sigma && !m.ref) {
    value = fmt(v, "d");  // a count («6», not «6.000»): a whole number without a unit, an error or a reference
  } else {
    value = unit(readoutText(v, hasR ? 5 : 4));
    if (hasR) ref = unit(readoutText(r, 5));
  }
  return { value, ref: hasR ? t("({label} {value})", { label: m.ref_label ? t(m.ref_label) : t("reference"), value: ref }) : null };
}
// «CSV of this point» (EX2 §5 F7; ui "standard"): one row per frame up to the time shown, t and every declared
// measurable (not those that serve as another's sigma, which are its «σ» column), built from the decoded point
// A CSV's format in the viewer's language (review R2-P F18): a spreadsheet opens a CSV with its locale's list separator
// and decimal sign, so a Russian one (Excel, LibreOffice in a Russian locale: «;» and «,») gets «;» between the fields
// and the decimal comma, an English one «,» and «.»; every CSV starts with the UTF-8 byte order mark, without which
// Excel reads it in the system's 8-bit code page and the headers' «σ», «²» and Cyrillic come out garbled
export const csvFormat = (code = lang()) => (code === "ru" ? { sep: ";", dec: "," } : { sep: ",", dec: "." });
// «CSV of this point» in that format
export function pointCsv(W, tt, measurables, label = (m) => m.id, tHead = "t, s", { sep = ",", dec = "." } = {}) {
  const ms = measurables || [];
  const sig = new Set(ms.map((m) => m.sigma).filter(Boolean));
  const cols = ms.filter((m) => !sig.has(m.id));
  const q = (x) => (x.includes('"') || x.includes("\n") || x.includes(sep) ? `"${x.replace(/"/g, '""')}"` : x);
  const head = [tHead, ...cols.flatMap((m) => (m.sigma ? [label(m), "σ " + label(m)] : [label(m)]))].map(q);
  const num = (x) => (dec === "." ? String(x) : String(x).replace(".", dec));
  const cell = (x) => (x === null || x === undefined || (typeof x === "number" && !Number.isFinite(x)) ? "" : typeof x === "number" ? num(x) : q(String(x)));
  const eps = 1e-12 * Math.abs(tt);
  const lines = (W ? W.frames : []).filter((f) => f.t <= tt + eps).map((f) => {
    const meas = (f.meta && f.meta.meas) || {};
    return [num(f.t), ...cols.flatMap((m) => (m.sigma ? [cell(meas[m.id]), cell(meas[m.sigma])] : [cell(meas[m.id])]))].join(sep);
  });
  return [head.join(sep), ...lines].join("\n") + "\n";
}

// Which detents of a slider carry their value as a label: texts[i] at pos[i] (per cent of the detents' row). Labels never
// collide (EX2, W35: a dense or uneven grid gave «4042» for 40° and 42° and «885» for 80° and 85°): every k-th detent with
// the smallest k from 1 (more than 12 detents: from ⌈n/10⌉) at which no two labels overlap; the last detent always, the
// labelled one before it dropped when they would overlap. A label's width is estimated from its characters at the
// detents' font (12 px on a wide screen in a 290 px row; 14 px in a phone's wider row scale alike). Returns booleans.
export function detentLabels(texts, pos, { rowPx = 290, charPx = 7, padPx = 6, sepPx = 4 } = {}) {
  const n = texts.length;
  if (!n) return [];
  const w = (i) => String(texts[i]).length * charPx + padPx;
  const fits = (a, b) => ((pos[b] - pos[a]) / 100) * rowPx >= (w(a) + w(b)) / 2 + sepPx;
  for (let k = n <= 12 ? 1 : Math.ceil(n / 10); k < Math.max(n, 2); k++) {
    const on = texts.map((_, i) => i % k === 0 || i === n - 1);
    const prev = Math.floor((n - 2) / k) * k;  // the labelled detent before the last
    if (prev > 0 && !fits(prev, n - 1)) on[prev] = false;
    const idx = on.flatMap((x, i) => (x ? [i] : []));
    if (idx.every((i, j) => j === 0 || fits(idx[j - 1], i))) return on;
  }
  return texts.map((_, i) => i === 0 || (i === n - 1 && n > 1 && fits(0, n - 1)));
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
  // on a server the slider moves in fine steps for a pointer only: the arrows, PageUp / PageDown, Home and End go to the
  // previous or next detent (review R2-P F2: a fine step of 1/20 of the smallest gap snapped back to the same detent, so
  // the keys never moved the slider)
  if (fine) input.addEventListener("keydown", (e) => {
    const up = ["ArrowRight", "ArrowUp", "PageUp"].includes(e.key), down = ["ArrowLeft", "ArrowDown", "PageDown"].includes(e.key);
    if (!up && !down && e.key !== "Home" && e.key !== "End") return;
    e.preventDefault();
    const x = cur ?? valueOf(), eps = 1e-12 * Math.max(1, Math.abs(x));
    const v = e.key === "Home" ? lo : e.key === "End" ? hi : up ? vals.find((d) => d > x + eps) : [...vals].reverse().find((d) => d < x - eps);
    if (v === undefined || v === x) return;
    input.value = String(v); out.textContent = valueText(c, v); valueSay(v); out.classList.toggle("dm-off-grid", false);
    onPick(v, { final: true });
  });
  // the detents: a tap on one chooses it (touch: the thumb need not be dragged). Out of the tab order: the slider is the
  // keyboard's way (review EX1-screens F10); their hit area is 44 px high and as wide as the gap to the neighbours (F15),
  // never wider (demo.css: a dense grid's labelled detent does not cover its neighbour); labels never collide (detentLabels)
  const pos = (v, i) => 100 * (fine ? (v - lo) / (hi - lo || 1) : i / Math.max(1, vals.length - 1));
  const labelled = detentLabels(vals.map((v) => valueText(c, v)), vals.map(pos));
  // the detents are a pointer's shortcut: hidden from a screen reader, which has the slider and its value (review R2-P:
  // 38 buttons of u35's θ read in browse mode)
  const ticks = el("div", { class: "dm-detents", "aria-hidden": "true" }, vals.map((v, i) => {
    const gapPct = Math.min(i > 0 ? pos(v, i) - pos(vals[i - 1], i - 1) : Infinity, i < vals.length - 1 ? pos(vals[i + 1], i + 1) - pos(v, i) : Infinity);
    const b = el("button", {
      class: "dm-detent", tabindex: "-1", "aria-pressed": "false", style: { left: `${pos(v, i).toFixed(3)}%` },
      title: valueText(c, v), "aria-label": valueUnitText(c, v), onclick: () => onPick(v, { final: true }) },
    labelled[i] ? valueText(c, v) : "");
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
  // a scrub to a frame keeps that frame's own time while the clock stays where the scrub put it: (L + t) − L can fall an
  // ulp of a large clock short of t, before the frame asked for (X-F, COORD 2026-11-19)
  if (shot.pin && shot.pin.clock === clock && shot.pin.at === shot.launchedAt) return shot.pin.t;
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
    sig: "", tracesSig: "", refused: null, seq: 0, live: null, readSig: "" };
  const view = kit.newView();
  const stage = el("div", { class: "dm-stage" }, view.center);
  const refusedBox = el("div", { class: "dm-refusal", role: "status", hidden: true });
  const loadingBox = el("div", { class: "dm-loading", hidden: true }, t("loading…"));
  stage.append(el("div", { class: "dm-stage-note" }, refusedBox));
  // readouts: the measurables the world declares in its header, shown once the time has reached them («—» before)
  const readBox = el("div", { class: "dm-readouts" });
  const params = ((kit.viz && kit.viz.schema) || {}).params || [];  // the schema's labels: a compound control's sets
  const ctls = A.controls.map((c) => {
    // a compound control takes its grid values only, on a server too (EX2 §5 F3: it sets several parameters at once)
    const r = controlRow(c, E.values[c.param], (v) => pick(c, v), { server: kit.server && !c.sets });
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
  // «CSV of this point» (ui "standard"; EX2 §5 F7): the shown point's series up to the time shown, from the decoded point
  const csvBtn = kit.ui === "standard" ? el("a", { class: "button dm-point-csv", download: `${kit.world}_${spec.id}_point.csv`,
    title: t("This point's measurables, one row per frame up to the time shown, with their errors, as CSV"),
    onclick: (e) => { const h = pointCsvHref(); if (!h) { e.preventDefault(); return; } e.currentTarget.href = h; } }, t("⤓ CSV of this point")) : null;
  // a law control (standard worlds only; never at school, registry) changes the physics: flagged as the live player does
  const modBox = el("div", { class: "dm-mod", hidden: true });
  const side = el("div", { class: "dm-side" }, modBox,
    el("div", { class: "dm-ctls" }, ctls.map((r) => r.el)), loadingBox,
    el("div", { class: "dm-refusal-side", role: "status" }),
    ovBox, readBox, el("div", { class: "row" }, clearBtn, anotherBtn, csvBtn));
  const sideRefusal = side.querySelector(".dm-refusal-side");
  const bar = timeMode === "none" ? null : kit.transport({
    launchLabel: timeMode === "flight" ? t("▶ Launch") : "▶",
    play: () => playPressed(), reset: () => resetPressed(), scrub: (i) => scrub(i), rate: (r) => { E.rate = r === 1 ? 1 : SLOW; kit.dirty(); },
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
  // «Another sample» (a server, time "buildup"): the same set-up with the next seed. Its reply is shown only when it is
  // still the one asked for, as load() does (review R2-P F3: a late reply replaced a later pick of the slider)
  async function another() {
    const seq = ++E.seq, vals = { ...E.values };
    E.seed = (E.seed ?? A.manifest.seed ?? 1) + 1;
    const slow = setTimeout(() => { if (seq === E.seq) loadingBox.hidden = false; }, 300);
    let pt = null;
    try { pt = await A.live(vals, E.seed); } catch (e) {
      if (seq === E.seq) showRefusal(t("This point could not be loaded: {why}", { why: e.message }));
      return;
    } finally { clearTimeout(slow); if (seq === E.seq) loadingBox.hidden = true; }
    if (seq !== E.seq) return;  // a newer choice came first
    if (pt && pt.state === "computed") { showRefusal(null); setPoint(pt); }
    else if (pt && pt.state === "refused") showRefusal(t(pt.refusal));
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
    c.pin = { clock: E.clock, at: c.launchedAt, t: f.t };
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
    const val = (v) => (typeof v === "number" ? num(v) : rawValueText(v));
    modBox.hidden = !mods.length;
    if (mods.length) modBox.textContent = t("MODIFIED PHYSICS:") + " " + mods.map((m) => t("{label}: {value} (accepted: {standard})", { label: t(m.label), value: val(m.value), standard: val(m.standard) })).join("; ");
    for (const [j, r] of ctls.entries()) r.el.classList.toggle("dm-law", !!A.controls[j].law && mods.length > 0);
    document.body.classList.toggle("dm-modified", mods.length > 0);
    // readouts: each with its error and its reference when the world declares them (EX2 §5 F7)
    const ms = (W.header.measurables || []).filter((m) => (spec.readouts || []).includes(m.id));
    const meas = (f && f.meta.meas) || {};
    const rsig = JSON.stringify(ms.map((m) => [m.id, meas[m.id], m.sigma ? meas[m.sigma] : null, m.ref ? meas[m.ref] : null]));
    if (rsig !== E.readSig) {
      E.readSig = rsig;
      fill(readBox, ms.map((m) => {
        const x = measText(m, meas);
        return el("div", { class: "dm-readout", "data-readout": m.id }, el("span", {}, t(m.label)),
          el("span", { class: "dm-rv" }, el("b", { class: "mono" }, x.value === null ? "—" : x.value), x.ref ? el("span", { class: "mono dm-ref" }, x.ref) : null));
      }));
    }
    const speed = speedOf(spec, c.pt);
    kit.self.rate = speed * E.rate;  // the view's ctx.speed(): world seconds per played second
    if (bar) {
      const launched = c.launchedAt !== null;
      const declared = spec.speed !== undefined && spec.speed !== null;
      bar.update({ playing: E.playing, i: Math.max(0, i), max: Math.max(0, F.length - 1),
        text: declared ? timeLabel({ tt, tEnd: c.pt.tEnd, speed, rate: E.rate, header: W.header, school: !!kit.school }) : `${secs(tt)} / ${secs(c.pt.tEnd)}`,
        title: declared ? t("The world's own time, how much slower or faster than real time it plays, and the position in the point") : "",
        canPlay: !E.refused, why: E.refused || "",
        launch: timeMode === "flight" && (!launched || ended(c, E.clock)) });
    }
  }
  function pointCsvHref() {
    const c = E.cur, W = c && c.pt && c.pt.W;
    if (!W) return null;
    const tt = (frameAt(W, timeMode === "none" ? c.pt.tEnd : localT(c, E.clock)) || {}).t ?? 0;
    const lab = (m) => (m.unit ? `${t(m.label)}, ${t(m.unit)}` : t(m.label));
    const text = pointCsv(W, tt, W.header.measurables || [], lab, t("t, {unit}", { unit: t("s") }), csvFormat());
    return "data:text/csv;charset=utf-8," + encodeURIComponent("\ufeff" + text);  // the BOM: Excel reads it as UTF-8
  }

  const API = {
    tick(now) {
      if (E.playing) {
        const dt = Math.min(0.25, (now - E.wall) / 1000);
        E.wall = now;
        E.clock += dt * E.rate * speedOf(spec, E.cur && E.cur.pt);  // world seconds: the screen's speed × normal or slow (EX2 §5 F1)
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
        passport = [[t("Point"), valuesText(A.controls, pt.values, params)], [t("Point's key"), pt.key || "—"], [t("Code"), pt.code || "—"],
          [t("Random seed"), pt.seed ?? m.seed], [t("Computed"), when(pt.made)], [t("Atlas"), m.atlas]];
        note = pt.source === "cache" ? t("Computed live on this server earlier, at {at}, and taken from its cache.", { at: when(pt.made) })
          : pt.source === "atlas" ? t("This value is on the atlas's grid: the server gave the atlas's point, computed when the atlas was built ({at}).", { at: when(pt.made) })
          : t("Computed live on this server at {at}.", { at: when(pt.made) });
      } else {
        passport = [[t("Point"), pt ? valuesText(A.controls, pt.values, params) : "—"], [t("Point's index"), pt && pt.i !== null ? `${pt.i} / ${m.points.length}` : "—"],
          [t("Atlas"), `${m.atlas} · ${t("key")} ${m.key}`], [t("Code"), m.code_hash], [t("Random seed"), pt && pt.seed ? pt.seed : m.seed],
          [t("The atlas was built"), when((A.entry || {}).made ?? m.made)]];
        if (src.fromSite) passport.push([t("From"), t("the public site")]);
        note = t("Computed by the engine when the site was built: every slider position is such a point; nothing between them is drawn.");
      }
      return kit.howWeKnow({ W, tt, passport, note });
    },
    liveBody() { return { preset: m0().preset, params: { ...(m0().fixed || {}), ...expandValues(A.controls, E.values) } }; },
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
