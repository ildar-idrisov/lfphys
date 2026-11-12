# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Server side of the 3-D wave-function worlds (plan P14.5: hydrogen, v13; P14.9: quarkonium, v14), shared by both:
the probability cloud |psi|^2 of a stationary state R(r) Y_lm or of a superposition of two (``lfphys.core.quantum.
central3d``), the probability current as glyphs, up to three slice planes (``lfviz.planes3d``) computed exactly for
their plane and checked at points against the world's independent route, and the checks every such world shares.

Time. The world clock runs in seconds. A stationary state's density does not change (its phase turns at E/hbar); a
superposition of two levels oscillates with the Bohr period T = 2 pi hbar / |E_2 - E_1| and is exactly periodic. The
run computes the cloud, the current and the slices at NB = 24 phases of the period, each revealed when the world's
time reaches it (accumulative messages carrying ``bin``); after the first period nothing new exists (the density at
t + T is the density at t, checked when the time reaches T), so frames name the phase they show (``bin``: the last
phase reached, never a later one) and the record stops growing. The cloud is sent as ``cloud`` messages: the amplitude
sqrt(|psi|^2 / peak) in 8 bits (the 3-D texture's own resolution), deflated; one fixed peak, (sum_k |c_k| |psi_k|)^2
maximised over the grid — a bound of |psi(t)|^2 at every t known from the stationary parts alone (review B4-10: the
largest density over the period, computed ahead, told at t = 0 what the cloud would reach) — so that brightness
changes are physical.

Preparation (review UX-ui U12). The state is live: a change of it is an ideal preparation of the new state at the
current moment t_p (``_prepare``): psi(t) = sum_k c_k exp(-i E_k (t - t_p) / hbar) psi_k from then on, the state before
it is discarded (how the system got there — a photon, a measurement — is not modelled). The box, the clouds, the
current, the slices on the planes the experimenter placed and the state's checks are made again from that moment; the
checks of the former state that the new one does not give at once are retired (marked as such, their values stay in
the record); a ``prepared`` message carries the parts of the header that describe the new state (the view starts its
state from it). A change of the cloud's grid alone keeps the state and its time (only the drawing is resampled).

A world subclasses ``OrbitalWorld`` and, before ``_build()``, sets: ``state`` (a ``central3d.Superposition`` in
computational units), ``mu``, ``hbar`` (computational), ``Lu`` (display length units per computational unit),
``units`` (e.g. "Å"), ``tu`` (seconds per computational time unit), ``r_max`` (computational radius beyond which
every R is negligible), ``ng`` (cloud points per axis), ``rb_state`` (the states' size, e.g. the smallest <r>) and
``scale_min`` (the shortest length psi varies on: the finite-difference steps of the checks); and implements ``_reference(x, y, z, t)`` (computational
coordinates and time) -> (psi, abs_tol): psi at points by a route independent of the world's own (another radial
route, scipy's harmonics), with the tolerance that route and the world's justify.
"""

from __future__ import annotations

import math
import zlib

import numpy as np

from lfphys.core import geometry as G
from lfphys.core.quantum import central3d as C
from lfviz.params import _num  # «2,5·10⁻¹⁶»: numbers in the owner's texts
from lfviz.planes3d import SlicePlanes
from lfviz.sim import Simulation as BaseSimulation

NB = 24  # phases per period of a two-level superposition
GLYPHS = 10  # current glyphs per axis (even: none at the nucleus, where psi has a cusp)
BOX_FRAC = 1e-3  # the scene's cube holds the sphere with 1 - BOX_FRAC of the probability
SLICE_N = {False: 160, True: 96}  # longest side of a slice: stationary / superposition (per phase: the record's size)
AUTO_N = 64
DEFAULT_NORMALS = {1: (0.0, -1.0, 0.0), 2: (0.0, 0.0, 1.0), 3: (1.0, 0.0, 0.0)}
RETIRED = " — прежнее состояние"  # a check of a state prepared over (review UX-ui U12)


def deflate(a) -> np.ndarray:
    return np.frombuffer(zlib.compress(np.ascontiguousarray(a).tobytes(), 6), np.uint8)


class OrbitalWorld(SlicePlanes, BaseSimulation):
    group = "Волновая функция"
    route_label = "точно для этой плоскости: ψ в её точках"

    def __init__(self, params, seed, emit):
        super().__init__(params, seed, emit)
        self.params = dict(params)
        self._buf = []
        self.mu, self.hbar = 1.0, 1.0
        self.t_prep = 0.0       # world time (s) at which the state shown was prepared (review UX-ui U12)
        self._check_ids = {}    # id -> label of every check this world emitted (a preparation retires the stale ones)

    # --- construction ---------------------------------------------------------------------------------------------------
    def _build(self, planes=None):
        sp = self.state
        freqs = sp.frequencies()
        if len(freqs) > 1:
            raise ValueError("суперпозиция — не больше двух уровней энергии (один период Бора)")
        self.omega = freqs[0] if freqs else 0.0  # rad per computational time unit
        self.nb = NB if self.omega > 0 else 1
        self.period = 2 * math.pi / self.omega * self.tu if self.omega > 0 else math.inf  # seconds
        rb = max(C.box_radius(o.R, BOX_FRAC, self.r_max) for o in sp.orbitals)
        self.rb = rb
        b = rb * self.Lu
        self.box = ((-b, -b, -b), (b, b, b))
        self.axis = np.linspace(-b, b, self.ng)  # display units
        g = self.axis / self.Lu
        Z, X, Y = np.meshgrid(g, g, g, indexing="ij")  # the volume's order: index iz nx ny + ix ny + iy
        self._grid_psi = [o.psi(X, Y, Z) for o in sp.orbitals]  # stationary parts, computed once
        # one scale for every phase, known without evolving: (sum_k |c_k| |psi_k|)^2 bounds |psi(t)|^2 at every t (review
        # B4-10: the largest density over the period was computed ahead, which told at t = 0 what the cloud would reach)
        self.peak = float(np.max(sum(abs(ck) * np.abs(p) for ck, p in zip(sp.c, self._grid_psi)) ** 2))
        self.revealed = 0
        self.period_checked = self.nb == 1
        self._cont_done = False
        # glyph lattice (cell centres) inside the sphere that holds the cloud
        c = (np.arange(GLYPHS) + 0.5) / GLYPHS * 2 - 1
        gz, gx, gy = np.meshgrid(c, c, c, indexing="ij")
        keep = gx**2 + gy**2 + gz**2 <= 1.0
        self.gpos = np.stack([gx[keep], gy[keep], gz[keep]]) * rb  # computational
        # speeds: one period (or one turn of the phase of a stationary state) in about six wall seconds
        E0 = abs(sp.orbitals[0].energy) or 1.0
        span = self.period if self.nb > 1 else 2 * math.pi * self.hbar / E0 * self.tu
        self.default_speed = span / 6.0
        self.speed_range = (span / 6e4, span * 1e3)
        # slice planes
        self._init_planes()
        self._rev = 0
        self.plane_center = (0.0, 0.0, 0.0)
        self.default_normals = DEFAULT_NORMALS
        self.plane_min_step = 2 * b / self.ng
        self.plane_time_scale = self.default_speed  # an auto plane's speed: display units per (default) wall second
        if planes:  # a preparation keeps the planes the experimenter placed (clamped into the new box)
            for pl in sorted(planes, key=lambda q: q["id"]):
                self._set_plane(int(pl["id"]), pl["origin"], pl["normal"], auto=bool(pl.get("auto")),
                                speed=float(pl.get("speed", 1.0)))
        else:
            self._set_plane(1, self.plane_center, DEFAULT_NORMALS[1])

    def _phases(self, t):
        """exp(-i E_k t / hbar) c_k at computational time t."""
        sp = self.state
        return [ck * np.exp(-1j * o.energy * t / self.hbar) for ck, o in zip(sp.c, sp.orbitals)]

    def _t_bin(self, k):
        """Computational time of phase k."""
        return 0.0 if self.nb == 1 else k * (2 * math.pi / self.omega) / self.nb

    def _density_grid(self, k):
        a = self._phases(self._t_bin(k))
        psi = sum(ak * p for ak, p in zip(a, self._grid_psi))
        return np.abs(psi) ** 2

    def bin_at(self, t_sec):
        """The phase shown at world time t: the last one reached (floor), never a later one (the period counted from
        the state's preparation)."""
        if self.nb == 1:
            return 0
        k = int(math.floor((t_sec - self.t_prep) / self.period * self.nb + 1e-9))
        return min(k, max(self.revealed - 1, 0)) if k < self.nb else k % self.nb

    # --- what is revealed -------------------------------------------------------------------------------------------
    def _reveal(self, k):
        """Phase k reached: its cloud, current and slices, and its checks."""
        q = np.round(np.sqrt(np.clip(self._density_grid(k) / self.peak, 0.0, 1.0)) * 255).astype(np.uint8)
        self._msg({"type": "cloud", "t": self.t, "id": "cloud", "bin": k, "nb": self.nb,
                   "t_bin": self._t_bin(k) * self.tu, "dims": [self.ng] * 3, "enc": "sqrt-u8", "codec": "deflate",
                   "peak": self.peak / self.Lu**3,
                   "note": "√(|ψ|²/пик) в 8 битах (разрешение 3D-текстуры); точные значения — в срезах"},
                  {"data": deflate(q)})
        tk = self._t_bin(k)
        j = C.current(self.state, *self.gpos, t=tk, mu=self.mu, hbar=self.hbar)
        if np.max(np.abs(j)) > 0:
            self._msg({"type": "vectors", "t": self.t, "id": "current", "bin": k, "count": int(self.gpos.shape[1]),
                       "note": "ток вероятности j = (ħ/μ) Im(ψ*∇ψ); длина ~ √|j| по наибольшему в этот момент"},
                      {"pos": (self.gpos.T * self.Lu).astype(np.float32), "vec": j.T.astype(np.float32)})
        self._check_current(k, j)
        if self.nb > 1:
            self._check_dipole(k)
        for pid in sorted(self.slices):
            sl = self.slices[pid]
            if k not in sl["bins"] and not sl["coarse"]:
                sl["bins"][k] = self._slice_values(sl["plane"], sl["s"], sl["t"], k)
                self._send_slice(pid, k)
        self.revealed = k + 1

    def after_header(self):
        buf, self._buf = self._buf, []
        self._send_static()
        self._reveal(0)
        buf, self._buf = buf + self._buf, None
        for meta, blobs in buf:
            self.emit(meta, blobs)

    def _reveal_due(self, t_target):
        """Reveal the phases (and check the period) the state has reached by world time t_target."""
        while self.revealed < self.nb and \
                self.t_prep + self._t_bin(self.revealed) * self.tu <= t_target + 1e-12 * abs(t_target):
            self._reveal(self.revealed)
        if not self.period_checked and t_target >= self.t_prep + self.period:
            self._check_period()

    def advance(self, t_target):
        dt = t_target - self.t
        self.t = t_target
        self._reveal_due(t_target)
        self._advance_planes(t_target, dt)

    def next_event_time(self):
        if self.revealed < self.nb:
            return self.t_prep + self._t_bin(self.revealed) * self.tu
        if not self.period_checked:
            return self.t_prep + self.period
        return None

    def frame(self):
        k = self.bin_at(self.t)
        return {"bin": k, "nb": self.nb, "t_prep": self.t_prep,
                "frac": ((self.t - self.t_prep) / self.period) % 1.0 if self.nb > 1 else 0.0}, {}

    # --- slices ---------------------------------------------------------------------------------------------------------
    def _plane_grid(self, s_rng, t_rng, n_long):
        span = max(s_rng[1] - s_rng[0], t_rng[1] - t_rng[0])
        step = span / (n_long - 1)
        ns = max(2, int(round((s_rng[1] - s_rng[0]) / step)) + 1)
        nt = max(2, int(round((t_rng[1] - t_rng[0]) / step)) + 1)
        return np.linspace(*s_rng, ns), np.linspace(*t_rng, nt)

    def _plane_points(self, pl, s, t):
        """Display coordinates of the plane's grid (nt, ns, 3) and the mask of the points inside the box."""
        o, u, v = (np.asarray(a, float) for a in (pl.origin, pl.u, pl.v))
        P = o + s[None, :, None] * u + t[:, None, None] * v
        b = self.box[1][0] * (1 + 1e-12)
        return P, np.all(np.abs(P) <= b, axis=2)

    def _psi_at(self, P, tk):
        a = self._phases(tk)
        x, y, z = (P[..., i] / self.Lu for i in range(3))
        return sum(ak * o.psi(x, y, z) for ak, o in zip(a, self.state.orbitals))

    def _slice_values(self, pl, s, t, k):
        P, inside = self._plane_points(pl, s, t)
        psi = self._psi_at(P, self._t_bin(k))
        I = np.where(inside, np.abs(psi) ** 2 / self.peak, np.nan)
        return I.astype(np.float32), np.where(inside, np.angle(psi), np.nan).astype(np.float32), psi, inside, P

    def _plane_slice(self, pid, pl, s_rng, t_rng, coarse):
        n_long = AUTO_N if coarse else SLICE_N[self.nb > 1]
        s, t = self._plane_grid(s_rng, t_rng, n_long)
        k_now = self.bin_at(self.t)
        ks = [k_now] if coarse else list(range(max(self.revealed, 1)))
        bins = {k: self._slice_values(pl, s, t, k) for k in ks}
        ver = {"points": 0, "note": "автосмещение: грубый срез, без сверки; полный — когда автосмещение выключено"}
        if not coarse:
            ver = self._verify(bins[k_now], k_now)
        self._rev += 1
        return {"s": s, "t": t, "bins": bins, "coarse": coarse, "verify": ver, "vbin": k_now, "plane": pl,
                "rev": self._rev, "sent": set()}

    def _verify(self, vals, k):
        """psi at the brightest point of the slice and at up to four more with >= 5 % of its density (drawn by the
        run's seeded generator), against the world's independent route (``_reference``)."""
        I, _, psi, inside, P = vals
        flat = np.where(inside, np.abs(psi) ** 2, -1.0).ravel()
        order = np.argsort(flat)[::-1]
        top = flat[order[0]]
        cand = np.nonzero(flat >= 0.05 * top)[0]
        cand = cand[cand != order[0]]
        pick = [int(order[0])] + [int(i) for i in self.rng.choice(cand, size=min(4, len(cand)), replace=False)]
        pts = P.reshape(-1, 3)[pick] / self.Lu
        ref, tol = self._reference(pts[:, 0], pts[:, 1], pts[:, 2], self._t_bin(k))
        got = psi.ravel()[pick]
        err = np.abs(got - ref)
        amp = math.sqrt(self.peak)
        return {"points": len(pick), "max_err": float(np.max(err) / amp), "tol": float(np.max(tol) / amp),
                "ok": bool(np.all(err <= tol)), "bin": k}

    def _plane_emit(self, pid):
        sl = self.slices[pid]
        for k in sorted(sl["bins"]):
            self._send_slice(pid, k)
        ver = sl["verify"]
        if ver.get("points"):
            pl = sl["plane"]
            when = "" if self.nb == 1 else f", фаза {ver['bin'] + 1} из {self.nb}"
            self._check(f"slice_{pid}", f"Срез {pid} ({G._label(pl)}{when}): ψ в {ver['points']} точках против "
                                        f"независимого расчёта", ver["max_err"], 0.0, tol=ver["tol"], ok=ver["ok"],
                        note=self.verify_note + "; разность и допуск — доли √(пика |ψ|²)")

    def _plane_removed(self, pid, sl):
        if sl and sl["verify"].get("points"):
            self._check(f"slice_{pid}", f"Срез {pid}: убран", None, None, info=True,
                        note="последняя сверка этого среза — в записи запуска")

    def _send_slice(self, pid, k):
        sl = self.slices[pid]
        if k in sl["sent"]:
            return
        sl["sent"].add(k)
        I, ph, *_ = sl["bins"][k]
        pd = self.planes.get(pid) or {}
        pl = sl["plane"]
        ver = sl["verify"] if k == sl.get("vbin") else {"points": 0, "note": (
            f"сверен срез фазы {sl['vbin'] + 1}" if sl["verify"].get("points") else sl["verify"].get("note", ""))}
        meta = {"type": "slice", "t": self.t, "id": pid, "shape": list(I.shape), "coarse": bool(sl["coarse"]),
                "s": [float(sl["s"][0]), float(sl["s"][-1]), len(sl["s"])],
                "tt": [float(sl["t"][0]), float(sl["t"][-1]), len(sl["t"])],
                "origin": pd.get("origin", [float(c) for c in pl.origin]), "u": pd.get("u", list(pl.u)),
                "v": pd.get("v", list(pl.v)), "normal": pd.get("normal", [float(c) for c in pl.normal]),
                "label": pd.get("label", G._label(pl)), "peak": self.peak / self.Lu**3, "route": "exact",
                "route_label": self.route_label + ("" if self.nb == 1 else f" (фаза {k + 1} из {self.nb})"),
                "exact": True, "approximation": False, "reason": "", "verify": ver,
                "verify_title": self.verify_note, "units": self.units, "depth": False, "window_est": 0.0,
                "bin": k, "nb": self.nb, "t_bin": self._t_bin(k) * self.tu, "rev": sl["rev"]}
        blobs = {"I": I}
        if not sl["coarse"]:
            blobs["phase"] = ph
        self._msg(meta, blobs)

    # --- checks shared by the worlds ------------------------------------------------------------------------------------
    def _check(self, cid, label, value, ref, unit="", note="", tol=1e-9, ok=None, info=False):
        rel = None
        if ref is not None and value is not None and ref != 0:
            rel = (value - ref) / abs(ref)
        d = {"type": "check", "t": self.t, "id": cid, "label": label, "value": value, "ref": ref, "unit": unit,
             "rel": rel, "group": self.group, "note": note, "tol": tol}
        if ok is not None:
            d["ok"] = bool(ok)
        if info:
            d["info"] = True
        self._check_ids[cid] = label
        self._msg(d)

    def _check_current(self, k, j):
        """The drawn current (centred differences) against what the physics fixes without them: a real wave function
        carries none; a single complex state R Y_lm circulates, j = (hbar m / mu) |psi|^2 phi_hat / rho; a
        superposition obeys d rho / dt + div j = 0 (both sides by centred differences; for a superposition of one
        energy d rho / dt = 0 and the current is divergence free), truncation and round-off as tolerance."""
        sp = self.state
        x, y, z = self.gpos
        jmax = float(np.max(np.abs(j)))
        if len(sp.orbitals) == 1:
            o = sp.orbitals[0]
            if o.real or o.m == 0:
                self._check("current", "Ток вероятности вещественной функции равен нулю", jmax, 0.0, tol=0.0,
                            ok=jmax == 0.0, note="Im(ψ*∇ψ) = 0 точно: стрелок нет")
                return
            jc = C.azimuthal_current(o, x, y, z, self.mu, self.hbar)
            j2 = C.current(sp, x, y, z, 0.0, self.mu, self.hbar, h=2e-5 * self.rb)
            trunc = float(np.max(np.abs(j - j2))) * 4 / 3  # O(h^2): the step h against 2h estimates the truncation
            tol = trunc + 64 * np.finfo(float).eps * float(np.max(np.abs(sp.psi(x, y, z)) ** 2)) / (1e-5 * self.rb)
            d = float(np.max(np.abs(j - jc)))
            self._check("current", f"Ток вероятности: кольца вокруг оси z (m = {o.m:+d}) против замкнутой формулы",
                        d / jmax, 0.0, tol=tol / jmax, ok=d <= tol,
                        note="рисуемый ток — центральные разности ψ; эталон j = (ħm/μ)|ψ|²φ̂/ρ; доля max|j|; "
                             "допуск — оценка усечения (шаг h против 2h) и округления")
            return
        if self._cont_done or k not in (0, self.nb // 4):
            return
        T = 2 * math.pi / self.omega if self.omega > 0 else 2 * math.pi * self.hbar / abs(sp.orbitals[0].energy)
        tk = self._t_bin(k)
        rho = lambda tt: np.abs(sp.psi(x, y, z, tt)) ** 2  # noqa: E731
        ht = 1e-4 * T
        drho = (rho(tk + ht) - rho(tk - ht)) / (2 * ht)
        if self.nb > 1:
            # rho = A + |B| cos(omega t - phi): at t = 0 or a quarter period later |d rho/dt| is at least 1/sqrt 2
            # of its largest value; the check waits for the phase where it is
            amp = self.omega * 2 * float(np.max(np.prod([np.abs(ck * o.psi(x, y, z)) for ck, o in
                                                          zip(sp.c, sp.orbitals)], axis=0)))
            if k == 0 and float(np.max(np.abs(drho))) < 0.5 * amp:
                return
        self._cont_done = True
        h0 = 1e-3 * self.scale_min  # the shortest length psi varies on (e.g. a / Z at the nucleus)

        def residual(f):
            h, hj, htf = h0 * f, 1e-2 * h0 * f, ht * f
            dr = (rho(tk + htf) - rho(tk - htf)) / (2 * htf)
            jf = lambda a, b, c: C.current(sp, a, b, c, tk, self.mu, self.hbar, hj)  # noqa: E731
            div = ((jf(x + h, y, z)[0] - jf(x - h, y, z)[0]) + (jf(x, y + h, z)[1] - jf(x, y - h, z)[1]) +
                   (jf(x, y, z + h)[2] - jf(x, y, z - h)[2])) / (2 * h)
            return dr + div
        far = x * x + y * y + z * z > (20 * h0) ** 2  # psi has a cusp at the nucleus: no derivatives there
        r1, r2 = residual(1.0)[far], residual(2.0)[far]
        res = float(np.max(np.abs(r1)))
        roundoff = 4 * np.finfo(float).eps * float(np.max(rho(tk))) * self.hbar / self.mu / (1e-2 * h0 * h0)
        tol = float(np.max(np.abs(r2 - r1))) + 2 * roundoff  # a pure truncation error grows 4x when h doubles
        scale = max(float(np.max(np.abs(drho))), jmax / self.rb_state)
        what = "∂ρ/∂t + ∇·j = 0" if self.nb > 1 else "∇·j = 0 (одна энергия: ∂ρ/∂t = 0)"
        if scale == 0.0:
            # review UX-params P3: real states of one energy with real coefficients (2p_z + 2s): j = 0 and d rho/dt = 0
            # everywhere, so the identity holds term by term; the share of the scale divided by zero and killed the
            # worker («float division by zero»). The residual itself must then be exactly zero
            self._check("continuity", f"Уравнение непрерывности {what} в узлах стрелок", res, 0.0, tol=0.0,
                        ok=res == 0.0,
                        note="ток равен нулю всюду и ∂ρ/∂t = 0 (вещественные состояния одной энергии с вещественными "
                             "коэффициентами): тождество выполняется почленно, невязка — ровно 0")
            return
        self._check("continuity", f"Уравнение непрерывности {what} в узлах стрелок", res / scale, 0.0,
                    tol=tol / scale, ok=res <= tol,
                    note=f"доля масштаба {scale:.2e} (max|∂ρ/∂t| или max|j|/⟨r⟩); производные — центральные разности "
                         f"по t, x, y, z с шагами h и 2h: невязка должна быть ошибкой усечения (расти вчетверо с "
                         f"шагом), допуск — |невязка(2h) − невязка(h)| + округление")

    def _dipole_ref(self):
        """<1| r |2> (complex 3-vector, computational units) and how it was obtained (a world may give a closed
        form); default: the quadrature of central3d."""
        a, b = self.state.orbitals
        return C.dipole(a, b, self.r_max), "матричный элемент ⟨1|r|2⟩ — квадратура (радиальные панели × точное " \
                                            "правило по углам)"

    def _check_dipole(self, k):
        """<r>(t_k) of the run's own psi(t) by 3-D quadrature against 2 Re(c1* c2 <1|r|2> e^{-i omega t})."""
        sp = self.state
        tk = self._t_bin(k)
        r, wr = C.radial_quadrature(self.r_max, 300)
        lmax = max(o.l for o in sp.orbitals) + 1
        T, P, W = C.angular_quadrature(lmax + 1)
        R3, T3 = r[:, None], T[None, :]
        X, Y, Z = R3 * np.sin(T3) * np.cos(P), R3 * np.sin(T3) * np.sin(P), R3 * np.cos(T3)
        w = wr[:, None] * r[:, None] ** 2 * W[None, :]
        dens = np.abs(sp.psi(X, Y, Z, tk)) ** 2
        got = np.array([np.sum(w * dens * X), np.sum(w * dens * Y), np.sum(w * dens * Z)])
        D, how = self._dipole_ref()
        closed = not how.startswith("матричный элемент ⟨1|r|2⟩ — квадратура")
        (c1, c2), (o1, o2) = sp.c, sp.orbitals
        ref = 2 * np.real(np.conj(c1) * c2 * D * np.exp(-1j * (o2.energy - o1.energy) * tk / self.hbar))
        err = float(np.max(np.abs(got - ref)))
        amp = float(np.max(np.abs(D))) * 2 * abs(c1 * c2) or 1.0
        i = int(np.argmax(np.abs(D)))
        self._check("dipole", f"⟨{'xyz'[i]}⟩ в фазе {k + 1} из {self.nb} (t = {tk * self.tu:.4g} с) — по облаку "
                              f"этого запуска против 2Re(c₁*c₂⟨1|r|2⟩e^(−iωt))", float(got[i] * self.Lu),
                    float(ref[i] * self.Lu), self.units, tol=1e-9, ok=err <= 1e-9 * amp, info=not closed,
                    note=f"⟨r⟩(t) — 3D-квадратура |ψ(t)|²; эталон: частота Бора ω = ΔE/ħ и {how}; "
                         f"допуск 1e-9 амплитуды колебания (квадратуры точны до ~1e-13)" + (
                             "" if closed else "; эталон из тех же орбиталей, что и облако: это сверка "
                             "согласованности зависимости от времени и квадратур, а не самих функций (их проверяют "
                             "энергия, ⟨r⟩, узлы, непрерывность тока и срезы; review B4-9)"))

    def _check_period(self):
        """When the time reaches T: the density at T equals that at 0 (to round-off): the reuse of the phases after
        the first period rests on this."""
        d = self._density_grid(0)
        aT = self._phases(2 * math.pi / self.omega)
        dT = np.abs(sum(ak * p for ak, p in zip(aT, self._grid_psi))) ** 2
        err = float(np.max(np.abs(dT - d)) / self.peak)
        self._check("period", "Облако через период Бора T совпадает с облаком в t = 0", err, 0.0, tol=1e-12,
                    ok=err <= 1e-12, info=True,
                    note=f"T = 2πħ/ΔE = {self.period:.4g} с; доля пика; тождество (e^(−iE_k T/ħ) по построению): "
                         f"подтверждает, что после первого периода можно показывать уже посчитанные фазы (кадр "
                         f"называет свою), физику не проверяет (review B4-9)")
        self.period_checked = True

    # --- messages -------------------------------------------------------------------------------------------------------
    def _msg(self, meta, blobs=None):
        if self._buf is not None:
            self._buf.append((meta, blobs))
        else:
            self.emit(meta, blobs)

    def _send_static(self):
        """The radial distributions r^2 R^2 of the states (computed), for the panel."""
        r = np.linspace(0.0, self.rb * 1.15, 400)
        P = np.stack([o.R(r) ** 2 * r * r for o in self.state.orbitals]).astype(np.float32)
        self._msg({"type": "radial", "t": self.t, "units": self.units, "r_max": float(r[-1] * self.Lu),
                   "count": len(r), "states": len(self.state.orbitals)}, {"P": P / self.Lu})

    # --- live: the state, prepared at the current moment (review UX-ui U12) ---------------------------------------------
    def _prepare(self, build, keep_time=False, notices=()):
        """Prepare the state ``build()`` sets (the world's state attributes, as its constructor does) at the current
        moment, or — ``keep_time`` — the same state again with the time it was prepared at (a new cloud grid). The box,
        the cloud and current of the phases reached, the slices of the planes in place, the radial distributions and the
        checks are made for it; ``prepared`` goes first, so that the view starts its state from it; the checks of the
        former state the new one does not give now are retired. All or nothing: a failure leaves the world as it was."""
        saved = dict(self.__dict__)
        rng = self.rng.bit_generator.state
        planes = self.view_state()
        old = dict(self._check_ids)
        self._buf = []
        try:
            build()
            if not keep_time:
                self.t_prep = self.t
            self._check_ids = {}
            self._build(planes)
            self._checks()
            self._send_static()
            self._reveal_due(self.t)
            for text in notices:
                self._msg({"type": "notice", "t": self.t, "text": text})
            buf = self._buf
            hd, _ = self.header()
            stale = [(cid, lab) for cid, lab in old.items() if cid not in self._check_ids]
            retire = []
            for cid, lab in stale:
                lab = lab if lab.endswith(RETIRED) else lab + RETIRED
                retire.append(({"type": "check", "t": self.t, "id": cid, "label": lab, "value": None, "ref": None,
                                "unit": "", "rel": None, "group": self.group, "tol": 0.0, "info": True,
                                "note": f"состояние приготовлено заново в t = {_num(float(f'{self.t:.6g}'))} с; эта сверка относилась к "
                                        f"прежнему (её значения — в записи до этого момента); если она относится и к "
                                        f"новому, она появится, когда до неё дойдёт время"}, None))
                self._check_ids[cid] = lab
            self._buf = None
        except Exception:
            self.__dict__.clear()
            self.__dict__.update(saved)
            self.rng.bit_generator.state = rng
            raise
        self.emit({"type": "prepared", "t": self.t, "t_prep": self.t_prep, "keep_time": bool(keep_time),
                   "header": {k: v for k, v in hd.items() if k != "type"}})
        for meta, blobs in retire + buf:
            self.emit(meta, blobs)

    def scene(self, objects):
        b = self.box[1][0]
        layers = [{"id": "cloud", "label": "Облако |ψ|² (плотность вероятности)", "kind": "volume", "visible": True,
                   "look": {"density": 0.9, "threshold": 0.01}},
                  {"id": "current", "label": "Ток вероятности (стрелки)", "kind": "vectors", "visible": True}]
        return {"box": [list(self.box[0]), list(self.box[1])], "units": self.units, "objects": objects,
                "layers": layers, "planes": {"max": 3, "center": [0.0, 0.0, 0.0],
                                             "defaults": {str(i): list(v) for i, v in DEFAULT_NORMALS.items()},
                                             "time_unit": f"({self.default_speed:.3g} с)"},
                "half": b}
