# Review B6-framework, script s11: lfphys.core.backend's temperature guard (CPU only: no GPU is touched; CuPy's
# availability and the temperature reader are replaced in this process).
#  (a) a hot reading, then the sensor stops answering (NVML returns an error, or the reader raises): the latch stays
#      "hot" with temp = None and choose() formats None with :.0f -> TypeError in every kernel call that wanted the GPU.
#  (b) where a mid-world switch of the device is reported: sim.py emits the backend's report only with a header.
# Usage: see s01; python3 /out/s11_thermal_guard.py
import subprocess

from lfphys.core import backend as B

name = "optics.angular_spectrum"
B._cupy = lambda: (None, {"available": True})  # pretend the GPU is there (nothing is computed on it here)
B._SETTINGS["kernels"][name] = {"device": "gpu"}
B.THERMAL["period_s"] = 0.0
for label, reader in [("NVML answers None after a hot reading", iter([90.0, None]).__next__),
                      ("the reader raises after a hot reading", iter([90.0]).__next__)]:
    B.set_temperature_reader(reader)
    ch = B.choose(name, 10 ** 6)
    print(f"{label}: first call -> {ch.device}, {ch.reason!r}")
    try:
        ch = B.choose(name, 10 ** 6)
        print("   second call ->", ch.device, repr(ch.reason))
    except Exception as e:  # noqa: BLE001
        print(f"   second call raises {type(e).__name__}: {e};  thermal() = {B.thermal()}")
B.set_temperature_reader(None)
print("--- (b) where the backend's report is emitted (sim.py) ---")
print(subprocess.run(["grep", "-n", "_backend_info\\|B.used()", "/lf/visualizations/server/lfviz/sim.py"],
                     capture_output=True, text=True).stdout)
