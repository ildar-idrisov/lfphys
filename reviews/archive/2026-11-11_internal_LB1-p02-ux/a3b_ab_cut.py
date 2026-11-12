# Review LB1-p02-ux, Part A, script a3b: where the drag's gauge factor next to an Aharonov-Bohm tube is discontinuous.
# The factor exp(i q [Lambda_{c+s}(r) - Lambda_c(r - s)]) uses straight-line integrals of A from the wave's mean
# position; when a straight segment crosses the tube, Lambda jumps by the flux. For a wave that has gone round the tube
# the moved wave gets a phase cut where it has amplitude. Measured: the probability on grid links whose phase step
# exceeds 1 rad (the wave's own phase gradient is ~k d = 0.4 rad), the spectrum in the outer third of the band, before
# and after the move; flux 0 as the control. Run as a1 (PYTHONPATH=/lf/lfphys); writes a3b_ab_cut.png.
import math
import numpy as np
from lfphys.core.quantum import scene as Q
import struct
import zlib


def png(path, rgb):
    """a minimal PNG writer (no PIL/matplotlib in the image): rgb uint8 (h, w, 3)"""
    h, w, _ = rgb.shape
    raw = b"".join(b"\x00" + rgb[i].tobytes() for i in range(h))
    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
                + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


def phase_rgb(ph):
    """phase in [-pi, pi] as a hue wheel; NaN grey"""
    hgt = (ph + math.pi) / (2 * math.pi) * 6.0
    i = np.floor(np.nan_to_num(hgt)).astype(int) % 6
    f = np.nan_to_num(hgt) - np.floor(np.nan_to_num(hgt))
    q, t = 1 - f, f
    r = np.choose(i, [1, q, 0, 0, t, 1]); g = np.choose(i, [t, 1, 1, q, 0, 0]); b = np.choose(i, [0, 0, t, 1, 1, q])
    out = (np.stack([r, g, b], -1) * 255).astype(np.uint8)
    out[np.isnan(ph)] = 40
    return out

el = Q.species("electron")


def jumps(psi, thr=1.0):
    rho = np.abs(psi) ** 2
    out = 0.0
    for a in (0, 1):
        ph = np.angle(np.roll(psi, -1, axis=a) * np.conj(psi))
        out += float(np.sum(rho * (np.abs(ph) > thr)) / rho.sum())
    return out


def outer(psi):
    F = np.abs(np.fft.fft2(psi)) ** 2
    n = psi.shape[0]
    m = np.abs(np.rint(np.fft.fftfreq(n) * n))
    M = np.maximum(m[:, None], m[None, :])
    return float(F[M > n / 3].sum() / F.sum())


panels = []
for j, flux in enumerate((0.5, 0.0)):
    s = Q.Scene((384, 384), 0.2, dt=0.01, edges=Q.EdgeLayers(5.0, 4.0), device="cpu")
    s.add(Q.FluxTube([0.0, 0.0], 2 * math.pi * flux, 0.5))
    s.add(Q.Ball([0.0, 0.0], 1.6, 5.0, 1.0))
    pid = s.add_particle(Q.Packet(el, [-8.0, 0.0], [2.0, 0.0], [2.0, 3.0]))
    s.advance(500)
    w0 = s.wave(pid)
    j0, o0 = jumps(w0), outer(w0)
    s.move_particle(pid, [0.0, 6.0])
    w1 = s.wave(pid)
    j1, o1 = jumps(w1), outer(w1)
    print(f"flux {flux} h/e: probability on links with a phase step > 1 rad: {j0:.2e} -> {j1:.2e}; spectrum in the outer "
          f"third of the band: {o0:.2e} -> {o1:.2e}")
    g = s.grid
    ext = [g.axes[1][0], g.axes[1][-1], g.axes[0][0], g.axes[0][-1]]
    # the phase relative to the unmoved wave shifted by the same amount (shows only the gauge factor's pattern)
    from lfphys.core.quantum import schrodinger_nd as S
    ref = S.translate(w0, g, [0.0, 6.0])
    rel = np.angle(w1 * np.conj(ref))
    rel[np.abs(ref) ** 2 < 1e-4 * np.max(np.abs(ref) ** 2)] = np.nan
    ix = (g.axes[0] >= -20) & (g.axes[0] < 30)
    iy = (g.axes[1] >= -20) & (g.axes[1] < 30)
    sub = rel[np.ix_(ix, iy)].T[::-1]  # y up
    img = phase_rgb(sub)
    c0 = (int(np.argmin(np.abs(g.axes[0][ix]))), sub.shape[0] - 1 - int(np.argmin(np.abs(g.axes[1][iy]))))
    img[c0[1] - 3:c0[1] + 4, c0[0]] = 0
    img[c0[1], c0[0] - 3:c0[0] + 4] = 0
    panels.append(img)
    panels.append(np.full((img.shape[0], 6, 3), 255, np.uint8))
png("/out/a3b_ab_cut.png", np.concatenate(panels[:-1], axis=1))
print("a3b_ab_cut.png: left flux 0.5 h/e, right flux 0; window x, y in [-20, 30) nm; phase of the moved wave relative to the "
      "plain translation (hue wheel; grey where |psi|^2 < 1e-4 of its peak); black cross: the tube (origin)")
