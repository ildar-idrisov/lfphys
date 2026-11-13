// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// u43 view: an optical vortex in the shared 3-D environment (/static/js/env3d.js): the helical surfaces of equal phase
// (one mesh per phase of the slowed optical period, revealed by the run as its time reaches it; a frame names the phase
// it shows), the intensity as a volume, the energy flow lines, the generator, the rotating element turned by the
// matrix each frame carries, the detector; slice planes with intensity and phase. Panels: the beam, the angular
// momentum per photon (measured against the closed forms: per unit length in the canonical split and Barnett's split
// of the flux through the plane), the detector's samples and the spectrum of the last
// measurement. Drawing only: every number and every surface comes from the run.
import { el, fill, num, panel, css, fresh2d } from "/static/js/ui.js";
import { t, fmt, lang } from "/static/js/i18n.js";
import { createEnv3D } from "/static/js/env3d.js";

export function createView(ctx) {
  const env = createEnv3D(ctx, { scale: "sqrt" });
  const beamBox = el("div", { class: "kv" }), amBox = el("div", {}), timeBox = el("div", { class: "kv" });
  const detText = el("div", { class: "kv" });
  const cvTrace = el("canvas", { style: { width: "100%", height: "120px", display: "block" } });
  const cvSpec = el("canvas", { style: { width: "100%", height: "120px", display: "block" } });
  const rightPanels = [panel(t("Beam"), beamBox), panel(t("Angular momentum per photon"), amBox),
                       panel(t("Rotation and detector"), el("div", {}, detText, cvTrace, cvSpec)),
                       panel(t("Time and phase"), timeBox),
                       panel(t("Scene layers"), env.layersPanel), panel(t("Slice: position and tilt"), env.planePanel)];
  let H = null, am = null, beat = null, helix = new Map(), want = 0, shownBin = -1, lastFrame = null;
  let trace = { ts: [], v: [], n: 0 };
  for (const cv of [cvTrace, cvSpec]) new ResizeObserver(() => drawDetector()).observe(cv);

  // --- the equiphase sheets of the phase a frame names ------------------------------------------------------------
  function nearest(k) {  // the phase k, or the last one revealed before it (never a later one)
    if (helix.has(k)) return k;
    let best = -1;
    for (const b of helix.keys()) if (b <= k && b > best) best = b;
    return best;
  }
  function showBin(force = false) {
    const k = nearest(want);
    if (k < 0) { if (shownBin >= 0) env.scene.removeLayer("helix"); shownBin = -1; return; }
    if (!force && k === shownBin) return;
    const h = helix.get(k);
    env.scene.setMesh("helix", h.blobs.pos, h.blobs.idx, h.blobs.rgb, { label: t(h.meta.label), opacity: 0.62 });
    shownBin = k;
  }
  function placeRotor(f) {
    const b = H && H.beam;
    if (!b || b.z_rot === null || b.z_rot === undefined) return;
    const A = f && f.rotA ? f.rotA : [1, 0, 0, 0, 1, 0, 0, 0, 1];
    env.scene.transformMesh("rotor", A, [0, 0, b.z_rot]);
  }

  // --- panels --------------------------------------------------------------------------------------------------------
  function drawBeam() {
    if (!H) return;
    const b = H.beam || {};
    if (b.model === "fork") {
      const kind = { amplitude: t("amplitude (1 + cos)/2"), binary: t("binary amplitude"), blazed: t("blazed phase (all into the 1st order)") }[b.kind] || b.kind;
      fill(beamBox, el("span", {}, t("source")), el("span", {}, t("a Gaussian beam on a “fork” hologram")),
        el("span", {}, t("charge l, hologram")), el("span", { class: "mono" }, t("{l:d}, {kind}", { l: b.l, kind })),
        el("span", {}, t("period Λ, w0, λ")), el("span", { class: "mono" }, t("{P:.4g}, {w:.4g}, {lam:.4g} µm", { P: b.period, w: b.w0, lam: b.lam })),
        el("span", {}, t("depth of the region")), el("span", { class: "mono" }, t("{z:.4g} µm", { z: b.z_end })),
        el("span", {}, t("what to look at")), el("span", {}, t("the order m leaves at the angle sin θ = −mλ/Λ (the order +1 towards negative x) and carries the charge m·l; the power fractions of the orders are in the checks")));
      return;
    }
    const pol = { "+1": t("circular σ = +1"), "-1": t("circular σ = −1"), lin: t("linear (x): σ̄ = 0") }[b.pol] || b.pol;
    fill(beamBox,
      el("span", {}, t("source")), el("span", {}, b.gen === "mode" ? t("an LG mode, p = {p}, l = {l}", { p: b.p, l: b.l }) : t("a Gaussian beam behind a spiral plate, l = {l}", { l: b.l })),
      el("span", {}, t("model")), el("span", { class: b.model === "exact" ? "" : "st-bad" }, b.model === "exact" ? t("exact: a vector solution of Maxwell's equations") : t("APPROXIMATION: paraxial")),
      el("span", {}, "w0, λ"), el("span", { class: "mono" }, t("{w:.4g} µm, {lam:.4g} µm (w0/λ = {r:.3g})", { w: b.w0, lam: b.lam, r: b.w0 / b.lam })),
      el("span", {}, t("z_R, divergence")), el("span", { class: "mono" }, t("{zr:.4g} µm, θ = λ/(πw0) = {th:.3g} rad", { zr: b.zr, th: b.theta_div })),
      el("span", {}, t("polarisation")), el("span", {}, pol),
      b.model === "exact" && b.kept !== undefined ? el("span", {}, t("source in the beam")) : null,
      b.model === "exact" && b.kept !== undefined ? el("span", { class: b.kept < 0.9999 ? "warn" : "mono" }, b.kept < 0.9999
        ? (b.gen === "mode" ? t("{p:.4g} % of the waist's power: the rest is evanescent waves (q > k), which the beam does not have; w0 is the width of the spectrum, not a measured waist", { p: 100 * b.kept })
          : t("{p:.4g} % of the power at z = 0: the rest is evanescent waves of the plate's near field, which die out within a few λ (in the world's header); farther on the beam is exact", { p: 100 * b.kept }))
        : t("all of it (the spectrum beyond q = k is negligible)")) : null,
      el("span", {}, t("helical fronts")), el("span", { class: "mono" }, b.helix_region ? t("z = {a:.4g} … {b:.4g} µm", { a: b.helix_region[0], b: b.helix_region[1] }) : t("none (l = 0: the fronts are not helices)")));
  }
  function drawAm() {
    if (H && H.beam && H.beam.model === "fork") { fill(amBox, el("div", { class: "muted" }, t("For the hologram the angular momentum per photon is not computed: see the charges and the power fractions of the orders in the checks."))); return; }
    if (!am) { fill(amBox, el("div", { class: "muted" }, t("Computing…"))); return; }
    const exact = H && H.beam && H.beam.model === "exact";
    const rows = [[t("L_z (orbital)"), am.L, am.L_ref, "#22b8ff"], [exact ? t("S_z (spin)") : t("S_z (spin, from the model's field)"), am.S, am.S_ref, "#ff8a1f"], ["J_z = L_z + S_z", am.J, am.J_ref, "#9fe870"]];
    const big = Math.max(1, ...rows.map((r) => Math.abs(r[1] ?? 0)), ...rows.map((r) => Math.abs(r[2] ?? 0)));
    const bar = (v, c) => el("div", { style: { position: "relative", height: "8px", background: "rgba(127,127,127,0.15)", margin: "2px 0 6px" } },
      el("div", { style: { position: "absolute", left: v >= 0 ? "50%" : `${50 - 50 * Math.abs(v) / big}%`, width: `${50 * Math.abs(v) / big}%`, top: 0, bottom: 0, background: c } }),
      el("div", { style: { position: "absolute", left: "50%", top: "-2px", bottom: "-2px", width: "1px", background: "#888" } }));
    const zt = am.z !== undefined && am.z !== null ? t("z = {z:.4g} µm", { z: am.z }) : "z_c";
    const vs = (v, r) => t("{v:.7g} ħ (formula {r:.7g})", { v, r });
    fill(amBox,
      el("div", { class: "muted" }, t("per unit length, the canonical split (Bliokh et al. 2010), the plane {z}", { z: zt })),
      rows.map(([lab, v, r, c]) => el("div", {}, el("div", { class: "kv" }, el("span", {}, lab),
        el("span", { class: "mono" }, vs(v, r))), bar(v ?? 0, c))),
      el("div", { class: "kv" },
        exact ? el("span", {}, t("⟨cos θ⟩ of the spectrum")) : null, exact ? el("span", { class: "mono" }, num(am.cos, 6)) : null,
        exact ? el("span", {}, t("angular momentum flux / energy flux × ω")) : null, exact ? el("span", { class: "mono" }, `${num(am.flux_J, 7)} ħ`) : null,
        exact ? el("span", {}, t("by the flux (Barnett): spin")) : null, exact ? el("span", { class: "mono" }, vs(am.S_flux, am.S_flux_ref)) : null,
        exact ? el("span", {}, t("by the flux (Barnett): orbit")) : null, exact ? el("span", { class: "mono" }, vs(am.L_flux, am.L_flux_ref)) : null,
        exact ? el("span", {}, t("by Poynting ∫(r×P)_z")) : null, exact ? el("span", { class: "mono" }, vs(am.J_poynting, am.J_poynting_ref)) : null,
        exact && am.ez !== undefined ? el("span", {}, t("longitudinal field |E_z|/|E|")) : null, exact && am.ez !== undefined ? el("span", { class: "mono" }, num(am.ez, 4)) : null),
      el("div", { class: "help" }, exact
        ? t("The exact beam: every plane wave has the helicity σ, and the total angular momentum per photon is exactly J_z = l + σ. How to divide it into spin and orbit is a matter of definition. In the canonical split per unit length (the upper rows) the spin S_z = σ⟨cos θ⟩ is smaller than 1 in magnitude, and the orbital L_z = l + σ(1 − ⟨cos θ⟩) is shifted from l towards σ. In Barnett's split of the flux through the plane (Monteiro et al. 2009) the spin σ⟨(1 + cos²θ)/2⟩/⟨cos θ⟩ is larger than 1 in magnitude: a shift the other way. Only J_z does not depend on the definition. Measured from the field on the plane {z} (Berry densities).", { z: zt })
        : t("The paraxial model: the polarisation is uniform, so the spin is S_z = σ̄ (computed from the model's field, but that is how the model is built); L_z is measured from the phase of the field and equals l. The plane {z}. The exact model shows the splitting.", { z: zt })));
  }
  function drawTime(f) {
    if (!H) return;
    const T = H.t_show, lam = (H.beam && H.beam.lam) || 1;
    const Topt = lam * 1e-6 / 299792458;
    const k = f ? f.bin : 0, have = f ? f.revealed : helix.size;
    fill(timeBox,
      el("span", {}, t("optical phase")), el("span", {}, t("shown slowed: 1 period per {ms:.4g} ms of the world (in reality {fs:.4g} fs, slowed ×{x:.3g})", { ms: T * 1e3, fs: Topt * 1e15, x: T / Topt })),
      el("span", {}, t("phase in the picture")), el("span", { class: "mono" }, helix.size || have ? t("{k} of {n}", { k: k + 1, n: H.nb }) : "—"),
      el("span", {}, t("phases revealed")), el("span", { class: have < H.nb ? "warn" : "muted" }, helix.size === 0 && !have ? t("no helical fronts in this world") : have < H.nb ? t("{k}: the rest when the time reaches them", { k: have }) : t("all: from now on the fronts repeat")),
      f && f.f_rot !== undefined ? el("span", {}, t("the element has turned by")) : null,
      f && f.f_rot !== undefined ? el("span", { class: "mono" }, t("{a:.4g}° (f = {f:.4g} Hz)", { a: (f.angle * 180 / Math.PI) % 360, f: f.f_rot })) : null,
      f && f.f_rot !== undefined ? el("span", {}, t("two time scales")) : null,
      f && f.f_rot !== undefined ? el("span", { class: "muted" }, t("the element turns in the world's real time, the optical phase is slowed: the mutual turning of the helices and the element on the screen is not the measured shift (that one counts from the true frequency of the light)")) : null);
  }
  function sizeCanvas(cv) {
    const dpr = Math.min(window.devicePixelRatio || 1, 2), W = cv.clientWidth, Hh = cv.clientHeight;
    if (!W || !Hh) return null;
    if (cv.width !== Math.round(W * dpr)) { cv.width = Math.round(W * dpr); cv.height = Math.round(Hh * dpr); }
    const g = fresh2d(cv.getContext("2d"), dpr);
    g.fillStyle = css("--canvas") || "#0b0e14"; g.fillRect(0, 0, W, Hh);
    return { g, W, H: Hh };
  }
  function drawDetector() {
    if (!H) return;
    const b = H.beam || {};
    if (!b.rot || b.rot === "none") {
      fill(detText, el("span", {}, t("element")), el("span", { class: "muted" }, t("no rotating element in this world")));
      for (const cv of [cvTrace, cvSpec]) cv.style.display = "none";
      return;
    }
    for (const cv of [cvTrace, cvSpec]) cv.style.display = "block";
    const what = b.rot === "disc" ? t("a rough disc; the detector behind a ±l mode filter") : t("a Dove prism in one arm of an interferometer");
    fill(detText, el("span", {}, t("element")), el("span", {}, what),
      el("span", {}, t("samples taken")), el("span", { class: "mono" }, fmt(trace.n, "d")),
      el("span", {}, t("beat: measured")), el("span", { class: "mono" }, beat ? t("{f:.7g} Hz (measurement {k})", { f: beat.f_meas, k: beat.n }) : t("— (it needs {n} samples: two turns)", { n: 128 })),
      el("span", {}, t("formula 2|l|f")), el("span", { class: "mono" }, beat ? t("{f:.7g} Hz", { f: beat.f_ref }) : "—"),
      el("span", {}, b.rot === "disc" ? t("frequency shift of the light scattered onto the axis") : t("frequency shift of the turned arm (against the arm at rest)")),
      el("span", { class: "mono" }, beat ? t("{f:.6g} Hz (formula {r:.6g})", { f: beat.shift_meas, r: beat.shift_ref }) : "—"));
    // the samples: the last 256
    const c = sizeCanvas(cvTrace);
    if (c && trace.n > 1) {
      const { g, W, H: Hh } = c, n0 = Math.max(0, trace.n - 256), left = 6, right = 6, top = 12, bot = 6;
      let lo = Infinity, hi = -Infinity;
      for (let i = n0; i < trace.n; i++) { lo = Math.min(lo, trace.v[i]); hi = Math.max(hi, trace.v[i]); }
      if (!(hi > lo)) { hi = lo + Math.abs(lo || 1) * 1e-6; }
      const t0 = trace.ts[n0], t1 = trace.ts[trace.n - 1] || t0 + 1;
      const X = (tm) => left + (W - left - right) * (tm - t0) / ((t1 - t0) || 1), Y = (v) => top + (Hh - top - bot) * (1 - (v - lo) / (hi - lo));
      g.strokeStyle = "#9fe870"; g.lineWidth = 1.2; g.beginPath();
      for (let i = n0; i < trace.n; i++) { const x = X(trace.ts[i]), y = Y(trace.v[i]); if (i === n0) g.moveTo(x, y); else g.lineTo(x, y); }
      g.stroke();
      g.fillStyle = css("--muted") || "#999"; g.font = "10px system-ui";
      g.fillText(t("detector signal, the last {n} samples ({ms:.4g} ms)", { n: trace.n - n0, ms: (t1 - t0) * 1e3 }), left, 10);
    }
    const s = sizeCanvas(cvSpec);
    if (s && beat) {
      const { g, W, H: Hh } = s, f = beat.f, P = beat.P, left = 6, right = 6, top = 12, bot = 14;
      const fmax = f[f.length - 1] || 1;
      const X = (x) => left + (W - left - right) * x / fmax, Y = (p) => top + (Hh - top - bot) * (1 - p);
      g.strokeStyle = css("--ink") || "#ddd"; g.lineWidth = 1; g.beginPath();
      for (let i = 0; i < f.length; i++) { const x = X(f[i]), y = Y(P[i]); if (i) g.lineTo(x, y); else g.moveTo(x, y); }
      g.stroke();
      if (beat.f_ref > 0) { g.strokeStyle = "#ff8a1f"; g.setLineDash([4, 3]); g.beginPath(); g.moveTo(X(beat.f_ref), top); g.lineTo(X(beat.f_ref), Hh - bot); g.stroke(); g.setLineDash([]); }
      if (beat.f_meas > 0) { g.strokeStyle = "#9fe870"; g.beginPath(); g.moveTo(X(beat.f_meas), top); g.lineTo(X(beat.f_meas), Hh - bot); g.stroke(); }
      g.fillStyle = css("--muted") || "#999"; g.font = "10px system-ui";
      g.fillText(t("spectrum of the measurement: green, the peak; orange dashed, 2|l|f"), left, 10);
      for (let q = 0; q <= 4; q++) g.fillText(num(fmax * q / 4, 3), X(fmax * q / 4) - (q === 4 ? 24 : 4), Hh - 2);
    }
  }

  return {
    center: env.center, rightPanels,
    help: () => el("div", {}, el("h4", {}, t("Optical vortices")),
      el("p", {}, t("In a beam with the phase e^{ilφ} the surfaces of equal phase are not planes but l intertwined helices with the pitch lλ: in 3-D these are the translucent helical surfaces (the “Surfaces of equal phase” layer). The light on the screen is slowed: one optical period lasts several hundred milliseconds of the world's time, so the helices “rotate” (in fact the front runs along z at the speed of light). The phases of the period are computed by the engine and revealed when the world's time reaches them; after that the fronts repeat.")),
      el("p", {}, t("The volume is the intensity |E|² of the beam (a ring: on the vortex's axis the field is zero). The yellow lines are the energy flow (the Poynting vector), the blue ones the orbital (canonical) current: they twist around the axis like spirals. The slices show the intensity and the phase on a colour wheel (the “phase” mode): a turn around the axis gives l full turns of the colour.")),
      el("p", {}, t("The model: “exact” is a vector solution of Maxwell's equations (a sum of plane waves of helicity σ, only propagating waves: at w0 ≲ λ the part of the source's spectrum beyond q = k is dropped; the world marks this, and if more than {p} % of the power is dropped, it is not built); “paraxial” is a Laguerre–Gauss mode with uniform polarisation (marked as an approximation). At tight focusing (w0 ~ λ) the paraxial picture breaks down: a longitudinal field appears (first order in λ/w0), and the angular momentum divides into spin and orbit differently. How exactly depends on the definition: in the canonical split per unit length the spin S_z = σ⟨cos θ⟩ is smaller than 1 in magnitude, in Barnett's split of the flux larger than 1; the sum J_z = l + σ is one and the same and is conserved exactly (the “Angular momentum per photon” panel).", { p: 10 })),
      el("p", {}, t("Rotation: a rough disc in the beam's path scatters the light; the detector looks through a ±l mode filter (as in Lavery et al., 2013): the part that kept +l is not shifted, the part scattered into −l is shifted by −2lf, so the intensity beats at the frequency 2|l|f; the light scattered onto the axis is shifted by −lf. A Dove prism (Courtial et al., 1998) turns the image twice as fast as itself and changes the sign of l: in an interferometer the power beats at the frequency 2|l|f. The detector collects samples as the time goes on; every two turns the spectrum of the samples gives the measured frequency, which is compared with the formula. The rotation frequency f can be changed on the fly (on the left). The element on the screen turns in the world's real time while the optical phase is slowed: their mutual turning in the picture is not the shift that is measured.")),
      el("p", {}, t("Generators (thin masks, an approximation): a spiral phase plate (its thickness grows with the azimuth) turns a Gaussian beam into a vortex of charge l, not a single LG mode; the scalar field's orbital angular momentum is lħ per photon, the vector field's L_z = l + σ(1 − ⟨cos θ⟩), where ⟨cos θ⟩ is set by the light that the singular point at the centre of an ideal plate sends to large angles; a “fork” hologram gives orders, the m-th carries the charge m·l and leaves towards x < 0 for m > 0."))),
    reset() { env.reset(); H = null; am = null; beat = null; helix = new Map(); want = 0; shownBin = -1; lastFrame = null; trace = { ts: [], v: [], n: 0 }; },
    snapshot() { return { env: env.snapshot(), helix: new Map(helix), am, beat, n: trace.n }; },
    restore(k) {
      env.restore(k.env);
      helix = new Map(k.helix); am = k.am; beat = k.beat; trace.n = k.n;
      showBin(true); placeRotor(lastFrame); drawAm(); drawDetector(); drawTime(lastFrame);
    },
    onHeader(meta) {
      env.onHeader(meta); H = meta; am = null; beat = null; helix = new Map(); want = 0; shownBin = -1; lastFrame = null;
      trace = { ts: [], v: [], n: 0 };
      drawBeam(); drawAm(); drawDetector(); drawTime(null);
    },
    onMessage(meta, blobs) {
      if (meta.type === "helix") { helix.set(meta.bin, { meta, blobs }); if (meta.bin === want || shownBin < 0) showBin(); return; }
      if (meta.type === "trace") {
        for (let i = 0; i < meta.count; i++) { trace.ts[trace.n + i] = blobs.ts[i]; trace.v[trace.n + i] = blobs.v[i]; }
        trace.n += meta.count; return;
      }
      if (meta.type === "beat") { beat = { ...meta, f: blobs.f, P: blobs.P }; drawDetector(); return; }
      if (meta.type === "am") { am = meta; drawAm(); return; }
      if (env.onMessage(meta, blobs)) { if (meta.type === "mesh" && meta.id === "rotor") placeRotor(lastFrame); return; }
    },
    render(meta) {
      if (!H) return;
      if (meta) {
        lastFrame = meta;
        if (meta.bin !== want) { want = meta.bin; showBin(); }
        placeRotor(meta);
        drawTime(meta);
      }
      drawDetector();
      env.scene.requestRender();
    },
  };
}
