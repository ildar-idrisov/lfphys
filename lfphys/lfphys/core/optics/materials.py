# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Optical constants of real, dispersive materials: the complex refractive index n + i kappa (kappa >= 0, the engine's
time factor e^{-i omega t}) at a vacuum wavelength, computed from the measured data of ``lfphys.core.data`` (each
material is a ``DATASETS`` entry there, with its source and how it was checked; the record of the checks is
``lfphys/sources/materials_2026-11-18.md``).

The forms, each as its source writes it (lambda in micrometres inside the formulas, in nanometres at the interface):

* SCHOTT's Sellmeier formula (the glass data sheets): n^2 - 1 = sum_i B_i lambda^2 / (lambda^2 - C_i);
  kappa from the sheet's internal transmittance tau_i of a sample of thickness d (25 mm; 10 mm where only that is
  printed): tau_i = exp(-4 pi kappa d / lambda), so kappa = -lambda ln(tau_i) / (4 pi d), interpolated between the
  sheet's wavelengths;
* the Sellmeier formula of Dodge (MgF2) and Malitson (fused silica): n^2 - 1 = sum_i A_i lambda^2 / (lambda^2 -
  lambda_i^2), kappa = 0 in their ranges;
* tabulated n and kappa (films and metals): a shape-preserving piecewise cubic Hermite interpolant (PCHIP: the
  weighted harmonic mean of the neighbouring slopes at interior nodes and the one-sided three-point formula at the
  ends, as described by Moler, Numerical Computing with MATLAB, §3.4, after Fritsch and Carlson) in lambda, applied to
  ln kappa (to kappa itself where a table has kappa = 0). Each node is reproduced exactly; between nodes the
  interpolant is monotone where the data are, so kappa stays >= 0. Its error between two nodes is estimated as the
  largest of the leave-one-out errors (each node interpolated from all the others: the spacing there doubles) of the
  six nodes around the interval, and not below half a unit of the last digit the source prints for the two nodes (for
  SCHOTT's kappa: of the printed tau_i, d kappa = lambda d tau / (4 pi d tau)); ``interpolation_error`` gives it at a
  wavelength, ``info`` its largest value over the range. Tested against a second shape-aware interpolant (Akima's)
  between the nodes from 0.2 to 2.5 um; the largest excess elsewhere is aluminium's L edge near 17 nm (1.8 times the
  estimate).

``dindex`` is the derivative d(n + i kappa)/d lambda (per nm), exact for the formulas and for the interpolant (the
derivative of the cubic, kappa' = kappa (ln kappa)'), as ``interfaces.group_delay`` needs it. Outside a material's
range a coded refusal ``material.out_of_range``.

The wavelength and the reference medium are each source's own. The SCHOTT glasses' indices are relative to air at
room temperature and normal pressure and lambda is the wavelength in air (SCHOTT, TIE-29: "The refractive index data
given in the data sheets are measured relative to the refractive index measured in air"; the printed indices are
reproduced at the air wavelengths of TIE-29's Tab. 1 and missed by up to 7e-5 at the vacuum ones, tests): what a
boundary between glass and air in air needs, with air n = 1. For the other materials lambda and the reference are as
the refractiveindex.info database gives them, not checked in their papers; air against vacuum changes n and lambda by
about (n_air - 1) = 2.7e-4 of their values (``info``: ``wavelength``).
"""

from __future__ import annotations

import math

import numpy as np

from lfphys.codes import coded
from lfphys.core import data
from lfphys.i18n import T

ABOUT = {
    "layer": "core", "kind": "data",
    "title": T("Optical constants of real materials (glasses, crystals, films, metals)"),
    "statement": T("The complex refractive index n + iκ of real, dispersive materials at a wavelength: the SCHOTT "
                   "glasses N-BK7, N-F2 and N-SF11 (SCHOTT's Sellmeier formula, relative to air at the wavelength in "
                   "air; κ from the internal transmittance), MgF₂ and fused silica (Dodge's and Malitson's Sellmeier "
                   "formulas), MgF₂, SiO₂ and Ta₂O₅ films, gold, silver and aluminium (measured tables, interpolated "
                   "by a shape-preserving cubic); the derivative dn/dλ for group delays; each material's range, "
                   "temperature, source and the check made."),
    "validity": T("each material within its stated range and at its stated temperature, as the source measured it (a "
                  "film's constants depend on its preparation); between the nodes of a table within the interpolation "
                  "error the module states"),
    "basis": [T("the datasets of lfphys.core.data (one entry per material, with its source)"),
              "Moler, Numerical Computing with MATLAB (SIAM, 2004), §3.4 (pchip, after Fritsch & Carlson, SIAM J. "
              "Numer. Anal. 17, 238 (1980))"],
    "conflicts": [],
}


# --- the forms -----------------------------------------------------------------------------------------------------
def sellmeier_schott(lam_um, B, C):
    """SCHOTT's form: n = sqrt(1 + sum B_i lambda^2 / (lambda^2 - C_i)), lambda in um, C_i in um^2."""
    l2 = np.asarray(lam_um, float) ** 2
    return np.sqrt(1.0 + sum(b * l2 / (l2 - c) for b, c in zip(B, C)))


def sellmeier_lambda(lam_um, A, L):
    """Dodge's and Malitson's form: n = sqrt(1 + sum A_i lambda^2 / (lambda^2 - lambda_i^2)), lambda, lambda_i in um."""
    l2 = np.asarray(lam_um, float) ** 2
    return np.sqrt(1.0 + sum(a * l2 / (l2 - li * li) for a, li in zip(A, L)))


def _dsellmeier(lam_um, coef, poles):
    """dn/dlambda (per um) of n^2 - 1 = sum a_i lambda^2/(lambda^2 - p_i): dn/dlambda = -(1/n) sum a_i p_i lambda /
    (lambda^2 - p_i)^2."""
    lam = np.asarray(lam_um, float)
    l2 = lam * lam
    n = np.sqrt(1.0 + sum(a * l2 / (l2 - p) for a, p in zip(coef, poles)))
    return -sum(a * p * lam / (l2 - p) ** 2 for a, p in zip(coef, poles)) / n


class Pchip:
    """Shape-preserving piecewise cubic Hermite interpolant through (x, y), x strictly increasing (the slopes as Moler
    describes them, §3.4): ``__call__`` and ``derivative`` for x within [x0, xN]."""

    def __init__(self, x, y):
        x = np.asarray(x, float)
        y = np.asarray(y, float)
        if x.ndim != 1 or len(x) < 2 or len(x) != len(y) or not np.all(np.diff(x) > 0):
            raise ValueError("Pchip: x must be strictly increasing, with as many y")
        self.x, self.y = x, y
        h = np.diff(x)
        delta = np.diff(y) / h
        n = len(x)
        d = np.zeros(n)
        if n == 2:
            d[:] = delta[0]
        else:
            k = np.flatnonzero(np.sign(delta[:-1]) * np.sign(delta[1:]) > 0) + 1
            w1 = 2 * h[k] + h[k - 1]
            w2 = h[k] + 2 * h[k - 1]
            d[k] = (w1 + w2) / (w1 / delta[k - 1] + w2 / delta[k])
            d[0] = self._end(h[0], h[1], delta[0], delta[1])
            d[-1] = self._end(h[-1], h[-2], delta[-1], delta[-2])
        self.d = d
        self.c = (3 * delta - 2 * d[:-1] - d[1:]) / h
        self.b = (d[:-1] - 2 * delta + d[1:]) / h ** 2

    @staticmethod
    def _end(h1, h2, del1, del2):
        """The non-centred, shape-preserving three-point formula at an end."""
        d = ((2 * h1 + h2) * del1 - h1 * del2) / (h1 + h2)
        if np.sign(d) != np.sign(del1):
            return 0.0
        if np.sign(del1) != np.sign(del2) and abs(d) > abs(3 * del1):
            return 3 * del1
        return d

    def _locate(self, u):
        u = np.asarray(u, float)
        k = np.clip(np.searchsorted(self.x, u, side="right") - 1, 0, len(self.x) - 2)
        return u, k, u - self.x[k]

    def __call__(self, u):
        u, k, s = self._locate(u)
        out = self.y[k] + s * (self.d[k] + s * (self.c[k] + s * self.b[k]))
        at = np.searchsorted(self.x, u)  # a node is reproduced exactly (not through the cubic's rounding)
        hit = (at < len(self.x)) & (self.x[np.minimum(at, len(self.x) - 1)] == u)
        return np.where(hit, self.y[np.minimum(at, len(self.x) - 1)], out)

    def derivative(self, u):
        u, k, s = self._locate(u)
        return self.d[k] + s * (2 * self.c[k] + 3 * s * self.b[k])


def _leave_one_out(x, y):
    """|y_i - P_{-i}(x_i)| at every interior node (P_{-i} the interpolant without node i); the ends get their
    neighbours' values."""
    e = np.zeros(len(x))
    for i in range(1, len(x) - 1):
        keep = np.r_[0:i, i + 1:len(x)]
        e[i] = abs(y[i] - Pchip(x[keep], y[keep])(x[i]))
    if len(x) > 2:
        e[0], e[-1] = e[1], e[-2]
    return e


def _half_unit(text: str) -> float:
    """Half a unit of the last digit of a printed number ("1.523846" -> 5e-7, "1.2399E-04" -> 5e-9)."""
    mant, _, exp = text.strip().lower().partition("e")
    dec = len(mant.partition(".")[2])
    return 0.5 * 10.0 ** (int(exp or 0) - dec)


def _column_precision(column) -> np.ndarray:
    """Half a unit of the last printed digit of each entry of a table's column; an exact zero printed as "0" (no
    decimals: Gao's Ta2O5 kappa) gets the finest precision printed in the column."""
    q = np.array([_half_unit(v) for v in column])
    plain = np.array(["." not in v and "e" not in v.lower() for v in column])
    if plain.any() and (~plain).any():
        q[plain] = q[~plain].min()
    return q


WINDOW = 3  # the error estimate of an interval takes the leave-one-out errors of WINDOW nodes on each side


# --- the materials -------------------------------------------------------------------------------------------------
class _Material:
    """One material: n and kappa as functions of lambda (nm), their derivatives, the range and the record."""

    def __init__(self, key, spec):
        self.key, self.spec = key, spec
        form = spec["form"]
        self.form = form
        self.n_tab = self.k_tab = None
        self.k_log = False
        self.q_n = self.q_k = None  # half a unit of the printed last digit at each node
        if form == "schott":
            self.range_nm = tuple(1000.0 * v for v in spec["range_um"])
            lam, kap, _, qk = _schott_kappa(spec)
            self._set_kappa(lam, kap)
            self.q_k = qk
        elif form == "sellmeier":
            self.range_nm = tuple(1000.0 * v for v in spec["range_um"])
        elif form == "table":
            text = [line.split() for line in spec["table"].strip().splitlines()]
            rows = np.array([[float(v) for v in r] for r in text])
            lam = 1000.0 * rows[:, 0]
            self.range_nm = (float(lam[0]), float(lam[-1]))
            self.n_tab = Pchip(lam, rows[:, 1])
            self._set_kappa(lam, rows[:, 2])
            self.q_n, self.q_k = (_column_precision([r[c] for r in text]) for c in (1, 2))
        else:
            raise ValueError(f"unknown form {form!r}")

    def _set_kappa(self, lam, kap):
        kap = np.asarray(kap, float)
        if np.any(kap < 0):
            raise ValueError(f"{self.key}: a negative kappa in the table")
        self.k_log = bool(np.all(kap > 0))
        self.k_tab = Pchip(lam, np.log(kap) if self.k_log else kap)
        self.k_nodes = (np.asarray(lam, float), kap)

    def check(self, lam_nm):
        lam = np.asarray(lam_nm, float)
        lo, hi = self.range_nm
        bad = ~((lam >= lo) & (lam <= hi))
        if np.any(bad):
            x = float(lam[bad].flat[0])
            raise coded(ValueError(T("{material}: λ = {lam} nm lies outside its data, {lo}–{hi} nm",
                                     material=self.key, lam=x, lo=lo, hi=hi)), "material.out_of_range")
        return lam

    def n(self, lam):
        if self.form == "schott":
            return sellmeier_schott(lam / 1000.0, self.spec["B"], self.spec["C"])
        if self.form == "sellmeier":
            return sellmeier_lambda(lam / 1000.0, self.spec["A"], self.spec["L"])
        return self.n_tab(lam)

    def dn(self, lam):
        if self.form == "schott":
            return _dsellmeier(lam / 1000.0, self.spec["B"], self.spec["C"]) / 1000.0
        if self.form == "sellmeier":
            return _dsellmeier(lam / 1000.0, self.spec["A"], [li * li for li in self.spec["L"]]) / 1000.0
        return self.n_tab.derivative(lam)

    def kappa(self, lam):
        if self.k_tab is None:
            return np.zeros_like(lam)
        v = self.k_tab(lam)
        out = np.exp(v) if self.k_log else np.maximum(v, 0.0)
        x, kap = self.k_nodes  # a node gives its tabulated kappa exactly (not exp(ln kappa) with its rounding)
        at = np.minimum(np.searchsorted(x, lam), len(x) - 1)
        return np.where(x[at] == lam, kap[at], out)

    def dkappa(self, lam):
        if self.k_tab is None:
            return np.zeros_like(lam)
        if self.k_log:
            return np.exp(self.k_tab(lam)) * self.k_tab.derivative(lam)
        return self.k_tab.derivative(lam)

    def loo(self):
        """Leave-one-out errors (n, kappa) at the nodes of the tables (None for a formula)."""
        if not hasattr(self, "_loo"):
            en = _leave_one_out(self.n_tab.x, self.n_tab.y) if self.n_tab is not None else None
            if self.k_tab is not None:
                lam, kap = self.k_nodes
                if self.k_log:
                    ek = np.zeros(len(lam))
                    for i in range(1, len(lam) - 1):
                        keep = np.r_[0:i, i + 1:len(lam)]
                        ek[i] = abs(kap[i] - math.exp(Pchip(lam[keep], np.log(kap[keep]))(lam[i])))
                    if len(lam) > 2:
                        ek[0], ek[-1] = ek[1], ek[-2]
                else:
                    ek = _leave_one_out(lam, kap)
            else:
                ek = None
            self._loo = (en, ek)
        return self._loo

    def interval_errors(self):
        """The error estimate of every interval between nodes, (n, kappa): the largest leave-one-out error of the
        WINDOW nodes on each side and half a unit of the printed last digit of its two nodes (None for a formula)."""
        if not hasattr(self, "_ivl"):
            out = []
            for e, q in zip(self.loo(), (self.q_n, self.q_k)):
                if e is None:
                    out.append(None)
                    continue
                m = len(e) - 1
                iv = np.array([e[max(0, i - WINDOW + 1):i + WINDOW + 1].max() for i in range(m)])
                if q is not None:
                    iv = np.maximum(iv, np.maximum(q[:-1], q[1:]))
                out.append(iv)
            self._ivl = tuple(out)
        return self._ivl


def _schott_kappa(spec):
    """(lambda nm, kappa, thickness mm, half a unit of kappa's precision) at the sheet's wavelengths: kappa = -lambda
    ln(tau_i)/(4 pi d) from tau_i of 25 mm where printed and above 0.000, else of 10 mm; the precision from half a unit
    of tau_i's last printed digit, d kappa = lambda d tau / (4 pi d tau)."""
    lam, kap, dmm, q = [], [], [], []
    for line in spec["tau"].strip().splitlines():
        lnm, t10, t25 = line.split()
        for t, d in ((t25, 25.0), (t10, 10.0)):
            if t != "-" and 0.0 < float(t) < 1.0:
                lam.append(float(lnm))
                kap.append(-float(lnm) * 1e-9 * math.log(float(t)) / (4 * math.pi * d * 1e-3))
                dmm.append(d)
                q.append(float(lnm) * 1e-9 * _half_unit(t) / (4 * math.pi * d * 1e-3 * float(t)))
                break
    order = np.argsort(lam)
    return tuple(np.array(v)[order] for v in (lam, kap, dmm, q))


_CACHE: dict[str, _Material] = {}


def ids() -> tuple[str, ...]:
    """The materials' ids (their ``core.data`` DATASETS keys)."""
    return tuple(data.OPTICAL_MATERIALS)


def _get(material: str) -> _Material:
    if material not in data.OPTICAL_MATERIALS:
        raise ValueError(T("unknown material {material}; the known ones: {known}", material=repr(material),
                           known=list(data.OPTICAL_MATERIALS)))
    m = _CACHE.get(material)
    if m is None:
        m = _CACHE[material] = _Material(material, data.OPTICAL_MATERIALS[material])
    return m


def _out(v):
    return complex(v) if np.ndim(v) == 0 else v


def index(material: str, lam_nm):
    """The complex refractive index n + i kappa (kappa >= 0) at the vacuum wavelength lam_nm (nm; a number or an
    array); outside the material's range a coded ValueError ``material.out_of_range``."""
    m = _get(material)
    lam = m.check(lam_nm)
    return _out(m.n(lam) + 1j * m.kappa(lam))


def dindex(material: str, lam_nm):
    """d(n + i kappa)/d lambda per nm at lam_nm (exact for the formulas and for the interpolant)."""
    m = _get(material)
    lam = m.check(lam_nm)
    return _out(m.dn(lam) + 1j * m.dkappa(lam))


def interpolation_error(material: str, lam_nm) -> tuple:
    """The estimate (dn, dkappa) of the interpolation error at lam_nm: that of the interval between nodes it lies in
    (``_Material.interval_errors``; at a node the larger of its two intervals'); 0 for a quantity given by a
    formula."""
    m = _get(material)
    lam = m.check(lam_nm)
    out = []
    for tab, iv in zip((m.n_tab, m.k_tab), m.interval_errors()):
        if tab is None:
            out.append(np.zeros_like(lam) if np.ndim(lam) else 0.0)
            continue
        x = tab.x
        k = np.clip(np.searchsorted(x, lam, side="right") - 1, 0, len(x) - 2)
        v = iv[k]
        node = (x[k] == lam) & (k > 0)  # at a node: the larger of its two intervals
        v = np.where(node, np.maximum(iv[k], iv[np.maximum(k - 1, 0)]), v)
        out.append(float(v) if np.ndim(v) == 0 else v)
    return tuple(out)


def info(material: str) -> dict:
    """The record of a material: dict(id, title, statement, validity, basis, checked (translatable texts and
    citations from ``core.data.DATASETS``), form, range_nm, temperature_C, wavelength ("air": lambda in air and n
    relative to air; else as the database gives it), nodes (of the n and the kappa tables),
    interp_error_n, interp_error_k (the largest interval error estimates over the range; 0 for a formula), and for the
    SCHOTT glasses kappa_nodes_from (the sample thickness in mm behind each kappa node))."""
    m = _get(material)
    d = dict(data.DATASETS[material])
    en, ek = m.interval_errors()
    d.update(id=material, form=m.form, range_nm=m.range_nm, temperature_C=m.spec.get("temperature_C"),
             wavelength=m.spec.get("wavelength", "as the database gives it"),
             nodes=(0 if m.n_tab is None else len(m.n_tab.x), 0 if m.k_tab is None else len(m.k_tab.x)),
             interp_error_n=0.0 if en is None else float(np.max(en)),
             interp_error_k=0.0 if ek is None else float(np.max(ek)))
    if m.form == "schott":
        d["kappa_nodes_from"] = tuple(float(x) for x in _schott_kappa(m.spec)[2])
    return d
