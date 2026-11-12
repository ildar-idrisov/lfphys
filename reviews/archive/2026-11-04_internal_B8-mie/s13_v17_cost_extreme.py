# Review B8-mie, script s13: the cost of the largest world v17 admits (x up to 2e4 at 380 nm): radius 600 um, width
# 0.3 (x_hi = 18850 at 380 nm), 24 wavelengths (the default): the build and the first wavelength's wall time and the
# process's peak memory. No label in the schema warns about such a world (only big_drops says "~минута").
import resource, sys, time
for p in ("/lf/visualizations", "/lf/visualizations/server", "/lf/lfphys", "/lf/visualizations/tests"):
    sys.path.insert(0, p)
from harness import Harness  # noqa: E402
from v17_mie_scattering.viz import T_LAM  # noqa: E402
t0 = time.time()
h = Harness("v17_mie_scattering", "rainbow", {"radius_um": 600.0, "width": 0.3})
tb = time.time() - t0
t1 = time.time()
h.run_to(T_LAM + 1e-9)
t2 = time.time() - t1
sm = h.of("sky")[-1]
print(f"radius 600 um +-30 %: build {tb:.1f} s (x = {h.of('mono')[-1]['x']:.0f} at 550 nm), first wavelength {t2:.1f} s "
      f"({sm['lam_nm']:.0f} nm, {sm['n_nodes']} nodes, dx {sm['dx']:.2f}, coarse {sm['coarse']}); {h.sim.sky_n} wavelengths; "
      f"peak RSS {resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6:.2f} GB; checks failing: "
      f"{[k for k, c in h.checks().items() if not c.get('info') and c.get('ok') is False]}")
