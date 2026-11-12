# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""de Broglie-Bohm guidance: trajectories driven by the probability current of the wave.

    dx/dz = Im(Psi^dagger dPsi/dx) / (k |Psi|^2)       (paraxial stationary waves behind slits)
    dr/dt = (hbar/m) Im(psi^dagger grad psi) / (psi^dagger psi) - (q/m) A     (time-dependent waves in 1-D, 2-D, 3-D)

For spinors the second form is the guidance law of Bohm, Schiller & Tiomno (1955) (the convective current summed
over the components); Holland's version adds the divergence-free spin term (hbar/2m) curl(psi^dag sigma psi) / rho,
which gives other trajectories with the same distribution (``lfphys.core.quantum.schrodinger_nd.Grid.current``
computes that term on request).

The trajectories reproduce the Born-rule distribution when started |Psi|^2-distributed (equivariance), so they add
no new prediction for position measurements: an interpretation, not a different theory. For photons the same field
lines are the average photon trajectories measured by weak measurement (Kocsis et al., Science 332, 1170 (2011)).
"""

from __future__ import annotations

import numpy as np

from ...core.quantum import schrodinger_nd as SND
from ..approx.paraxial import current, slit_amplitudes

ABOUT = {
    "layer": "theories", "kind": "interpretation",
    "title": "Интерпретация де Бройля–Бома: траектории по току вероятности",
    "statement": "Частица имеет траекторию: dx/dz = Im(Ψ†∂Ψ)/(k|Ψ|²) за щелями (параксиально) или "
                 "dr/dt = (ħ/m) Im(ψ†∇ψ)/(ψ†ψ) − (q/m)A для волны, зависящей от времени, в 1-D, 2-D и 3-D (для спинора "
                 "— по Бому–Шиллеру–Томно); начальные положения распределены по |ψ|², поэтому предсказания для "
                 "положений совпадают с правилом Борна.",
    "validity": "чистое состояние без декогеренции; при смеси — линии усреднённого тока ансамбля",
    "basis": ["Bohm, Phys. Rev. 85, 166 (1952)", "Kocsis et al., Science 332, 1170 (2011)",
              "Bohm, Schiller, Tiomno, Nuovo Cimento Suppl. 1, 48 (1955) — уравнение Паули",
              "Philippidis, Dewdney, Hiley, Nuovo Cimento B 52, 15 (1979) — траектории за двумя щелями"],
    "conflicts": ["копенгагенская интерпретация: траекторий нет; многомировая: траекторий нет, есть ветви",
                  "теория относительности (lfphys.core.relativity, core.causality): для запутанных частиц закон "
                  "ведения нелокален — скорость одной частицы зависит от мгновенного положения другой, нужна "
                  "выделенная слоистость пространства-времени; лоренц-инвариантных траекторий нет, хотя "
                  "наблюдаемые предсказания с СТО согласуются (Bell, Speakable and Unspeakable in Quantum "
                  "Mechanics, 1987; Dürr et al., Proc. R. Soc. A 470, 20130699 (2014))"],
}


def slit_trajectories(k, slits, a, L1, G, weights, z_max, n=40, rng=None, n_steps=1500):
    """Bohmian (de Broglie-Bohm) paths of the paraxial wave: dx/dz = Im(Psi^dag dPsi/dx) / (k |Psi|^2).
    For photons the same field lines are the average photon trajectories measured by weak measurement
    (Kocsis et al., Science 332, 1170 (2011)). Starting points at z0 = 2a, distributed by |Psi(x, z0)|^2 (the
    density with the coherence matrix G, which carries the slits' weights): stratified quantiles u_i = (i + 1/2)/n
    of its cumulative distribution on a fine grid, so the ensemble is equivariant from the start. (Until 2026-10-23
    the starts were uniform across each slit, which at z0 = 2a misses the ripple of |Psi|^2 and the 4-11 % of it
    outside the slit window: review 2026-10-23, E10.) ``rng`` is kept for the call signature (the starts are
    deterministic)."""
    w = np.asarray(weights, float)
    if w.sum() <= 0:
        return None
    sl = np.asarray(slits, float)
    z0 = 2.0 * a
    spread = 3.0 * a + 6.0 * np.sqrt(2.0 * np.pi * z0 / k)  # the slit window, its Fresnel fringes and diffraction
    dx = min(a / 200.0, np.sqrt(2.0 * np.pi * z0 / k) / 20.0)
    xs = np.arange(sl.min() - spread, sl.max() + spread + dx, dx)
    if xs.size > 400000:
        xs = np.linspace(sl.min() - spread, sl.max() + spread, 400000)
    A = slit_amplitudes(xs[None, :], z0, k, sl, a, L1)
    rho = np.einsum("jx,lx,jl->x", A[0], A[0].conj(), np.asarray(G)).real
    rho = np.maximum(rho, 0.0)
    cdf = np.concatenate([[0.0], np.cumsum(0.5 * (rho[1:] + rho[:-1]) * np.diff(xs))])
    if cdf[-1] <= 0:
        return None
    x = np.interp((np.arange(n) + 0.5) / n * cdf[-1], cdf, xs)
    zs = z0 * (z_max / z0) ** np.linspace(0.0, 1.0, n_steps + 1)
    out = np.empty((n_steps + 1, n))
    out[0] = x

    def vel(xx, zz):
        A, dA = slit_amplitudes(xx[:, None], zz, k, slits, a, L1, deriv=True)
        num, den = current(A, dA, G)
        return (num / np.maximum(den, 1e-300))[:, 0] / k

    for i in range(n_steps):
        z, h = zs[i], zs[i + 1] - zs[i]
        k1 = vel(x, z)
        k2 = vel(x + 0.5 * h * k1, z + 0.5 * h)
        k3 = vel(x + 0.5 * h * k2, z + 0.5 * h)
        k4 = vel(x + h * k3, z + h)
        x = x + h / 6.0 * (k1 + 2 * k2 + 2 * k3 + k4)
        out[i + 1] = x
    return {"z": zs, "x": out}


def velocity_1d(grid, psi, floor: float = 1e-30):
    """Guidance velocity v = j / |psi|^2 on the grid of a lfphys.core.quantum.schrodinger1d.Grid."""
    rho = np.abs(psi) ** 2
    return grid.current(psi) / np.maximum(rho, floor * rho.max())


def advance_1d(xs, grid, psi_a, psi_b, dt: float):
    """Move particles xs over dt with the velocity field of psi(t) and psi(t + dt) (Heun's rule, linear
    interpolation on the grid)."""
    va = velocity_1d(grid, psi_a)
    vb = velocity_1d(grid, psi_b)
    x1 = xs + dt * np.interp(xs, grid.x, va)
    return xs + 0.5 * dt * (np.interp(xs, grid.x, va) + np.interp(x1, grid.x, vb))


def quantile_positions(x, rho, absorbed_left: float, q):
    """1-D Bohm trajectories without integration: in one dimension trajectories do not cross, so the probability to
    the left of a trajectory is conserved, d/dt int_{-inf}^{x(t)} |psi|^2 dx = rho v - j = 0, and the trajectory that
    starts at quantile q stays at the q-quantile of |psi(t)|^2. With absorbing detectors the mass they absorbed counts
    as lying beyond the window: F(x) = absorbed_left + int_{x_min}^{x} |psi|^2. Returns positions, with -inf / +inf
    for trajectories already absorbed on the left / right."""
    dx = x[1] - x[0]
    F = absorbed_left + np.cumsum(rho) * dx
    q = np.asarray(q, float)
    pos = np.interp(q, F, x)
    pos = np.where(q < F[0], -np.inf, pos)
    return np.where(q > F[-1], np.inf, pos)


# --- time-dependent waves in 2-D and 3-D (plan P6, P14.4) -------------------------------------------------------------
def velocity_nd(grid, psi, X, H=None, order: int = 8, xp=None):
    """The guidance velocity at points X (N, ndim) of a wave psi on a ``schrodinger_nd.Grid`` (spinors (2, *shape):
    summed over the components): v = (hbar/m) Im(psi^dag grad psi) / (psi^dag psi) - (q/m) A, with psi and its
    gradient interpolated from the grid (``schrodinger_nd.sample``, Lagrange through ``order`` samples per axis).
    Returns (v (N, ndim), rho (N,)) as NumPy arrays; where rho = 0 (a node) v is 0."""
    xp = xp or np
    vals, grads = (np.asarray(SND.backend.to_numpy(a)) for a in SND.sample(grid, psi, X, order, xp, host_ok=True))
    num = np.imag(np.sum(np.conj(vals)[:, None, :] * grads, axis=0))  # (ndim, N)
    den = np.sum(vals.real**2 + vals.imag**2, axis=0)
    v = np.where(den > 0, grid.hbar / grid.m * num / np.where(den > 0, den, 1.0), 0.0).T
    if H is not None and H.A is not None:
        v = v - H.q / grid.m * H.A.at(X)
    return v, den


def rk4(X, h: float, vel):
    """One fourth-order Runge-Kutta step of dX/dt = v(X, t) over h; ``vel(X, f)`` gives the velocity at the fraction f
    in {0, 1/2, 1} of the step (for a wave known at t, t + h/2 and t + h: two steps of its split operator)."""
    k1 = vel(X, 0.0)
    k2 = vel(X + 0.5 * h * k1, 0.5)
    k3 = vel(X + 0.5 * h * k2, 0.5)
    k4 = vel(X + h * k3, 1.0)
    return X + h / 6.0 * (k1 + 2 * k2 + 2 * k3 + k4)


def _velocity_from_samples(grid, samples, w, X, H):
    """v at points from psi and grad psi sampled at three times, combined with the weights w (Lagrange in time)."""
    xp_vals = sum(wi * s[0] for wi, s in zip(w, samples))
    xp_grads = sum(wi * s[1] for wi, s in zip(w, samples))
    num = np.imag(np.sum(np.conj(xp_vals)[:, None, :] * xp_grads, axis=0))
    den = np.sum(xp_vals.real**2 + xp_vals.imag**2, axis=0)
    v = np.where(den > 0, grid.hbar / grid.m * num / np.where(den > 0, den, 1.0), 0.0).T
    if H is not None and H.A is not None:
        v = v - H.q / grid.m * H.A.at(X)
    return v


PATCH_MAX = 64   # advance_ensemble: at most this many particles are stepped on the host from copied patches
PATCH_R = 8      # a patch spans 2 PATCH_R + 1 samples per axis around a particle (a stencil needs 9)


class _Patches:
    """Copies of the grid around a few particles (all snapshots, all components), so that their many small steps are
    interpolated on the host; a particle that leaves the inner part of its patch gets a new one."""

    def __init__(self, grid, stack, order):
        self.grid, self.stack, self.order = grid, stack, order
        self.n = order + 1
        self.P = 2 * max(PATCH_R, order // 2 + 4) + 1  # a higher order (the control of p02: 16) gets a wider patch
        self.store, self.lo, self.owner = None, None, {}

    def ensure(self, ids, Z):
        g, P, n = self.grid, self.P, self.n
        rows = np.array([self.owner.get(int(i), -1) for i in ids])
        need = rows < 0
        if self.store is not None and np.any(~need):  # still inside the inner part (a full stencil left)?
            u = (Z[~need] - self.lo[rows[~need]]) / g.d - 0.5
            inside = np.all((u >= self.n // 2) & (u <= P - 1 - self.n // 2), axis=1)
            need[np.flatnonzero(~need)[~inside]] = True
        if np.any(need):
            centre = np.rint((Z[need] - np.array([a[0] for a in g.axes])) / g.d).astype(np.int64)
            i0 = np.clip(centre - P // 2, 0, np.array(g.shape) - P)
            idx = np.zeros((len(i0),) + (P,) * g.ndim, np.int64)
            stride = 1
            for ax in reversed(range(g.ndim)):
                shape = [len(i0)] + [1] * g.ndim
                shape[ax + 1] = P
                idx = idx + ((i0[:, ax][:, None] + np.arange(P)[None, :]) * stride).reshape(shape)
                stride *= g.shape[ax]
            nc = self.stack.shape[0]
            xp = SND.backend
            new = np.asarray(xp.to_numpy(self.stack.reshape(nc, -1)[:, _xp_asarray(self.stack, idx.reshape(-1))]))
            new = new.reshape((nc, len(i0)) + (P,) * g.ndim)
            lo = np.array([a[0] for a in g.axes]) + i0 * g.d
            base = 0 if self.store is None else self.store.shape[1]
            self.store = new if self.store is None else np.concatenate([self.store, new], axis=1)
            self.lo = lo if self.lo is None else np.concatenate([self.lo, lo])
            for k, i in enumerate(np.asarray(ids)[need]):
                self.owner[int(i)] = base + k
            rows = np.array([self.owner[int(i)] for i in ids])
        return rows

    def sample(self, rows, Z, carrier=None):
        """psi and grad psi of every stored component at points Z from their patches (the same stencils and weights
        as ``schrodinger_nd.sample``, with its ``carrier``)."""
        g, n, P = self.grid, self.n, self.P
        F = len(rows)
        W, DW, sel = [], [], []
        for ax in range(g.ndim):
            u = (Z[:, ax] - self.lo[rows, ax]) / g.d[ax]
            i0 = np.clip(np.floor(u + 0.5).astype(np.int64) - self.order // 2, 0, P - n)
            w, dw = SND.lagrange_weights(u - i0, n, deriv=True)
            dw = dw / g.d[ax]
            if carrier is not None:
                w, dw = SND.demodulated(w, dw, u - i0, carrier[:, ax], g.d[ax])
            W.append(w)
            DW.append(dw)
            shape = [F] + [1] * g.ndim
            shape[ax + 1] = n
            sel.append((i0[:, None] + np.arange(n)[None, :]).reshape(shape))
        T = self.store[(slice(None), rows.reshape((F,) + (1,) * g.ndim)) + tuple(sel)]  # (nc, F, n, ..., n)
        letters = "defghij"[:g.ndim]  # not "c" or "n" (as schrodinger_nd.sample; B6 finding)
        spec = "cn" + letters + "," + ",".join("n" + L for L in letters) + "->cn"
        vals = np.einsum(spec, T, *W)
        grads = np.stack([np.einsum(spec, T, *[DW[a] if a == i else W[a] for a in range(g.ndim)])
                          for i in range(g.ndim)], axis=1)
        return vals, grads


def _xp_asarray(like, a):
    """``a`` on the device of ``like`` (NumPy or CuPy)."""
    if isinstance(like, np.ndarray):
        return np.asarray(a)
    import cupy
    return cupy.asarray(a)


# Dormand & Prince's embedded Runge-Kutta pair 5(4) (J. Comput. Appl. Math. 6, 19 (1980)): nodes, coefficients, the
# fifth-order weights and the difference to the fourth-order ones (the error estimate); the last stage is the next
# step's first (FSAL)
_DP_C = (0.0, 1 / 5, 3 / 10, 4 / 5, 8 / 9, 1.0, 1.0)
_DP_A = ((),
         (1 / 5,),
         (3 / 40, 9 / 40),
         (44 / 45, -56 / 15, 32 / 9),
         (19372 / 6561, -25360 / 2187, 64448 / 6561, -212 / 729),
         (9017 / 3168, -355 / 33, 46732 / 5247, 49 / 176, -5103 / 18656),
         (35 / 384, 0.0, 500 / 1113, 125 / 192, -2187 / 6784, 11 / 84))
_DP_B5 = (35 / 384, 0.0, 500 / 1113, 125 / 192, -2187 / 6784, 11 / 84, 0.0)
_DP_E = (71 / 57600, 0.0, -71 / 16695, 71 / 1920, -17253 / 339200, 22 / 525, -1 / 40)  # b5 - b4


def carriers(grid, psi, X):
    """The carrier wavevector per point and axis for demodulated interpolation (``schrodinger_nd.sample``, review
    B6-Q1), from the samples around the nearest node j: kappa_a = the circular mean of the phase steps
    arg(psi_{j+1} psi_j^*) and arg(psi_j psi_{j-1}^*) along axis a (summed over spinor components; unique while
    |k_a| d < pi, which the scene's admission rule keeps), used on that axis where it makes the samples smoother: the
    second difference of the demodulated samples psi_{j+-1} e^{-+i kappa d} - 2 psi_j + ... at most a quarter of that
    of psi itself (scaled down to none as the two become equal) — so a propagating wave is demodulated by its local
    wavevector, while near a node (where the phase winds and psi is locally a smooth polynomial) the plain
    interpolation stays. Any carrier keeps the interpolation exact on the samples; the choice sets whose remainder
    applies. Returns (N, ndim) on the host."""
    p = psi if psi.ndim == grid.ndim + 1 else psi[None]
    nc = p.shape[0]
    X = np.asarray(SND.backend.to_numpy(X), float)
    N, d = X.shape
    idx = [np.clip(np.rint((X[:, a] - grid.axes[a][0]) / grid.d[a]).astype(np.int64), 1, grid.shape[a] - 2)
           for a in range(d)]
    flat = p.reshape(nc, -1)

    def at(a=None, off=0):
        ii = [ix + (off if b == a else 0) for b, ix in enumerate(idx)]
        f = np.ravel_multi_index(ii, grid.shape)
        v = flat[:, _xp_asarray(p, f)]
        return v if isinstance(v, np.ndarray) else v.get()  # a CuPy gather comes to the host

    c = at()
    out = np.zeros((N, d))
    for a in range(d):
        up, dn = at(a, 1), at(a, -1)
        zf = np.sum(up * np.conj(c), axis=0)
        zb = np.sum(c * np.conj(dn), axis=0)
        th = np.angle(zf / np.maximum(np.abs(zf), 1e-300) + zb / np.maximum(np.abs(zb), 1e-300))
        ph = np.exp(1j * th)
        plain = np.sum(np.abs(up - 2 * c + dn) ** 2, axis=0)
        demod = np.sum(np.abs(up * np.conj(ph) - 2 * c + dn * ph) ** 2, axis=0)
        # the carrier in full where it makes the samples clearly smoother (demod <= plain / 4), none where it does not
        # (demod >= plain), scaled in between: a point and its neighbour (or its control) never switch abruptly between
        # two interpolants
        r = demod / np.maximum(plain, 1e-300)
        out[:, a] = np.clip((1.0 - r) / 0.75, 0.0, 1.0) * th / grid.d[a]
    return out


def advance_ensemble(grid, snaps, X, h: float, H=None, order: int = 8, xp=None, rtol: float = 1e-5,
                     atol: float | None = None, max_disp: float | None = None, max_sub: int = 4096,
                     demodulate: bool = True):
    """Advance trajectories X (N, ndim) over h in a wave known at three times (``snaps``: psi at t, t + h/2, t + h; in
    between, psi and grad psi at a particle are quadratic in time through them, exact at the snapshots), with error
    control per particle: Dormand-Prince 5(4) steps, each accepted when its error estimate is at most
    atol + rtol |displacement| (atol default 1e-6 of the grid step) and the particle moved at most ``max_disp`` (default
    one grid step), the next step size from the usual (tol / err)^(1/5) rule. The error is measured against the step's
    own displacement: a particle circling a node of the wave (where Bohm's velocities grow without bound) keeps the same
    relative accuracy on every turn, however small its circle (an absolute tolerance let it spiral in: tests); it takes
    as many small steps as it needs (at most ``max_sub`` per h), a particle in smooth flow one step. Review B3-4: with a
    fixed rule a few per cent of the trajectories were not converged (hits up to two fringes away). The error control
    covers the time integration; the interpolation of psi in space (``schrodinger_nd.sample``, Lagrange of ``order``)
    errs by its remainder at the wave's local k d — 1e-3 of the velocity at k d = 1, 0.13 at k d = 2 (review B6-Q1).
    With ``demodulate`` each point is interpolated with the carrier of its local wavevector at the interval's start
    (``carriers``): exact on the samples, the remainder then set by the local spread of wavenumbers, not by k d
    (measured on free packets: the trajectories' error stays at the integrator's tolerance up to k d = 2.8). Returns
    (X_new, steps taken (N,))."""
    xp = xp or np
    X = np.array(X, float)
    N = len(X)
    step = float(min(grid.d))
    max_disp = float(max_disp if max_disp is not None else step)
    atol = float(atol if atol is not None else 1e-6 * step)
    nc = 1 if snaps[0].ndim == grid.ndim else snaps[0].shape[0]
    stack = xp.concatenate([sn if sn.ndim == grid.ndim + 1 else sn[None] for sn in snaps])

    def combine(vals, grads, f, Z):
        """The guidance velocity from psi, grad psi of the three snapshots at the fractions f (per point) of h."""
        w = (2 * (f - 0.5) * (f - 1.0), -4 * f * (f - 1.0), 2 * f * (f - 0.5))  # Lagrange on 0, 1/2, 1
        v = sum(w[k] * vals[k * nc:(k + 1) * nc] for k in range(3))
        g = sum(w[k][None, :] * grads[k * nc:(k + 1) * nc] for k in range(3))
        num = np.imag(np.sum(np.conj(v)[:, None, :] * g, axis=0))
        den = np.sum(v.real**2 + v.imag**2, axis=0)
        out = np.where(den > 0, grid.hbar / grid.m * num / np.where(den > 0, den, 1.0), 0.0).T
        if H is not None and H.A is not None:
            out = out - H.q / grid.m * H.A.at(Z)
        return out

    def raw(Z, rows=None, kc=None):
        """psi and grad psi of the three snapshots at points Z: from the grid on the device, or for the few
        slow-to-converge particles from their patches on the host (``rows``: their rows in the patch store); ``kc``
        the points' carriers (None: plain interpolation)."""
        if rows is None:
            return (np.asarray(SND.backend.to_numpy(a)) for a in SND.sample(grid, stack, Z, order, xp, host_ok=True,
                                                                             carrier=kc))
        return patches.sample(rows, Z, kc)

    def vel(Z, f, rows=None, kc=None):
        if not len(Z):
            return np.zeros((0, grid.ndim))
        vals, grads = raw(Z, rows, kc)
        return combine(vals, grads, f, Z)

    patches = _Patches(grid, stack, order)
    s = np.zeros(N)                      # the fraction of h done
    kap = carriers(grid, snaps[0], X) if (demodulate and N) else None
    if kap is not None and not np.any(kap != 0):
        kap = None
    k1 = vel(X, s, None, kap)
    sp = np.linalg.norm(k1, axis=1)
    hs = np.minimum(1.0, max_disp / np.maximum(sp * h, 1e-300))  # the first try: the whole step if slow enough
    steps = np.zeros(N, int)
    hmin = 1.0 / max_sub
    act = np.arange(N)
    while len(act):
        # once few particles are left (those near nodes, which take many small steps), their surroundings are copied
        # to the host once and they are stepped there: one device call instead of six per step
        rows = patches.ensure(act, X[act]) if len(act) <= PATCH_MAX else None
        Xa, sa, ha, K = X[act], s[act], np.minimum(hs[act], 1.0 - s[act]), [k1[act]]
        for i in range(1, 7):
            Y = Xa + h * ha[:, None] * sum(_DP_A[i][j] * K[j] for j in range(i))
            K.append(vel(Y, sa + _DP_C[i] * ha, rows, None if kap is None else kap[act]))
        Y5 = Xa + h * ha[:, None] * sum(_DP_B5[j] * K[j] for j in range(7))
        err = np.linalg.norm(h * ha[:, None] * sum(_DP_E[j] * K[j] for j in range(7)), axis=1)
        disp = np.linalg.norm(Y5 - Xa, axis=1)
        tol = atol + rtol * disp
        ok = ((err <= tol) & (disp <= max_disp)) | (ha <= hmin * (1 + 1e-9))
        acc = act[ok]
        X[acc], s[acc], k1[acc] = Y5[ok], sa[ok] + ha[ok], K[6][ok]  # FSAL: the last stage is at the new point
        steps[acc] += 1
        fac = np.clip(0.9 * (tol / np.maximum(err, 1e-300)) ** 0.2, 0.2, 5.0)
        fac = np.minimum(fac, np.where(disp > 0, max_disp / np.maximum(disp, 1e-300), 5.0))
        hs[act] = np.maximum(hmin, ha * fac)
        act = act[(s[act] < 1.0 - 1e-12)]
    return X, steps


def gaussian_trajectory(x_start, t: float, center, k0, sigma, m: float = 1.0, hbar: float = 1.0):
    """The exact Bohm trajectory in a free Gaussian packet (``schrodinger_nd.Grid.gaussian``), per axis:
    x(t) = x0 + v t + (x_start - x0) |s_t| / sigma, |s_t| = sigma sqrt(1 + (hbar t / (2 m sigma^2))^2): the
    trajectories scale with the packet's width (each keeps its quantile)."""
    x_start = np.asarray(x_start, float)
    c, k, s = (np.broadcast_to(np.asarray(a, float), x_start.shape[-1:]) for a in (center, k0, sigma))
    st = s * np.sqrt(1.0 + (hbar * t / (2 * m * s * s)) ** 2)
    return c + hbar * k / m * t + (x_start - c) * st / s
