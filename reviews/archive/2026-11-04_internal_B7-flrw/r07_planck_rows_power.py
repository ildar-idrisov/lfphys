"""r07: what each Planck 2018 Table 2 row of tests/test_flrw.py can detect. For variants of the physics, the row's
difference to the printed value is compared with the row's budget as listed in sources/verification_2026-11-04_p8_flrw.md
§11.1 (Omega_m 1.8e-4, Omega_L 1.8e-4, Omega_m h^2 1.5e-5, Omega_m h^3 2.7e-5, age 1.6e-3, r_* 1.2e-2, r_drag 1.2e-2,
100 theta_* 5.2e-5; z_eq: 0.5 + input rounding ~0.25 -> 0.75 used here). A variant that stays inside every budget is
invisible to the comparison.
Run (from engine/):
  docker run --rm --name lf-b7rc-r07 -v $PWD:/lf:ro -v $PWD/reviews/2026-11-04_internal_B7-flrw:/out \
    -e PYTHONDONTWRITEBYTECODE=1 -e LFPHYS_NO_GPU=1 -w /lf/lfphys light-funnel-viz python3 /out/r07_planck_rows_power.py
"""
import sys

sys.path.insert(0, "/lf/lfphys")
from lfphys.core import data as D  # noqa: E402
from lfphys.core.cosmology import flrw as F  # noqa: E402

P = D.PLANCK2018_BAO
h, ob, oc = P["H0"][0] / 100, P["omega_b"][0], P["omega_c"][0]
zs, zd = P["z_star"][0], P["z_drag"][0]
T, NEFF, M = D.PLANCK2018_T_CMB_K, D.PLANCK2018_N_EFF, D.PLANCK2018_M_NU_EV
BUDGET = {"Omega_m": 1.8e-4, "Omega_L": 1.8e-4, "omega_m": 1.5e-5, "Omega_m_h3": 2.7e-5, "age": 1.6e-3,
          "r_star": 1.2e-2, "r_drag": 1.2e-2, "100theta": 5.2e-5, "z_eq": 0.75}
PRINT = {"Omega_m": P["Omega_m"][0], "Omega_L": P["Omega_L"][0], "omega_m": P["omega_m"][0],
         "Omega_m_h3": P["Omega_m_h3"][0], "age": P["age_Gyr"][0], "r_star": P["r_star_Mpc"][0],
         "r_drag": P["r_drag_Mpc"][0], "100theta": P["100theta_star"][0], "z_eq": P["z_eq"][0]}


def rowsof(bg, age_fac=1.0, rs_cut=0.0, extra_rad_in_closure=True):
    orad = bg.Orad + bg.Onu_per_species * bg._y0.size
    rs_piece = rs_cut / (3 * orad) ** 0.5 * bg.hubble_distance if rs_cut else 0.0
    rs, rd = bg.sound_horizon(zs) - rs_piece, bg.sound_horizon(zd) - rs_piece
    OL = bg.OL if extra_rad_in_closure else 1 - bg.Om_total
    return {"Omega_m": bg.Om_total, "Omega_L": OL, "omega_m": bg.Om_total * bg.h ** 2,
            "Omega_m_h3": bg.Om_total * bg.h ** 3, "age": bg.age() * age_fac, "r_star": rs, "r_drag": rd,
            "100theta": 100 * rs / bg.transverse_comoving_distance(zs),
            "z_eq": bg.z_equality("relativistic") if orad > 0 else float("nan")}


def mk(**kw):
    a = dict(T_cmb=T, N_eff=NEFF, m_nu=(M,))
    a.update(kw)
    return F.from_physical(h, ob, oc, **a)


eng = mk()
s = (NEFF / 3) ** 0.25
variants = [
    ("engine", rowsof(eng)),
    ("radiation left out of the closure only", rowsof(eng, extra_rad_in_closure=False)),
    ("Astropy/Komatsu nu convention", rowsof(mk(m_nu=(M * s,)))),
    ("massive nu as dust (2 massless + omega_nu in dust)",
     rowsof(F.from_physical(h, ob + eng.omega_nu_massive(), oc, T_cmb=T, N_eff=NEFF * 2 / 3, n_nu=2))),
    ("N_eff = 3.044 (current standard value)", rowsof(mk(N_eff=3.044))),
    ("T_cmb = 2.72548 (Fixsen's value, not rounded)", rowsof(mk(T_cmb=2.72548))),
    ("CAMB<=1.3.6 numerics: Gyr 3.1556926e16 s, Mpc 3.085678e22, r_s from a=1e-8",
     rowsof(eng, age_fac=(3.085678e22 / F.MPC_M) / (3.1556926e16 / F.GYR_S), rs_cut=1e-8)),
    ("no massive neutrino at all (3 massless)", rowsof(mk(m_nu=()))),
]
keys = list(BUDGET)
print(f"{'variant':72s} " + " ".join(f"{k:>10s}" for k in keys))
print(f"{'budget':72s} " + " ".join(f"{BUDGET[k]:10.1e}" for k in keys))
for lab, r in variants:
    cells = []
    for k in keys:
        d = r[k] - PRINT[k]
        cells.append(f"{d / BUDGET[k]:+9.2f}{'*' if abs(d) > BUDGET[k] else ' '}")
    print(f"{lab:72s} " + " ".join(cells))
print("\ncells: (variant - printed) / budget; * = outside the budget (the row would detect the variant)")
