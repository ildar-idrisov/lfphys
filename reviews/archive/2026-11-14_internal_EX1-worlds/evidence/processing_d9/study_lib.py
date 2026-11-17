import math
import numpy as np

def basis(nb=200, fr=10.0, env=0.35):
    """Two slits: A_j(x) = sinc(env 4 x) exp(+-i pi fr x / 2), x in [-1, 1], averaged over nb bins (16 points each)."""
    sub = 16
    xe = np.linspace(-1, 1, nb + 1)
    xs = (xe[:-1, None] + (np.arange(sub)[None, :] + 0.5) / sub * (xe[1] - xe[0])).ravel()
    E = np.sinc(env * 4 * xs)
    A1, A2 = E * np.exp(1j * math.pi * fr * xs / 2), E * np.exp(-1j * math.pi * fr * xs / 2)
    rb = lambda f: f.reshape(nb, sub).mean(axis=1)
    return rb(np.abs(A1) ** 2), rb(np.abs(A2) ** 2), rb((A1 * A2.conj()).real) + 1j * rb((A1 * A2.conj()).imag)

def pattern(b, g11, g22, gam, phi=0.3):
    b11, b22, b12 = b
    G12 = gam * math.sqrt(g11 * g22) * np.exp(1j * phi)
    return np.maximum(g11 * b11 + g22 * b22 + 2 * (G12 * b12).real, 0)
