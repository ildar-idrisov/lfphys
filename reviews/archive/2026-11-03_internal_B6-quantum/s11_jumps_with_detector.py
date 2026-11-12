"""Q: the localization unravelling together with a detector (the split of each step's loss into the detectors' part,
kept as absorbed probability, and Gamma/2's part, restored; the hazard ln((n0 - dA)/n1)) — derived in the verification
file (§3 (b)) but tested only by the balance norm + absorbed = 1. Independent route: the master equation of the
in-flight density matrix with the detector as -i W in H_eff,
    d rho/dt = -i (H rho - rho H) - (W(r) + W(r')) rho + [lambda K(r, r') - (Gamma(r) + Gamma(r'))/2] rho,
    dA/dt = 2 sum_r W(r) rho(r, r),
integrated directly (DOP853, rtol 1e-11), against the average over M trajectories of the scene's unnormalised
in-flight states (E[|psi><psi|] = rho_flight) and of their absorbed probabilities. The test's set-up (1-D trap, cat
state, lambda = 1, a = 0.8, region x > 0) plus a detector W0 = 0.6 on x in [1.5, 3.5] (edge 0.8), inside the region:
the right lump sits in both. z-scores of: in-flight norm, P_left, x^2/64, cos 5x (unnormalised), the cat fidelity, A."""
import math
import numpy as np
from scipy import integrate
from lfphys.core.quantum import scene as Q
import scipy.constants as sc

M1 = Q.species("atom", mass_u=sc.m_e / sc.atomic_mass)


def run(M=800, lam_ref=1.0, W_ref=1.0, seed=3):
    N, d, lam, a = 64, 0.25, 1.0, 0.8
    T = math.pi / 2
    s = Q.Scene((N,), d, dt=T / 100, seed=seed)
    s.add(Q.HarmonicTrap([0.0], [1.0]))
    s.add(Q.Localization(lam, a, lo=[0.0], hi=[None], edge=0.8))
    det = s.add(Q.Detector([1.5], [3.5], 0.6, 0.8))
    g = s.grid
    x = g.axes[0]
    cat = np.exp(-(x - 2.5) ** 2) + np.exp(-(x + 2.5) ** 2)
    cat = cat / math.sqrt(g.norm(cat))
    pids = []
    for _ in range(M):
        pid = s.add_particle(Q.Packet(M1, [0.0], [0.0], [0.5]))
        s.set_wave(pid, cat)
        pids.append(pid)
    obs = {"P_left": (x < 0).astype(float), "x2": x**2 / 64.0, "cos": np.cos(5.0 * x)}

    def values():
        out = {k: [] for k in list(obs) + ["norm", "F_cat", "A"]}
        for pid in pids:
            psi = s.wave(pid)
            rho = np.abs(psi) ** 2 * g.dV
            out["norm"].append(float(np.sum(rho)))
            for k, o in obs.items():
                out[k].append(float(np.sum(rho * o)))
            out["F_cat"].append(abs(np.sum(np.conj(cat) * psi) * g.dV) ** 2)
            out["A"].append(s.absorbed(pid).get(f"detector {det}", 0.0))
        return {k: np.array(v) for k, v in out.items()}
    traj = []
    for _ in range(2):
        s.advance(50)
        traj.append(values())
    bal = max(abs(r["balance"]) for r in s.checks().values())
    H = s.hamiltonian(s._key(s.particles[pids[0]]))
    Hm = np.array([H.apply(e) for e in np.eye(N, dtype=complex)]).T
    W = s._arr["W_parts"][f"detector {det}"] * W_ref
    lr = lam * lam_ref
    w_tot = 2 * Q.ERF80 * math.sqrt(Q.edge_eps(0.8) ** 2 + a * a)
    chi = lambda z: Q.smooth_interval(z, 0.0, None, w_tot)  # noqa: E731
    D = (lr * np.exp(-(x[:, None] - x[None, :]) ** 2 / (4 * a * a)) * chi(0.5 * (x[:, None] + x[None, :]))
         - 0.5 * lr * (chi(x)[:, None] + chi(x)[None, :]) - (W[:, None] + W[None, :]))
    rho0 = (np.outer(cat, cat) * g.dV).astype(complex)

    def f(t, y):
        r = y[:-1].view(complex).reshape(N, N)
        dr = (-1j * (Hm @ r - r @ Hm) + D * r).ravel().view(float)
        return np.concatenate([dr, [2 * float(np.sum(W * np.real(np.diag(r))))]])
    y0 = np.concatenate([rho0.ravel().view(float), [0.0]])
    sol = integrate.solve_ivp(f, (0, T), y0, method="DOP853", rtol=1e-11, atol=1e-13, t_eval=[T / 2, T])
    z = {}
    for j in range(2):
        r = np.ascontiguousarray(sol.y[:-1, j]).view(complex).reshape(N, N)
        ref = {k: float(np.real(np.sum(np.diag(r) * o))) for k, o in obs.items()}
        ref["norm"] = float(np.real(np.trace(r)))
        ref["F_cat"] = float(np.real(cat @ r @ cat) * g.dV)
        ref["A"] = float(sol.y[-1, j])
        for k, v in traj[j].items():
            z[(k, j)] = ((v.mean() - ref[k]) / (v.std(ddof=1) / math.sqrt(M)), v.mean(), ref[k])
    jumps = float(np.mean([len(s.particles[p].jumps) for p in pids]))
    return z, jumps, bal


z, jumps, bal = run()
print(f"mean jumps per trajectory {jumps:.3f}; max |balance| {bal:.1e}")
for (k, j), (zz, m, r) in sorted(z.items(), key=lambda kv: (kv[0][1], kv[0][0])):
    print(f"  t = T/{2 if j == 0 else 1}  {k:6s}: trajectories {m:.6f}  master eq. {r:.6f}  z = {zz:+.2f}")
print(f"max |z| = {max(abs(v[0]) for v in z.values()):.2f}")
z2, _, _ = run(lam_ref=1.0, W_ref=0.7)
print(f"negative control (master equation with 0.7 W): max |z| = {max(abs(v[0]) for v in z2.values()):.2f}")
