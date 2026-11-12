// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// 2-D canvas with world coordinates, pan (drag) and zoom (wheel), for the visualization views.
// sx, sy: pixels per world unit along x and y (y up). Wheel zooms both axes; Shift+wheel only y; Alt+wheel only x.
import { css, fresh2d } from "./ui.js";

export class Plane {
  constructor(canvas, { onChange, lockAspect = true } = {}) {
    this.cv = canvas;
    this.ctx = canvas.getContext("2d");
    this.cx = 0; this.cy = 0;        // world point at the canvas centre
    this.sx = 1; this.sy = 1;        // px per world unit
    this.lockAspect = lockAspect;
    this.onChange = onChange || (() => {});
    this.w = 1; this.h = 1; this.dpr = 1;
    this._bind();
    new ResizeObserver(() => { this.resize(); this.onChange(); }).observe(canvas);
    this.resize();
  }

  resize() {
    const r = this.cv.getBoundingClientRect();
    this.dpr = Math.min(window.devicePixelRatio || 1, 2);
    this.w = Math.max(1, r.width); this.h = Math.max(1, r.height);
    this.cv.width = Math.round(this.w * this.dpr); this.cv.height = Math.round(this.h * this.dpr);
    this.ctx.setTransform(this.dpr, 0, 0, this.dpr, 0, 0);
  }

  fit(x0, x1, y0, y1, margin = 0.06) {
    const W = this.w * (1 - 2 * margin), H = this.h * (1 - 2 * margin);
    this.cx = 0.5 * (x0 + x1); this.cy = 0.5 * (y0 + y1);
    const sx = W / Math.max(x1 - x0, 1e-300), sy = H / Math.max(y1 - y0, 1e-300);
    if (this.lockAspect) { this.sx = this.sy = Math.min(sx, sy); } else { this.sx = sx; this.sy = sy; }
    this.onChange();
  }

  X(x) { return this.w / 2 + (x - this.cx) * this.sx; }
  Y(y) { return this.h / 2 - (y - this.cy) * this.sy; }
  wx(px) { return this.cx + (px - this.w / 2) / this.sx; }
  wy(py) { return this.cy - (py - this.h / 2) / this.sy; }
  bounds() { return { x0: this.wx(0), x1: this.wx(this.w), y0: this.wy(this.h), y1: this.wy(0) }; }

  _bind() {
    let drag = null;
    this.cv.addEventListener("mousedown", (e) => { drag = { x: e.clientX, y: e.clientY, cx: this.cx, cy: this.cy }; });
    window.addEventListener("mouseup", () => { drag = null; });
    window.addEventListener("mousemove", (e) => {
      if (!drag) return;
      this.cx = drag.cx - (e.clientX - drag.x) / this.sx;
      this.cy = drag.cy + (e.clientY - drag.y) / this.sy;
      this.onChange();
    });
    this.cv.addEventListener("wheel", (e) => {
      e.preventDefault();
      const r = this.cv.getBoundingClientRect();
      const px = e.clientX - r.left, py = e.clientY - r.top;
      const wx = this.wx(px), wy = this.wy(py);
      const k = Math.exp(-e.deltaY * 0.0015);
      const onlyY = e.shiftKey && !this.lockAspect, onlyX = e.altKey && !this.lockAspect;
      if (!onlyY) this.sx *= k;
      if (!onlyX) this.sy *= k;
      this.cx = wx - (px - this.w / 2) / this.sx;
      this.cy = wy + (py - this.h / 2) / this.sy;
      this.onChange();
    }, { passive: false });
  }

  clear() {  // the start of a frame: the default drawing state too (ui.js fresh2d)
    const c = fresh2d(this.ctx, this.dpr);
    // the whole bitmap: w, h are fractional (the element's box), so filling w x h would leave the last pixel column and
    // row blended with the previous frame (found by the key frames' browser check: v01)
    c.fillStyle = css("--canvas"); c.fillRect(0, 0, this.cv.width / this.dpr, this.cv.height / this.dpr);
  }

  // grid with "nice" steps; label(v) formats a coordinate
  grid({ labelX, labelY, unitX = 1, unitY = 1 } = {}) {
    const c = this.ctx, b = this.bounds();
    c.save();
    c.strokeStyle = css("--grid"); c.lineWidth = 1;
    c.fillStyle = css("--muted"); c.font = "11px system-ui";
    // label spacing in pixels, not a fixed count: long labels must not overlap on narrow canvases
    const stepX = nice((b.x1 - b.x0) / unitX / Math.max(2, this.w / 120)) * unitX;
    const stepY = nice((b.y1 - b.y0) / unitY / Math.max(2, this.h / 60)) * unitY;
    for (let x = Math.ceil(b.x0 / stepX) * stepX; x <= b.x1; x += stepX) {
      const X = this.X(x); c.beginPath(); c.moveTo(X, 0); c.lineTo(X, this.h); c.stroke();
      if (labelX) c.fillText(labelX(x), X + 3, this.h - 4);
    }
    for (let y = Math.ceil(b.y0 / stepY) * stepY; y <= b.y1; y += stepY) {
      const Y = this.Y(y); c.beginPath(); c.moveTo(0, Y); c.lineTo(this.w, Y); c.stroke();
      if (labelY) c.fillText(labelY(y), 4, Y - 3);
    }
    c.restore();
  }
}

export function nice(x) {
  if (!(x > 0)) return 1;
  const e = Math.floor(Math.log10(x)), m = x / 10 ** e;
  return (m < 1.5 ? 1 : m < 3.5 ? 2 : m < 7.5 ? 5 : 10) * 10 ** e;
}
