// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// The instruments' fixture playground (tests only): the shared panels and a list of positions.
import { el } from "/static/js/ui.js";
import { createPlayground } from "/static/js/playground.js";

export function createView(ctx) {
  const pg = createPlayground(ctx);
  const out = el("pre", { id: "osc-pos" });
  return {
    center: el("div", {}, out), leftPanels: pg.leftPanels, rightPanels: pg.rightPanels,
    reset() { pg.reset(); },
    snapshot() { return { pg: pg.snapshot() }; },
    restore(k) { pg.restore(k.pg); },
    onHeader(meta) { pg.onHeader(meta); },
    onMessage(meta, blobs) { pg.onMessage(meta, blobs); },
    render(frame, t, blobs) { out.textContent = JSON.stringify({ t, ids: frame.ids, pos: Array.from(blobs.pos || []) }); pg.render(frame, t); },
  };
}
