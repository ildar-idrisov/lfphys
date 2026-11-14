// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// The Watch screen's story (watch.js; design lfphys/sources/explore_2026-11-14_design.md §2.2, §3.6) on the toy world's
// recording "story" (tests/site_worlds/recordings/s98_atlas_toy; three captions, a new world and a speed change in its
// script): the frames of every world in order, each caption at the frame that follows it in the stream (its frame's
// world time and its played second agree with the recording's fps), and the caption shown as of a cursor.
// Run from visualizations/: node --test player/js/tests/*.test.mjs
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { readStream } from "../api.js";
import { captionAt, story } from "../watch.js";

const REC = new URL("../../../tests/site_worlds/recordings/s98_atlas_toy/", import.meta.url);
const index = JSON.parse(readFileSync(new URL("index.json", REC), "utf-8"));
const entry = index.recordings.find((r) => r.id === "story");

test("the story: worlds, frames in order, captions at their frames", async () => {
  const S = story(await readStream(readFileSync(new URL(entry.file, REC))));
  assert.equal(S.worlds.length, entry.worlds);
  assert.equal(S.steps.length, entry.frames);
  assert.equal(S.captions.length, entry.captions);
  for (const c of S.captions) {
    const st = S.steps[c.step], f = S.worlds[st.w].frames[st.i];
    assert.ok(Math.abs(f.t - c.t) <= 1e-12, `caption ${c.n}: its frame's world time`);
    // the played second of its frame: step / (fps / stride)
    assert.ok(Math.abs(c.step / (entry.fps / (entry.frame_stride || 1)) - c.at) < 1e-9, `caption ${c.n}: its played second ${c.at}`);
  }
  assert.deepEqual(S.captions.map((c) => c.n), [0, 1, 2]);
  assert.ok(S.captions.some((c) => c.hold), "a caption with a hold");
  assert.ok(S.steps.some((s) => s.w === 1), "the second world's frames follow the first's");
});

test("the caption as of the cursor", async () => {
  const S = story(await readStream(readFileSync(new URL(entry.file, REC))));
  const [c0, c1, c2] = S.captions;
  assert.equal(captionAt(S.captions, 0), c0);
  assert.equal(captionAt(S.captions, c1.step - 1), c0);
  assert.equal(captionAt(S.captions, c1.step), c1);
  assert.equal(captionAt(S.captions, S.steps.length - 1), c2);
  assert.equal(captionAt([{ step: 5 }], 2), null, "before the first caption: none");
});
