from lfphys.theories.alternatives import johannsen_metric as JP
rng = {"alpha13": (-10, 10), "alpha22": (-3, 10), "alpha12": (-3, 10)}
for k, (lo, hi) in rng.items():
    for chi in (0.998, 0.9, 0.5, 0.2, 0.0):
        print(k, chi, [(round(a, 3), round(b, 3)) for a, b in JP.admissible_intervals(chi, k, {}, lo, hi)])
