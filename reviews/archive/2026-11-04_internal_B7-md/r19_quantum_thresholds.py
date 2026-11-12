"""p03's approximation text: "классическая механика атомов (без квантовых эффектов: для аргона заметны ниже ~ 20 K)".
(a) Solid argon: Debye temperature 85 K (arXiv:1304.2049); the Debye heat capacity against the classical 3k at the
    melting preset's start (20 K) and at 40 K, 80 K.
(b) The playground's molecules: hbar omega / k of a bond k_bond (eps/sigma^2) between two argon-mass atoms, for the
    preset (400) and the parameter's range (1 ... 1e4)."""
import common  # noqa: F401
import math

from scipy import constants as sc
from scipy.integrate import quad

from p03_molecules.viz import PS


def debye_cv(T, theta=85.0):
    x = theta / T
    return 3 * (1 / x) ** 3 * quad(lambda y: y ** 4 * math.exp(y) / (math.exp(y) - 1) ** 2, 0, x)[0]


for T in (20.0, 40.0, 80.0):
    print(f"(a) T = {T:4.0f} K: Debye C_v / (3 N k) = {debye_cv(T):.3f} (classical: 1)")
for kb in (1.0, 400.0, 1e4):
    w = math.sqrt(kb / 0.5) / (PS * 1e-12)
    print(f"(b) k_bond = {kb:7.0f} eps/sigma^2: hbar omega / k_B = {sc.hbar * w / sc.k:7.1f} K")
