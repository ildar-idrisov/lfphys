# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""lfphys.core.optics.materials and its datasets in lfphys.core.data (EX2 design §3.9): the SCHOTT glasses against the
indices their data sheets print (to the printed 10⁻⁵), the printed constants and transmittances; the Sellmeier crystals
against a second transcription of their coefficients; every tabulated material at its nodes (exactly) and between
them within its stated interpolation error (against a second, Akima interpolant); κ ≥ 0; the derivatives against the
complex step and SciPy's PCHIP (tests only); the refusals; ``stack`` with a material; the registry entries; the
design's numbers. The sources and how each was checked: lfphys/sources/materials_2026-11-18.md."""

import cmath
import math
from decimal import Decimal

import numpy as np
import pytest
from scipy.interpolate import Akima1DInterpolator, PchipInterpolator
from scipy.optimize import minimize_scalar

from lfphys import registry
from lfphys.codes import code_of
from lfphys.core import data
from lfphys.core.optics import interfaces
from lfphys.core.optics import materials as M
from lfphys.i18n import is_t

# --- SCHOTT's data sheets, as printed (N-BK7: as of 01-Dec-2023; N-F2, N-SF11: as of 01-Feb-2014) ---------------
PRINTED = {  # (lambda nm, n) of every printed index
    "schott_n_bk7": [(2325.4, 1.48921), (1970.1, 1.49495), (1529.6, 1.50091), (1060.0, 1.50669), (1014.0, 1.50731),
                     (852.1, 1.50980), (706.5, 1.51289), (656.3, 1.51432), (643.8, 1.51472), (632.8, 1.51509),
                     (589.3, 1.51673), (587.6, 1.51680), (546.1, 1.51872), (486.1, 1.52238), (480.0, 1.52283),
                     (435.8, 1.52668), (404.7, 1.53024), (365.0, 1.53627), (334.1, 1.54272), (312.6, 1.54862)],
    "schott_n_f2": [(2325.4, 1.58136), (1970.1, 1.58744), (1529.6, 1.59410), (1060.0, 1.60167), (1014.0, 1.60261),
                    (852.1, 1.60667), (706.5, 1.61229), (656.3, 1.61506), (643.8, 1.61584), (632.8, 1.61658),
                    (589.3, 1.61990), (587.6, 1.62005), (546.1, 1.62408), (486.1, 1.63208), (480.0, 1.63310),
                    (435.8, 1.64209), (404.7, 1.65087)],
    "schott_n_sf11": [(2325.4, 1.72937), (1970.1, 1.73600), (1529.6, 1.74377), (1060.0, 1.75401), (1014.0, 1.75542),
                      (852.1, 1.76182), (706.5, 1.77119), (656.3, 1.77596), (643.8, 1.77732), (632.8, 1.77860),
                      (589.3, 1.78446), (587.6, 1.78472), (546.1, 1.79192), (486.1, 1.80651), (480.0, 1.80841),
                      (435.8, 1.82533), (404.7, 1.84235)],
}
PRINTED_CONSTANTS = {  # B1, B2, B3, C1, C2, C3 as the sheets print them
    "schott_n_bk7": ("1.039612120", "0.231792344", "1.010469450", "0.006000699", "0.0200179144", "103.56065300"),
    "schott_n_f2": ("1.397570370", "0.159201403", "1.268654300", "0.009959061", "0.0546931752", "119.24834600"),
    "schott_n_sf11": ("1.737596950", "0.313747346", "1.898781010", "0.013188707", "0.0623068142", "155.23629000"),
}
PRINTED_DISPERSION = {"schott_n_bk7": (0.008054, 64.17), "schott_n_f2": (0.017020, 36.43),
                      "schott_n_sf11": (0.030558, 25.68)}  # n_F - n_C and the Abbe number nu_d
# the sheets print the lines' wavelengths rounded to 0.1 nm; SCHOTT's TIE-29 (version August 2023), Tab. 1, gives the
# wavelengths the indices are computed at ("The wavelengths used in the equation have to be inserted in um with the
# same number of digits as listed in Table 1"): the lines' wavelengths in air (the indices are relative to air)
LINES = {2325.4: 2325.42, 1970.1: 1970.09, 1529.6: 1529.582, 1060.0: 1060.0, 1014.0: 1013.98, 852.1: 852.11,
         706.5: 706.5188, 656.3: 656.2725, 643.8: 643.8469, 632.8: 632.8, 589.3: 589.2938, 587.6: 587.5618,
         546.1: 546.074, 486.1: 486.1327, 480.0: 479.9914, 435.8: 435.8343, 404.7: 404.6561, 365.0: 365.0146,
         334.1: 334.1478, 312.6: 312.5663}
GLASSES = tuple(PRINTED)
TABLES = tuple(k for k, v in data.OPTICAL_MATERIALS.items() if v["form"] == "table")


def _half_unit(text):
    return 0.5 * 10.0 ** -len(text.partition(".")[2])


@pytest.mark.parametrize("glass", GLASSES)
def test_schott_glasses_reproduce_every_printed_index(glass):
    """Every index the data sheet prints within the formula's range, at the line's wavelength of TIE-29's Tab. 1, to its
    last digit (|n - printed| <= 0.5e-5); n_F - n_C and nu_d = (n_d - 1)/(n_F - n_C) as printed. The wavelengths are
    in air: shifted to vacuum (times n_air ~ 1.00027) the formula misses the printed indices by up to 7e-5."""
    lo, hi = M.info(glass)["range_nm"]
    rows = [(LINES[lam], n) for lam, n in PRINTED[glass] if lo <= LINES[lam] <= hi]
    assert len(rows) >= 17
    for lam, n in rows:
        assert abs(M.index(glass, lam).real - n) <= 0.5e-5 * (1 + 1e-9), (glass, lam)
    assert max(abs(M.index(glass, lam * 1.00027).real - n) for lam, n in rows) > 2.5e-5
    nF, nC, nd = (M.index(glass, LINES[lam]).real for lam in (486.1, 656.3, 587.6))
    dFC, nu = PRINTED_DISPERSION[glass]
    assert abs((nF - nC) - dFC) <= 0.5e-6 * (1 + 1e-9)
    assert abs((nd - 1) / (nF - nC) - nu) <= 0.005 * (1 + 1e-9)


@pytest.mark.parametrize("glass", GLASSES)
def test_schott_constants_are_the_printed_ones(glass):
    spec = data.OPTICAL_MATERIALS[glass]
    for ours, printed in zip(tuple(spec["B"]) + tuple(spec["C"]), PRINTED_CONSTANTS[glass]):
        assert abs(ours - float(printed)) <= _half_unit(printed) * (1 + 1e-12), (glass, ours, printed)


@pytest.mark.parametrize("glass", GLASSES)
def test_schott_kappa_from_the_printed_transmittance(glass):
    """kappa at the sheet's wavelengths is -lambda ln(tau_i)/(4 pi d) of the printed tau_i (strictly between 0 and 1)
    of the thickness, 25 or 10 mm, whose printed digits give kappa more precisely: half a unit of the last digit of
    tau_i over d tau_i (review EX2, R2-E F9; 25 mm at equal precision), reproduced exactly; between them kappa > 0. The
    node's stated precision covers the other thickness's kappa where both are printed."""
    spec = data.OPTICAL_MATERIALS[glass]
    nodes = 0
    for line in spec["tau"].strip().splitlines():
        lam, t10, t25 = line.split()
        ok = [(t, d) for t, d in ((t25, 25.0), (t10, 10.0)) if t != "-" and 0 < float(t) < 1]
        if not ok:
            continue
        t, dmm = min(ok, key=lambda c: _half_unit(c[0]) / (c[1] * float(c[0])))
        k = -float(lam) * 1e-9 * math.log(float(t)) / (4 * math.pi * dmm * 1e-3)
        assert M.index(glass, float(lam)).imag == k
        if len(ok) == 2:
            other = [c for c in ok if c != (t, dmm)][0]
            k2 = -float(lam) * 1e-9 * math.log(float(other[0])) / (4 * math.pi * other[1] * 1e-3)
            assert M.interpolation_error(glass, float(lam))[1] >= abs(k - k2)
        nodes += 1
    assert nodes == M.info(glass)["nodes"][1] == len(M.info(glass)["kappa_nodes_from"])
    lo, hi = M.info(glass)["range_nm"]
    assert np.all(M.index(glass, np.linspace(lo, hi, 4001)).imag > 0)


def test_schott_kappa_agrees_with_the_databases_transcription():
    """The refractiveindex.info database's kappa (SCHOTT's catalogue of 2017-01-20, printed to 5 digits) at a few
    wavelengths, from tau_i(25 mm) as the database takes it; N-SF11 at 370 nm differs as recorded (the current sheet
    prints tau_i(25 mm) = 0.000). Where the 10 mm value is more precise the engine takes it (review EX2, R2-E F9), and
    the two agree within their printed precisions."""
    for glass, lam, k_db in (("schott_n_bk7", 300.0, 2.8607e-06), ("schott_n_bk7", 500.0, 9.5781e-09),
                             ("schott_n_bk7", 2500.0, 8.1300e-06), ("schott_n_f2", 365.0, 3.7398e-06),
                             ("schott_n_f2", 620.0, 1.7842e-08), ("schott_n_sf11", 380.0, 2.5646e-06),
                             ("schott_n_sf11", 660.0, 4.0300e-08)):
        rows = {r.split()[0]: r.split()[1:] for r in data.OPTICAL_MATERIALS[glass]["tau"].strip().splitlines()}
        t10, t25 = rows[f"{lam:g}"]
        k25 = -lam * 1e-9 * math.log(float(t25)) / (4 * math.pi * 25e-3)
        assert k25 == pytest.approx(k_db, rel=1e-4)
        k = M.index(glass, lam).imag
        if k != k25:  # the 10 mm value; the interpolation error there covers the difference of the two
            k10 = -lam * 1e-9 * math.log(float(t10)) / (4 * math.pi * 10e-3)
            assert k == k10
            assert M.interpolation_error(glass, lam)[1] >= abs(k10 - k25)
    assert M.index("schott_n_bk7", 300.0).imag == pytest.approx(2.9552e-06, rel=1e-4)  # tau_i(10 mm) = 0.29
    assert M.index("schott_n_sf11", 370.0).imag == pytest.approx(7.4367e-06, rel=1e-4)  # database: 7.3192e-06


def test_sellmeier_crystals_against_a_second_transcription():
    """Dodge's MgF2 and Malitson's fused silica: the database's A_i, lambda_i against Wikipedia's «Sellmeier equation»
    (A_i and lambda_i^2 as printed there, revision of 2026-11-18)."""
    wiki = {"mgf2_dodge_o": ((0.48755108, 0.39875031, 2.3120353), ("0.001882178", "0.008951888", "566.13559")),
            "sio2_malitson": ((0.6961663, 0.4079426, 0.8974794), ("0.004679148", "0.01351206", "97.934"))}
    for key, (A, C) in wiki.items():
        spec = data.OPTICAL_MATERIALS[key]
        assert tuple(spec["A"]) == A
        for li, c in zip(spec["L"], C):
            assert abs(li * li - float(c)) <= _half_unit(c) * (1 + 1e-9), (key, li * li, c)
    assert M.index("mgf2_dodge_o", 632.8) == pytest.approx(1.37698, abs=0.5e-5)
    assert M.index("sio2_malitson", 632.8) == pytest.approx(1.45702, abs=0.5e-5)
    assert M.index("mgf2_dodge_o", 632.8).imag == 0.0 == M.index("sio2_malitson", 632.8).imag


# --- the tables ---------------------------------------------------------------------------------------------------
def _rows(key):
    return np.array([[float(v) for v in line.split()] for line in data.OPTICAL_MATERIALS[key]["table"].strip()
                     .splitlines()])


def _ends_nm(key):
    """A material's documented ends in nm, from the decimal text of its source (micrometres times 1000 exactly)."""
    spec = data.OPTICAL_MATERIALS[key]
    if "table" in spec:
        lines = spec["table"].strip().splitlines()
        ends = (lines[0].split()[0], lines[-1].split()[0])
    else:
        ends = tuple(repr(float(v)) for v in spec["range_um"])
    return tuple(float(Decimal(e) * 1000) for e in ends)


@pytest.mark.parametrize("key", M.ids())
def test_both_documented_ends_of_every_material_are_inside_its_range(key):
    """Review EX2, R2-E F3: 1000 * float("2.00146") is 2001.4599999999998 nm, which refused the documented end
    2001.46 nm of the MgF2 film (and 0.12399 nm of aluminium's table). Each end, written in nm as the source prints it
    in um, is accepted (a table's end node reproduced exactly), and the next double outwards is refused."""
    lo, hi = _ends_nm(key)
    assert M.info(key)["range_nm"] == (lo, hi)
    for end, out in ((lo, np.nextafter(lo, -np.inf)), (hi, np.nextafter(hi, np.inf))):
        v = M.index(key, end)
        assert np.isfinite(v.real) and v.imag >= 0
        with pytest.raises(ValueError) as e:
            M.index(key, out)
        assert code_of(e.value) == "material.out_of_range"
    if "table" in data.OPTICAL_MATERIALS[key]:
        rows = _rows(key)
        assert M.index(key, lo) == complex(rows[0, 1], rows[0, 2])
        assert M.index(key, hi) == complex(rows[-1, 1], rows[-1, 2])


def test_the_reviewed_ends_are_accepted():
    """The two ends the review found refused: MgF2 film at 2001.46 nm and aluminium at 0.12399 nm (their last and
    first table nodes)."""
    assert M.index("mgf2_film_rodriguez", 2001.46) == complex(*_rows("mgf2_film_rodriguez")[-1, 1:])
    assert M.index("al_rakic", 0.12399) == complex(*_rows("al_rakic")[0, 1:])


@pytest.mark.parametrize("key", TABLES)
def test_every_node_is_reproduced_exactly(key):
    rows = _rows(key)
    lines = data.OPTICAL_MATERIALS[key]["table"].strip().splitlines()
    lam = np.array([float(Decimal(line.split()[0]) * 1000) for line in lines])
    assert np.all(np.diff(lam) > 0)
    v = M.index(key, lam)
    assert np.array_equal(v.real, rows[:, 1]) and np.array_equal(v.imag, rows[:, 2])
    lo, hi = M.info(key)["range_nm"]
    assert (lo, hi) == (lam[0], lam[-1])


@pytest.mark.parametrize("key", TABLES)
def test_between_the_nodes_within_the_stated_interpolation_error(key):
    """At a quarter, a half and three quarters of every interval from 0.2 to 2.5 um, PCHIP and a second interpolant
    (Akima's, through the same nodes; kappa in ln kappa where the module uses it) differ by less than the stated
    interpolation error, for n and for kappa."""
    m = M._get(key)
    for which, tab in ((0, m.n_tab), (1, m.k_tab)):
        x = tab.x
        aki = Akima1DInterpolator(x, tab.y)
        for f in (0.25, 0.5, 0.75):
            pts = x[:-1] + f * np.diff(x)
            pts = pts[(pts >= 200.0) & (pts <= 2500.0)]
            if not len(pts):
                continue
            v = M.index(key, pts)
            ours = v.real if which == 0 else v.imag
            ref = aki(pts)
            if which == 1 and m.k_log:
                ref = np.exp(ref)
            err = M.interpolation_error(key, pts)[which]
            assert np.all(np.abs(ours - ref) <= err), (key, which, f, float(np.max(np.abs(ours - ref) / err)))


@pytest.mark.parametrize("key", M.ids())
def test_kappa_is_never_negative(key):
    lo, hi = M.info(key)["range_nm"]
    lam = np.geomspace(lo, hi, 20001)
    assert np.all(M.index(key, lam).imag >= 0)


def test_pchip_against_scipy():
    """The module's own PCHIP (the slopes as Moler describes them, §3.4) against SciPy's PchipInterpolator (BSD, in tests
    only): values and derivatives on uneven nodes with monotone stretches, extrema and flat parts."""
    rng = np.random.default_rng(3591)
    for trial in range(200):
        n = int(rng.integers(3, 40))
        x = np.cumsum(rng.uniform(0.1, 3.0, n))
        y = np.cumsum(rng.normal(size=n)) * rng.choice([0.0, 1.0], n, p=[0.1, 0.9])
        ours, ref = M.Pchip(x, y), PchipInterpolator(x, y)
        u = rng.uniform(x[0], x[-1], 200)
        scale = 1 + np.max(np.abs(y))
        assert np.allclose(ours(u), ref(u), atol=1e-13 * scale)
        assert np.allclose(ours.derivative(u), ref.derivative()(u), atol=1e-12 * scale)
        assert np.array_equal(ours(x), y)


# --- derivatives -------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("key", ["schott_n_bk7", "schott_n_f2", "schott_n_sf11", "mgf2_dodge_o", "sio2_malitson"])
def test_formula_derivatives_against_the_complex_step(key):
    """dn/dlambda of a Sellmeier formula against the complex-step derivative of the same formula (n is real-analytic in
    lambda: Im n(lambda + ih)/h, h = 1e-20 nm, no subtraction)."""
    spec = data.OPTICAL_MATERIALS[key]
    lo, hi = M.info(key)["range_nm"]
    for lam in np.linspace(lo + 1, hi - 1, 57):
        z = (lam + 1e-20j) / 1000.0
        if spec["form"] == "schott":
            n = np.sqrt(1 + sum(b * z * z / (z * z - c) for b, c in zip(spec["B"], spec["C"])))
        else:
            n = np.sqrt(1 + sum(a * z * z / (z * z - li * li) for a, li in zip(spec["A"], spec["L"])))
        assert M.dindex(key, lam).real == pytest.approx(n.imag / 1e-20, rel=1e-12)


@pytest.mark.parametrize("key", TABLES + ("schott_n_bk7",))
def test_table_derivatives_against_scipy_and_differences(key):
    m = M._get(key)
    lo, hi = m.range_nm
    lam = np.geomspace(lo, hi, 3001)[1:-1]
    d = M.dindex(key, lam)
    if m.n_tab is not None:
        assert np.allclose(d.real, PchipInterpolator(m.n_tab.x, m.n_tab.y).derivative()(lam), rtol=1e-10, atol=1e-15)
    kx, ky = m.k_tab.x, m.k_tab.y
    ref = PchipInterpolator(kx, ky).derivative()(lam)
    if m.k_log:
        ref = ref * np.exp(PchipInterpolator(kx, ky)(lam))
    assert np.allclose(d.imag, ref, rtol=1e-9, atol=1e-18)


# --- refusals, stack, the registry ---------------------------------------------------------------------------------
def test_refusals(ru):
    with pytest.raises(ValueError) as e:
        M.index("schott_n_bk7", 250.0)
    assert code_of(e.value) == "material.out_of_range" and is_t(e.value.args[0])
    assert "schott_n_bk7" in ru(e.value.args[0]) and "нм" in ru(e.value.args[0])
    with pytest.raises(ValueError) as e:
        M.index("au_johnson_christy", [500.0, 2000.0])
    assert code_of(e.value) == "material.out_of_range"
    with pytest.raises(ValueError):
        M.index("glass of unknown index", 632.8)
    with pytest.raises(ValueError):
        M.dindex("al_rakic", 3e5)


def test_stack_with_a_material_is_stack_with_its_index():
    """``stack`` takes the material's complex index as any other: the same r, t, R, T as with the number typed in, and
    within the sheet's printed digit of the printed n(632.8 nm)."""
    n = M.index("schott_n_bk7", 632.8)
    typed = complex(repr(n))
    for th in np.radians([0.0, 30.0, 56.574, 80.0]):
        for pol in "sp":
            a = interfaces.stack([1.0, n], [], 632.8, th, pol)
            b = interfaces.stack([1.0, typed], [], 632.8, th, pol)
            c = interfaces.stack([1.0, 1.51509], [], 632.8, th, pol)
            assert a == b
            assert abs(a["R"] - c["R"]) < 1e-6
    gold = M.index("au_johnson_christy", 632.8)
    a = interfaces.stack([n.real, gold, 1.0], [50.0], 632.8, math.radians(43.773), "p")
    assert a == interfaces.stack([n.real, complex(repr(gold)), 1.0], [50.0], 632.8, math.radians(43.773), "p")


@pytest.mark.parametrize("key", M.ids())
def test_every_material_is_a_dataset_entry_with_its_record(key):
    entry = registry.about(f"core.data:{key}")
    assert entry["layer"] == "core" and entry["kind"] == "data" and entry["basis"]
    assert all(entry[k] for k in ("title", "statement", "validity")) and is_t(entry["checked"])
    i = M.info(key)
    assert i["id"] == key and i["range_nm"][0] < i["range_nm"][1]
    assert i["interp_error_n"] >= 0 and i["interp_error_k"] >= 0
    if key in GLASSES:  # the statement's numbers are the module's
        args = data.DATASETS[key]["statement"].args
        assert M.index(key, 632.8).real == pytest.approx(args["n633"], abs=0.5e-5)
        assert M.index(key, 587.5618).real == pytest.approx(args["nd"], abs=0.5e-5)


def test_the_catalogue_names_every_material():
    assert set(M.ids()) <= set(data.DATASETS)
    assert set(M.ids()) == {"schott_n_bk7", "schott_n_f2", "schott_n_sf11", "mgf2_dodge_o", "mgf2_film_rodriguez",
                            "sio2_malitson", "sio2_film_gao", "ta2o5_film_gao", "au_johnson_christy",
                            "ag_johnson_christy", "al_rakic"}


# --- the numbers the EX2 design builds on (§3.1, §3.2, §3.3, §3.9, Appendix A.7) -----------------------------------
def test_numbers_the_ex2_design_uses():
    deg = math.degrees
    L = 632.8
    printed = {"schott_n_bk7": 1.51509, "schott_n_f2": 1.61658, "schott_n_sf11": 1.77860, "mgf2_dodge_o": 1.37698,
               "sio2_malitson": 1.45702, "sio2_film_gao": 1.47615, "ta2o5_film_gao": 2.13576}
    for key, n in printed.items():
        assert M.index(key, L).real == pytest.approx(n, abs=0.5e-5)
    assert M.index("mgf2_film_rodriguez", L) == pytest.approx(1.42118 + 0.00054j, abs=0.5e-5)
    for key, thb, thc in (("schott_n_bk7", 56.574, 41.302), ("schott_n_f2", 58.259, 38.213),
                          ("schott_n_sf11", 60.654, 34.211)):
        n = M.index(key, L).real
        assert round(deg(interfaces.brewster(1.0, n)), 3) == thb and round(deg(interfaces.critical(n, 1.0)), 3) == thc

    def R(lam, layers, ds):
        ns = [1.0] + [M.index(k, lam) for k in layers] + [M.index("schott_n_bk7", lam)]
        return 0.5 * (interfaces.stack(ns, ds, lam, 0.0, "s")["R"] + interfaces.stack(ns, ds, lam, 0.0, "p")["R"])

    q = {k: 550.0 / (4 * M.index(k, 550.0).real) for k in ("mgf2_film_rodriguez", "mgf2_dodge_o", "ta2o5_film_gao",
                                                           "sio2_film_gao")}
    assert round(q["mgf2_film_rodriguez"], 2) == 96.64
    for lam, bare, film in ((400.0, 4.40, 2.79), (550.0, 4.24, 2.04), (633.0, 4.19, 2.14), (700.0, 4.17, 2.28)):
        assert round(100 * R(lam, [], []), 2) == bare
        assert round(100 * R(lam, ["mgf2_film_rodriguez"], [q["mgf2_film_rodriguez"]]), 2) == film
    assert round(100 * R(550.0, ["mgf2_dodge_o"], [q["mgf2_dodge_o"]]), 2) == 1.25
    HL = ["ta2o5_film_gao", "sio2_film_gao"]
    dHL = [q["ta2o5_film_gao"], q["sio2_film_gao"]]
    assert round(100 * R(550.0, HL * 4, dHL * 4), 1) == 87.9 and round(100 * R(632.8, HL * 4, dHL * 4), 1) == 70.3
    assert round(100 * R(550.0, HL * 8, dHL * 8), 2) == 99.37 and round(100 * R(632.8, HL * 8, dHL * 8), 1) == 75.8
    assert round(100 * R(450.0, HL * 8, dHL * 8), 1) == 27.4
    # the Kretschmann preset: 50 nm of gold on N-BK7; with the module's PCHIP R_p is smallest, 0.0038, at 43.773 deg
    # ([error in earlier] the design's 0.0058 at 43.785 deg came from linear interpolation of the same table)
    nb, au = M.index("schott_n_bk7", L).real, M.index("au_johnson_christy", L)
    res = minimize_scalar(lambda t: interfaces.stack([nb, au, 1.0], [50.0], L, t, "p")["R"],
                          bounds=(math.radians(42), math.radians(46)), method="bounded", options={"xatol": 1e-12})
    assert round(res.fun, 4) == 0.0038 and round(deg(res.x), 3) == 43.773
