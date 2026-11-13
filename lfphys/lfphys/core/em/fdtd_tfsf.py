# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""The total-field / scattered-field plane wave of the FDTD solver (``lfphys.core.em.fdtd``), as an exact plane wave of
the Yee grid (the construction is described in ``fdtd_sources``).

The corrections: for every update whose difference stencil joins a node inside the total-field box with a node
outside it, the incident value of the node across is added (the node across is outside) or subtracted (inside):
E_c += cb (coef H_inc), H_c -= db (coef E_inc), coef = sign of the curl term x (+-1/dx) x (in(c) - in(s)). The
incident series of the nodes across the faces: for a pulse a window around the arrival of the pulse, computed by FFT
from the sampled profile (every frequency with the grid's own wavevector and the discrete amplitudes of E and H); for a
continuous wave the one frequency exactly, the ramp delayed by the discrete group delay. A pulse's window is chosen
from the group delays over the propagating part of its band and checked by its tail (``TAIL_MAX``; review B8-fdtd F7).
``monitor_factor`` gives how the flux monitor sees the wave (F5).
"""

from __future__ import annotations

import math

import numpy as np

from ...codes import coded
from ...i18n import T
from .fdtd_sources import ContinuousWave, omega_tilde, yee_normal_wavenumber, yee_wavenumber

ABOUT = {
    "layer": "core", "kind": "numerics",
    "title": T("FDTD: a total-field/scattered-field plane wave (the grid's exact wave)"),
    "statement": T("Corrections on the faces of the total-field region with an incident wave that satisfies the Yee "
                   "grid's difference equations exactly at every frequency (the wave vector from the grid's dispersion "
                   "relation, the amplitudes of E and H from the difference equations); a pulse through a time window "
                   "by the FFT, a continuous wave exactly at its frequency."),
    "validity": T("a homogeneous lossless background at the faces (correction nodes not in the background are counted "
                  "in checks()); faces outside the absorbing layers; the leak is round-off plus the start of the "
                  "series: ~0.3–0.4 of the window's tail (2–3e-9 away from a cut-off; a tail above 1e-6, at a Bloch "
                  "wave's cut-off or the grid's band edge, is refused); in 3-D a polarisation along the direction is "
                  "refused"),
    "basis": [T("Schneider, Understanding the FDTD Method (2010), §3.10, §8.5 (TF/SF), §7.4 (the dispersion "
                "relation)")],
    "conflicts": [],
}

AXES = "xyz"
MAX_TABLE_BYTES = 512 * 2 ** 20
OMIT_MAX = 1e-6  # share of the pulse energy that may lie where no propagating grid wave exists
POL_MIN = 1e-3  # smallest component of a 3-D polarization across the wave's direction
TAIL_MAX = 1e-6  # largest window tail of an incident series (of its peak; the leak is ~0.3-0.4 x it): refused above


def _direction(sim, pw):
    d = pw.direction
    if sim.dim == 2:
        if np.ndim(d) == 0:
            th = float(d)
            return np.array([math.cos(th), math.sin(th), 0.0])
        v = np.array(list(d) + [0.0] * (3 - len(d)), float)
    else:
        if np.ndim(d) == 0:
            raise ValueError(T("in 3-D the plane wave's direction is a vector (x, y, z)"))
        v = np.array(d, float)
    if not np.linalg.norm(v) > 0:
        raise ValueError(T("the plane wave's direction must be nonzero"))
    v = v / np.linalg.norm(v)
    v[np.abs(v) < 1e-15] = 0.0
    return v


def build_tfsf(sim, pw) -> dict:
    dim = sim.dim
    lo = list(pw.box[0]) + [-math.inf] * (3 - len(pw.box[0]))
    hi = list(pw.box[1]) + [math.inf] * (3 - len(pw.box[1]))
    if len(pw.box[0]) != dim:
        raise ValueError(T("total-field region: {n} coordinates", n=dim))
    tol = 1e-9 * sim.dx
    spanned = []
    for u in range(3):
        if u >= dim:
            spanned.append(True)
            continue
        x0 = sim.coord(-0.5, u)
        x1 = sim.coord(sim.shape[u] - 0.5, u)
        full = lo[u] <= x0 + tol and hi[u] >= x1 - tol
        spanned.append(full)
        if full and not sim.periodic[u]:
            raise ValueError(T("the total-field region spans the whole non-periodic axis {axis}: the wave would enter "
                               "the absorbing layer (keep a face inside, or use ±inf on one side only)", axis=AXES[u]))
        if not full:
            for x in (lo[u], hi[u]):
                if math.isfinite(x):
                    i = sim.index_of(x, u)
                    lo_p, hi_p = sim.npml[u]
                    if not (lo_p + 1 <= i <= sim.shape[u] - hi_p - 1) and not sim.periodic[u]:
                        raise ValueError(T("the face of the total-field region along axis {axis} (x = {x}) lies in "
                                           "the absorbing layer or at a wall: move it inwards", axis=AXES[u],
                                           x=float(x)))
    bg = sim.background
    nb = math.sqrt(bg.eps * bg.mu)
    finite_axes = [u for u in range(dim) if not spanned[u]]
    if not finite_axes:
        raise ValueError(T("the total-field region has no face"))
    # family
    if len(finite_axes) == 1 and all(spanned[u] for u in range(3) if u != finite_axes[0]):
        family = "slab"
        un = finite_axes[0]
        if math.isfinite(lo[un]) and not math.isfinite(hi[un]):
            sgn = 1.0
        elif math.isfinite(hi[un]) and not math.isfinite(lo[un]):
            sgn = -1.0
        else:
            dv = _direction(sim, pw)
            sgn = 1.0 if dv[un] >= 0 else -1.0
        kpar = np.array([sim.bloch[u] if u != un else 0.0 for u in range(3)])
        khat = None
    else:
        family = "fixed"
        un, sgn, kpar = None, 1.0, None
        khat = _direction(sim, pw)
        for u in range(3):
            if spanned[u] and u < dim and khat[u] != 0:
                raise ValueError(T("a plane wave with a component along axis {axis}, which the total-field region "
                                   "spans entirely: Bloch periodicity is needed (the Bloch phase then sets the angle)",
                                   axis=AXES[u]))
        if sim.complex:
            raise ValueError(T("an oblique plane wave in a world with a Bloch phase: use a slab (faces along one axis "
                               "only), the wave will take the Bloch wave vector"))
    # polarization
    if dim == 2:
        if sim.pol == "both":
            pol2d = pw.polarization if isinstance(pw.polarization, str) else "tm"
        else:
            pol2d = sim.pol
            if isinstance(pw.polarization, str) and pw.polarization != pol2d:
                raise ValueError(T("the wave's polarisation {pol} does not match the world's ({world})",
                                   pol=str(pw.polarization), world=pol2d))
        if pol2d not in ("tm", "te"):
            raise ValueError(T("polarisation of a 2-D wave: tm or te"))
        pvec = None
    else:
        pol2d = None
        if pw.polarization is None or isinstance(pw.polarization, str):
            raise ValueError(T("in 3-D the plane wave's polarisation is a vector E"))
        pvec = np.array(pw.polarization, float)
        pvec = pvec / np.linalg.norm(pvec)
    # reference point
    if pw.reference is not None:
        r0 = np.array(list(pw.reference) + [0.0] * (3 - dim))
    else:
        r0 = np.zeros(3)
        for u in range(dim):
            if family == "slab":
                if u == un:
                    r0[u] = lo[u] if sgn > 0 else hi[u]
                continue
            k = khat[u]
            if k > 0:
                r0[u] = lo[u]
            elif k < 0:
                r0[u] = hi[u]
            else:
                r0[u] = lo[u] if math.isfinite(lo[u]) else 0.0
            if not math.isfinite(r0[u]):
                raise ValueError(T("the wave enters the total-field region from infinity along axis {axis}: give a "
                                   "face on the side of incidence", axis=AXES[u]))

    # --- corrections: per (target component, curl term) -----------------------------------------------------------
    def inside(x, u):
        return (x >= lo[u] - tol) & (x <= hi[u] + tol)

    lists = []
    for c in sim.comps:
        kind_e = c[0] == "e"
        for (v, s, sign) in sim._terms[c]:
            if spanned[v]:
                continue
            nv = sim.shape[v]
            ic = np.arange(nv)
            xc = sim.coord(ic + sim.offset(c, v), v)
            in_c = inside(xc, v)
            # E: d = (S[i] - S[i-1]) / dx -> the S[i] neighbour has +1/dx; H: d = (S[i+1] - S[i]) / dx
            nb_list = (((ic, +1.0), ((ic - 1) % nv, -1.0)) if kind_e else (((ic + 1) % nv, +1.0), (ic, -1.0)))
            for (j, pm) in nb_list:
                xs = sim.coord(j + sim.offset(s, v), v)
                if sim.periodic[v]:
                    # the wrapped neighbour's coordinate is across the period
                    L = sim.shape[v] * sim.dx
                    xs = np.where((j == nv - 1) & (ic == 0) & kind_e, xs - L, xs)
                    xs = np.where((j == 0) & (ic == nv - 1) & (not kind_e), xs + L, xs)
                in_s = inside(xs, v)
                cross = in_c != in_s
                if not np.any(cross):
                    continue
                rows_i = ic[cross]
                cols_j = j[cross]
                coefs = sign * pm * sim.rd * (in_c[cross].astype(float) - in_s[cross].astype(float))
                # transverse nodes inside the box (the same for c and s)
                tr = []
                for w in range(3):
                    if w == v:
                        tr.append(None)
                        continue
                    if w >= dim:
                        tr.append(np.array([0]))
                        continue
                    iw = np.arange(sim.shape[w])
                    xw = sim.coord(iw + sim.offset(c, w), w)
                    tr.append(iw[inside(xw, w)] if not spanned[w] else iw)
                if any(t is not None and len(t) == 0 for t in tr):
                    continue
                for i_c, j_s, cf in zip(rows_i, cols_j, coefs):
                    axes_c = [np.array([i_c]) if w == v else tr[w] for w in range(3)]
                    axes_s = [np.array([j_s]) if w == v else tr[w] for w in range(3)]
                    Ic = np.meshgrid(*axes_c, indexing="ij")
                    Is = np.meshgrid(*axes_s, indexing="ij")
                    e_idx = np.ravel_multi_index([a.ravel() for a in Ic], sim.shape)
                    # coordinates of the source nodes (for the incident field)
                    pos = np.zeros((3, e_idx.size))
                    for w in range(dim):
                        pos[w] = sim.coord(Is[w].ravel() + sim.offset(s, w), w)
                    if sim.periodic[v]:
                        L = sim.shape[v] * sim.dx
                        if kind_e and i_c == 0 and j_s == nv - 1:
                            pos[v] -= L
                        if (not kind_e) and i_c == nv - 1 and j_s == 0:
                            pos[v] += L
                    lists.append({"target": c, "src": s, "kind": "e" if kind_e else "h", "v": v, "e_idx": e_idx,
                                  "coef": float(cf), "pos": pos})
    if not lists:
        raise ValueError(T("no correction node on the faces of the total-field region (check the polarisation and the "
                           "axes)"))
    # merge lists with the same (target, src, v): their node sets are disjoint (different faces)
    merged = {}
    for L in lists:
        key = (L["target"], L["src"], L["v"])
        if key not in merged:
            merged[key] = {"target": L["target"], "src": L["src"], "kind": L["kind"], "e_idx": [], "coef": [],
                           "pos": []}
        m = merged[key]
        m["e_idx"].append(L["e_idx"])
        m["coef"].append(np.full(L["e_idx"].size, L["coef"]))
        m["pos"].append(L["pos"])
    lists = []
    for m in merged.values():
        e_idx = np.concatenate(m["e_idx"])
        if len(np.unique(e_idx)) != len(e_idx):
            raise RuntimeError("TF/SF: repeated nodes in one list of corrections")
        lists.append({"target": m["target"], "src": m["src"], "kind": m["kind"], "e_idx": e_idx,
                      "coef": np.concatenate(m["coef"]), "pos": np.concatenate(m["pos"], axis=1)})

    rec = {"kind": "tfsf", "src": pw, "family": family, "pol2d": pol2d, "un": un, "sgn": sgn, "khat": khat,
           "kpar": kpar, "pvec": pvec, "r0": r0, "lists": lists, "nb": nb, "ref_series": [], "tail": 0.0,
           "omitted": 0.0, "ref_step0": int(sim.steps), "box": (lo, hi), "spanned": spanned}
    # rows: unique (component, phase coordinate)
    rows_key = {}
    for L in lists:
        d = L["pos"] - r0[:, None]
        if family == "fixed":
            xi = khat @ d
            nodew = None
        else:
            xi = d[un]
            ph = np.exp(1j * (kpar @ d))
            nodew = ph if sim.complex else None
        key_xi = np.round(xi / sim.dx * 1e6).astype(np.int64)
        rid = np.empty(len(xi), np.int64)
        for q, kx in enumerate(key_xi):
            k = (L["src"], int(kx))
            if k not in rows_key:
                rows_key[k] = (len(rows_key), float(xi[q]))
            rid[q] = rows_key[k][0]
        L["row"] = rid
        L["nodew"] = nodew
    rows = sorted(rows_key.items(), key=lambda kv: kv[1][0])
    rec["rows"] = [(k[0], v[1]) for k, v in rows]
    _build_series(sim, rec)
    return rec


def _vectors(sim, rec, omega):
    """The discrete plane wave at signed angular frequencies omega (arrays): (E (3, n) of unit amplitude along the
    polarization, H (3, n), k (3, n), ok mask, pol (n): |p - (p.K^) K^| in 3-D, the polarization's component across
    the grid's K (1 in 2-D))."""
    dx, dt = sim.dx, sim.dt
    bg = sim.background
    nb = rec["nb"]
    w = np.asarray(omega, float)
    aw = np.abs(w)
    sg = np.where(w >= 0, 1.0, -1.0)
    k = np.zeros((3, len(w)))
    if rec["family"] == "fixed":
        km = yee_wavenumber(aw, rec["khat"][:sim.dim], dx, dt, nb)
        ok = np.isfinite(km)
        km = np.where(ok, km, 0.0)
        k = rec["khat"][:, None] * (sg * km)[None]
    else:
        un = rec["un"]
        kpar = rec["kpar"]
        par = [kpar[u] for u in range(sim.dim) if u != un]
        kn = yee_normal_wavenumber(aw, np.array(par), dx, dt, nb)
        ok = np.isfinite(kn)
        kn = np.where(ok, kn, 0.0)
        k = np.repeat(kpar[:, None], len(w), axis=1).astype(float)
        k[un] = rec["sgn"] * sg * kn
    ok = ok & (aw > 0)
    K = 2.0 / dx * np.sin(k * dx / 2.0)
    Om = omega_tilde(w, dt)
    Kn = np.linalg.norm(K, axis=0)
    Khat_pos = np.where(Kn > 0, K / np.where(Kn > 0, Kn, 1.0), 0.0) * sg[None]  # the positive-frequency direction
    # E (unit amplitude along the polarization)
    nE = np.ones(len(w))
    if sim.dim == 2:
        if rec["pol2d"] == "tm":
            E = np.zeros((3, len(w)))
            E[2] = 1.0
        else:
            E = np.stack([-Khat_pos[1], Khat_pos[0], np.zeros(len(w))])
    else:
        p = rec["pvec"][:, None]
        E = p - (p * Khat_pos).sum(0)[None] * Khat_pos
        nE = np.linalg.norm(E, axis=0)
        E = np.where(nE > 0, E / np.where(nE > 0, nE, 1.0), 0.0)
    H = np.cross(K, E, axis=0) / np.where(Om != 0, Om * bg.mu, 1.0)
    return E, H, k, ok, nE


def _amplitudes(sim, rec, omega, comp):
    """Amplitude of component ``comp`` relative to the reference E amplitude, and the wavevector, for signed
    angular frequencies omega (arrays): (A, k (3, n), ok mask)."""
    E, H, k, ok, _ = _vectors(sim, rec, omega)
    a = "xyz".index(comp[1])
    A = (E if comp[0] == "e" else H)[a]
    A = np.where(ok, A, 0.0)
    return A, k, ok


def _check_polarization(sim, rec, omega):
    """Refuse a 3-D polarization (nearly) parallel to the wave's direction at any of the frequencies (review B8-fdtd
    F16: it gave a silent zero wave, or a direction set by round-off)."""
    if sim.dim != 3:
        return
    _, _, _, ok, pol = _vectors(sim, rec, omega)
    if np.any(ok) and float(np.min(pol[ok])) < POL_MIN:
        raise ValueError(T("the plane wave's polarisation is nearly parallel to its direction of propagation (the "
                           "transverse share {share:.2g} < {lim}): give E across the direction",
                           share=float(np.min(pol[ok])), lim=float(POL_MIN)))


def _build_series(sim, rec):
    pw = rec["src"]
    prof = pw.profile
    dt = sim.dt
    rows = rec["rows"]
    if isinstance(prof, ContinuousWave):
        w0 = 2 * math.pi * prof.frequency
        _check_polarization(sim, rec, np.array([w0]))
        coef, delay = [], []
        dw = 1e-6 * w0
        for comp, xi in rows:
            A, k, ok = _amplitudes(sim, rec, np.array([w0, w0 + dw]), comp)
            if not ok[0]:
                raise ValueError(T("the continuous wave's frequency is outside the grid's band (no propagating wave)"))
            if rec["family"] == "fixed":
                ph = k[:, 0] @ (rec["khat"] * xi)
                dphase = (k[:, 1] - k[:, 0]) @ (rec["khat"] * xi) / dw
            else:
                un = rec["un"]
                ph = k[un, 0] * xi
                dphase = (k[un, 1] - k[un, 0]) * xi / dw
            coef.append(A[0] * np.exp(1j * ph))
            delay.append(dphase)  # the envelope's (discrete) group delay to this node
        a = pw.amplitude * 1j * np.exp(-1j * prof.phase)
        rec["cw"] = {"w0": w0, "coef": np.array(coef) * a, "delay": np.array(delay), "ramp": prof.ramp}
        rec["table"] = None
        return
    t_end = prof.end()
    if not math.isfinite(t_end):
        raise ValueError(T("the plane wave's profile has no end: for a continuous wave use ContinuousWave, for a "
                           "profile of your own give end"))
    n_p = int(math.ceil(t_end / dt)) + 2
    xis = np.array([xi for _, xi in rows])
    nb = rec["nb"]
    d = np.floor(xis * nb / dt).astype(np.int64) if rec["family"] == "fixed" else np.floor(xis * nb / dt).astype(
        np.int64)
    item = 16 if sim.complex else 8
    m_cap = 1 << int(math.floor(math.log2(max(MAX_TABLE_BYTES // max(len(rows) * item, 1), 64))))
    # FFT length: the pulse plus the spread of the group delays over the propagating part of the band (review
    # B8-fdtd F7: the delays were sampled at three frequencies and the diverging delay near a Bloch wave's cut-off was
    # replaced by the continuum's, so the window was too short there)
    M = 1 << int(math.ceil(math.log2(max(64, 2 * n_p + 256))))
    for _ in range(40):
        t = np.arange(M) * dt
        g = pw.amplitude * prof(t)
        X = np.fft.fft(g)
        w = -2 * math.pi * np.fft.fftfreq(M, dt)
        pw_ = np.abs(X) ** 2
        band = pw_ > 1e-16 * pw_.max() if pw_.max() > 0 else np.zeros(M, bool)
        spread = 0
        if np.any(band) and len(xis):
            wb = np.unique(np.clip(np.abs(w[band]), 1e-12, None))
            _, k1, ok1 = _amplitudes(sim, rec, wb, rows[0][0])
            _, k2, ok2 = _amplitudes(sim, rec, wb * (1 + 1e-6), rows[0][0])
            ax = rec["khat"] if rec["family"] == "fixed" else np.eye(3)[rec["un"]]
            dk = ((k2 - k1).T @ ax) / (wb * 1e-6)
            prop = ok1 & ok2
            if np.any(prop):
                spread = int(math.ceil(np.max(np.abs(xis)) * np.max(np.abs(dk[prop] - nb)) / dt)) + 8
        if M >= 2 * (n_p + spread) + 256 or M >= m_cap:
            break
        M *= 2
    prev_tail = None
    while True:
        rec["omitted"] = 0.0
        tables = np.zeros((len(rows), M), complex if sim.complex else float)
        if tables.nbytes > MAX_TABLE_BYTES:
            raise coded(ValueError(T("the incident wave's series would take {mb:.0f} MB (> {lim:.0f}): reduce the "
                                     "total-field region or the pulse's duration, or use normal incidence",
                                     mb=tables.nbytes / 2**20, lim=MAX_TABLE_BYTES / 2**20)), "fdtd.incident_memory")
        t = np.arange(M) * dt
        X = np.fft.fft(pw.amplitude * prof(t))
        w = -2 * math.pi * np.fft.fftfreq(M, dt)
        pw_ = np.abs(X) ** 2
        _check_polarization(sim, rec, w[pw_ > 1e-16 * pw_.max()] if pw_.max() > 0 else w[:1])
        tail = 0.0
        tot = float(np.sum(np.abs(X) ** 2))
        cache = {}
        for q, (comp, xi) in enumerate(rows):
            if comp not in cache:
                cache[comp] = _amplitudes(sim, rec, w, comp)
            A, k, ok = cache[comp]
            if rec["family"] == "fixed":
                phase = (k.T @ (rec["khat"] * xi))
            else:
                phase = k[rec["un"]] * xi
            tau = 0.5 * dt if comp[0] == "h" else 0.0
            spec = X * A * np.exp(1j * phase - 1j * w * (d[q] * dt + tau))
            s = np.fft.ifft(spec)
            if not sim.complex:
                s = s.real
            tables[q] = s
            m = np.max(np.abs(s))
            if m > 0:  # what wraps around: the last quarter of the window (the pulse and its spread end before M / 2)
                tail = max(tail, float(np.max(np.abs(s[(3 * M) // 4:])) / m))
        ok_any = next(iter(cache.values()))[2]
        omitted = float(np.sum(np.abs(X[~ok_any]) ** 2) / tot) if tot > 0 else 0.0
        if omitted > OMIT_MAX:
            raise ValueError(T("the pulse has {share:.2g} of its energy at frequencies without a propagating wave of "
                               "the grid (below a Bloch wave's cut-off or above the grid's band edge; {lim} is "
                               "allowed): narrow the pulse's band or shift its frequency", share=omitted,
                               lim=float(OMIT_MAX)))
        # the window's tail: what the periodic FFT wraps from before t = 0 and after the window into the series. It
        # is the incident wave's value at the start of the run, where the injection begins abruptly; the leak through
        # the faces is ~0.3 x the tail (review B8-fdtd F7, measured). A window too short for the group delays makes
        # it fall when M is doubled; otherwise it is the precursor of a spectrum cut sharply where the propagating
        # band ends (a Bloch wave's cut-off, the grid's band edge) or of the profile's own cut-off, and does not
        # depend on M (measured: 1.8e-5 at M = 4096 ... 65536 for a pulse 1.2 +- 0.15 at the cut-off 0.6)
        if tail <= TAIL_MAX:
            break
        if prev_tail is not None and tail > 0.5 * prev_tail:
            raise ValueError(T("the incident wave's series are not zero at the start of the run (the window's tail "
                               "{tail:.2g} of the peak > {lim}; it does not depend on the window's length): the pulse "
                               "has spectral content at the edge of the band of propagating waves (a Bloch wave's "
                               "cut-off or the grid's band edge), where the spectrum is cut sharply, and the grid's "
                               "wave has a precursor before the start of the run; the leak through the faces would be "
                               "~{leak:.1g}. Narrow the pulse's band, shift its frequency away from the cut-off or "
                               "delay it (t0)", tail=tail, lim=float(TAIL_MAX), leak=0.3 * tail))
        if 2 * tables.nbytes > MAX_TABLE_BYTES:
            raise ValueError(T("the window's tail of the incident wave's series is {tail:.2g} (> {lim}) at the memory "
                               "limit of {mb:.0f} MB: the group delays do not fit into the window; narrow the "
                               "pulse's band or the total-field region", tail=tail, lim=float(TAIL_MAX),
                               mb=MAX_TABLE_BYTES / 2**20))
        prev_tail = tail
        M *= 2
    # the reference: unit E amplitude at r0 (the injected spectrum)
    A0 = np.where(_amplitudes(sim, rec, w, "ez" if (sim.dim == 2 and rec["pol2d"] == "tm") else "ex")[2], 1.0, 0.0)
    ref = np.fft.ifft(X * A0)
    rec["ref_table"] = ref if sim.complex else ref.real
    rec["table"] = tables
    rec["d"] = d
    rec["M"] = M
    rec["tail"] = tail
    rec["omitted"] = omitted or 0.0


def tfsf_to(rec, conv):
    for L in rec["lists"]:
        L["e_idx_d"] = conv(L["e_idx"])
        L["coef_d"] = conv(L["coef"])
        L["row_d"] = conv(L["row"])
        L["nodew_d"] = None if L["nodew"] is None else conv(L["nodew"])
        if rec.get("table") is not None:
            L["d_d"] = conv(rec["d"][L["row"]])
        else:
            L["cwc_d"] = conv(rec["cw"]["coef"][L["row"]])
            L["cwd"] = rec["cw"]["delay"][L["row"]]
            L["cwd_d"] = conv(L["cwd"])
    if rec.get("table") is not None:
        rec["table_d"] = conv(rec["table"])


def _values(sim, rec, L, m: int, t: float):
    """Incident values of list L's source nodes at step index m (time t)."""
    xp = sim.xp
    if rec.get("table") is not None:
        col = m - L["d_d"]
        M = rec["M"]
        ok = (col >= 0) & (col < M)
        colc = xp.clip(col, 0, M - 1)
        v = rec["table_d"][L["row_d"], colc] * ok
    else:
        cw = rec["cw"]
        tt = t - L["cwd_d"]
        if cw["ramp"] > 0:
            s = xp.clip(tt / cw["ramp"], 0.0, 1.0)
            env = s * s * s * (10.0 + s * (-15.0 + 6.0 * s))
        else:
            env = (tt >= 0).astype(float)
        z = L["cwc_d"] * np.exp(-1j * cw["w0"] * t)
        v = (z if sim.complex else xp.real(z)) * env
    if L["nodew_d"] is not None:
        v = v * L["nodew_d"]
    return v


def apply_tfsf(sim, rec, kind: str):
    m = sim.steps
    t = (m + 0.5) * sim.dt if kind == "e" else m * sim.dt
    for L in rec["lists"]:
        if L["kind"] != kind:
            continue
        if "e_idx_d" not in L:
            tfsf_to(rec, lambda a: sim.xp.asarray(a) if sim.xp is not np else a)
        v = _values(sim, rec, L, m, t)
        F = sim.F[L["target"]].reshape(-1)
        idx = L["e_idx_d"]
        co = sim.coef[L["target"]]
        if kind == "e":
            F[idx] = F[idx] + co["cb"].reshape(-1)[idx] * (L["coef_d"] * v)
        else:
            db = co["db"]
            dbv = db if isinstance(db, float) else db.reshape(-1)[idx]
            F[idx] = F[idx] - dbv * (L["coef_d"] * v)


def reference_value(sim, rec, t: float):
    """The injected E amplitude at the reference point at E time t (= steps dt)."""
    if rec.get("table") is not None:
        m = int(round(t / sim.dt))
        ref = rec["ref_table"]
        return ref[m] if 0 <= m < len(ref) else (0j if sim.complex else 0.0)
    cw = rec["cw"]
    pw = rec["src"]
    prof = pw.profile
    env = float(prof.envelope(t))
    z = pw.amplitude * 1j * np.exp(-1j * prof.phase) * np.exp(-1j * cw["w0"] * t) * env
    return complex(z) if sim.complex else float(np.real(z))


def slab_normal_factor(sim, rec, f):
    """K_n / (Omega mu) of a slab wave at frequencies f: its power flux density along the slab's axis per (1/2)|E|^2."""
    w = 2 * math.pi * np.asarray(f, float)
    _, k, ok = _amplitudes(sim, rec, w, "ex")
    un = rec["un"]
    Kn = 2.0 / sim.dx * np.sin(k[un] * sim.dx / 2.0)
    Om = omega_tilde(w, sim.dt)
    return np.where(ok, np.abs(Kn) / (Om * sim.background.mu), np.nan)


def monitor_factor(sim, rec, f, axis: int):
    """How the flux monitor (``fdtd_monitors.Face``) sees this plane wave: its measured flux density through a plane
    normal to ``axis`` divided by the wave's true flux density there, at frequencies f (closed form). The monitor
    averages the tangential E along the axis of the H component it multiplies, and that H across the plane and along
    the same axis, so for the grid's plane wave a term E_t1 H_t2 is multiplied by cos(k_v dx/2) cos^2(k_t2 dx/2)
    (no factor along a collapsed axis): 2-D TM cos(k_v dx/2) cos^2(k_t dx/2), 2-D TE cos(k_v dx/2), normal incidence
    cos(k dx/2) = 1 - (k dx)^2/8 + ... (review B8-fdtd F5)."""
    w = 2 * math.pi * np.asarray(f, float)
    E, H, k, ok, _ = _vectors(sim, rec, w)
    v = int(axis)
    t1, t2 = (v + 1) % 3, (v + 2) % 3

    def c(u):
        return np.cos(k[u] * sim.dx / 2.0) if u < sim.dim else np.ones(len(w))

    true = E[t1] * H[t2] - E[t2] * H[t1]
    meas = np.cos(k[v] * sim.dx / 2.0) * (c(t2) ** 2 * E[t1] * H[t2] - c(t1) ** 2 * E[t2] * H[t1])
    good = ok & (np.abs(true) > 0)
    return np.where(good, meas / np.where(good, true, 1.0), np.nan)
