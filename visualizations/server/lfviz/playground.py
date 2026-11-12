# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""The playground (plan P15.0; owner, 2026-10-28): a research sandbox, one per section of physics.

A playground world starts empty or from a scene (a preset or a file) and is changed by hand at any moment: objects of
the section's palette are added, removed, duplicated and their parameters changed (command ``scene``), and the
section's solver advances everything from the engine's laws in real time. The rules of the demonstrations hold
(``RULES.md``): every visible consequence is computed by the run; the section's laws are world parameters (a changed
law starts a new world and is flagged); the scene's objects are the experimenter's set-up, changed at the current
moment and recorded with their time like every world-changing command (a restore repeats them).

A section subclasses ``PlaygroundSimulation`` and gives:

* ``PALETTE``: the object types it offers (``ObjectType``: a label, a kind, a schema of parameters), and the hooks
  ``on_add(obj, state)``, ``on_remove(obj)``, ``on_set(obj, old)``, ``object_state(obj)`` that create, drop and change
  an object's part of the solver (raise ``ValueError`` to refuse: the scene is then left as it was);
* ``frame()`` with the solver's state (and the probes' readings), the running checks of its conservation laws
  (``running_check``, emitted every ``CHECK_FRAMES`` frames: by frame count, so that a restored world emits the same);
* ``rekey()``: what a view needs to be drawn from this point on besides what the base repeats (the scene message and
  the latest value of every set-like message, ``SET_LIKE``: boxes, meshes, lines, marks, approximations, actions), e.g.
  the trails kept so far; emitted at the start of each segment of the record (``segment_start``, called by
  ``Runner.checkpoint``), so that a record kept only as a moving window (the buffer, ``runs.py``) can be shown from its
  first kept message. **It must not change the world's state** (a world restored by replay has no segment starts:
  review B6-F8). The base's repetitions carry ``repeat: true``: a viewer that has the same message already ignores
  them (review UX-ui U1: an unchanged ``box`` re-sent every minute reset the camera);
* optionally (the integrator's API of 2026-11-05 for reviews UX-ui U4, U7, U22 and UX-params P28):
  ``place(kind, values) -> values`` — called on every palette add with what the owner set in the pre-placement form
  (and ``position`` [x, y, z] when he clicked a point in the scene or its window); returns the completed values (e.g.
  moved to a free spot, a free side chosen) or raises ``lfviz.errors.Refusal``. Without it the values are used as they
  are, ``position`` going to the type's ``x``, ``y``, ``z``. ``palette_state() -> {kind: None | reason}`` — the palette
  types the world cannot take now and why (Russian, with what to change), sent in every ``scene`` message (after each
  change and in a new world); the player disables those buttons and shows the reason. ``can_remove(obj) -> None |
  reason`` — asked before a removal and for every object before «Очистить сцену» removes any, so that a refusal leaves
  the scene whole. All of them are deterministic (a restore repeats them), cheap, and never change the world's state.

Direct manipulation (plan P16.2; the integrator's API of 2026-11-11): a palette type may declare ``handles`` — the
object's own parameter ids that a drag in the player changes (``position``: 2 or 3 ids, ``velocity``: as many, optional;
``size``: the id of a radius or half-size, optional, for picking). The player sends one scene edit per release (``op``
edit {id, values}: only those parameters), applied through the same path as ``set`` (``on_set``, rolled back when it
raises). Every object with a position is reported in the frame's ``at[id]`` (world units) by the section. A section may
also give ``measurables()`` (plan P16.3): the quantities its instruments can record, sent in every ``scene`` message.

A new world that keeps the scene (plan P16.1, «перенести сцену»): ``new_world`` with ``carry`` puts the current world's
export (``carry_export``: the scene file's data with the objects' ids) into the new world's ``params["scene"]`` marked
``carry`` (``sim.Runner``); ``start_scene`` then re-adds each object through ``place`` and the add path, under its old id
(review LB1-F15), and skips those the new world refuses. The carried scene is part of the new world's parameters (its
header), so a restore rebuilds the same world.

The state that goes with it (review LB1-F5; the hooks announced to the sections on 2026-11-11). A scene file holds only
what ``object_state`` gives as JSON; sections whose state is large (atoms, a flow field, a wave) give it for a carry-over
through two optional hooks, and the framework says exactly what went how:

* ``carry_state() -> {"objects": {obj_id: state}, "world": state} | None`` (the old world): plain data with NumPy arrays
  at any depth (numeric or bool dtype; nothing else). The runner writes it once per carry into the run's folder
  (``carry-w<N>-<ns>.npz``: the arrays and a JSON skeleton, read with ``allow_pickle=False``, never pickled) and names
  the file with its SHA-256 in the new world's ``params["scene"]["carry_file"]``, so that a restore by replay reads the
  very same state. ``objects[id]`` replaces ``object_state`` for the carry only; ``on_add(obj, state)`` gets it.
* ``carry_world(state, laws)`` (the new world): called once after the carried objects were re-added, always in a carried
  world (``state`` None when the old world gave none; ``laws`` the old world's laws): take over the world's own state
  where the new laws allow; raise to start it afresh (the reason goes into the notice).
* ``carry_note(text, obj=None, restarted=False)`` (the framework's): from ``place``, ``on_add`` or ``carry_world`` during a
  carry, an adaptation of the carried state, or (``restarted``) a state that could not be taken and started afresh from
  the parameters. ``obj`` None means the object being carried (in ``place`` / ``on_add``) or the world (in
  ``carry_world``). ``self.carrying`` is the old world's laws during a carry, else None.

The notice of a carry (recorded, and shown) lists the objects carried with their state, those rebuilt from their
parameters (no state of their own: walls, probes; or a state not carried: said so, with the reason), the values the new
world changed (``place``, the schema) and the objects it refused, and the world's own state; its ``carry`` field holds
the same as data.

Messages besides the ``Simulation``'s: ``scene`` (the whole object list after every change and at each segment start:
a view is a function of the latest one and of the frame), ``scene_export`` (the scene as plain data, on request; the
server forwards it to the viewers and never records it). A scene file (``FORMAT``) holds the section, its laws (the
world parameters), the time and the objects with their parameters and their dynamic state as plain data; loading it
starts a world with ``params["scene"]``.
"""

from __future__ import annotations

import copy
import hashlib
import io
import json
import math
import os
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .errors import Refusal, owner_text
from .params import Param, Schema
from .sim import Simulation

FORMAT = "lfscene"
FORMAT_VERSION = 1

OBJ_ID = re.compile(r"^o[1-9]\d{0,8}$")  # an object's id as the framework gives it (kept by a carry: review LB1-F15)


# --- the state carried into a new world (review LB1-F5) ------------------------------------------------------------------
CARRY_NAME = re.compile(r"^carry-w\d+-\d+\.npz$")  # the only names a carried state's file may have
_carry_dir: Path | None = None  # the run's folder of saved states (set by the worker); None: kept in this process only
_carry_cache: dict = {}  # sha256 -> the decoded state (this process: the new world and a restore in it read no file)


def set_carry_dir(path) -> None:
    """Where this worker's carried states are written and read (the run's checkpoint folder)."""
    global _carry_dir
    _carry_dir = Path(path) if path else None


def pack_state(state) -> bytes:
    """A carried state as bytes: NumPy arrays (numeric or bool) into an .npz, the rest as a JSON skeleton in it. Only
    plain data (dict with str keys, list, tuple, str, int, float, bool, None, NumPy scalars) and arrays; anything else
    raises TypeError (a section's definition error)."""
    arrays = {}

    def walk(x):
        if isinstance(x, np.ndarray):
            if x.dtype.kind not in "biufc":
                raise TypeError(f"a carried array must be numeric or bool, not {x.dtype}")
            key = f"a{len(arrays)}"
            arrays[key] = np.ascontiguousarray(x)
            return {"__nd__": key}
        if isinstance(x, dict):
            if "__nd__" in x:
                raise TypeError("a carried dict may not use the key '__nd__'")
            if not all(isinstance(k, str) for k in x):
                raise TypeError("a carried dict needs string keys")
            return {k: walk(v) for k, v in x.items()}
        if isinstance(x, (list, tuple)):
            return [walk(v) for v in x]
        if isinstance(x, np.generic):
            return walk(x.item())
        if x is None or isinstance(x, (bool, int, float, str)):
            return x
        raise TypeError(f"a carried state holds {type(x).__name__}: only plain data and NumPy arrays")

    skel = json.dumps(walk(state), ensure_ascii=False, allow_nan=True).encode()
    buf = io.BytesIO()
    np.savez(buf, __json__=np.frombuffer(skel, np.uint8), **arrays)
    return buf.getvalue()


def unpack_state(data: bytes):
    """The state ``pack_state`` wrote (no pickles are read)."""
    with np.load(io.BytesIO(data), allow_pickle=False) as z:
        skel = json.loads(bytes(z["__json__"]).decode())
        arrays = {k: z[k] for k in z.files if k != "__json__"}

    def walk(x):
        if isinstance(x, dict):
            if set(x) == {"__nd__"}:
                return arrays[x["__nd__"]]
            return {k: walk(v) for k, v in x.items()}
        if isinstance(x, list):
            return [walk(v) for v in x]
        return x
    return walk(skel)


def store_carry(state, world: int, folder: Path | None = None) -> dict:
    """Keep a carried state for the new world ``world``: in this process, and as a file in ``folder`` (the run's) when
    there is one. Returns the reference the new world's parameters hold: {"file": name | None, "sha256", "bytes"}."""
    data = pack_state(state)
    sha = hashlib.sha256(data).hexdigest()
    _carry_cache[sha] = unpack_state(data)  # what a file would give (arrays as read back), not the old world's objects
    while len(_carry_cache) > 4:
        del _carry_cache[next(iter(_carry_cache))]
    folder = folder if folder is not None else _carry_dir
    name = None
    if folder is not None:
        name = f"carry-w{int(world)}-{time.time_ns()}.npz"
        folder.mkdir(parents=True, exist_ok=True)
        tmp = folder / (name + ".tmp")
        try:
            with open(tmp, "wb") as f:
                f.write(data)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, folder / name)
        except BaseException:
            tmp.unlink(missing_ok=True)
            raise
    return {"file": name, "sha256": sha, "bytes": len(data)}


def drop_carry(ref, folder: Path | None = None) -> None:
    """Remove a carried state's file (its new world was refused)."""
    folder = folder if folder is not None else _carry_dir
    if isinstance(ref, dict) and folder is not None and isinstance(ref.get("file"), str) and CARRY_NAME.match(ref["file"]):
        (folder / ref["file"]).unlink(missing_ok=True)


def prune_carry(world: int, folder: Path | None = None) -> None:
    """Remove the carried states of worlds before ``world``: only a run's latest world is ever restored."""
    folder = folder if folder is not None else _carry_dir
    if folder is None or not folder.is_dir():
        return
    for p in folder.glob("carry-w*-*.npz"):
        if CARRY_NAME.match(p.name) and int(p.name.split("-")[1][1:]) < int(world):
            p.unlink(missing_ok=True)


def load_carry(ref):
    """The carried state a new world's parameters name (``store_carry``'s reference): from this process, else from the
    run's folder, checked against its SHA-256. Raises ValueError (in Russian) when it is not there or not the same."""
    if not isinstance(ref, dict) or not isinstance(ref.get("sha256"), str):
        raise ValueError("ссылка на перенесённое состояние повреждена")
    sha = ref["sha256"]
    if sha in _carry_cache:
        return _carry_cache[sha]
    name = ref.get("file")
    if not isinstance(name, str) or not CARRY_NAME.match(name) or _carry_dir is None:
        raise ValueError("перенесённое состояние прежнего мира не сохранено в папке запуска — этот мир не восстановить")
    try:
        data = (_carry_dir / name).read_bytes()
    except OSError as e:
        raise ValueError(f"файл перенесённого состояния {name} не найден — этот мир не восстановить") from e
    if hashlib.sha256(data).hexdigest() != sha:
        raise ValueError(f"файл перенесённого состояния {name} изменён — этот мир не восстановить")
    _carry_cache[sha] = unpack_state(data)
    return _carry_cache[sha]


# --- numbers for the owner's texts (review LB1-p02-ux X6: one Russian format in the events and the player) ----------------
_SUP = str.maketrans("-0123456789", "⁻⁰¹²³⁴⁵⁶⁷⁸⁹")


def fmt(v, digits: int = 4) -> str:
    """A number as the player shows it (``ui.js`` ``num``): ``digits`` significant digits, a decimal comma, the minus
    sign −, and m·10ⁿ (a comma in m too) outside 10⁻⁴ … 10⁷."""
    try:
        x = float(v)
    except (TypeError, ValueError):
        return str(v)
    if math.isnan(x):
        return "—"
    if math.isinf(x):
        return "∞" if x > 0 else "−∞"
    a = abs(x)
    if a == 0:
        return "0"
    if a >= 1e7 or a < 1e-4:
        e = math.floor(math.log10(a))
        m = float(f"{x / 10 ** e:.{digits}g}")
        if abs(m) >= 10:  # rounded up to 10
            m, e = m / 10, e + 1
        return f"{m:.{digits}g}".replace(".", ",").replace("-", "−") + "·10" + str(e).translate(_SUP)
    s = repr(float(f"{x:.{digits}g}"))  # plain notation in this range
    s = s[:-2] if s.endswith(".0") else s
    whole, _, frac = s.lstrip("-").partition(".")
    if len(whole) >= 5:  # grouped as the player's ru-RU numbers (12 345)
        whole = f"{int(whole):,}".replace(",", " ")
    return ("−" if x < 0 else "") + whole + ("," + frac if frac else "")


def unit_of(p) -> str:
    """A parameter's unit: its ``unit``, else the one its label carries after a comma («Центр пакета: x, нм»)."""
    if p is None:
        return ""
    if getattr(p, "unit", ""):
        return p.unit
    m = re.search(r",\s*([^,(]+?)\s*(\(|$)", p.label or "")
    return m.group(1) if m else ""


HANDLE_KEYS = ("position", "velocity", "size", "velocity_max", "velocity_display")


AXES = ("x", "y", "z")


def axis_index(v) -> int | None:
    """The axis an axis handle's select names: "x" | "y" | "z", 0 | 1 | 2 or "0" | "1" | "2" (integrator, 2026-11-11:
    p03's piston uses the letters, p02's walls the numbers as text); None for anything else."""
    if isinstance(v, str):
        if v in AXES:
            return AXES.index(v)
        return int(v) if v in ("0", "1", "2") else None
    if isinstance(v, (int, float)) and not isinstance(v, bool) and v in (0, 1, 2):
        return int(v)
    return None


def check_handles(handles, schema: Schema, typ: str = "") -> dict:
    """A palette type's ``handles`` (API of 2026-11-11, §1): ``position`` 2 or 3 parameter ids, or (integrator,
    2026-11-11, for a piston) one coordinate along an axis, ``{"param": <scalar id>, "axis_param": <id of a select whose
    values are x, y, z, or 0, 1, 2 as numbers or as text>}``; ``velocity`` as many ids as a list position has (optional; not with the axis form);
    ``size`` one parameter id (optional, for picking); ``velocity_max`` (optional, with a velocity; integrator, 2026-11-11):
    the largest speed the world can carry, in world length per world time — a number, or the id of the object's own
    parameter that holds it (a throw is clamped to it); ``velocity_display`` (optional, with a velocity; integrator,
    2026-11-12, for p03 whose throws are in nm/s): {"unit": <text>, "factor": <positive number>} — the factor turns a
    velocity in world units into the unit shown in the throw's readout and the scene's log (the edit itself stays in world
    units). Every id a numeric parameter of the type (the axis a select). Raises ValueError (a definition error of the
    section, found when the palette is built)."""
    where = f"palette type {typ!r}: handles"
    if not isinstance(handles, dict) or not set(handles) <= set(HANDLE_KEYS):
        raise ValueError(f"{where} must be a dict with keys among {HANDLE_KEYS}")
    out = {}

    def numeric(pid, what):
        p = schema.by_id.get(pid) if isinstance(pid, str) else None
        if p is None or p.type not in ("float", "int"):
            raise ValueError(f"{where}: {what} {pid!r} is not a numeric parameter of the type")
        return pid

    pos = handles.get("position")
    if isinstance(pos, dict):
        if set(pos) != {"param", "axis_param"}:
            raise ValueError(f"{where}: an axis position is {{'param': <id>, 'axis_param': <id>}}")
        ax = schema.by_id.get(pos["axis_param"]) if isinstance(pos["axis_param"], str) else None
        if ax is None or ax.type != "select" or not ax.options or not all(axis_index(o[0]) is not None for o in ax.options):
            raise ValueError(f"{where}: axis_param {pos['axis_param']!r} is not a select of the axes x, y, z (or 0, 1, 2)")
        out["position"] = {"param": numeric(pos["param"], "position"), "axis_param": pos["axis_param"]}
        if handles.get("velocity") is not None:
            raise ValueError(f"{where}: an axis position takes no velocity")
    elif pos is not None:
        if not isinstance(pos, (list, tuple)) or len(pos) not in (2, 3):
            raise ValueError(f"{where}: position must list 2 or 3 parameter ids")
        out["position"] = [numeric(k, "position") for k in pos]
    vel = handles.get("velocity")
    if vel is not None:
        if not isinstance(out.get("position"), list) or not isinstance(vel, (list, tuple)) \
                or len(vel) != len(out["position"]):
            raise ValueError(f"{where}: velocity must list as many ids as position (and needs a position)")
        out["velocity"] = [numeric(k, "velocity") for k in vel]
    if handles.get("size") is not None:
        out["size"] = numeric(handles["size"], "size")
    vm = handles.get("velocity_max")
    if vm is not None:  # the largest speed the world can carry (integrator, 2026-11-11): a number or a parameter's id
        if "velocity" not in out:
            raise ValueError(f"{where}: velocity_max needs a velocity")
        if isinstance(vm, str):
            out["velocity_max"] = numeric(vm, "velocity_max")
        elif isinstance(vm, (int, float)) and not isinstance(vm, bool) and math.isfinite(vm) and vm > 0:
            out["velocity_max"] = float(vm)
        else:
            raise ValueError(f"{where}: velocity_max must be a positive number or a parameter id")
    vd = handles.get("velocity_display")
    if vd is not None:
        if "velocity" not in out:
            raise ValueError(f"{where}: velocity_display needs a velocity")
        f = vd.get("factor") if isinstance(vd, dict) else None
        if not isinstance(vd, dict) or set(vd) != {"unit", "factor"} or not isinstance(vd["unit"], str) \
                or not vd["unit"].strip() or len(vd["unit"]) > 24 or isinstance(f, bool) \
                or not isinstance(f, (int, float)) or not math.isfinite(f) or f <= 0:
            raise ValueError(f"{where}: velocity_display is {{'unit': <short text>, 'factor': <positive number>}}")
        out["velocity_display"] = {"unit": vd["unit"].strip(), "factor": float(f)}
    ids = handle_ids(out)
    if len(set(ids)) != len(ids):
        raise ValueError(f"{where}: a parameter is named twice")
    return out


def handle_ids(handles: dict | None) -> list[str]:
    """The parameters a scene edit (``op`` edit) may change: the position's (the axis form: its coordinate, not its
    axis) and the velocity's."""
    h = handles or {}
    pos = h.get("position") or []
    return ([pos["param"]] if isinstance(pos, dict) else list(pos)) + list(h.get("velocity") or [])


@dataclass
class ObjectType:
    """An entry of a section's palette: what kind of object it is and its parameters (all changeable at any moment).
    ``handles``: the parameters a drag in the player changes (``check_handles``; plan P16.2)."""
    type: str
    label: str
    kind: str  # body | particle | light | field | potential | detector | probe | observer | source
    schema: Schema
    help: str = ""
    limit: int | None = None  # at most this many of the type in a scene
    color: str = "#868e96"
    handles: dict | None = None
    #: whether its objects have a dynamic state beyond their parameters (a carry-over says whether that state went with
    #: them: review LB1-F5); None: those with a velocity handle do
    stateful: bool | None = None

    def __post_init__(self):
        if self.handles is not None:
            self.handles = check_handles(self.handles, self.schema, self.type)

    def has_state(self) -> bool:
        return bool(self.stateful) if self.stateful is not None else bool((self.handles or {}).get("velocity"))

    def handle_ids(self) -> list[str]:
        """The parameters a scene edit (``op`` edit) may change: the position's and the velocity's."""
        return handle_ids(self.handles)

    def to_json(self) -> dict:
        return {"type": self.type, "label": self.label, "kind": self.kind, "help": self.help, "limit": self.limit,
                "color": self.color, "params": [p.to_json() for p in self.schema.params],
                **({"handles": self.handles} if self.handles else {})}


T_MAX = 1e30  # the latest time a scene file may start at (s)


def check_scene(scene, viz_id: str, carried_ok: bool = False) -> None:
    """A scene file's form (it may come from anywhere: review B6-F17): an object of this section and format, objects a
    list of objects with a string type, the time a finite number in [0, T_MAX]. A file never names a carried state
    (``carry_file``: only a new world made by the runner does, ``carried_ok``). Raises ValueError with the reason."""
    if not isinstance(scene, dict):
        raise ValueError("файл сцены — объект JSON")
    if "carry_file" in scene and not carried_ok:
        raise ValueError("файл сцены не может ссылаться на перенесённое состояние другого мира")
    if scene.get("format", FORMAT) != FORMAT or not isinstance(scene.get("version", FORMAT_VERSION), int) \
            or int(scene.get("version", FORMAT_VERSION)) > FORMAT_VERSION:
        raise ValueError("это не файл сцены этого плейграунда (или более новой версии)")
    if scene.get("viz") not in (None, viz_id):
        raise ValueError(f"сцена другого раздела ({scene.get('viz')}), а это {viz_id}")
    objs = scene.get("objects", [])
    if not isinstance(objs, list) or not all(isinstance(o, dict) and isinstance(o.get("type"), str) for o in objs):
        raise ValueError("объекты сцены — список объектов с полем type")
    for o in objs:
        if not isinstance(o.get("values", {}), dict) or not isinstance(o.get("state") or {}, dict):
            raise ValueError("значения и состояние объекта — объекты JSON")
    t = scene.get("t", 0.0)
    if t is None:
        t = 0.0
    if isinstance(t, bool) or not isinstance(t, (int, float)) or not (0.0 <= float(t) <= T_MAX):
        raise ValueError(f"время сцены — число от 0 до {T_MAX:g} с")


def scene_time(params: dict) -> float:
    """The time a world built from ``params["scene"]`` starts at (0 without a scene)."""
    sc = params.get("scene")
    return float(sc.get("t") or 0.0) if isinstance(sc, dict) else 0.0


def scene_param(help_text: str = "") -> Param:
    """The world parameter that carries a scene to start from (a preset's or a loaded file's); hidden in the forms."""
    return Param("scene", "Начальная сцена", "json", None, group="Сцена", hidden=True,
                 help=help_text or "Объекты, с которых начинается мир (сценарий или загруженный файл сцены)")


class PlaygroundSimulation(Simulation):
    #: the section's palette: object type -> ObjectType
    PALETTE: dict = {}
    #: the visualization id of the section (the scene file names it)
    VIZ_ID: str = ""
    MAX_OBJECTS = 300
    #: frames between two emissions of the running checks (by count: the same in a restored world)
    CHECK_FRAMES = 20
    #: wall seconds between checkpoints while computing: the segments of a buffered record (``Runner.checkpoint``);
    #: LFVIZ_PLAYGROUND_CKPT shortens it for the tests (the key-frame browser check crosses segments: review B6-F23)
    checkpoint_every = float(os.environ.get("LFVIZ_PLAYGROUND_CKPT", "60"))

    #: message types whose latest value a view holds (set, not accumulated): repeated at every segment start, with
    #: any message carrying ``approximations`` (review B6-F4: a segment must be drawable on its own)
    SET_LIKE = ("box", "mesh", "lines", "marks", "shapes", "actions", "approx", "arrow", "volume", "target")

    def __init__(self, params: dict, seed: int, emit):
        super().__init__(params, seed, emit)
        self.objects: dict[str, dict] = {}
        self.next_id = 1
        self.rev = 0
        self.n_frames = 0
        self._loading = False
        # messages a section emits while its world is built (its initial scene) wait for the header (after_header)
        self._emit_real = emit
        self._held: list | None = []
        self._latest: dict = {}  # (type, id) -> the latest set-like message and its blobs
        self._starting: set | None = None  # the keys emitted during a segment start
        self.emit = self._out
        self.carrying: dict | None = None  # the previous world's laws while its scene is carried in (review LB1-F5)
        self._carry_log: dict | None = None  # what the section said during a carry: key (index or "world") -> notes

    # --- the section's hooks -------------------------------------------------------------------------------------
    def on_add(self, obj: dict, state: dict | None) -> None:
        """Create the object's part of the solver (``state``: its dynamic state from a file or a duplicate)."""

    def on_remove(self, obj: dict) -> None:
        """Drop the object's part of the solver."""

    def on_set(self, obj: dict, old: dict) -> None:
        """The object's parameters changed (``obj["values"]`` new, ``old`` before): apply at the current moment."""

    def object_state(self, obj: dict) -> dict | None:
        """The object's dynamic state as plain data (positions, velocities; for files and duplicates), or None."""
        return None

    def rekey(self) -> None:
        """Emit what a view needs from this point on besides the scene message (e.g. full trails)."""

    def place(self, kind: str, values: dict) -> dict:
        """Complete the values of a new object of palette type ``kind`` before it is added: ``values`` are what the
        owner set in the pre-placement form, with ``position`` [x, y, z] when he clicked a point. Return the values to
        add (moved to a free spot, a free side chosen; ``position`` may be left: the framework maps it to x, y, z) or
        raise ``lfviz.errors.Refusal``. Deterministic: a restore repeats it."""
        return values

    def palette_state(self) -> dict:
        """{palette type: None, or why the world cannot take it now} (Russian, with what to change: «нужны стенки:
        Новый мир → Границы»); the player disables those buttons with the reason. Cheap; never changes the world."""
        return {}

    def can_remove(self, obj: dict) -> str | None:
        """Why ``obj`` cannot be removed now (Russian), or None. Asked before a removal and for every object before
        «Очистить сцену» removes any, so that a refusal leaves the scene whole."""
        return None

    def carry_state(self) -> dict | None:
        """The dynamic state a carry-over takes into a new world beyond ``object_state`` (review LB1-F5): {"objects":
        {obj_id: state}, "world": state}, plain data and NumPy arrays (``pack_state``); stored with the run, never in a
        scene file. ``objects[id]`` replaces ``object_state`` for the carry. Never changes the world. None: nothing more."""
        return None

    def carry_world(self, state, laws: dict) -> None:
        """Take over the previous world's own state (``carry_state()["world"]`` of that world; None when it gave none;
        ``laws``: its laws) after the carried objects were re-added: called once in every carried world. Say what was
        adapted, or what starts afresh, with ``carry_note``; raise to start the world's own state afresh (the reason
        goes into the notice). Deterministic (a restore repeats it)."""

    def carry_note(self, text: str, obj: dict | None = None, restarted: bool = False) -> None:
        """During a carry-over (``place``, ``on_add``, ``carry_world``): what the new world did with the carried state —
        an adaptation, or (``restarted``) a state it could not take and started afresh from the parameters. ``obj`` None:
        the object being carried, or the world in ``carry_world``. Outside a carry nothing happens."""
        log = self._carry_log
        if log is None or not str(text).strip():
            return
        key = log["current"] if obj is None else log["by_id"].get(obj.get("id"), log["current"])
        log["notes"].setdefault(key, []).append(("restarted" if restarted else "adapted", str(text).strip()))

    def measurables(self) -> list:
        """The quantities the instruments can record (plan P16.3; the integrator's API of 2026-11-11, §2): a list of
        {"id", "label" (Russian), "unit" (Russian, display), "of": an object id or None for the world, "group"?}. Sent
        in every ``scene`` message (after each change, in a new world, at each segment start); every frame then carries
        their values in ``meas`` ({id: number}, NaN with the reason in ``meas_note`` when undefined). Cheap,
        deterministic, never changes the world."""
        return []

    # --- the scene ------------------------------------------------------------------------------------------------
    def start_scene(self) -> None:
        """Build the initial scene from ``params["scene"]`` (a preset's or a file's); call at the end of __init__."""
        scene = self.params.get("scene")
        if not scene:
            return
        check_scene(scene, self.VIZ_ID, carried_ok=True)
        self.t = scene_time(self.params)
        if scene.get("carry"):
            self._carry_scene(scene)
            return
        self._loading = True
        try:
            for o in scene.get("objects") or []:
                self._add(o.get("type"), o.get("values") or {}, o.get("state"), o.get("label"), oid=o.get("id"))
        finally:
            self._loading = False

    def carry_export(self) -> tuple[dict, dict | None]:
        """What a carry-over takes from this world (``sim.Runner._new_world``): the scene as a file has it, with the
        objects' ids, as plain data; and the heavy state of ``carry_state`` (None when there is none), whose objects' entries
        replace their ``object_state`` in the scene."""
        scene = plain(self.export_message()[0]["scene"])
        cs = self.carry_state()
        if cs is None:
            return scene, None
        if not isinstance(cs, dict) or not set(cs) <= {"objects", "world"} \
                or not isinstance(cs.get("objects") or {}, dict):
            raise TypeError("carry_state() must return {'objects': {id: state}, 'world': state} or None")
        heavy = {}
        objs = {k: v for k, v in (cs.get("objects") or {}).items() if k in self.objects and v is not None}
        if objs:
            heavy["objects"] = objs
            for o in scene["objects"]:
                if o.get("id") in objs:
                    o.pop("state", None)
        if cs.get("world") is not None:
            heavy["world"] = cs["world"]
        return scene, (heavy or None)

    def _carry_scene(self, scene: dict) -> None:
        """The scene of the previous world carried into this one (plan P16.1; ``new_world`` with ``carry``): each
        object re-added under its id through ``place`` and the add path, in the scene's order, with its state (the
        scene's, or the carried file's); an object this world refuses (a type it has not, a value its laws exclude, a
        state its solver cannot take) is skipped; then the world's own state (``carry_world``). One notice says what
        went how (review LB1-F5). The carried scene is this world's parameter, so a restore repeats exactly the same
        (``place``, ``on_add`` and ``carry_world`` are deterministic; the carried file is the same file)."""
        objs = scene.get("objects") or []
        heavy = load_carry(scene["carry_file"]) if scene.get("carry_file") else {}
        heavy_objs = (heavy or {}).get("objects") or {}
        laws = dict(scene.get("laws") or {})
        self._carry_log = log = {"current": None, "by_id": {}, "notes": {}}
        self.carrying = laws
        rows, world = [], {"how": "none", "notes": []}
        self._loading = True
        try:
            for i, o in enumerate(objs):
                label = str(o.get("label") or o.get("type"))[:80]
                was = o.get("id") if isinstance(o.get("id"), str) else None
                st = o.get("state") if o.get("state") is not None else heavy_objs.get(was) if was else None
                row = {"id": was, "label": label, "how": "refused", "notes": [], "changed": {}}
                rows.append(row)
                log["current"] = i
                try:
                    ot = self._type(o.get("type"))
                    sent = dict(o.get("values") or {})
                    values = self._placed(o["type"], ot, dict(sent))
                    obj = self._add(o["type"], values, st, o.get("label"), oid=was)
                except Exception as e:  # noqa: BLE001 - a refused object is skipped and named, the rest goes on
                    row["notes"] = [("refused", owner_text(e)[0])]
                    continue
                log["by_id"][obj["id"]] = i
                hidden = {p.id for p in ot.schema.params if getattr(p, "hidden", False)}
                row.update(new_id=obj["id"], label=obj["label"], changed=_changed(sent, obj["values"], hidden))
                said = log["notes"].get(i, [])
                row["notes"] = said
                if st is not None and not any(k == "restarted" for k, _ in said):
                    row["how"] = "state"
                elif ot.has_state() or st is not None:
                    row["how"] = "restarted"
                else:
                    row["how"] = "params"
            log["current"] = "world"
            try:
                self.carry_world((heavy or {}).get("world"), laws)
            except Exception as e:  # noqa: BLE001 - the world's own state starts afresh, said in the notice
                log["notes"].setdefault("world", []).append(("restarted", f"начато заново — {owner_text(e)[0]}"))
            said = log["notes"].get("world", [])
            world = {"how": ("restarted" if any(k == "restarted" for k, _ in said) else
                             "state" if (heavy or {}).get("world") is not None else "none"), "notes": said}
        finally:
            self._loading = False
            self._carry_log = None
            self.carrying = None
        text, data = _carry_report(objs, rows, world, self.t)
        self.emit({"type": "notice", "t": self.t, "text": text, "carried": sum(r["how"] != "refused" for r in rows),
                   "not_carried": sum(r["how"] == "refused" for r in rows), "carry": data})

    def _type(self, name) -> ObjectType:
        if name not in self.PALETTE:
            raise ValueError(f"в этом разделе нет объектов «{name}»")
        return self.PALETTE[name]

    def _values(self, ot: ObjectType, values: dict) -> dict:
        v, errors = ot.schema.resolve(None, values)
        if errors:
            raise ValueError("; ".join(errors))
        return v

    def _add(self, typ, values: dict, state: dict | None = None, label: str | None = None, oid=None) -> dict:
        """Add an object; ``oid``: the id it had (a carried scene or a file: review LB1-F15), kept when it is a free id
        of the framework's form, else a new one is given."""
        ot = self._type(typ)
        if len(self.objects) >= self.MAX_OBJECTS:
            raise ValueError(f"в сцене уже {self.MAX_OBJECTS} объектов: больше нельзя")
        if ot.limit is not None and sum(1 for o in self.objects.values() if o["type"] == typ) >= ot.limit:
            raise ValueError(f"«{ot.label}»: не больше {ot.limit} в сцене")
        keep = isinstance(oid, str) and OBJ_ID.match(oid) and oid not in self.objects
        if not keep:
            while f"o{self.next_id}" in self.objects:
                self.next_id += 1
            oid = f"o{self.next_id}"
        n = sum(1 for o in self.objects.values() if o["type"] == typ) + 1
        obj = {"id": oid, "type": typ, "kind": ot.kind, "label": str(label or f"{ot.label} {n}")[:80],
               "values": self._values(ot, values), "t_added": self.t}
        self.on_add(obj, state)  # raises: nothing was added
        self.objects[oid] = obj
        self.next_id = max(self.next_id, int(oid[1:]) + 1)
        return obj

    def scene(self, args: dict) -> str:
        """A change of the scene at the current moment (command ``scene``): ``op`` add {type, values, state?, label?},
        remove {id}, set {id, values}, edit {id, values} (a drag: the type's handles only), duplicate {id, values?},
        label {id, label}, clear, or export (the scene as a file, not a change). Returns the log line; a refused change
        raises and leaves the scene as it was."""
        op = args.get("op")
        if op == "export":
            self.emit(*self.export_message())
            return ""
        if op == "add":
            typ = args.get("type")
            ot = self._type(typ)
            values = self._placed(typ, ot, dict(args.get("values") or {}))
            obj = self._add(typ, values, args.get("state"), args.get("label"))
            text = f"добавлен объект «{obj['label']}»"
        elif op == "duplicate":
            src = self._obj(args.get("id"))
            values = {**src["values"], **(args.get("values") or {})}
            obj = self._add(src["type"], values, self.object_state(src), args.get("label") or f"{src['label']} (копия)")
            text = f"«{obj['label']}» — копия «{src['label']}»"
        elif op == "remove":
            obj = self._obj(args.get("id"))
            why = self.can_remove(obj)
            if why:
                raise ValueError(f"«{obj['label']}» сейчас удалить нельзя: {why}")
            self.on_remove(obj)
            del self.objects[obj["id"]]
            text = f"удалён объект «{obj['label']}»"
        elif op == "set":
            obj = self._obj(args.get("id"))
            ot = self._type(obj["type"])
            old = copy.deepcopy(obj["values"])
            new = self._values(ot, {**old, **(args.get("values") or {})})
            changed = {k: v for k, v in new.items() if old.get(k) != v}
            if not changed:
                return ""
            obj["values"] = new
            try:
                self.on_set(obj, old)
            except Exception:
                obj["values"] = old
                raise
            text = f"«{obj['label']}»: " + "; ".join(_setting(ot.schema.by_id.get(k), k, v) for k, v in changed.items())
        elif op == "edit":
            text = self._edit(args)
            if not text:
                return ""
        elif op == "label":
            obj = self._obj(args.get("id"))
            obj["label"] = str(args.get("label") or obj["label"])[:80]
            text = f"переименован объект: «{obj['label']}»"
        elif op == "clear":
            # every object is asked first: a refused clear leaves the scene whole (review UX-params P28)
            why = [(o["label"], self.can_remove(o)) for o in self.objects.values()]
            why = [f"«{lab}»: {w}" for lab, w in why if w]
            if why:
                raise ValueError("сцену очистить нельзя — " + "; ".join(why) + ". Удалите сначала то, что мешает")
            for obj in list(self.objects.values()):
                self.on_remove(obj)
                del self.objects[obj["id"]]
            text = "сцена очищена"
        else:
            raise ValueError(f"неизвестная операция со сценой {op!r}")
        self.rev += 1
        self.emit_scene()
        return text

    def _edit(self, args: dict) -> str:
        """A drag in the player (plan P16.2): the object's position and, for a throw, its velocity — only the parameters
        its type declares as ``handles`` — applied at the current moment through the path of ``set`` (``on_set``;
        rolled back when the section refuses). Every parameter sent is applied, even with its stored value (``old``
        then holds None for it). Returns the log line."""
        obj = self._obj(args.get("id"))
        ot = self._type(obj["type"])
        allowed = ot.handle_ids()
        vals = args.get("values")
        if not allowed:
            raise Refusal(f"«{obj['label']}» нельзя перетаскивать: у объекта этого типа нет положения, которое можно "
                          f"двигать рукой", hint="меняйте его параметры в инспекторе")
        if not isinstance(vals, dict) or not vals:
            raise ValueError(f"«{obj['label']}»: перетаскивание без новых значений")
        extra = [k for k in vals if k not in allowed]
        if extra:
            raise Refusal(f"«{obj['label']}»: перетаскивание меняет только положение и скорость, а не "
                          + ", ".join(f"«{_label(ot, k)}»" for k in extra),
                          hint="остальные параметры меняйте в инспекторе")
        old = copy.deepcopy(obj["values"])
        new = self._values(ot, {**old, **vals})
        h = ot.handles or {}
        clamped = self._clamp_throw(h, new, vals)
        # every handle sent is applied, also one equal to its stored value: the stored position of a moving object is
        # where it was set, not where it is now. The section's on_set sees such a parameter as changed: its value in
        # ``old`` is None ("applied again")
        changed = {k: new[k] for k in vals}
        seen = {k: (None if k in vals and old.get(k) == new[k] else v) for k, v in old.items()}
        obj["values"] = new
        try:
            self.on_set(obj, seen)
        except Exception:
            obj["values"] = old
            raise
        pos, vel = h.get("position") or [], h.get("velocity") or []
        axis = None
        if isinstance(pos, dict):
            ai = axis_index(new.get(pos["axis_param"]))
            axis = AXES[ai] if ai is not None else None
            pos = [pos["param"]]
        # the log line in the short form of the player (review LB1-F13, LB1-p02-ux X12): the numbers with the unit of
        # the parameters, no labels inside the brackets, a noun (no participle to agree with the object's gender)
        parts = []
        if any(k in changed for k in pos):
            parts.append(f"перемещение: {axis} = {_vec(ot, new, pos)}" if axis else f"перемещение в {_vec(ot, new, pos)}")
        vd = h.get("velocity_display")  # the throw in the unit the type shows (the edit stays in world units)
        if any(k in changed for k in vel):
            parts.append(f"бросок: v = {_vec(ot, new, vel, vd)}")
        # the player clamps the hand's speed already and says what it gave (``asked``); the world clamps too (a REST
        # edit). A clamp is said only when one happened: here, or in the player (the speed sent is the largest one and
        # the hand's was more); ``asked`` is a finite positive number or ignored
        asked = args.get("asked")
        asked = float(asked) if isinstance(asked, (int, float)) and not isinstance(asked, bool) \
            and math.isfinite(asked) and asked > 0 else None
        vm = self._velocity_max(h, new)
        if vm and any(k in changed for k in vel):
            sent = math.sqrt(sum(float(new[k]) ** 2 for k in vel))
            # what the hand gave: the player's ``asked`` when it clamped (its rounded speed may be clamped here again by
            # a hair), else the speed this edit sent
            gave = asked if (asked is not None and asked > vm and (clamped or abs(sent - vm) <= 2e-3 * vm)) \
                else clamped[0] if clamped else None
            if gave is not None:
                u = vd["unit"] if vd else unit_of(ot.schema.by_id.get(vel[0]))
                k = vd["factor"] if vd else 1.0
                parts[-1] += (f" — ограничено наибольшей скоростью {fmt(vm * k)}{' ' + u if u else ''} (рука дала "
                              f"{fmt(gave * k)}; уменьшите масштаб броска)")
        return f"«{obj['label']}»: " + "; ".join(parts)

    @staticmethod
    def _velocity_max(h: dict, values: dict) -> float | None:
        vm = h.get("velocity_max")
        if vm is None:
            return None
        v = float(values[vm]) if isinstance(vm, str) else float(vm)
        return v if math.isfinite(v) and v > 0 else None

    def _clamp_throw(self, h: dict, new: dict, sent: dict):
        """A throw faster than the type's ``velocity_max`` is clamped to it (its direction kept): (the speed sent, the
        largest one) when it was, else None."""
        vel = h.get("velocity") or []
        vm = self._velocity_max(h, new)
        if not vm or not any(k in sent for k in vel):
            return None
        speed = math.sqrt(sum(float(new[k]) ** 2 for k in vel))
        if speed <= vm:
            return None
        for k in vel:
            new[k] = float(new[k]) * vm / speed
        return speed, vm

    def _placed(self, typ: str, ot: ObjectType, values: dict) -> dict:
        """A new object's values after the section's ``place``; ``position`` left by it as a clicked point (a list of 2
        or 3 numbers) goes to the type's x, y, z parameters (review UX-ui U4). Any other ``position`` is the type's own
        parameter (p03's piston has a scalar one) and is kept as it is."""
        values = self.place(typ, values)
        if not isinstance(values, dict):
            raise ValueError("раздел вернул не значения объекта")
        pos = values.get("position")
        if _is_point(pos):
            del values["position"]
            for k, v in zip(("x", "y", "z"), pos):
                if k in ot.schema.by_id and k not in values and v is not None:
                    values[k] = v
        return values

    def _obj(self, oid) -> dict:
        if oid not in self.objects:
            raise ValueError(f"в сцене нет объекта {oid!r}")
        return self.objects[oid]

    def scene_meta(self) -> dict:
        meta = {"type": "scene", "t": self.t, "rev": self.rev,
                "objects": [{k: o[k] for k in ("id", "type", "kind", "label", "values", "t_added")}
                            for o in self.objects.values()]}
        # the palette types the world cannot take now, with the reason: the player disables those buttons (U7, U22)
        try:
            st = {str(k): str(v) for k, v in (self.palette_state() or {}).items() if v}
        except Exception:  # noqa: BLE001 - a hint must never break the scene message
            st = {}
        if st:
            meta["palette_state"] = st
        ms = self._measurables()
        if ms:
            meta["measurables"] = ms
        return meta

    def _measurables(self) -> list:
        """The section's ``measurables()`` in the API's form; an entry that is not is dropped (said in the worker's log),
        and a failure never breaks the scene message."""
        try:
            raw = self.measurables() or []
        except Exception as e:  # noqa: BLE001 - instruments must never break the scene
            print(f"lfviz.playground: measurables() failed: {type(e).__name__}: {e}", file=sys.stderr)
            return []
        out = []
        for m in raw:
            ok = (isinstance(m, dict) and isinstance(m.get("id"), str) and isinstance(m.get("label"), str)
                  and isinstance(m.get("unit", ""), str) and (m.get("of") is None or isinstance(m.get("of"), str))
                  and isinstance(m.get("group", ""), str))
            if not ok:
                print(f"lfviz.playground: measurable dropped (not id/label/unit/of/group): {m!r}"[:300], file=sys.stderr)
                continue
            out.append({"id": m["id"], "label": m["label"], "unit": m.get("unit", ""), "of": m.get("of"),
                        **({"group": m["group"]} if m.get("group") else {})})
        return out

    def emit_scene(self) -> None:
        self.emit(self.scene_meta())

    def export_message(self) -> tuple[dict, dict]:
        """The scene as a file (``FORMAT``): the section, its laws, the time and the objects with their parameters and
        dynamic state; blobs none (the state is plain JSON)."""
        # the laws in force: live ones as they are now (integrator, 2026-11-05: playgrounds' live laws)
        laws = {k: v for k, v in {**self.params, **(self.live_values() or {})}.items() if k != "scene"}
        objs = []
        for o in self.objects.values():
            st = self.object_state(o)
            objs.append({"id": o["id"], "type": o["type"], "label": o["label"], "values": o["values"],
                         **({"state": st} if st is not None else {})})
        return {"type": "scene_export", "t": self.t,
                "scene": {"format": FORMAT, "version": FORMAT_VERSION, "viz": self.VIZ_ID, "laws": laws,
                          "t": self.t, "objects": objs}}, {}

    def playground_header(self) -> dict:
        """The part of the header a playground view needs: the palette and the limits."""
        return {"viz": self.VIZ_ID, "palette": [ot.to_json() for ot in self.PALETTE.values()],
                "max_objects": self.MAX_OBJECTS}

    def _out(self, meta, blobs=None):
        """Every message of the world: held until the header, the latest set-like ones remembered."""
        if self._held is not None:
            self._held.append((meta, blobs))
            return
        typ = meta.get("type")
        if typ in self.SET_LIKE or isinstance(meta.get("approximations"), list):
            key = (typ, meta.get("id"))
            self._latest[key] = (meta, blobs)
            if self._starting is not None:
                self._starting.add(key)
        self._emit_real(meta, blobs)

    def after_header(self) -> None:
        held, self._held = self._held or [], None
        for meta, blobs in held:
            self.emit(meta, blobs)
        self.emit_scene()

    def segment_start(self) -> None:
        """A new segment of the record (``Runner.checkpoint``): the scene, the section's ``rekey`` and the latest value of
        every set-like message not emitted again by them, at the current time — so that a viewer of the segment alone
        draws the world as it is (review B6-F4)."""
        self._starting = set()
        try:
            self.emit({**self.scene_meta(), "repeat": True})
            self.rekey()
            for key, (meta, blobs) in list(self._latest.items()):
                if key not in self._starting:
                    # marked: a viewer holding the same message already ignores it (review UX-ui U1)
                    self._emit_real({**meta, **({"t": self.t} if "t" in meta else {}), "repeat": True}, blobs)
        finally:
            self._starting = None

    # --- running checks ----------------------------------------------------------------------------------------
    def check_due(self) -> bool:
        """Count a frame; True every ``CHECK_FRAMES`` frames (the running checks are emitted then)."""
        self.n_frames += 1
        return self.n_frames % self.CHECK_FRAMES == 1

    def running_check(self, cid: str, label: str, value, ref, tol: float, unit: str = "", note: str = "",
                      group: str = "Законы сохранения", ok: bool | None = None, info: bool = False,
                      expected: str = "") -> None:
        """``expected``: why a failure of this check is expected here (a «what if» law, a scene outside an
        approximation): the player draws such a failure as expected, with the reason (review UX-params P23)."""
        rel = None
        if ref is not None and value is not None and ref != 0:
            rel = (value - ref) / abs(ref)
        d = {"type": "check", "t": self.t, "id": cid, "label": label, "value": value, "ref": ref, "unit": unit,
             "rel": rel, "group": group, "note": note, "tol": tol}
        if ok is not None:
            d["ok"] = bool(ok)
        if info:
            d["info"] = True
        if expected:
            d["expected"] = str(expected)
        self.emit(d)


def _is_point(v) -> bool:
    """A point clicked in the scene: a list or tuple of 2 or 3 numbers (not a parameter's own scalar value)."""
    return isinstance(v, (list, tuple)) and 2 <= len(v) <= 3 and all(
        isinstance(c, (int, float)) and not isinstance(c, bool) for c in v)


def _g(v) -> str:
    """A number for the scene's log (the player's Russian format: ``fmt``)."""
    return fmt(v)


def _setting(p, pid: str, v) -> str:
    """«label = value unit» for the log (review LB1-p02-ux X12): the label without its explanation in brackets, a
    select by its option's name, a number in the player's format with the unit when the label does not carry it."""
    if p is None:
        return f"{pid} = {v}"
    lab = re.sub(r"\s*\([^()]*\)\s*$", "", p.label or pid).strip() or pid
    if p.type == "select":
        name = next((o[1] for o in (p.options or []) if o[0] == v), v)
        return f"{lab}: {name}"
    if p.type == "bool":
        return f"{lab}: {'да' if v else 'нет'}"
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        u = p.unit if p.unit and p.unit not in lab else ""
        return f"{lab} = {fmt(v)}" + (f" {u}" if u else "")
    return f"{lab} = {v}"


def _vec(ot: ObjectType, values: dict, ids: list, display: dict | None = None) -> str:
    """Handle values for the log: «(−10,81; 8,378) нм» when they share a unit, else each with its own; ``display``
    ({unit, factor}: a type's ``velocity_display``) shows them in that unit."""
    if display:
        body = "; ".join(fmt(float(values[k]) * display["factor"]) for k in ids)
        return (f"({body})" if len(ids) > 1 else body) + f" {display['unit']}"
    units = [unit_of(ot.schema.by_id.get(k)) for k in ids]
    if len(set(units)) == 1:
        body = "; ".join(fmt(values[k]) for k in ids)
        return (f"({body})" if len(ids) > 1 else body) + (f" {units[0]}" if units[0] else "")
    return "(" + "; ".join(fmt(values[k]) + (f" {u}" if u else "") for k, u in zip(ids, units)) + ")"


def _close(a, b) -> bool:
    if isinstance(a, bool) or isinstance(b, bool) or not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        return a == b
    return a == b or abs(a - b) <= 1e-9 * max(abs(a), abs(b))


def _blank(v) -> bool:
    return v is None or v == "" or v is False or (isinstance(v, (int, float)) and not isinstance(v, bool) and v == 0)


def _changed(sent: dict, now: dict, hidden: set | frozenset = frozenset()) -> dict:
    """The carried values the new world changed (``place``, its schema): {param: [carried, now]}; a parameter the new
    world has not, with a value that was not zero or empty, as [carried, None] (dropped). Hidden parameters (set by the
    world itself, e.g. p02's recomputed ``v_max``) are not the owner's values and are left out (review LB1-p02-ux,
    the p02 processing's note)."""
    out = {}
    for k, v in sent.items():
        if k == "position" and _is_point(v):
            continue
        if k in hidden:
            continue
        if k in now:
            if not _close(v, now[k]):
                out[k] = [v, now[k]]
        elif not _blank(v):
            out[k] = [v, None]
    return out


def _names(rows) -> str:
    return ", ".join(f"«{r['label']}»" for r in rows)


def _carry_report(objs: list, rows: list, world: dict, t_now: float) -> tuple[str, dict]:
    """The notice of a carry-over (review LB1-F5): what went with its state, what was rebuilt from its parameters (no
    state of its own; a state not carried, with the reason), what the new world changed, what it refused, and the world's
    own state. Returns the text and the same as data."""
    by = {k: [r for r in rows if r["how"] == k] for k in ("state", "params", "restarted", "refused")}
    note = lambda r: "; ".join(x for _, x in r["notes"])  # noqa: E731
    parts = []
    if not objs:
        head = "Новый мир: сцена прежнего мира была пуста — переносить нечего"
    else:
        n = len(rows) - len(by["refused"])
        head = (f"Сцена перенесена в новый мир: все объекты ({n})" if not by["refused"]
                else f"Сцена перенесена в новый мир: {n} из {len(rows)} объектов")
        if by["state"]:
            parts.append("с состоянием — " + _names(by["state"]))
        if by["params"]:
            parts.append("по параметрам (своего состояния нет) — " + _names(by["params"]))
        if by["restarted"]:
            parts.append("состояние не перенесено, начато заново из параметров — " + ", ".join(
                f"«{r['label']}»" + (f" ({note(r)})" if note(r) else "") for r in by["restarted"]))
        adapted = []
        for r in rows:
            if r["how"] == "refused":
                continue
            ch = [f"{k} {_g(a) if isinstance(a, (int, float)) and not isinstance(a, bool) else a} → "
                  + ("отброшено" if b is None else _g(b) if isinstance(b, (int, float)) and not isinstance(b, bool) else str(b))
                  for k, (a, b) in r["changed"].items()]
            ad = [x for k, x in r["notes"] if k == "adapted"]
            if ch or (ad and r["how"] != "restarted"):
                adapted.append(f"«{r['label']}»: " + "; ".join(ch + (ad if r["how"] != "restarted" else [])))
        if adapted:
            parts.append("изменено при переносе — " + " | ".join(adapted))
        if by["refused"]:
            parts.append("не перенесены: " + "; ".join(f"«{r['label']}» — {note(r)}" for r in by["refused"]))
    wn = [x for _, x in world["notes"]]
    if world["how"] == "state":
        parts.append("состояние мира перенесено" + (": " + "; ".join(wn) if wn else ""))
    elif world["how"] == "restarted":
        parts.append("состояние мира: " + "; ".join(wn))  # the section's notes say what started afresh
    elif wn:
        parts.append("мир: " + "; ".join(wn))
    text = head + "".join(". " + p[:1].upper() + p[1:] for p in parts)
    data = {"t": t_now, "objects": [{"id": r.get("new_id") or r["id"], "was": r["id"], "label": r["label"],
                                     "how": r["how"], "notes": [x for _, x in r["notes"]], "changed": r["changed"]} for r in rows],
            "world": {"how": world["how"], "notes": wn}}
    return text, plain(data)


def plain(x):
    """A scene export as plain JSON data (NumPy numbers and arrays a section may leave in a state become numbers and
    lists), so that it can travel as a world parameter."""
    if isinstance(x, dict):
        return {str(k): plain(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [plain(v) for v in x]
    if hasattr(x, "tolist"):
        return plain(x.tolist())
    if hasattr(x, "item") and not isinstance(x, (str, bytes)):
        return x.item()
    return x


def _label(ot: ObjectType, pid: str) -> str:
    p = ot.schema.by_id.get(pid)
    return p.label if p else pid
