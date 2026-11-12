# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Write RESULTS.md of the comparison suite (plan item P13): every comparison row of the test modules in this folder,
with the library versions and licences, a summary per library and the known disagreements.

Runs in the image lfphys-ext only (the libraries are not in the runtime image). From engine/:
    docker run --rm --user "$(id -u):$(id -g)" -v "$PWD":/lf -w /lf/lfphys -e LFPHYS_EXTERNAL=1 \\
        lfphys-ext:latest python3 tests/external/make_results.py
The rows are the ones the tests assert (each module's ``rows()``); the exit status is 1 if a row that is not a
recorded disagreement exceeds its tolerance, or if a recorded disagreement has disappeared.
"""

from __future__ import annotations

import argparse
import datetime
import importlib
import importlib.metadata as md
import platform
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE_PKG = HERE.parents[1]  # engine/lfphys

MODULES = [  # (module, library, distribution names, licence found in the repository's LICENSE file, 2026-10-27)
    ("test_ext_qcd_rundec", "CRunDec 3.1 via rundec", ["rundec"],
     "MIT (rundec-python LICENSE; CRunDec 3.1 source header: MIT, 'Jan 2019: Changed license from GPLv3 to MIT')"),
    ("test_ext_kerr_kerrgeopy", "KerrGeoPy", ["kerrgeopy"], "MIT (LICENSE)"),
    ("test_ext_optics_tmm", "tmm", ["tmm"], "MIT (LICENSE.txt)"),
    ("test_ext_qubits_qutip", "QuTiP", ["qutip"], "BSD-3-Clause (LICENSE.txt)"),
    ("test_ext_open_qutip", "QuTiP (open systems)", ["qutip"], "BSD-3-Clause (LICENSE.txt)"),
    ("test_ext_constants_astropy", "Astropy", ["astropy"], "BSD-3-Clause (LICENSE.rst)"),
    ("test_ext_flrw_astropy", "Astropy (FLRW cosmology)", ["astropy"], "BSD-3-Clause (LICENSE.rst)"),
    ("test_ext_mie_miepython", "miepython (Mie scattering)", ["miepython"], "MIT (LICENSE.txt, 2026-11-04)"),
]
BASES = {
    "coefficient budgets + truncation": "engine: its tested coefficient bound (mie.coefficient_bound: u (4N + 8s), "
                                        "s the case's largest sensitivity x|da_n/dx|/max|a| of the exact "
                                        "coefficients, 50 digits) propagated "
                                        "through the row's formula with the moduli of its partial derivatives; "
                                        "miepython: its coefficients' measured distance to the 40-digit reference, "
                                        "propagated the same way, plus the omitted tail beyond its N = Wiscombe's; "
                                        "both: gamma_{8N} times the moduli of the summed terms",
    "stated bound + 16N u": "the engine's tested coefficient bound with that order's sensitivity, u (4N + 8s), "
                            "plus 16 N u of the largest coefficient for the library's recurrences",
    "integrators": "both sides' stated error control: CRunDec pi*1e-10 per accepted Runge-Kutta step, the engine's "
                   "DOP853 atol + rtol|a| per step, steps counted, propagated with f(a_end)/f(a_k)",
    "decoupling": "rounding of alpha(1 + c2 a^2 + c3 a^3): 2 gamma_16 alpha (1 + |c2| a^2 + |c3| a^3)",
    "brentq + noise": "brentq's xtol + rtol|p| plus the width of {|S_exact| <= running bound of S} (KerrGeoPy), "
                      "plus the engine's running error bound",
    "running error": "first-order running error bounds of both sides along their actual operations (_common.Fe)",
    "residual": "running error bound of the engine's R(r) with KerrGeoPy's E, L carrying their own bounds",
    "conditioning + running error": "the engine's Newton-polished E, L, Q: |J^-1| gamma_16 |terms| x 2 + 2u (J the "
                                    "Jacobian of the defining equations); KerrGeoPy's closed form: its running "
                                    "error bound (_common.Fe)",
    "sensitivity budget": "256 u per input (p, e, x), per constant (E, L, Q) and on the result, propagated with the "
                          "engine's sensitivities; plus KerrGeoPy's constants' running bounds propagated the same way",
    "TMM rounding": "16u backward error in every input, admittance and phase (mpmath sensitivities) on each side, "
                    "tmm's absolute error in cos(arcsin x), and the 2x2 product chain (product of moduli)",
    "TMM rounding (fluxes)": "as TMM rounding; tmm's absorption is a difference of two fluxes",
    "TMM rounding + stated err": "the engine's stated err_r/err_t/err_T plus TMM rounding",
    "TMM rounding + running error": "tmm side as TMM rounding, the engine's closed form by its running bound",
    "one rounding + TMM rounding": "the engine's stated single rounding plus tmm's sensitivity terms",
    "contraction 34": "sum |x||y| gamma_34 per side (QuTiP and engine contractions)",
    "contraction 34 x 4": "four contractions and three additions (CHSH)",
    "contraction 12": "sum |x||y| gamma_12 per side",
    "contraction 18": "sum |x||y| gamma_18 per side",
    "contraction 2": "one complex addition per entry, per side",
    "Lueders": "products P rho P and the division by p, per side",
    "LAPACK eig + h(x)": "LAPACK eigenvalue error p(n) u ||rho|| (p(n) = 10n) through h(x) = -x log2 x, and the "
                         "cut-offs",
    "LAPACK eig + sqrt": "Bauer-Fike with LAPACK's p(n) u ||R||, through sqrt (sqrt(dl) at zero eigenvalues)",
    "expm/gates": "scipy expm (backward error u||A||, Lipschitz 1 on skew-Hermitian) and QuTiP's five gates",
    "superop rounding": "every Liouvillian entry within gamma_k M_ij (k = 3 + 2d + 2(2 + 3 n_c), M the sum of the "
                        "moduli of its kron terms), per side",
    "expm + diag a posteriori": "engine: its stated expm bound plus the construction error carried by trace-norm "
                                "contraction; QuTiP diag: residuals L U - U Lambda and U Uinv - I in mpmath, the "
                                "roundings of Uinv rho0, of the k products by exp(lambda dt) and of U y",
    "engine estimate + Verner control": "engine: the error estimate evolve() returns (step doubling); QuTiP "
                                        "vern9: d^{3/2}(atol + rtol) per step times the attempted steps (counted "
                                        "coefficient calls / 16 stages); global <= sum of local errors (CPTP flow "
                                        "contracts the trace norm)",
    "Wedin + LU": "engine: Wedin's bound on the SVD null vector; QuTiP direct: cond(A)(10 n u + ||E_c||/||A||) for "
                  "the LAPACK solve, plus its hermitisation",
    "MC z = 5": "5 sqrt(se_engine^2 + se_qutip^2) of the trajectory means, plus QuTiP's collapse-time and ODE bias",
    "DKW two-sample": "eps(N_e) + eps(N_q), eps(N) = sqrt(ln(2/alpha)/(2N)) at alpha = 1e-6, plus QuTiP's "
                      "collapse-time bias in the CDF",
    "same decimal": "both sides parse the same published decimal: 0",
    "engine bound + quad 1.49e-8": "engine: the error bound its integral returns (with_error=True); Astropy: QUADPACK's"
                                   " request, scipy.integrate.quad's defaults epsabs = epsrel = 1.49e-8, i.e. 1.49e-8 "
                                   "max(1, |I|) of the dimensionless integral times c/H0 or 1/H0",
    "engine bound + quad 1.49e-8 + Komatsu fit 0.35 %": "engine: the error bound its integral returns "
                                                        "(with_error=True); Astropy: QUADPACK's request, "
                                                        "scipy.integrate.quad's defaults epsabs = epsrel = 1.49e-8, "
                                                        "i.e. 1.49e-8 max(1, |I|) of the dimensionless integral times "
                                                        "c/H0 or 1/H0; the massive neutrino through Komatsu et al. "
                                                        "2011's fit: 0.35 % of its density (half of its largest share "
                                                        "over the range for integrals and E)",
    "engine bound + closed form 64u": "engine: the error bound its integral returns; Astropy's closed forms (flat, no "
                                      "radiation): 64u times the sum of the moduli of the two terms it subtracts "
                                      "(hyp2f1 or asinh; scipy states no bound for hyp2f1, the measured lib err is "
                                      "shown)",
    "propagated + quad 1.49e-8": "the bounds of D_C (engine + library as in the other bases) carried through sinh/sin "
                                 "and the factors (1+z), log10, plus 2u per extra operation; Astropy: QUADPACK's "
                                 "1.49e-8 request",
    "propagated + quad 1.49e-8 + Komatsu fit 0.35 %": "the bounds of D_C (engine + library as in the other bases) "
                                                      "carried through sinh/sin and the factors (1+z), log10, plus 2u "
                                                      "per extra operation; Astropy: QUADPACK's 1.49e-8 request; the "
                                                      "massive neutrino through Komatsu et al. 2011's fit: 0.35 % of "
                                                      "its density (half of its largest share over the range for "
                                                      "integrals and E)",
    "propagated + closed form 64u": "the bounds of D_C (engine + library as in the other bases) carried through "
                                    "sinh/sin and the factors (1+z), log10, plus 2u per extra operation; Astropy: "
                                    "closed form 64u",
    "16u x conditioning per side": "E, Omega_x(z), rho_crit evaluated algebraically: 16u per side times the "
                                   "conditioning sum|terms|/E^2 of the Friedmann sum, plus Astropy's 11-digit literal "
                                   "0.22710731766 for 7/8 (4/11)^(4/3) (relative 1.05e-12) on the neutrinos' share",
    "16u x conditioning per side + Komatsu fit 0.35 %": "E, Omega_x(z), rho_crit evaluated algebraically: 16u per side "
                                                        "times the conditioning sum|terms|/E^2 of the Friedmann sum, "
                                                        "plus Astropy's 11-digit literal 0.22710731766 for 7/8 "
                                                        "(4/11)^(4/3) (relative 1.05e-12) on the neutrinos' share; the "
                                                        "massive neutrino through Komatsu et al. 2011's fit: 0.35 % of "
                                                        "its density (half of its largest share over the range for "
                                                        "integrals and E)",
    "Komatsu fit 0.35 % + literal": "the neutrino density relative to photons: Komatsu's 0.35 % on the massive share, "
                                    "the 11-digit literal, 32u, the engine's Fermi-Dirac quadrature bound (4e-15) "
                                    "twice; the exact value by 30-digit quadrature",
    "16 roundings + literal": "2 gamma_16 |x| plus Astropy's 11-digit literal for 7/8 (4/11)^(4/3)",
    "16 roundings + literal + Komatsu fit 0.35 %": "2 gamma_16 |x|, the literal, and Komatsu's 0.35 % on the massive "
                                                   "share",
    "4 roundings": "four roundings per side: 2 gamma_4 |x|",
    "8 roundings": "eight roundings per side: 2 gamma_8 |x|",
    "12 roundings": "twelve roundings per side: 2 gamma_12 |x|",
    "1 roundings": "one rounding per side: 2 gamma_1 |x|",
    "2 roundings": "two roundings per side: 2 gamma_2 |x|",
}


def fmt(x) -> str:
    if isinstance(x, complex) or type(x).__name__ in ("complex128", "complex64"):
        x = complex(x)
        return f"{x.real:.12g}{x.imag:+.12g}j" if x.imag else f"{x.real:.15g}"
    return f"{float(x):.15g}"


def e(x) -> str:
    return "" if x is None else f"{x:.2e}"


def cell(text) -> str:
    """A table cell: '|' (as in |E|^2 or |00>) escaped for Markdown."""
    return str(text).replace("|", "\\|")


# distributions installed without pip metadata (conda packages): the module whose __version__ stands in
NO_PIP_METADATA: dict = {}  # e.g. {"pymeep": "meep"} for a conda-only library in a one-off image (AGENTS §3 rule 8)


def _module_version(dist: str) -> str | None:
    mod = NO_PIP_METADATA.get(dist)
    if mod is None:
        return None
    try:
        return str(importlib.import_module(mod).__version__)
    except Exception:  # noqa: BLE001 - not importable here: reported as not installed
        return None


def licence_of(dist: str) -> str:
    try:
        meta = md.distribution(dist).metadata
    except md.PackageNotFoundError:
        if _module_version(dist) is not None:
            return "no pip metadata (conda package; licence from its conda record, sources/dependencies.md)"
        return "not installed"
    for key in ("License-Expression", "License"):
        val = (meta.get(key) or "").strip()
        if val and "\n" not in val and len(val) < 80:
            return f"{key}: {val}"
    cls = [c.split("::")[-1].strip() for c in (meta.get_all("Classifier") or []) if c.startswith("License ::")]
    return "classifier: " + "; ".join(cls) if cls else "none declared"


def version_of(dist: str) -> str:
    try:
        return md.version(dist)
    except md.PackageNotFoundError:
        v = _module_version(dist)
        return f"{v} (module __version__)" if v is not None else "-"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=HERE / "RESULTS.md", help="output file (default: RESULTS.md here)")
    ap.add_argument("--image", default="lfphys-ext",
                    help="the image the rows are generated in, for the header (default: lfphys-ext; a one-off "
                         "image of a copyleft library names itself here)")
    ap.add_argument("--only", nargs="*", default=None,
                    help="module names to include (default: all), e.g. test_ext_optics_tmm")
    args = ap.parse_args(argv)

    for p in (str(ENGINE_PKG), str(HERE)):
        if p not in sys.path:
            sys.path.insert(0, p)
    mods = [m for m in MODULES if args.only is None or m[0] in args.only]
    results = []
    for name, lib, dists, repo_lic in mods:
        mod = importlib.import_module(name)
        results.append((name, lib, dists, repo_lic, mod, mod.rows()))

    lines = [
        "# Comparison of lfphys with third-party libraries (plan item P13)",
        "",
        f"Generated {datetime.date.today().isoformat()} by `tests/external/make_results.py` in the image "
        f"{args.image} (Python {platform.python_version()}). Do not edit by hand; regenerate (README.md).",
        "",
        "Each row is one assertion of `tests/external/test_ext_*.py`: the engine's value, the library's value, their "
        "difference and the tolerance derived for it (the derivations are in each module's docstring; the key is in "
        "the column *basis*). Where an exact reference exists (closed forms or the same equations in 30-50-digit "
        "mpmath for the same binary64 inputs), *eng err* and *lib err* are each side's distance to it. *status*: "
        "pass, FAIL, or xfail (a known disagreement, recorded with its numbers and asserted to persist).",
        "",
        "## Libraries",
        "",
        "| library | package | version | licence declared (installed metadata) | licence in the repository |",
        "|---|---|---|---|---|",
    ]
    for name, lib, dists, repo_lic, mod, rows in results:
        for d in dists:
            lines.append(f"| {lib} | `{d}` | {version_of(d)} | {licence_of(d)} | {repo_lic} |")
    lines += ["", "Engine side: lfphys from this repository, numpy " + version_of("numpy") + ", scipy "
              + version_of("scipy") + ", mpmath " + version_of("mpmath") + " (the runtime image's pinned versions). "
              "The libraries are used only here, in a separate image that is never distributed (README.md); "
              "their audit: `../../sources/dependencies.md`, section \"Comparison-only libraries (plan P13)\".", ""]
    if any(r[0] == "test_ext_constants_astropy" for r in results):
        mod = [r[4] for r in results if r[0] == "test_ext_constants_astropy"][0]
        lines += ["Editions of the constants:", ""] + [f"* {s}" for s in mod.edition_notes()] + [""]

    lines += ["## Summary", "",
              "| library | comparisons | pass | xfail (known) | FAIL | max diff/tol (passing) | engine closer to exact | "
              "library closer | equal |",
              "|---|---|---|---|---|---|---|---|---|"]
    bad = 0
    for name, lib, dists, repo_lic, mod, rows in results:
        n_pass = sum(1 for r in rows if r.ok and not r.xfail)
        n_xf = sum(1 for r in rows if r.xfail)
        n_fail = sum(1 for r in rows if not r.ok and not r.xfail)
        gone = sum(1 for r in rows if r.xfail and r.ok)  # a recorded disagreement that no longer shows
        bad += n_fail + gone
        ratios = [r.diff / r.tol for r in rows if r.ok and not r.xfail and r.tol > 0]
        ex = [r for r in rows if r.eng_err is not None]
        closer_e = sum(1 for r in ex if r.eng_err < r.lib_err)
        closer_l = sum(1 for r in ex if r.lib_err < r.eng_err)
        lines.append(f"| {lib} | {len(rows)} | {n_pass} | {n_xf} | {n_fail}{' (+' + str(gone) + ' xfail now passing)' if gone else ''} "
                     f"| {max(ratios) if ratios else 0:.3f} | {closer_e} | {closer_l} | {len(ex) - closer_e - closer_l} |")
    lines += ["", "*engine closer / library closer / equal*: among the rows with an exact reference, which side is "
              "nearer to it.", ""]

    known = [(lib, r) for _, lib, _, _, _, rows in results for r in rows if r.xfail]
    lines += ["## Known disagreements", ""]
    if known:
        for lib, r in known:
            lines.append(f"* {lib}: {r.quantity} at {r.inputs}: {r.xfail}".replace("|", "\\|"))
    else:
        lines.append("None.")
    lines += ["", "## Tolerance bases", "", "| basis | meaning (details in the module docstrings) |", "|---|---|"]
    used = sorted({r.basis for *_, rows in results for r in rows})
    for b in used:
        lines.append(f"| {b} | {cell(BASES.get(b, ''))} |")
    lines.append("")

    for name, lib, dists, repo_lic, mod, rows in results:
        lines += [f"## {lib} (`{name}.py`)", "",
                  "| quantity | inputs | engine | library | diff | tol | status | basis | eng err | lib err |",
                  "|---|---|---|---|---|---|---|---|---|---|"]
        for r in rows:
            status = "xfail" if r.xfail else ("pass" if r.ok else "FAIL")
            lines.append(f"| {cell(r.quantity)} | {cell(r.inputs)} | {fmt(r.engine)} | {fmt(r.library)} | {r.diff:.2e} | "
                         f"{r.tol:.2e} | {status} | {r.basis} | {e(r.eng_err)} | {e(r.lib_err)} |")
        lines.append("")
    args.out.write_text("\n".join(lines), encoding="utf-8")
    total = sum(len(r[5]) for r in results)
    print(f"wrote {args.out} ({total} comparisons; problems: {bad})")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
