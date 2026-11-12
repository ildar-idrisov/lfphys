# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""p04: the fluids playground (plan P15.7; owner, 2026-10-28). A wrapper over the engine's lattice Boltzmann solver
(``lfphys.core.fluids.lbm``: the incompressible Navier–Stokes equations in 2-D with their compressibility error
O(Ma²) stated); the framework is ``lfviz.playground``.

The laws of the world. World parameters (a change starts a new world): the fluid at the start, the domain and its grid,
the largest expected speed (it sets the time step through the Mach number; for a fluid the grid cannot resolve at that
speed the world lowers it to what the grid resolves and says so: review UX-params P24). Live laws (review UX-ui U12:
changed at the current moment, the flow kept): the viscosity (``Flow2D.set_viscosity``), the density
(``set_density``), the collision operator (``set_collision``), the dye on or off (``enable_dye`` / ``disable_dye``) and
its diffusivity. A grid above the memory budget is refused before anything is allocated (P25). Inside it the
experimenter places, at any moment, obstacles
(disks, rectangles, wing profiles; fixed, with a moving surface or a turning one — the bodies themselves stay where
they are), inlets and outlets on the sides, a moving wall (a lid), periodic sides, a body force, dye sources and
velocity probes; the solver advances the flow from the engine's laws in real time. Forces on each obstacle (drag, lift
and their coefficients: over the last step, and averaged over the slowest sound period of the domain, which the
weakly compressible scheme rings at), the mass, momentum and dye balances, the numbers that bound the solver's validity
(Mach, the cell Reynolds number) and, where the scene is a published benchmark's set-up, the benchmark's numbers next
to the computed ones are shown as the flow runs. A new object lands where it can exist (``place``: a free side, a
free spot for a body, a probe in the fluid, a body force the scheme can carry) or is refused in Russian with what to
change (reviews UX-ui U4, U7, U8, U13; UX-params P27).

Units: SI (m, s, kg); a 2-D flow is per metre of depth (forces in N/m).
"""

from __future__ import annotations

import math

import numpy as np

from lfphys.core.fluids import lbm as L
from lfviz.params import Param, Schema
from lfviz.playground import ObjectType, PlaygroundSimulation, scene_param, scene_time

try:  # the framework's refusal (reviews UX-params P4, UX-ui U13): shown as it is, in Russian, with what to change
    from lfviz.errors import Refusal
except ImportError:  # an older framework: a Russian ValueError is shown as it is
    Refusal = ValueError


def refusal(text, hint=None, detail=None):
    """A refusal for the owner: what is wrong and what to change (Russian)."""
    for kw in ({"hint": hint, "detail": detail}, {"change": hint, "detail": detail}):
        try:
            return Refusal(text, **kw)
        except TypeError:
            continue
    return Refusal(text.rstrip(".") + (f": {hint}" if hint else ""))

PIC_EVERY = 5      # frames between two pictures of the field (by count: the same in a restored world)
IMG_MAX = 512      # points per axis of the field's picture (area-averaged beyond)
ARROWS = 28        # velocity arrows along the longer side
MAX_STEPS = 400    # lattice steps per advance call (the runner interleaves commands and frames)
WINDOW_BLOCKS = 64  # blocks of the force record per sound period (the window of the forces' mean)
SIDES = [("left", "слева"), ("right", "справа"), ("bottom", "снизу"), ("top", "сверху")]
SIDE_RU = dict(SIDES)
FIELDS = {"speed": "модуль скорости |u|", "vorticity": "завихренность ω", "pressure": "давление p", "dye": "краситель"}
COLORS = {"obstacle": "#adb5bd", "inlet": "#51cf66", "outlet": "#ff922b", "lid": "#b197fc", "periodic": "#74c0fc",
          "dye": "#f783ac", "probe": "#ffd43b", "gravity": "#868e96"}
KIND_RU = {"closed-open": "4L/c_s (закрытый и открытый концы)", "closed-closed": "2L/c_s (два закрытых конца)",
           "open-open": "2L/c_s (два открытых конца)", "periodic": "L/c_s (периодичность)"}
FRAME_S = 0.1        # the modelled computing time of one advance call on the CPU (commands and frames keep flowing;
#                      measured: 3 steps per call cost 23 % more than 400 on the 880-node Kármán grid, 8 steps ~8 %)
RE_MARGIN = 0.9      # the speed the world resolves: this share of the open-domain cell-Reynolds limit (P24)
MEM_DEFAULT = 6 * 2 ** 30   # the grid's memory budget when the server gave the worker none (P25)
FLUIDS_RU = {"water": "вода", "air": "воздух", "dfg": "жидкость теста DFG", "custom": "своя жидкость"}
SIDE_ORDER = {"inlet": ("left", "bottom", "right", "top"), "outlet": ("right", "top", "left", "bottom"),
              "lid": ("top", "bottom", "left", "right")}


def _p(*a, **k):
    return Param(*a, **k)


SCHEMA = Schema([
    # the defaults build: the DFG benchmark's fluid and channel; water and air at these scales run at the speeds the grid
    # resolves (review UX-params P24), or in their own presets at millimetre and centimetre scales
    _p("fluid", "Жидкость в начале", "select", "dfg", group="Законы",
       options=[("water", "вода, 20 °C"), ("air", "воздух, 20 °C, 1 атм"),
                ("dfg", "жидкость теста DFG (ν = 10⁻³ м²/с, ρ = 1 кг/м³)"), ("custom", "своя: ρ и ν ниже")],
       help="Задаёт плотность и вязкость в начале мира (на ходу их можно менять в «Установке»). Если сетка не разрешает "
            "жидкость при «наибольшей ожидаемой скорости», мир понижает эту скорость до разрешимой и пишет почему; "
            "вода и воздух при скоростях см/с — в своих сценариях (миллиметровый и сантиметровый каналы)"),
    _p("rho", "Плотность ρ, кг/м³", "float", 1000.0, group="Жидкость (на ходу)", min=1e-3, max=1e5, log=True, live=True,
       help="Меняется в текущий момент: течение то же, давления и силы — в новом масштабе ρ. В начале мира — плотность "
            "выбранной жидкости (у «своей» — это значение)"),
    _p("nu", "Кинематическая вязкость ν, м²/с", "float", 1e-6, group="Жидкость (на ходу)", min=1e-9, max=10.0, log=True,
       live=True,
       help="Меняется в текущий момент (время релаксации схемы; шаг по времени тот же): скорость и давление прежние, "
            "вязкое напряжение подстраивается за несколько шагов. Не меньше того, что разрешает сетка. В начале мира — "
            "вязкость выбранной жидкости (у «своей» — это значение)"),
    _p("Lx", "Длина области по x, м", "float", 2.2, group="Область и сетка (на ходу)", min=1e-6, max=1e4, log=True,
       live=True,
       help="Меняется в текущий момент: шаг сетки прежний, область растёт или уменьшается со стороны, выбранной ниже; "
            "новая часть — жидкость в покое или с входящим потоком; уменьшать можно только там, где нет тел, "
            "красителя и датчиков"),
    _p("Ly", "Высота области по y, м", "float", 0.41, group="Область и сетка (на ходу)", min=1e-6, max=1e4, log=True,
       live=True, help="Как длина: на ходу, шаг прежний (высота округляется до целых ячеек)"),
    _p("nx", "Узлов сетки по x", "int", 440, group="Область и сетка (на ходу)", min=16, max=8192, live=True,
       help="Шаг сетки = длина / число узлов; по y — столько же на метр (высота округляется до целых ячеек). На ходу "
            "течение переносится на новую сетку (давление, скорость и неравновесная часть популяций с пересчётом по "
            "временам релаксации — как при измельчении сеток), тела перестраиваются по узлам. Сетка больше предела "
            "памяти не создаётся (оценка — в отказе)"),
    _p("u_max", "Наибольшая ожидаемая скорость, м/с", "float", 0.45, group="Область и сетка (на ходу)", min=1e-9,
       max=1e4, log=True, live=True,
       help="Задаёт шаг по времени через число Маха решётки (≈ 0,1) и с ним скорость звука схемы c_s = u_max/0,1: "
            "больше — меньше ошибка сжимаемости, но медленнее счёт; скорости в мире — до 3·u_max. Не больше того, что "
            "сетка разрешает для жидкости (число Рейнольдса ячейки ≤ 9): иначе в начале мира она понижается, а на ходу "
            "смена отклоняется с причиной. На ходу шаг по времени пересчитывается, популяции — тоже"),
    _p("anchor", "Область растёт или уменьшается", "select", "right_top", group="Область и сетка (на ходу)", live=True,
       options=[("right_top", "справа и сверху (координаты тел прежние)"),
                ("left_bottom", "слева и снизу (тела сдвигаются в координатах вместе с жидкостью)"),
                ("center", "поровну с обеих сторон (тела сдвигаются в координатах)")]),
    _p("fill", "Новая часть области", "select", "rest", group="Область и сетка (на ходу)", live=True,
       options=[("rest", "жидкость в покое (давление — от ближайшего края)"),
                ("inflow", "с входящим потоком (скорость первого входа)")]),
    _p("collision", "Оператор столкновений", "select", "trt", group="Схема (на ходу)", live=True,
       options=[("trt", "TRT (стенки не зависят от вязкости)"), ("bgk", "BGK (однопараметрический)")]),
    _p("dye", "Краситель", "select", "on", group="Схема (на ходу)", live=True,
       options=[("on", "есть (пассивная примесь)"), ("off", "нет")],
       help="Включается и выключается на ходу (выключить — когда в сцене нет источников красителя)"),
    _p("dye_D", "Диффузия красителя, м²/с (0 — как вязкость)", "float", 0.0, group="Схема (на ходу)", min=0.0,
       max=10.0, show_if={"dye": ["on"]}, live=True),
    scene_param(),
], presets={})

LIVE = ("rho", "nu", "collision", "dye", "dye_D", "Lx", "Ly", "nx", "u_max", "anchor", "fill")
GRID = ("Lx", "Ly", "nx", "u_max")  # live laws that move the populations to another grid or time step (Flow2D.remap)
ANCHOR_RU = {"right_top": "справа и сверху", "left_bottom": "слева и снизу", "center": "поровну с обеих сторон"}


def _scene(objs):
    return {"format": "lfscene", "version": 1, "objects": objs}


SCHEMA.presets.update({
    "cylinder_re20": {"label": "Обтекание цилиндра, Re = 20 (постановка DFG 2D-1: средние C_x, C_y против диапазонов "
                               "Schäfer & Turek)",
                      # u_max = Um as in the engine's test (Ma 0.1 at Um): the preset's numbers are the test's (D = 20,
                      # interpolated: 5.5895 / 0.010504 once the start's ringing has decayed, inside the range)
                      "params": {"fluid": "dfg", "Lx": 2.2, "Ly": 0.41, "nx": 440, "u_max": 0.3, "scene": _scene([
                          {"type": "inlet", "label": "Вход (парабола, 0,3 м/с)",
                           "values": {"side": "left", "speed": 0.3, "profile": "parabolic", "ramp": 3.0}},
                          {"type": "outlet", "label": "Выход", "values": {"side": "right"}},
                          {"type": "disk", "label": "Цилиндр", "values": {"x": 0.2, "y": 0.2, "radius": 0.05,
                                                                         "wall": "interpolated", "ref": 0.1,
                                                                         "u_ref": 0.2}},
                          {"type": "dye_source", "label": "Краситель", "values": {"x": 0.08, "y": 0.2,
                                                                                  "radius": 0.01}}])}},
    # 880 nodes: D = 40 cells and the developed flow's cell Reynolds number ~5.6 (at 440 it passed the open-domain
    # limit 10 from t = 0.44 s: review B7 L8); heavy on the CPU, real time on GPU 0
    "karman": {"label": "Дорожка Кармана за цилиндром, Re = 100 (постановка DFG 2D-2: C_x max, C_y max, St против "
                        "диапазонов; D = 40 ячеек — для GPU)",
               "params": {"fluid": "dfg", "Lx": 2.2, "Ly": 0.41, "nx": 880, "u_max": 2.0, "scene": _scene([
                   {"type": "inlet", "label": "Вход (парабола, 1,5 м/с)",
                    "values": {"side": "left", "speed": 1.5, "profile": "parabolic", "ramp": 0.5}},
                   {"type": "outlet", "label": "Выход", "values": {"side": "right"}},
                   {"type": "disk", "label": "Цилиндр", "values": {"x": 0.2, "y": 0.2, "radius": 0.05,
                                                                  "wall": "interpolated", "ref": 0.1, "u_ref": 1.0}},
                   {"type": "dye_source", "label": "Краситель", "values": {"x": 0.08, "y": 0.2, "radius": 0.01}},
                   {"type": "probe", "label": "Датчик за цилиндром", "values": {"x": 0.6, "y": 0.2}}])}},
    "cavity": {"label": "Каверна с подвижной крышкой, Re = 100 (осевые профили против таблиц Ghia, Ghia, Shin 1982)",
               "params": {"fluid": "custom", "rho": 1.0, "nu": 0.01, "Lx": 1.0, "Ly": 1.0, "nx": 192, "u_max": 1.2,
                          "scene": _scene([
                              {"type": "lid", "label": "Крышка", "values": {"side": "top", "speed": 1.0}},
                              {"type": "dye_source", "label": "Краситель", "values": {"x": 0.5, "y": 0.75,
                                                                                      "radius": 0.03}}])}},
    "channel": {"label": "Течение в канале (Пуазейль, Re ≈ 2) и пластина поперёк: профиль выше по потоку против "
                         "параболы",
                "params": {"fluid": "dfg", "Lx": 0.4, "Ly": 0.04, "nx": 512, "u_max": 0.1, "scene": _scene([
                    {"type": "inlet", "label": "Вход (парабола, 0,05 м/с)", "values": {"side": "left", "speed": 0.05,
                                                                                    "profile": "parabolic",
                                                                                    "ramp": 0.5}},
                    {"type": "outlet", "label": "Выход", "values": {"side": "right"}},
                    {"type": "rect", "label": "Пластина", "values": {"x": 0.2, "y": 0.01, "w": 0.004, "h": 0.016}},
                    {"type": "probe", "label": "Скорость на оси", "values": {"x": 0.1, "y": 0.02}}])}},
    # the DFG 2D-1 set-up made with real fluids at the scale where Re = 20 (review UX-params P24): the same numbers of
    # cells and the same Re, so the same flow in the units of D and U; water in a 22 mm channel, air in a 22 cm one
    "water_cylinder": {"label": "Вода: обтекание цилиндра D = 1 мм в канале 22 × 4,1 мм, Re = 20 (как тест DFG 2D-1, "
                                "в масштабе, где вода разрешается сеткой)",
                       "params": {"fluid": "water", "Lx": 0.022, "Ly": 0.0041, "nx": 440, "u_max": 0.03,
                                  "scene": _scene([
                                      {"type": "inlet", "label": "Вход (парабола, 3 см/с)",
                                       "values": {"side": "left", "speed": 0.03, "profile": "parabolic", "ramp": 0.3}},
                                      {"type": "outlet", "label": "Выход", "values": {"side": "right"}},
                                      {"type": "disk", "label": "Цилиндр", "values": {"x": 0.002, "y": 0.002,
                                                                                     "radius": 0.0005,
                                                                                     "wall": "interpolated"}},
                                      {"type": "dye_source", "label": "Краситель",
                                       "values": {"x": 0.0008, "y": 0.002, "radius": 0.0001}}])}},
    "air_cylinder": {"label": "Воздух: обтекание цилиндра D = 1 см в канале 22 × 4,1 см, Re = 20 (как тест DFG 2D-1, "
                              "в масштабе, где воздух разрешается сеткой)",
                     "params": {"fluid": "air", "Lx": 0.22, "Ly": 0.041, "nx": 440, "u_max": 0.0455,
                                "scene": _scene([
                                    {"type": "inlet", "label": "Вход (парабола, 4,55 см/с)",
                                     "values": {"side": "left", "speed": 0.0455, "profile": "parabolic", "ramp": 2.0}},
                                    {"type": "outlet", "label": "Выход", "values": {"side": "right"}},
                                    {"type": "disk", "label": "Цилиндр", "values": {"x": 0.02, "y": 0.02,
                                                                                   "radius": 0.005,
                                                                                   "wall": "interpolated"}},
                                    {"type": "dye_source", "label": "Краситель",
                                     "values": {"x": 0.008, "y": 0.02, "radius": 0.001}}])}},
    "airfoil": {"label": "Профиль крыла NACA 2412 под углом атаки 8° — решётка профилей (сверху и снизу "
                         "периодичность: шаг 0,8 м = 2 хорды, не одиночное крыло)",
                "params": {"fluid": "dfg", "Lx": 2.0, "Ly": 0.8, "nx": 512, "u_max": 1.2, "scene": _scene([
                    {"type": "inlet", "label": "Поток", "values": {"side": "left", "speed": 1.0,
                                                                   "profile": "uniform", "ramp": 0.3}},
                    {"type": "outlet", "label": "Выход", "values": {"side": "right"}},
                    {"type": "periodic", "label": "Сверху и снизу — периодичность (решётка профилей)",
                     "values": {"axis": "y"}},
                    {"type": "airfoil", "label": "Крыло", "values": {"code": "2412", "chord": 0.4, "x": 0.5,
                                                                     "y": 0.4, "aoa": 8.0, "wall": "interpolated"}},
                    {"type": "dye_source", "label": "Краситель", "values": {"x": 0.2, "y": 0.42,
                                                                            "radius": 0.012}}])}},
})


def _nice(v: float, digits: int = 2) -> float:
    """v rounded down to ``digits`` significant digits (defaults that read well: 0.041, 4e-4)."""
    if v == 0 or not math.isfinite(v):
        return 0.0
    e = math.floor(math.log10(abs(v))) - digits + 1
    return math.copysign(math.floor(abs(v) / 10 ** e) * 10 ** e, v)


def _xy(label="Центр", x=0.1, y=0.1):
    return [_p("x", f"{label}: x, м", "float", x, min=-1e4, max=1e4), _p("y", f"{label}: y, м", "float", y,
                                                                         min=-1e4, max=1e4)]


# the engine imposes a surface velocity on a fixed shape (Ladd); the body itself does not move (review B7 L3)
MOTION = [_p("vx", "Скорость поверхности (тело на месте): vx, м/с", "float", 0.0, min=-1e4, max=1e4,
             help="Тело НЕ перемещается: на его неподвижной форме задаётся скорость поверхности (условие Ладда). "
                  "Часть, нормальная к поверхности, — источник спереди и сток сзади (жидкость проходит сквозь стенку; "
                  "баланс массы это учитывает): так получается мгновенное граничное условие движущегося тела, но не "
                  "его течение. Перемещение тел пока не сделано (STATUS V41 o)"),
          _p("vy", "Скорость поверхности (тело на месте): vy, м/с", "float", 0.0, min=-1e4, max=1e4),
          _p("omega", "Вращение поверхности, рад/с", "float", 0.0, min=-1e6, max=1e6,
             help="Поверхность вращается вокруг центра, форма на месте (у круга скорость касательна к поверхности: "
                  "вращающийся цилиндр, эффект Магнуса)")]
WALL = _p("wall", "Стенка тела", "select", "staircase",
          options=[("staircase", "ступеньки (отражение на полпути; 1-й порядок по форме)"),
                   ("interpolated", "интерполяция Бузиди (точнее; только у неподвижной поверхности)")],
          help="Как сетка видит кривую стенку: ступеньками из ячеек или с точным положением стенки на каждой связи "
               "(масса через такую стенку не сохраняется точно — баланс это учитывает)")
SIDE = _p("side", "Сторона", "select", "left", options=SIDES)


def _otype(*args, handles=None, **kw) -> ObjectType:
    """A palette type with its handles (the LB1 framework: the parameters a drag in the scene changes, checked against
    the type's schema); an older framework without handles takes the type as before."""
    if handles is None:
        return ObjectType(*args, **kw)
    try:
        return ObjectType(*args, handles=handles, **kw)
    except TypeError:
        ot = ObjectType(*args, **kw)
        ot.handles = handles
        return ot


def palette(size=(2.2, 0.41), u_max=0.45, g=9.81) -> dict:
    """The palette with defaults made for this world (review UX-ui U4, U7): places and sizes in proportion to the domain
    (a body a tenth of the shorter side, a quarter along x, on the centre line), speeds a fraction of the speed the world
    resolves, the body force the largest the scheme carries up to 9.81 m/s²."""
    Lx, Ly = float(size[0]), float(size[1])
    m = min(Lx, Ly)
    cx, cy = _nice(0.25 * Lx, 3), _nice(0.5 * Ly, 3)
    v0 = _nice(u_max / 4.5) or 1e-9
    disk = Schema([*_xy(x=cx, y=cy), _p("radius", "Радиус, м", "float", _nice(0.1 * m), min=1e-9, max=1e4), WALL,
                   *MOTION,
                   _p("ref", "Длина для коэффициентов (0 — диаметр), м", "float", 0.0, min=0.0, max=1e4),
                   _p("u_ref", "Скорость для коэффициентов (0 — средняя на входе), м/с", "float", 0.0, min=0.0,
                      max=1e4)])
    rect = Schema([*_xy(x=cx, y=cy), _p("w", "Ширина, м", "float", _nice(0.1 * m), min=1e-9, max=1e4),
                   _p("h", "Высота, м", "float", _nice(0.05 * m), min=1e-9, max=1e4),
                   _p("angle", "Поворот, °", "float", 0.0, min=-360.0, max=360.0), WALL, *MOTION[:2],
                   _p("ref", "Длина для коэффициентов (0 — высота поперёк потока), м", "float", 0.0, min=0.0,
                      max=1e4),
                   _p("u_ref", "Скорость для коэффициентов (0 — средняя на входе), м/с", "float", 0.0, min=0.0,
                      max=1e4)])
    foil = Schema([_p("code", "Профиль NACA (4 цифры)", "select", "0012",
                      options=[(c, f"NACA {c}") for c in ("0006", "0012", "0018", "2412", "4412", "6409")]),
                   _p("chord", "Хорда, м", "float", _nice(0.3 * m), min=1e-9, max=1e4),
                   *_xy("Передняя кромка", x=cx, y=cy), _p("aoa", "Угол атаки, °", "float", 5.0, min=-90.0, max=90.0),
                   WALL,
                   _p("u_ref", "Скорость для коэффициентов (0 — средняя на входе), м/с", "float", 0.0, min=0.0,
                      max=1e4)])
    inlet = Schema([SIDE, _p("speed", "Скорость входа (наибольшая для параболы), м/с", "float", v0, min=-1e4,
                             max=1e4),
                    _p("profile", "Профиль", "select", "uniform",
                       options=[("uniform", "однородный"), ("parabolic", "парабола (как в канале)")]),
                    _p("ramp", "Плавный разгон за, с", "float", 0.0, min=0.0, max=1e6,
                       help="После смены скорости вход плавно переходит от прежней скорости к новой за это время; "
                            "смена только красителя разгон не перезапускает"),
                    _p("dye", "Краситель во входящей жидкости (доля)", "float", 0.0, min=0.0, max=1.0)])
    outlet = Schema([_p("side", "Сторона", "select", "right", options=SIDES),
                     _p("pressure", "Давление на выходе (относительное), Па", "float", 0.0, min=-1e9, max=1e9,
                        help="Давление в середине стороны; при объёмной силе вдоль стороны к нему добавляется "
                             "гидростатическая часть. Движок откажет, если плотность схемы отклонится больше чем на "
                             "0,045 (масштаб — c_s²ρ, c_s — скорость звука схемы)")])
    lid = Schema([_p("side", "Сторона", "select", "top", options=SIDES),
                  _p("speed", "Скорость стенки вдоль себя, м/с", "float", v0, min=-1e4, max=1e4,
                     help="Снизу и сверху — вдоль +x, слева и справа — вдоль +y")])
    periodic = Schema([_p("axis", "Пара сторон", "select", "x",
                          options=[("x", "слева–справа (по x)"), ("y", "снизу–сверху (по y)")])])
    gravity = Schema([_p("gx", "Ускорение: gx, м/с²", "float", 0.0, min=-1e4, max=1e4),
                      _p("gy", "Ускорение: gy, м/с²", "float", -g, min=-1e4, max=1e4,
                         help="Однородная объёмная сила (схема Гуо). В жидкости постоянной плотности она меняет только "
                              "давление (гидростатическое, сразу), пока стенки и выходы её уравновешивают; вдоль "
                              "периодической оси она гонит течение, как перепад давления. Схема несёт её "
                              "гидростатический перепад плотности g·L/c_s² (c_s — скорость звука схемы, не жидкости): "
                              "по умолчанию — наибольшая сила, которую схема этого мира выдерживает (до 9,81 м/с²); "
                              "для большей — больше «наибольшая ожидаемая скорость» (новый мир)")])
    dye = Schema([*_xy(x=_nice(0.1 * Lx, 3), y=cy), _p("radius", "Радиус пятна, м", "float", _nice(0.03 * m),
                                                     min=1e-9, max=1e4),
                  _p("concentration", "Концентрация (доля)", "float", 1.0, min=0.0, max=1.0),
                  _p("mode", "Как", "select", "source", options=[("source", "источник (держит концентрацию)"),
                                                               ("drop", "капля один раз")])])
    probe = Schema([*_xy("Точка", x=_nice(0.6 * Lx, 3), y=cy)])
    return {
        # handles (P16.2): the bodies, the dye and the probes are dragged in the plane; a body moved is re-voxelised at
        # once (the nodes it leaves start as fluid at its neighbours' density, the ones it covers book their fluid)
        "disk": _otype("disk", "Цилиндр (круг)", "body", disk, color=COLORS["obstacle"],
                       handles={"position": ["x", "y"], "size": "radius"}),
        "rect": _otype("rect", "Прямоугольник", "body", rect, color=COLORS["obstacle"],
                       handles={"position": ["x", "y"]}),
        "airfoil": _otype("airfoil", "Профиль крыла NACA", "body", foil, color=COLORS["obstacle"],
                          handles={"position": ["x", "y"]}),
        "inlet": ObjectType("inlet", "Вход потока", "source", inlet, limit=4, color=COLORS["inlet"],
                            help="Заданная скорость на стороне области (ставится на первую свободную сторону)"),
        "outlet": ObjectType("outlet", "Выход (давление)", "source", outlet, limit=4, color=COLORS["outlet"]),
        "lid": ObjectType("lid", "Подвижная стенка", "source", lid, limit=4, color=COLORS["lid"]),
        "periodic": ObjectType("periodic", "Периодичность", "field", periodic, limit=2, color=COLORS["periodic"],
                               help="Ушедшее через одну сторону входит с противоположной (тела повторяются: решётка)"),
        "gravity": ObjectType("gravity", "Объёмная сила (тяжесть)", "field", gravity, limit=1,
                              color=COLORS["gravity"]),
        "dye_source": _otype("dye_source", "Краситель", "source", dye, limit=12, color=COLORS["dye"],
                             help="Пассивная примесь: показывает, куда течёт жидкость (капля, сдвинутая мышью, "
                                  "падает снова на новом месте)",
                             handles={"position": ["x", "y"], "size": "radius"}),
        "probe": _otype("probe", "Датчик скорости", "probe", probe, limit=8, color=COLORS["probe"],
                        handles={"position": ["x", "y"]}),
    }


def naca4(code: str, chord: float, n: int = 80) -> np.ndarray:
    """The NACA four-digit profile (Abbott & von Doenhoff, Theory of Wing Sections, 1959, §6.4: the thickness
    distribution y_t = 5 t (0.2969 sqrt x - 0.1260 x - 0.3516 x^2 + 0.2843 x^3 - 0.1015 x^4) — with the closed
    trailing edge, last coefficient 0.1036 — about the mean line of camber m at p), in units of the chord from the
    leading edge, as a closed polygon (upper surface then lower)."""
    m, p, t = int(code[0]) / 100.0, int(code[1]) / 10.0, int(code[2:]) / 100.0
    beta = np.linspace(0.0, math.pi, n)
    x = 0.5 * (1.0 - np.cos(beta))
    yt = 5 * t * (0.2969 * np.sqrt(x) - 0.1260 * x - 0.3516 * x ** 2 + 0.2843 * x ** 3 - 0.1036 * x ** 4)
    if m > 0 and p > 0:
        yc = np.where(x < p, m / p ** 2 * (2 * p * x - x ** 2), m / (1 - p) ** 2 * ((1 - 2 * p) + 2 * p * x - x ** 2))
        dy = np.where(x < p, 2 * m / p ** 2 * (p - x), 2 * m / (1 - p) ** 2 * (p - x))
    else:
        yc, dy = np.zeros_like(x), np.zeros_like(x)
    th = np.arctan(dy)
    xu, yu = x - yt * np.sin(th), yc + yt * np.cos(th)
    xl, yl = x + yt * np.sin(th), yc - yt * np.cos(th)
    pts = np.concatenate([np.stack([xu, yu], 1), np.stack([xl, yl], 1)[::-1][1:-1]])
    return pts * chord


def _overlap(n: int, m: int) -> np.ndarray:
    """(m, n): the part of cell j (n equal cells over the side) inside picture interval k (m equal intervals over the
    same side), in units of a cell."""
    ec, ep = np.arange(n + 1) / n, np.arange(m + 1) / m
    lo = np.maximum(ep[:-1, None], ec[None, :-1])
    hi = np.minimum(ep[1:, None], ec[None, 1:])
    return np.clip(hi - lo, 0.0, None) * n


def resample(a: np.ndarray, fluid: np.ndarray, m: int):
    """The picture of a field ``a`` (nx, ny) on at most ``m`` points per axis (review B7 L16): each point covers an
    equal part of the domain (cells cut at its edges count by their share), so the picture spans the whole domain, and
    its value is the mean over the fluid it covers only (solid cells have weight 0). Returns (values, fluid fraction)."""
    nx, ny = a.shape
    s = max(nx, ny) / m
    w = fluid.astype(float)
    if s <= 1.0:
        return np.where(fluid, a, 0.0), w
    mx, my = max(1, int(round(nx / s))), max(1, int(round(ny / s)))
    Ax, Ay = _overlap(nx, mx), _overlap(ny, my)
    num = Ax @ (np.where(fluid, a, 0.0) * w) @ Ay.T
    den = Ax @ w @ Ay.T
    area = Ax.sum(axis=1)[:, None] * Ay.sum(axis=1)[None, :]
    return np.where(den > 0, num / np.where(den > 0, den, 1.0), 0.0), den / area


_SUP = str.maketrans("-0123456789", "⁻⁰¹²³⁴⁵⁶⁷⁸⁹")


def _num(v, d=3):
    """A number for the owner: d significant digits, a decimal comma, powers of ten as ·10⁻⁶ outside 10⁻³…10⁵."""
    v = float(v)
    if v == 0 or not math.isfinite(v):
        return "0" if v == 0 else str(v)
    if 1e-3 <= abs(v) < 1e5:
        s = f"{v:.{d}g}"
        if "e" in s:
            s = f"{v:.0f}"
        return s.replace(".", ",")
    e = math.floor(math.log10(abs(v)))
    m = f"{v / 10 ** e:.{max(d - 1, 0)}f}".rstrip("0").rstrip(".")
    return f"{m}·10{str(e).translate(_SUP)}".replace(".", ",")


_LBM_RU = [  # the engine's refusals (Russian already) in the world's terms: "dt" is not a parameter here (U13, P24)
    (r"число Маха ([\d.e+-]+) > ([\d.]+)", "mach"),
    (r"неустойчиво: τ = ([\d.e+-]+) слишком близко к 1/2", "tau"),
    (r"число Рейнольдса ячейки u·dx/ν = ([\d.e+-]+) > ([\d.]+)", "recell"),
    (r"плотность покоя схемы отклонилась бы", "density"),
    (r"интерполированные стенки — только у неподвижной поверхности", "interp"),
]


def _grid(params):
    """(nx, ny, dx) of a world's grid, as the world builds it."""
    nx = int(params["nx"])
    dx = float(params["Lx"]) / nx
    ny = max(8, int(round(float(params["Ly"]) / dx)))
    return nx, ny, dx


def _budget():
    try:
        from lfviz import limits
        b = limits.worker_budget()
        return int(b * limits.HEADROOM) if b else MEM_DEFAULT
    except Exception:  # noqa: BLE001 - an older framework without limits
        return MEM_DEFAULT


def _fmt_bytes(n):
    try:
        from lfviz.limits import fmt_bytes
        return fmt_bytes(n)
    except Exception:  # noqa: BLE001
        for unit, k in (("ТБ", 2 ** 40), ("ГБ", 2 ** 30), ("МБ", 2 ** 20)):
            if n >= k:
                return f"{n / k:.3g} {unit}".replace(".", ",")
        return f"{n:.0f} Б"


def _sci(v):
    return _num(v, 2)


class Simulation(PlaygroundSimulation):
    VIZ_ID = "p04_fluids"
    speed_range = (1e-9, 1e6)

    # --- before a world is built (the integrator's API of 2026-11-05; review UX-params P25) ------------------------
    @classmethod
    def estimate_bytes(cls, params):
        nx, ny, _ = _grid(params)
        return (L.Flow2D.memory_estimate(nx, ny, params.get("dye", "on") == "on"),
                f"сетка течения {nx} × {ny} узлов", cls._grid_hint(params))

    @classmethod
    def _grid_hint(cls, params, budget=None):
        budget = budget or _budget()
        per = 1000 if params.get("dye", "on") == "on" else 800
        n_max = budget / per
        Lx, Ly = float(params["Lx"]), float(params["Ly"])
        nx = int(params["nx"])
        # the largest nx whose grid fits: nx * ny ~ nx^2 Ly / Lx <= n_max (ny at least 8)
        fit = [o for o in (int(math.sqrt(n_max * Lx / Ly)), int(n_max / 8)) if o >= 16
               and o * max(8, round(Ly / (Lx / o))) <= n_max]
        lx_min = nx * nx * Ly / n_max
        parts = []
        if fit:
            parts.append(f"«Узлов сетки по x» не больше {max(fit)}")
        parts.append(f"«Длина области по x» не меньше {_sci(lx_min)} м при {nx} узлах")
        parts.append("область ближе к квадрату (узлов по y — столько же на метр, сколько по x)")
        return ", или ".join(parts)

    @classmethod
    def check_params(cls, params):
        nx, ny, dx = _grid(params)
        need = L.Flow2D.memory_estimate(nx, ny, params.get("dye", "on") == "on")
        budget = _budget()
        if need > budget:
            raise refusal(f"область {_sci(float(params['Lx']))} × {_sci(float(params['Ly']))} м на сетке nx = {nx}: "
                          f"шаг {_sci(dx)} м, по y {_sci(float(ny))} узлов, всего {_sci(float(nx) * ny)} узлов — это "
                          f"≈ {_fmt_bytes(need)} памяти, больше предела {_fmt_bytes(budget)}",
                          hint=cls._grid_hint(params, budget))

    def __init__(self, params, seed, emit):
        super().__init__(params, seed, emit)
        self.params = dict(self.params)
        self.check_params(params)
        fl = params["fluid"]
        if fl == "custom":
            rho, nu = float(params["rho"]), float(params["nu"])
        elif fl == "dfg":
            rho, nu = 1.0, 1e-3
        else:
            props = L.FLUIDS["water_20C" if fl == "water" else "air_20C"]
            rho, nu = float(props["rho"]), float(props["nu"])
        self.rho, self.nu = rho, nu
        nx, ny, dx = _grid(params)
        # P24: a fluid the grid cannot resolve at the asked u_max runs at the largest speed it resolves
        u_req = float(params["u_max"])
        u_ok = _nice(RE_MARGIN * L.RE_CELL_MAX_OPEN * nu / dx)
        self.u_note = None
        if u_req > u_ok:
            self.u_note = (f"{FLUIDS_RU[fl]} (ν = {_sci(nu)} м²/с) на сетке с шагом {_sci(dx)} м разрешается при "
                           f"скоростях до {_sci(u_ok)} м/с (число Рейнольдса ячейки u·dx/ν ≤ {_num(RE_MARGIN * 10)}): "
                           f"«наибольшая ожидаемая скорость» понижена с {_sci(u_req)} до {_sci(u_ok)} м/с; для бо́льших "
                           f"скоростей — область меньше или узлов больше (новый мир), или сценарии «Вода…», «Воздух…»")
            self.params["u_max"] = u_ok
        self.u_max = float(self.params["u_max"])
        self.live = {"rho": rho, "nu": nu, "collision": params["collision"], "dye": params["dye"],
                     "dye_D": float(params["dye_D"]), "Lx": nx * dx, "Ly": ny * dx, "nx": nx, "u_max": self.u_max,
                     "anchor": params["anchor"], "fill": params["fill"]}
        self.D = (float(params["dye_D"]) or nu) if params["dye"] == "on" else None
        # a world from a scene file starts at the file's time (the flow from rest): the engine counts its steps from
        # there (review B7 L2)
        self.fl = L.Flow2D(size=(nx * dx, ny * dx), dx=dx, nu=nu, rho=rho, u_max=self.u_max,
                           collision=params["collision"], dye=self.D, device="auto", t0=scene_time(params))
        self.size = (nx * dx, ny * dx)
        self.PALETTE = palette(self.size, self.u_max, self._g_default())
        self.ref = {}            # scene object id -> ("obstacle", oid) | ("side", names) | ("dye", sid) | ("probe",) ...
        self.side_owner = {}     # side name -> scene object id
        self.shown = "dye" if self.D else "speed"
        self.n_pic = 0
        self.win = None
        self._dup = False
        self.start_scene()
        self._record_setup()
        self.default_speed = self.size[0] / (10.0 * self.u_max)  # the fastest flow crosses in ~10 s

    def after_header(self):
        super().after_header()
        if self.u_note:
            self.emit({"type": "notice", "t": self.t, "text": "Жидкость и скорости: " + self.u_note})

    # --- limits of this world (U7, U13, P24) -----------------------------------------------------------------------
    def _v_limit(self, sides=None):
        """The largest speed (m/s) a side or a surface may have now: Mach 0.3 of the scheme's sound and the cell
        Reynolds limit of the domain (with an inlet or an outlet the lower one)."""
        fl = self.fl
        c_s = fl.units.c * L.CS
        return min(L.MACH_MAX * c_s, fl.re_cell_limit(sides) * self.live["nu"] / fl.units.dx)

    def _g_default(self):
        """The body force the palette offers: 9.81 m/s² downwards when the scheme carries it with walls on every side,
        else the largest it carries (two digits)."""
        lim = self.fl.gravity_limit((0.0, -1.0), {k: L.Wall() for k in L.SIDES})
        return 9.81 if lim >= 9.81 else _nice(0.98 * lim)

    def _u_for_g(self, g, lim):
        """The u_max at which the scheme would carry |g| (the hydrostatic spread goes as 1/c_s² ∝ 1/u_max²)."""
        return self.u_max * math.sqrt(g / lim) * 1.02 if lim > 0 else math.inf

    def _ru(self, e):
        """An engine refusal of the flow put in this world's terms (what to change here: the speeds, ν, u_max, the
        grid), its sentence as the detail (review UX-ui U13, UX-params P24)."""
        import re
        s = str(e)
        nu, dx = self.live["nu"], self.fl.units.dx
        for rx, key in _LBM_RU:
            m = re.search(rx, s)
            if not m:
                continue
            v = self._v_limit()
            if key == "mach":
                return refusal(f"скорость больше, чем выдерживает слабосжимаемая схема этого мира (число Маха "
                               f"{_num(float(m.group(1)), 2)} > {m.group(2)}: до {_sci(v)} м/с)",
                               hint=f"скорости не больше {_sci(v)} м/с, или «Наибольшая ожидаемая скорость» больше "
                                    f"(новый мир)", detail=s)
            if key == "tau":
                nu_min = L.TAU_MIN_EXCESS / 3 * dx ** 2 / self.fl.units.dt
                return refusal(f"вязкость ν = {_sci(nu)} м²/с слишком мала для этой сетки и шага (схема неустойчива)",
                               hint=f"ν не меньше {_sci(nu_min * 1.01)} м²/с, или больше узлов, или меньше «Наибольшая "
                                    f"ожидаемая скорость» (новый мир)", detail=s)
            if key == "recell":
                return refusal(f"течение с такой скоростью сетка не разрешает (число Рейнольдса ячейки "
                               f"{float(m.group(1)):.3g} > {m.group(2)})",
                               hint=f"скорости не больше {_sci(v)} м/с, или ν больше (меняется на ходу), или больше "
                                    f"узлов (новый мир)", detail=s)
            if key == "density":
                return refusal("давление выхода или объёмная сила слишком велики для слабосжимаемой схемы этого мира "
                               "(её плотность отклонилась бы больше чем на 4,5 %)",
                               hint="меньше давление или сила, или больше «Наибольшая ожидаемая скорость» (новый мир)",
                               detail=s)
            if key == "interp":
                return refusal("у тела с интерполированной стенкой поверхность не может двигаться",
                               hint="«Стенка тела» = ступеньки, или скорость и вращение поверхности 0", detail=s)
        return e

    # --- objects ------------------------------------------------------------------------------------------------
    def _shape(self, obj):
        t, v = obj["type"], obj["values"]
        if t == "disk":
            return L.Disk((v["x"], v["y"]), v["radius"])
        if t == "rect":
            return L.Rect((v["x"], v["y"]), (v["w"], v["h"]), math.radians(v["angle"]))
        if t == "airfoil":
            return L.Polygon([tuple(map(float, q)) for q in self._foil(v)])
        raise ValueError(t)

    @staticmethod
    def _foil(v):
        """The profile placed: leading edge at (x, y), turned by the angle of attack (nose up into a stream along +x:
        the trailing edge goes down)."""
        a = -math.radians(v["aoa"])
        R = np.array([[math.cos(a), -math.sin(a)], [math.sin(a), math.cos(a)]])
        return naca4(v["code"], v["chord"]) @ R.T + np.array([v["x"], v["y"]])

    def _outline(self, obj, n=48):
        t, v = obj["type"], obj["values"]
        if t == "disk":
            a = np.linspace(0, 2 * math.pi, n, endpoint=False)
            return np.stack([v["x"] + v["radius"] * np.cos(a), v["y"] + v["radius"] * np.sin(a)], 1)
        if t == "rect":
            a = math.radians(v["angle"])
            R = np.array([[math.cos(a), -math.sin(a)], [math.sin(a), math.cos(a)]])
            c = np.array([[-1, -1], [1, -1], [1, 1], [-1, 1]]) * 0.5 * np.array([v["w"], v["h"]])
            return c @ R.T + np.array([v["x"], v["y"]])
        if t == "airfoil":
            return self._foil(v)
        return None

    def _ref_len(self, obj) -> float:
        """The coefficients' length: the chord of a profile, the object's own length, or 0 = the engine's default
        (the width across the flow); 0 also clears a length set before (review B7 L10)."""
        v = obj["values"]
        if obj["type"] == "airfoil":
            return float(v["chord"])
        return float(v.get("ref", 0.0) or 0.0)

    def _claim(self, obj, sides):
        for sd in sides:
            own = self.side_owner.get(sd)
            if own is not None and own != obj["id"]:
                free = [SIDE_RU[k] for k in L.SIDES if self.side_owner.get(k) in (None, obj["id"])]
                raise refusal(f"сторона «{SIDE_RU[sd]}» уже занята объектом «{self.objects[own]['label']}»",
                              hint=("свободны: " + ", ".join(free)) if free else
                              "все стороны заняты: уберите один из объектов на сторонах")

    def _side_obj(self, obj):
        t, v = obj["type"], obj["values"]
        if t == "inlet":
            return {v["side"]: L.Inlet(velocity=float(v["speed"]), profile=v["profile"], ramp=float(v["ramp"]),
                                       dye=float(v["dye"]))}
        if t == "outlet":
            return {v["side"]: L.Outlet(pressure=float(v["pressure"]))}
        if t == "lid":
            return {v["side"]: L.Wall(velocity=float(v["speed"]))}
        if t == "periodic":
            a, b = ("left", "right") if v["axis"] == "x" else ("bottom", "top")
            return {a: L.Periodic(), b: L.Periodic()}
        raise ValueError(t)

    # --- placement (reviews UX-ui U4, U7, U8, P27; the integrator's API of 2026-11-05) ----------------------------
    def place(self, kind, values):
        """A palette object's values before it is added: the defaults completed; a clicked point (``position``, m) as
        its place (for a side object: the nearest side); a side object on the first free side; a body moved to the
        nearest place where it does not cover another body; a probe or a dye spot into the fluid; a body force reduced
        to what the scheme carries (with a note); speeds above what the world resolves reduced to it (with a note).
        Deterministic: it reads the state, never changes it."""
        ot = self._type(kind)
        values = dict(values or {})
        pos = values.pop("position", None)
        v, errors = ot.schema.resolve(None, values)
        if errors:
            raise refusal("; ".join(errors))
        v = dict(v)
        Lx, Ly = self.size
        if pos is not None:
            px, py = float(pos[0]), float(pos[1])
            if "x" in v:
                v["x"], v["y"] = px, py
            elif kind in ("inlet", "outlet", "lid"):
                d = {"left": abs(px), "right": abs(Lx - px), "bottom": abs(py), "top": abs(Ly - py)}
                v["side"] = min(d, key=d.get)
            elif kind == "periodic":
                v["axis"] = "x" if min(abs(px), abs(Lx - px)) <= min(abs(py), abs(Ly - py)) else "y"
        if kind in ("inlet", "outlet", "lid"):
            if self.side_owner.get(v["side"]) is not None:
                free = [k for k in SIDE_ORDER[kind] if self.side_owner.get(k) is None]
                if not free:
                    raise refusal("все четыре стороны области уже заняты",
                                  hint="уберите один из объектов на сторонах или смените его сторону")
                self._note(f"сторона «{SIDE_RU[v['side']]}» занята — «{ot.label}» поставлен на сторону "
                           f"«{SIDE_RU[free[0]]}»")
                v["side"] = free[0]
            self._cap_speed(kind, v, "speed")
        elif kind == "periodic":
            pair = {"x": ("left", "right"), "y": ("bottom", "top")}
            if any(self.side_owner.get(k) is not None for k in pair[v["axis"]]):
                other = "y" if v["axis"] == "x" else "x"
                if any(self.side_owner.get(k) is not None for k in pair[other]):
                    raise refusal("для периодичности нужна пара свободных противоположных сторон, а заняты обе пары",
                                  hint="уберите объекты с левой и правой (или нижней и верхней) сторон")
                v["axis"] = other
        elif kind in ("disk", "rect", "airfoil"):
            self._inside(kind, v, place=True)
            self._free_body(kind, v)
            for c in ("vx", "vy"):
                self._cap_speed(kind, v, c)
        elif kind in ("probe", "dye_source"):
            v["x"] = min(max(float(v["x"]), 0.0), Lx)
            v["y"] = min(max(float(v["y"]), 0.0), Ly)
            self._into_fluid(v)
        elif kind == "gravity":
            g = math.hypot(float(v["gx"]), float(v["gy"]))
            if g > 0:
                lim = self.fl.gravity_limit((float(v["gx"]), float(v["gy"])))
                if g > lim:
                    k = _nice(0.98 * lim) / g
                    self._note(f"сила {_num(g, 3)} м/с² для схемы этого мира велика (её гидростатический перепад плотности "
                               f"превысил бы 4,5 %): поставлено {_num(_nice(0.98 * lim), 3)} м/с²; для {_num(g, 3)} м/с² нужна "
                               f"«наибольшая ожидаемая скорость» не меньше {_sci(self._u_for_g(g, lim))} м/с (новый мир)")
                    v["gx"], v["gy"] = float(v["gx"]) * k, float(v["gy"]) * k
        return v

    def _note(self, text):
        """A short note for the owner about what was done instead of what was asked (shown at once: ``notify``)."""
        if not self._loading:
            self.emit({"type": "event", "kind": "scene", "t": self.t, "text": text, "notify": True})

    def _cap_speed(self, kind, v, key):
        lim = self._v_limit()
        sp = float(v.get(key, 0.0))
        if abs(sp) > lim:
            new = math.copysign(_nice(0.95 * lim), sp)
            self._note(f"скорость {_num(sp, 3)} м/с больше, чем этот мир разрешает (до {_sci(lim)} м/с): поставлено "
                       f"{_sci(new)} м/с")
            v[key] = new

    def _bbox(self, kind, v):
        P = self._outline({"type": kind, "values": v})
        return P[:, 0].min(), P[:, 0].max(), P[:, 1].min(), P[:, 1].max()

    def _inside(self, kind, v, place=False):
        """A body wholly outside the domain is refused (place: moved in); one that would cover (nearly) the whole
        domain is refused; one partly outside is accepted with a note (the wall cuts it)."""
        Lx, Ly = self.size
        x0, x1, y0, y1 = self._bbox(kind, v)
        if x1 <= 0 or x0 >= Lx or y1 <= 0 or y0 >= Ly:
            if place:
                cx, cy = 0.5 * (x0 + x1), 0.5 * (y0 + y1)
                v["x"] = round(float(v["x"]) + min(max(cx, 0.0), Lx) - cx, 9)
                v["y"] = round(float(v["y"]) + min(max(cy, 0.0), Ly) - cy, 9)
                return
            raise refusal(f"тело целиком вне области {_sci(Lx)} × {_sci(Ly)} м",
                          hint=f"его место внутри: x от 0 до {_sci(Lx)} м, y от 0 до {_sci(Ly)} м")
        frac = float(np.mean(self.fl.shape_mask(self._shape({"type": kind, "values": v}))))
        if frac > 0.9:
            raise refusal(f"тело закрыло бы {frac:.0%} области: жидкости почти не осталось бы",
                          hint="тело меньше области")
        if (x0 < 0 or x1 > Lx or y0 < 0 or y1 > Ly) and not place:
            self._note("тело выходит за край области: его часть за стенкой срезана (считается часть внутри)")

    def _free_body(self, kind, v):
        """Move a body (in place) to the nearest spot where it does not cover another body, inside the domain with a
        margin of two cells; a refusal when there is none."""
        solid = self._bodies_mask()
        if not solid.any():
            return
        shape0 = self._shape({"type": kind, "values": v})
        m = self.fl.shape_mask(shape0)
        if not (m & solid).any():
            return
        Lx, Ly = self.size
        x0, x1, y0, y1 = self._bbox(kind, v)
        hx, hy = 0.5 * (x1 - x0), 0.5 * (y1 - y0)
        cx, cy = 0.5 * (x0 + x1), 0.5 * (y0 + y1)
        dx = self.fl.units.dx
        xs = np.linspace(hx + 2 * dx, Lx - hx - 2 * dx, 61) if Lx - 2 * hx > 4 * dx else np.array([cx])
        ys = np.linspace(hy + 2 * dx, Ly - hy - 2 * dx, 31) if Ly - 2 * hy > 4 * dx else np.array([cy])
        C = np.stack(np.meshgrid(xs, ys, indexing="ij"), -1).reshape(-1, 2)
        order = np.argsort((C[:, 0] - cx) ** 2 + (C[:, 1] - cy) ** 2, kind="stable")
        for k in order[:400]:
            w = {**v, "x": float(v["x"]) + C[k, 0] - cx, "y": float(v["y"]) + C[k, 1] - cy}
            if not (self.fl.shape_mask(self._shape({"type": kind, "values": w})) & solid).any():
                self._note(f"место занято другим телом — тело поставлено в ({_num(w['x'], 4)}, {_num(w['y'], 4)}) м")
                v["x"], v["y"] = round(w["x"], 9), round(w["y"], 9)
                return
        raise refusal("в области нет места для этого тела, не накрыв другое", hint="тело меньше или уберите другое тело")

    def _bodies_mask(self):
        m = np.zeros((self.fl.nx, self.fl.ny), bool)
        for oid, k in self.ref.items():
            if k[0] == "obstacle":
                m |= self.fl.shape_mask(self._shape(self.objects[oid]))
        return m

    def _into_fluid(self, v):
        """A probe or a dye spot inside a body goes to the nearest fluid node (with a note)."""
        solid = self.fl.solid()
        i, j = self._at(v["x"], v["y"])
        if not solid[i, j]:
            return
        fi, fj = np.nonzero(~solid)
        if not len(fi):
            raise refusal("в области нет жидкости", hint="уберите тела")
        k = int(np.argmin((self.fl.x[fi] - v["x"]) ** 2 + (self.fl.y[fj] - v["y"]) ** 2))
        v["x"], v["y"] = float(self.fl.x[fi[k]]), float(self.fl.y[fj[k]])
        self._note(f"точка внутри тела — поставлено в ближайшую точку жидкости ({_num(v['x'], 4)}, {_num(v['y'], 4)}) м")

    def palette_state(self):
        """The palette types the world cannot take now and why (review UX-ui U7, U22)."""
        out = {}
        if all(self.side_owner.get(k) is not None for k in L.SIDES):
            for t in ("inlet", "outlet", "lid"):
                out[t] = "все четыре стороны заняты: уберите объект с одной из сторон"
        pairs = (("left", "right"), ("bottom", "top"))
        if all(any(self.side_owner.get(k) is not None for k in p) for p in pairs):
            out["periodic"] = "нет пары свободных противоположных сторон: уберите объекты с одной из пар"
        if self.D is None:
            out["dye_source"] = "краситель выключен: включите «Краситель» в «Установке» (на ходу)"
        return out

    # --- a new world that keeps the scene (plan P16.1; review LB1-framework F5) ------------------------------------
    def carry_state(self):
        """The flow itself goes with a carry-over (the scene file keeps only the set-up): the engine's whole state but
        its force record (keyed by obstacle number; the new world records its own)."""
        d = self.fl.state_dict()
        d["rec"] = None
        return {"world": {"flow": d}}

    def carry_world(self, state, laws):
        """Continue the previous world's flow here (``Flow2D.adopt``): on the same grid and time step as it is; on another
        grid, domain or time step moved there first by the engine's transfer (``Flow2D.remap``, as a live change of the
        grid would; the domain grows or is cut on the right and the top, where the objects keep their coordinates);
        this world's fluid, sides, bodies, dye and force from now on. What could not be taken starts at rest, said in the
        carry-over's notice."""
        fl = self.fl
        if not state or not isinstance(state.get("flow"), dict):
            self.carry_note("течение начато заново из покоя: прежний мир его не передал", restarted=True)
            return
        try:
            old = L.Flow2D.from_state_dict(state["flow"], device="cpu")
        except (ValueError, KeyError, TypeError) as e:
            self.carry_note(f"течение начато заново из покоя: состояние прежнего мира не читается ({e})", restarted=True)
            return
        notes = []
        same = (old.nx, old.ny) == (fl.nx, fl.ny) and old.units.dx == fl.units.dx and \
            math.isclose(old.units.dt, fl.units.dt, rel_tol=1e-12)
        if not same:
            g0 = f"{old.nx} × {old.ny} узлов (шаг {_sci(old.units.dx)} м, dt {_sci(old.units.dt)} с)"
            try:
                try:
                    old.remap(dx=fl.units.dx, size=fl.size, dt=fl.units.dt)
                except ValueError:  # the old viscosity may not run on the new grid: this world's first
                    old.set_viscosity(self.nu)
                    old.remap(dx=fl.units.dx, size=fl.size, dt=fl.units.dt)
            except (ValueError, L.Unstable) as e:
                self.carry_note(f"течение начато заново из покоя: его нельзя перенести с сетки {g0} на сетку этого мира "
                                f"({e})", restarted=True)
                return
            notes.append(f"течение перенесено с сетки {g0} на {fl.nx} × {fl.ny} (шаг {_sci(fl.units.dx)} м, dt "
                         f"{_sci(fl.units.dt)} с) переносом движка, как при смене сетки на ходу (он занял один шаг "
                         f"прежней сетки)")
        try:
            rep = fl.adopt(old)
        except (ValueError, L.Unstable) as e:
            self.carry_note(f"течение начато заново из покоя: {e}", restarted=True)
            return
        if not notes:
            notes.append(f"течение перенесено как было ({fl.nx} × {fl.ny} узлов, тот же шаг по времени)")
        if not math.isclose(old.nu, self.nu, rel_tol=1e-12):
            notes.append(f"вязкость {_sci(old.nu)} → {_sci(self.nu)} м²/с: вязкое напряжение подстроится за несколько "
                         f"шагов")
        if not math.isclose(old.units.rho, self.rho, rel_tol=1e-12):
            notes.append(f"плотность {_sci(old.units.rho)} → {_sci(self.rho)} кг/м³: течение то же, давления и силы — в "
                         f"новом масштабе")
        if rep["rest"]:
            notes.append(f"{rep['rest']} узлов, где у прежнего мира было тело, начаты в покое")
        if rep["dye"] == "zero":
            notes.append("краситель в этом мире начат с нуля (в прежнем его не было)")
        elif rep["dye"] == "dropped":
            notes.append("краситель прежнего мира не перенесён: здесь он выключен")
        lost = [n for n, sd in fl._sides.items() if isinstance(sd, L.Inlet) and n not in rep["ramps"]]
        if lost:
            notes.append("разгон входа начат заново: " + ", ".join(lost))
        notes.append("балансы считаются от перенесённого состояния")
        for n in notes:
            self.carry_note(n)

    def scene(self, args):
        # a copy lands on its original by design (lfviz.playground): this section moves a body's copy aside (U4)
        self._dup = args.get("op") == "duplicate"
        try:
            return super().scene(args)
        finally:
            self._dup = False

    def on_add(self, obj, state):
        try:
            self._on_add(obj, state)
        except ValueError as e:
            raise self._ru(e) from e

    def _on_add(self, obj, state):
        t, v = obj["type"], obj["values"]
        fl = self.fl
        if t in ("disk", "rect", "airfoil"):
            self._inside(t, v)
            if self._dup:
                self._free_body(t, v)
            oid = fl.add_obstacle(self._shape(obj), velocity=(v.get("vx", 0.0), v.get("vy", 0.0)),
                                  omega=v.get("omega", 0.0), interpolated=v.get("wall") == "interpolated",
                                  label=obj["label"], ref_length=self._ref_len(obj))
            self.ref[obj["id"]] = ("obstacle", oid)
        elif t in ("inlet", "outlet", "lid", "periodic"):
            sides = self._side_obj(obj)
            self._claim(obj, sides)
            fl.set_sides(sides)
            for sd in sides:
                self.side_owner[sd] = obj["id"]
            self.ref[obj["id"]] = ("side", tuple(sides))
        elif t == "gravity":
            self._set_gravity(v)
            self.ref[obj["id"]] = ("gravity",)
        elif t == "dye_source":
            if self.D is None:
                raise refusal("в этом мире краситель выключен", hint="включите «Краситель» в «Установке» (на ходу)")
            self._point_inside(v)
            shape = L.Disk((v["x"], v["y"]), v["radius"])
            if v["mode"] == "drop":
                fl.add_dye(shape, concentration=float(v["concentration"]), mode="add")
                self.ref[obj["id"]] = ("drop",)
            else:
                self.ref[obj["id"]] = ("dye", fl.add_dye_source(shape, concentration=float(v["concentration"]),
                                                                label=obj["label"]))
        elif t == "probe":
            self._point_inside(v)
            self.ref[obj["id"]] = ("probe",)
        self._changed()

    def _point_inside(self, v):
        Lx, Ly = self.size
        if not (0.0 <= float(v["x"]) <= Lx and 0.0 <= float(v["y"]) <= Ly):
            raise refusal(f"точка ({_num(float(v['x']), 4)}, {_num(float(v['y']), 4)}) м — вне области {_sci(Lx)} × {_sci(Ly)} м",
                          hint=f"x от 0 до {_sci(Lx)} м, y от 0 до {_sci(Ly)} м")

    def _set_gravity(self, v):
        g = (float(v["gx"]), float(v["gy"]))
        try:
            self.fl.set_gravity(g)
        except ValueError as e:
            gm = math.hypot(*g)
            lim = self.fl.gravity_limit(g) if gm > 0 else 0.0
            raise refusal(f"объёмная сила {_num(gm, 3)} м/с² для слабосжимаемой схемы этого мира велика (гидростатический "
                          f"перепад плотности превысил бы 4,5 %): она выдерживает до {_num(_nice(lim), 3)} м/с²",
                          hint=f"|g| не больше {_num(_nice(lim), 3)} м/с², или «Наибольшая ожидаемая скорость» не меньше "
                               f"{_sci(self._u_for_g(gm, lim))} м/с (новый мир)", detail=str(e)) from e

    def on_remove(self, obj):
        kind = self.ref.get(obj["id"], (None,))
        fl = self.fl
        if kind[0] == "obstacle":
            fl.remove_obstacle(kind[1])
        elif kind[0] == "side":
            fl.set_sides({sd: L.Wall() for sd in kind[1]})
            for sd in kind[1]:
                self.side_owner.pop(sd, None)
        elif kind[0] == "gravity":
            fl.set_gravity((0.0, 0.0))
        elif kind[0] == "dye":
            fl.remove_dye_source(kind[1])
        self.ref.pop(obj["id"], None)
        self._changed()

    def on_set(self, obj, old):
        try:
            self._on_set(obj, old)
        except ValueError as e:
            raise self._ru(e) from e

    def _on_set(self, obj, old):
        t, v = obj["type"], obj["values"]
        kind = self.ref[obj["id"]]
        fl = self.fl
        if kind[0] == "obstacle":
            self._inside(t, v)
            fl.update_obstacle(kind[1], shape=self._shape(obj), velocity=(v.get("vx", 0.0), v.get("vy", 0.0)),
                               omega=v.get("omega", 0.0), interpolated=v.get("wall") == "interpolated",
                               label=obj["label"], ref_length=self._ref_len(obj))
        elif kind[0] == "side":
            sides = self._side_obj(obj)
            self._claim(obj, sides)
            new = {sd: L.Wall() for sd in kind[1] if sd not in sides}
            new.update(sides)
            fl.set_sides(new)  # an inlet whose velocity is unchanged keeps its ramp (engine: review B7 L1)
            for sd in kind[1]:
                self.side_owner.pop(sd, None)
            for sd in sides:
                self.side_owner[sd] = obj["id"]
            self.ref[obj["id"]] = ("side", tuple(sides))
        elif kind[0] == "gravity":
            self._set_gravity(v)
        elif kind[0] in ("dye", "drop"):
            self._point_inside(v)
            if kind[0] == "dye":
                fl.remove_dye_source(kind[1])
            self.ref.pop(obj["id"])
            self._on_add(obj, None)
            return
        elif kind[0] == "probe":
            self._point_inside(v)
        self._changed()

    def _changed(self):
        """After a change of the scene: the outlines, and the force record's block (the sound period depends on the
        sides; the engine restarts the record itself when the flow's set-up changed)."""
        self._shapes()
        if not self._loading:
            self._record_setup()

    def emit_scene(self):
        super().emit_scene()
        self.emit({"type": "approximations", "t": self.t, "approximations": self._approx()})

    # --- live laws (review UX-ui U12) ------------------------------------------------------------------------------
    def live_values(self):
        return dict(self.live)

    def set_live(self, values):
        """The fluid's viscosity and density, the collision operator and the dye at the current moment: the populations
        stay (the density ratio and the velocity of every node are kept: mass and momentum do not jump in lattice
        units), the next steps use the new rates; a new ρ rescales pressures and forces; the dye switched off books its
        amount as removed (its balance closes again when it comes back, zero). The grid, the domain and the largest
        expected speed (plan P16.1): the flow is moved to the new grid or time step (``Flow2D.remap``, ``_regrid``). What
        the scheme cannot carry is refused, the world as it was (all or nothing)."""
        new, errors = SCHEMA.coerce_live(self.live, values or {})
        if errors:
            raise refusal("; ".join(errors))
        changed = {k: v for k, v in new.items() if self.live.get(k) != v}
        if not changed:
            return ""
        fl = self.fl
        old = dict(self.live)
        if "dye" in changed and new["dye"] == "off":
            srcs = [o["label"] for o in self.objects.values() if o["type"] == "dye_source"]
            if srcs:
                raise refusal("краситель нельзя выключить, пока в сцене есть его источники: " + ", ".join(srcs),
                              hint="сначала уберите их из сцены")
        if "nu" in changed:
            try:
                fl._check_numbers(float(new["nu"]), fl.u_max)
            except ValueError as e:
                raise self._ru(e) from e
        D_new = (float(new["dye_D"]) or float(new["nu"])) if new["dye"] == "on" else None
        try:
            if "nu" in changed:
                fl.set_viscosity(float(new["nu"]))
            if "rho" in changed:
                fl.set_density(float(new["rho"]))
            if "collision" in changed:
                fl.set_collision(new["collision"])
            if D_new is None and self.D is not None:
                fl.disable_dye()
            elif D_new is not None and D_new != self.D:
                fl.set_dye_diffusivity(D_new)   # switches it on (zero) when it was off
        except ValueError as e:
            self._live_back(old)
            raise self._ru(e) from e
        self.nu, self.rho = float(new["nu"]), float(new["rho"])
        regrid = ""
        if any(k in changed for k in GRID):
            try:
                regrid = self._regrid(new, old)
            except Exception:
                self.nu, self.rho = float(old["nu"]), float(old["rho"])
                self._live_back(old)
                raise
            changed = {k: new[k] for k in changed if k not in GRID or new[k] != old[k]}
        self.live, self.D = dict(new), D_new
        if self.D is None and self.shown == "dye":
            self.shown = "speed"
        self._record_setup()
        self.emit({"type": "approximations", "t": self.t, "approximations": self._approx()})
        self.emit_picture()

        def show(k, v):
            p = SCHEMA.by_id[k]
            if p.options:
                return dict(p.options).get(v, v)
            return str(v) if p.type == "int" else _sci(float(v))
        labels = ", ".join(f"{SCHEMA.by_id[k].label} = {show(k, v)}" for k, v in changed.items())
        what = []
        if "nu" in changed:
            what.append("скорость и давление прежние, вязкое напряжение подстраивается за несколько шагов")
        if "rho" in changed:
            what.append(f"давления и силы — в масштабе ρ (×{_num(float(new['rho']) / float(old['rho']), 3)})")
        if "dye" in changed:
            what.append("краситель выключен (его количество учтено как убранное)" if D_new is None
                        else "краситель включён (пока нулевой)")
        if regrid:
            what.append(regrid)
        return f"законы на ходу: {labels}" + (f"; {'; '.join(what)}" if what else "") + "; окно средних сил — заново"

    def _anchor_shift(self, anchor, grow, dx):
        """Where the present domain's origin lands in the new one (m) when it grows by ``grow`` (m, < 0: shrinks)."""
        if anchor == "left_bottom":
            return grow
        if anchor == "center":
            return round(0.5 * grow / dx) * dx
        return 0.0

    def _regrid(self, new, old):
        """The grid (nx), the domain (Lx, Ly) and the largest expected speed (u_max) changed now (plan P16.1): the flow
        goes on on the new grid or time step (``Flow2D.remap``: the pre-collision populations' pressure, velocity and
        non-equilibrium part moved to the new nodes, the latter rescaled with the relaxation times — Dupuis & Chopard's
        grid-refinement transfer; a new part of the domain at rest or with the inflow, as chosen; the bodies
        re-voxelised). A change of nx changes the spacing (dx = Lx / nx); a change of Lx or Ly keeps it (cells added or
        cut at the side ``anchor`` names; objects keep their place in the fluid, so with the left or the middle anchor
        their coordinates move). Refused, with the world as it was: a grid beyond the memory budget, a domain that would
        cut a body, a dye source or leave a probe outside, a grid or time step the scheme cannot run. ``new`` gets the
        values in force (the domain rounded to whole cells). Returns the event's text: the grids, the time steps, the
        mass and momentum before and after and what the transfer changed."""
        fl = self.fl
        dx0, (Lx0, Ly0) = fl.units.dx, self.size
        Lx_req, Ly_req = float(new["Lx"]), float(new["Ly"])
        if new["nx"] != old["nx"]:
            dx1 = Lx_req / int(new["nx"])
        else:
            dx1 = dx0
        nx1 = max(2, int(round(Lx_req / dx1)))
        ny1 = max(8, int(round(Ly_req / dx1)))
        Lx1, Ly1 = nx1 * dx1, ny1 * dx1
        sx = self._anchor_shift(new["anchor"], Lx1 - Lx0, dx1)
        sy = self._anchor_shift(new["anchor"], Ly1 - Ly0, dx1)
        um = float(new["u_max"])
        dye = self.D is not None
        need = L.Flow2D.memory_estimate(nx1, ny1, dye)
        budget = _budget()
        if need > budget:
            raise refusal(f"сетка {nx1} × {ny1} узлов (шаг {_sci(dx1)} м) потребует ≈ {_fmt_bytes(need)} памяти, больше "
                          f"предела {_fmt_bytes(budget)}", hint=self._grid_hint({"Lx": Lx1, "Ly": Ly1, "nx": nx1,
                                                                               "dye": "on" if dye else "off"}, budget))
        try:
            from lfviz import limits
            limits.require(fl.remap_memory_estimate(nx1, ny1), f"перенос течения на сетку {nx1} × {ny1} узлов",
                           "меньше узлов или меньшая область")
        except ImportError:  # an older framework without limits: the estimate above holds
            pass
        for o in self.objects.values():  # probes and dye drops must stay in the fluid (the engine checks the sources)
            if o["type"] in ("probe", "dye_source"):
                x, y = float(o["values"]["x"]) + sx, float(o["values"]["y"]) + sy
                if not (0.0 <= x <= Lx1 and 0.0 <= y <= Ly1):
                    raise refusal(f"«{o['label']}» оказался бы вне новой области {_sci(Lx1)} × {_sci(Ly1)} м",
                                  hint="сдвиньте или уберите его, или уменьшайте область с другой стороны")
        inflow = any(isinstance(v, L.Inlet) for v in fl._sides.values())
        dfg0 = self._dfg_case()
        # the pressure integral now: the transfer keeps the pressure, so the scheme's density deviation p / c_s^2 (and the
        # lattice mass with it) changes with the scheme's sound speed (review LB1-p02-ux X14)
        Ip = float(np.nansum(fl.fields()["p"])) * dx0 * dx0
        cs0 = fl.units.c * L.CS
        try:
            rep = fl.remap(dx=dx1, size=(Lx1, Ly1), shift=(sx, sy), u_max=um, fill=new["fill"])
        except ValueError as e:
            raise self._ru(e) from e
        moved = sx != 0.0 or sy != 0.0
        if moved:
            for o in self.objects.values():
                if "x" in o["values"] and "y" in o["values"]:
                    o["values"] = {**o["values"], "x": float(o["values"]["x"]) + sx, "y": float(o["values"]["y"]) + sy}
        self.size = fl.size
        self.u_max = um
        if um != float(old["u_max"]):
            self.u_note = None
        new.update(Lx=fl.size[0], Ly=fl.size[1], nx=fl.nx, u_max=um)
        self.PALETTE = palette(self.size, self.u_max, self._g_default())
        h = 0.04 * max(self.size)
        self.emit({"type": "box", "t": self.t, "box": [[0.0, 0.0, -h], [self.size[0], self.size[1], h]]})
        self._shapes()
        if moved:
            self.rev += 1
            self.emit_scene()
        b, a, tr = rep["before"], rep["after"], rep["transfer"]

        def mom(v):
            return f"({_num(v[0], 4)}; {_num(v[1], 4)})"
        parts = [f"сетка {b['nodes'][0]} × {b['nodes'][1]} → {a['nodes'][0]} × {a['nodes'][1]} узлов (шаг "
                 f"{_sci(b['dx'])} → {_sci(a['dx'])} м), шаг по времени {_sci(b['dt'])} → {_sci(a['dt'])} с (τ "
                 f"{_num(b['tau_plus'], 3)} → {_num(a['tau_plus'], 3)})"]
        if rep["new_part"] > 0:
            parts.append(f"новая часть области ({_num(100 * rep['new_part'], 2)} %) — "
                         + ("с входящим потоком" if rep["fill"] == "inflow" else "в покое")
                         + (" (входа нет: в покое)" if new["fill"] == "inflow" and not inflow else ""))
        if moved:
            parts.append(f"область выросла или уменьшилась {ANCHOR_RU[new['anchor']]}: координаты тел, красителя и "
                         f"датчиков сдвинуты на ({_num(sx, 4)}; {_num(sy, 4)}) м вместе с жидкостью")
        if new["nx"] != old["nx"] and not math.isclose(Ly1, Ly_req, rel_tol=1e-9):
            keep = self._nx_keeping(Lx_req, Ly_req, int(new["nx"]))
            parts.append(f"высота области {_num(Ly_req, 6)} → {_num(Ly1, 6)} м: при шаге {_num(dx1, 4)} м по y помещается целое "
                         f"число ячеек ({ny1})" + (f"; обе длины сохраняют nx = {', '.join(map(str, keep))}" if keep else ""))
        if dfg0 and not self._dfg_case():
            parts.append("постановка DFG больше не узнаётся (размеры канала изменились): её «Эталоны» не показываются")
        cs1 = fl.units.c * L.CS
        dm_cs = Ip * (1.0 / cs1**2 - 1.0 / cs0**2)
        m_inc = self.rho * float(np.sum(~fl.solid())) * fl.units.dx ** 2
        parts.append(f"масса {_num(b['mass'], 6)} → {_num(a['mass'], 6)} кг/м, импульс {mom(b['momentum'])} → "
                     f"{mom(a['momentum'])} кг/(м·с); перенос изменил массу на {_num(tr['mass'], 3)} кг/м "
                     f"({_num(100 * tr['mass'] / b['mass'], 3)} %) и импульс на {mom(tr['momentum'])}")
        why = []
        if not math.isclose(cs1, cs0, rel_tol=1e-9):
            why.append(f"{_num(dm_cs, 3)} кг/м — сжимаемость схемы, не жидкости: давление перенесено как было, а "
                       f"плотность схемы при том же давлении ρ − ρ₀ = p/c_s², а скорость звука схемы (u_max/"
                       f"{_num(fl.mach_target, 2)}, больше — где шаг ограничен временем релаксации) сменилась "
                       f"{_num(cs0, 4)} → {_num(cs1, 4)} м/с")
        if rep["new_part"] > 0:
            why.append(f"≈ {_num(self.rho * rep['new_part'] * fl.size[0] * fl.size[1], 3)} кг/м — жидкость новой части "
                       f"области")
        if b["nodes"] != a["nodes"]:
            why.append("остальное — интерполяция на новые узлы и тела, заново разложенные по узлам")
        if why:
            parts.append("из этого " + "; ".join(why) + f"; масса несжимаемой жидкости ρ·S = {_num(m_inc, 6)} кг/м")
        parts.append("перенос записан в балансы как «перенос» (remap): проверки балансов сходятся по построению и ошибку "
                     "самого переноса не видят; его точность — тесты движка (Пуазейль — до округления, Тейлор–Грин — "
                     "с точностью схемы) и «Эталоны» этого мира (остальное — шаг течения)")
        parts.append(f"течение продолжено: давление и скорость перенесены, неравновесная часть популяций пересчитана "
                     f"(×{_num(rep['factors']['neq_plus'], 3)}), перенос занял один шаг прежней сетки")
        return "; ".join(parts)

    @staticmethod
    def _nx_keeping(Lx, Ly, nx):
        """Up to two numbers of nodes along x nearest ``nx`` (within the schema's 16 … 8192) whose spacing Lx / n fits
        a whole number of cells into Ly too (review LB1-physics P14)."""
        out = []
        for n in sorted(range(16, 8193), key=lambda k: (abs(k - nx), k)):
            m = Ly * n / Lx
            if abs(m - round(m)) <= 1e-9 * max(1.0, m) and round(m) >= 8:
                out.append(n)
                if len(out) == 2:
                    break
        return out

    def _live_back(self, old):
        """Put the engine's live laws back as they were (a later setter of the same change refused)."""
        fl = self.fl
        fl.set_viscosity(float(old["nu"]))
        fl.set_density(float(old["rho"]))
        fl.set_collision(old["collision"])
        D_old = self.D
        if D_old is None:
            if fl.dye_D is not None and not fl.dye_sources():
                fl.disable_dye()
        elif fl.dye_D != D_old:
            fl.set_dye_diffusivity(D_old)

    # --- time ----------------------------------------------------------------------------------------------------
    def advance(self, t_target):
        if t_target > self.fl.t:
            try:
                self.fl.advance_to(t_target)
            except L.Unstable as e:
                raise RuntimeError(f"течение потеряло устойчивость (мир остановлен в состоянии до шага): {e}. "
                                   f"Уменьшите скорости или увеличьте «наибольшую ожидаемую скорость» в законах "
                                   f"мира (новый мир)") from e
        self.t = max(self.t, t_target)

    def max_step(self):
        """At most MAX_STEPS lattice steps per advance call, fewer when the CPU's measured rate (``lbm.RATES``, a fixed
        table: deterministic) makes one call longer than FRAME_S: a large grid keeps the frames and the commands flowing
        (review UX-params P25: one frame of a 4·10⁶-node grid took minutes). The flow does not depend on the cut: the
        engine steps to the step nearest each target."""
        per = L._interp_rate("cpu", self.fl.N)
        return int(min(MAX_STEPS, max(1, FRAME_S / per))) * self.fl.units.dt

    # --- the forces' window ----------------------------------------------------------------------------------------
    def _record_setup(self):
        """The forces are recorded in blocks of 1/``WINDOW_BLOCKS`` of the domain's slowest sound period (whole
        steps); the mean shown is over the last ``WINDOW_BLOCKS`` blocks, i.e. one whole period to within half a block
        (the scheme's standing sound wave averages out: review B7 L4)."""
        ap = self.fl.acoustic_period()
        dt = self.fl.units.dt
        T_steps = ap["period"] / dt
        k = max(1, int(T_steps // WINDOW_BLOCKS))
        n = max(1, int(round(T_steps / k)))
        self.win = {"every": k, "n": n, "period": ap["period"], "axis": ap["axis"],
                    "kind": ap[ap["axis"]]["kind"], "length": ap[ap["axis"]]["length"], "c_s": ap["c_s"]}
        rec = self.fl.force_record()
        if rec is None or rec["every"] != k:
            self.fl.record_forces(k, keep=max(8 * n, 1024))

    def _window(self, eid):
        """The mean force (N/m) on obstacle ``eid`` over the last whole window, with the window; or the time it will be
        ready."""
        r = self.fl.force_record()
        if r is None or self.win is None:
            return None
        n = self.win["n"]
        t = r["t_end"]
        if len(t) < n or eid not in r["obstacles"]:
            return {"ready_at": r["since"] + n * r["block"]}
        F = r["obstacles"][eid]["force"][-n:]
        return {"force": F.mean(axis=0), "t0": float(t[-n] - r["block"]), "t1": float(t[-1])}

    def _window_text(self, w):
        return (f"{_num(w['t0'], 4)} … {_num(w['t1'], 4)} с (период звука {KIND_RU[self.win['kind']]} = "
                f"{_num(self.win['period'], 4)} с, вдоль {self.win['axis']}, c_s = {_num(self.win['c_s'], 4)} м/с)")

    def _coeffs(self, F, vec):
        q = 0.5 * self.rho * F["u_ref"] ** 2 * F["length"]
        return (float(vec[0]) / q, float(vec[1]) / q) if q > 0 else (float("nan"), float("nan"))

    # --- frames --------------------------------------------------------------------------------------------------
    def _at(self, x, y):
        fl = self.fl
        i = int(np.clip(np.rint((x - fl.x[0]) / fl.units.dx), 0, fl.nx - 1))
        j = int(np.clip(np.rint((y - fl.y[0]) / fl.units.dx), 0, fl.ny - 1))
        return i, j

    def _body_at(self, i, j):
        for oid, k in self.ref.items():
            if k[0] == "obstacle" and self.fl.shape_mask(self._shape(self.objects[oid]))[i, j]:
                return self.objects[oid]["label"]
        return None

    def frame(self):
        fl = self.fl
        now, probes, ids = {}, {}, []
        rates = fl.flow_rates()
        f = fl.fields()
        om = fl.vorticity()
        dye = fl.dye() if self.D else None
        for oid, kind in self.ref.items():
            o = self.objects[oid]
            if kind[0] == "obstacle" and (F := self._force(oid, kind[1])):
                w = self._window(kind[1])
                r = {}
                if w and "force" in w:
                    cx, cy = self._coeffs(F, w["force"])
                    r.update({"C_x, среднее за период звука": cx, "C_y, среднее за период звука": cy,
                              "сопротивление, среднее, Н/м": float(w["force"][0]),
                              "подъёмная сила, средняя, Н/м": float(w["force"][1]),
                              "окно среднего": self._window_text(w)})
                elif w:
                    r["C_x, C_y средние за период звука"] = f"окно набирается: до t = {_num(w['ready_at'], 4)} с"
                r.update({"C_x за последний шаг (со звуком схемы)": F["cd"],
                          "C_y за последний шаг (со звуком схемы)": F["cl"], "момент за последний шаг, Н": F["torque"],
                          "Re (по длине и скорости для коэффициентов)": F["u_ref"] * F["length"] / self.nu})
                now[oid] = r
            elif kind[0] == "side":
                now[oid] = {f"расход {SIDE_RU[sd]}, кг/(с·м)": rates.get(sd, 0.0) for sd in kind[1]}
                if o["type"] == "inlet":
                    sc = fl.inlet_scales()
                    now[oid].update({f"разгон {SIDE_RU[sd]} (0…1)": sc[sd] for sd in kind[1] if sd in sc})
                if o["type"] == "lid":  # Re of a driven cavity: the wall's speed and length
                    side_len = self.size[0] if o["values"]["side"] in ("bottom", "top") else self.size[1]
                    now[oid]["Re = U·L/ν"] = abs(float(o["values"]["speed"])) * side_len / self.nu
            elif kind[0] == "probe":
                i, j = self._at(o["values"]["x"], o["values"]["y"])
                if not math.isfinite(float(f["ux"][i, j])):   # inside a body: no fluid there (UX-params P27)
                    body = self._body_at(i, j)
                    r = {"где": f"внутри тела{f' «{body}»' if body else ''}: здесь нет жидкости — сдвиньте датчик"}
                else:
                    r = {"ux, м/с": float(f["ux"][i, j]), "uy, м/с": float(f["uy"][i, j]),
                         "|u|, м/с": float(math.hypot(f["ux"][i, j], f["uy"][i, j])),
                         "p, Па": float(f["p"][i, j]), "ω, 1/с": float(om[i, j])}
                    if dye is not None:
                        r["краситель"] = float(dye[i, j])
                probes[oid] = r
                ids.append(oid)
        if self.check_due():
            self.checks()
        if self.n_pic % PIC_EVERY == 0:
            self.emit_picture(f, om, dye)
        self.n_pic += 1
        nb = fl.numbers()
        meas, notes = self._meas(f, rates, nb)
        out = {"ids": ids, "now": now, "probes": probes, "steps": int(fl.steps), "re": nb.get("re"),
               "mach": nb.get("mach_max"), "at": self._at_all(), "meas": meas}
        if notes:
            out["meas_note"] = notes
        return out, {}

    # --- positions and measurables (P16.2, P16.3) ----------------------------------------------------------------------
    def _at_all(self):
        """Where every positioned object is (m, the plane z = 0): its handle's x, y (a profile's leading edge)."""
        return {oid: [float(o["values"]["x"]), float(o["values"]["y"]), 0.0] for oid, o in self.objects.items()
                if o["type"] in ("disk", "rect", "airfoil", "dye_source", "probe")}

    def measurables(self):
        """The quantities the instruments record (P16.3): per body its drag and lift coefficients (over the last step and
        averaged over the domain's slowest sound period) and its forces; per probe the velocity and the pressure; per side
        object the mass flow through its side; for the world the balances' residuals, the Reynolds and Mach numbers and
        the net inflow."""
        out = []
        for oid, o in self.objects.items():
            lab, t = o["label"], o["type"]
            if t in ("disk", "rect", "airfoil"):
                out += [{"id": f"{oid}.cd", "label": f"«{lab}»: C_x за последний шаг (со звуком схемы)", "unit": "",
                         "of": oid, "group": "Тела"},
                        {"id": f"{oid}.cl", "label": f"«{lab}»: C_y за последний шаг (со звуком схемы)", "unit": "",
                         "of": oid, "group": "Тела"},
                        {"id": f"{oid}.cd_mean", "label": f"«{lab}»: C_x, среднее за период звука", "unit": "",
                         "of": oid, "group": "Тела"},
                        {"id": f"{oid}.cl_mean", "label": f"«{lab}»: C_y, среднее за период звука", "unit": "",
                         "of": oid, "group": "Тела"},
                        {"id": f"{oid}.fx", "label": f"«{lab}»: сила вдоль x (сопротивление)", "unit": "Н/м", "of": oid,
                         "group": "Тела"},
                        {"id": f"{oid}.fy", "label": f"«{lab}»: сила вдоль y (подъёмная)", "unit": "Н/м", "of": oid,
                         "group": "Тела"}]
            elif t == "probe":
                out += [{"id": f"{oid}.ux", "label": f"«{lab}»: скорость u_x", "unit": "м/с", "of": oid,
                         "group": "Датчики"},
                        {"id": f"{oid}.uy", "label": f"«{lab}»: скорость u_y", "unit": "м/с", "of": oid,
                         "group": "Датчики"},
                        {"id": f"{oid}.speed", "label": f"«{lab}»: модуль скорости |u|", "unit": "м/с", "of": oid,
                         "group": "Датчики"},
                        {"id": f"{oid}.p", "label": f"«{lab}»: давление (относительное)", "unit": "Па", "of": oid,
                         "group": "Датчики"}]
            elif t in ("inlet", "outlet", "lid"):
                out.append({"id": f"{oid}.q", "label": f"«{lab}»: расход в область через сторону", "unit": "кг/(с·м)",
                            "of": oid, "group": "Расходы"})
        out += [{"id": "q_net", "label": "Суммарный расход в область (все стороны)", "unit": "кг/(с·м)", "of": None,
                 "group": "Расходы"},
                {"id": "mass_res", "label": "Невязка баланса массы (доля массы)", "unit": "", "of": None,
                 "group": "Балансы"},
                {"id": "mom_res", "label": "Невязка баланса импульса (на массу решётки)", "unit": "", "of": None,
                 "group": "Балансы"},
                {"id": "re", "label": "Число Рейнольдса Re (длина тела и скорость входа)", "unit": "", "of": None,
                 "group": "Числа"},
                {"id": "mach", "label": "Число Маха решётки, наибольшее", "unit": "", "of": None, "group": "Числа"}]
        return out

    def measure(self):
        """The measurables' values now (``meas`` of a frame without the picture; the sweeps read it)."""
        fl = self.fl
        return self._meas(fl.fields(), fl.flow_rates(), fl.numbers())[0]

    def _meas(self, f, rates, nb):
        """({measurable id: value in its unit}, {id: why it is undefined}) from the fields, rates and numbers of now."""
        fl = self.fl
        m, notes = {}, {}
        for oid, kind in self.ref.items():
            o = self.objects[oid]
            if kind[0] == "obstacle":
                F = self._force(oid, kind[1])
                if not F:
                    continue
                m[f"{oid}.cd"], m[f"{oid}.cl"] = float(F["cd"]), float(F["cl"])
                m[f"{oid}.fx"], m[f"{oid}.fy"] = float(F["force"][0]), float(F["force"][1])
                w = self._window(kind[1])
                if w and "force" in w:
                    m[f"{oid}.cd_mean"], m[f"{oid}.cl_mean"] = self._coeffs(F, w["force"])
                else:
                    m[f"{oid}.cd_mean"] = m[f"{oid}.cl_mean"] = float("nan")
                    why = (f"окно среднего за период звука набирается: до t = {_num(w['ready_at'], 4)} с" if w
                           else "запись сил не идёт")
                    notes[f"{oid}.cd_mean"] = notes[f"{oid}.cl_mean"] = why
            elif kind[0] == "probe":
                i, j = self._at(o["values"]["x"], o["values"]["y"])
                vals = (float(f["ux"][i, j]), float(f["uy"][i, j]), float(f["p"][i, j]))
                if all(math.isfinite(v) for v in vals):
                    m[f"{oid}.ux"], m[f"{oid}.uy"], m[f"{oid}.p"] = vals
                    m[f"{oid}.speed"] = math.hypot(vals[0], vals[1])
                else:
                    for k in ("ux", "uy", "speed", "p"):
                        m[f"{oid}.{k}"] = float("nan")
                        notes[f"{oid}.{k}"] = "датчик внутри тела: здесь нет жидкости"
            elif kind[0] == "side" and o["type"] in ("inlet", "outlet", "lid"):
                m[f"{oid}.q"] = float(sum(rates.get(sd, 0.0) for sd in kind[1]))
        m["q_net"] = float(sum(rates.values()))
        b = fl.balance()
        m["mass_res"] = float(b["mass"]["relative_residual"])
        m["mom_res"] = float(b["momentum"]["relative_residual"])
        m["re"] = float(nb.get("re") or float("nan"))
        m["mach"] = float(nb.get("mach_max") or 0.0)
        return m, notes

    def emit_picture(self, f=None, om=None, dye=None):
        """The field shown (``view`` op "field"), 8-bit (255 = solid), and the velocity arrows: drawing only."""
        fl = self.fl
        if f is None:
            f, om = fl.fields(), fl.vorticity()
            dye = fl.dye() if self.D else None
        name = self.shown if (self.shown != "dye" or dye is not None) else "speed"
        if name == "speed":
            a = np.hypot(f["ux"], f["uy"])
            lo, hi, note = 0.0, None, "м/с"
        elif name == "vorticity":
            a, note = om, "1/с (0 — середина шкалы)"
            lo = hi = None
        elif name == "pressure":
            a, note = f["p"], "Па"
            lo = hi = None
        else:
            a, lo, hi, note = dye, 0.0, 1.0, "доля"
        a = np.asarray(a, float)
        solid = ~np.isfinite(a)
        fin = a[~solid]
        if name == "vorticity":  # symmetric about zero (the middle of the scale), also for a fluid at rest
            m = (float(np.percentile(np.abs(fin), 99.0)) if fin.size else 0.0) or 1.0
            lo, hi = -m, m
        if lo is None:
            lo = float(fin.min()) if fin.size else 0.0
        if hi is None:
            hi = float(fin.max()) if fin.size else 1.0
        if not hi > lo:
            hi = lo + 1.0
        val, frac = resample(a, ~solid, IMG_MAX)
        img = np.clip((val - lo) / (hi - lo), 0.0, 1.0)
        u8 = np.where(frac < 0.5, 255, np.round(254 * img)).astype(np.uint8)
        self.emit({"type": "field", "t": self.t, "name": name, "label": FIELDS[name], "unit": note,
                   "range": [lo, hi], "shape": list(u8.shape), "size": list(self.size)}, {"img": u8})
        # velocity arrows on a coarse grid (z = 0 plane)
        s = max(1, int(math.ceil(max(fl.nx, fl.ny) / ARROWS)))
        ii, jj = np.meshgrid(np.arange(s // 2, fl.nx, s), np.arange(s // 2, fl.ny, s), indexing="ij")
        ux, uy = f["ux"][ii, jj], f["uy"][ii, jj]
        ok = np.isfinite(ux) & np.isfinite(uy)
        pos = np.stack([fl.x[ii][ok], fl.y[jj][ok], np.full(ok.sum(), 0.01 * self.size[0])], 1)
        vec = np.stack([ux[ok], uy[ok], np.zeros(ok.sum())], 1)
        self.emit({"type": "vectors", "t": self.t, "id": "flow"},
                  {"pos": pos.astype(np.float32).reshape(-1), "vec": vec.astype(np.float32).reshape(-1)})

    def view(self, args):
        if args.get("op") != "field" or args.get("field") not in FIELDS:
            raise ValueError("поле картины: speed | vorticity | pressure | dye")
        self.shown = args["field"]
        self.emit_picture()
        return f"картина: {FIELDS[self.shown]}"

    def view_state(self):
        return {"field": self.shown}

    def adopt_view(self, state):
        if isinstance(state, dict) and state.get("field") in FIELDS:
            self.shown = state["field"]

    # --- checks ----------------------------------------------------------------------------------------------------
    def checks(self):
        fl = self.fl
        names = {"mass": ("Масса жидкости (баланс с притоком и оттоком)", "Законы сохранения"),
                 "momentum": ("Импульс жидкости (баланс с силами и потоками)", "Законы сохранения"),
                 "dye": ("Количество красителя (баланс)", "Законы сохранения"),
                 "mach": ("Число Маха решётки (ошибка сжимаемости ~ Ma²)", "Применимость"),
                 "re_cell": ("Число Рейнольдса ячейки u·dx/ν (предел устойчивости, не точности)", "Применимость"),
                 "compressibility": ("Перепад плотности (мера ошибки сжимаемости)", "Применимость")}
        for key, c in fl.checks().items():
            lab, grp = names.get(key, (key, "Проверки"))
            val = c.get("relative_residual", c.get("value", c.get("residual")))
            conserved = key in ("mass", "momentum", "dye")
            self.running_check(key, lab, val, 0.0 if conserved else None, float(c.get("limit", 0.0) or 0.0),
                               group=grp, ok=c.get("ok"), info="ok" not in c,
                               note=(f"допуск {_num(c['limit'], 3)}" if "limit" in c else "") + (
                                   f"; {c['note']}" if c.get("note") else ""))
        for oid, kind in self.ref.items():
            if kind[0] != "obstacle":
                continue
            F = self._force(oid, kind[1])
            if not F:
                continue
            lab = self.objects[oid]["label"]
            re = F["u_ref"] * F["length"] / self.nu
            basis = (f"Re = {_num(re, 4)} (длина {_num(F['length'], 4)} м, скорость {_num(F['u_ref'], 4)} м/с); силы — по обмену "
                     f"импульсом на стенке")
            w = self._window(kind[1])
            if w and "force" in w:
                cx, cy = self._coeffs(F, w["force"])
                self.running_check(f"cd_{oid}", f"«{lab}»: C_x, среднее за период звука", cx, None, 0.0, info=True,
                                   group="Силы", note=f"C_y среднее = {_num(cy, 4)}; окно {self._window_text(w)}; за "
                                                      f"последний шаг C_x = {_num(F['cd'], 4)}, C_y = {_num(F['cl'], 4)} (несут "
                                                      f"звуковую волну схемы); {basis}")
            else:
                ready = f"; среднее за период звука набирается до t = {_num(w['ready_at'], 4)} с" if w else ""
                self.running_check(f"cd_{oid}", f"«{lab}»: C_x за последний шаг (мгновенное, со звуком схемы)",
                                   F["cd"], None, 0.0, info=True, group="Силы",
                                   note=f"C_y = {F['cl']:.4g}{ready}; {basis}")
        self._benchmark_checks()
        c = fl.cost_estimate()
        self.running_check("cost", f"Счёт: секунд на шаг ({'GPU 0' if c.get('device') == 'gpu' else 'CPU'}, "
                           f"оценка)", c.get("per_step_s"), None, 0.0, info=True, group="Расчёт", unit="с",
                           note=f"{fl.nx}×{fl.ny} узлов, шаг {_num(fl.units.dt, 3)} с; предел реального времени ≈ "
                                f"{_num(fl.units.dt / c['per_step_s'], 3)} с мира в секунду (по оценке; измеренная скорость "
                                f"зависит от часов стены — она у ползунка скорости)")

    def _force(self, oid, eid):
        """Forces on an obstacle with its own reference speed (the object's u_ref, else the engine's)."""
        u = float(self.objects[oid]["values"].get("u_ref", 0.0) or 0.0)
        return self.fl.forces(u_ref=u if u > 0 else None).get(eid)

    # --- the published benchmarks, where the scene is their set-up (review B7 L5) -------------------------------------
    def _objs(self, typ):
        return [o for o in self.objects.values() if o["type"] == typ]

    def _plain_sides(self, **want):
        """The sides are of the kinds ``want`` (side -> kind) and fixed walls elsewhere."""
        sd = self.fl.sides()
        for name in L.SIDES:
            k = want.get(name, "wall")
            if sd[name]["kind"] != k or (name not in want and sd[name]["velocity"] != 0.0):
                return False
        return True

    def _dfg_case(self):
        """("2D-1" | "2D-2", scene id, engine id) when the world is the DFG cylinder channel of Schäfer & Turek: their
        fluid and channel, a parabolic inlet of Um 0.3 or 1.5 m/s on the left, an outlet at 0 Pa on the right, plain
        walls, one fixed disk of D = 0.1 m at (0.2, 0.2), no body force."""
        G = L.DFG_GEOMETRY
        if not (math.isclose(self.nu, G["nu"], rel_tol=1e-12) and math.isclose(self.rho, G["rho"], rel_tol=1e-12)):
            return None
        if not (math.isclose(self.size[0], G["Lx"], rel_tol=1e-9) and math.isclose(self.size[1], G["H"],
                                                                                    rel_tol=1e-9)):
            return None
        if not self._plain_sides(left="inlet", right="outlet") or self._objs("gravity"):
            return None
        sd = self.fl.sides()
        inl, out = sd["left"], sd["right"]
        if inl.get("profile") != "parabolic" or inl.get("tangential") or out["pressure"] != 0.0:
            return None
        obs = [(k, v) for k, v in self.ref.items() if v[0] == "obstacle"]
        if len(obs) != 1 or self.objects[obs[0][0]]["type"] != "disk":
            return None
        v = self.objects[obs[0][0]]["values"]
        if (v["x"], v["y"], 2 * v["radius"]) != (G["center"][0], G["center"][1], G["D"]) or v["vx"] or v["vy"] \
                or v["omega"]:
            return None
        for case, ref in (("2D-1", L.DFG_2D1), ("2D-2", L.DFG_2D2)):
            if inl["velocity"] == ref["Um"]:
                return case, obs[0][0], obs[0][1][1]
        return None

    def _range_note(self, value, lo, hi, source):
        where = "внутри" if lo <= value <= hi else "вне"
        return f"диапазон {source}: {lo:.4f} … {hi:.4f} — значение {where}"

    def _benchmark_checks(self):
        fl = self.fl
        case = self._dfg_case()
        if case and min(fl.inlet_scales().values() or [1.0]) >= 1.0:
            name, oid, eid = case
            G = L.DFG_GEOMETRY
            Um = L.DFG_2D1["Um"] if name == "2D-1" else L.DFG_2D2["Um"]
            q = 0.5 * G["rho"] * (2 * Um / 3) ** 2 * G["D"]  # their U = 2 Um / 3 and D
            interp = self.objects[oid]["values"].get("wall") == "interpolated"
            cells = G["D"] / fl.units.dx
            grid = (f"сетка: D = {_num(cells, 4)} ячеек, стенка {'интерполированная' if interp else 'ступенчатая'}; "
                    f"C = 2F/(ρU²D), U = 2Um/3 = {_num(2 * Um / 3, 4)} м/с")
            if name == "2D-1":
                w = self._window(eid)
                if w and "force" in w:
                    known = ("движок в этой постановке (Ma 0,1 при Um, разгон 3 с; окна после 24 с): интерполяция "
                             "D = 20: 5,5895 / 0,010504, D = 40: 5,5791 / 0,010770 — внутри; ступеньки D = 20: "
                             "≈ 5,637 / 0,0113 — вне; пока звук старта затухает (≈ 40 % за период), среднее за один "
                             "период отклоняется от установившегося до ±0,007 к 14 с и ±0,002 к 20 с")
                    for key, lab, val in (("cD", "C_D", w["force"][0] / q), ("cL", "C_L", w["force"][1] / q)):
                        lo, hi = L.DFG_2D1[key]
                        self.running_check(f"dfg_{key}", f"DFG 2D-1: {lab}, среднее за период звука", val,
                                           0.5 * (lo + hi), 0.0, info=True, group="Эталоны",
                                           note=f"{self._range_note(val, lo, hi, 'Schäfer & Turek 1996, табл. 3')}; "
                                                f"окно {self._window_text(w)}; {grid}; {known}")
            else:
                r = fl.force_record()
                n = self.win["n"]
                if r is not None and eid in r["obstacles"] and len(r["t_end"]) >= n:
                    m = min(len(r["t_end"]), 4 * n)  # St over the last four sound periods (~5 shedding periods)
                    t = (r["t_end"] - 0.5 * r["block"])[-m:]
                    Fr = r["obstacles"][eid]["force"]
                    cd, cl = Fr[:, 0] / q, Fr[:, 1] / q
                    c = cl[-m:] - cl[-m:].mean()
                    up = np.flatnonzero((c[:-1] < 0) & (c[1:] >= 0))
                    win = (f"по средним за блоки по {_num(r['block'] * 1e3, 3)} мс: C_D max и C_L max — за последний "
                           f"период звука (блоков: {n}), St — за последние периоды звука (блоков: {m}, с t = "
                           f"{_num(t[0] - 0.5 * r['block'], 4)} с)")
                    known = ("тест движка (Ma 0,1, интерполяция, 9–12 с): D = 20: St 0,2990, C_D max 3,330, C_L max "
                             "0,979; D = 40: St 0,3009, C_D max 3,248, C_L max 0,980 (C_L max и C_D max — вне "
                             "диапазонов, причина открыта: STATUS)")
                    vals = [("cDmax", "C_D max за последний период звука", float(cd[-n:].max())),
                            ("cLmax", "C_L max за последний период звука", float(cl[-n:].max()))]
                    if len(up) >= 3:
                        tz = t[up] - c[up] * (t[up + 1] - t[up]) / (c[up + 1] - c[up])
                        vals.append(("St", f"St = f D / U (периодов C_L: {len(up) - 1})",
                                     G["D"] * (len(tz) - 1) / (tz[-1] - tz[0]) / (2 * Um / 3)))
                    for key, lab, val in vals:
                        lo, hi = L.DFG_2D2[key]
                        self.running_check(f"dfg_{key}", f"DFG 2D-2: {lab}", val, 0.5 * (lo + hi), 0.0, info=True,
                                           group="Эталоны",
                                           note=f"{self._range_note(val, lo, hi, 'Schäfer & Turek 1996, табл. 4')}; "
                                                f"{win}; {grid}; {known}; нужна развитая дорожка (≳ 5 с)")
        self._ghia_check()
        self._poiseuille_checks()
        self._force_poiseuille_check()
        self._couette_check()

    def _ghia_check(self):
        """The driven cavity of Ghia, Ghia & Shin at Re = 100: a square, a lid on top moving along +x, plain walls, no
        obstacles and no body force; the centre-line profiles against their tables."""
        fl = self.fl
        lids = self._objs("lid")
        if fl.nx != fl.ny or len(lids) != 1 or self._objs("gravity") or any(v[0] == "obstacle"
                                                                              for v in self.ref.values()):
            return
        sd = fl.sides()
        if not self._plain_sides(top="wall") or sd["top"]["velocity"] <= 0.0:
            return
        sd_ok = all(sd[k]["velocity"] == 0.0 for k in ("left", "right", "bottom"))
        U, Lc = sd["top"]["velocity"], self.size[0]
        if not sd_ok or not math.isclose(U * Lc / self.nu, 100.0, rel_tol=1e-9):
            return
        ux, uy = fl.velocity()
        n = fl.nx
        i = n // 2
        yy = fl.y / Lc
        if n % 2 == 0:  # the centre line half-way between two columns
            ucol, vrow = 0.5 * (ux[i - 1] + ux[i]), 0.5 * (uy[:, i - 1] + uy[:, i])
        else:
            ucol, vrow = ux[i], uy[:, i]
        ye = np.concatenate([[0.0], yy, [1.0]])
        u = np.interp(L.GHIA_Y, ye, np.concatenate([[0.0], ucol / U, [1.0]]))
        v = np.interp(L.GHIA_X, ye, np.concatenate([[0.0], vrow / U, [0.0]]))
        du = float(np.max(np.abs(u - np.array(L.GHIA_U100))[1:-1]))
        dv = float(np.max(np.abs(v - np.array(L.GHIA_V100))[1:-1]))
        known = (f"сетка {n}²; тест движка на 64²–256²: 0,005 (u) и 0,008 (v) — не убывает с сеткой (разница с "
                 f"решением Ghia 129²); нужно установившееся течение (≈ 25 L/U = {_num(25 * Lc / U, 3)} с); таблицы — по "
                 f"двум совпадающим перепечаткам")
        self.running_check("ghia_u", "Ghia 1982, Re = 100: max |u − u_Ghia| / U на вертикальной оси", du, None, 0.0,
                           info=True, group="Эталоны", note=f"15 точек таблицы I; {known}")
        self.running_check("ghia_v", "Ghia 1982, Re = 100: max |v − v_Ghia| / U на горизонтальной оси", dv, None, 0.0,
                           info=True, group="Эталоны", note=f"15 точек таблицы II; {known}")

    def _poiseuille_checks(self):
        """A channel with a parabolic inlet on the left and an outlet on the right between plain walls, no body force:
        at each probe at least 2 H from the inlet and 2 H upstream of every obstacle, the velocity profile of its
        column against the inflow's parabola 4 Um y (H - y) / H^2."""
        fl = self.fl
        if not self._plain_sides(left="inlet", right="outlet") or self._objs("gravity"):
            return
        inl = fl.sides()["left"]
        if inl.get("profile") != "parabolic" or inl.get("tangential") or fl.inlet_scales().get("left", 1.0) < 1.0:
            return
        H, Um = self.size[1], inl["velocity"]
        starts = [float(np.min(self._outline(o)[:, 0])) for o in self.objects.values()
                  if o["type"] in ("disk", "rect", "airfoil")]
        ux, uy = fl.velocity()
        for oid, kind in self.ref.items():
            if kind[0] != "probe":
                continue
            x = self.objects[oid]["values"]["x"]
            if x < 2 * H or any(s < x + 2 * H for s in starts):
                continue
            i, _ = self._at(x, 0.0)
            exact = 4 * Um * fl.y * (H - fl.y) / H**2
            ok = np.isfinite(ux[i])
            d = float(np.max(np.abs(ux[i][ok] - exact[ok]))) / Um
            dvy = float(np.max(np.abs(uy[i][ok]))) / Um
            dr = fl.numbers()["density_range"]
            self.running_check(f"pois_{oid}", f"Пуазейль у «{self.objects[oid]['label']}»: max |u − u_P| / Um", d,
                               None, 0.0, info=True, group="Эталоны",
                               note=f"u_P = 4 Um y (H − y)/H², Um = {_num(Um, 4)} м/с, H = {_num(H, 4)} м, x = {_num(fl.x[i], 4)} м; "
                                    f"max |v| / Um = {_num(dvy, 3)}; эталон — развитое течение несжимаемой жидкости: "
                                    f"разность включает ошибку сжимаемости (поток ρu сохраняется, а плотность вдоль "
                                    f"канала падает с давлением: сейчас {_num(dr[0], 4)} … {_num(dr[1], 4)}) и след входа "
                                    f"(STATUS V41 m); тест движка: канал с силой и периодическими концами — парабола "
                                    f"до округления")

    def _force_poiseuille_check(self):
        """Poiseuille flow driven by a body force (review LB1-physics P7: a reference a wrong transfer to a new grid breaks,
        which the balances cannot see): periodic along x, fixed plain walls at the bottom and the top, a body force gx
        along x only, no bodies: the profile averaged along x against the steady u = gx y (H − y) / (2 ν)."""
        fl = self.fl
        sd = fl.sides()
        if sd["left"]["kind"] != "periodic" or any(v[0] == "obstacle" for v in self.ref.values()):
            return
        if not all(sd[k]["kind"] == "wall" and sd[k]["velocity"] == 0.0 for k in ("bottom", "top")):
            return
        gx, gy = fl.gravity
        if gx == 0.0 or gy != 0.0:
            return
        H = self.size[1]
        exact = gx * fl.y * (H - fl.y) / (2 * self.nu)
        peak = abs(gx) * H * H / (8 * self.nu)
        u = np.nanmean(fl.velocity()[0], axis=0)
        d = float(np.max(np.abs(u - exact))) / peak
        self.running_check("pois_force", "Пуазейль под объёмной силой: max |u − u_P| / u_max (среднее вдоль x)", d, None,
                           0.0, info=True, group="Эталоны",
                           note=f"u_P = g_x y (H − y)/(2ν), g_x = {_num(gx, 4)} м/с², H = {_num(H, 4)} м, u_max = "
                                f"{_num(peak, 4)} м/с; эталон — установившийся профиль: разность затухает как "
                                f"exp(−π²νt/H²), время H²/ν = {_num(H**2 / self.nu, 4)} с; тест движка: парабола до "
                                f"округления, в том числе после смены сетки, области и шага (неверный перенос на новую "
                                f"сетку заметен здесь, а балансы его не видят)")

    def _couette_check(self):
        """Plane Couette flow: periodic along x, one wall (bottom or top) moving along +x at U and the other fixed, no
        bodies and no body force: the profile averaged along x against the steady u = U y / H (or U (H - y) / H)."""
        fl = self.fl
        sd = fl.sides()
        if sd["left"]["kind"] != "periodic" or self._objs("gravity") or any(v[0] == "obstacle"
                                                                              for v in self.ref.values()):
            return
        if sd["bottom"]["kind"] != "wall" or sd["top"]["kind"] != "wall":
            return
        ub, ut = sd["bottom"]["velocity"], sd["top"]["velocity"]
        if (ub == 0.0) == (ut == 0.0):
            return
        U, H = (ut or ub), self.size[1]
        exact = U * (fl.y / H if ut else (H - fl.y) / H)
        u = np.nanmean(fl.velocity()[0], axis=0)
        d = float(np.max(np.abs(u - exact))) / abs(U)
        t_visc = H**2 / self.nu
        self.running_check("couette", "Куэтт: max |u − U·y/H| / U (среднее вдоль x)", d, None, 0.0, info=True,
                           group="Эталоны",
                           note=f"U = {_num(U, 4)} м/с, H = {_num(H, 4)} м; эталон — установившийся линейный профиль: разность "
                                f"затухает как exp(−π²νt/H²), время H²/ν = {_num(t_visc, 4)} с; тест движка: линейный "
                                f"профиль до округления (1e-11), разгон — по ряду с вторым порядком по сетке")

    # --- header and drawing ------------------------------------------------------------------------------------------
    def _shapes(self):
        items = []
        for oid, kind in self.ref.items():
            o = self.objects.get(oid)
            if o is None:
                continue
            base = {"id": oid, "label": o["label"], "type": o["type"]}
            if kind[0] == "obstacle":
                P = self._outline(o)
                items.append({**base, "shape": "polygon", "pts": [[float(a), float(b)] for a, b in P],
                              "color": COLORS["obstacle"]})
            elif kind[0] == "side":
                items.append({**base, "shape": "sides", "sides": list(kind[1]), "color": COLORS[o["type"]]})
            elif kind[0] in ("dye", "drop"):
                v = o["values"]
                items.append({**base, "shape": "circle", "c": [v["x"], v["y"]], "r": v["radius"],
                              "color": COLORS["dye"]})
            elif kind[0] == "probe":
                v = o["values"]
                items.append({**base, "shape": "point", "c": [v["x"], v["y"]], "color": COLORS["probe"]})
        self.emit({"type": "shapes", "t": self.t, "items": items, "size": list(self.size)})

    def rekey(self):
        self.emit_picture()

    def header(self):
        Lx, Ly = self.size
        h = 0.04 * max(Lx, Ly)
        fl = self.fl
        nb = fl.numbers()
        return {
            "title": "Плейграунд: жидкости",
            "text": ("Течение несжимаемой жидкости в плоскости: решёточный метод Больцмана решает уравнения "
                     "Навье–Стокса. Добавляйте препятствия, входы и выходы, подвижные стенки, краситель и датчики — "
                     "в текущий момент; силы на телах и балансы считаются вживую."),
            "actions": [],
            "approximations": self._approx(),
            "scene3d": {"box": [[0.0, 0.0, -h], [Lx, Ly, h]], "units": "м", "up": [0, 0, 1],
                        "objects": [{"id": "field", "label": "Поле течения (картина)", "kind": "panel",
                                     "origin": [0.0, 0.0, 0.0], "u": [Lx, 0.0, 0.0], "v": [0.0, Ly, 0.0],
                                     "visible": True}],
                        "layers": [{"id": "flow", "label": "Скорость (стрелки)", "kind": "vectors", "visible": False}],
                        "coord_names": ["x", "y", "z"],
                        "planes": {"max": 0, "center": [0.5 * Lx, 0.5 * Ly, 0.0], "defaults": {"1": [0, 0, 1]}}},
            "grid": {"nx": fl.nx, "ny": fl.ny, "dx": fl.units.dx, "dt": fl.units.dt, "size": [Lx, Ly]},
            "fluid": {"rho": self.rho, "nu": self.nu, "dye_D": self.D},
            "fields": FIELDS, "shown": self.shown,
            "numbers": nb,
            "playground": self.playground_header(),
            "modifications": SCHEMA.modifications(self.params),
        }, {}

    def _approx(self):
        out = ["несжимаемая жидкость в плоскости (2-D, на метр глубины): решёточный метод Больцмана D2Q9; "
               "ошибка сжимаемости ~ Ma² (число Маха решётки ≈ 0,1)",
               "звуковые волны схемы (скорость звука c_s = u_max/0,1 — свойство счёта): стоячая волна O(Ma²) в силах "
               "и давлении, больше после резких изменений; средние за период звука её не несут",
               "стенки — отражение «на полпути» (кривые стенки ступеньками: первый порядок по форме) или с интерполяцией "
               "Бузиди (у тел с этим выбором)",
               "краситель — пассивная примесь (не влияет на течение)"
               + ("; его диффузия равна вязкости (число Шмидта 1), если не задана" if self.D else ""),
               "турбулентность не моделируется отдельно: при больших Re сетка должна разрешать все вихри "
               "(иначе мир сам остановится с причиной); пределы числа Рейнольдса ячейки — пределы устойчивости, "
               "не точности"]
        if self.u_note:
            out.append(self.u_note)
        fl0 = self.params["fluid"]
        nu0, rho0 = ((float(self.params["nu"]), float(self.params["rho"])) if fl0 == "custom" else
                     (1e-3, 1.0) if fl0 == "dfg" else
                     (float(L.FLUIDS["water_20C" if fl0 == "water" else "air_20C"]["nu"]),
                      float(L.FLUIDS["water_20C" if fl0 == "water" else "air_20C"]["rho"])))
        if not (math.isclose(self.nu, nu0, rel_tol=1e-12) and math.isclose(self.rho, rho0, rel_tol=1e-12)):
            out.append(f"жидкость изменена на ходу: ν = {_sci(self.nu)} м²/с, ρ = {_sci(self.rho)} кг/м³ (в начале — "
                       f"{FLUIDS_RU[fl0]})")
        per = L._interp_rate(self.fl.device if self.fl.device in ("cpu", "gpu") else "cpu", self.fl.N)
        if per > 0.25:
            out.append(f"большая сетка ({self.fl.nx} × {self.fl.ny}): шаг считается ≈ {_num(per, 2)} с — мир идёт медленно; "
                       f"меньше узлов — быстрее")
        bodies = [o for o in self.objects.values() if o["type"] in ("disk", "rect", "airfoil")]
        if any(o["values"].get("vx") or o["values"].get("vy") or o["values"].get("omega") for o in bodies):
            out.append("тела с движущейся поверхностью стоят на месте: задана скорость поверхности при неподвижной "
                       "форме (её нормальная часть — источник и сток), а не движение тела")
        sd = self.fl.sides()
        if bodies and any(sd[k]["kind"] == "periodic" for k in L.SIDES):
            out.append("периодичность: тела повторяются с шагом области (решётка тел), а не одиночное тело в "
                       "неограниченном потоке")
        return out

    def engine_modules(self):
        return ["lfphys.core.fluids.lbm"]


VIZ = {
    "id": "p04_fluids",
    "title": "Жидкости",
    "summary": ("Песочница течений: препятствия, крылья, входы и выходы, подвижные стенки, краситель; несжимаемая "
                "жидкость решёточным методом Больцмана."),
    "purpose": ("Собрать течение и посмотреть, что из него выйдет: обтекание, отрыв, дорожка Кармана, вихрь в "
                "каверне, подъёмная сила крыла, перемешивание красителя; силы и балансы — вживую."),
    "version": "0.2",
    "schema": SCHEMA,
    "simulation": Simulation,
    "kind": "playground",
    "section": "fluids",
}
