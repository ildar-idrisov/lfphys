# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Server side of the 3-D environment's slice planes (RULES.md §2.10; owner, 2026-10-27), shared by every 3-D world:
up to three planes of any orientation, each fixed by its normal and its distance (its centre is its point closest to
the region's centre), placed, moved, removed and reset by the view command ``view``, kept in a new world of the run,
and moved along their normal while world time runs only when "auto" is chosen for them (coarse, rate-limited slices
while they move).

A world mixes ``SlicePlanes`` into its Simulation, calls ``_init_planes()`` and sets before the first plane:
  self.box              ((xmin, ymin, zmin), (xmax, ymax, zmax)): the region slices are computed in
  self.plane_center     the point a plane's centre is taken closest to
  self.default_normals  {1: n1, 2: n2, 3: n3}, mutually perpendicular (plane 1's is the default view)
  self.plane_min_step   the smallest move of an auto plane worth a recompute (a grid step)
  self.plane_time_scale (optional) world seconds per unit of an auto plane's speed (default 1: per second)
and implements
  _plane_slice(pid, pl, s_rng, t_rng, coarse) -> dict   compute the slice (no messages; may raise ValueError)
  _plane_emit(pid)                                      emit plane pid's slice and its checks
optionally
  _plane_preview(pid, pl, s_rng, t_rng)                 emit a coarse slice marked ``preview`` (nothing kept)
  _plane_removed(pid, sl)                               after a plane was removed
  _plane_label(pl)                                      a plane's label (default: lfphys.core.geometry._label)
The world's ``advance`` calls ``_advance_planes(t_target, dt)``.
"""

from __future__ import annotations

import numpy as np

from lfphys.core import geometry as G

from .i18n import T

MAX_PLANES = 3
AUTO_STEPS = 24      # an auto plane is recomputed when it moved 1/24 of its range (or a grid step) ...
AUTO_INTERVAL = 0.5  # ... at most twice per world second


class SlicePlanes:
    def _init_planes(self):
        self.planes = {}  # id -> the plane as sent to the player
        self.slices = {}  # id -> what the world computed on it

    # --- hooks (overridden by the world) -------------------------------------------------------------------------
    def _plane_label(self, pl) -> str:
        return G._label(pl)

    def _plane_preview(self, pid, pl, s_rng, t_rng):
        raise ValueError(T("this world needs no preview of a slice"))

    def _plane_removed(self, pid, sl):
        pass

    # --- geometry --------------------------------------------------------------------------------------------------
    def _depth_range(self, n):
        lo, hi = np.asarray(self.box[0], float), np.asarray(self.box[1], float)
        corners = np.array([[x, y, z] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])])
        return float((corners @ n).min()), float((corners @ n).max())

    def _canonical(self, origin, n):
        """The plane's point closest to the region's centre, with the plane's distance o.n clamped to the box (clipping
        the point itself would move it off the plane): every request with the same normal and distance gives the same
        plane and the same in-plane coordinates. The clamp keeps a grid step inside the box (review 2026-11-04
        UX-params P22: a plane moved past the box stayed on its face, where the slice is all outside: an empty
        window)."""
        dmin, dmax = self._depth_range(n)
        inset = min(float(getattr(self, "plane_min_step", 0.0) or 0.0), 0.25 * (dmax - dmin))
        d = min(max(float(np.asarray(origin, float) @ n), dmin + inset), dmax - inset)
        c = np.asarray(self.plane_center, float)
        return c + (d - c @ n) * n

    def _set_plane(self, pid, origin, normal, auto=False, speed=1.0, coarse=False):
        if pid not in range(1, MAX_PLANES + 1):
            raise ValueError(T("there are at most three slice planes (numbers 1–3)"))
        nrm = np.asarray(normal, float)
        if nrm.shape != (3,) or not np.all(np.isfinite(nrm)) or np.linalg.norm(nrm) < 1e-12:
            raise ValueError(T("the plane's normal is not given"))
        org = np.asarray(origin, float)
        if org.shape != (3,) or not np.all(np.isfinite(org)):
            raise ValueError(T("the plane's centre is not given"))
        nrm = nrm / np.linalg.norm(nrm)
        pl, poly, s_rng, t_rng = G.plane_cut(self._canonical(org, nrm), nrm, self.box)
        sl = self._plane_slice(pid, pl, s_rng, t_rng, coarse)  # nothing changes if this refuses
        sl.setdefault("plane", pl)
        sl.setdefault("coarse", coarse)
        self.planes[pid] = {"id": pid, "origin": [float(c) for c in pl.origin], "normal": [float(c) for c in pl.normal],
                            "u": list(pl.u), "v": list(pl.v), "auto": bool(auto), "speed": float(speed),
                            "polygon": poly.tolist(), "label": self._plane_label(pl)}
        self.slices[pid] = sl
        self._send_planes()
        self._plane_emit(pid)

    def _send_planes(self):
        self._msg({"type": "planes", "t": self.t, "planes": [self.planes[i] for i in sorted(self.planes)]})

    def _reset_planes(self):
        """The default view: plane 1 through the centre with its default normal, the others removed."""
        for pid in sorted(self.planes):
            if pid != 1:
                self._remove_plane(pid)
        self._set_plane(1, self.plane_center, self.default_normals[1])

    def _remove_plane(self, pid):
        self.planes.pop(pid, None)
        sl = self.slices.pop(pid, None)
        self._send_planes()
        self._plane_removed(pid, sl)

    # --- the view command ------------------------------------------------------------------------------------------
    def view(self, args):
        """View commands (the world's physics is unchanged): place or move a slice plane, preview it, remove it, or
        restore the default."""
        op = args.get("op")
        if op == "plane":
            pid = int(args.get("id", 0))
            if pid not in self.planes and len(self.planes) >= MAX_PLANES:
                raise ValueError(T("there are at most three slice planes"))
            cur = self.planes.get(pid, {})
            origin = args.get("origin") or cur.get("origin") or list(self.plane_center)
            normal = args.get("normal") or cur.get("normal") or self.default_normals.get(pid, self.default_normals[1])
            self._set_plane(pid, origin, normal, auto=bool(args.get("auto", cur.get("auto", False))),
                            speed=float(args.get("speed", cur.get("speed", 1.0))))
            moved = False
            try:  # asked for beyond the region: said, not silently moved (review UX-params P22)
                nn = np.asarray(normal, float) / np.linalg.norm(np.asarray(normal, float))
                if abs(float(np.asarray(origin, float) @ nn) - float(np.asarray(self.planes[pid]["origin"]) @ nn)) > \
                        1e-9 * max(1.0, float(np.abs(np.asarray(self.box, float)).max())):
                    moved = True
            except (TypeError, ValueError, ZeroDivisionError):
                pass
            if moved:
                return T("slice {id:d}: {label} (beyond the region's edge the slice is empty — the plane is put at the "
                         "edge, inside the region)", id=pid, label=self.planes[pid]["label"])
            return T("slice {id:d}: {label}", id=pid, label=self.planes[pid]["label"])
        if op == "preview":  # while a plane is dragged: a coarse slice, not kept, not checked
            pid = int(args.get("id", 0))
            if pid not in self.planes:
                raise ValueError(T("there is no slice {id:d}", id=pid))
            nrm = np.asarray(args.get("normal") or self.planes[pid]["normal"], float)
            nrm = nrm / np.linalg.norm(nrm)
            o = self._canonical(args.get("origin") or self.planes[pid]["origin"], nrm)
            pl, _, s_rng, t_rng = G.plane_cut(o, nrm, self.box)
            self._plane_preview(pid, pl, s_rng, t_rng)
            return ""
        if op == "remove":
            pid = int(args.get("id", 0))
            self._remove_plane(pid)
            return T("slice {id:d} removed", id=pid)
        if op == "reset":
            self._reset_planes()
            return T("default slices")
        raise ValueError(T("unknown view command {op}", op=repr(op)))

    def view_state(self):
        """The planes the experimenter placed (pose, auto, speed), kept in a new world of this run."""
        return [{"id": p["id"], "origin": p["origin"], "normal": p["normal"], "auto": p["auto"], "speed": p["speed"]}
                for p in self.planes.values()]

    def adopt_view(self, state):
        if not state:
            return
        for pid in list(self.planes):
            self.planes.pop(pid)
            self.slices.pop(pid, None)
        for p in sorted(state, key=lambda q: q["id"]):
            self._set_plane(int(p["id"]), p["origin"], p["normal"], auto=bool(p.get("auto")),
                            speed=float(p.get("speed", 1.0)))

    # --- time: planes with "auto" move along their normal; the others stay where they are -----------------------------
    def _advance_planes(self, t_target, dt):
        if dt <= 0:
            return
        for pid, pl in list(self.planes.items()):
            if not pl["auto"]:
                continue
            n = np.asarray(pl["normal"])
            dmin, dmax = self._depth_range(n)
            span = dmax - dmin
            scale = getattr(self, "plane_time_scale", 1.0)
            move = pl["speed"] * dt / scale + pl.get("pending", 0.0)
            if abs(move) < max(self.plane_min_step, span / AUTO_STEPS) or \
                    t_target - pl.get("last_auto", -1e9) < AUTO_INTERVAL * scale:
                pl["pending"] = move
                continue
            d = float(np.asarray(pl["origin"]) @ n)
            d_new = dmin + ((d - dmin) + move) % span
            self._set_plane(pid, self._canonical(np.asarray(pl["origin"]) + (d_new - d) * n, n), n, auto=True,
                            speed=pl["speed"], coarse=True)
            self.planes[pid]["last_auto"] = t_target
