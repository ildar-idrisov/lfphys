# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Write chi2_sf.json: the p-value of χ² that the lab's fit prints (player/js/fit.js chi2Sf, chi2LogSf, pValueText;
EX2 design lfphys/sources/explore_EX2_2026-11-18_design.md §5 F6 (c), F11), computed by mpmath at 50 digits as the
regularised upper incomplete gamma Q(ν/2, χ²/2) = mpmath.gammainc(ν/2, χ²/2, ∞, regularized=True), from p near 1 to
χ² = 10⁶ (p = 3.05·10⁻²¹⁷¹³⁴ for ν = 7), far below the double's range (p < 10⁻³⁰⁸ beyond χ² ≈ 1 400).

Each case: {chi2, dof, ln_p, p, text}: ln_p the natural logarithm of p (a double); p the double nearest to p while
p ≥ 1e-300, else null; text the p as fit.js prints it in English («0.0123», «3.2·10⁻⁴⁵», «3.05·10⁻²¹⁷¹³⁴»: three
significant digits, trailing zeros dropped), built here from mpmath's digits. Where SciPy's chi2.sf has p in the
double's normal range, it is checked against mpmath to 1e-12 (the previous fixture was SciPy's). A case whose fourth
significant digit makes the rounding to three ambiguous (within 1e-6 of a half) is refused, so that the printed text
is decided by the value, not by the last bits. mpmath and SciPy are used here only (rule 8: in tests).
Run from the repository root in Docker:
    docker run --rm --memory=2g -v "$PWD":/lf -w /lf lfphys-viz \\
        python3 visualizations/player/js/tests/fixtures/make_chi2_sf.py
"""

import json
import math
from decimal import Decimal
from pathlib import Path

import mpmath as mp
from scipy import stats as sps

mp.mp.dps = 50
SUP = str.maketrans("-0123456789", "⁻⁰¹²³⁴⁵⁶⁷⁸⁹")
DIGITS = 3


def rounded(mant: mp.mpf) -> int:
    """mant in [1, 10) to DIGITS significant digits, as an integer (321 for 3.21); refused near a tie."""
    scaled = mant * 10 ** (DIGITS - 1)
    frac = scaled - mp.floor(scaled)
    assert abs(frac - mp.mpf("0.5")) > mp.mpf("1e-6"), f"a rounding tie: {mant}"
    return int(mp.nint(scaled))


def text_of(q: mp.mpf) -> str:
    """fit.js pValueText in English (i18n.js fmt with ".3g": plain decimals for 1e-4 <= p < 1e7, else m·10ⁿ)."""
    if q == 1:
        return "1"
    e = int(mp.floor(mp.log10(q)))
    k = rounded(q / mp.power(10, e))
    if k == 10 ** DIGITS:  # 9.995 -> 10.0: the next decade
        k, e = 10 ** (DIGITS - 1), e + 1
    digits = str(k).rstrip("0") or "0"
    if q >= mp.mpf("1e-4"):  # a plain decimal: k·10^(e - DIGITS + 1), trailing zeros dropped
        return format(Decimal(k).scaleb(e - DIGITS + 1).normalize(), "f")
    mant = digits[0] + ("." + digits[1:] if len(digits) > 1 else "")
    return f"{mant}·10{str(e).translate(SUP)}"


DOFS = (1, 2, 3, 4, 5, 7, 10, 15, 30, 100, 300, 1000)
CHI2 = (0.001, 0.01, 0.5, 1.0, 2.0, 3.84, 7.5, 15.0, 40.0, 120.0, 300.0, 700.0, 1000.0, 1380.0, 1400.0, 1450.0,
        1500.0, 3000.0, 1.0e4, 1.0e5, 4.9e5, 1.0e6)
EXTRA = [(990.0, 1000), (1000.0, 1000), (1100.0, 1000), (290.0, 300), (99.0, 100)]  # near the mean: the series' side
cases = []
for d, c in [(d, c) for d in DOFS for c in CHI2] + [(d, c) for c, d in EXTRA]:
    q = mp.gammainc(mp.mpf(d) / 2, mp.mpf(c) / 2, mp.inf, regularized=True)
    lnq = mp.log(q)
    p = float(q) if q >= mp.mpf("1e-300") else None
    if p is not None and p > 1e-300:
        ref = float(sps.chi2.sf(c, d))
        assert math.isclose(ref, p, rel_tol=1e-12), (c, d, ref, p)
    cases.append({"chi2": c, "dof": d, "ln_p": float(lnq), "p": p, "text": text_of(q)})

out = Path(__file__).with_name("chi2_sf.json")
out.write_text(json.dumps(cases, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"{out}: {len(cases)} cases, {sum(c['p'] is None for c in cases)} below 1e-300, "
      f"the smallest ln p {min(c['ln_p'] for c in cases):.6g}")
