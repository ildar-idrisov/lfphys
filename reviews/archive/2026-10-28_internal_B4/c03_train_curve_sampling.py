# [root path fixed after archiving, 2026-10-28, by the responder: reviews/ -> reviews/archive/]
# Review B4, check c03: are v12's curves computed from the initial state (ABK, semiclassical, absorbing boundary;
# CURVE_N = 1501 samples over the observation window, K_N = 4001 wave numbers) resolved for a train of packets?
# The semiclassical density of a train, Pi_SC = (mD/hbar t^2)|psi~(mD/hbar t)|^2, carries the train's comb
# |sum_j e^{i k j sep}|^2 in k = D/t (Das & Struyve 2021, eq. 43: sin^2(N ...)/sin^2(...)); its fringes are
# Delta t ~ 2 pi D / (sep k0^2) apart, which for long trains is shorter than the window's sample spacing.
#
# Root (fix after archiving): engine mounted at /lf (host /home/ildar/hdd/projects/i/light-funnel/engine); this
# script in /lf/reviews/archive/2026-10-28_internal_B4/.
# Run:
#   docker run --rm --user "$(id -u):$(id -g)" -v <engine>:/lf:ro \
#     -e PYTHONPATH=/lf/visualizations:/lf/visualizations/server:/lf/lfphys light-funnel-viz \
#     python3 /lf/reviews/archive/2026-10-28_internal_B4/c03_train_curve_sampling.py > out/c03_train_curve_sampling.txt
import math

import numpy as np

from lfphys.core.quantum.schrodinger1d import FreeGaussians
from lfphys.theories.interpretations import arrival_times as AT
from lfphys.theories.models import detection as DET
from v12_arrival_times_2d.engine import apparatus as AP
from v12_arrival_times_2d import viz as V12


def stats(t, P):
    w = np.gradient(t)
    w[0] *= 0.5
    w[-1] *= 0.5
    tot = float(np.sum(P * w))
    return tot, float(np.sum(t * P * w) / tot)


def case(label, state, sigma_z, D, n_train=4, sep=30.0):
    pk = AP.packets(state, sigma_z, n_train, sep, D)
    fg = FreeGaussians(pk)
    t_obs = 1.02 * AP.leave_time(fg, D)
    t0 = D / AP.V0_SPEED
    lo, hi = AP.k_range(pk)
    k = np.linspace(lo, hi, V12.K_N)
    phi = fg.phi(k)
    tau = np.linspace(0.0, t_obs, V12.CURVE_N)           # v12's samples
    fine = np.linspace(0.0, t_obs, 400001)               # a reference grid
    print(f"\n== {label}: state {state}, sigma_z {sigma_z}, D {D}, N {n_train}, sep {sep}; t_obs = {t_obs / t0:.4f} t0, "
          f"sample step {t_obs / (V12.CURVE_N - 1) / t0:.2e} t0, fringe spacing ~ 2 pi D/(sep k0^2) = "
          f"{2 * math.pi * D / (sep * AP.K0 ** 2) / t0:.2e} t0 ==")
    for name, f in (("semiclassical", lambda tt: AT.semiclassical(fg.phi, D, tt)),
                    ("ABK", lambda tt: AT.kijowski(phi, k, D, tt)),
                    ("ABR kappa=k0", lambda tt: DET.abr_density(phi, k, D, AP.K0, tt))):
        P = f(tau)
        tot, mean = stats(tau, P)
        if name == "semiclassical":
            Pf = f(fine)
        else:  # ABK and ABR are smooth on the scale of a packet: a 20001-sample grid is enough as reference
            fine2 = np.linspace(0.0, t_obs, 20001)
            Pf = f(fine2)
            tot_f, mean_f = stats(fine2, Pf)
            print(f"  {name:14s} v12 grid: total {tot:.6f}, mean {mean / t0:.5f} t0 | fine: total {tot_f:.6f}, "
                  f"mean {mean_f / t0:.5f} t0")
            continue
        tot_f, mean_f = stats(fine, Pf)
        # the drawn curve against the fine one at the drawn samples' positions is exact (same function); what matters is
        # what lies between them: the largest value in each sample interval against the sampled values
        idx = np.searchsorted(fine, tau)
        peak_between = max(float(Pf[idx[i]:idx[i + 1] + 1].max()) for i in range(len(tau) - 1))
        print(f"  {name:14s} v12 grid: total {tot:.6f}, mean {mean / t0:.5f} t0 | fine: total {tot_f:.6f}, mean "
              f"{mean_f / t0:.5f} t0 | exact total int_k>0 |phi|^2 = "
              f"{float(np.trapezoid(np.abs(fg.phi(np.linspace(1e-9, hi, 400001))) ** 2, np.linspace(1e-9, hi, 400001))):.6f}"
              f" | largest value: sampled {float(P.max()) * t0:.4g}, between samples {peak_between * t0:.4g} (x t0)")


case("preset 'train'", "train", 5.0, 30.0, 4, 30.0)
case("train N = 8, sep = 60", "train", 5.0, 30.0, 8, 60.0)
case("train N = 8, sep = 120 (schema maximum)", "train", 5.0, 30.0, 8, 120.0)
case("train N = 8, sep = 120, sigma_z = 2", "train", 2.0, 30.0, 8, 120.0)
case("preset 'gauss'", "gauss", 5.0, 30.0)
