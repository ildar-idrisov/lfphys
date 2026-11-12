"""set_piston on an axis whose hi wall is thermal removes that wall without carrying its heat into the first-law
balance (set_wall and remove_thermostat do carry it): the residual jumps by the wall's heat. Ideal gas (no forces):
the bookkeeping is otherwise exact, so the residual should stay at round-off."""
import common  # noqa: F401

from lfphys.core.md.system import MD

md = MD(dim=2, box=(10.0, 10.0), boundary="walls", pair=None, dt=0.01, seed=3)
md.add_species("A")
md.fill("A", n=400, T=1.0)
md.set_wall("y", "hi", "thermal", T=3.0)
md.reset_counters()
md.step(2000)
b = md.energy_balance()
print(f"before: Q = {b['Q']:.6f}  W = {b['W']:.6f}  residual = {b['residual']:.3e}")
heat_hi = md.counters()["walls"]["y-hi"]["heat"]
md.set_piston("y", X=10.0, mass=float("inf"), V=0.0)
b = md.energy_balance()
print(f"after set_piston: Q = {b['Q']:.6f}  W = {b['W']:.6f}  residual = {b['residual']:.6f}  "
      f"(the y-hi wall's heat was {heat_hi:.6f})")
# control: replacing the wall by set_wall keeps the balance
m2 = MD(dim=2, box=(10.0, 10.0), boundary="walls", pair=None, dt=0.01, seed=3)
m2.add_species("A")
m2.fill("A", n=400, T=1.0)
m2.set_wall("y", "hi", "thermal", T=3.0)
m2.reset_counters()
m2.step(2000)
m2.set_wall("y", "hi", "specular")
print(f"control (set_wall to specular): residual = {m2.energy_balance()['residual']:.3e}")
