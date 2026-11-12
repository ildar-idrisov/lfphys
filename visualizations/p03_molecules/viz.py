# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""p03: the particles-and-molecules playground (plan P15.4; owner, 2026-10-28: «например частицы и молекулы
взаимодействующие»). A wrapper over the engine's molecular dynamics (``lfphys.core.md``: Newton's equations by velocity
Verlet, thermostats, walls and a piston, statistical-mechanics observables; event-driven hard spheres in
``core.md.hard``) with the interatomic potentials of ``lfphys.theories.models.interatomic`` (Lennard-Jones, WCA, bonds
and angles: models, injected); the framework is ``lfviz.playground``.

The laws of the world. World parameters (a change starts a new world, which can take the scene over): the space (a plane
or the volume) and the boundaries at the start. Live laws (review 2026-11-04 UX-ui U12; LB1, plan P16.1, a bench that
never restarts: changed at the current moment, the world kept): the dynamics (continuous forces ↔ hard spheres by
events: the same atoms handed to the other solver, ``core.md.hard.hard_from_md`` / ``md_from_hard``), the pair model
(Lennard-Jones or the purely repulsive WCA, through ``MD.set_pair``), its cutoff and shift, the time step
(``MD.set_dt``) and the box (``MD.deform``: an affine deformation with its work in the first law, or a wall moved over
empty space). Objects have handles (LB1, P16.2: a drag moves a group as a whole, a throw gives it a centre-of-mass
velocity), every positioned object is in the frames' ``at`` and the world's measurables in their ``meas`` (P16.3).
Inside it the
experimenter places, at any moment, a gas or a crystal block of atoms, single atoms, molecules (bonded atoms with
angles), walls (specular, soft, or thermal: a heat bath; on a periodic axis a wall makes the axis walled), a piston,
thermostats (CSVR or Langevin, everywhere or in a region), a field and thermometers; a new object lands where it can
exist (``place``: the nearest free spot, a crystal around the atoms already there) or is refused in Russian with what to
change (reviews UX-ui U4–U8, U13; UX-params P31–P33); the engine computes the motion and measures
the temperature, the pressure, the energy balance (heat and work), the velocity distribution against Maxwell–Boltzmann,
the radial distribution function, the density along the field, the bond-orientational order and the mean-square
displacement, and for molecules the temperature of each kind of motion.

Every change of the scene is all or nothing (review B7-md M6): the engine's state and the wrapper's maps are saved
before it and put back bit for bit when the engine refuses any part of it.

Units: the engine's reduced units with argon's 12-6 parameters (σ = 3.405 Å, ε/k = 119.8 K, m = 39.948 u;
``argon_units``); the playground speaks nm, ps, K, bar (in 3-D; in a plane the pressure is a force per length, mN/m).
"""

from __future__ import annotations

import copy
import math

import numpy as np

from lfphys.core.md import observables as OB
from lfphys.core.md.system import MD, free_sites
from lfphys.theories.models import interatomic as IA
from lfviz.params import Param, Schema
from lfviz.playground import ObjectType, PlaygroundSimulation, scene_param, scene_time

try:  # the framework's refusal (reviews UX-params P4, UX-ui U13): shown as it is, in Russian, with what to change
    from lfviz.errors import Refusal
except ImportError:  # an older framework: a Russian ValueError is shown as it is
    Refusal = ValueError
try:
    from lfviz.limits import require as _require
except ImportError:
    _require = None


def refusal(text, hint=None, detail=None):
    """A refusal for the owner: what is wrong and what to change (Russian)."""
    for kw in ({"hint": hint, "detail": detail}, {"change": hint, "detail": detail}):
        try:
            return Refusal(text, **kw)
        except TypeError:
            continue
    return Refusal(text.rstrip(".") + (f": {hint}" if hint else ""))

U = IA.argon_units()
NM = U.to_angstrom(1.0) / 10.0          # nm per reduced length
PS = U.to_ps(1.0)                       # ps per reduced time
KELVIN = U.to_kelvin(1.0)               # K per reduced temperature
STATS_EVERY = 10                        # frames between two statistics messages (by count)
ORDER_EVERY_PS = 1.0                    # world time between two values of the order parameter in ``meas`` (ps)
MAX_STEPS = 400                         # integrator steps per advance call
ORDER_RCUT = 1.5                        # neighbours for the bond-orientational order: nearer than 1.5 sigma
Z_BLOCK = 1.0                           # the hard world's pressure blocks: at least one time unit (2.16 ps) each
Z_EQUIL = 5.0                           # ... counted from five time units after the last change of the scene
Z_MIN_BLOCKS = 10
HBAR_OVER_K = 1.054571817e-34 / 1.380649e-23   # s K (CODATA 2018 exact k, ħ)
COLORS = ["#74c0fc", "#ff922b", "#8ce99a", "#f783ac", "#ffd43b", "#b197fc", "#e9ecef", "#ff6b6b"]
# the time step must resolve the repulsive core (review UX-params P32): the rms step v dt over the distance r_t / 12 in
# which the 12-6 repulsion rises by kT near its turning point r_t = sigma (4 eps / kT)^(1/12), q = 12 v dt / r_t, at
# most Q_MAX. Measured (2-D and 3-D LJ gas, 200 atoms, dt = 10 fs, 3 seeds, 3000 steps; the response's checks): q <= 0.36
# keeps the energy error below 0.6 % of kT per atom; at q = 0.44-0.46 it is 0.02-5 %; at q = 0.58 two of three 2-D runs
# crashed («two interacting particles at the same point»), as did every run at 10^5 K (q = 1.8). Argon at 300 K: q =
# 0.12 (2-D); an atom of 4 u at 300 K: 0.38
Q_MAX = 0.4
FRAME_S = 0.04          # the modelled computing time of one advance call (the runner interleaves commands and frames)
# random sequential insertion jams near these covered fractions (equal disks / spheres); refused at once above
JAM = {2: 0.50, 3: 0.35}
MOL_JAM = {2: 0.40, 3: 0.28}
PAIR_BYTES = 120        # bytes per pair of the neighbour list while it is built (indices, separations, terms)

# the critical temperature of the pair model, eps/k (sources: lfphys/sources/verification_2026-11-04_p8_md.md §8):
# 3-D: the full 12-6 1.3120 (NIST SRS, Potoff & Panagiotopoulos 1998), linear force shift at 2.5 sigma 0.937 (NIST
# SRS, Errington, Debenedetti & Torquato 2003); 2-D: full 0.515, truncated and energy-shifted at 2.5 sigma 0.459 (Smit
# & Frenkel 1991)
TC = {(3, "full"): 1.3120, (3, 2.5, "force"): 0.937, (2, "full"): 0.515, (2, 2.5, "energy"): 0.459}


def _p(*a, **k):
    return Param(*a, **k)


BOX_HELP = ("Меняется в текущий момент (см. «Как менять размер ящика» и «Время изменения размера»). Аффинно: координаты "
            "атомов вдоль оси умножаются на L′/L, их скорости относительно центра масс — на L/L′ (для движения "
            "относительно центра масс — каноническое преобразование, шаг объёма баростата Андерсена). Работа над "
            "системой — изменение энергии, учтена в первом начале. За заданное время (по шагу на каждом шаге счёта) "
            "сжатие тем ближе к квазистатическому, чем медленнее: работа стремится к −∫P dV по адиабате, сжатие и "
            "возврат почти не нагревают; скачком (время 0) — необратимо: вещество после скачка неравновесно и греется "
            "(газ аргона, 300 атомов при 300 K, 12 → 11 → 12 нм: скачками ≈ 16 K, за 10 пс ≈ 0,7 K, за 50 пс ≈ 0,6 K, "
            "за 200 пс — 0 ± 0,2 K; см. README). Отказ — с "
            "причиной: атомы перекрылись бы (скачок), связь молекулы изменила бы длину больше чем на 10 % (скачок), "
            "радиус обрезки больше половины ящика, ось поршня (двигайте поршень), удары не разрешает шаг по времени "
            "(сжатие нагревает)")
BOX_TIME_HELP = ("Время, за которое ящик доходит до нового размера (аффинно): размер меняется равномерно, на каждом шаге "
                 "счёта — малым аффинным шагом, работа каждого шага учтена. Чем дольше (медленнее грани ящика по "
                 "сравнению со скоростью звука, у газа аргона при 300 K ≈ 320 м/с), тем ближе к квазистатической "
                 "адиабате: газ аргона (300 атомов, 300 K), сжатый 12 → 11 нм и возвращённый, нагревается скачками на "
                 "≈ 16 K, за 10 пс на ≈ 0,7 K, за 50 пс на ≈ 0,6 K, за 200 пс — 0 ± 0,2 K (измерено, 4 запуска). 0 — "
                 "скачком (необратимо). Пока размер меняется, текущий размер — в кадре; конец изменения — событием с "
                 "работой")


class _Schema(Schema):
    """p03's schema: laws written before the split of 2026-11-05 (review UX-ui U12) still resolve. Then «model» held
    lj | wca | hard as one world parameter; now «dynamics» (forces | hard) is the world's and «model» (lj | wca) a live
    law. An old ``"model": "hard"`` (from a scene file's laws or a stored run) becomes ``dynamics = hard``; old lj / wca
    are valid as they are (the default dynamics is the forces). The world says so in a notice (``legacy_note``)."""

    def resolve(self, preset, values):
        return super().resolve(preset, legacy_laws(values))


def legacy_laws(values):
    """The laws of the old combined «model» in the new split (a copy; other values untouched)."""
    if isinstance(values, dict) and values.get("model") == "hard":
        values = {**values, "dynamics": "hard", "model": "lj"}   # the live model is unused by hard spheres
    return values


def legacy_note(scene):
    """The notice for a scene file of the old format (its laws carry «model» and no «dynamics»), or None."""
    laws = scene.get("laws") if isinstance(scene, dict) else None
    if not isinstance(laws, dict) or "dynamics" in laws or "model" not in laws:
        return None
    old = laws["model"]
    if old == "hard":
        what = "«Взаимодействие» = твёрдые диски / шары стало «Динамика» = твёрдые диски / шары"
    else:
        lab = {"lj": "Леннард-Джонс", "wca": "только отталкивание (WCA)"}.get(old, str(old))
        what = (f"«Взаимодействие» = {lab} стало «Динамика» = непрерывные силы и «Взаимодействие» = {lab} — теперь "
                f"закон, который меняется на ходу")
    return f"файл старого формата (до 2026-11-05): {what}; сцена загружена с теми же законами"


SCHEMA = _Schema([
    _p("dim", "Пространство", "select", "2d", group="Законы",
       options=[("2d", "плоскость"), ("3d", "объём")],
       help="Плоскость или объём — другой мир (новый мир); сцену можно перенести: объекты создаются заново по своим "
            "параметрам, координата z отбрасывается или берётся по умолчанию; стенка и поршень поперёк z в плоскость не "
            "переносятся"),
    _p("dynamics", "Динамика", "select", "forces", group="Законы (на ходу)", live=True,
       options=[("forces", "непрерывные силы (Леннард-Джонс или WCA)"),
                ("hard", "твёрдые диски / шары (событийная динамика)")],
       help="Переключается в текущий момент: те же атомы с теми же положениями и скоростями. К твёрдым шарам — только "
            "если ни одна пара атомов не ближе σ и ни один атом не ближе σ/2 к стенке, а в сцене нет молекул, поршня, "
            "термостатов, поля, мягких стенок и зарядов (у твёрдых шаров их нет). Обратно — всегда: появляется "
            "потенциальная энергия пар (скачок энергии сказан в событии); шаг по времени должен разрешать удары"),
    _p("model", "Взаимодействие", "select", "lj", group="Законы (на ходу)", live=True,
       show_if={"dynamics": ["forces"]},
       options=[("lj", "Леннард-Джонс (притяжение и отталкивание; модель)"),
                ("wca", "только отталкивание (WCA; модель)")],
       help="Меняется в текущий момент: те же атомы с новым законом взаимодействия; энергия меняется на разность "
            "потенциалов (учтено в балансе энергии), отсчёты проверок начинаются заново"),
    _p("cutoff", "Радиус обрезки, σ", "float", 2.5, group="Законы (на ходу)", min=1.2, max=6.0, live=True,
       show_if={"dynamics": ["forces"], "model": ["lj"]},
       help="Потенциал Леннард-Джонса обрезан на этом расстоянии; сдвиг убирает скачок. Обрезка меняет вещество: "
            "его критическая точка и тройная точка другие, чем у полного потенциала (см. приближения). Меняется на "
            "ходу (не больше половины периодического ящика)"),
    _p("shift", "Сдвиг на обрезке", "select", "force", group="Законы (на ходу)", live=True,
       show_if={"dynamics": ["forces"], "model": ["lj"]},
       options=[("force", "сила и энергия непрерывны (чистая ошибка схемы O(dt²))"),
                ("energy", "только энергия непрерывна (скачок силы: ошибка энергии O(dt))")]),
    _p("dt_fs", "Шаг по времени, фс", "float", 10.0, group="Законы (на ходу)", min=0.1, max=50.0, live=True,
       show_if={"dynamics": ["forces"]},
       help="Схема Верле: ошибка энергии ~ dt² при непрерывных силах; для аргона 10 фс ≈ 0,005 τ. Меняется на ходу "
            "(состояние то же, следующие шаги — с новым шагом); атом за шаг должен проходить не больше 0,1 σ"),
    _p("Lx", "Размер ящика по x, нм", "float", 12.0, group="Ящик (на ходу)", min=0.5, max=1e3, log=True, live=True,
       help=BOX_HELP),
    _p("Ly", "Размер ящика по y, нм", "float", 12.0, group="Ящик (на ходу)", min=0.5, max=1e3, log=True, live=True,
       help=BOX_HELP),
    _p("Lz", "Размер ящика по z, нм", "float", 6.0, group="Ящик (на ходу)", min=0.5, max=1e3, log=True, live=True,
       show_if={"dim": ["3d"]}, help=BOX_HELP),
    _p("box_mode", "Как менять размер ящика", "select", "affine", group="Ящик (на ходу)", live=True,
       options=[("affine", "сжать или растянуть вместе с веществом (аффинно; работа над системой)"),
                ("wall", "сдвинуть верхнюю стенку: добавить или убрать пустое место")],
       help="«Аффинно»: всё вещество сжимается или растягивается вместе с ящиком (так делает баростат) за «Время "
            "изменения размера»: медленное сжатие приближается к адиабатическому, скачок необратим; работа над "
            "системой учтена в первом начале. «Стенка» (только ось со стенками; у оси поршня — его верхний упор): "
            "стенка сдвигается по пустому месту сразу — расширение в пустоту (опыт Джоуля, необратимо), работы нет у "
            "зеркальных и тепловых стенок, у мягкой стенки работа — изменение её энергии под атомами (сказано в "
            "событии); убрать место можно только там, где нет атомов. У твёрдых шаров — только «стенка»"),
    _p("box_time_ps", "Время изменения размера, пс (0 — скачком)", "float", 50.0, group="Ящик (на ходу)", min=0.0,
       max=1e4, live=True, show_if={"box_mode": ["affine"]}, help=BOX_TIME_HELP),
    _p("boundary", "Границы в начале", "select", "periodic", group="Ящик",
       options=[("periodic", "периодические (бесконечное вещество)"), ("walls", "стенки со всех сторон"),
                ("slab", "стенки снизу и сверху (по y), по бокам периодично")],
       help="«Стенка» или «Поршень» из палитры на периодической оси делают её осью со стенками (на ходу)"),
    scene_param(),
], presets={})

LIVE = ("dynamics", "model", "cutoff", "shift", "dt_fs", "Lx", "Ly", "Lz", "box_mode", "box_time_ps")
BOX_KEYS = ("Lx", "Ly", "Lz")
MAX_BOND_STRAIN = 0.10   # an affine change of the box stretches the molecules' bonds with it: at most 10 % per change


def _scene(objs):
    return {"format": "lfscene", "version": 1, "objects": objs}


# the melting preset's box holds a whole triangular lattice of density 0.85 (25 x 15 rectangular cells of a x a√3,
# a = (2/(√3 · 0.85))^½ σ = 0.39685 nm): the crystal fills it without strain or a vacancy strip (review B7-md M17)
_A085 = math.sqrt(2.0 / (math.sqrt(3.0) * 0.85)) * NM
# the liquid-vapour preset's box: 5 fcc cells of the liquid's density 0.693 (NIST, LFS 2.5σ at 0.75 ε/k) across x and z
_AFCC = (4.0 / 0.693) ** (1.0 / 3.0) * NM

SCHEMA.presets.update({
    "maxwell": {"label": "Газ аргона из одинаковых скоростей: распределение Максвелла устанавливается само",
                "params": {"dim": "2d", "model": "lj", "Lx": 12.0, "Ly": 12.0, "boundary": "periodic",
                           "scene": _scene([{"type": "gas", "label": "Аргон", "values": {
                               "n": 300, "T": 300.0, "start": "same_speed"}}])}},
    "melting": {"label": "Плоский кристалл (ρσ² = 0,85) нагревают термостатом до 120 K: порядок ψ6 исчезает, атомы "
                         "начинают диффундировать — плавление",
                "params": {"dim": "2d", "model": "lj", "Lx": round(25 * _A085, 4),
                           "Ly": round(15 * math.sqrt(3.0) * _A085, 4), "boundary": "periodic",
                           "scene": _scene([
                               {"type": "crystal", "label": "Кристалл", "values": {"density": 0.85, "T": 20.0}},
                               {"type": "thermostat", "label": "Нагрев 120 K", "values": {"T": 120.0, "tau": 2.0}}])}},
    "piston": {"label": "Газ под поршнем: сжатие поршнем и теплообмен со стенкой (первое начало)",
               "params": {"dim": "2d", "model": "lj", "Lx": 12.0, "Ly": 16.0, "boundary": "walls",
                          "scene": _scene([
                              {"type": "gas", "label": "Аргон", "values": {"n": 200, "T": 300.0, "sy": 8.0,
                                                                           "y": 4.5}},
                              {"type": "piston", "label": "Поршень", "values": {"position": 10.0, "mass": 4000.0,
                                                                               "p_ext": 50.0}},
                              {"type": "wall", "label": "Тёплое дно", "values": {"axis": "y", "side": "lo",
                                                                                 "kind": "thermal", "T": 300.0}}])}},
    "liquid_vapour": {"label": "Жидкость и пар в объёме при 90 K в поле: жидкость (ρσ³ ≈ 0,69) внизу, над ней пар "
                               "(≈ 0,03) — профиль плотности по высоте",
                      "params": {"dim": "3d", "model": "lj", "Lx": round(5 * _AFCC, 4), "Ly": 6.0,
                                 "Lz": round(5 * _AFCC, 4), "boundary": "slab",
                                 "scene": _scene([
                                     {"type": "crystal", "label": "Жидкость (из решётки)",
                                      "values": {"density": 0.693, "T": 90.0, "y": 1.3, "sy": 2.6}},
                                     {"type": "thermostat", "label": "Термостат 90 K", "values": {"T": 90.0,
                                                                                                  "tau": 5.0}},
                                     {"type": "gravity", "label": "Поле", "values": {"g": 0.02}}])}},
    "molecules": {"label": "Двухатомные молекулы стартуют только с поступательным движением: столкновения "
                           "раздают энергию вращению и колебаниям (равнораспределение устанавливается)",
                  "params": {"dim": "3d", "model": "lj", "Lx": 5.0, "Ly": 5.0, "Lz": 5.0, "boundary": "periodic",
                             "scene": _scene([{"type": "molecule", "label": "Молекулы X₂", "values": {
                                 "shape": "dimer", "count": 150, "T": 400.0, "bond": 1.1, "k_bond": 50.0,
                                 "start": "translation"}}])}},
    "hard_disks": {"label": "Твёрдые диски: давление против уравнения состояния (Колафа и Роттнер)",
                   "params": {"dim": "2d", "dynamics": "hard", "Lx": 12.0, "Ly": 12.0, "boundary": "periodic",
                              "scene": _scene([{"type": "gas", "label": "Диски", "values": {
                                  "n": 400, "T": 300.0}}])}},
})


def _xyz(ndim, label="Центр", d=(6.0, 6.0, 3.0)):
    return [_p(c, f"{label}: {c}, нм", "float", float(d[i]), min=-1e3, max=1e3) for i, c in enumerate("xyz"[:ndim])]


def _region(ndim):
    return [*[_p(c, f"Центр области: {c}, нм (0 и размер 0 — весь ящик)", "float", 0.0, min=-1e3, max=1e3)
              for c in "xyz"[:ndim]],
            *[_p(f"s{c}", f"Размер области по {c}, нм (0 — весь ящик)", "float", 0.0, min=0.0, max=1e3)
              for c in "xyz"[:ndim]]]


def _subst(model):
    out = [_p("substance", "Вещество", "select", "argon",
              options=[("argon", "аргон (σ = 3,405 Å, ε/k = 119,8 K, m = 39,948 а.е.м.)"), ("custom", "своё")],
              help="Смена вещества — те же атомы с новыми параметрами в текущий момент; температура сохраняется "
                   "(скорости пересчитаны v·√(m/m′)); перекрытия при новом σ отклоняются"),
           _p("sigma", "Размер σ, доля аргонового", "float", 1.0, min=0.3, max=3.0, show_if={"substance": ["custom"]}),
           _p("mass", "Масса, а.е.м.", "float", 39.948, min=1.0, max=1e4, log=True,
              show_if={"substance": ["custom"]})]
    if model != "hard":
        out[2:2] = [_p("epsilon", "Глубина ямы ε, доля аргоновой", "float", 1.0, min=0.0, max=20.0,
                       show_if={"substance": ["custom"]})]
        out.append(_p("charge", "Заряд, e (только в ящике со стенками)", "float", 0.0, min=-5.0, max=5.0,
                      show_if={"substance": ["custom"]}))
    out.append(_p("color", "Цвет", "select", "0", options=[(str(i), c) for i, c in enumerate(
        ["голубой", "оранжевый", "зелёный", "розовый", "жёлтый", "фиолетовый", "белый", "красный"])]))
    return out


SP_KEYS = {"substance", "sigma", "epsilon", "mass", "charge", "color"}
POS_KEYS = ("x", "y", "z")
CARRIED = {"gas": "атомы газа", "crystal": "атомы кристалла", "atom": "атом", "molecule": "молекулы", "piston": "поршень"}
VEL_KEYS = ("vx", "vy", "vz")
AXIS_KEYS = {"z", "sz", "vz", "throw_vz"}   # the keys of the axis a plane has not (a 3-D scene carried into a plane)


def _vcom(ndim):
    return [_p(f"v{c}", f"Скорость центра масс v{c}, м/с", "float", 0.0, min=-1e5, max=1e5,
               help="Объект движется как целое с этой скоростью (бросок мышью задаёт её); тепловое движение атомов — "
                    "по температуре") for c in "xyz"[:ndim]]


# a throw (LB1, P16.2) comes in the world's units - nm per second of world time (the frames' ``at`` and ``t``); the
# objects' velocities are in m/s: the throw's own hidden parameters carry it, ``_set_obj`` turns it into vx, vy, vz
# (review LB1-p02-ux X4: a throw of 1.9·10¹² nm/s was taken for 1.9·10¹² m/s and refused)
THROW_KEYS = ("throw_vx", "throw_vy", "throw_vz")
NM_PER_S = 1e9            # nm/s per m/s
THROW_MAX_M_S = 500.0     # the largest throw (m/s): see palette()


def _throw(ndim):
    return [_p(f"throw_v{c}", f"Бросок: скорость центра масс v{c}, нм/с", "float", 0.0, min=-1e15, max=1e15,
               hidden=True, help="задаётся броском мышью (в единицах мира: нм за секунду его времени); объект получает "
                                 "эту скорость центра масс (в инспекторе — в м/с)") for c in "xyz"[:ndim]]


def _ot(typ, label, kind, schema, handles=None, **kw):
    """A palette type with its handles for direct manipulation (LB1, P16.2: the params a drag or a throw changes) and
    whether it has a dynamic state (``stateful``: the carry-over says whether it went along); a framework without them
    takes the type without them."""
    tries = [dict(kw, handles=handles)] if handles else []
    if handles and "velocity_display" in handles:   # a framework without the display unit: the rest of the handles
        tries.append(dict(kw, handles={k: v for k, v in handles.items() if k != "velocity_display"}))
    tries += [dict(kw)] + ([{k: v for k, v in kw.items() if k != "stateful"}] if "stateful" in kw else [])
    for i, k in enumerate(tries):
        try:
            return ObjectType(typ, label, kind, schema, **k)
        except (TypeError, ValueError):
            if i == len(tries) - 1:
                raise


def palette(ndim: int, model: str = "lj") -> dict:
    """The palette: one for both dynamics (LB1: the dynamics is a live law; what the hard spheres have not is disabled
    by ``palette_state`` with the reason). ``model`` is kept for the callers of before."""
    T = _p("T", "Температура, K", "float", 300.0, min=0.0, max=1e5)
    SUBST = _subst("lj")
    gas = Schema([_p("n", "Число атомов", "int", 200, min=1, max=20000), T,
                  _p("start", "Начальные скорости", "select", "maxwell",
                     options=[("maxwell", "по Максвеллу при T"), ("same_speed", "все с одной скоростью (как при T)")]),
                  *_region(ndim), *_vcom(ndim), *_throw(ndim), *SUBST])
    crystal = Schema([_p("density", "Плотность решётки ρσ^d", "float", 0.9, min=0.05, max=1.3,
                         help="Решётка (2-D треугольная, 3-D ГЦК) с шагом этой плотности: целые ячейки в области; "
                              "вдоль периодической оси, которую блок занимает целиком, ячейки подогнаны к ящику "
                              "(фактическая плотность — в инспекторе). Плотная упаковка: ρσ² ≈ 0,9, ρσ³ ≈ 1,0"),
                      T, *_region(ndim), *_vcom(ndim), *_throw(ndim), *SUBST])
    atom = Schema([*_xyz(ndim), *[_p(f"v{c}", f"Скорость v{c}, м/с", "float", 0.0, min=-1e5, max=1e5)
                                  for c in "xyz"[:ndim]], *_throw(ndim), *SUBST])
    mol = Schema([_p("shape", "Молекула", "select", "dimer",
                     options=[("dimer", "двухатомная"), ("bent", "трёхатомная угловая"), ("chain", "цепочка")]),
                  _p("atoms", "Атомов в цепочке", "int", 6, min=3, max=50, show_if={"shape": ["chain"]}),
                  _p("count", "Сколько молекул", "int", 20, min=1, max=2000), T,
                  _p("start", "Начальное движение", "select", "maxwell",
                     options=[("maxwell", "всё при T (поступательное, вращение, колебания)"),
                              ("translation", "только поступательное при T (вращение и колебания холодные)")],
                     help="«всё при T»: скорость каждого атома по Максвеллу при T, длины связей и углы — по "
                          "Больцману около равновесных (каноническое начало); «только поступательное»: молекула "
                          "движется как целое со скоростью при T своей массы, связи и углы равновесные"),
                  _p("bond", "Длина связи, σ", "float", 1.0, min=0.5, max=2.0),
                  _p("k_bond", "Жёсткость связи, ε/σ²", "float", 400.0, min=1.0, max=1e4, log=True),
                  _p("angle", "Угол связей, °", "float", 105.0, min=30.0, max=180.0,
                     show_if={"shape": ["bent", "chain"]}),
                  _p("k_angle", "Жёсткость угла, ε/рад²", "float", 50.0, min=0.0, max=1e4,
                     show_if={"shape": ["bent", "chain"]}),
                  *_region(ndim), *_vcom(ndim), *_throw(ndim), *SUBST])
    axes = [(c, c) for c in "xyz"[:ndim]]
    wall_kinds = [("specular", "зеркальная (упругое отражение)"),
                  ("thermal", "тепловая (возвращает атомы с температурой стенки: тепловая ванна)"),
                  ("soft", "мягкая (потенциал стенки Леннард-Джонса; не у твёрдых шаров)")]
    wall = Schema([_p("axis", "Стенка поперёк оси", "select", "y", options=axes),
                   _p("side", "Сторона", "select", "lo", options=[("lo", "нижняя / левая"), ("hi", "верхняя / правая")]),
                   _p("kind", "Стенка", "select", "thermal", options=wall_kinds),
                   _p("T", "Температура стенки, K", "float", 300.0, min=0.0, max=1e5, show_if={"kind": ["thermal"]})])
    piston = Schema([_p("axis", "Поршень поперёк оси", "select", "y", options=axes),
                     _p("position", "Положение, нм", "float", 10.0, min=0.0, max=1e3,
                        help="Задаётся при установке; правка других параметров поршень не двигает"),
                     _p("mass", "Масса поршня, а.е.м. (0 — движется как задано)", "float", 4000.0, min=0.0,
                        max=1e9),
                     _p("p_ext", "Внешнее давление, бар (в плоскости — мН/м)", "float", 50.0, min=0.0, max=1e6),
                     _p("speed", "Скорость (если масса 0), м/с", "float", 0.0, min=-1e4, max=1e4)])
    thermo = Schema([_p("kind", "Термостат", "select", "csvr",
                        options=[("csvr", "CSVR (Буси–Донадио–Парринелло): канонический, мягкий"),
                                 ("langevin", "Ланжевен (трение и шум)")]),
                     _p("T", "Температура, K", "float", 300.0, min=0.0, max=1e5),
                     _p("tau", "Время релаксации, пс", "float", 2.0, min=1e-3, max=1e6, show_if={"kind": ["csvr"]}),
                     _p("gamma", "Трение γ, 1/пс", "float", 1.0, min=1e-6, max=1e4, show_if={"kind": ["langevin"]}),
                     *_region(ndim)])
    field = Schema([_p("g", "Поле g (вниз по y), ε/(mσ)", "float", 0.02, min=-10.0, max=10.0,
                       help="Для аргона единица ε/(mσ) ≈ 7,3·10¹³ м/с² (земное g ≈ 1,3·10⁻¹³ в этих единицах): "
                            "земное поле на масштабе атомов незаметно, здесь — модельное сильное поле, чтобы увидеть "
                            "расслоение")])
    probe = Schema([*_xyz(ndim, "Центр"), _p("r", "Радиус, нм", "float", 2.0, min=0.1, max=1e3)])
    pos = list(POS_KEYS[:ndim])
    # the throw: in the world's units (nm/s), at most THROW_MAX_M_S (review LB1-p02-ux X4): about the speed of sound of
    # argon gas at room temperature and above its thermal speed; the default step (10 fs) resolves the collisions of a
    # 300 K argon group thrown at it (q = 12 v dt / r_t at 500 m/s plus the thermal speed: 0.34 in a plane, 0.37 in a
    # volume, the limit Q_MAX = 0.4; tests/test_p03_lab.py);
    # faster, or hotter, or lighter, is refused by the step with what to change
    group = {"position": pos, "velocity": list(THROW_KEYS[:ndim]), "velocity_max": THROW_MAX_M_S * NM_PER_S,
             # the throw read and logged in m/s (the framework's velocity_display: shown = factor × world units)
             "velocity_display": {"unit": "м/с", "factor": 1.0 / NM_PER_S}}
    pal = {
        "gas": _ot("gas", "Газ (атомы)", "particle", gas, handles=group, color=COLORS[0],
                   help="Атомы в случайных местах (не ближе σ друг к другу и к уже имеющимся: случайная "
                        "последовательная вставка), скорости при температуре T; общий импульс газа снят, затем "
                        "добавлена скорость центра масс. Перетаскивание сдвигает все его атомы, бросок (Shift) задаёт "
                        "скорость центра масс"),
        "crystal": _ot("crystal", "Кристалл (решётка атомов)", "particle", crystal, handles=group, color=COLORS[2]),
        "atom": _ot("atom", "Атом", "particle", atom, handles=group, color=COLORS[4]),
        "wall": _ot("wall", "Стенка (тип)", "field", wall, limit=6, color="#adb5bd",
                    help="Меняет одну из стенок ящика (у границ со стенками)"),
        "probe": _ot("probe", "Термометр (область)", "probe", probe, handles={"position": pos, "size": "r"}, limit=6,
                     color="#ffd43b",
                     help="Число атомов, их плотность и температура в шаре вокруг точки (периодические грани учтены)"),
        "molecule": _ot("molecule", "Молекулы", "particle", mol, handles=group, color=COLORS[1],
                        help="Атомы, связанные пружинами (и углами): модель молекулы; размещаются без перекрытий "
                             "(энергия каждого атома при вставке не выше 2kT); не у твёрдых шаров"),
        "piston": _ot("piston", "Поршень", "body", piston, handles={"position": {"param": "position", "axis_param": "axis"}},
                      limit=1, color="#868e96", stateful=True,
                      help="Верхняя стенка оси подвижна: масса и внешнее давление; работа считается; не у твёрдых "
                           "шаров"),
        "thermostat": _ot("thermostat", "Термостат", "field", thermo, limit=4, color="#ff6b6b",
                          help="Держит температуру (вся область или её часть); теплота считается; не у твёрдых шаров"),
        "gravity": _ot("gravity", "Поле (тяжесть)", "field", field, limit=1, color="#868e96",
                       help="Однородное поле вниз по y; не у твёрдых шаров"),
    }
    return pal


def _hex(c):
    h = c.lstrip("#")
    return [int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]


def debye_cv_fraction(T, theta):
    """C_v / (3 N k) of the Debye model at T (Θ_D = theta): 3 (T/Θ)^3 ∫_0^{Θ/T} x^4 e^x/(e^x - 1)^2 dx."""
    if T <= 0:
        return 0.0
    xm = theta / T
    x = np.linspace(1e-9, xm, 4001)
    f = x ** 4 * np.exp(-x) / (-np.expm1(-x)) ** 2
    return float(3.0 / xm ** 3 * np.trapezoid(f, x))


def einstein_cv_fraction(T, theta):
    """C / k of one quantum harmonic oscillator of ħω/k = theta at T (1 classically)."""
    if T <= 0:
        return 0.0
    x = theta / T
    return float(x * x * math.exp(-x) / (-math.expm1(-x)) ** 2)


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


_EN = [  # the engine's refusals (core.md, English) in the owner's terms (reviews UX-ui U13, UX-params P31)
    (r"random placement jammed: (\d+) of (\d+)", lambda m, s: (
        f"без перекрытий удалось разместить только {m.group(1)} из {m.group(2)} атомов",
        "меньше атомов или больше область; плотнее — «Кристалл»")),
    (r"overlap: an inserted particle's potential energy ([-\d.e+]+)", lambda m, s: (
        (f"энергия вставки нового атома {_num(float(m.group(1)), 3)} ε больше предела "
         f"{_num(getattr(s.md, 'max_insert_energy', 50))} ε: с зарядами её задаёт и кулоновское отталкивание дальних атомов"
         if any(d.get("charge", 0.0) for d in s.md.species()) else
         f"новые атомы легли бы на уже имеющиеся (энергия вставки {_num(float(m.group(1)), 3)} ε при пределе "
         f"{_num(getattr(s.md, 'max_insert_energy', 50))} ε)"),
        ("меньше заряд или меньше атомов" if any(d.get("charge", 0.0) for d in s.md.species()) else
         "сдвиньте объект в свободное место или уменьшите размер σ"))),
    (r"two interacting particles at the same point|two bonded atoms at the same point", lambda m, s: (
        "два атома оказались бы в одной точке", "сдвиньте объект")),
    (r"overlapping hard particles", lambda m, s: (
        "твёрдые диски (шары) перекрылись бы", "сдвиньте объект в свободное место или уменьшите σ")),
    (r"region: hi > lo", lambda m, s: (
        "область объекта лежит вне ящика (внутри стенок её не остаётся)",
        "центр и размеры области — внутри ящика (размер 0 — весь ящик)")),
    (r"a particle outside the walls on axis (\w)", lambda m, s: (
        f"атом оказался бы за стенкой по оси {m.group(1)}", "координаты — внутри ящика (и ниже поршня)")),
    (r"the pair cutoff \+ skin ([\d.e+-]+) exceeds half a periodic box length ([\d.e+-]+)", lambda m, s: (
        f"радиус обрезки с запасом ({_num(float(m.group(1)) * NM, 3)} нм) больше половины периодического ящика "
        f"({_num(float(m.group(2)) * NM, 3)} нм)", "меньше «Радиус обрезки» или ящик больше (оба меняются на ходу)")),
    (r"charges in a box with a periodic axis", lambda m, s: (
        "заряды в ящике с периодической осью не поддерживаются (сумма Эвальда не реализована)",
        "поставьте «Стенку» на каждую периодическую ось (ось станет со стенками) или начните новый мир с «Границы в "
        "начале» = стенки")),
    (r"a periodic box length must be >= 4 times the largest diameter \(([\d.e+-]+)\)", lambda m, s: (
        f"периодический ящик короче четырёх диаметров самого крупного атома ({_num(float(m.group(1)) * NM, 3)} нм)",
        "меньше σ атомов или ящик больше (на ходу, при непрерывных силах)")),
    (r"the piston's axis (\w)", lambda m, s: (
        f"по оси {m.group(1)} объём задаёт поршень: аффинно ящик вдоль неё не меняется",
        "двигайте поршень (его «Положение»), или «Как менять размер ящика» = сдвинуть стенку: тогда меняется верхний "
        "упор поршня")),
    (r"the piston's face ([\d.e+-]+) lies beyond", lambda m, s: (
        f"поршень стоит на {_num(float(m.group(1)) * NM, 4)} нм — выше новой верхней стенки",
        f"размер по оси поршня не меньше {_num(float(m.group(1)) * NM, 4)} нм, или сначала опустите поршень")),
    (r"axis ([xyz, ]+) is periodic: it has no wall", lambda m, s: (
        f"ось {m.group(1)} периодическая: стенки, которую можно сдвинуть, нет",
        "«Как менять размер ящика» = аффинно, или сначала поставьте «Стенку» на эту ось")),
    (r"a bond would change its length by ([\d.e+-]+) \(limit ([\d.e+-]+)\)", lambda m, s: (
        f"связи молекул растянулись или сжались бы на {_num(100 * float(m.group(1)), 3)} % (предел "
        f"{_num(100 * float(m.group(2)))} % за одно изменение: атомы сдвигаются вместе с ящиком, связи — тоже)",
        f"меняйте размер шагами не больше {_num(100 * float(m.group(2)))} %")),
    (r"the hi side of this axis is the piston", lambda m, s: (
        "верхняя сторона этой оси — поршень", "выберите нижнюю сторону или другую ось")),
    (r"no free lattice site", lambda m, s: (
        "все узлы кристалла заняты уже имеющимися атомами", "задайте кристаллу свободную область (центр и размер)")),
    (r"the region is smaller than one lattice cell", lambda m, s: (
        "область кристалла меньше одной ячейки решётки при этой плотности", "область больше или плотность выше")),
    (r"0 < x_min <= X <= L", lambda m, s: (
        "положение поршня — вне ящика", "положение от нижней стенки до верхней грани ящика")),
    (r"non-finite forces|non-finite", lambda m, s: (
        "силы стали бесконечными (атомы слишком близко)", "сдвиньте объект или уменьшите температуру")),
    (r"a thermal wall needs", lambda m, s: (
        "у тепловой стенки температура должна быть больше 0 K", "температура стенки > 0 K")),
]


def _is_russian(e):
    return any("А" <= ch <= "я" or ch in "Ёё" for ch in str(e))


def _ru(e, sim=None):
    """An engine exception in the owner's terms (a Refusal with what to change), the engine's sentence as the detail."""
    import re
    s = str(e)
    for rx, fn in _EN:
        m = re.search(rx, s)
        if m:
            text, hint = fn(m, sim)
            return refusal(text, hint=hint, detail=s)
    if isinstance(e, ValueError):
        return refusal("движок отказал в этом изменении", hint="другие значения объекта", detail=s)
    return e


def _val(k, v):
    p = SCHEMA.by_id.get(k)
    if p is not None and p.type == "select":
        return dict(p.options).get(v, v)
    return v


class Simulation(PlaygroundSimulation):
    VIZ_ID = "p03_molecules"
    speed_range = (1e-3, 1e5)  # ps of the world per second (the world's time is in seconds: ×1e-12 below)

    def __init__(self, params, seed, emit):
        super().__init__(params, seed, emit)
        self.ndim = 2 if params["dim"] == "2d" else 3
        self.hard = params.get("dynamics", "forces") == "hard"
        self.live = {k: params[k] for k in LIVE}      # the live laws in force (review UX-ui U12)
        self.model = "hard" if self.hard else self.live["model"]
        box = [params["Lx"], params["Ly"], params["Lz"]][:self.ndim]
        self.box = [float(b) / NM for b in box]  # reduced
        bd = params["boundary"]
        boundary = ["periodic", "walls", "periodic"][:self.ndim] if bd == "slab" else [bd] * self.ndim
        self.boundary = list(boundary)      # at the start; walls and pistons may make a periodic axis walled
        self.rng = np.random.default_rng(seed)
        self._ramp_seen, self._ramp_T0 = 0, None   # the last change of the box over a time announced; T at its start
        # the solver starts at the scene's time (a file's, a carried scene's): before, it started at 0 and the first
        # advance computed the whole interval up to the scene's time over the scene's atoms (found processing review
        # LB1-framework F5: the carried atoms moved before the new world's first frame)
        t0 = scene_time(params) * 1e12 / PS
        if self.hard:
            from lfphys.core.md import hard as HD
            # the walls act on the atoms' centres, as the forces' walls do: the box is the same region of the centres in
            # both dynamics (review LB1-physics P4)
            self.md = HD.HardSpheres(self.ndim, self.box, boundary, seed=int(seed), walls_on="centre", t=t0)
        else:
            self.md = MD(dim=self.ndim, box=self.box, boundary=boundary, pair=self._pair_term(),
                         dt=float(self.live["dt_fs"]) * 1e-3 / PS, seed=int(seed), t=t0)
        self.PALETTE = palette(self.ndim)
        self._kcache = {}   # object id -> its atoms' keys (derived; cleared at every change)
        # the order parameter for ``meas``, the world time it was computed at and its period's number (ORDER_EVERY_PS)
        self._order, self._order_t, self._order_bucket = None, None, None
        self.parts = {}     # object id -> np.array of particle keys (atoms, gas, crystal) or molecule keys
        self.kind = {}      # object id -> what the engine holds for it
        self.species = {}   # object id -> species name in the engine
        self.info = {}      # object id -> what the engine reported when it was made (a crystal's lattice)
        self.conv = {}      # axis -> ids of the walls / the piston that made that periodic axis walled (review U7)
        self.n_stats = 0
        self._dup = False
        self._piston_pos = None
        self._zb = {"blocks": [], "prev": None, "t_change": 0.0}
        self.start_scene()
        self._after_change()
        self.default_speed = 2.0e-12  # 2 ps of the world per second
        self.legacy = legacy_note(params.get("scene"))

    def after_header(self):
        super().after_header()
        if self.legacy:   # a scene file of the old format, read with the same laws (said once, at the start)
            self.emit({"type": "notice", "t": self.t, "text": self.legacy})

    def _pair_term(self):
        if self.live["model"] == "wca":
            return IA.WCA()
        return IA.LennardJones(float(self.live["cutoff"]), shift=self.live["shift"])

    # --- conversions -----------------------------------------------------------------------------------------------
    def _len(self, nm):
        return float(nm) / NM

    def _region_of(self, v):
        c = [float(v.get(c, 0.0)) for c in "xyz"[:self.ndim]]
        s = [float(v.get(f"s{c}", 0.0)) for c in "xyz"[:self.ndim]]
        if not any(s):
            return None
        lo = [self._len(c[i] - 0.5 * s[i]) if s[i] > 0 else 0.0 for i in range(self.ndim)]
        hi = [self._len(c[i] + 0.5 * s[i]) if s[i] > 0 else self.box[i] for i in range(self.ndim)]
        return (lo, hi)

    def _subst_values(self, v):
        if v.get("substance", "argon") == "argon":
            return 1.0, 1.0, 1.0, 0.0
        q = U.from_elementary_charge(float(v.get("charge", 0.0)))
        return U.from_amu(float(v["mass"])), float(v["sigma"]), float(v.get("epsilon", 1.0)), q

    def _species(self, obj):
        """One engine species per particle object (its own parameters): argon or the given ones, in reduced units; an
        existing one (the object made again) is changed in place in both worlds."""
        oid = obj["id"]
        m, s, e, q = self._subst_values(obj["values"])
        exists = oid in self._sp_names()
        if self.hard:
            if exists:
                self.md.set_species(oid, mass=m, sigma=s)
            else:
                self.md.add_species(oid, mass=m, sigma=s)
        elif exists:
            self.md.set_species(oid, mass=m, sigma=s, epsilon=e, charge=q)
        else:
            self.md.add_species(oid, mass=m, sigma=s, epsilon=e, charge=q)
        self.species[oid] = oid
        return oid

    def _sp_names(self):
        return [d["name"] for d in self.md.species()]

    def _sp(self, name):
        return next((d for d in self.md.species() if d["name"] == name), None)

    def _xs(self):
        """The particles' positions (wrapped on periodic axes) and diameters (reduced)."""
        md = self.md
        x = np.asarray(md.positions(), float).reshape(-1, self.ndim).copy()
        per = np.flatnonzero(md.periodic)
        L = np.array(self.box)
        for a in per:
            x[:, a] -= L[a] * np.floor(x[:, a] / L[a])
        sig = {d["name"]: float(d.get("sigma", 1.0)) for d in md.species()}
        names = md.particles()["species"] if md.n else []
        return x, np.array([sig[q] for q in names], float)

    def _hi(self, a):
        """The upper end of axis a for the particles: the piston's face on its axis, else the box."""
        if not self.hard:
            p = self.md.piston()
            if p is not None and "xyz".index(p["axis"]) == a:
                return float(p["X"])
        return self.box[a]

    # --- placement (reviews UX-ui U4, U8; the integrator's API of 2026-11-05) -----------------------------------
    def _import_values(self, kind, values):
        """An object's values as this world takes them (LB1, P16.1: a scene carried over into a new world of the other
        space): in a plane the keys of z (its coordinate, region size, speed) are dropped; a wall or a piston across z
        is refused (a plane has no z). Values of the plane in a volume take z's defaults. A copy."""
        values = dict(values or {})
        if self.ndim == 2:
            if kind in ("wall", "piston") and values.get("axis") == "z":
                what = "стенку" if kind == "wall" else "поршень"
                raise refusal(f"в плоскости нет оси z: {what} поперёк z не перенести",
                              hint=f"поставьте {'её' if kind == 'wall' else 'его'} поперёк x или y, или вернитесь к объёму "
                                   f"(«Пространство»)")
            for k in AXIS_KEYS:
                values.pop(k, None)
        return values

    def _values(self, ot, values):
        # every path that adds an object (a palette form, a scene file, a scene carried over) takes the values so
        return super()._values(ot, self._import_values(ot.type, values))

    def place(self, kind, values):
        """A palette object's values before it is added: the defaults completed, a clicked point (``position``, nm)
        taken as the object's place (a region's centre, the nearest face for a wall or a piston), an atom moved to the
        nearest free spot inside the box, a piston above the atoms below it; what cannot fit is refused at once with
        the numbers (a gas or molecules denser than random packing allows, a temperature the time step cannot
        resolve). Deterministic: it reads the state, never changes it."""
        ot = self._type(kind)
        values = self._import_values(kind, values)
        # a clicked point is a list; the piston's own «position» is a number
        pos = values.pop("position") if isinstance(values.get("position"), (list, tuple)) else None
        v, errors = ot.schema.resolve(None, values)
        if errors:
            raise refusal("; ".join(errors))
        v = dict(v)
        nd = self.ndim
        if pos is not None:
            pos = [float(q) for q in list(pos)[:nd]]
            if kind in ("atom", "probe"):
                for i, c in enumerate("xyz"[:nd]):
                    v[c] = pos[i]
            elif kind in ("gas", "crystal", "molecule", "thermostat"):
                for i, c in enumerate("xyz"[:nd]):
                    v[c] = pos[i]
                    if not float(v.get(f"s{c}", 0.0)):
                        v[f"s{c}"] = round(self.box[i] * NM / 3.0, 4)
            elif kind in ("wall", "piston"):
                a, side = self._nearest_face(pos)
                v["axis"] = "xyz"[a]
                if kind == "wall":
                    v["side"] = side
                else:
                    v["position"] = round(min(max(pos[a], 0.0), self.box[a] * NM), 4)
        carrying = getattr(self, "carrying", None) is not None   # its atoms come with their places (on_add)
        if kind == "atom" and not carrying:
            sig = self._subst_values(v)[1]
            x = self._free_spot(sig, [self._len(v[c]) for c in "xyz"[:nd]])
            for i, c in enumerate("xyz"[:nd]):
                v[c] = round(x[i] * NM, 6)
        elif kind == "probe":
            for i, c in enumerate("xyz"[:nd]):
                v[c] = round(min(max(float(v[c]), 0.0), self.box[i] * NM), 6)
            per = [i for i in range(nd) if self.md.periodic[i]]
            if per:
                v["r"] = min(float(v["r"]), round(0.5 * min(self.box[i] for i in per) * NM, 6))
        elif kind == "piston" and not carrying:
            v["position"] = self._piston_position(v)
            # the framework takes a returned «position» for a clicked point and drops a number: kept here for on_add
            self._piston_pos = v["position"]
        elif kind in ("gas", "molecule") and not carrying:
            self._pack_check(kind, v)
        self._check_temperature(kind, v)
        return v

    def _nearest_face(self, pos):
        best = None
        for a in range(self.ndim):
            L = self.box[a] * NM
            for side, d in (("lo", abs(pos[a])), ("hi", abs(L - pos[a]))):
                if best is None or d < best[0]:
                    best = (d, a, side)
        return best[1], best[2]

    def _allowed(self, sig):
        """Per axis the interval a particle's centre of diameter ``sig`` may take (reduced)."""
        lo, hi = [], []
        for a in range(self.ndim):
            if self.md.periodic[a]:
                lo.append(0.0)
                hi.append(self.box[a])
            else:
                lo.append(0.5 * sig)
                hi.append(self._hi(a) - 0.5 * sig)
        return np.array(lo), np.array(hi)

    def _is_free(self, sig, x):
        lo, hi = self._allowed(sig)
        x = np.asarray(x, float)
        if np.any((x < lo) | (x > hi)):
            return False
        X, S = self._xs()
        xw = x.copy()
        for a in np.flatnonzero(self.md.periodic):
            xw[a] -= self.box[a] * math.floor(xw[a] / self.box[a])
        return bool(free_sites(xw[None], sig, X, S, self.box, self.md.periodic)[0])

    def _free_spot(self, sig, x0, refuse=True):
        """The free point nearest to x0 (reduced): no particle nearer than sigma_ij, inside the walls (sigma/2 from
        them) and below the piston; first on a fine grid around x0, then on a coarser one over the whole box. None
        (or a refusal) when there is none."""
        lo, hi = self._allowed(sig)
        L = np.array(self.box)
        per = np.asarray(self.md.periodic, bool)
        if np.any(hi < lo):
            if not refuse:
                return None
            raise refusal(f"атом диаметром {_num(sig * NM, 3)} нм не помещается между стенками ящика",
                          hint="меньше размер σ атома, или больше ящик (на ходу)")
        x0 = np.asarray(x0, float).copy()
        for a in range(self.ndim):
            x0[a] = x0[a] - L[a] * math.floor(x0[a] / L[a]) if per[a] else min(max(x0[a], lo[a]), hi[a])
        X, S = self._xs()

        def nearest(points):
            pw = points.copy()
            for a in np.flatnonzero(per):
                pw[:, a] -= L[a] * np.floor(pw[:, a] / L[a])
            ok = np.all((pw >= lo - 1e-12) & (pw <= hi + 1e-12), axis=1)
            pw = pw[ok]
            if not len(pw):
                return None
            free = free_sites(pw, sig, X, S, L, per)
            if not free.any():
                return None
            pw = pw[free]
            dx = pw - x0
            for a in np.flatnonzero(per):
                dx[:, a] -= L[a] * np.rint(dx[:, a] / L[a])
            d2 = np.einsum("ij,ij->i", dx, dx)
            return pw[int(np.argmin(d2))]

        h = 0.2 * sig
        g = np.arange(-20, 21) * h
        local = np.stack(np.meshgrid(*([g] * self.ndim), indexing="ij"), -1).reshape(-1, self.ndim) + x0
        got = nearest(local)
        if got is None:
            span = hi - lo
            step = max(0.3 * sig, float((np.prod(np.maximum(span, sig)) / 3e5) ** (1.0 / self.ndim)))
            axes = [np.linspace(lo[a], hi[a], max(2, int(span[a] / step) + 1)) for a in range(self.ndim)]
            got = nearest(np.stack(np.meshgrid(*axes, indexing="ij"), -1).reshape(-1, self.ndim))
        if got is None and refuse:
            raise refusal(f"в ящике нет свободного места для атома диаметром {_num(sig * NM, 3)} нм",
                          hint="уберите часть атомов, уменьшите σ атома или сделайте ящик больше (на ходу)")
        return got

    def _piston_position(self, v):
        """The piston's face in nm: as asked, but above every atom's centre on its axis (the gas side is below the face;
        the face, like a wall, reflects the centres)."""
        a = "xyz".index(v["axis"])
        X = self._len(v["position"])
        L = self.box[a]
        x, sig = self._xs()
        need = float(np.max(x[:, a])) * (1 + 1e-9) if len(x) else 0.0
        X = min(max(X, need, 1e-3 * L * 1.01), L)
        return math.ceil(X * NM * 1e6) / 1e6 if X < L else round(L * NM, 9)

    def _pack_check(self, kind, v):
        """Refuse at once what random placement cannot fit (review UX-ui U5, UX-params P33): the covered fraction of the
        region with the atoms already in it and the new ones, against where random sequential insertion jams."""
        nd = self.ndim
        reg = self._region_of(v)
        lo = np.array(reg[0]) if reg else np.zeros(nd)
        hi = np.array(reg[1]) if reg else np.array([self._hi(a) for a in range(nd)])
        lo, hi = np.maximum(lo, 0.0), np.minimum(hi, [self._hi(a) for a in range(nd)])
        if np.any(hi <= lo):
            raise refusal("область объекта лежит вне ящика",
                          hint=f"центр и размеры области — внутри ящика {' × '.join(f'{_num(b * NM)}' for b in self.box)} нм "
                               f"(размер 0 — весь ящик)")
        V = float(np.prod(hi - lo))
        sig = self._subst_values(v)[1]
        v1 = (math.pi / 4 * sig ** 2) if nd == 2 else (math.pi / 6 * sig ** 3)
        X, S = self._xs()
        inside = np.all((X >= lo) & (X <= hi), axis=1) if len(X) else np.zeros(0, bool)
        vs = (math.pi / 4 * S ** 2) if nd == 2 else (math.pi / 6 * S ** 3)
        have = float(np.sum(vs[inside])) if len(X) else 0.0
        if kind == "gas":
            per, n, lim, what = 1, int(v["n"]), JAM[nd], "атомов"
        else:
            per = 2 if v["shape"] == "dimer" else 3 if v["shape"] == "bent" else int(v["atoms"])
            n, lim, what = int(v["count"]), MOL_JAM[nd], "молекул"
        eta = (have + n * per * v1) / V
        if eta > lim:
            n_max = max(0, int((lim * V - have) / (per * v1)))
            area = " × ".join(_num((h - l) * NM, 3) for l, h in zip(lo, hi))
            raise refusal(f"{n} {what} в области {area} нм заняли бы {eta:.0%} {'площади' if nd == 2 else 'объёма'}"
                          f" (с уже имеющимися атомами) — случайно без перекрытий укладывается не больше ≈ {lim:.0%}",
                          hint=f"не больше {n_max} {what}, или область больше; плотнее — «Кристалл»")
        if _require is not None:
            n_all = len(X) + n * per
            rl = (float(self.live["cutoff"]) if self.live["model"] == "lj" else 1.13) * max(sig, float(S.max())
                                                                                            if len(S) else 1.0) + 0.3
            vol = float(np.prod(self.box))
            ball = (math.pi * rl ** 2) if nd == 2 else (4.0 / 3.0 * math.pi * rl ** 3)
            pairs = 0.5 * n_all * min(n_all, n_all / vol * ball * max(1.0, eta / max(n_all * v1 / vol, 1e-9)))
            _require(int(pairs * PAIR_BYTES), "список соседних пар атомов", "меньше атомов или меньше радиус обрезки")

    def _lightest(self):
        ms = [float(d["mass"]) for d in self.md.species() if math.isfinite(d["mass"])]
        return min(ms) if ms else 1.0

    def _smallest(self):
        ss = [float(d.get("sigma", 1.0)) for d in self.md.species()]
        return min(ss) if ss else 1.0

    def _step_q(self, vel, energy, sig, eps, dt):
        """q = 12 v dt / r_t: the step against the steepness of the repulsion at the collision energy ``energy``."""
        if vel <= 0 or eps <= 0:
            return 0.0
        r_t = sig * min((4.0 * eps / energy) ** (1.0 / 12.0), 2.0 ** (1.0 / 6.0)) if energy > 0 else sig
        return 12.0 * vel * dt / r_t

    def _check_temperature(self, kind, v, dt=None):
        """Refuse a temperature (or a speed) the time step cannot resolve (q > Q_MAX; review UX-params P32: at 10^5 K
        the Verlet step let atoms pass into each other and the world stopped with a traceback), with the largest
        temperature at this step and the step for this temperature."""
        if self.hard or kind not in ("gas", "crystal", "molecule", "atom", "thermostat", "wall"):
            return
        if kind == "wall" and v.get("kind") != "thermal":
            return
        nd = self.ndim
        dt = self.md.dt if dt is None else dt
        dt_fs = dt * PS * 1e3
        own = kind in ("gas", "crystal", "molecule", "atom")
        m, sig, eps, _ = self._subst_values(v) if own else (self._lightest(), self._smallest(), 1.0, 0.0)
        if kind == "atom":
            vel = math.sqrt(sum((float(v.get(f"v{c}", 0.0)) / U.velocity_m_s) ** 2 for c in "xyz"[:nd]))
            q = self._step_q(vel, 0.5 * m * vel * vel, sig, eps, dt)
            if q <= Q_MAX:
                return
            # v^(7/6) (m/2)^(1/12) = Q_MAX sigma (4 eps)^(1/12) / (12 dt)
            v_ok = (Q_MAX * sig * (4.0 * eps) ** (1 / 12) / (12.0 * dt) / (0.5 * m) ** (1 / 12)) ** (6 / 7)
            raise refusal(f"атом со скоростью {_num(vel * U.velocity_m_s, 3)} м/с: шаг {_num(dt_fs)} фс не разрешает его удары "
                          f"(за шаг он проходит {_num(q, 2)} от толщины крутой части отталкивания, можно до {_num(Q_MAX)})",
                          hint=f"скорость не больше {_num(v_ok * U.velocity_m_s, 3)} м/с, или «Шаг по времени» не больше "
                               f"{_num(dt_fs * Q_MAX / q, 2)} фс (меняется на ходу, в «Установке»)")
        T = float(v.get("T", 0.0)) / KELVIN
        vc = math.sqrt(sum((float(v.get(f"v{c}", 0.0)) / U.velocity_m_s) ** 2 for c in "xyz"[:nd])) if own else 0.0
        if vc > 0:
            # a thrown group: its atoms meet the others at the thermal speed plus the centre's (LB1, P16.2)
            vel = math.sqrt(nd * T / m) + vc
            q = self._step_q(vel, 0.5 * m * vel * vel, sig, eps, dt)
            if q > Q_MAX:
                v_ok = max(0.0, (Q_MAX / q) ** (6.0 / 7.0) * vel - math.sqrt(nd * T / m))
                raise refusal(f"скорость центра масс {_num(vc * U.velocity_m_s, 3)} м/с при {_num(float(v.get('T', 0.0)), 4)} K: "
                              f"шаг {_num(dt_fs)} фс не разрешает удары атомов (за шаг атом проходит {_num(q, 2)} от "
                              f"толщины крутой части отталкивания, можно до {_num(Q_MAX)})",
                              hint=f"скорость центра масс не больше ≈ {_num(v_ok * U.velocity_m_s, 2)} м/с, или «Шаг по "
                                   f"времени» не больше {_num(dt_fs * Q_MAX / q, 2)} фс (на ходу)")
        if T <= 0:
            return
        q = self._step_q(math.sqrt(nd * T / m), T, sig, eps, dt)
        if q <= Q_MAX:
            return
        # q ∝ T^(1/2 + 1/12): the largest T at this step, and the step for this T (q ∝ dt)
        T_ok = T * (Q_MAX / q) ** (12.0 / 7.0)
        raise refusal(f"при {_num(float(v['T']), 4)} K шаг {_num(dt_fs)} фс не разрешает столкновения атомов (за шаг атом проходит "
                      f"{_num(q, 2)} от толщины крутой части отталкивания, можно до {_num(Q_MAX)}): атомы проскочили бы друг в "
                      f"друга", hint=f"температура не выше {_num(T_ok * KELVIN, 3)} K при этом шаге, или «Шаг по времени» не "
                                     f"больше {_num(dt_fs * Q_MAX / q, 2)} фс (меняется на ходу, в «Установке»)")

    def palette_state(self):
        """The palette types the world cannot take now (review UX-ui U7, U22): what the hard spheres have not
        (molecules, the piston, thermostats, the field: LB1, one palette for both dynamics), and, in a box already
        packed beyond random insertion, a gas or molecules; walls and the piston work on every axis (a periodic one
        becomes walled)."""
        out = {}
        if self.hard:
            why = ("у твёрдых {} нет {}: переключите «Динамика» = непрерывные силы (на ходу, в «Законах»)")
            bodies = "дисков" if self.ndim == 2 else "шаров"
            for k, what in (("molecule", "молекул (связей)"), ("piston", "поршня"), ("thermostat", "термостатов"),
                            ("gravity", "поля")):
                out[k] = why.format(bodies, what)
        X, S = self._xs()
        if not len(X):
            return out
        nd = self.ndim
        vs = (math.pi / 4 * S ** 2) if nd == 2 else (math.pi / 6 * S ** 3)
        eta = float(np.sum(vs)) / float(np.prod([self._hi(a) for a in range(nd)]))
        if eta > JAM[nd]:
            out["gas"] = f"ящик уже заполнен на {eta:.0%}: случайно больше атомов не уложить — уберите часть атомов"
        if eta > MOL_JAM[nd] and "molecule" in self.PALETTE and "molecule" not in out:
            out["molecule"] = f"ящик уже заполнен на {eta:.0%}: молекулы не уложить — уберите часть атомов"
        return out

    # --- all-or-nothing changes (review B7-md M6) -----------------------------------------------------------------
    _MAPS = ("parts", "kind", "species", "info", "_zb", "conv", "live", "model", "box", "hard", "_ramp_seen", "_ramp_T0")

    def _snapshot(self):
        # the solver's class too: a refused switch of the dynamics puts the other solver back (LB1)
        return (type(self.md), self.md.state_dict(), {k: copy.deepcopy(getattr(self, k)) for k in self._MAPS},
                copy.deepcopy(self.rng.bit_generator.state))

    def _restore(self, snap):
        cls, st, maps, rng = snap
        self.md = cls.from_state_dict(st)
        for k, v in maps.items():
            setattr(self, k, v)
        self.rng.bit_generator.state = rng
        self._kcache = {}

    def _atomic(self, fn, *a):
        snap = self._snapshot()
        try:
            fn(*a)
            self._after_change()
        except BaseException as e:
            self._restore(snap)
            if isinstance(e, Exception) and not _is_russian(e):
                raise _ru(e, self) from e
            raise

    def _after_change(self):
        """A change of the scene: the counters (heat, work, impulses, the first-law balance), the momentum's
        reference, the mean-square displacement and the hard world's pressure blocks restart now."""
        self.md.reset_counters()
        self.md.msd_origin()
        self._zb = {"blocks": [], "prev": None, "t_change": float(self.md.t)}
        self._kcache = {}

    # --- the framework's hooks -------------------------------------------------------------------------------------
    def scene(self, args):
        # a copy lands on its original by design (lfviz.playground): this section moves it to a free spot (U4)
        self._dup = args.get("op") == "duplicate"
        self._piston_pos = None
        try:
            return super().scene(args)
        finally:
            self._dup = False
            self._piston_pos = None

    def on_add(self, obj, state):
        if state is not None and getattr(self, "carrying", None) is not None and obj["type"] in CARRIED:
            # a carry-over into a new world (review LB1-framework F5): the atoms with their positions and velocities
            why = self._carry_mismatch(state)
            if why is None:
                try:
                    self._atomic(self._add_carried, obj, state)
                    return
                except Exception as e:  # noqa: BLE001 - started again from the parameters, said in the notice
                    why = (getattr(e, "text", None) or str(e))[:300]
            self._carry_note(f"{CARRIED[obj['type']]} начаты заново из параметров: {why}", obj, restarted=True)
        self._atomic(self._add_obj, obj)

    def on_remove(self, obj):
        self._atomic(self._remove_obj, obj)

    def on_set(self, obj, old):
        self._atomic(self._set_obj, obj, old)

    def _note(self, text):
        """A short note for the owner about what an edit did (shown at once: ``notify``)."""
        if not self._loading:
            self.emit({"type": "event", "kind": "scene", "t": self.t, "text": text, "notify": True})

    def _add_obj(self, obj):
        t, v, md = obj["type"], obj["values"], self.md
        oid = obj["id"]
        if self.hard and t in ("molecule", "piston", "thermostat", "gravity"):   # (a scene file or a carry-over)
            raise refusal(self.palette_state()[t].split(":")[0], hint="«Динамика» = непрерывные силы (на ходу)")
        if t in ("gas", "crystal", "atom", "molecule", "thermostat", "wall"):
            self._check_temperature(t, v)
        if t in ("gas", "crystal", "atom", "molecule"):
            if t in ("gas", "molecule"):
                self._pack_check(t, v)
            sp = self._species(obj)
            Tred = float(v.get("T", 0.0)) / KELVIN
            if t == "gas":
                keys = self._gas(sp, int(v["n"]), self._region_of(v), Tred, v["start"])
            elif t == "crystal":
                inf = {}
                keys = md.fill(sp, density=float(v["density"]), region=self._region_of(v), T=Tred, info=inf,
                               skip_occupied=True)
                self.info[oid] = inf
                if inf.get("skipped"):
                    self._note(f"«{obj['label']}»: {inf['skipped']} узлов решётки заняты уже имеющимися атомами — "
                               f"оставлены пустыми")
            elif t == "atom":
                keys = self._atom(obj, sp)
            else:
                keys = self._molecules(obj, sp, Tred)
            self.parts[oid] = np.asarray(keys)
            self.kind[oid] = "molecules" if t == "molecule" else "particles"
            self._kcache.pop(oid, None)
            vc = np.array([float(v.get(f"v{c}", 0.0)) / U.velocity_m_s for c in "xyz"[:self.ndim]])
            if t != "atom" and np.any(vc):      # the group's centre-of-mass velocity (a throw, LB1)
                ak = self._atom_keys(oid)
                if len(ak):
                    md.set(ak, v=md.particles(ak)["v"] + vc)
        elif t == "wall":
            self._make_walled("xyz".index(v["axis"]), oid)
            self._wall(v)
            self.kind[oid] = "wall"
        elif t == "piston":
            if getattr(self, "_piston_pos", None) is not None:
                v["position"] = self._piston_pos
            a = "xyz".index(v["axis"])
            self._make_walled(a, oid)
            self._check_piston(v)
            self._piston(v)
            self.kind[oid] = "piston"
        elif t == "thermostat":
            self._region_inside(v)
            self.parts[oid] = md.add_thermostat(v["kind"], float(v["T"]) / KELVIN, region=self._region_of(v),
                                                **self._bath_args(v))
            self.kind[oid] = "thermostat"
        elif t == "gravity":
            md.set_gravity(self._gvec(v))
            self.kind[oid] = "gravity"
        elif t == "probe":
            self._point_inside(v)
            self.kind[oid] = "probe"

    def _point_inside(self, v):
        """A probe's centre inside the box along its walled axes (review UX-ui U8: far outside it was accepted)."""
        for i, c in enumerate("xyz"[:self.ndim]):
            if not self.md.periodic[i] and not (0.0 <= float(v[c]) <= self.box[i] * NM):
                raise refusal(f"центр термометра по оси {c} ({_num(float(v[c]), 4)} нм) — вне ящика",
                              hint=f"{c} от 0 до {_num(self.box[i] * NM, 4)} нм")

    def _region_inside(self, v):
        reg = self._region_of(v)
        if reg is None:
            return
        for i in range(self.ndim):
            if not self.md.periodic[i] and (reg[1][i] <= 0.0 or reg[0][i] >= self.box[i]):
                raise refusal(f"область термостата по оси {'xyz'[i]} лежит вне ящика",
                              hint="центр и размеры области — внутри ящика (размер 0 — весь ящик)")

    def _atom(self, obj, sp):
        """One atom: at its place when that is free; a copy (⧉) goes to the nearest free spot; an occupied or outside
        place is refused with the nearest free one (review UX-ui U4, U8)."""
        v = obj["values"]
        x = np.array([self._len(v[c]) for c in "xyz"[:self.ndim]])
        sig = self._sp(sp)["sigma"]
        if not self._is_free(sig, x):
            spot = self._free_spot(sig, x)
            if self._dup:
                x = spot
                for i, c in enumerate("xyz"[:self.ndim]):
                    v[c] = round(spot[i] * NM, 6)
            else:
                lo, hi = self._allowed(sig)
                out = [c for i, c in enumerate("xyz"[:self.ndim]) if not (lo[i] <= x[i] <= hi[i])]
                where = (f"за стенкой ящика по оси {', '.join(out)}" if out
                         else "ближе σ к другому атому (атомы перекрылись бы)")
                raise refusal(f"атом в точке ({', '.join(f'{_num(q * NM, 4)}' for q in x)}) нм — {where}",
                              hint="ближайшее свободное место — (" + ", ".join(f"{_num(q * NM, 4)}" for q in spot) + ") нм")
        vel = np.array([float(v[f"v{c}"]) / U.velocity_m_s for c in "xyz"[:self.ndim]])
        return self.md.add(sp, x, v=vel)

    def _check_piston(self, v):
        a = "xyz".index(v["axis"])
        X = self._len(v["position"])
        x, sig = self._xs()
        need = float(np.max(x[:, a])) if len(x) else 0.0
        if X > self.box[a] * (1 + 1e-12) or X <= 0:
            raise refusal(f"поршень на {_num(float(v['position']))} нм — вне ящика (по оси {v['axis']} он "
                          f"{_num(self.box[a] * NM, 4)} нм)", hint=f"положение от {_num(need * NM, 4)} до {_num(self.box[a] * NM, 4)} нм")
        if X < need:
            raise refusal(f"под поршнем на {_num(float(v['position']))} нм не помещаются атомы: самый высокий по оси "
                          f"{v['axis']} доходит до {_num(need * NM, 4)} нм",
                          hint=f"положение поршня не ниже {_num(math.ceil(need * NM * 1e4) / 1e4)} нм")

    def _make_walled(self, a, oid):
        """A wall or the piston on a periodic axis makes it walled at the current moment (review UX-ui U7, UX-params
        P31); the axis returns to periodic when the last such object goes."""
        if self.md.periodic[a]:
            try:
                self.md.set_boundary(a, "walls")
            except ValueError as e:
                raise refusal(f"ось {'xyz'[a]} периодическая, и у её граней есть атомы: стенку там не поставить, не "
                              f"сдвинув их", hint="уберите атомы у граней или начните новый мир с «Границы в начале» "
                                                  "= стенки", detail=str(e)) from e
            self.conv[a] = set()
            self._note(f"ось {'xyz'[a]} стала осью со стенками (зеркальные стенки на её гранях); когда последняя "
                       f"стенка или поршень на ней уйдёт, она снова станет периодической")
        if a in self.conv:
            self.conv[a].add(oid)

    def _release_axis(self, oid, a=None):
        for ax in [a] if a is not None else list(self.conv):
            ids = self.conv.get(ax)
            if ids is None:
                continue
            ids.discard(oid)
            if not ids:
                del self.conv[ax]
                try:
                    self.md.set_boundary(ax, "periodic")
                    self._note(f"ось {'xyz'[ax]} снова периодическая (её стенки убраны)")
                except ValueError as e:
                    self._note(f"ось {'xyz'[ax]} остаётся со стенками (зеркальными): атомы у противоположных граней "
                               f"перекрылись бы при периодичности ({_ru(e, self)})")

    def _gas(self, sp, n, region, T, start):
        keys = self.md.fill(sp, n=n, region=region, T=T, arrangement="random")
        if start == "same_speed" and len(keys):
            # every atom with the speed of the mean kinetic energy at T, in random directions (not Maxwellian); with one
            # atom or T = 0 there is nothing to rescale (review UX-params P32: 0/0)
            m = self._sp(sp)["mass"]
            speed = math.sqrt(self.ndim * T / m)
            d = self.rng.normal(size=(len(keys), self.ndim))
            d /= np.linalg.norm(d, axis=1, keepdims=True)
            vel = speed * d
            if len(keys) > 1:
                vel -= vel.mean(axis=0)
            ms = math.sqrt(float(np.mean(np.sum(vel * vel, axis=1))))
            if ms > 0 and speed > 0:
                vel *= speed / ms
            self.md.set(keys, v=vel)
        return keys

    def _molecules(self, obj, sp, T):
        """``count`` molecules at random places and orientations, each atom's potential energy at insertion below
        2kT (at least 0.1 ε); "maxwell": every atom's velocity Maxwellian at T and the bond lengths and angles drawn
        about their rest values with the Boltzmann spread √(kT/k) (harmonic terms: each starts with about kT/2), the
        canonical start; "translation": every molecule moves as a whole with a Maxwellian velocity of its mass at T,
        rest geometry (no rotation, no vibration). The object's total momentum is removed (review B7-md M4).

        Placed in batches (review UX-ui U5: one engine edit per try took minutes): candidates for all the molecules
        still missing are drawn at once and inserted in one edit (``MD.add_molecules``: candidates over the energy
        bound left out, the first ones in order kept), until all are placed or 200 tries per molecule were spent."""
        v, md, oid = obj["values"], self.md, obj["id"]
        shape = v["shape"]
        na = 2 if shape == "dimer" else 3 if shape == "bent" else int(v["atoms"])
        b0, kb = float(v["bond"]), float(v["k_bond"])
        md.set_bond_type(f"{oid}-b", IA.HarmonicBond(kb, b0))
        th0 = math.radians(float(v.get("angle", 180.0))) if na >= 3 else math.pi
        ka = float(v.get("k_angle", 0.0))
        if na >= 3:
            md.set_angle_type(f"{oid}-a", IA.HarmonicAngle(ka, th0))
        bonds = [(i, i + 1, f"{oid}-b") for i in range(na - 1)]
        angles = [(i, i + 1, i + 2, f"{oid}-a") for i in range(na - 2)]
        thermal = v.get("start", "maxwell") == "maxwell" and T > 0
        m_atom = self._sp(sp)["mass"]
        reg = self._region_of(v) or ([0.0] * self.ndim, [self._hi(a) for a in range(self.ndim)])
        lo, hi = np.array(reg[0]), np.array(reg[1])
        e_max = max(2.0 * T, 0.1)
        count = int(v["count"])
        mks, tries = [], 0
        while len(mks) < count:
            need = count - len(mks)
            k = min(4 * need + 16, 4096, 200 * count - tries)
            if k <= 0:
                raise refusal(f"не удалось разместить {count} молекул без перекрытий: размещено {len(mks)}",
                              hint="меньше молекул или больше область")
            tries += k
            X = self._mol_candidates(k, na, b0, kb, th0, ka, thermal, T, lo, hi)
            vel = None
            if not thermal:
                vc = (self.rng.normal(size=(k, 1, self.ndim)) * math.sqrt(T / (na * m_atom)) if T > 0
                      else np.zeros((k, 1, self.ndim)))
                vel = np.broadcast_to(vc, (k, na, self.ndim))
            _, mk, _ = md.add_molecules(sp, X, bonds=bonds, angles=angles, v=vel, T=T if thermal else None,
                                        max_energy=e_max, limit=need)
            mks.extend(int(q) for q in mk)
        keys = np.concatenate([md.molecules()[mk] for mk in mks])
        if len(keys) > 1:
            vel = md.particles(keys)["v"]
            md.set(keys, v=vel - vel.mean(axis=0))   # one species: equal masses
        return mks

    def _mol_candidates(self, k, na, b0, kb, th0, ka, thermal, T, lo, hi):
        """k candidate molecules (k, na, d): a planar zigzag with this molecule's bond lengths and angles (Boltzmann
        spreads at a thermal start), turned at random, centred at random in [lo, hi]."""
        nd = self.ndim
        bl = b0 + (self.rng.normal(size=(k, na - 1)) * math.sqrt(T / kb) if thermal else 0.0)
        bl = np.maximum(np.broadcast_to(bl, (k, na - 1)), 0.3 * b0)
        if na >= 3:
            th = th0 + (self.rng.normal(size=(k, na - 2)) * math.sqrt(T / ka) if thermal and ka > 0 else 0.0)
            th = np.clip(np.broadcast_to(th, (k, na - 2)), 0.05, math.pi)
        pts = np.zeros((k, na, 3))
        pts[:, 1, 0] = bl[:, 0]
        heading = np.zeros(k)
        for j in range(1, na - 1):
            heading = heading + (math.pi - th[:, j - 1]) * (1 if j % 2 else -1)
            pts[:, j + 1, 0] = pts[:, j, 0] + bl[:, j] * np.cos(heading)
            pts[:, j + 1, 1] = pts[:, j, 1] + bl[:, j] * np.sin(heading)
        tpl = pts[:, :, :nd]
        tpl = tpl - tpl.mean(axis=1, keepdims=True)
        if nd == 2:
            a = 2 * math.pi * self.rng.random(k)
            R = np.stack([np.stack([np.cos(a), -np.sin(a)], -1), np.stack([np.sin(a), np.cos(a)], -1)], -2)
        else:
            q = self.rng.normal(size=(k, 4))
            q /= np.linalg.norm(q, axis=1, keepdims=True)
            w, x, y, z = q.T
            R = np.stack([np.stack([1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)], -1),
                          np.stack([2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)], -1),
                          np.stack([2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)], -1)], -2)
        c = lo + (hi - lo) * self.rng.random((k, nd))
        return np.einsum("kij,knj->kni", R, tpl) + c[:, None, :]

    def _wall(self, v, reset=False):
        kind = "specular" if reset else v["kind"]
        args = {}
        if kind == "thermal":
            T = float(v["T"]) / KELVIN
            if not T > 0:
                raise refusal("у тепловой стенки температура должна быть больше 0 K",
                              hint="температура стенки > 0 K, или стенка зеркальная")
            args["T"] = T
        if self.hard and kind == "soft":
            raise refusal("у твёрдых шаров мягкой стенки нет", hint="зеркальная или тепловая стенка")
        if kind == "soft":
            args["term"] = IA.LJWall(self.ndim)
        self.md.set_wall(v["axis"], v["side"], kind, **args)

    def _piston(self, v, old=None):
        """Put the piston or change it. Its position is set when it is put or when "position" itself is edited; its
        velocity when it is put or its mass or driven speed is edited (review B7-md M12): an edit of the pressure
        acts on the piston where it is."""
        p = float(v["p_ext"])
        p_red = U.from_bar(p) if self.ndim == 3 else p * 1e-3 / U.pressure_Pa(2)
        m = float(v["mass"])
        kw = {"p_ext": p_red}
        if old is None or old.get("position") != v["position"] or old.get("axis") != v["axis"]:
            kw["X"] = self._len(v["position"])
        if m > 0:
            kw["mass"] = U.from_amu(m)
        else:
            kw["mass"] = math.inf
            if old is None or old.get("speed") != v["speed"] or old.get("mass") != v["mass"]:
                kw["V"] = float(v["speed"]) / U.velocity_m_s
        if old is not None and m > 0 and float(old.get("mass", 0.0)) == 0.0:
            kw["V"] = 0.0      # a driven piston made free starts at rest
        self.md.set_piston(v["axis"], **kw)

    def _bath_args(self, v):
        if v["kind"] == "csvr":
            return {"tau": float(v["tau"]) / PS}
        return {"gamma": float(v["gamma"]) * PS}

    def _gvec(self, v):
        g = [0.0] * self.ndim
        g[1] = -float(v["g"])
        return g

    def _remove_obj(self, obj):
        oid, md = obj["id"], self.md
        mol_atoms = self._atom_keys(oid) if self.kind.get(oid) == "molecules" else None
        k = self.kind.pop(oid, None)
        if k == "particles":
            md.remove(self.parts.pop(oid))
        elif k == "molecules":
            self.parts.pop(oid)
            if len(mol_atoms):
                md.remove(mol_atoms)  # all the molecules' atoms, bonds and angles in one edit (U5)
        elif k == "wall":
            self._wall(obj["values"], reset=True)
            self._release_axis(oid, "xyz".index(obj["values"]["axis"]))
        elif k == "piston":
            md.remove_piston()
            self._release_axis(oid, "xyz".index(obj["values"]["axis"]))
        elif k == "thermostat":
            md.remove_thermostat(self.parts.pop(oid))
        elif k == "gravity":
            md.set_gravity([0.0] * self.ndim)
        self.info.pop(oid, None)

    def _set_obj(self, obj, old):
        oid, k, v = obj["id"], self.kind.get(obj["id"]), obj["values"]
        md = self.md
        thrown = [a for a in range(self.ndim) if THROW_KEYS[a] in v and v[THROW_KEYS[a]] != old.get(THROW_KEYS[a])]
        if thrown:
            # a throw in the world's units (nm/s) becomes the object's velocity in m/s (review LB1-p02-ux X4); it is
            # applied even when equal to the stored one (the stored velocity is the last one set, not the motion now)
            old = dict(old)
            for a in thrown:
                v[VEL_KEYS[a]] = float(v[THROW_KEYS[a]]) / NM_PER_S
                old[VEL_KEYS[a]] = None
        if obj["type"] in ("gas", "crystal", "atom", "molecule", "thermostat", "wall"):
            self._check_temperature(obj["type"], v)
        if k in ("particles", "molecules"):
            # a handle param sent by a drag or a throw counts as changed even when equal to the stored one (old[k] is
            # None then: the stored place is where the object was last set, not where it is): never used here
            changed = {key for key in v if v.get(key) != old.get(key)}
            pos = [a for a in range(self.ndim) if POS_KEYS[a] in changed]
            vel = [a for a in range(self.ndim) if VEL_KEYS[a] in changed]
            other = changed - SP_KEYS - set(POS_KEYS) - set(VEL_KEYS) - set(THROW_KEYS)
            if other:  # a new set of atoms (count, region size, temperature, shape) at the current moment
                self._remove_obj({**obj, "values": old})
                self._add_obj(obj)
                return
            if changed & SP_KEYS:
                # the substance changed: the same atoms with new parameters now, at the same temperature (a mass
                # change rescales the velocities by sqrt(m_old/m_new); review B7-md M14)
                m_old = self._sp(oid)["mass"]
                self._species(obj)
                m_new = self._sp(oid)["mass"]
                if m_new != m_old:
                    keys = self._atom_keys(oid)
                    if len(keys):
                        md.set(keys, v=md.particles(keys)["v"] * math.sqrt(m_old / m_new))
            if pos:      # a drag: the group (or the atom) moved as a whole, its centre to the new place (LB1, P16.2)
                self._move_group(obj, pos)
            if vel:      # a throw: the group's centre-of-mass velocity (an atom's velocity)
                self._throw_group(obj, vel)
        elif k == "wall":
            if (old["axis"], old["side"]) != (v["axis"], v["side"]):
                self._wall(old, reset=True)
                if old["axis"] != v["axis"]:
                    self._release_axis(oid, "xyz".index(old["axis"]))
                    self._make_walled("xyz".index(v["axis"]), oid)
            self._wall(v)
        elif k == "piston":
            if old["axis"] != v["axis"]:
                md.remove_piston()
                self._release_axis(oid, "xyz".index(old["axis"]))
                self._make_walled("xyz".index(v["axis"]), oid)
                self._check_piston(v)
                self._piston(v)
            else:
                if old.get("position") != v["position"]:
                    self._check_piston(v)
                self._piston(v, old)
        elif k == "thermostat":
            self._region_inside(v)
            if old["kind"] != v["kind"]:
                md.remove_thermostat(self.parts[oid])
                self.parts[oid] = md.add_thermostat(v["kind"], float(v["T"]) / KELVIN, region=self._region_of(v),
                                                    **self._bath_args(v))
            else:
                md.set_thermostat(self.parts[oid], T=float(v["T"]) / KELVIN, region=self._region_of(v),
                                  **self._bath_args(v))
        elif k == "gravity":
            md.set_gravity(self._gvec(v))
        elif k == "probe":
            self._point_inside(v)

    def _atom_keys(self, oid):
        if self.kind.get(oid) == "molecules":
            if not hasattr(self, "_kcache"):
                self._kcache = {}
            got = self._kcache.get(oid)
            if got is None:
                mol = self.md.molecules()
                ks = [mol[int(mk)] for mk in self.parts[oid] if int(mk) in mol]
                got = np.sort(np.concatenate(ks)) if ks else np.zeros(0, np.int64)
                self._kcache[oid] = got
            return got
        return np.asarray(self.parts.get(oid, []), np.int64)

    # --- direct manipulation (LB1, P16.2): a group moved or thrown as a whole -----------------------------------
    def _centre(self, X):
        """The centre of a group of positions (reduced): the mean along a walled axis; along a periodic axis the
        circular mean (the angle of the mean of exp(2 pi i x / L)), or the middle of the box when the group spreads
        over the whole axis (the mean vector shorter than 0.15: no centre to speak of)."""
        c = np.zeros(self.ndim)
        for a in range(self.ndim):
            if self.md.periodic[a]:
                L = self.box[a]
                th = 2.0 * math.pi * X[:, a] / L
                C, S = float(np.mean(np.cos(th))), float(np.mean(np.sin(th)))
                c[a] = (math.atan2(S, C) / (2.0 * math.pi) * L) % L if math.hypot(C, S) > 0.15 else 0.5 * L
            else:
                c[a] = float(np.mean(X[:, a]))
        return c

    def _group(self, oid):
        """The keys, positions (wrapped) and velocities of an object's atoms (reduced)."""
        keys = self._atom_keys(oid)
        if not len(keys):
            return keys, np.zeros((0, self.ndim)), np.zeros((0, self.ndim))
        p = self.md.particles(keys)
        X = np.asarray(p["x"], float)
        for a in np.flatnonzero(self.md.periodic):
            X[:, a] -= self.box[a] * np.floor(X[:, a] / self.box[a])
        return keys, X, np.asarray(p["v"], float)

    def _move_group(self, obj, axes):
        """Translate an object's atoms so that their centre is at the object's x, y, z along ``axes`` (the others
        stay): refused with the reason where an atom would leave the walls (with the shift that fits) or come nearer
        than σ to an atom of another object; the engine checks the energies too. Cheap: one engine edit."""
        oid, v = obj["id"], obj["values"]
        keys, X, _ = self._group(oid)
        if not len(keys):
            return
        c = self._centre(X)
        d = np.zeros(self.ndim)
        for a in axes:
            d[a] = self._len(v[POS_KEYS[a]]) - c[a]
        if not np.any(d):
            return
        new = X + d
        sig = float(self._sigma_of(self.species[oid]))
        lo, hi = self._allowed(0.0)       # the walls act on the centres in both dynamics (review LB1-physics P4)
        for a in range(self.ndim):
            if self.md.periodic[a]:
                new[:, a] -= self.box[a] * np.floor(new[:, a] / self.box[a])
            elif np.any(new[:, a] < lo[a]) or np.any(new[:, a] > hi[a]):
                dmin, dmax = lo[a] - float(np.min(X[:, a])), hi[a] - float(np.max(X[:, a]))
                who = "атом оказался бы" if len(keys) == 1 else "атомы оказались бы"
                raise refusal(f"«{obj['label']}»: {who} за стенкой по оси {'xyz'[a]}",
                              hint=f"центр по {'xyz'[a]} от {_num((c[a] + dmin) * NM, 4)} до "
                                   f"{_num((c[a] + dmax) * NM, 4)} нм")
        Xall, Sall = self._xs()
        allk = np.asarray(self.md.particles()["keys"])
        others = ~np.isin(allk, keys)
        if np.any(others):
            free = free_sites(new, sig, Xall[others], Sall[others], np.array(self.box), self.md.periodic)
            bad = int(np.sum(~free))
            if bad:
                hint = "сдвиньте в свободное место"
                if obj["type"] == "atom":
                    spot = self._free_spot(sig, new[0], refuse=False)
                    if spot is not None:
                        hint = "ближайшее свободное место — (" + ", ".join(_num(z * NM, 4) for z in spot) + ") нм"
                raise refusal(f"«{obj['label']}»: {bad} {'атом лёг' if bad == 1 else 'атомов легли'} бы ближе σ к атомам "
                              f"других объектов (перекрылись бы)", hint=hint)
        self.md.set(keys, x=new)

    def _throw_group(self, obj, axes):
        """Give an object's atoms the centre-of-mass velocity vx, vy, vz along ``axes`` (one species: equal masses);
        their motion about the centre stays."""
        oid, v = obj["id"], obj["values"]
        keys, _, V = self._group(oid)
        if not len(keys):
            return
        vc = V.mean(axis=0)
        new = V.copy()
        for a in axes:
            new[:, a] += float(v[VEL_KEYS[a]]) / U.velocity_m_s - vc[a]
        self.md.set(keys, v=new)

    def object_state(self, obj):
        # the atoms' positions and velocities are not kept in a scene file: an object starts again from its values (a
        # carry-over into a new world takes them: ``carry_state``)
        return None

    # --- the scene carried into a new world (review LB1-framework F5; the framework's hooks of 2026-11-11) -----------
    def carry_state(self):
        """What a new world takes over: per particle object its atoms' positions and velocities (molecules: per
        molecule, unwrapped, in the molecule's atom order), a crystal's lattice note; the piston's face and velocity;
        the world's box, space and random generators. Plain data and NumPy arrays; never changes the world."""
        md, nd = self.md, self.ndim
        L = np.asarray(md.L, float).copy()
        objs = {}
        for oid, k in self.kind.items():
            if k in ("particles", "molecules"):
                ak = self._atom_keys(oid)
                q = md.particles(ak) if len(ak) else {"x": np.zeros((0, nd)), "v": np.zeros((0, nd))}
                st = {"dim": nd, "box": L, "x": np.asarray(q["x"], float), "v": np.asarray(q["v"], float)}
                if k == "molecules" and len(ak):
                    mol = md.molecules()
                    groups = [np.sort(mol[int(mk)]) for mk in self.parts[oid] if int(mk) in mol]
                    keys = np.concatenate(groups)
                    pq = md.particles(keys)
                    na = len(groups[0])
                    st["xm"] = np.asarray(pq["x_unwrapped"], float).reshape(-1, na, nd)
                    st["vm"] = np.asarray(pq["v"], float).reshape(-1, na, nd)
                if self.info.get(oid):
                    st["info"] = {kk: (float(vv) if isinstance(vv, (float, np.floating)) else int(vv))
                                  for kk, vv in self.info[oid].items() if isinstance(vv, (int, float, np.number))}
                objs[oid] = st
            elif k == "piston" and not self.hard and md.piston() is not None:
                p = md.piston()
                objs[oid] = {"dim": nd, "box": L, "X": float(p["X"]), "V": float(p["V"])}
        def rng(g):   # PCG64's 128-bit integers as decimal text (plain JSON everywhere)
            st = g.bit_generator.state
            return {"state": str(st["state"]["state"]), "inc": str(st["state"]["inc"]),
                    "has_uint32": int(st["has_uint32"]), "uinteger": int(st["uinteger"])}
        world = {"dim": nd, "box": L, "rng_md": rng(md.rng), "rng": rng(self.rng),
                 "ramp": bool(not self.hard and getattr(md, "ramp_running", lambda: False)())}
        return {"objects": objs, "world": world}

    def _carry_note(self, text, obj=None, restarted=False):
        note = getattr(self, "carry_note", None)
        if note is not None:
            note(text, obj, restarted=restarted)

    def _carry_mismatch(self, st):
        """Why a carried state cannot go into this world as it is (None: it can)."""
        if int(st.get("dim", 0)) != self.ndim:
            return "другая размерность (плоскость ↔ объём): положения атомов в ней не продолжить"
        return None

    def _add_carried(self, obj, st):
        """An object with its carried state: the same atoms at the same places with the same velocities (a box of
        another size: as they were, where they fit; refused - then started from the parameters - where an atom would
        be outside a wall or on another one)."""
        t, v, oid, md = obj["type"], obj["values"], obj["id"], self.md
        L_old = np.asarray(st["box"], float)
        other_box = L_old.shape != np.asarray(md.L).shape or not np.allclose(L_old, md.L, rtol=1e-12, atol=0.0)
        if t == "piston":
            v["position"] = round(float(st["X"]) * NM, 9)
            self._piston_pos = None
            self._add_obj(obj)
            p = md.piston()
            md.set_piston(p["axis"], X=float(st["X"]), V=float(st["V"]), mass=p["M"], p_ext=p["p_ext"],
                          x_min=p["x_min"])
            self._carry_note("поршень перенесён на своё место со своей скоростью", obj)
            return
        sp = self._species(obj)
        if t == "molecule":
            if self.hard:
                raise refusal("у твёрдых шаров нет молекул")
            na = int(np.asarray(st["xm"]).shape[1])
            b0, kb = float(v["bond"]), float(v["k_bond"])
            md.set_bond_type(f"{oid}-b", IA.HarmonicBond(kb, b0))
            if na >= 3:
                md.set_angle_type(f"{oid}-a", IA.HarmonicAngle(float(v.get("k_angle", 0.0)),
                                                               math.radians(float(v.get("angle", 180.0)))))
            bonds = [(i, i + 1, f"{oid}-b") for i in range(na - 1)]
            angles = [(i, i + 1, i + 2, f"{oid}-a") for i in range(na - 2)]
            X = np.array(st["xm"], float)
            moved, most = 0, 0.0
            for a in np.flatnonzero(~np.asarray(md.periodic)):
                # a walled axis here: each molecule whole, by its centre, in the box; one that crossed a periodic face
                # of the old world (now a wall) is moved inside as a whole, by the least shift (said)
                La = float(md.L[a])
                X[:, :, a] -= La * np.floor(X[:, :, a].mean(axis=1) / La)[:, None]
                lo, hi = X[:, :, a].min(axis=1), X[:, :, a].max(axis=1)
                sh = np.where(lo < 0.0, -lo, np.where(hi > La, La - hi, 0.0))
                X[:, :, a] += sh[:, None]
                moved += int(np.count_nonzero(sh))
                most = max(most, float(np.max(np.abs(sh))) if len(sh) else 0.0)
            _, mks, _ = md.add_molecules(sp, X, bonds=bonds, angles=angles, v=np.asarray(st["vm"], float),
                                         keep_all=True)
            if moved:
                self._carry_note(f"{moved} молекул пересекали грань, ставшую стенкой: сдвинуты внутрь целиком (не "
                                 f"больше чем на {_num(most * NM, 3)} нм)", obj)
            self.parts[oid] = np.asarray(mks)
            self.kind[oid] = "molecules"
        else:
            x, vel = np.asarray(st["x"], float), np.asarray(st["v"], float)
            self.parts[oid] = np.asarray(md.add(sp, x, v=vel) if len(x) else np.zeros(0, np.int64))
            self.kind[oid] = "particles"
        if st.get("info"):
            self.info[oid] = dict(st["info"])
        self._kcache.pop(oid, None)
        if other_box:
            self._carry_note(f"ящик другой ({self._size([q * NM for q in L_old])} → {self._size([q * NM for q in md.L])}): "
                             f"атомы оставлены на своих местах", obj)

    def carry_world(self, state, laws):
        """The world's own state from the previous world: its random generators (the thermostats', the thermal walls'
        and the hard spheres' draws continue the same sequence); the first law's balance, the momentum's reference and
        the mean-square displacement count from the new world's start (a world with other laws has another energy
        function); a change of the box still running there is not continued (the new world's box is its target)."""
        if state is None:
            raise refusal("прежний мир не передал своего состояния: случайная последовательность начата заново")
        for g, key in ((self.md.rng, "rng_md"), (self.rng, "rng")):
            d = state[key]
            g.bit_generator.state = {"bit_generator": "PCG64", "state": {"state": int(d["state"]), "inc": int(d["inc"])},
                                     "has_uint32": int(d["has_uint32"]), "uinteger": int(d["uinteger"])}
        self._carry_note("случайная последовательность (термостаты, тепловые стенки, твёрдые шары) продолжена из "
                         "прежнего мира; баланс первого начала, импульс и средний квадрат смещения отсчитываются с начала "
                         "нового мира")
        if state.get("ramp"):
            self._carry_note(f"изменение ящика, шедшее в прежнем мире, не продолжено: ящик нового мира сразу "
                             f"{self._size([q * NM for q in self.md.L])}")
        self._after_change()

    # --- live laws (review UX-ui U12) ------------------------------------------------------------------------------
    def live_values(self):
        return dict(self.live)

    def set_live(self, values):
        """The live laws at the current moment (review UX-ui U12; LB1, P16.1: a bench that never restarts), all or
        nothing (a refusal puts the world back bit for bit):

        * the pair model, its cutoff and shift (``MD.set_pair``) and the time step (``MD.set_dt``): the same atoms,
          positions and velocities; the potential energy changes by the difference of the models (the first-law
          balance moves E0 by it) and the conservation references restart; a time step the hottest atoms cannot
          resolve is refused. In the hard world they are kept for the forces (they act after a switch);
        * the dynamics: continuous forces ↔ hard spheres (``core.md.hard.hard_from_md``, ``md_from_hard``): the same
          atoms with their positions and velocities; to hard spheres only without what they have not (named) and
          with no pair inside contact; back always, the potential energy appearing (stated);
        * the box, Lx, Ly, Lz (``MD.deform``): affine (the box with the matter, its work booked in the first law) or a
          wall moved over empty space (``box_mode``)."""
        new, errors = SCHEMA.coerce_live(self.live, values or {})
        if errors:
            raise refusal("; ".join(errors))
        changed = {k: v for k, v in new.items() if self.live.get(k) != v}
        if not changed:
            return ""
        if self.ndim == 2 and "Lz" in changed:
            raise refusal("в плоскости нет оси z: размер ящика по z здесь не действует", hint="меняйте Lx и Ly")
        snap = self._snapshot()
        parts = []
        laws = {"model", "cutoff", "shift", "dt_fs"} & set(changed)
        box = [k for k in BOX_KEYS if k in changed]
        try:
            self.live = dict(new)
            if "dynamics" in changed:
                parts.append(self._switch_to_hard() if new["dynamics"] == "hard" else self._switch_to_soft())
            elif laws and self.hard:
                parts.append("законы сил запомнены: " + ", ".join(
                    f"{SCHEMA.by_id[k].label} = {_val(k, changed[k])}" for k in sorted(laws))
                    + " — действуют после перехода к непрерывным силам")
            elif laws:
                E0 = self.md.energy()
                self.model = self.live["model"]
                if {"model", "cutoff", "shift"} & laws:
                    self.md.set_pair(self._pair_term())
                if "dt_fs" in laws:
                    dt = float(self.live["dt_fs"]) * 1e-3 / PS
                    self._check_dt(dt)
                    self.md.set_dt(dt)
                dE = self.md.energy() - E0
                de = U.to_kJ_mol(dE / max(self.md.n, 1))
                labels = ", ".join(f"{SCHEMA.by_id[k].label} = {_val(k, changed[k])}" for k in sorted(laws))
                parts.append(f"законы на ходу: {labels}" + (
                    f"; энергия изменилась на {'+' if de >= 0 else '−'}{_num(abs(de), 4)} кДж/моль на атом (разность "
                    f"потенциалов; учтена в балансе)" if abs(dE) > 0 else ""))
            self.model = "hard" if self.hard else self.live["model"]
            if "dynamics" in changed or (laws and not self.hard):
                self._after_change()
            if box:
                parts.append(self._set_box())
            elif "box_mode" in changed:
                parts.append("размер ящика дальше меняется " + (
                    "аффинно (вещество вместе с ящиком)" if new["box_mode"] == "affine"
                    else "сдвигом верхней стенки по пустому месту"))
            if "dynamics" in changed or laws:
                parts.append("отсчёты проверок — с этого момента")
        except BaseException as e:
            self._restore(snap)
            if isinstance(e, Exception) and not _is_russian(e):
                raise _ru(e, self) from e
            raise
        self.emit({"type": "approximations", "t": self.t, "approximations": self._approx()})
        if "dynamics" in changed:
            self._stale_checks()
        return "; ".join(q for q in parts if q)

    def _sub_seed(self):
        """A seed for a solver built at the current moment (the switch of the dynamics), from the world's generator:
        deterministic, as a restore repeats it."""
        return int(self.rng.integers(0, 2 ** 62))

    def _switch_to_hard(self):
        from lfphys.core.md import hard as HD
        bodies = "дисков" if self.ndim == 2 else "шаров"
        block = []
        for o in self.objects.values():
            t, v, lab = o["type"], o["values"], f"«{o['label']}»"
            what = {"molecule": "молекулы", "piston": "поршень", "thermostat": "термостат", "gravity": "поле"}.get(t)
            if t == "wall" and v.get("kind") == "soft":
                what = "мягкая стенка"
            if t in ("gas", "crystal", "atom") and v.get("substance") == "custom" and float(v.get("charge", 0.0)):
                what = "заряд"
            if what:
                block.append(f"{what} {lab}")
        if block:
            raise refusal(f"у твёрдых {bodies} этого нет: {', '.join(block)}",
                          hint="уберите их (мягкую стенку сделайте зеркальной или тепловой), затем переключите "
                               "«Динамика»")
        p = self.md.particles()
        sig = np.array([self._sigma_of(q) for q in p["species"]], float)
        cv = HD.contact_violations(p["x"], sig, self.md.L, self.md.periodic, walls_on="centre")
        if cv["pairs"] or cv["walls"]:
            what = []
            if cv["pairs"]:
                what.append(f"{cv['pairs']} пар атомов ближе σ друг к другу (ближайшая — {_num(cv['closest'], 3)} σ)")
            if cv["walls"]:
                what.append(f"{cv['walls']} атомов за стенкой")
            raise refusal(f"твёрдые {'диски' if self.ndim == 2 else 'шары'} перекрылись бы: {'; '.join(what)}",
                          hint="уменьшите плотность (ящик больше — на ходу) или температуру (чем слабее удар, тем меньше "
                               "атомы заходят друг в друга), либо попробуйте в другой момент: такие пары возникают и "
                               "расходятся")
        n = max(self.md.n, 1)
        stopped = self._stop_ramp("другая динамика")
        Ep = self.md.energy() - self.md.kinetic_energy()
        self.md = HD.hard_from_md(self.md, seed=self._sub_seed(), walls_on="centre")
        self.hard = True
        self.model = "hard"
        de = U.to_kJ_mol(Ep / n)
        walls = ("; стенки действуют на центры атомов, как и при непрерывных силах: область центров и плотность не "
                 "изменились" if not all(self.md.periodic) else "")
        return stopped + (f"динамика: твёрдые {bodies} (событийно) — те же атомы, положения и скорости; потенциальная "
                          f"энергия ({'+' if de >= 0 else '−'}{_num(abs(de), 4)} кДж/моль на атом) исчезла: энергия "
                          f"теперь только кинетическая{walls}")

    def _switch_to_soft(self):
        from lfphys.core.md import hard as HD
        K = self.md.kinetic_energy()
        extra = {}
        for oid, k in self.kind.items():
            if k in ("particles", "molecules"):
                _, _, e, q = self._subst_values(self.objects[oid]["values"])
                extra[self.species[oid]] = {"epsilon": e, "charge": q}
        dt = float(self.live["dt_fs"]) * 1e-3 / PS
        self.md = HD.md_from_hard(self.md, self._pair_term(), dt, seed=self._sub_seed(), species_extra=extra)
        self.hard = False
        self.model = self.live["model"]
        self._check_dt(dt)
        n = max(self.md.n, 1)
        de = U.to_kJ_mol((self.md.energy() - K) / n)
        lab = _val("model", self.live["model"])
        return (f"динамика: непрерывные силы ({lab}) — те же атомы, положения и скорости; появилась потенциальная "
                f"энергия пар: скачок энергии {'+' if de >= 0 else '−'}{_num(abs(de), 4)} кДж/моль на атом")

    def _box3d(self, L=None):
        b = [x * NM for x in (self.box if L is None else L)] + [0.0] * (3 - self.ndim)
        if self.ndim == 2:
            b[2] = 0.05 * max(b[:2])
        return [[0.0, 0.0, -b[2] if self.ndim == 2 else 0.0], b]

    def _size(self, L_nm):
        return " × ".join(_num(x, 4) for x in L_nm) + " нм"

    def _set_box(self):
        """The box to the live Lx, Ly (, Lz) at the current moment: ``MD.deform`` (a jump: affine, or a wall over empty
        space) or ``MD.ramp_box`` (affine over «Время изменения размера»: a small affine step after every step of the
        integrator, the work of each booked; review LB1-physics P3) with its work in the first law; the hard world
        only by a wall. A change still running is stopped where the box is (its work stays). The view gets the new box
        (a ``box`` message: for a ramp the region it spans, then the final box at its end); the mean-square
        displacement and the hard world's pressure blocks restart; the first-law balance goes on (its W has the box's
        work). Refusals in the owner's terms, with the size that fits."""
        nd = self.ndim
        L_nm = [float(self.live[k]) for k in BOX_KEYS[:nd]]
        L = np.array(L_nm) / NM
        mode = self.live["box_mode"]
        tau_ps = float(self.live.get("box_time_ps", 0.0) or 0.0)
        bodies = "дисков" if nd == 2 else "шаров"
        if self.hard and mode == "affine":
            raise refusal(f"у твёрдых {bodies} аффинное сжатие скачком не совершает работы давления столкновений: даже "
                          f"медленное оно шло бы по адиабате идеального газа — это неверно",
                          hint="«Как менять размер ящика» = сдвинуть стенку (ось со стенками; на периодическую ось "
                               "сначала поставьте «Стенку»), или «Динамика» = непрерывные силы, ящик, и обратно")
        before = self._stop_ramp("задан новый размер")
        old_nm = [b * NM for b in self.box]
        if not self.hard and mode == "affine" and tau_ps > 0 and np.any(L != np.asarray(self.md.L)):
            return before + self._start_ramp(L, L_nm, old_nm, tau_ps)
        T0 = self._T_kelvin()
        try:
            o = self.md.deform(L, mode="wall") if self.hard else self.md.deform(
                L, mode=mode, max_bond_strain=MAX_BOND_STRAIN)
        except ValueError as e:
            raise self._box_refusal(e, L, mode) from e
        self.box = [float(b) for b in self.md.L]
        if not self.hard:
            self._check_dt(self.md.dt)        # a compression heats: the step must still resolve the collisions
        else:
            self.md.reset_counters()          # the collision pressure's sums belong to one box
        self.md.msd_origin()
        self._zb = {"blocks": [], "prev": None, "t_change": float(self.md.t)}
        self.emit({"type": "box", "t": self.t, "box": self._box3d()})
        size = self._size(old_nm) + " → " + self._size(L_nm)
        if mode == "wall" or self.hard:
            W = float(o.get("dE", 0.0))
            if W != 0.0:      # a soft wall's energy under the atoms near it changed (review LB1-physics P8)
                Wk = U.to_kJ_mol(W)
                return before + (f"ящик {size}: сдвинута стенка (пустое место добавлено или убрано); мягкая стенка "
                                 f"сдвинулась под атомами у неё — работа над системой W = {'+' if Wk >= 0 else '−'}"
                                 f"{_num(abs(Wk), 4)} кДж/моль (изменение энергии стенки), учтена в первом начале")
            return before + (f"ящик {size}: сдвинута стенка (пустое место добавлено или убрано), работы над системой "
                             f"нет (зеркальные и тепловые стенки по пустому месту); расширение в пустоту необратимо")
        n = max(self.md.n, 1)
        W = U.to_kJ_mol(o["dE"])
        T1 = self._T_kelvin()
        lam = max(abs(x - 1.0) for x in o["lambda"])
        txt = (f"ящик {size}, аффинно скачком (на {_num(100 * lam, 3)} %): работа над системой W = "
               f"{'+' if W >= 0 else '−'}{_num(abs(W), 4)} кДж/моль")
        if o.get("pdv") is not None:
            pdv = U.to_kJ_mol(o["pdv"])
            how = ("−P·ΔV по вириалу до и после" if o.get("virial_is_affine") else
                   "−∫S dV по аффинному напряжению до и после — с полем, мягкими стенками или замороженными атомами "
                   "это не давление вириала")
            txt += f" ({how}: {'+' if pdv >= 0 else '−'}{_num(abs(pdv), 4)})"
        txt += (f"; координаты ×L′/L, скорости относительно центра масс ×L/L′: кинетическая энергия "
                f"{'+' if o['dK'] >= 0 else '−'}{_num(abs(U.to_kJ_mol(o['dK'] / n)), 4)} кДж/моль на атом")
        if T0 is not None and T1 is not None:
            txt += f", температура {_num(T0, 4)} → {_num(T1, 4)} K"
        return before + txt + ("; работа учтена в первом начале. Скачок не квазистатичен: вещество после него "
                               "неравновесно и, расслабляясь, необратимо греется (медленно — «Время изменения размера» "
                               "больше 0)")

    def _start_ramp(self, L, L_nm, old_nm, tau_ps):
        """An affine change of the box over tau_ps (``MD.ramp_box``): refused where the end would pack the atoms beyond
        close packing at contact σ, or a step would change a length by more than the engine's limit (then a longer time
        or a jump), or as the jump would be (the piston's axis, the cutoff); the view gets the region the change spans."""
        nd = self.ndim
        X, S = self._xs()
        if len(X):
            vs = (math.pi / 4 * S ** 2) if nd == 2 else (math.pi / 6 * S ** 3)
            eta = float(np.sum(vs)) / float(np.prod(L))
            eta_max = (math.pi / (2 * math.sqrt(3.0))) if nd == 2 else (math.pi / (3 * math.sqrt(2.0)))
            if eta > eta_max:
                cap = (float(np.sum(vs)) / eta_max / float(np.prod(np.asarray(self.md.L)))) ** (1.0 / nd)
                raise refusal(f"атомы заняли бы {eta:.0%} {'площади' if nd == 2 else 'объёма'} — плотнее плотной упаковки "
                              f"шаров диаметром σ ({eta_max:.0%})",
                              hint=f"размеры не меньше ≈ {_num(cap * 100, 3)} % нынешних (сейчас "
                                   f"{self._size(old_nm)}), или уберите часть атомов")
        tau = tau_ps / PS
        try:
            r = self.md.ramp_box(L, tau)
        except ValueError as e:
            msg = str(e)
            import re
            m = re.search(r"changes a length by ([\d.e+-]+) per step \(limit ([\d.e+-]+)\)", msg)
            if m:
                need = tau_ps * float(m.group(1)) / float(m.group(2))
                raise refusal(f"за {_num(tau_ps, 3)} пс ящик менялся бы слишком быстро: {_num(100 * float(m.group(1)), 2)} % "
                              f"длины за шаг счёта (предел {_num(100 * float(m.group(2)), 2)} %)",
                              hint=f"«Время изменения размера» не меньше {_num(math.ceil(need * 100) / 100, 3)} пс, "
                                   f"или 0 — скачком", detail=msg) from e
            raise self._box_refusal(e, L, "affine") from e
        self._ramp_T0 = self._T_kelvin()
        self.emit({"type": "box", "t": self.t, "box": self._box3d(np.maximum(np.asarray(self.md.L), L))})
        dL = max(abs(a - b) for a, b in zip(L_nm, old_nm))
        v_face = dL * 1e-9 / (tau_ps * 1e-12)                 # m/s
        T = self._T_kelvin()
        ms = self._masses()
        m_mean = float(np.mean(ms[np.isfinite(ms)])) if len(ms) and np.any(np.isfinite(ms)) else 1.0
        txt = (f"ящик {self._size(old_nm)} → {self._size(L_nm)} аффинно за {_num(tau_ps, 3)} пс (до t = "
               f"{_num((self.t + tau_ps * 1e-12) * 1e12, 6)} пс): грани ящика движутся со скоростью до "
               f"{_num(v_face, 3)} м/с")
        if T is not None and T > 0:
            u = math.sqrt(nd * (T / KELVIN) / m_mean) * U.velocity_m_s
            txt += f" (тепловая скорость атомов ≈ {_num(u, 3)} м/с; квазистатически — когда грани много медленнее)"
        return txt + ("; размер меняется на каждом шаге счёта, работа каждого шага учтена в первом начале; конец — "
                      "событием с работой")

    def _stop_ramp(self, why):
        """Stop a change of the box still running (another box, the other dynamics): the text for the event."""
        if self.hard or not hasattr(self.md, "ramp_running") or not self.md.ramp_running():
            return ""
        self.md.stop_box_ramp(why)
        self.box = [float(b) for b in self.md.L]
        return self._ramp_text(self.md.box_ramp()) + "; "

    def _ramp_text(self, r):
        """What a change of the box over a time did (its end, or where it was stopped)."""
        self._ramp_seen = r["n"]
        L0 = [x * NM for x in r["L0"]]
        L1 = [x * NM for x in r["L"]]
        W = U.to_kJ_mol(r["W"])
        pdv = U.to_kJ_mol(r["pdv"])
        dur = (r["t_end"] - r["t0"]) * PS
        head = ("изменение ящика закончено" if r["done"] else "изменение ящика остановлено (" + {
            "задан новый размер": "задан новый размер",
            "другая динамика": "переход к твёрдым шарам",
            "шаг": "сжатие нагрело вещество: шаг по времени не разрешал бы удары",
            "cutoff": "радиус обрезки стал бы больше половины ящика",
        }.get(r["stopped"], "сила стала бы бесконечной" if str(r["stopped"]).startswith("refused") else
              str(r["stopped"])) + ")")
        txt = (f"{head}: {self._size(L0)} → {self._size(L1)} за {_num(dur, 4)} пс, {r['steps']} шагов; работа над "
               f"системой W = {'+' if W >= 0 else '−'}{_num(abs(W), 4)} кДж/моль (по шагам, точно; "
               f"−∫{'P' if r.get('virial_is_affine') else 'S'} dV по шагам — {'+' if pdv >= 0 else '−'}"
               f"{_num(abs(pdv), 4)}), учтена в первом начале")
        T0, T1 = getattr(self, "_ramp_T0", None), self._T_kelvin()
        if T0 is not None and T1 is not None:
            txt += f"; температура {_num(T0, 4)} → {_num(T1, 4)} K"
        return txt

    def _follow_ramp(self):
        """After an advance: the box the engine's ramp has reached (frames, measurables), the time step against the
        heating it brings (stopped where the step would not resolve the collisions), and its end announced once."""
        r = self.md.box_ramp()
        if r is None:
            return
        self.box = [float(b) for b in self.md.L]
        if r["running"]:
            try:
                self._check_dt(self.md.dt)
            except Exception:  # noqa: BLE001 - the heating outran the step: stop here, said in the event
                self.md.stop_box_ramp("шаг")
                r = self.md.box_ramp()
        if not r["running"] and r["n"] != getattr(self, "_ramp_seen", 0):
            self.emit({"type": "event", "kind": "action", "name": "box", "t": self.t, "text": self._ramp_text(r),
                       "notify": True})
            self.emit({"type": "box", "t": self.t, "box": self._box3d()})
            self.md.msd_origin()

    def _T_kelvin(self):
        T = self.md.temperature().get("T") if self.md.n else None
        return float(T) * KELVIN if T is not None and math.isfinite(T) else None

    def _box_refusal(self, e, L, mode):
        """A refused change of the box in the owner's terms, with what fits now."""
        msg = str(e)
        nd = self.ndim
        names = [k for k, a, b in zip(BOX_KEYS, L, self.box) if a != b]
        if "overlap" in msg or "non-finite" in msg or "same point" in msg:
            # the largest part of the way to the asked size that the engine takes (bisection on copies of the system)
            cls, st = type(self.md), self.md.state_dict()
            L0 = np.array(self.box)
            lo_t, hi_t = 0.0, 1.0
            for _ in range(10):
                mid = 0.5 * (lo_t + hi_t)
                try:
                    # with the same bond limit as the change itself (review LB1-physics P13)
                    cls.from_state_dict(st).deform(L0 + mid * (L - L0), mode=mode,
                                                   **({} if self.hard else {"max_bond_strain": MAX_BOND_STRAIN}))
                    lo_t = mid
                except ValueError:
                    hi_t = mid
            ok = (L0 + lo_t * (L - L0)) * NM
            fit = ", ".join(f"{k} ≈ {_num(ok[BOX_KEYS.index(k)], 4)} нм" for k in names)
            return refusal("при таком сжатии атомы перекрылись бы (энергия атома выше предела "
                           f"{_num(getattr(self.md, 'max_insert_energy', 50))} ε)",
                           hint=f"сейчас можно до {fit}; дальше — шагами, давая веществу разойтись", detail=msg)
        if "outside the walls" in msg or "particle outside" in msg:
            X = np.asarray(self.md.positions(), float)
            need = ", ".join(f"{k} не меньше {_num(float(np.max(X[:, BOX_KEYS.index(k)])) * NM * 1.0001, 4)} нм"
                             for k in names if len(X))
            return refusal("за сдвинутой стенкой остались бы атомы: убрать можно только пустое место",
                           hint=(need or "размер больше") + ", или «аффинно»", detail=msg)
        return _ru(e, self)
    def _check_dt(self, dt):
        """A new time step must resolve the hottest motion present: the kinetic temperature of each species and the
        temperatures the baths and thermal walls impose (``_check_temperature``)."""
        for d in self.md.species():
            if not math.isfinite(d["mass"]):
                continue
            Tsp = self.md.temperature(species=d["name"]).get("T")
            if Tsp is not None and math.isfinite(Tsp) and Tsp > 0:
                obj = self.objects.get(d["name"])
                vals = {**(obj["values"] if obj else {}), "T": Tsp * KELVIN}
                self._check_temperature("gas", vals, dt=dt)
        for o in self.objects.values():
            if o["type"] in ("thermostat", "wall"):
                self._check_temperature(o["type"], o["values"], dt=dt)

    # --- time ----------------------------------------------------------------------------------------------------
    def advance(self, t_target):
        tr = t_target * 1e12 / PS  # reduced
        if tr > self.md.t:
            try:
                self.md.advance(tr)
            except FloatingPointError as e:   # review UX-params P4: the owner's words, not the engine's
                raise RuntimeError(f"шаг Верле не удался ({e}): атомы сблизились до одной точки или пролетели сквозь "
                                   f"стенку — шаг по времени велик для этих скоростей; уменьшите «Шаг по времени» (на "
                                   f"ходу) или температуру и удалите или измените последний объект") from e
        self.t = max(self.t, t_target)
        if not self.hard and getattr(self.md, "_ramp", None) is not None:
            self._follow_ramp()

    def max_step(self):
        """At most MAX_STEPS steps per advance call, fewer when the modelled cost of a step (``md_step_model``: the
        atoms and the pairs; deterministic) would make one call longer than FRAME_S: a large scene keeps the frames and
        the commands flowing (review UX-params P33). The result does not depend on the cut: the engine steps to the
        last step time before each target."""
        if self.hard:
            return MAX_STEPS * 0.01 * PS * 1e-12
        c = self.md.cost_estimate()
        per = OB.md_step_model(c["n"], c["pairs"], self.ndim)
        k = int(min(MAX_STEPS, max(1, FRAME_S / per)))
        return k * self.md.dt * PS * 1e-12

    # --- frames ----------------------------------------------------------------------------------------------------
    def _colors(self):
        out = {}
        for oid, k in self.kind.items():
            if k in ("particles", "molecules"):
                out[oid] = COLORS[int(self.objects[oid]["values"].get("color", 0) or 0) % len(COLORS)]
        return out

    # --- measurables (LB1, P16.3) ---------------------------------------------------------------------------------
    def measurables(self):
        """The quantities this world measures as time series (the frames' ``meas``): of the world (temperature,
        pressure, energy per atom, density, the first law's Q, W, E − E₀ and residual, the momentum, the order
        parameter, the mean-square displacement), of every thermometer (atoms, density, temperature in its ball), of
        the piston (position, the gas's mean force on it, speed), of every molecule object (its modes' temperatures)
        and of every particle object (its temperature). Russian labels, display units."""
        nd = self.ndim
        E, G1, G2 = "кДж/моль", "Вещество", "Первое начало (с последнего изменения сцены)"
        sq = "²" if nd == 2 else "³"
        out = [{"id": "T", "label": "Температура", "unit": "K", "of": None, "group": G1},
               {"id": "p", "label": "Давление (вириал; у твёрдых шаров — по столкновениям с изменения)",
                "unit": "бар" if nd == 3 else "мН/м", "of": None, "group": G1},
               {"id": "e", "label": "Энергия на атом", "unit": E, "of": None, "group": G1},
               {"id": "N", "label": "Число атомов", "unit": "шт.", "of": None, "group": G1},
               {"id": "rho", "label": "Плотность числа атомов", "unit": f"нм⁻{sq}", "of": None, "group": G1},
               {"id": "rho_red", "label": f"Плотность ρσ{sq} (σ аргона)", "unit": "безразм.", "of": None, "group": G1},
               {"id": "V", "label": "Объём ящика" if nd == 3 else "Площадь ящика", "unit": f"нм{sq}", "of": None,
                "group": G1},
               {"id": "Q", "label": "Теплота Q от ванн и тепловых стенок", "unit": E, "of": None, "group": G2},
               {"id": "W", "label": "Работа W над системой (поршень и изменения ящика)", "unit": E, "of": None,
                "group": G2},
               {"id": "dE", "label": "Изменение энергии E − E₀", "unit": E, "of": None, "group": G2},
               {"id": "resid", "label": "Остаток баланса E − E₀ − Q − W", "unit": E, "of": None, "group": G2},
               *[{"id": f"P{c}", "label": f"Импульс системы P{c}", "unit": "а.е.м.·м/с", "of": None,
                  "group": "Импульс"} for c in "xyz"[:nd]],
               {"id": "order", "label": "Порядок |⟨ψ6⟩| (раз в 1 пс)" if nd == 2 else "Порядок Q6 (раз в 1 пс)",
                "unit": "безразм.", "of": None, "group": "Строение"},
               {"id": "msd", "label": "Средний квадрат смещения (с последнего изменения)", "unit": "нм²", "of": None,
                "group": "Строение"}]
        for oid, o in self.objects.items():
            lab, t = o["label"], o["type"]
            if t == "probe":
                out += [{"id": f"{oid}.N", "label": f"«{lab}»: атомов в шаре", "unit": "шт.", "of": oid,
                         "group": "Термометры"},
                        {"id": f"{oid}.rho", "label": f"«{lab}»: плотность", "unit": f"нм⁻{sq}", "of": oid,
                         "group": "Термометры"},
                        {"id": f"{oid}.T", "label": f"«{lab}»: температура", "unit": "K", "of": oid,
                         "group": "Термометры"}]
            elif t == "piston":
                out += [{"id": f"{oid}.X", "label": f"«{lab}»: положение", "unit": "нм", "of": oid, "group": "Поршень"},
                        {"id": f"{oid}.F", "label": f"«{lab}»: сила газа (средняя с последнего изменения)",
                         "unit": "пН", "of": oid, "group": "Поршень"},
                        {"id": f"{oid}.V", "label": f"«{lab}»: скорость", "unit": "м/с", "of": oid,
                         "group": "Поршень"}]
            elif t == "molecule":
                for part, nm in (("tr", "поступательная"), ("rot", "вращательная"), ("vib", "колебательная (кин.)"),
                                 ("bond", "связей (пот.)"), ("ang", "углов (пот.)")):
                    out.append({"id": f"{oid}.T_{part}", "label": f"«{lab}»: температура мод — {nm}", "unit": "K",
                                "of": oid, "group": "Молекулы"})
            if t in ("gas", "crystal", "atom", "molecule"):
                out.append({"id": f"{oid}.Tobj", "label": f"«{lab}»: температура атомов", "unit": "K", "of": oid,
                            "group": "Объекты"})
        return out

    def measure(self):
        """The current values of the measurables (``meas``), everything computed now (sweeps)."""
        return self._readings(full=True)["meas"]

    def _readings(self, full):
        """What a frame shows of the objects (``now``, the probes) and the measurables' values with the notes for the
        undefined ones, and every positioned object's place (``at``, nm; groups: their centre). ``full``: the order
        parameter too (else it is computed with the statistics, every STATS_EVERY frames)."""
        md, nd = self.md, self.ndim
        p = md.particles()
        X = np.asarray(p["x"], float)
        keys_all = np.asarray(p["keys"])
        n = len(X)
        nan = float("nan")
        meas, notes, at, now, probes, ids = {}, {}, {}, {}, {}, []

        def put(mid, val, why=""):
            ok = val is not None and math.isfinite(float(val))
            meas[mid] = float(val) if ok else nan
            if not ok and why:
                notes[mid] = why

        def nm3(c):
            c = [float(z) * NM for z in c]
            return c + [0.0] * (3 - nd)

        Tsys = md.temperature().get("T") if n else None
        put("T", Tsys * KELVIN if Tsys is not None else None, "нет атомов")
        P = md.pressure() if n else {}
        pv = P.get("virial") if not self.hard else P.get("pressure")
        put("p", (U.to_bar(pv) if nd == 3 else pv * U.pressure_Pa(2) * 1e3) if pv is not None else None,
            "нет атомов" if not n else ("у твёрдых шаров — после первых столкновений с изменения" if self.hard
                                        else "вириал не определён (замороженные атомы)"))
        Etot = md.energy() if not self.hard else md.kinetic_energy()
        put("e", U.to_kJ_mol(Etot / n) if n else None, "нет атомов")
        meas["N"] = float(n)
        V = float(md.volume())
        put("V", V * NM ** nd)
        put("rho", n / (V * NM ** nd))
        put("rho_red", n / V)
        b = md.energy_balance()
        for mid, k in (("Q", "Q"), ("W", "W"), ("dE", "dE"), ("resid", "residual")):
            val = b.get(k, 0.0 if k == "W" else None)
            put(mid, U.to_kJ_mol(val) if val is not None else None)
        mom = md.momentum() if n else np.zeros(nd)
        for a, c in enumerate("xyz"[:nd]):
            put(f"P{c}", float(mom[a]) * U.to_amu(1.0) * U.velocity_m_s)
        try:
            put("msd", md.msd()["msd"] * NM * NM)
        except (RuntimeError, ValueError):
            put("msd", None, "нет отсчёта")
        if full:      # a sweep's reading: computed now, the frames' schedule untouched
            put("order", self._order_value(), "нет атомов")
        else:
            # by world time, not by frame count (a frame drawn again at the same moment shows the same): computed when a
            # new ORDER_EVERY_PS of world time begins, shown in that frame only
            b = math.floor(self.t * 1e12 / ORDER_EVERY_PS + 1e-9)
            if b != getattr(self, "_order_bucket", None):
                self._order_bucket = b
                self._order, self._order_t = self._order_value(), self.t
            if getattr(self, "_order_t", None) == self.t and getattr(self, "_order", None) is not None:
                put("order", self._order)
            else:
                put("order", None, f"считается раз в {_num(ORDER_EVERY_PS)} пс времени мира (дорого: как 1–3 шага)")
        names = np.asarray(p["species"], dtype=object)
        for oid, k in self.kind.items():
            o = self.objects.get(oid)
            if o is None:
                continue
            if k in ("particles", "molecules"):
                Tsp = md.temperature(species=self.species[oid])
                Tk = float(Tsp["T"]) * KELVIN if Tsp.get("T") is not None and math.isfinite(Tsp["T"]) else None
                d = {"атомов": int(np.count_nonzero(names == self.species[oid])), "температура, K": Tk}
                put(f"{oid}.Tobj", Tk, "нет атомов")
                inf = self.info.get(oid)
                if inf:
                    d[f"плотность решётки ρσ^{nd}"] = inf["density"]
                    d["деформация ячейки"] = inf["strain"]
                    if inf.get("skipped"):
                        d["узлов оставлено пустыми (заняты)"] = inf["skipped"]
                ak = self._atom_keys(oid)
                if len(ak):
                    rows = np.searchsorted(keys_all, ak)
                    c = self._centre(X[rows])
                    at[oid] = nm3(c)
                    d["центр, нм"] = ", ".join(_num(z, 4) for z in at[oid][:nd])
                if k == "molecules":
                    mm = md.molecule_modes(self.parts[oid]) if not self.hard else None
                    for part, key, lab in (("translation", "tr", "поступат."), ("rotation", "rot", "вращат."),
                                           ("vibration", "vib", "колебат. (кин.)"), ("bonds", "bond", "связи (пот.)"),
                                           ("angles", "ang", "углы (пот.)")):
                        Tm = mm[part]["T"] * KELVIN if mm and mm[part]["T"] is not None else None
                        put(f"{oid}.T_{key}", Tm, "нет таких мод")
                        if Tm is not None:
                            d[f"T {lab}, K"] = Tm
                now[oid] = d
            elif k == "piston":
                pist = md.piston()
                if pist is not None:
                    a = "xyz".index(pist["axis"]) if isinstance(pist["axis"], str) else int(pist["axis"])
                    c = [0.5 * L for L in self.box]
                    c[a] = pist["X"]
                    at[oid] = nm3(c)
                    put(f"{oid}.X", pist["X"] * NM)
                    dt = md.t - pist["t0"]
                    put(f"{oid}.F", pist["impulse"] / dt * U.force_N * 1e12 if dt > 0 else None,
                        "измеряется со следующего шага")
                    put(f"{oid}.V", pist["V"] * U.velocity_m_s if math.isfinite(pist["V"]) else None)
            elif k == "thermostat":
                reg = self._region_of(o["values"])
                if reg is not None:
                    at[oid] = nm3([0.5 * (lo + hi) for lo, hi in zip(*reg)])
        for oid, o in self.objects.items():
            if o["type"] == "probe":
                v = o["values"]
                c = [self._len(v[cc]) for cc in "xyz"[:nd]]
                at[oid] = nm3(c)
                try:
                    pr = md.probe(c, self._len(v["r"]))
                except ValueError:
                    pr = {"n": None, "density": None, "T": None}
                probes[oid] = {"температура, K": pr["T"] * KELVIN if pr["T"] is not None else None,
                               "атомов": pr["n"], f"плотность ρσ^{nd}": pr["density"]}
                ids.append(oid)
                why = "шар вне ящика или радиус больше половины периодического ящика"
                put(f"{oid}.N", pr["n"], why)
                put(f"{oid}.rho", pr["density"] / NM ** nd if pr["density"] is not None else None, why)
                put(f"{oid}.T", pr["T"] * KELVIN if pr["T"] is not None else None,
                    "в шаре нет атомов" if pr["n"] == 0 else why)
        return {"meas": meas, "notes": notes, "at": at, "now": now, "probes": probes, "ids": ids, "p": p, "X": X}

    def _order_value(self):
        """The bond-orientational order (|⟨ψ6⟩| in a plane, Q6 in a volume) of all atoms now (None without atoms)."""
        md = self.md
        if md.n == 0:
            return None
        X = np.asarray(md.positions())
        sig = np.array([self._sigma_of(q) for q in md.particles()["species"]])
        bo = OB.bond_order(X, self.box, [bool(b) for b in md.periodic], ORDER_RCUT * float(np.mean(sig)))
        return bo.get("psi6_global") if self.ndim == 2 else bo.get("Q6")

    def frame(self):
        md = self.md
        R = self._readings(full=False)
        p, X = R["p"], R["X"]
        n = len(X)
        # the particles: positions quantized to 16 bits over the box (drawing only), the species index of each
        span = np.array(self.box)
        q = np.clip(np.round(X / span * 65535), 0, 65535).astype(np.uint16) if n else \
            np.zeros((0, self.ndim), np.uint16)
        sp_names = list(self.species.values())
        spec = np.array([sp_names.index(s) if s in sp_names else 0 for s in p["species"]], np.uint8)
        now, probes, ids = R["now"], R["probes"], R["ids"]
        if self.check_due():
            self.checks()
        if self.n_stats % STATS_EVERY == 0:
            self.emit_stats()
        self.n_stats += 1
        pist = md.piston() if self.model != "hard" else None
        bonds = None
        if self.model != "hard" and any(k == "molecules" for k in self.kind.values()):
            topo = md.topology()
            bonds = np.array([[a, b] for a, b, *_ in topo.get("bonds", [])], np.int32).reshape(-1)
        meta = {"ids": ids, "now": now, "probes": probes, "n": n, "box_nm": [b * NM for b in self.box],
                "at": R["at"], "meas": R["meas"], "meas_note": R["notes"],   # always present: a frame's keys never vary
                "species_colors": [self._colors().get(s, COLORS[0]) for s in sp_names],
                "species_radius_nm": [0.5 * NM * self._sigma_of(s) for s in sp_names],
                "piston_nm": (pist["X"] * NM if pist else None),
                "walled": [a for a in range(self.ndim) if not md.periodic[a]],
                "piston_axis": ("xyz".index(pist["axis"]) if pist and isinstance(pist.get("axis"), str)
                                else int(pist["axis"]) if pist and pist.get("axis") is not None else 1)}
        blobs = {"q": q.reshape(-1), "sp": spec}
        if bonds is not None:
            keys = list(p["keys"])
            index = {int(k): i for i, k in enumerate(keys)}
            blobs["bonds"] = np.array([index[int(k)] for k in bonds], np.int32)
        return meta, blobs

    def _sigma_of(self, sp):
        d = self._sp(sp)
        return float(d.get("sigma", 1.0)) if d else 1.0

    def _masses(self):
        ms = {d["name"]: d["mass"] for d in self.md.species()}
        return np.array([ms[s] for s in self.md.particles()["species"]], float)

    def emit_stats(self):
        """Statistics for the charts (accumulative: every message is a point of the time series, the latest also the
        distributions)."""
        md = self.md
        if md.n == 0:
            return
        T = md.temperature()
        Tk = float(T["T"]) * KELVIN if T.get("T") is not None and math.isfinite(T["T"]) else None
        P = md.pressure()
        # MD: the instantaneous virial pressure; hard spheres: the collision virial since the last change
        p_val = P.get("virial") if self.model != "hard" else P.get("pressure")
        p_phys = (U.to_bar(p_val) if self.ndim == 3 else p_val * U.pressure_Pa(2) * 1e3) if p_val is not None \
            else None
        e = (md.energy() / md.n) if self.model != "hard" else md.kinetic_energy() / md.n
        # the velocity components scaled by sqrt(kT/m) of each particle's own mass: one standard Gaussian
        # (Maxwell-Boltzmann); T of the sample, as in the KS check
        V = np.asarray(md.velocities())
        m = self._masses()
        mob = np.isfinite(m)
        hist = None
        if np.any(mob):
            Ts = float(np.sum(m[mob, None] * V[mob] ** 2)) / V[mob].size
            if Ts > 0:
                z = (V[mob] * np.sqrt(m[mob] / Ts)[:, None]).reshape(-1)
                hist, _ = np.histogram(z, bins=40, range=(-4.0, 4.0), density=True)
        ks = md.velocity_ks()
        r_max = min(0.5 * min(self.box), 5.0)
        r, g, _ = md.rdf(r_max, nbins=80)
        X = np.asarray(md.positions())
        # the density along y (the field's axis), in slabs of about one sigma
        Ly = self.box[1] if self.model == "hard" or md.piston() is None else md.piston()["X"]
        nb = int(min(max(round(Ly), 8), 100))
        cnt, _ = np.histogram(X[:, 1], bins=nb, range=(0.0, Ly))
        area = float(np.prod(np.delete(np.array(self.box), 1)))
        rho_y = cnt / (area * Ly / nb)
        order = self._order if getattr(self, "_order_t", None) == self.t else self._order_value()
        msd = md.msd()["msd"] * NM * NM
        modes = None
        if self.model != "hard" and any(k == "molecules" for k in self.kind.values()):
            mm = md.molecule_modes()
            if mm:
                modes = {part: (mm[part]["T"] * KELVIN if mm[part]["T"] is not None else None)
                         for part in ("translation", "rotation", "vibration", "bonds", "angles")}
        self.emit({"type": "stats", "t": self.t, "T_K": Tk, "p": p_phys, "p_unit": "бар" if self.ndim == 3 else "мН/м",
                   "p_kind": "вириал (мгновенный)" if self.model != "hard" else "по столкновениям (с изменения)",
                   "e_kJ_mol": U.to_kJ_mol(e), "ks": {k: ks.get(k) for k in ("D", "bound", "within", "n")},
                   "order": order, "order_kind": "|⟨ψ6⟩|" if self.ndim == 2 else "Q6", "msd_nm2": msd,
                   "modes": modes, "rho_y_nm": Ly * NM},
                  {"rdf_r": np.asarray(r, np.float32) * NM, "rdf_g": np.asarray(g, np.float32),
                   "rho_y": rho_y.astype(np.float32),
                   **({"vh": hist.astype(np.float32)} if hist is not None else {})})

    # --- checks ------------------------------------------------------------------------------------------------------
    def checks(self):
        md = self.md
        if md.n == 0:
            return
        if self.model != "hard":
            b = md.energy_balance()
            stiff = any(o["type"] in ("piston",) or (o["type"] == "wall") for o in self.objects.values()) or \
                not all(md.periodic)
            note = (f"E − E₀ = Q + W + остаток с последнего изменения сцены: теплота от ванн и стенок Q = "
                    f"{_num(U.to_kJ_mol(b['Q']), 4)}, работа W = {_num(U.to_kJ_mol(b['W']), 4)} кДж/моль (поршень "
                    f"{_num(U.to_kJ_mol(b.get('W_piston', b['W'])), 4)}, изменения ящика "
                    f"{_num(U.to_kJ_mol(b.get('W_box', 0.0)), 4)}; правки сцены сдвигают E₀ на изменённую ими энергию); "
                    f"остаток — ошибка схемы Верле: O(dt²) при непрерывных силах")
            if stiff:
                note += ("; удары о жёсткие стенки и поршень внутри шага при взаимодействующих атомах дают ошибку "
                         "порядка F·v·dt на удар, она копится с ударами — ошибка первого порядка по dt (пресет "
                         "поршня: остаток 1–14 ε за первый ход при 2,5–10 фс, не больше ~1,5 % работы; у идеального "
                         "газа баланс точен)")
            if not self._baths():
                try:
                    se = md.step_error(n_steps=10)
                    note += f"; оценка компаньона (dt против dt/2) за 10 шагов: {_num(U.to_kJ_mol(se['dE_estimate']), 3)}"
                except ValueError:
                    pass
            self.running_check("energy", "Энергия: первое начало (остаток баланса), кДж/моль",
                               U.to_kJ_mol(b["residual"]), 0.0, 0.0, info=True, group="Законы сохранения", note=note)
            dr = md.momentum_drift()
            if dr["ratio"] is not None:
                ax = ", ".join("xyz"[a] for a in range(self.ndim) if dr["axes"][a])
                self.running_check("momentum", f"Импульс системы вдоль {ax}: сохраняется (силы попарны)",
                                   dr["ratio"], 0.0, 1.0, group="Законы сохранения", ok=dr["ratio"] <= 1.0,
                                   note=(f"|P − P₀| / граница округления за {dr['steps']} шагов (P₀ — импульс при "
                                         f"последнем изменении сцены; граница — ε·шаги·(суммы |m v|, |F|): "
                                         f"engine momentum_drift); сохраняется вдоль периодических осей без поля, "
                                         f"тепловых стенок, ванн Ланжевена и местных ванн, замороженных атомов"))
        else:
            b = md.energy_balance()
            self.running_check("energy", "Энергия: первое начало (остаток баланса), кДж/моль",
                               U.to_kJ_mol(b["residual"]), 0.0, 0.0, info=True, group="Законы сохранения",
                               note=f"твёрдые шары: энергия только кинетическая, удары упругие — E − E₀ = Q (теплота "
                                    f"тепловых стенок {_num(U.to_kJ_mol(b['Q']), 4)} кДж/моль) с точностью до округления")
        ks = md.velocity_ks()
        if ks.get("D") is not None:
            self.running_check("maxwell", "Скорости против распределения Максвелла (расстояние КС)", ks["D"], None,
                               ks.get("bound") or 0.0, info=True, group="Статистика",
                               note=f"{'в пределах' if ks.get('within') else 'вне'} границы ДКВ {_num(ks.get('bound'), 3)} "
                                    f"при уровне 0,01 ({ks.get('n')} компонент скорости всех атомов, каждая делена "
                                    f"на √(kT/m) своей массы): в равновесии — в пределах")
        P = md.pressure()
        if self.model != "hard" and P.get("walls"):
            walls = ", ".join(f"{k}: {v:.4g}" for k, v in P["walls"].items() if v is not None)
            self.running_check("pressure", "Давление: вириал против стенок (приведённые единицы)",
                               P.get("virial"), None, 0.0, info=True, group="Статистика",
                               note=f"давление на стенки — переданный им импульс за время: {walls}"
                                    + ("; с замороженными атомами вириал определён только вдоль осей со стенками"
                                       if P.get("virial") is None else ""))
        if self.model == "hard":
            self._z_check()
        c = md.cost_estimate()
        if self.model == "hard":
            self.running_check("cost", "Счёт: секунд на событие (CPU, измерено)", c.get("s_per_event"), None, 0.0,
                               info=True, group="Расчёт", unit="с",
                               note=f"{c.get('n')} атомов, {c.get('events')} событий")
        else:
            self.running_check("cost", f"Счёт: секунд на шаг ({c.get('device', 'cpu').upper()}, оценка)",
                               c.get("per_step_s"), None, 0.0, info=True, group="Расчёт", unit="с",
                               note=f"{c.get('n')} атомов")

    def _stale_checks(self):
        """After a switch of the dynamics: the checks the other solver computed and this one does not are marked so
        (the panel keeps every check's latest version)."""
        if self.hard:
            gone = (("momentum", "Импульс системы: сохраняется (силы попарны)", "Законы сохранения"),
                    ("pressure", "Давление: вириал против стенок (приведённые единицы)", "Статистика"))
        else:
            gone = (("eos", "Фактор сжимаемости Z против уравнения состояния", "Статистика"),)
        what = "твёрдых шаров" if self.hard else "непрерывных сил"
        for cid, label, group in gone:
            self.running_check(cid, label, None, None, 0.0, info=True, group=group,
                               note=f"не считается при динамике {what} (переключена на ходу)")

    def _z_check(self):
        """Hard disks / spheres in a periodic box, one species: the compressibility factor Z of the run (mean of blocks
        of at least Z_BLOCK time units, from Z_EQUIL after the last change) against the equation of state of the
        fluid (Kolafa & Rottner 2006 / Kolafa, Labík & Malijevský 2004) with the ensemble correction for this N;
        pass/fail from Z_MIN_BLOCKS blocks with the tolerance 5 standard errors of the block mean + 1e-4 (review
        B7-md M5)."""
        from lfphys.core.md import hard as HD
        md, zb = self.md, self._zb
        a = md.accumulators()
        if a["t"] < zb["t_change"] + Z_EQUIL:
            zb["prev"] = None
            return
        if zb["prev"] is None:
            zb["prev"] = a
            return
        dt = a["t"] - zb["prev"]["t"]
        if dt >= Z_BLOCK:
            dK = a["Kdt"] - zb["prev"]["Kdt"]
            if dK > 0:
                Tb = 2.0 * dK / dt / a["dof"]
                zb["blocks"].append(1.0 + (a["W"] - zb["prev"]["W"]) / (self.ndim * a["n"] * Tb * dt))
            zb["prev"] = a
        names = {s for s in md.particles()["species"]}
        if not all(self.md.periodic) or len(names) != 1 or md.n < 2:
            return
        sig = self._sigma_of(next(iter(names)))
        rho = md.n * sig ** self.ndim / float(np.prod(self.box))
        z_inf = HD.z_reference(self.ndim, rho)
        if z_inf is None:
            return
        ref = z_inf - HD.ensemble_correction(self.ndim, rho, md.n)
        bl = np.array(zb["blocks"])
        src = "Колафа и Роттнер 2006 (диски)" if self.ndim == 2 else "Колафа, Лабик и Малиевски 2004 (шары)"
        if len(bl) < Z_MIN_BLOCKS:
            self.running_check("eos", "Фактор сжимаемости Z против уравнения состояния", None, ref, 0.0, info=True,
                               group="Статистика", note=f"набирается: {len(bl)} из {Z_MIN_BLOCKS} блоков по "
                                                        f"{_num(Z_BLOCK * PS, 2)} пс после {_num(Z_EQUIL * PS, 2)} пс с "
                                                        f"изменения сцены; эталон {ref:.5f} ({src})")
            return
        z = float(bl.mean())
        se = float(bl.std(ddof=1) / math.sqrt(len(bl)))
        tol = 5.0 * se + 1e-4
        self.running_check("eos", "Фактор сжимаемости Z против уравнения состояния", z, ref, tol,
                           group="Статистика", ok=abs(z - ref) <= tol,
                           note=(f"Z = 1 + Σ r·Δp / (d N T Δt) по столкновениям, среднее {len(bl)} блоков ± {_num(se, 2)}; "
                                 f"эталон: жидкость при ρσ^{self.ndim} = {rho:.4f} в пределе N → ∞ {z_inf:.5f} "
                                 f"({src}) минус поправка ансамбля для N = {md.n}: {ref:.5f}; допуск 5 стандартных "
                                 f"ошибок + 1e-4"))

    def _baths(self):
        return any(k == "thermostat" for k in self.kind.values()) or any(
            o["type"] == "wall" and o["values"]["kind"] == "thermal" for o in self.objects.values())

    # --- header --------------------------------------------------------------------------------------------------------
    def header(self):
        box = self._box3d()
        b = box[1]
        return {
            "title": "Плейграунд: частицы и молекулы",
            "text": ("Атомы и молекулы движутся по законам Ньютона с модельным межатомным взаимодействием; "
                     "температура, давление, теплота и работа, распределение скоростей и строение вещества "
                     "измеряются по ходу счёта."),
            "actions": [],
            "approximations": self._approx(),
            "scene3d": {"box": box, "units": "нм",
                        "up": [0, 1, 0] if self.ndim == 2 else [0, 0, 1], "objects": [], "layers": [],
                        "coord_names": ["x", "y", "z"],
                        "planes": {"max": 0, "center": [0.5 * x for x in b], "defaults": {"1": [0, 0, 1]}}},
            "md": {"ndim": self.ndim, "model": self.model, "box_nm": [x * NM for x in self.box],
                   "boundary": ["periodic" if b else "walls" for b in self.md.periodic],
                   "units": {"nm": NM, "ps": PS, "K": KELVIN}},
            "playground": self.playground_header(),
            "modifications": SCHEMA.modifications(self.params),
        }, {}

    def _approx(self):
        """The approximations of this world (review B7-md M16), with the numbers that set their limits."""
        a = [f"классическая механика атомов: у твёрдого аргона квантовые эффекты существенны ниже температуры Дебая "
             f"Θ_D = 85 K (теплоёмкость по Дебаю при 20 / 40 / 80 K — {debye_cv_fraction(20, 85):.2f} / "
             f"{debye_cv_fraction(40, 85):.2f} / {debye_cv_fraction(80, 85):.2f} классической)"]
        if self.model == "lj":
            rc, sh = float(self.live["cutoff"]), self.live["shift"]
            a.append(f"межатомное взаимодействие — модель Леннард-Джонса (12-6) с параметрами аргона, обрезанная на "
                     f"{_num(rc)} σ (сдвиг {'силы' if sh == 'force' else 'энергии'}): это другое вещество, чем аргон")
            tc = TC.get((self.ndim, rc, sh))
            full = TC[(self.ndim, "full")]
            if tc is not None:
                a.append(f"критическая температура этой модели {_num(tc)} ε/k = {tc * KELVIN:.0f} K (у полного 12-6 — "
                         f"{_num(full)} ε/k = {full * KELVIN:.0f} K, у аргона ≈ 150,7–150,9 K): выше неё жидкости и пара "
                         f"по отдельности нет")
            else:
                a.append(f"критическая температура зависит от обрезки и сдвига (у полного 12-6 в "
                         f"{'объёме' if self.ndim == 3 else 'плоскости'} — {_num(full)} ε/k = {full * KELVIN:.0f} K; "
                         f"{'со сдвигом силы на 2,5σ — 0,937 ε/k = 112 K' if self.ndim == 3 else 'обрезанного на 2,5σ со сдвигом энергии — 0,459 ε/k = 55 K, тройная точка около 0,42 ε/k'}); "
                         f"для этой обрезки значение не найдено")
        elif self.model == "wca":
            a.append("только отталкивание (WCA) — модель: без притяжения нет жидкости и пара")
        else:
            a.append("твёрдые диски / шары — модель (бесконечно жёсткое отталкивание, без притяжения: нет жидкости и "
                     "пара, только жидкость и кристалл)")
        if self.ndim == 2:
            a.append("плоскость: двумерное вещество (его фазы и уравнение состояния — двумерные)")
        mols = [o for o in self.objects.values() if o["type"] == "molecule"]
        for o in mols:
            v = o["values"]
            m = self._subst_values(v)[0]
            w = math.sqrt(float(v["k_bond"]) / (0.5 * m))                 # homonuclear bond: mu = m/2
            hw = w * HBAR_OVER_K / (PS * 1e-12)                            # ħω/k in K (ω in 1/τ)
            T = float(v["T"])
            frac = einstein_cv_fraction(T, hw) if T > 0 else 0.0
            a.append(f"«{o['label']}»: связи — гармонические пружины (не рвутся, без ангармонизма), ħω/k = {hw:.0f} K; "
                     f"при kT ≲ ħω колебания квантовые (теплоёмкость колебания при {_num(T)} K — {frac:.2f} "
                     f"классической), здесь — классические")
        return a

    def engine_modules(self):
        mods = ["lfphys.core.md.system", "lfphys.core.md.cells", "lfphys.core.md.observables", "lfphys.core.md.units",
                "lfphys.theories.models.interatomic"]
        return mods + (["lfphys.core.md.hard"] if self.model == "hard" else [])


VIZ = {
    "id": "p03_molecules",
    "title": "Частицы и молекулы",
    "summary": ("Песочница молекулярной динамики: газ, кристалл, молекулы, стенки, поршень, термостаты; "
                "температура, давление, теплота и работа, распределение Максвелла — по ходу счёта."),
    "purpose": ("Собрать вещество из атомов и посмотреть, как из законов Ньютона возникают тепловые свойства: "
                "распределение скоростей, давление, плавление, жидкость и пар, теплота и работа поршня."),
    "version": "0.2",
    "schema": SCHEMA,
    "simulation": Simulation,
    "kind": "playground",
    "section": "molecules",
}
