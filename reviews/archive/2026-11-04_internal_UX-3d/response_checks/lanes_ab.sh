#!/bin/sh
# The processing's evidence, as run (Playwright image, next to node_modules, /orig = the files before the processing):
# lane 1 = tours, lane 2 = probes (run in parallel), then perf alone (sh lanes_ab.sh perf). Each world/case: orig, then new.
PORT=${PORT:-8571}
if [ "$1" = "tours" ]; then
for j in \
  "v08_wave_3d double v08_double 8000" "v11_double_slit_2d narrow v11_narrow 12000" "v12_arrival_times_2d gauss v12_gauss 10000" \
  "p02_quantum double_slit p02_dslit 8000" "p04_fluids cylinder_re20 p04_cyl 6000" "p01_gravity sun_earth p01_sun_earth 8000" \
  "v10_fast_observer terrell v10_terrell 8000" "v15_kerr_shadow m87 v15_m87 8000" "v17_mie_scattering rainbow v17_rainbow 8000" \
  "p03_molecules maxwell p03_maxwell 5000" "v09_thomas_3d lab v09_lab 12000"
do set -- $j; for v in orig new; do node /pw/tour_ab.mjs $PORT $v $1 $2 $3 $4 - /out/final; done; done
elif [ "$1" = "probes" ]; then
for c in volsphere planevol twoplanes boxjump zfight faint flat layerspanel; do
  for v in orig new; do node /pw/probe_ab.mjs $PORT $c $v /out/final; done
done
elif [ "$1" = "looks" ]; then
for j in "v13_hydrogen_3d 1s v13_1s 4000" "v13_hydrogen_3d 3d_m2 v13_3dm2 4000" "v14_quarkonium_3d cc_1S v14_cc1S 4000"   "v09_thomas_3d thomas v09_thomas 6000" "v11_double_slit_2d narrow v11_narrow 12000" "v16_optical_vortices lg3 v16_lg3 8000"   "v17_mie_scattering near v17_near 8000" "p02_quantum ball_3d p02_ball3d 8000" "v08_wave_3d double v08_double 8000"
do set -- $j; for v in orig new; do node /pw/look_ab.mjs $PORT $v $1 $2 $3 $4 /out/lookF; done; done
elif [ "$1" = "perf" ]; then
for rep in 1 2; do
for j in "v13_hydrogen_3d 1s v13_1s 4000 -" "v13_hydrogen_3d super_1s2p v13_super 6000 play" "v17_mie_scattering near v17_near 8000 -" "p03_molecules liquid_vapour p03_lv 6000 -" "v11_double_slit_2d narrow v11_narrow 12000 -" "v16_optical_vortices lg3 v16_lg3 8000 -"; do
  set -- $j; for v in orig new; do node /pw/perf_ab.mjs $PORT $v $1 $2 ${3}_r$rep $4 $5 /out/final; done
done; done
fi
