# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""lfphys.theories.models.photodetector (EX2 §4.7): every closed form against a Monte Carlo of the time stream (5σ),
the limits of an ideal detector, and the devices' values against their data sheets."""

import math

import numpy as np
import pytest

from lfphys.core.quantum import qubits as Q
from lfphys.theories.models import photodetector as PD

rng = np.random.default_rng(2015)


def _sequential(t, td):
    """The non-paralysable rule, one count after another (the plain definition)."""
    keep, last = [], -math.inf
    for x in t:
        if x - last >= td:
            keep.append(True)
            last = x
        else:
            keep.append(False)
    return np.array(keep, bool)


@pytest.mark.parametrize("n_td", [0.01, 0.3, 2.0])
def test_dead_time_scan_equals_the_plain_rule(n_td):
    td = 50e-9
    t = PD.poisson_times(n_td / td, 0.0, 2e-3, rng)
    assert np.array_equal(PD._nonparalysable(t, td), _sequential(t, td))


@pytest.mark.parametrize("R,eta,d,td", [(2e6, 0.7, 1e4, 22e-9), (2e7, 0.65, 100.0, 22e-9), (5e6, 1.0, 0.0, 50e-9),
                                        (1e5, 0.68, 250.0, 20e-9)])
def test_observed_rate_against_the_time_stream(R, eta, d, td):
    det = PD.Detector(eta, d, td, 0.15e-9)
    dur = 4e5 / max(R * eta, 1.0)
    tags = PD.detect(PD.poisson_times(R, 0.0, dur, rng), det, 0.0, dur, rng)
    m = float(PD.detector_rate(R, det))
    assert m == pytest.approx((eta * R + d) / (1 + (eta * R + d) * td), rel=1e-15)
    assert abs(len(tags) - m * dur) < 5 * math.sqrt(m * dur)  # the dead-time count is sub-Poissonian: 5σ is generous
    assert float(PD.true_rate(m, td)) == pytest.approx(eta * R + d, rel=1e-12)
    # the live fraction: the share of time not covered by dead intervals after recorded counts
    tol = 5 * math.sqrt(m * dur) * td / dur
    assert float(PD.live_fraction(m, td)) == pytest.approx(1 - len(tags) * td / dur, abs=tol)


def test_data_sheet_dead_time_correction():
    """SPCM-AQRH Rev 2023-1, Figure 1: Correction Factor = 1/(1 - t_d C_R); Table 1: 1.02 at 1 Mc/s (22 ns gives
    1.0225). The tabulated factors at 5, 10, 20 and 25 Mc/s (1.16, 1.40, 2.35, 3.32) follow the same form to 2.5 % with
    one effective dead time of 28.2 ns (each alone implies 27.6-28.7 ns), not with the nominal 22 ns (2.22 instead of
    3.32 at 25 Mc/s): the form holds, the dead time at high rates is longer than the nominal one."""
    assert float(PD.true_rate(1e6, 22e-9)) / 1e6 == pytest.approx(1.02, abs=0.005)
    table = ((5e6, 1.16), (10e6, 1.40), (20e6, 2.35), (25e6, 3.32))
    implied = [(1 - 1 / cf) / m for m, cf in table]
    assert min(implied) == pytest.approx(27.6e-9, abs=0.1e-9) and max(implied) == pytest.approx(28.7e-9, abs=0.1e-9)
    for m, cf in table:
        assert float(PD.true_rate(m, 28.2e-9)) / m == pytest.approx(cf, rel=0.025)
    assert float(PD.true_rate(25e6, 22e-9)) / 25e6 == pytest.approx(2.22, abs=0.005)
    with pytest.raises(ValueError):
        PD.true_rate(5e7, 22e-9)


@pytest.mark.parametrize("ra,rb,w", [(1e5, 2e5, 25e-9), (3e5, 3e5, 2e-9)])
def test_accidental_rate_against_the_time_stream(ra, rb, w):
    dur = 0.5
    ta, tb = PD.poisson_times(ra, 0, dur, rng), PD.poisson_times(rb, 0, dur, rng)
    n = PD.coincidences(ta, tb, w, delay=100e-9)
    ref = float(PD.accidental_rate(w, ra, rb)) * dur
    assert abs(n - ref) < 5 * math.sqrt(ref)


@pytest.mark.parametrize("w,sa,sb", [(2e-9, 0.5e-9, 0.5e-9), (0.5e-9, 0.5e-9, 0.5e-9), (0.5e-9, 0.1486e-9, 0.1486e-9),
                                     (1e-9, 0.1e-9, 0.4e-9)])
def test_window_share_against_the_time_stream(w, sa, sb):
    n = 200_000
    t = np.sort(rng.uniform(0, 1.0, n))
    a = PD.detect(t, PD.Detector(jitter_sigma=sa), 0, 1.0, rng)
    b = PD.detect(t, PD.Detector(jitter_sigma=sb), 0, 1.0, rng)
    p = PD.window_share(w, sa, sb)
    if sa == sb:
        assert p == pytest.approx(math.erf(w / (4 * sa)), rel=1e-15)
    k = PD.coincidences(a, b, w)
    assert abs(k / n - p) < 5 * math.sqrt(p * (1 - p) / n) + 1e-4  # + the accidental pairs of neighbours (< 1e-5)


def test_ideal_detector_limits():
    t = PD.poisson_times(1e6, 0, 1e-2, rng)
    assert np.array_equal(PD.detect(t, PD.IDEAL, 0, 1e-2, rng), t)
    assert float(PD.observed_rate(3e6, 0.0)) == 3e6
    assert PD.window_share(1e-9, 0.0) == 1.0 and PD.window_share(0.0, 0.0) == 0.0
    assert PD.dark_click_probability(0.0, 1e-6) == 0.0
    assert PD.slot_coupling(0.0, 0.0, 1e-6) == 0.0
    # approaching the limits continuously
    assert float(PD.observed_rate(1e6, 1e-15)) == pytest.approx(1e6, rel=1e-8)
    assert PD.window_share(2e-9, 1e-13) == pytest.approx(1.0, abs=1e-15)
    with pytest.raises(ValueError):
        PD.Detector(eta=1.2)
    with pytest.raises(ValueError):
        PD.Detector(dark_rate=-1.0)


@pytest.mark.parametrize("mean,eta,d", [(0.05, 0.7, 300.0), (0.8, 0.68, 5e4), (0.0, 0.7, 1e5)])
def test_slot_click_probability_against_the_time_stream(mean, eta, d):
    slot, n = 1e-6, 200_000
    det = PD.Detector(eta, d, 22e-9, 0.15e-9)
    t = PD.poisson_times(mean / slot, 0, n * slot, rng)
    clicks = PD.slot_clicks(PD.detect(t, det, 0, n * slot, rng), slot, n)
    p = float(PD.click_probability(mean, det, slot))
    assert p == pytest.approx(-math.expm1(-(eta * mean + d * slot)), rel=1e-15)
    if mean == 0.0:
        assert p == pytest.approx(PD.dark_click_probability(d, slot), rel=1e-15)
    eps = PD.slot_coupling(det.dead_time, det.jitter_sigma, slot)
    assert eps < 0.03
    assert abs(clicks.mean() - p) < 5 * math.sqrt(p * (1 - p) / n) + eps * p


def test_coincidence_rates_against_the_time_stream():
    """A continuous pair source (|Phi+>, polarisers at 0 and 30 degrees, two detectors per station: real devices with
    a bright background) counted with a 25 ns window: per detector pair, the counted coincidences equal the true ones
    in the window plus the accidentals."""
    R, dur, w = 1e5, 1.0, 25e-9
    PA, PB = Q.polarizer_projectors(0.0), Q.polarizer_projectors(math.radians(30))
    P = Q.joint_probabilities(Q.PHI_PLUS, PA, PB)
    da = [PD.Detector(0.7, 2e5, 22e-9, 0.5e-9), PD.Detector(0.65, 1e5, 22e-9, 0.5e-9)]
    db = [PD.Detector(0.68, 1.5e5, 20e-9, 0.15e-9), PD.Detector(0.7, 3e4, 50e-9, 0.15e-9)]
    ref = PD.coincidence_rates(R, P, da, db, w)
    te = PD.poisson_times(R, 0, dur, rng)
    k = rng.choice(4, size=len(te), p=P.ravel())
    ia, ib = k // 2, k % 2
    ta = [PD.detect(te[ia == i], d, 0, dur, rng) for i, d in enumerate(da)]
    tb = [PD.detect(te[ib == j], d, 0, dur, rng) for j, d in enumerate(db)]
    for i in range(2):
        assert abs(len(ta[i]) - ref["singles_a"][i] * dur) < 5 * math.sqrt(ref["singles_a"][i] * dur)
        for j in range(2):
            exp = (ref["true"][i, j] + ref["accidental"][i, j]) * dur
            assert ref["accidental"][i, j] * dur > 100  # the background matters here
            assert abs(PD.coincidences(ta[i], tb[j], w) - exp) < 5 * math.sqrt(exp)


def test_pair_slots_respects_each_stations_clock_and_settings():
    """Slots on each station's own clock (delays 1.7 µs and 0.4 µs): with ideal detectors and |Phi+> at equal settings
    every pair clicks the same port at both stations in its own slot; the settings switch per slot."""
    n, slot = 2000, 1e-6
    pp = [[Q.joint_probabilities(Q.PHI_PLUS, Q.polarizer_projectors(a), Q.polarizer_projectors(b)) for b in (0.0, 0.5)]
          for a in (0.0, 0.5)]
    sa = rng.integers(0, 2, n)
    (ca, cb), (ta, tb) = PD.pair_slots(n, slot, 3e5, pp, sa, sa, [PD.IDEAL, PD.IDEAL], [PD.IDEAL, PD.IDEAL], rng,
                                       delay_a=1.7e-6, delay_b=0.4e-6)
    assert len(ta[0]) + len(ta[1]) == len(tb[0]) + len(tb[1]) > 0.9 * 3e5 * n * slot
    for i in range(2):
        assert np.array_equal(ca[i], cb[i])
    # the absorbed port of a polariser has no detector: one detector per station sees only its port
    (ca1, cb1), _ = PD.pair_slots(n, slot, 3e5, pp, sa, sa, [PD.IDEAL], [PD.IDEAL], rng)
    assert np.array_equal(ca1[0], cb1[0]) and 0.1 < ca1[0].mean() < 0.2


def test_devices_quote_their_data_sheets():
    """SPCM-AQRH Rev 2023-1 Table 1 (650 nm: PDE 65 % typ.; grade -X4: at most 100 counts/s; dead time 22 ns; timing
    resolution 350 ps) and SPCM-NIR Rev 2018-09 Table 2 (800 nm: 68 % typ.; W3: at most 250 counts/s; dead time 20 ns
    typ.; 350 ps)."""
    a = PD.DEVICES["spcm_aqrh_14_650nm"]["detector"]
    b = PD.DEVICES["spcm_nir_800_13"]["detector"]
    assert (a.eta, a.dark_rate, a.dead_time) == (0.65, 100.0, 22e-9)
    assert (b.eta, b.dark_rate, b.dead_time) == (0.68, 250.0, 20e-9)
    for det in (a, b):
        assert 2 * math.sqrt(2 * math.log(2)) * det.jitter_sigma == pytest.approx(350e-12, rel=1e-12)
    for dev in PD.DEVICES.values():
        assert dev["basis"].startswith("Excelitas") and str(dev["title"]) and str(dev["values"])
