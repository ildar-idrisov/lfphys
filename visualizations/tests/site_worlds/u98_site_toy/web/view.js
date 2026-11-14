// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// The tests' point (tests of the site's build only): its position as text. Drawing only.
import { el } from "/static/js/ui.js";

export function createView(ctx) {
  // the player's view contract: the view returns its own `center` element and draws a frame in `render(meta, t, blobs)`
  const out = el("pre", { id: "site-toy-x" });
  return {
    center: out,
    onHeader() {},
    render(meta) { out.textContent = `x = ${meta.x}`; },
  };
}
