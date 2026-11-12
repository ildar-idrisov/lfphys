# Review B5, check c10: negative controls. Each mutation is applied to a COPY of engine/lfphys (never to the
# repository) and the in-scope tests are run against the copy: test_kerr_null, test_kerr_shadow, test_johannsen_metric,
# test_kerr_orbits and v15's tests. A mutation that no test catches is a gap.
#
# Run on the host (it only copies files and starts containers); the copies go to the scratch folder given as argv[1]:
#   python3 c10_mutations.py <scratch>/mut > out/c10_mutations.txt
# Each test run: docker run --rm light-funnel-viz with the engine mounted read-only at /lf and the mutated copy mounted
# read-only over /lf/lfphys; CPU only.
import os
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

ENGINE = "/home/ildar/hdd/projects/i/light-funnel/engine"
KN = "lfphys/core/gravity/kerr_null.py"
KS = "lfphys/core/gravity/kerr_shadow.py"
JPM = "lfphys/theories/alternatives/johannsen_metric.py"
KO = "lfphys/core/gravity/kerr_orbits.py"

MUTATIONS = {
    # the sign of the photon's p^r at crossings after the radial turning point (redshift of the n >= 1 images)
    "M1_kr_always_out": (KN, "kr = xp.where(valid, xp.where(scatter & (tn > tau_turn), -1.0, 1.0), xp.nan)",
                         "kr = xp.where(valid, 1.0, xp.nan)"),
    # the extra half-libration of rays arriving with beta > 0 (GL-b Eq. 82) dropped
    "M2_no_heaviside": (KN, "H = xp.where(b_eff > 0.0, 1.0, 0.0)", "H = xp.zeros_like(b_eff)"),
    # the radial term of the redshift with the wrong sign
    "M3_redshift_radial_sign": (KS, "return 1.0 / (ut - lam * up - pr * ur)", "return 1.0 / (ut - lam * up + pr * ur)"),
    # the Lyapunov exponent per orbit instead of per half-orbit
    "M4_lyapunov_x2": (KN, "return 4.0 * np.sqrt(chi_t) * EL.ellipk(pol[\"m\"]) / np.sqrt(pol[\"A_m\"])",
                       "return 8.0 * np.sqrt(chi_t) * EL.ellipk(pol[\"m\"]) / np.sqrt(pol[\"A_m\"])"),
    # the screen mirrored left-right, consistently everywhere (alpha = +lambda/sin): the approaching side of the disk
    # would appear on the right
    "M5_mirror_alpha": (KN, "return -alpha * s, (alpha * alpha - a * a) * c * c + beta * beta",
                        "return alpha * s, (alpha * alpha - a * a) * c * c + beta * beta",
                        "return -lam / math.sin(theta_o), sign_beta",
                        "return lam / math.sin(theta_o), sign_beta",
                        "    al = -lam / s\n    be = np.sqrt(np.maximum(eta + a * a * c * c - lam * lam * c * c / (s * s), 0.0))\n    alpha = np.concatenate((al, al[::-1][1:]))",
                        "    al = lam / s\n    be = np.sqrt(np.maximum(eta + a * a * c * c - lam * lam * c * c / (s * s), 0.0))\n    alpha = np.concatenate((al, al[::-1][1:]))",
                        "return float(-lam / s), sgn * math.sqrt(max(b2, 0.0)), b2",
                        "return float(lam / s), sgn * math.sqrt(max(b2, 0.0)), b2"),
    # the screen upside down (rows from the bottom): the lensed far side of the disk would appear below the shadow
    "M6_screen_rows_flipped": (KS, "return top - p * (np.arange(self.ny) + 0.5)",
                               "return top - p * (np.arange(self.ny)[::-1] + 0.5)"),
    # Keplerian gas allowed inside the ISCO (no plunge): the Keplerian model's inner edge
    "M7_keplerian_inside_isco": (KS, "    out = r >= r_isco\n", "    out = r >= 0.0 * r_isco\n"),
    # the Johannsen photon orbits with the sign of A2' flipped
    "M8_jp_dA2_sign": (JPM, "lam = (dlp * w - 2.0 * dl * wp) / (a * (dlp * dev.A2(r) - 2.0 * dl * dev.dA2(r)))",
                       "lam = (dlp * w - 2.0 * dl * wp) / (a * (dlp * dev.A2(r) + 2.0 * dl * dev.dA2(r)))"),
    # the Cunningham plunge with the energy of the circular orbit at r instead of the ISCO's (no plunge constants)
    "M9_plunge_wrong_constants": (KS, "E, L = kerr.circular_e_l(r_isco, chi, prograde)",
                                  "E, L = kerr.circular_e_l(r_isco * 1.05, chi, prograde)"),
    # the turning-point time of scattered rays off by 10 %: kr flips at the wrong place
    "M10_tau_turn": (KN, "tau_turn = xp.where(scatter, I_inf, xp.nan)", "tau_turn = xp.where(scatter, 0.9 * I_inf, xp.nan)"),
}

TESTS = ["tests/test_kerr_null.py", "tests/test_kerr_shadow.py", "tests/test_johannsen_metric.py",
         "tests/test_kerr_orbits.py"]


def prepare(scratch, name, spec):
    dst = os.path.join(scratch, name)
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(os.path.join(ENGINE, "lfphys"), dst, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
    path = os.path.join(dst, spec[0])
    src = open(path).read()
    pairs = spec[1:]
    for old, new in zip(pairs[0::2], pairs[1::2]):
        if old not in src:
            return None, f"pattern not found: {old[:60]!r}"
        src = src.replace(old, new)
    open(path, "w").write(src)
    return dst, None


def run(name, dst):
    uid = f"{os.getuid()}:{os.getgid()}"
    base = ["docker", "run", "--rm", "--name", f"lf-rev15-mut-{name.split('_')[0].lower()}", "--user", uid, "-e",
            "HOME=/tmp", "-e", "LFPHYS_NO_GPU=1", "-e", "OMP_NUM_THREADS=1", "-v", f"{ENGINE}:/lf:ro", "-v",
            f"{dst}:/lf/lfphys:ro", "-e",
            "PYTHONPATH=/lf/visualizations:/lf/visualizations/server:/lf/lfphys:/lf/visualizations/tests",
            "light-funnel-viz"]
    r1 = subprocess.run(base + ["sh", "-c", "cd /lf/lfphys && python3 -m pytest -q -x -p no:cacheprovider "
                                + " ".join(TESTS) + " 2>&1 | tail -3"], capture_output=True, text=True)
    r2 = subprocess.run(base + ["sh", "-c", "cd /lf/visualizations && python3 -m pytest -q -p no:cacheprovider "
                                "v15_kerr_shadow/tests 2>&1 | tail -3"], capture_output=True, text=True)
    return r1.stdout.strip().splitlines()[-1:] + r2.stdout.strip().splitlines()[-1:]


def main():
    scratch = sys.argv[1]
    os.makedirs(scratch, exist_ok=True)
    jobs = {}
    for name, spec in MUTATIONS.items():
        dst, err = prepare(scratch, name, spec)
        if err:
            print(f"{name}: NOT APPLIED ({err})", flush=True)
            continue
        jobs[name] = dst
    with ThreadPoolExecutor(5) as ex:
        res = dict(zip(jobs, ex.map(lambda kv: run(*kv), jobs.items())))
    for name in jobs:
        print(f"{name}: engine tests -> {res[name][0] if res[name] else '?'} | v15 tests -> "
              f"{res[name][1] if len(res[name]) > 1 else '?'}", flush=True)


if __name__ == "__main__":
    main()
