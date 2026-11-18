// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// The university toy of the screens' tests (tests/site_worlds/u96_lab_toy): it draws through the toy ball's view
// (s98_atlas_toy). Its declarations are literals here, as registry.view_declarations reads them from this file.
import { createView as toyView } from "/viz/s98_atlas_toy/view.js";

// what the view accepts quantised and the overlays it can toggle (the toy ball's, read by the registry)
export const QUANT_SAFE = { "traj.s": "u16" };
export const OVERLAYS = [
  { id: "path", label: "path", default: true },
  { id: "v", label: "velocity", default: false },
];

export function createView(ctx) { return toyView(ctx); }
