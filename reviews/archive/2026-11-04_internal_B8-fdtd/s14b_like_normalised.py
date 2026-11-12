# Review B8-fdtd, script s14b: from s14_meep.out, the engine's 40-cell R divided by its monitor factor cos(k dx/2)
# (the incident grid wave's measured flux / I_inc, s09 (5)) against Meep's 40-cell R (normalised by its own flux of
# the incident wave): the like-normalised difference, next to the difference as the comparison test takes it.
import argparse
import math
import re
argparse.ArgumentParser(description=__doc__).parse_args()
for line in open("/out/s14_meep.out"):
    m = re.match(r"\s+(slab|drude) f=([\d.]+): exact ([\d.]+) \| eng ([\d.]+) ([\d.]+) .*\| meep ([\d.]+) ([\d.]+)", line)
    if not m:
        continue
    name, f, ex, e20, e40, m20, m40 = m.group(1), *map(float, m.groups()[1:])
    fac = math.cos(2 * math.pi * f / 40 / 2)
    print(f"  {name:5s} f={f:4.2f}: |eng - meep| = {abs(e40 - m40):.2e};  |eng/cos(k dx/2) - meep| = "
          f"{abs(e40 / fac - m40):.2e}  (R = {m40:.6f})")
