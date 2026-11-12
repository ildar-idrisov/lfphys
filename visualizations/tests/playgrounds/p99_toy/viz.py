# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""A toy playground for the framework's tests (``LFVIZ_EXTRA``; never in the catalogue): free particles moving in
straight lines, a probe that reads the nearest particle's distance, and a random kick (to test that a world continued
from a checkpoint draws the same numbers); a trail of each particle (accumulative messages, the kept points repeated at
a segment's start without changing the world: review B6-F5, F8) and a scene box sent once (a set-like message the
framework repeats at a segment's start: B6-F4).

For direct manipulation and the instruments (plan P16.2, P16.3; the integrator's API of 2026-11-11) the toy also has:
handles on every type (a particle: position and velocity in 3-D or in the plane z = 0, its radius for picking; a probe:
x, y in the plane z = 0; a reflecting wall: one coordinate along the axis it chooses, the axis form of a handle), every
object's place in the frame's ``at``, measurables with their values in ``meas``, and a world parameter ``ndim`` (3-D or
the plane z = 0) so that a new world of the other dimension refuses what it cannot take when the scene is carried over
(a particle off the plane). A hand placement outside the region ±5 m is refused (the ghost snaps back).

The reference of the carry-over hooks (review LB1-F5): a «cloud» of points whose state is not in a scene file
(``object_state`` None) but goes into a new world through ``carry_state``; and a state of the world itself, the time
the particles spent in each cell of an 8 × 8 grid over the region («visits»), carried through ``carry_state`` /
``carry_world`` and said in the notice."""

from __future__ import annotations

import os

import numpy as np

from lfviz.errors import Refusal
from lfviz.params import Param, Schema
from lfviz.playground import ObjectType, PlaygroundSimulation, axis_index, fmt, scene_param

HALF = 5.0  # the region: |x|, |y|, |z| <= HALF (m)


def _p(*a, **k):
    return Param(*a, **k)


PARTICLE3 = Schema([_p("x", "x", "float", 0.0, unit="м"), _p("y", "y", "float", 0.0, unit="м"),
                    _p("z", "z", "float", 0.0, unit="м"),
                    _p("vx", "vx", "float", 1.0, unit="м/с"), _p("vy", "vy", "float", 0.0, unit="м/с"),
                    _p("vz", "vz", "float", 0.0, unit="м/с"), _p("mass", "масса", "float", 1.0, min=1e-6),
                    _p("kick", "толчок", "float", 0.0, min=0.0), _p("r", "радиус", "float", 0.3, min=1e-3, unit="м"),
                    _p("vmax", "Наибольшая скорость броска", "float", 12.0, min=1e-3, unit="м/с")])
PARTICLE2 = Schema([p for p in PARTICLE3.params if p.id not in ("z", "vz")])
PROBE = Schema([_p("x", "x", "float", 0.0, unit="м"), _p("y", "y", "float", 0.0, unit="м")])
CLOUD = Schema([_p("x", "x", "float", 0.0, unit="м"), _p("y", "y", "float", 0.0, unit="м"),
                _p("vx", "vx", "float", 0.0, unit="м/с"), _p("vy", "vy", "float", 0.0, unit="м/с"),
                _p("n", "Точек", "int", 12, min=2, max=200), _p("spread", "Разброс", "float", 0.5, min=1e-3, unit="м")])
NCELL = 8  # the world's own state: the time the particles spent in each cell of NCELL x NCELL over the region


def _wall(axes, form="letter"):
    """A reflecting plane across one axis: its coordinate and the axis, named by a letter (a wall), by its number 0, 1,
    2 (a mirror) or by that number as text "0", "1", "2" (a screen, as p02's walls): every form of an axis handle
    (integrator, 2026-11-11)."""
    opts = [(i if form == "number" else str(i) if form == "text" else a, a) for i, a in enumerate(axes)]
    start = {"letter": 3.0, "number": -3.0, "text": 2.0}[form]
    return Schema([_p("position", "Положение", "float", start, min=-HALF, max=HALF, unit="м"),
                   _p("axis", "Ось", "select", opts[0][0], options=opts)])


SCHEMA = Schema([_p("drag", "Сопротивление (закон)", "float", 0.0, standard=0.0, min=0.0),
                 _p("ndim", "Размерность", "select", 3, options=[(3, "3-D"), (2, "2-D: плоскость z = 0")]),
                 scene_param()], presets={
    "two": {"label": "Две частицы и датчик", "params": {"scene": {"format": "lfscene", "version": 1, "objects": [
        {"type": "particle", "values": {"x": -1.0, "vx": 1.0}},
        {"type": "particle", "values": {"x": 1.0, "vx": -0.5, "kick": 0.1}},
        {"type": "probe", "values": {"x": 0.0, "y": 0.5}}]}}},
    "empty": {"label": "Пустая сцена", "params": {}},
})


def palette(ndim: int) -> dict:
    three = ndim == 3
    return {"particle": ObjectType("particle", "Частица", "particle", PARTICLE3 if three else PARTICLE2,
                                   color="#1c7ed6",
                                   handles={"position": ["x", "y", "z"] if three else ["x", "y"],
                                            "velocity": ["vx", "vy", "vz"] if three else ["vx", "vy"], "size": "r",
                                            "velocity_max": "vmax"}),
            "probe": ObjectType("probe", "Датчик", "probe", PROBE, limit=3, color="#e8590c",
                                handles={"position": ["x", "y"]}),
            "wall": ObjectType("wall", "Стенка (отражает)", "body", _wall("xyz" if three else "xy"), limit=2,
                               color="#adb5bd", handles={"position": {"param": "position", "axis_param": "axis"}}),
            "mirror": ObjectType("mirror", "Зеркало (отражает; ось — номер)", "body",
                                 _wall("xyz" if three else "xy", "number"), limit=2, color="#868e96",
                                 handles={"position": {"param": "position", "axis_param": "axis"}}),
            "screen": ObjectType("screen", "Экран (отражает; ось — номер текстом)", "body",
                                 _wall("xyz" if three else "xy", "text"), limit=2, color="#5c7cfa",
                                 handles={"position": {"param": "position", "axis_param": "axis"}}),
            "cloud": ObjectType("cloud", "Облако точек", "particle", CLOUD, limit=3, color="#37b24d",
                                handles={"position": ["x", "y"], "velocity": ["vx", "vy"], "size": "spread",
                                         # shown in cm/s (the reference of a display unit; the edit stays in m/s)
                                         "velocity_display": {"unit": "см/с", "factor": 100.0}})}


class Simulation(PlaygroundSimulation):
    VIZ_ID = "p99_toy"
    PALETTE = palette(3)
    default_speed = 1.0
    speed_range = (0.01, 100.0)
    checkpoint_every = float(os.environ.get("P99_CKPT", "60"))  # tests make segments quickly

    def __init__(self, params, seed, emit):
        super().__init__(params, seed, emit)
        self.ndim = int(params.get("ndim", 3))
        self.PALETTE = {**type(self).PALETTE, **palette(self.ndim)}  # a test's subclass may add its own types
        self.state = {}  # id -> [x, y, vx, vy, z, vz] (the first four as in the earlier, flat toy)
        self.trail_new, self.trail_kept, self.n_tick = {}, {}, 0
        self.clouds = {}  # id -> [points (n, 2), velocity (2,)]: in no scene file, carried by carry_state
        self.visits = np.zeros((NCELL, NCELL))  # the world's own state (s per cell)
        self.start_scene()
        self.emit({"type": "box", "t": self.t, "box": self._box()})

    # --- the scene ---------------------------------------------------------------------------------------------
    def place(self, kind, values):
        if self.ndim == 2 and kind == "particle":  # a particle carried from 3-D: only one on the plane z = 0
            z, vz = values.pop("z", 0.0), values.pop("vz", 0.0)
            if z or vz:
                raise Refusal(f"частица вне плоскости z = 0 (z = {fmt(z)} м, vz = {fmt(vz)} м/с)",
                              hint="перенесите её в 3-D мир или поставьте z = 0, vz = 0")
        if self.ndim == 2 and kind == "cloud" and float(values.get("spread", 0.5)) > 2.0:
            values["spread"] = 2.0  # the toy's plane takes clouds at most 2 m wide (a value a carry-over changes, said)
        if kind in ("wall", "mirror", "screen") and "axis" in values \
                and values["axis"] not in [o[0] for o in self.PALETTE[kind].schema.by_id["axis"].options]:
            raise Refusal(f"стенки поперёк оси {values.get('axis')} в этом мире нет: он плоский",
                          hint="выберите ось x или y")
        return values

    def _vec(self, v):
        return [v["x"], v["y"], v["vx"], v["vy"], v.get("z", 0.0), v.get("vz", 0.0)]

    def _inside(self, obj, v):
        out = [k for k in ("x", "y", "z") if k in v and abs(v[k]) > HALF]
        if out:
            raise Refusal(f"«{obj['label']}»: точка вне области игрушки (|{', '.join(out)}| > {HALF:g} м)",
                          hint="отпустите объект внутри области")

    def on_add(self, obj, state):
        v = obj["values"]
        if obj["type"] == "particle":
            xv = np.array(state["xv"] if state else self._vec(v), float)
            if len(xv) == 4:  # a file of the earlier toy (x, y, vx, vy)
                xv = np.concatenate([xv, [0.0, 0.0]])
            if self.ndim == 2 and (xv[4] or xv[5]):
                raise Refusal(f"частица вне плоскости z = 0 (z = {fmt(xv[4])} м, vz = {fmt(xv[5])} м/с)",
                              hint="перенесите её в 3-D мир")
            self.state[obj["id"]] = xv
        elif obj["type"] == "cloud":
            if state and "pts" in state:  # carried (an array from carry_state)
                pts = np.array(state["pts"], float).reshape(-1, 2)
                if len(pts) != v["n"]:
                    self.carry_note(f"число точек {len(pts)} → {v['n']}: облако разыграно заново", restarted=True)
                    pts = None
            else:
                pts = None
            if pts is None:
                pts = np.array([v["x"], v["y"]]) + v["spread"] * self.rng.normal(size=(v["n"], 2))
            self.clouds[obj["id"]] = [pts, np.array([v["vx"], v["vy"]], float)]

    def on_remove(self, obj):
        self.state.pop(obj["id"], None)
        self.clouds.pop(obj["id"], None)
        self.trail_new.pop(obj["id"], None)
        self.trail_kept.pop(obj["id"], None)

    def on_set(self, obj, old):
        v = obj["values"]
        if obj["type"] in ("particle", "probe") and any(v.get(k) != old.get(k) for k in ("x", "y", "z")):
            self._inside(obj, v)
        if obj["type"] == "particle":
            s = self.state[obj["id"]]
            for i, k in enumerate(("x", "y", "vx", "vy", "z", "vz")):
                if k in v and v[k] != old[k]:
                    s[i] = v[k]
        if obj["type"] == "cloud":
            if v["n"] != old.get("n"):
                raise Refusal("число точек облака меняется только новым облаком", hint="удалите и добавьте облако")
            c = self.clouds[obj["id"]]
            if any(v[k] != old.get(k) for k in ("x", "y")):  # moved: the points go with their centre
                c[0] = c[0] + (np.array([v["x"], v["y"]]) - c[0].mean(axis=0))
            if any(v[k] != old.get(k) for k in ("vx", "vy")):
                c[1] = np.array([v["vx"], v["vy"]], float)

    def object_state(self, obj):
        s = self.state.get(obj["id"])
        return None if s is None else {"xv": s.tolist()}  # a cloud: None (its points are in no scene file)

    # --- the carry-over (review LB1-F5): the reference of the hooks ------------------------------------------------
    def carry_state(self):
        return {"objects": {k: {"pts": c[0].copy()} for k, c in self.clouds.items()},
                "world": {"visits": self.visits.copy(), "ndim": self.ndim}}

    def carry_world(self, state, laws):
        if state is None:
            self.carry_note("посещения ячеек начаты заново с нуля", restarted=True)
            return
        v = np.asarray(state["visits"], float)
        if v.shape != self.visits.shape:
            raise Refusal(f"сетка посещений {v.shape} не та, что здесь {self.visits.shape}")
        self.visits = v.copy()
        if int(state.get("ndim", self.ndim)) != self.ndim:
            self.carry_note("посещения перенесены в плоскость z = 0 (ячейки по x, y те же)")

    # --- the solver ----------------------------------------------------------------------------------------------
    def advance(self, t_target):
        dt = t_target - self.t
        if dt <= 0:
            return
        walls = [(axis_index(o["values"]["axis"]), o["values"]["position"])
                 for o in self.objects.values() if o["type"] in ("wall", "mirror", "screen")]
        P, V = [0, 1, 4], [2, 3, 5]  # the state's places of x, y, z and of vx, vy, vz
        for oid, s in self.state.items():
            kick = self.objects[oid]["values"]["kick"]
            s[V] *= np.exp(-self.params["drag"] * dt)
            if kick:
                s[2:4] += kick * self.rng.normal(size=2) * np.sqrt(dt)
            before = s[P].copy()
            s[P] += s[V] * dt
            for ax, w in walls:  # an elastic reflection by a plane crossed during the step
                if (before[ax] - w) * (s[P[ax]] - w) < 0:
                    s[P[ax]] = 2 * w - s[P[ax]]
                    s[V[ax]] = -s[V[ax]]
            ij = np.floor((s[[0, 1]] + HALF) / (2 * HALF) * NCELL).astype(int)
            if (0 <= ij).all() and (ij < NCELL).all():
                self.visits[ij[0], ij[1]] += dt
        for c in self.clouds.values():
            c[0] = c[0] + c[1] * dt
        self.t = t_target

    def max_step(self):
        return 0.05

    def _trail(self, full=False):
        src = self.trail_kept if full else self.trail_new
        ids = [k for k, v in src.items() if v]
        if not ids and not full:
            return
        self.emit({"type": "trail", "t": self.t, "ids": ids, "counts": [len(src[k]) for k in ids],
                   **({"reset": True} if full else {})},
                  {"pts": np.array([q for k in ids for q in src[k]], np.float32).reshape(-1, 2)})
        if not full:
            for k in ids:
                self.trail_kept.setdefault(k, []).extend(self.trail_new[k])
                del self.trail_kept[k][:-50]
                self.trail_new[k] = []

    def rekey(self):
        self._trail(full=True)

    def _at(self, o) -> list:
        v = o["values"]
        if o["type"] == "particle":
            return self.state[o["id"]][[0, 1, 4]].tolist()
        if o["type"] == "probe":
            return [v["x"], v["y"], 0.0]
        if o["type"] == "cloud":
            return [*self.clouds[o["id"]][0].mean(axis=0).tolist(), 0.0]
        p = [0.0, 0.0, 0.0]
        p[axis_index(v["axis"])] = v["position"]
        return p

    def measurables(self):
        out = [{"id": "ke", "label": "Кинетическая энергия частиц", "unit": "Дж", "of": None},
               {"id": "visits", "label": "Время частиц в области (сумма по ячейкам)", "unit": "с", "of": None}]
        for o in self.objects.values():
            if o["type"] == "particle":
                out.append({"id": f"speed.{o['id']}", "label": f"Скорость «{o['label']}»", "unit": "м/с", "of": o["id"]})
            elif o["type"] == "probe":
                out.append({"id": f"near.{o['id']}", "label": f"«{o['label']}»: до ближайшей частицы", "unit": "м",
                            "of": o["id"], "group": "Датчики"})
        return out

    def frame(self):
        ids = list(self.state)
        for k in ids:
            self.trail_new.setdefault(k, []).append(self.state[k][:2].tolist())
        self.n_tick += 1
        if self.n_tick % 3 == 0:
            self._trail()
        pos = np.array([self.state[i][[0, 1, 4]] for i in ids], float).reshape(-1, 3)
        probes, meas, note = {}, {}, {}
        ke = 0.0
        for i in ids:
            vel = self.state[i][[2, 3, 5]]
            v2 = float(vel @ vel)
            ke += 0.5 * self.objects[i]["values"]["mass"] * v2
            meas[f"speed.{i}"] = float(np.sqrt(v2))
        meas["ke"] = ke
        meas["visits"] = float(self.visits.sum())
        for o in self.objects.values():
            if o["type"] == "probe":
                d = np.hypot(pos[:, 0] - o["values"]["x"], pos[:, 1] - o["values"]["y"]) if len(ids) else np.array([])
                probes[o["id"]] = {"nearest": float(d.min()) if d.size else None}
                meas[f"near.{o['id']}"] = float(d.min()) if d.size else float("nan")
                if not d.size:
                    note[f"near.{o['id']}"] = "частиц нет"
        if self.check_due():
            self.running_check("energy", "Кинетическая энергия", ke, None, 0.0, info=True)
        at = {o["id"]: self._at(o) for o in self.objects.values()}
        now = {i: {"положение, м": ", ".join(f"{x:.4g}" for x in self.state[i][[0, 1, 4]]),
                   "скорость, м/с": ", ".join(f"{x:.4g}" for x in self.state[i][[2, 3, 5]])} for i in ids}
        rad = np.array([self.objects[i]["values"]["r"] for i in ids], float)
        return ({"ids": ids, "probes": probes, "at": at, "meas": meas, "now": now, **({"meas_note": note} if note else {})},
                {"pos": pos.astype(np.float32), "rad": rad.astype(np.float32)})

    def header(self):
        return {"title": "Игрушка: свободные частицы", "actions": [], "playground": self.playground_header(),
                "toy": {"ndim": self.ndim, "half": HALF},
                "scene3d": {"box": self._box(),
                            "units": "м", "objects": [], "layers": [], "planes": {"max": 0}},
                "modifications": SCHEMA.modifications(self.params)}, {}

    def engine_modules(self):
        return []

    def _box(self):
        zh = HALF if self.ndim == 3 else 0.2
        return [[-HALF, -HALF, -zh], [HALF, HALF, zh]]


VIZ = {"id": "p99_toy", "title": "Игрушка (тесты)", "summary": "", "purpose": "", "version": "1.1", "schema": SCHEMA,
       "simulation": Simulation, "kind": "playground", "section": "toy"}
