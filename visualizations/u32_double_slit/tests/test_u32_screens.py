# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""u32's screens (design ``lfphys/sources/explore_2026-11-14_design.md`` §6, §8): the Watch story's script applies
(each set-up change starts a segment with the apparatus the captions describe, the speed takes the stages from a few
photons to thousands, the captions are in the stream at their frames), and the corners of the Explore grid build with
every check ✓ on the screen's fixed screen (in CI the atlas build checks every point anyway)."""

from __future__ import annotations

import itertools

import pytest
from lfviz import headless, registry

VIZ = registry.load("u32_double_slit")
SCREENS = {s["id"]: s for s in VIZ["screens"]}
RECS = {r["id"]: r for r in VIZ["recordings"]}


def _run(spec_or_screen, values=None, clock=None, stop=None, script=None, captions=None, preset=None, seed=1):
    msgs = []
    out = headless.run_spec("u32_double_slit", preset, values, seed, clock, stop, script,
                            lambda m, b=None: msgs.append((m, b)), captions=captions, end_reason="test")
    return out, msgs


@pytest.fixture(scope="module")
def story():
    r = RECS["story"]
    return _run(None, preset=r["preset"], clock={"fps": r["fps"], "speed": r.get("speed")},
                stop={"seconds": r["seconds"]}, script=r["script"], captions=r["captions"])


def test_the_story_has_a_segment_per_stage_with_the_apparatus_its_captions_name(story):
    out, msgs = story
    assert out.frames == RECS["story"]["seconds"] * RECS["story"]["fps"]
    assert out.check_counts()["failed"] == 0
    segs = [m for m, _b in msgs if m["type"] == "segment"]
    assert len(segs) == 4  # start, slit 2 closed, which-path detector, detector removed
    apps = [s["app"] for s in segs]
    assert apps[0]["el2"] == "none" and apps[0]["wp_mode"] == "none"
    assert apps[1]["el2"] == "block" and apps[1]["wp_mode"] == "none"
    assert apps[2]["el2"] == "none" and apps[2]["wp_mode"] == "qubit" and apps[2]["wp_theta"] == 90
    assert apps[3]["el2"] == "none" and apps[3]["wp_mode"] == "none"
    # each change at its played second: the world times follow the script's speeds (0.002, 0.02, 0.2 world s per s)
    t_of = {c["at"]: c for c in RECS["story"]["script"]}
    assert [s["t"] for s in segs[1:]] == pytest.approx([8 * 0.002 + 8 * 0.02 + 10 * 0.2, 8 * 0.002 + 8 * 0.02 + 20 * 0.2,
                                                       8 * 0.002 + 8 * 0.02 + 32 * 0.2], rel=2e-3)
    assert set(t_of) == {0, 8, 16, 26, 36, 48}


def test_the_story_goes_from_single_photons_to_thousands_and_the_pattern_follows_the_set_up(story):
    _out, msgs = story
    frames = [m for m, _b in msgs if m["type"] == "frame"]
    fps = RECS["story"]["fps"]
    seg_n = lambda k: frames[k]["n_seg"]  # noqa: E731 - hits of the current segment at played frame k
    assert seg_n(8 * fps - 1) < 40          # the first 8 s: a few photons, one at a time
    assert seg_n(16 * fps - 1) < 400        # then tens per second
    assert seg_n(26 * fps - 1) > 1500       # thousands when the bands are explained
    # the coherence fitted to the histogram: bands, then none with the which-path mark, then bands again
    coh = lambda k: frames[k]["coh"]["hist"]  # noqa: E731
    assert coh(26 * fps - 1) > 0.9
    assert frames[36 * fps - 1]["coh"]["why"]  # one slit dark: |γ12| undefined, said instead of a fit
    assert abs(coh(48 * fps - 1)) < 0.15
    assert coh(60 * fps - 1) > 0.9
    for k in (26 * fps - 1, 36 * fps - 1, 48 * fps - 1, 60 * fps - 1):
        assert frames[k]["chi2"]["p"] > 1e-3  # every stage's histogram agrees with its own expectation


def test_the_captions_are_in_the_stream_at_their_frames(story):
    _out, msgs = story
    caps = [m for m, _b in msgs if m["type"] == "caption"]
    assert [c["n"] for c in caps] == list(range(len(RECS["story"]["captions"])))
    assert [c["at"] for c in caps] == [c["at"] for c in RECS["story"]["captions"]]
    assert [c.get("hold") for c in caps] == [c.get("hold") for c in RECS["story"]["captions"]]
    for r in RECS.values():  # every recording of the Watch screen has captions
        assert r.get("captions")


EX = SCREENS["explore"]
CORNERS = list(itertools.product(*[(c["values"][0], c["values"][-1]) for c in EX["controls"]]))


@pytest.mark.parametrize("vals", CORNERS, ids=[f"lam{a:g}_d{b:g}_a{c:g}" for a, b, c in CORNERS])
def test_the_explore_grid_corners_build_with_every_check_ok(vals):
    values = {**EX["fixed"], **{c["param"]: v for c, v in zip(EX["controls"], vals)}}
    out, msgs = _run(None, values=values, preset=EX["preset"], clock={"frame_dt": EX["frame_dt"]}, stop=EX["stop"])
    counts = out.check_counts()
    assert counts["failed"] == 0 and counts["ok"] >= 4, counts
    frames = [m for m, _b in msgs if m["type"] == "frame"]
    last = frames[-1]
    assert out.t_end == pytest.approx(EX["stop"]["world_s"])
    assert last["n_seg"] > 2500  # one sample of thousands of hits on the fixed screen
    assert last["chi2"]["p"] > 1e-4
    seg = next(m for m, _b in msgs if m["type"] == "segment")
    assert seg["setup"]["geometry"]["half"] == pytest.approx(EX["fixed"]["screen_um"] * 1e-6)


def test_the_explore_screen_is_the_registry_s_and_its_view_declares_what_it_uses():
    assert registry.check(VIZ) == []
    decl = registry.view_declarations(VIZ)
    assert set(EX["overlays"]) <= set(decl["overlays"])
    assert all(decl["quantSafe"].get(f"{t}.{b}") for t, b, _e in registry.quantize_items(EX["quantize"]))
    assert len(registry.atlases_of(VIZ)) == 1
    n = 1
    for c in EX["controls"]:
        n *= len(c["values"])
    assert n == 48
