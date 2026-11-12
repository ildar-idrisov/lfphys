"""s17 continued: with a heavy particle the wrapper's step is long (a neutron of lambda = 2 nm: dt = 16 units), so even
the palette's default environment (10/ps) has lambda dt > 0.05 and is refused, although _tune_dt would shorten dt."""
import sys
sys.path.insert(0, "/lf/visualizations/tests")
from harness import Harness
from p02_quantum import viz as P

h = Harness("p02_quantum", None, {"dim": "2d", "n2": "256", "size": 80.0, "edges": "open"})
h.cmd("scene", op="add", type="packet", values={"species": "neutron", "x": -10.0, "wavelength": 2.0})
print(f"neutron packet: errors {h.errors()}; dt = {h.sim.qs.dt} units = {h.sim.qs.dt / P.FS:.3g} fs")
h.cmd("scene", op="add", type="env", values={})  # the palette's defaults: 10/ps, a = 2 nm, everywhere
print(f"default environment: lambda dt = {10e12 * P.TU * h.sim.qs.dt:.3g}; errors {h.errors()}")
