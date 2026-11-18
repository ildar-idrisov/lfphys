# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""A university toy demonstration for the tests of the screens' university features (design
``lfphys/sources/explore_EX2_2026-11-18_design.md`` §1.4, §5, §7; found only through ``LFVIZ_EXTRA``, never in the
catalogue): the toy ball of ``s98_atlas_toy`` with a law parameter ``g_scale`` (the field × a factor; the accepted value
1), so that a lab step may carry modified physics (``fixed``: allowed at ``standard`` only, flagged «MODIFIED PHYSICS»
on its card and in the bar), a world whose default speed is half real time (Explore's ``speed: "world"``) and whose
time is shown in ms (``units.t_show``). Explore: a compound control and the law control, readouts with an error and a
reference, «CSV of this point». Lab work: one step on the modified field with a counter, a readout with the run's own
error and formula columns; its worksheet names a ``basis`` (with a quotation). Its atlases are built by the browser
tests' fixtures (``site/fixtures.py --world u96_lab_toy``)."""

from __future__ import annotations

from lfviz.i18n import T
from lfviz.params import Param, Schema
from s98_atlas_toy.viz import G, SCHEMA as TOY, Simulation as Toy

SCHEMA = Schema(list(TOY.params) + [Param("g_scale", T("Gravity, × the standard"), "float", 1.0, min=0.5, max=2.0,
                                          standard=1.0)],
                presets={"field": TOY.presets["field"], "chute": TOY.presets["chute"]})


class Simulation(Toy):
    default_speed = 0.5  # half real time: Explore's speed "world" plays it so (EX2 §5 F1)

    @classmethod
    def field(cls, params) -> float:
        return G * float(params.get("g_scale", 1.0))

    def header(self):
        meta, blobs = super().header()
        meta = dict(meta)
        meta["units"] = {**meta.get("units", {}), "t_show": {"unit": T("ms"), "s": 1e-3}}
        meta["modifications"] = SCHEMA.modifications(self.params)
        return meta, blobs

    @classmethod
    def lab_reference(cls, step_id, fixed, values, reference):
        if step_id == "counts" and reference == "fall_coefficient":
            return Toy.lab_reference.__func__(cls, "ticks", fixed, values, reference)  # on this world's field
        if step_id == "throws" and reference == "horizontal_speed":  # the step on Explore's atlas (EX2 §5 F9)
            return {"value": 2.0, "unit": T("m/s"), "label": T("L / T = v₀ of the flat throw"),
                    "how": T("closed form of a horizontal throw without air"), "kind": "closed form"}
        raise ValueError(T("no law for the step {step}", step=step_id))


_COLS = [{"id": "h", "label": T("h, m"), "from": "stand"},
         {"id": "n", "label": T("n, ticks"), "from": "ticks"},
         {"id": "v", "label": T("v, m/s"), "from": "speedo"},
         {"id": "sqrt_h", "label": T("√h, m^½"), "expr": "sqrt(h)"},
         {"id": "T", "label": T("T = 0.1·n, s"), "expr": "0.1 * n"}]

VIZ = {
    "id": "u96_lab_toy", "title": T("A thrown ball for the tests of the university screens"), "summary": "",
    "purpose": "", "version": "1.0", "schema": SCHEMA, "simulation": Simulation, "audience": "university",
    "section": "mechanics", "teaser": T("A ball is thrown; where does it land?"), "related": [],
    "courses": [{"text": T("A book for the tests of the site"), "chapters": "1"}],
    "recordings": [{"id": "field", "preset": "field", "seconds": 2, "fps": 10, "speed": None, "seed": 1, "poster": 1.0}],
    "screens": [
        {"id": "explore", "kind": "explore", "preset": "field", "fixed": {},
         "controls": [{"id": "throw", "label": T("Throw"), "values": ["flat", "lob"],
                       "labels": [T("flat, 2 m/s"), T("a lob, 3 m/s at 30°")],
                       "sets": {"v0": [2.0, 3.0], "angle_deg": [0.0, 30.0]}, "default": "flat"},
                      {"param": "g_scale", "values": [1.0, 1.5], "default": 1.0, "label": T("Gravity"),
                       "unit": T("× standard")}],
         "acts": "next", "time": "flight", "fps": 10, "speed": "world",
         "stop": {"events": {"landing": 1}, "after_s": 0.1, "max_world_s": 5.0},
         "drop": {"types": ["story"], "frame_blobs": ["ghost"]}, "quantize": {"traj.s": "u16"},
         "overlays": ["path", "v"], "traces": 2, "readouts": ["range", "v_mean", "n_ticks"]},
        {"id": "lab", "kind": "lab",
         "instruments": {
             "stand": {"kind": "readout", "label": T("Height scale of the stand"), "unit": "m", "division": 0.01,
                       "error": 0, "error_note": T("the stand sets the height at its marks"), "reads": "control:h_m"},
             "ticks": {"kind": "counter", "label": T("Tick counter"), "unit": "", "error": "poisson",
                       "reads": "n_ticks"},
             "speedo": {"kind": "readout", "label": T("Speedometer"), "unit": "m/s", "division": 0.001,
                        "sigma": "v_mean_se", "reads": "v_mean"},
             "tape": {"kind": "readout", "label": T("Measuring tape"), "unit": "m", "division": 0.001, "error": 0.0005,
                      "reads": "range"},
             "timer": {"kind": "readout", "label": T("Flight timer"), "unit": "s", "division": 0.001, "error": 0.0005,
                       "reads": "flight_time"}},
         "steps": [{"id": "counts", "title": T("The timer's ticks on a stronger field"),
                    "goal": T("Count the timer's ticks during the fall and find how the fall time depends on the height"),
                    "preset": "chute", "controls": [{"param": "h_m", "values": [0.3, 0.6, 1.0, 1.5], "default": 0.6}],
                    "fixed": {"v0": 0.0, "g_scale": 1.5}, "instruments": ["stand", "ticks", "speedo"],
                    "columns": _COLS, "plot": {"x": "sqrt_h", "y": "T", "fit": "line0", "fits": ["line0", "line", "power"]},
                    "laws": [{"x": "sqrt_h", "y": "T", "model": "line0", "quantity": "slope", "label": T("T / √h"),
                              "unit": T("s/m^½"), "reference": "fall_coefficient"}],
                    "frame_dt": 1 / 60, "speed": "world",
                    "stop": {"events": {"landing": 1}, "after_s": 0.05, "max_world_s": 3.0},
                    "quantize": {"traj.s": "u16"}, "overlays": ["path"], "readouts": ["n_ticks", "v_mean"]},
                   # the points of the Explore screen (EX2 §5 F9): its atlas, its controls; its own instruments
                   {"id": "throws", "atlas": "explore", "title": T("Throws: range and time"),
                    "goal": T("Measure the range and the flight time of each throw and find the horizontal speed"),
                    "instruments": ["tape", "timer"],
                    "columns": [{"id": "L", "label": T("L, m"), "from": "tape"},
                                {"id": "Tf", "label": T("T, s"), "from": "timer"}],
                    "plot": {"x": "Tf", "y": "L", "fit": "line0", "fits": ["line0", "line"]},
                    "laws": [{"x": "Tf", "y": "L", "model": "line0", "quantity": "slope",
                              "label": T("L / T"), "unit": T("m/s"), "reference": "horizontal_speed"}]}],
         "worksheet": {"basis": [{"text": T("Free fall timed by counting: the time grows as the square root of the height"),
                                  "source": "A. Author, A Book for the Tests of the Site, ch. 1",
                                  "quote": "The time of fall is proportional to the square root of the height.",
                                  "quote_lang": "en"}],
                       "goal": T("Find how the fall time depends on the height on a field 1.5 times the standard one"),
                       "bench": [T("A ball falls from rest from a stand of 0.3–1.5 m on a field 1.5 times the standard "
                                   "one (modified physics, said on the step); a tick counter, a speedometer.")],
                       "procedure": [T("Count the ticks at each height and plot T = 0.1·n against the square root of "
                                       "the height; try a line through the origin and a power law.")],
                       "record": [T("the table of your readings with their errors"),
                                  T("each fit: the model, the parameters with their errors, χ² and p")],
                       "variants": [{"id": "high", "label": T("From the highest stand"),
                                     "values": {"counts": {"h_m": 1.5}, "throws": {"throw": "lob", "g_scale": 1.5}},
                                     "text": {"goal": T("Find the fall time from the highest stand")}}]}},
    ],
}
