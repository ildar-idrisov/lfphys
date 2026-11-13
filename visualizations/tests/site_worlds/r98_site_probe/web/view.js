// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// The tests' probe (tests of the site's build only): its position as text. Drawing only.
import { el } from "/static/js/ui.js";

export function createView(ctx) {
  const out = el("pre", { id: "site-toy-x" });
  ctx.center.append(out);
  return {
    onHeader() {},
    onFrame(meta) { out.textContent = `x = ${meta.x}`; },
    draw() {},
  };
}
