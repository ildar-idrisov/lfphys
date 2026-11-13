// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// A camera window of a 3-D world (plan P14.2; first used by u39): the image a run computed for an observer (RGB,
// deflate-compressed), what it shows (the image's mode; a mode that is not what is seen is marked), its time, the
// values under the cursor from the run's per-pixel data (the world's describe(i, j) callback), the angles of the
// camera on its axes, and a PNG export. Drawing only: every number comes from the run.
import { t } from "./i18n.js";
import { el, fill, num, fresh2d } from "./ui.js";

// deflate (zlib) bytes -> ArrayBuffer (the browser's DecompressionStream)
export async function inflate(u8) {
  const stream = new Blob([u8]).stream().pipeThrough(new DecompressionStream("deflate"));
  return await new Response(stream).arrayBuffer();
}

// a field sent as row differences (uint16 modulo 2^16): summed back along each row
export function unsubRows(u16, W) {
  const out = new Uint16Array(u16.length);
  for (let r = 0; r < u16.length / W; r++) {
    let acc = 0;
    for (let i = 0; i < W; i++) { acc = (acc + u16[r * W + i]) & 0xffff; out[r * W + i] = acc; }
  }
  return out;
}

export function createImageWindow({ title = t("What the observer sees"), describe = null, overlay = null } = {}) {
  const head = el("span", { class: "sw-title" }, t(title));
  const png = el("button", { title: t("Save the image (PNG, at the computed resolution)") }, "PNG");
  const cv = el("canvas", { class: "sw-canvas" });
  const status = el("div", { class: "sw-status" }, el("span", { class: "muted" }, t("waiting for the image…")));
  const readout = el("div", { class: "sw-readout mono" }, t("point at the image"));
  const box = el("div", { class: "slicewin imgwin", style: { borderColor: "#7fb7ff", minHeight: "260px" } },
    el("div", { class: "sw-head" }, head, el("span", { class: "grow" }), png), cv, status, readout);
  const root = el("div", { class: "s3d-windows wide" }, box);
  const off = document.createElement("canvas");
  let cur = null, geom = null;

  function draw() {
    const dpr = Math.min(window.devicePixelRatio || 1, 2), Wc = cv.clientWidth, Hc = cv.clientHeight;
    if (!Wc || !Hc) return;
    if (cv.width !== Math.round(Wc * dpr) || cv.height !== Math.round(Hc * dpr)) { cv.width = Math.round(Wc * dpr); cv.height = Math.round(Hc * dpr); }
    const g = fresh2d(cv.getContext("2d"), dpr);
    g.fillStyle = "#0b0e14"; g.fillRect(0, 0, Wc, Hc);
    if (!cur) return;
    const [H, W] = cur.meta.shape, left = 34, right = 6, bot = 26;
    const want = Math.max(160, Math.min(900, Math.round(H * (Wc - left - right) / W) + 4 + bot));  // review B3-14
    if (Math.abs(Hc - want) > 2) { box.style.flex = "0 0 auto"; cv.style.flex = "0 0 auto"; cv.style.height = `${want}px`; return; }
    const sc = Math.min((Wc - left - right) / W, (Hc - 4 - bot) / H), pw = W * sc, ph = H * sc;
    const top = Math.max(4, (Hc - bot - ph) / 2);  // centred in the window
    g.imageSmoothingEnabled = sc < 2;
    g.drawImage(off, left, top, pw, ph);
    g.strokeStyle = "#3a4350"; g.strokeRect(left, top, pw, ph);
    // the camera's angles on its axes (degrees from the direction of view, in the observer's frame)
    const cam = cur.meta.camera || {};
    g.fillStyle = "#9aa3ad"; g.font = "10px system-ui";
    if (cam.kind === "screen") {  // a screen in the world's own units (u42: impact parameters alpha, beta in M)
      const [a0, a1] = cam.alpha, [b0, b1] = cam.beta;
      for (const f of [0, 0.5, 1]) {
        g.fillText(num(a0 + f * (a1 - a0), 3), left + pw * f - 8, top + ph + 12);
        g.fillText(num(b1 - f * (b1 - b0), 3), 2, top + ph * f + 4);
      }
      g.fillText(t(cam.axis_label), left, top + ph + 24);
    } else if (cam.kind === "sky") {
      for (let q = 0; q <= 4; q++) g.fillText(`${num(-180 + 90 * q)}°`, left + pw * q / 4 - 8, top + ph + 12);
      for (let q = 0; q <= 2; q++) g.fillText(`${num(90 - 90 * q)}°`, 2, top + ph * q / 2 + 4);
      g.fillText(t("longitude from the direction of view (in the observer's frame)"), left, top + ph + 24);
    } else {
      const hf = (cam.fov || 90) / 2, th = Math.tan(hf * Math.PI / 180);
      for (const f of [0, 0.5, 1]) {
        const a = Math.atan((2 * f - 1) * th) * 180 / Math.PI;
        g.fillText(`${num(a, 3)}°`, left + pw * f - 8, top + ph + 12);
      }
      g.fillText(t("angle from the direction of view (in the observer's frame)"), left, top + ph + 24);
      g.strokeStyle = "rgba(255,255,255,0.25)"; g.beginPath();
      g.moveTo(left + pw / 2 - 6, top + ph / 2); g.lineTo(left + pw / 2 + 6, top + ph / 2);
      g.moveTo(left + pw / 2, top + ph / 2 - 6); g.lineTo(left + pw / 2, top + ph / 2 + 6); g.stroke();
    }
    if (cur.meta.mode && cur.meta.mode !== "seen") {
      const txt = t(cur.meta.mode_label || cur.meta.mode);
      g.fillStyle = "rgba(0,0,0,0.65)"; g.fillRect(left, top, Math.min(pw, g.measureText(txt).width + 8), 16);
      g.fillStyle = "#ffd28a"; g.fillText(txt, left + 4, top + 11);
    }
    geom = { left, top, pw, ph, W, H };
    if (overlay) { g.save(); g.beginPath(); g.rect(left, top, pw, ph); g.clip(); overlay(g, geom, cur.meta, cur.fields); g.restore(); }
  }

  function setImage(meta, rgb, fields = {}, statusText = "") {
    const [H, W] = meta.shape;
    off.width = W; off.height = H;
    const im = off.getContext("2d").createImageData(W, H);
    for (let k = 0; k < W * H; k++) { im.data[4 * k] = rgb[3 * k]; im.data[4 * k + 1] = rgb[3 * k + 1]; im.data[4 * k + 2] = rgb[3 * k + 2]; im.data[4 * k + 3] = 255; }
    off.getContext("2d").putImageData(im, 0, 0);
    cur = { meta, fields };
    // the status is not an error in any mode (a mode other than "seen" is labelled on the image itself)
    fill(status, el("span", { class: "muted" }, t(statusText || meta.mode_label)));
    draw();
  }
  function hover(e) {
    if (!cur || !geom) return;
    const r = cv.getBoundingClientRect(), x = e.clientX - r.left - geom.left, y = e.clientY - r.top - geom.top;
    const i = Math.floor(x / geom.pw * geom.W), j = Math.floor(y / geom.ph * geom.H);
    if (i < 0 || j < 0 || i >= geom.W || j >= geom.H) { readout.textContent = t("point at the image"); return; }
    readout.textContent = describe ? t(describe(cur.meta, cur.fields, i, j)) : t("pixel ({i:d}, {j:d})", { i, j });
  }
  cv.addEventListener("mousemove", hover);
  cv.addEventListener("mouseleave", () => { readout.textContent = t("point at the image"); });
  png.onclick = () => { if (cur) el("a", { href: off.toDataURL("image/png"), download: "observer.png" }).click(); };
  new ResizeObserver(draw).observe(cv);

  const api = { el: root, setImage, current: () => cur, redraw: draw, setStatus: (n) => fill(status, n), geometry: () => geom };
  root.__imagewin = api;  // for automated tests of the page
  return api;
}
