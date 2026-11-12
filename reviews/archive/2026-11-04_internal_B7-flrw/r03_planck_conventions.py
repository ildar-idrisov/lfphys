"""r03: what the Planck 2018 comparisons can and cannot see.

 1. Omega_m h^2 of Table 1's best fit under four neutrino conventions, against the tolerance of
    tests/test_flrw.py::test_planck2018_best_fit_table1 (5e-6 + 5e-7 + 5e-6).
 2. The constants of the CAMB that produced Planck 2018 (tags Aug2017 ... 1.3.6: Gyr = 3.1556926e16 s,
    Mpc = 3.085678e22 m, G = 6.6738e-11, k_B = 1.3806504e-23, h = 6.62606896e-34, neutrino_mass_fac = 94.07 in CosmoMC)
    against the engine's (Julian Gyr, IAU pc, CODATA 2022): the shifts of the age, z_eq, k_eq.
 3. The sound horizon as CAMB <= 1.3.6 computed its derived r_* and r_drag: rombint(dsound_da_exact, 1d-8, ...) - the
    piece from a = 0 to 1e-8 that it omits.
 4. N_eff != 3.046: the engine's equal sharing against CAMB/CosmoMC's split (massive species keep 3.046/3 each).
 5. The tolerance of the "H0 solved from theta_*" row: which part is derived.
Run (from engine/):
  docker run --rm --name lf-b7rc-r03 -v $PWD:/lf:ro -v $PWD/reviews/2026-11-04_internal_B7-flrw:/out \
    -e PYTHONDONTWRITEBYTECODE=1 -e LFPHYS_NO_GPU=1 -w /lf/lfphys light-funnel-viz python3 /out/r03_planck_conventions.py
"""
import math
import sys

import mpmath as mp
import numpy as np
from scipy import optimize

sys.path.insert(0, "/lf/lfphys")
from lfphys.core import data as D  # noqa: E402
from lfphys.core.cosmology import flrw as F  # noqa: E402

T, NEFF, M = D.PLANCK2018_T_CMB_K, D.PLANCK2018_N_EFF, D.PLANCK2018_M_NU_EV
P1, P2 = D.PLANCK2018_BESTFIT, D.PLANCK2018_BAO


def bg_from(h, ob, oc, m=M, neff=NEFF, n_nu=3):
    return F.from_physical(h, ob, oc, T_cmb=T, N_eff=neff, m_nu=(m,), n_nu=n_nu)


# ---- 1. Omega_m h^2 under four conventions ------------------------------------------------------------------------
print("1. Table 1 best fit, Omega_m h^2 = omega_b + omega_c + omega_nu (printed 0.14314); test tolerance 1.05e-5")
h = P1["H0"] / 100
eng = bg_from(h, P1["omega_b"], P1["omega_c"])
s = (NEFF / 3) ** 0.25
conv = {
    "engine (CAMB: T x (Neff/3)^(1/4), physical m)": eng.omega_nu_massive(),
    "Astropy/Komatsu (density x Neff/3 at T_std)": bg_from(h, P1["omega_b"], P1["omega_c"], m=M * s).omega_nu_massive(),
    "Mangano et al. 2005: sum m / 93.14 eV": M / 93.14,
    "instantaneous decoupling, no N_eff factor: m/94.07": M / 94.07,
}
tol = 5e-6 + 5e-7 + 5e-6
for k, onu in conv.items():
    om = P1["omega_b"] + P1["omega_c"] + onu
    print(f"   {k:48s} omega_nu = {onu:.5e}  Omega_m h^2 = {om:.7f}  |diff| = {abs(om - P1['omega_m']):.2e}  "
          f"{'passes' if abs(om - P1['omega_m']) <= tol else 'FAILS'}")
om0 = P1["omega_b"] + P1["omega_c"]
print(f"   {'no massive neutrino at all':48s} omega_nu = 0            Omega_m h^2 = {om0:.7f}  |diff| = "
      f"{abs(om0 - P1['omega_m']):.2e}  {'passes' if abs(om0 - P1['omega_m']) <= tol else 'FAILS'}")
print(f"   engine's sum m/omega_nu = {M / eng.omega_nu_massive():.4f} eV; NR proxy of CosmoMC: 94.07/(3.046/3)^0.75 = "
      f"{94.07 / (NEFF / 3) ** 0.75:.4f} eV; Mangano 93.14 eV is quoted at their T0 (instantaneous value 94.12)")

# ---- 2. CAMB <= 1.3.6 constants ------------------------------------------------------------------------------------
print("\n2. CAMB constants behind Planck 2018 vs the engine's")
GYR_OLD, MPC_OLD = 3.1556926e16, 3.085678e22
G_OLD, KB_OLD, H_OLD = 6.6738e-11, 1.3806504e-23, 6.62606896e-34
from scipy import constants as sc  # noqa: E402
age_fac = (MPC_OLD / F.MPC_M) / (GYR_OLD / F.GYR_S)       # Planck's age number / the engine's for the same universe
for lab, P, hh in (("Table 1 best fit", P1, P1["H0"]), ("Table 2 BAO means", P2, P2["H0"][0])):
    ob = P["omega_b"] if lab.startswith("Table 1") else P["omega_b"][0]
    oc = P["omega_c"] if lab.startswith("Table 1") else P["omega_c"][0]
    b = bg_from(hh / 100, ob, oc)
    age_pr = P["age_Gyr"] if lab.startswith("Table 1") else P["age_Gyr"][0]
    a_eng = b.age()
    print(f"   {lab}: engine age {a_eng:.6f} Gyr (Julian); in CAMB<=1.3.6 units {a_eng * age_fac:.6f}; printed "
          f"{age_pr}; diff engine {a_eng - age_pr:+.2e}, CAMB units {a_eng * age_fac - age_pr:+.2e}")
print(f"   factor (Mpc_old/Mpc)/(Gyr_old/Gyr_Julian) - 1 = {age_fac - 1:.3e}")
og_ratio = (G_OLD / sc.G) * (KB_OLD / sc.k) ** 4 * (sc.h / H_OLD) ** 3
b = bg_from(P2["H0"][0] / 100, P2["omega_b"][0], P2["omega_c"][0])
zeq = b.z_equality("relativistic")
zeq_old = (zeq + 1) / og_ratio - 1
print(f"   omega_gamma(old constants)/omega_gamma(CODATA 2022) - 1 = {og_ratio - 1:.3e} (G dominates); z_eq "
      f"{zeq:.3f} -> {zeq_old:.3f} (shift {zeq_old - zeq:+.3f}; Table 2: 3387 +- 21, printed to 1)")

# ---- 3. the sound-horizon integral from a = 1e-8 -------------------------------------------------------------------
print("\n3. r_s as CAMB <= 1.3.6 integrated it: from a = 1e-8 (current CAMB: 1e-9)")
mp.mp.dps = 30
Or, Om, Ok, OL, Onu = (mp.mpf(x) for x in (b.Orad, b.Om, b.Ok, b.OL, b.Onu_per_species))
R0 = mp.mpf(3) * mp.mpf(b.Ob) / (4 * mp.mpf(b.Ogamma))
y0 = float(b._y0[0])


def Smp(a):
    return Or + Om * a + Ok * a * a + OL * a ** 4 + Onu * mp.mpf(F.fermi_dirac_energy(float(a) * y0))


for lo in (1e-8, 1e-9):
    piece = mp.quad(lambda a: 1 / mp.sqrt(Smp(a)) / mp.sqrt(3 * (1 + R0 * a)), [0, lo]) * b.hubble_distance
    rs = b.sound_horizon(P2["z_star"][0])
    print(f"   omitted int_0^{lo:g}: {float(piece):.3e} Mpc = {float(piece) / rs:.2e} of r_* = {rs:.4f} Mpc "
          f"(the test budgets CAMB's r_s at 1e-6 relative = {1e-6 * rs:.1e} Mpc)")

# ---- 4. N_eff != 3.046 ---------------------------------------------------------------------------------------------
print("\n4. one 0.06 eV species with N_eff != 3.046: engine (N_eff/3 per species) vs CAMB/CosmoMC (massive keeps "
      "3.046/3, rest massless)")
for neff in (2.5, 3.046, 3.5, 4.0):
    e = F.Background(67.66, 0.31, T_cmb=T, N_eff=neff, m_nu=(M,))
    # CAMB split: the massive species at degeneracy 3.046/3 (temperature (3.046/3)^(1/4) T_nu), massless = neff - that
    deg = 3.046 / 3 if neff > 3.046 / 3 else neff
    onu_camb = M / 94.07 * deg ** 0.75 if neff > 3.046 else M / 94.07 * (neff / 3) ** 0.75   # CosmoMC lines 302-306
    print(f"   N_eff = {neff:5.3f}: engine omega_nu = {e.omega_nu_massive():.5e}, CosmoMC/CAMB = {onu_camb:.5e} "
          f"(ratio {e.omega_nu_massive() / onu_camb:.4f}); engine massive-species T scale {(neff / 3) ** 0.25:.4f}, "
          f"CAMB {(3.046 / 3) ** 0.25:.4f}")

# ---- 5. the H0-from-theta_* tolerance ------------------------------------------------------------------------------
print("\n5. tests/test_flrw.py: H0 solved from theta_* (z_* = 1089.80 and theta_* from the table)")
zs = P2["z_star"][0]
target = P2["100theta_star"][0] / 100


def theta_of(H0, ob=P2["omega_b"][0], oc=P2["omega_c"][0]):
    bb = bg_from(H0 / 100, ob, oc)
    return bb.sound_horizon(zs) / bb.transverse_comoving_distance(zs)


H0s = optimize.brentq(lambda x: theta_of(x) - target, 60, 75, xtol=1e-10)
dth = (theta_of(H0s + 0.01) - theta_of(H0s - 0.01)) / 0.02
derived = 0.005 + (5e-8 + 1e-6 * target) / abs(dth)
# what the row leaves out: the rounding of omega_b, omega_c (5e-6 each) and of z_* (0.005) carried into H0
dH_dob = abs((optimize.brentq(lambda x: theta_of(x, ob=P2["omega_b"][0] + 5e-6) - target, 60, 75, xtol=1e-10) - H0s))
dH_doc = abs((optimize.brentq(lambda x: theta_of(x, oc=P2["omega_c"][0] + 5e-6) - target, 60, 75, xtol=1e-10) - H0s))
print(f"   H0 = {H0s:.5f} (table 67.66); |diff| = {abs(H0s - 67.66):.2e}")
print(f"   tolerance in the test: derived part {derived:.2e} + ad hoc 0.1 sigma(H0) = {0.1 * P2['H0'][1]:.3f} "
      f"-> total {derived + 0.1 * P2['H0'][1]:.3f}")
print(f"   left out: omega_b rounding -> {dH_dob:.2e}, omega_c rounding -> {dH_doc:.2e} km/s/Mpc")
print("   the row is the theta_* row inverted (same equation, same inputs): not an independent agreement")
