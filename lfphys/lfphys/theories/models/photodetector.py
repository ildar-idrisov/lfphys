# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Single-photon detectors in time: efficiency, dark counts, dead time, timing jitter, the coincidence window and the
locally defined time slots of a Bell test (EX2 design §4.7). A device model with measured parameters: the values of
real devices are in ``DEVICES``, quoted from their data sheets.

The model of one detector (``Detector``):
* each photon reaching it is detected with probability ``eta`` (independently: a threshold detector does not resolve
  the photon number);
* dark counts form a Poisson process of rate ``dark_rate`` (the SPCM-AQRH data sheet, note 6: "In the dark, the module
  generates random counts that follow a Poisson distribution.");
* after each recorded count the detector is dead for ``dead_time`` (non-paralysable: a photon or dark count arriving
  while dead is lost and does not extend the dead time). For a Poisson input of rate n the observed rate is
  m = n / (1 + n t_d); inverted, n = m / (1 - m t_d), the data sheet's "Correction Factor = 1/(1 - (t_d x C_R))" with
  C_R the output count rate ("The theoretical value, at low count rate", SPCM-AQRH Rev 2023-1, Figure 1);
* each recorded count's time tag carries Gaussian jitter of standard deviation ``jitter_sigma`` (a stated shape: a
  silicon SPAD's response has a slower, non-Gaussian tail that is not modelled).

Two stations:
* a coincidence is a pair of tags with |t_B - t_A - delay| <= w/2 (a window of full width w). Two uncorrelated Poisson
  streams of rates R_A, R_B give accidental coincidences at the rate R_acc = w R_A R_B (Dehlinger and Mitchell 2002:
  N_acc = tau N_A N_B / T for a coincidence window tau); the true coincidences of one pair fall inside the window with
  probability erf(w / (2 sqrt 2 sigma_d)), sigma_d^2 = sigma_A^2 + sigma_B^2 (erf(w / (4 sigma)) for equal jitters);
* a locally defined slot k of length Ts is [t0 + k Ts, t0 + (k + 1) Ts) on the station's own clock; the slot's outcome
  for a detector is whether it recorded at least one tag in it. Slots are independent trials when the dead time and
  the jitter are far below the slot (``slot_coupling`` = (t_d + 5 sigma_j) / Ts << 1); then a slot's outcome
  probabilities are those of ``lfphys.tools.bell_stats.slot_probabilities``.

The time-stream Monte Carlo (``detect``, ``pair_slots``, ``coincidences``, ``slot_clicks``) is the second method
against which every closed form here is tested.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from lfphys.i18n import T

ABOUT = {
    "layer": "theories", "kind": "model",
    "title": T("Single-photon detectors in time"),
    "statement": T("A threshold detector with efficiency η, Poisson dark counts, a non-paralysable dead time and "
                   "Gaussian timing jitter; the observed rate m = (ηR + d)/(1 + (ηR + d)t_d), the accidental "
                   "coincidences w·R_A·R_B in a window of full width w, the share erf(w/(4σ)) of true coincidences "
                   "inside it, locally defined time slots; a time-stream Monte Carlo of the counts."),
    "validity": T("a device model with measured parameters (the values of real devices quoted from their data "
                  "sheets); the observed rate is exact for a Poisson input and a non-paralysable dead time; the slots "
                  "are independent trials when (t_d + 5σ)/T_s ≪ 1; accidentals to first order in w·R"),
    "basis": [T("Excelitas Technologies, SPCM-AQRH Series data sheet and operating manual, Rev 2023-1: Table 1, "
                "Table 4, Figure 1 (the dead-time correction factor), notes 6–8, 13–14"),
              T("Excelitas Technologies, SPCM-NIR product brief, Rev 2018-09: Table 2"),
              T("Dehlinger and Mitchell, Am. J. Phys. 70, 903 (2002): the accidental coincidences N_acc = τN_AN_B/T"),
              T("Giustina et al., PRL 115, 250401 (2015): locally defined time slots")],
    "conflicts": [T("not modelled: afterpulsing (0.5–1 % of the counts of a silicon SPAD module by its data sheet), "
                    "twilight events at the end of the dead time, a count-rate-dependent efficiency and the "
                    "non-Gaussian tail of the timing response; the data sheet's dead-time correction holds «at low "
                    "count rate»: its tabulated linearity factors at 5–25 Mc/s follow the same form to 2.5 % only "
                    "with an effective dead time of 28 ns instead of the nominal 22 ns; the ideal detector of the "
                    "core (η = 1, no dark counts, no dead time, no jitter) is the limit of this model")],
}

#: sigma of a Gaussian of full width at half maximum 1: 1 / (2 sqrt(2 ln 2))
FWHM_TO_SIGMA = 1.0 / (2.0 * math.sqrt(2.0 * math.log(2.0)))


@dataclass(frozen=True)
class Detector:
    """One single-photon detector: efficiency (0..1), dark-count rate (s^-1), non-paralysable dead time (s), Gaussian
    jitter of its time tags (standard deviation, s)."""
    eta: float = 1.0
    dark_rate: float = 0.0
    dead_time: float = 0.0
    jitter_sigma: float = 0.0

    def __post_init__(self):
        if not 0.0 <= self.eta <= 1.0:
            raise ValueError(T("detector efficiency η must lie in [0, 1], got {x:.4g}", x=float(self.eta)))
        for name, x in (("dark_rate", self.dark_rate), ("dead_time", self.dead_time),
                        ("jitter_sigma", self.jitter_sigma)):
            if not (math.isfinite(x) and x >= 0.0):
                raise ValueError(T("detector parameter {name} must be finite and non-negative, got {x:.4g}",
                                   name=name, x=float(x)))


IDEAL = Detector()

#: real devices, each value quoted from the data sheet named in ``basis`` (``values``: which number is typical and
#: which a maximum). The timing resolution is given by the data sheet as one number, 350 ps, without naming the width
#: measure; it is read as the full width at half maximum (the measure Excelitas's timing-resolution papers use).
DEVICES = {
    "spcm_aqrh_14_650nm": {
        "detector": Detector(eta=0.65, dark_rate=100.0, dead_time=22e-9, jitter_sigma=350e-12 * FWHM_TO_SIGMA),
        "title": T("Excelitas SPCM-AQRH-14 (silicon SPAD module) at 650 nm"),
        "values": T("photon detection efficiency 65 % typical at 650 nm (minimum 50 %); dark counts at most 100 per "
                    "second (grade -X4); dead time 22 ns typical (Table 1; Table 4 of the same revision: 24 ns); "
                    "timing resolution 350 ps typical at 825 nm, read as FWHM (σ = 149 ps); afterpulsing 0.5 % "
                    "typical, not modelled"),
        "basis": "Excelitas Technologies, SPCM-AQRH Series, Rev 2023-1, Table 1 and Table 4",
    },
    "spcm_nir_800_13": {
        "detector": Detector(eta=0.68, dark_rate=250.0, dead_time=20e-9, jitter_sigma=350e-12 * FWHM_TO_SIGMA),
        "title": T("Excelitas SPCM-NIR (SPCM-800-13, silicon SPAD module) at 800 nm"),
        "values": T("photon detection efficiency 68 % typical at 800 nm (minimum 62 %); dark counts at most 250 per "
                    "second (grade W3); dead time 20 ns typical (at most 40 ns); timing resolution 350 ps typical at "
                    "825 nm, read as FWHM (σ = 149 ps); afterpulsing 1.0 % typical, not modelled"),
        "basis": "Excelitas Technologies, SPCM-NIR product brief, Rev 2018-09, Table 2",
    },
}


# --- closed forms ------------------------------------------------------------------------------------------------
def observed_rate(rate_in, dead_time: float):
    """m = n / (1 + n t_d): the recorded rate of a non-paralysable detector for a Poisson input of rate n (photons
    detected plus dark counts)."""
    n = np.asarray(rate_in, float)
    return n / (1.0 + n * dead_time)


def detector_rate(photon_rate, det: Detector):
    """The recorded rate of ``det`` for a Poisson stream of photons of rate R reaching it: (eta R + d)/(1 + (eta R +
    d) t_d)."""
    return observed_rate(det.eta * np.asarray(photon_rate, float) + det.dark_rate, det.dead_time)


def true_rate(observed, dead_time: float):
    """n = m / (1 - m t_d): the data sheet's dead-time correction (Correction Factor = 1/(1 - t_d C_R)); refused for
    m t_d >= 1."""
    m = np.asarray(observed, float)
    if np.any(m * dead_time >= 1.0):
        raise ValueError(T("an observed rate of {m:.4g} per second cannot come from a dead time of {td:.4g} s "
                           "(m·t_d ≥ 1)", m=float(np.max(m)), td=float(dead_time)))
    return m / (1.0 - m * dead_time)


def live_fraction(observed, dead_time: float):
    """1 - m t_d: the fraction of time a non-paralysable detector of recorded rate m is live (= the probability that a
    Poisson arrival finds it live)."""
    return 1.0 - np.asarray(observed, float) * dead_time


def accidental_rate(w: float, rate_a, rate_b):
    """w R_A R_B: coincidences of two uncorrelated Poisson streams within |t_B - t_A| <= w/2 (Dehlinger and
    Mitchell's N_acc = tau N_A N_B / T)."""
    return w * np.asarray(rate_a, float) * np.asarray(rate_b, float)


def window_share(w: float, sigma_a: float, sigma_b: float | None = None) -> float:
    """The probability that the two tags of one pair (arriving together) fall within |t_B - t_A| <= w/2 when each
    carries Gaussian jitter: erf(w / (2 sqrt 2 sigma_d)), sigma_d = sqrt(sigma_a^2 + sigma_b^2) (erf(w / (4 sigma))
    for equal jitters); 1 without jitter."""
    sb = sigma_a if sigma_b is None else sigma_b
    sd = math.hypot(sigma_a, sb)
    if sd == 0.0:
        return 1.0 if w > 0 else 0.0
    return math.erf(w / (2.0 * math.sqrt(2.0) * sd))


def dark_click_probability(dark_rate: float, window: float) -> float:
    """1 - exp(-d window): the probability of at least one dark count in a window (a slot, or the part of it the
    station reads)."""
    return -math.expm1(-dark_rate * window)


def click_probability(mean_photons, det: Detector, window: float):
    """1 - exp(-(eta n + d window)): at least one count in a window that a Poisson number of photons of mean n reaches
    (threshold detector, dead time and jitter far below the window)."""
    return -np.expm1(-(det.eta * np.asarray(mean_photons, float) + det.dark_rate * window))


def slot_coupling(dead_time: float, jitter_sigma: float, slot: float) -> float:
    """(t_d + 5 sigma_j) / Ts: the part of a slot that the previous slot's last count can reach (a dead detector at
    the slot's start, a tag jittered across the boundary). The slots are independent trials when it is << 1; the
    error of the independent-slot probabilities is at most of the order of this fraction times the click
    probability."""
    return (dead_time + 5.0 * jitter_sigma) / slot


def coincidence_rates(pair_rate: float, port_probs, dets_a, dets_b, w: float) -> dict:
    """Expected rates of a continuous source of pairs (a Poisson process of rate R) seen by two stations with fixed
    settings; ``port_probs[i][j]`` the probability that a pair's photon at A leaves by port i and its partner at B by
    port j (``lfphys.core.quantum.qubits.joint_probabilities`` of the analysers' projectors), detector i of A behind
    port i (``dets_a[i]``), j of B behind port j. Per detector pair (i, j):
    true coincidences in the window R P_ij eta_i eta_j L_i L_j erf(...) (L = live fraction), accidentals w m_i m_j
    (m the recorded singles), to first order in w m and in m t_d. Returns {"singles_a", "singles_b", "true",
    "accidental"} (arrays: rates per second)."""
    P = np.asarray(port_probs, float)
    ra = np.array([detector_rate(pair_rate * P[i].sum(), d) for i, d in enumerate(dets_a)], float)
    rb = np.array([detector_rate(pair_rate * P[:, j].sum(), d) for j, d in enumerate(dets_b)], float)
    true = np.empty(P.shape)
    for i, da in enumerate(dets_a):
        for j, db in enumerate(dets_b):
            true[i, j] = (pair_rate * P[i, j] * da.eta * db.eta * live_fraction(ra[i], da.dead_time)
                          * live_fraction(rb[j], db.dead_time) * window_share(w, da.jitter_sigma, db.jitter_sigma))
    return {"singles_a": ra, "singles_b": rb, "true": true, "accidental": accidental_rate(w, ra[:, None], rb[None, :])}


# --- the time stream (Monte Carlo) ------------------------------------------------------------------------------
def poisson_times(rate: float, t0: float, t1: float, rng) -> np.ndarray:
    """Sorted times of a Poisson process of ``rate`` on [t0, t1)."""
    n = rng.poisson(rate * (t1 - t0)) if rate > 0 else 0
    return np.sort(rng.uniform(t0, t1, n))


def _nonparalysable(t: np.ndarray, dead_time: float) -> np.ndarray:
    """Indices of the sorted times ``t`` that a non-paralysable detector records: a count is recorded when it comes at
    least t_d after the last recorded one. A count more than t_d after its predecessor (recorded or not) is always
    recorded, so only the runs of close counts are scanned one by one."""
    keep = np.ones(len(t), bool)
    if dead_time <= 0.0 or len(t) < 2:
        return keep
    close = np.flatnonzero(np.diff(t) < dead_time) + 1  # counts within t_d of their predecessor
    last = -math.inf
    prev_close = -2
    for i in close:
        if i != prev_close + 1:  # a new run: its first count (i - 1) follows a gap >= t_d, so it was recorded
            last = t[i - 1]
        if t[i] - last >= dead_time:
            last = t[i]
        else:
            keep[i] = False
        prev_close = i
    return keep


def detect(arrivals, det: Detector, t0: float, t1: float, rng) -> np.ndarray:
    """The recorded time tags of ``det`` on [t0, t1): each photon arrival (times) detected with probability eta, dark
    counts added as a Poisson process, the non-paralysable dead time applied to the merged stream, then each recorded
    count's tag jittered by N(0, sigma). Sorted."""
    a = np.asarray(arrivals, float)
    a = a[(a >= t0) & (a < t1)]
    hits = a[rng.random(len(a)) < det.eta] if det.eta < 1.0 else a
    t = np.sort(np.concatenate([hits, poisson_times(det.dark_rate, t0, t1, rng)]))
    t = t[_nonparalysable(t, det.dead_time)]
    if det.jitter_sigma > 0.0:
        t = np.sort(t + rng.normal(0.0, det.jitter_sigma, len(t)))
    return t


def coincidences(tags_a, tags_b, w: float, delay: float = 0.0) -> int:
    """The number of tag pairs with |t_B - t_A - delay| <= w/2 (every pair counted)."""
    a = np.asarray(tags_a, float)
    b = np.sort(np.asarray(tags_b, float))
    hi = np.searchsorted(b, a + delay + 0.5 * w, side="right")
    lo = np.searchsorted(b, a + delay - 0.5 * w, side="left")
    return int(np.sum(hi - lo))


def slot_clicks(tags, slot: float, n_slots: int, t0: float = 0.0) -> np.ndarray:
    """A boolean per slot k = 0 .. n_slots - 1: at least one tag in [t0 + k Ts, t0 + (k + 1) Ts)."""
    k = np.floor((np.asarray(tags, float) - t0) / slot).astype(np.int64)
    k = k[(k >= 0) & (k < n_slots)]
    out = np.zeros(n_slots, bool)
    out[k] = True
    return out


def pair_slots(n_slots: int, slot: float, pair_rate: float, port_probs, settings_a, settings_b, dets_a, dets_b,
               rng, delay_a: float = 0.0, delay_b: float = 0.0, t0: float = 0.0):
    """A time-stream Monte Carlo of a Bell test with locally defined slots. Pairs are emitted as a Poisson process of
    ``pair_rate`` on [t0, t0 + n_slots Ts); a pair emitted at t reaches A at t + delay_a and B at t + delay_b, where it
    meets the setting of the slot containing its arrival (``settings_a[k]``, ``settings_b[k]``: indices); its ports
    (i at A, j at B) are drawn from ``port_probs[sa][sb]`` (a matrix: the joint Born probabilities of the pair's ports
    for that setting pair, e.g. ``qubits.joint_probabilities`` of (Pi, I - Pi) for a polariser). The photons of port i
    at A reach ``dets_a[i]`` (``detect``); a port without a detector (i >= len(dets_a): a polariser's absorbed light)
    loses its photon. Each station's clock starts its slots at t0 + its delay. Returns ((clicks_a, clicks_b), (tags_a,
    tags_b)): per detector a boolean array over the slots (at least one tag in the slot) and its recorded tags."""
    sa_all = np.asarray(settings_a, np.int64)
    sb_all = np.asarray(settings_b, np.int64)
    t_end = t0 + n_slots * slot
    te = poisson_times(pair_rate, t0, t_end, rng)
    ta, tb = te + delay_a, te + delay_b
    ka = np.clip(np.floor((ta - t0 - delay_a) / slot).astype(np.int64), 0, n_slots - 1)
    kb = np.clip(np.floor((tb - t0 - delay_b) / slot).astype(np.int64), 0, n_slots - 1)
    ports_a = np.empty(len(te), np.int64)
    ports_b = np.empty(len(te), np.int64)
    sa, sb = sa_all[ka], sb_all[kb]
    for x in np.unique(sa):
        for y in np.unique(sb):
            m = (sa == x) & (sb == y)
            if not m.any():
                continue
            P = np.asarray(port_probs[x][y], float)
            nb = P.shape[1]
            k = rng.choice(P.size, size=int(m.sum()), p=P.ravel() / P.sum())
            ports_a[m], ports_b[m] = k // nb, k % nb
    tags_a = [detect(ta[ports_a == i], d, t0 + delay_a, t_end + delay_a, rng) for i, d in enumerate(dets_a)]
    tags_b = [detect(tb[ports_b == j], d, t0 + delay_b, t_end + delay_b, rng) for j, d in enumerate(dets_b)]
    clicks_a = [slot_clicks(t, slot, n_slots, t0 + delay_a) for t in tags_a]
    clicks_b = [slot_clicks(t, slot, n_slots, t0 + delay_b) for t in tags_b]
    return (clicks_a, clicks_b), (tags_a, tags_b)
