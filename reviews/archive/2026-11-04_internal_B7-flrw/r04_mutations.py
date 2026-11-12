"""r04: negative controls - plausible variants of the engine run through tests/test_flrw.py.

 M0  the engine as it is (all pass).
 M1  Astropy's / Komatsu's neutrino convention (massive species = N_eff/3 x the density of mass m at (4/11)^(1/3) T,
     i.e. the engine with m -> m (N_eff/3)^(1/4)).
 M2  the gigayear of the CAMB behind Planck 2018 (3.1556926e16 s, 365.2422 d) instead of the Julian one.
 M3  r_s integrated from a = 1e-8 instead of 0 (CAMB <= 1.3.6's derived r_*, r_drag).
 M4  the massive species' temperature scaled by (N_eff/3)^(1/3) instead of ^(1/4) (a wrong exponent: omega_nu
     changes by (N_eff/3)^(-1/12 x 3)... i.e. -0.04 %).
 M5  N_eff counted as 3.046 for the massless species but 3 for the massive one (no heating of the massive species).
Each mutation is applied by monkeypatching the module the tests import; the test functions are called directly.
Run (from engine/):
  docker run --rm --name lf-b7rc-r04 -v $PWD:/lf:ro -v $PWD/reviews/2026-11-04_internal_B7-flrw:/out \
    -e PYTHONDONTWRITEBYTECODE=1 -e LFPHYS_NO_GPU=1 -w /lf/lfphys light-funnel-viz python3 /out/r04_mutations.py
"""
import contextlib
import math
import sys

import numpy as np

sys.path.insert(0, "/lf/lfphys")
sys.path.insert(0, "/lf/lfphys/tests")
import test_flrw as TF  # noqa: E402
from lfphys.core.cosmology import flrw as F  # noqa: E402

TESTS = [n for n in dir(TF) if n.startswith("test_")]
ORIG_INIT = F.Background.__init__
ORIG_RS = F.Background.sound_horizon
ORIG_GYR = F.GYR_S


@contextlib.contextmanager
def m1():
    def init(self, H0, Om, *, m_nu=(), N_eff=0.0, n_nu=3, **kw):
        s = (N_eff / n_nu) ** 0.25 if N_eff > 0 else 1.0
        ORIG_INIT(self, H0, Om, m_nu=tuple(m * s for m in np.atleast_1d(m_nu)) if np.size(m_nu) else (),
                  N_eff=N_eff, n_nu=n_nu, **kw)
    F.Background.__init__ = init
    try:
        yield
    finally:
        F.Background.__init__ = ORIG_INIT


@contextlib.contextmanager
def m2():
    F.GYR_S = 3.1556926e16
    try:
        yield
    finally:
        F.GYR_S = ORIG_GYR


@contextlib.contextmanager
def m3():
    def rs(self, z, *, rtol=1e-13, with_error=False):
        v, e = ORIG_RS(self, z, rtol=rtol, with_error=True)
        orad = self.Orad + self.Onu_per_species * self._y0.size
        piece = 1e-8 / math.sqrt(3 * orad) * self.hubble_distance      # radiation era, R ~ 0
        v = np.asarray(v) - piece
        v = float(v) if v.ndim == 0 else v
        return (v, e) if with_error else v
    F.Background.sound_horizon = rs
    try:
        yield
    finally:
        F.Background.sound_horizon = ORIG_RS


@contextlib.contextmanager
def m4():
    def init(self, H0, Om, *, m_nu=(), N_eff=0.0, n_nu=3, **kw):
        s = (N_eff / n_nu) ** (0.25 - 1 / 3) if N_eff > 0 else 1.0     # y0 uses T x (N/n)^(1/3) instead of ^(1/4)
        ORIG_INIT(self, H0, Om, m_nu=tuple(m * s for m in np.atleast_1d(m_nu)) if np.size(m_nu) else (),
                  N_eff=N_eff, n_nu=n_nu, **kw)
    F.Background.__init__ = init
    try:
        yield
    finally:
        F.Background.__init__ = ORIG_INIT


@contextlib.contextmanager
def m5():
    def init(self, H0, Om, *, m_nu=(), N_eff=0.0, n_nu=3, **kw):
        ORIG_INIT(self, H0, Om, m_nu=m_nu, N_eff=N_eff, n_nu=n_nu, **kw)
        if self._y0.size and N_eff > 0:
            # the massive species at the unheated temperature and density (degeneracy 1): rescale its term
            s = (N_eff / n_nu) ** 0.25
            self._y0 = self._y0 * s
            fac = 1.0 / (N_eff / n_nu)
            old = self.Onu_massive
            self.Onu_massive = self.Onu_per_species * fac * float(np.sum(F._fd_sums(self._y0)[0]))
            self._mut_fac = fac
            self.OL = self.OL - (self.Onu_massive - old) if kw.get("OL") is None else self.OL
    F.Background.__init__ = init
    orig_terms = F.Background._terms

    def terms(self, a):
        out = list(orig_terms(self, a))
        f = getattr(self, "_mut_fac", 1.0)
        out[4] = out[4] * f
        out[6] = out[6] * f
        return tuple(out)
    F.Background._terms = terms
    try:
        yield
    finally:
        F.Background.__init__ = ORIG_INIT
        F.Background._terms = orig_terms


def run(label, ctx):
    failed = []
    with ctx():
        for n in TESTS:
            try:
                getattr(TF, n)()
            except AssertionError:
                failed.append(n)
            except Exception as exc:  # noqa: BLE001
                failed.append(f"{n} ({type(exc).__name__})")
    print(f"{label}: {len(TESTS) - len(failed)} of {len(TESTS)} pass; failing: {failed if failed else 'none'}")


run("M0 engine as is", contextlib.nullcontext)
run("M1 Astropy/Komatsu neutrino convention", m1)
run("M2 Gyr = 3.1556926e16 s (CAMB <= 1.3.6)", m2)
run("M3 r_s from a = 1e-8 (CAMB <= 1.3.6)", m3)
run("M4 massive-species temperature exponent 1/3", m4)
run("M5 massive species unheated (degeneracy 1, T_std)", m5)
