# Review B8-fdtd, script s09: the TF/SF plane wave and the cross-section normalization.
# (1) leak of a Bloch slab wave at oblique incidence (complex fields), TM and TE;
# (2) a plane wave added after step 0: FDTD._incident_dft numbers the reference series from step 1 (fdtd.py:1365),
#     so the incident spectrum of monitors started later is cut wrongly -> cross sections;
# (3) a body crossing a TF/SF face is accepted without a word (the validity says "homogeneous background at the faces");
# (4) a 3-D polarization parallel to the direction gives a zero wave without a refusal;
# (5) the flux monitor on the incident grid wave itself: P_face / (I_inc * length) against cos factors.
import argparse
import math

import numpy as np

from lfphys.core.em import fdtd as F

argparse.ArgumentParser(description=__doc__).parse_args()

print("== (1) Bloch slab wave at oblique incidence: leak into the scattered-field side ==")
for pol in ("tm", "te"):
    for f_par in (0.3, 0.6):
        dx = 0.05
        w = F.FDTD((6.0, 1.0), dx, pol=pol, boundary={"x": "pml", "y": "periodic"}, pml=16,
                   bloch=(0.0, 2 * math.pi * f_par))
        prof = F.ModulatedGaussian(1.2, fwidth=0.15)
        w.add_source(F.PlaneWave(prof, ((2.0, -math.inf), (math.inf, math.inf))))
        c = "ez" if pol == "tm" else "hz"
        x = w.coords(c)[0]
        sf = (x > 0.2) & (x < 1.7)
        tf = (x > 2.3) & (x < 5.8)
        msf = mtf = 0.0
        for _ in range(int((prof.end() + 8) / w.dt) // 20):
            w.advance(20)
            a = np.abs(w.field(c))
            msf, mtf = max(msf, a[sf].max()), max(mtf, a[tf].max())
        print(f"  {pol} k_par = 2 pi x {f_par}: leak {msf / mtf:.2e}; omitted energy {w.checks()['tfsf_1']['omitted_energy']:.2e}")

print("== (2) a plane wave added at a later step: cross sections of a PEC-free dielectric cylinder ==")


def cyl(delay_steps, res=20):
    a = 0.5
    fs = np.array([0.4, 0.6, 0.8])
    w = F.FDTD((4.0, 4.0), 1.0 / res, pol="tm", pml=16)
    w.add_body(F.Cylinder((2.0, 2.0), a), F.Medium(eps=2.25))
    width = 1.0 / (2 * math.pi * 0.25)
    w.advance(delay_steps)
    prof = F.ModulatedGaussian(0.7, fwidth=0.25, t0=w.t + 6 * width)
    w.add_source(F.PlaneWave(prof, ((0.8, 0.8), (3.2, 3.2)), direction=0.0))
    sca = w.add_flux(((0.5, 0.5), (3.5, 3.5)), freqs=fs)
    w.advance(int((6 * width + 25) / w.dt) + int(6 * width / w.dt))
    cs = w.cross_sections(sca)
    return cs["sigma_sca"] / (2 * a), w


q0, _ = cyl(0)
for d in (100, 400):
    qd, w = cyl(d)
    print(f"  plane wave added at step {d}: Q_sca / Q_sca(added at step 0) = {np.round(qd / q0, 6)}")

print("== (3) a dielectric slab crossing a TF/SF face: accepted? leak? ==")
w = F.FDTD((5.0, 5.0), 0.05, pol="tm", pml=12)
prof = F.ModulatedGaussian(1.0, fwidth=0.3)
w.add_source(F.PlaneWave(prof, ((1.5, 1.5), (3.5, 3.5)), direction=0.0))
try:
    w.add_body(F.Box((1.0, 2.2), (4.0, 2.8)), F.Medium(eps=2.25))
    print("  accepted (no refusal, no warning in checks():", w.checks().get("tfsf_1"), ")")
except Exception as e:
    print("  refused:", e)

print("== (4) 3-D: polarization parallel to the direction ==")
w = F.FDTD((1.0, 1.0, 1.0), 0.1, pml=6)
try:
    w.add_source(F.PlaneWave(F.ModulatedGaussian(0.8, fwidth=0.3), ((0.3,) * 3, (0.7,) * 3), direction=(0, 0, 1),
                             polarization=(0, 0, 1)))
    w.advance(80)
    print(f"  accepted; max|E| in the box after 80 steps: "
          f"{max(np.abs(w.field(c)).max() for c in ('ex', 'ey', 'ez')):.3e}")
except Exception as e:
    print("  refused:", e)

print("== (5) the flux monitor on the incident grid wave alone (no scatterer), 2-D TM ==")
for deg in (0.0, 30.0, 45.0):
    for res in (10, 20, 40):
        dx = 1.0 / res
        fs = np.array([0.5, 1.0])
        w = F.FDTD((4.0, 4.0), dx, pol="tm", pml=12)
        th = math.radians(deg)
        prof = F.ModulatedGaussian(0.75, fwidth=0.25)
        w.add_source(F.PlaneWave(prof, ((0.5, 0.5), (3.5, 3.5)), direction=th))
        # a plane x = 2 inside the total-field box, length 1 in y
        fid = w.add_flux(((2.0, 1.5), (2.0, 2.5)), freqs=fs)
        w.advance(int((prof.end() + 6) / w.dt))
        P = w.flux(fid)["spectrum"]
        I = w.incident_intensity(fs)
        k = 2 * math.pi * fs
        ratio = P / (I * 1.0 * math.cos(th))
        pred = np.cos(k * math.cos(th) * dx / 2) * np.cos(k * math.sin(th) * dx / 2) ** 2
        print(f"  {deg:4.1f} deg, {res:3d} cells/unit: P/(I L cos th) - 1 = {np.round(ratio - 1, 6)}; "
              f"cos(kx dx/2) cos^2(ky dx/2) - 1 = {np.round(pred - 1, 6)}")
