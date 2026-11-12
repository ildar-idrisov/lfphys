"""P5 + P7 review, check 4: negative controls. Each mutation changes one coefficient or sign in a COPY of the engine
(made inside the container under /tmp/mut; the repository is mounted read-only and never touched) and runs the test
files that should catch it. A mutation that leaves the tests passing is a hole in the tests (or a harmless change,
noted per row).

Run: python3 s04_negative_controls.py [--only P5|P7]
"""
import argparse
import os
import shutil
import subprocess
import sys
import time

SRC = "/lf/lfphys"
DST = "/tmp/mut"

QT = "lfphys/core/quantum/"
GR = "lfphys/core/gravity/"
PMF = "lfphys/theories/approx/peters_mathews.py"
T5 = ["tests/test_open_systems.py"]
T7 = ["tests/test_pn_binary.py", "tests/test_gw_quadrupole.py", "tests/test_peters_mathews.py"]

MUT = [
    # P5
    ("P5", "dissipator anticommutator 1/2 -> 0.49", QT + "open_systems.py",
     "return sprepost(L, L.conj().T) - 0.5 * (spre(LdL) + spost(LdL))",
     "return sprepost(L, L.conj().T) - 0.49 * (spre(LdL) + spost(LdL))", T5),
    ("P5", "Magnus commutator coefficient x1.05", QT + "open_systems.py",
     "_K = math.sqrt(3.0) / 12.0", "_K = 1.05 * math.sqrt(3.0) / 12.0", T5),
    ("P5", "Richardson divisor 15 -> 150 (error estimate 10x too small)", QT + "open_systems.py",
     "est = trace_norm(unvec(half - full, d)) / 15.0", "est = trace_norm(unvec(half - full, d)) / 150.0", T5),
    ("P5", "dephasing jump operator sqrt(gc/2) -> sqrt(gc)", QT + "two_level.py",
     "out.append(math.sqrt(0.5 * gc) * SZ)", "out.append(math.sqrt(gc) * SZ)", T5),
    ("P5", "steady state v: G1 gp -> G1 gp * 1.01", QT + "two_level.py",
     "Omega * G1 * gp / D,", "Omega * G1 * gp * 1.01 / D,", T5),
    ("P5", "Torrey resonance: delta sign", QT + "two_level.py",
     "kappa, delta = 0.5 * (gp + G1), 0.5 * (gp - G1)", "kappa, delta = 0.5 * (gp + G1), 0.5 * (G1 - gp)", T5),
    ("P5", "waiting-time c_e amplitude x1.001", QT + "two_level.py",
     "return -0.5j * Omega * sh, ch - sbar * sh", "return -0.5005j * Omega * sh, ch - sbar * sh", T5),
    ("P5", "jump channel weights |L psi| instead of |L psi|^2", QT + "jumps.py",
     "w = np.stack([np.sum(np.abs(phi @ L.T) ** 2, axis=1) for L in c_ops], axis=1)",
     "w = np.stack([np.sqrt(np.sum(np.abs(phi @ L.T) ** 2, axis=1)) for L in c_ops], axis=1)", T5),
    ("P5", "jump thresholds not rescaled after renormalisation", QT + "jumps.py",
     "        r = r / nn\n", "        r = r\n", T5),
    ("P5", "Gaussian kick overlap 4a^2 -> 2a^2", QT + "decoherence.py",
     "return np.exp(-d * d / (4.0 * a * a))", "return np.exp(-d * d / (2.0 * a * a))", T5),
    # P7
    ("P7", "2PN A: 87/4 -> 88/4", GR + "pn_binary.py", "(9.0 + 87.0 / 4.0 * nu)", "(9.0 + 88.0 / 4.0 * nu)", T7),
    ("P7", "2.5PN A: -17/3 -> -16/3", GR + "pn_binary.py", "(-17.0 / 3.0 * g - 3.0 * v2)",
     "(-16.0 / 3.0 * g - 3.0 * v2)", T7),
    ("P7", "3.5PN A: 112 rdot^4 -> 113", GR + "pn_binary.py", "+ 112.0 * rd2 * rd2)", "+ 113.0 * rd2 * rd2)", T7),
    ("P7", "3.5PN A: 3956/35 -> 3946/35", GR + "pn_binary.py", "(3956.0 / 35.0 + 184.0 / 5.0 * nu)",
     "(3946.0 / 35.0 + 184.0 / 5.0 * nu)", T7),
    ("P7", "3.5PN B: -120 rdot^4 -> -119", GR + "pn_binary.py", "- 120.0 * rd2 * rd2)", "- 119.0 * rd2 * rd2)", T7),
    ("P7", "3.5PN B: -1060/21 -> -1050/21", GR + "pn_binary.py", "(-1060.0 / 21.0 - 104.0 / 5.0 * nu)",
     "(-1050.0 / 21.0 - 104.0 / 5.0 * nu)", T7),
    ("P7", "3.5PN B: 678/5 + 12/5 nu -> 678/5 + 13/5 nu", GR + "pn_binary.py", "(678.0 / 5.0 + 12.0 / 5.0 * nu)",
     "(678.0 / 5.0 + 13.0 / 5.0 * nu)", T7),
    ("P7", "3.5PN A: 184/5 nu -> 180/5 nu (nu^2 part of the G^3 term)", GR + "pn_binary.py",
     "(3956.0 / 35.0 + 184.0 / 5.0 * nu)", "(3956.0 / 35.0 + 180.0 / 5.0 * nu)", T7),
    ("P7", "E_2PN: 27 nu^2 -> 26 nu^2", GR + "pn_binary.py", "(21.0 - 23.0 * nu - 27.0 * nu**2)",
     "(21.0 - 23.0 * nu - 26.0 * nu**2)", T7),
    ("P7", "K(eps, j): 15/j^2 (7 - 2 nu) -> (7 - nu)", GR + "pn_binary.py", "15.0 / (j * j) * (7.0 - 2.0 * nu)",
     "15.0 / (j * j) * (7.0 - 1.0 * nu)", T7),
    ("P7", "n(eps, j): 555 -> 556", GR + "pn_binary.py", "c2 = 555.0 +", "c2 = 556.0 +", T7),
    ("P7", "x(eps, j): 2/j -> 1.9/j", GR + "pn_binary.py", "nu / 12.0 + 2.0 / j", "nu / 12.0 + 1.9 / j", T7),
    ("P7", "e_t: 17 - 7 nu -> 17 - 6 nu", GR + "pn_binary.py", "j * (17.0 - 7.0 * nu)", "j * (17.0 - 6.0 * nu)", T7),
    ("P7", "circular inspiral rate: -1751/336 -> -1700/336", GR + "pn_binary.py", "c1 = (-1751.0 / 336.0",
     "c1 = (-1700.0 / 336.0", T7),
    ("P7", "1PN CM positions: m/(2r) -> 0.45 m/r", GR + "pn_binary.py", "Pc = 0.5 * np.sum(v * v, axis=-1) - 0.5 / r",
     "Pc = 0.5 * np.sum(v * v, axis=-1) - 0.45 / r", T7),
    ("P7", "elements route: drop v x (x x f) in dA/dt (x-component)", GR + "pn_binary.py",
     "return np.array([L, h * fy + L * VY,", "return np.array([L, h * fy,", T7),
    ("P7", "GW angular momentum flux 2/5 -> 0.41", GR + "gw_quadrupole.py", "return 0.4 * np.einsum(",
     "return 0.41 * np.einsum(", T7),
    ("P7", "polarisation vector P -> -P (with Q = N x P: a no-op, h+ and hx invariant under a rotation by pi)",
     GR + "gw_quadrupole.py", "P = np.array([math.sin(Phi), -math.cos(Phi), 0.0])",
     "P = -np.array([math.sin(Phi), -math.cos(Phi), 0.0])", T7),
    ("P7", "left-handed triad Q = P x N (hx sign)", GR + "gw_quadrupole.py", "return N, P, np.cross(N, P)",
     "return N, P, np.cross(P, N)", T7),
    ("P7", "Peters de/dt: 121/304 -> 121/300", PMF, "* (1.0 + 121.0 / 304.0 * e2) / (1.0 - e2) ** 2.5)",
     "* (1.0 + 121.0 / 300.0 * e2) / (1.0 - e2) ** 2.5)", T7),
    ("P7", "omega_dot: 3 -> 3.003 (1e-3)", PMF, "return 3.0 * (gm1 + gm2)", "return 3.003 * (gm1 + gm2)", T7),
    ("P7", "Einstein gamma: m1 + 2 m2 -> 2 m1 + m2 (pulsar/companion swapped)", PMF, "gm2 * (gm1 + 2.0 * gm2)",
     "gm2 * (2.0 * gm1 + gm2)", T7),
    ("P7", "data: Pb_dot^GR -2.40263 -> -2.40273 (2 sigma)", "lfphys/core/data.py",
     "PSR_B1913_PBDOT_GR = (-2.40263e-12,", "PSR_B1913_PBDOT_GR = (-2.40273e-12,", T7),
]


def run(tests):
    env = dict(os.environ, PYTHONPATH=DST, PYTHONDONTWRITEBYTECODE="1")
    p = subprocess.run([sys.executable, "-m", "pytest", "-x", "-q", "-p", "no:cacheprovider", *tests], cwd=DST,
                       env=env, capture_output=True, text=True)
    tail = [ln for ln in p.stdout.splitlines() if ln.strip()][-1:] or [""]
    first_fail = next((ln for ln in p.stdout.splitlines() if ln.startswith("FAILED")), "")
    return p.returncode, tail[0], first_fail


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--only", choices=["P5", "P7"])
    ap.add_argument("--match", default="", help="run only the mutations whose name contains this text")
    args = ap.parse_args()
    if os.path.exists(DST):
        shutil.rmtree(DST)
    shutil.copytree(SRC, DST, ignore=shutil.ignore_patterns("__pycache__", "external"))
    for item, name, path, old, new, tests in MUT:
        if (args.only and item != args.only) or args.match not in name:
            continue
        f = os.path.join(DST, path)
        orig = open(f).read()
        assert orig.count(old) == 1, (name, orig.count(old))
        open(f, "w").write(orig.replace(old, new))
        t0 = time.time()
        rc, tail, ff = run(tests)
        open(f, "w").write(orig)
        verdict = "CAUGHT" if rc != 0 else "NOT CAUGHT"
        print(f"[{item}] {name}: {verdict} ({time.time()-t0:.0f} s) {tail} {ff}", flush=True)


if __name__ == "__main__":
    main()
