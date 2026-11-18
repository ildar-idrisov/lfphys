// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// Watch's time label (watch.js rateText; EX2 design lfphys/sources/explore_EX2_2026-11-18_design.md §5 F12, §1.1): written
// as Explore's (explore.js worldTime, factorText, timeLabel): the world's time on a human scale (ns … s) or in the
// header's units.t_show, in seconds at school, the factor in powers of ten from 10⁶ on; never «world 0.00 s · slow
// motion ×1199040767» for a world of nanoseconds (step F's notes, V53). Run from visualizations/:
// node --test player/js/tests/*.test.mjs
import { test } from "node:test";
import assert from "node:assert/strict";
import { rateText } from "../watch.js";
import { factorText, timeLabel, worldTime } from "../explore.js";

const NB = "\u00a0";

test("a world of nanoseconds and microseconds: its time on a human scale, the factor in powers of ten (u35, u37)", () => {
  // u35: a photon's flight of 2 ns, the build-up 0.1 s in 10 played s → 0.01 world s per played s, ×100 slow
  assert.equal(rateText(2e-9, 0.01), `world 2${NB}ns · slow motion ×100`);
  // the label step F's notes found: 0.834 ns of world time per played second, «×1199040767» before F12
  assert.equal(rateText(1.5e-9, 1 / 1199040767), `world 1.5${NB}ns · slow motion ×1.2·10⁹`);
  assert.equal(rateText(1.67e-6, 0.02), `world 1.67${NB}µs · slow motion ×50`);  // u37: a pair's flight over 500 m
  assert.equal(rateText(0.25, 1e-3), `world 250${NB}ms · slow motion ×1,000`);
  assert.equal(rateText(3.5, 1), `world 3.5${NB}s · real time`);
  assert.equal(rateText(3.5, 2.5), `world 3.5${NB}s · sped up ×2.5`);
  assert.equal(rateText(3.5, 4e7), `world 3.5${NB}s · sped up ×4·10⁷`);
});

test("Watch's label is Explore's: the same time and factor for any rate, unit and audience", () => {
  const u34 = { units: { t_show: { unit: "GM/c³", s: 4.925e-5 } } };  // 10 M☉: GM/c³ = 49.25 µs
  for (const [tt, r, h, school] of [[2e-9, 1e-10, null, false], [0.0123, 1 / 120, null, false], [0.05, 8.33e-3, u34, false],
    [0.45, 0.25, null, true], [1.234, 1, null, true], [7e-7, 2e-8, null, false]]) {
    const ex = timeLabel({ tt, tEnd: 2 * tt, speed: r, header: h, school });
    const w = rateText(tt, r, h, school);
    assert.ok(ex.startsWith(`${w} · `), `${w} | ${ex}`);
    assert.equal(w, `world ${worldTime(tt, h, school)} · ${factorText(r)}`);
  }
  // u34: the world's own unit; a school world: seconds («0.45 s», never «450 ms»: the EX1 design, review EX1-worlds F8)
  assert.equal(rateText(0.05, 8.33e-3, u34), `world 1,015${NB}GM/c³ · slow motion ×120`);
  assert.equal(rateText(0.45, 0.25, null, true), `world 0.45${NB}s · slow motion ×4`);
  assert.equal(rateText(0.45, 0.25, null, false), `world 450${NB}ms · slow motion ×4`);
  assert.equal(rateText(0.45, 0.25, u34, true), `world 9,137${NB}GM/c³ · slow motion ×4`, "a declared unit wins at school too");
  // no rate (a single frame): the time alone
  assert.equal(rateText(2e-9, null), `world 2${NB}ns`);
  assert.equal(rateText(2e-9, 0), `world 2${NB}ns`);
});
