#!/bin/sh
# The tours of the review as run: two lanes in parallel (the first one by hand), against the private server on 8561.
# Each job: viz preset tag playMs. Run inside the Playwright image next to node_modules (see README.md).
# Re-run after a first attempt lost a worker race or the test browser crashed: v09_thomas, v11_narrow, v14_cc1P.
set -e
for j in \
  "v08_wave_3d double v08_double 10000" \
  "v08_wave_3d double_slices v08_slices 10000" \
  "v09_thomas_3d thomas v09_thomas 10000" \
  "v09_thomas_3d lab v09_lab 15000" \
  "v10_fast_observer terrell v10_terrell 10000" \
  "v10_fast_observer city v10_city 10000" \
  "v11_double_slit_2d narrow v11_narrow 15000" \
  "v11_double_slit_2d observer v11_observer 15000" \
  "v12_arrival_times_2d gauss v12_gauss 12000" \
  "v12_arrival_times_2d slits v12_slits 15000" \
  "v13_hydrogen_3d 1s v13_1s 8000" \
  "v13_hydrogen_3d 3d_m2 v13_3dm2 8000" \
  "p01_gravity sun_earth p01_sun_earth 10000" \
  "p01_gravity pythagorean p01_pyth 20000" \
  "p01_gravity kerr_orbits p01_kerr 10000" \
  "p02_quantum double_slit p02_dslit 10000" \
  "p02_quantum ball_3d p02_ball3d 10000" \
  "p03_molecules maxwell p03_maxwell 10000" \
  "p03_molecules liquid_vapour p03_lv 10000" \
  "p04_fluids cylinder_re20 p04_cyl 10000" \
  "p04_fluids karman p04_karman 10000" \
  "v15_kerr_shadow m87 v15_m87 10000" \
  "v15_kerr_shadow edge_on v15_edge 10000" \
  "v16_optical_vortices lg3 v16_lg3 10000" \
  "v16_optical_vortices fork v16_fork 10000" \
  "v17_mie_scattering rainbow v17_rainbow 10000" \
  "v17_mie_scattering near v17_near 10000" \
  "v13_hydrogen_3d super_1s2p v13_super 10000"
do
  set -- $j
  node /pw/tour.mjs 8561 $1 $2 $3 $4 - /pw/out
done
