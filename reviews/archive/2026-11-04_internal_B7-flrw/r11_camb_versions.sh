#!/bin/sh
# r11: the constants and the sound-horizon call of the CAMB versions around Planck 2018, read from the public GitHub
# tags (raw files, read only; no contact parameter or personal identifier is sent). Planck 2018 VI (arXiv:1807.06209v1,
# July 2018) predates CAMB 1.4.0 (tag 1.3.6 is dated 2022-08-31).
# Run: sh r11_camb_versions.sh > r11_camb_versions.out
UA="Mozilla/5.0"
for t in Aug2017 1.0.1 1.3.6 1.4.0 master; do
  case $t in Aug2017) c=constants.f90; m=modules.f90;; *) c=fortran/constants.f90; m=fortran/results.f90;; esac
  echo "== CAMB $t: $c"
  curl -sL -A "$UA" "https://raw.githubusercontent.com/cmbant/CAMB/$t/$c" | grep -E "parameter :: (Gyr|Mpc|G|k_B|h_P|default_nnu|neutrino_mass_fac)\b|Gyr *=|Mpc *=" | sed 's/^ */   /'
  echo "== CAMB $t: $m (derived r_* / sound horizon)"
  curl -sL -A "$UA" "https://raw.githubusercontent.com/cmbant/CAMB/$t/$m" | grep -E "rombint\(dsound_da_exact|Integrate_Romberg\(this, ?dsound_da_exact" | sed 's/^ */   /'
done
echo "== CosmoMC master: source/Calculator_Cosmology.f90"
curl -sL -A "$UA" https://raw.githubusercontent.com/cmbant/CosmoMC/master/source/Calculator_Cosmology.f90 | grep -E "neutrino_mass_fac=|standard_neutrino_neff =" | sed 's/^ */   /'
echo "== CosmoMC master: source/Calculator_CAMB.f90 (neutrino set-up)"
curl -sL -A "$UA" https://raw.githubusercontent.com/cmbant/CosmoMC/master/source/Calculator_CAMB.f90 | grep -E "share_delta_neff|SetNeutrinoHierarchy\(CMB" | sed 's/^ */   /'
echo "== CAMB Aug2017 camb.f90: degenerate hierarchy split"
curl -sL -A "$UA" https://raw.githubusercontent.com/cmbant/CAMB/Aug2017/camb.f90 | grep -E "neff_massive_standard *=|Num_Nu_Massless *= *nnu|Nu_mass_degeneracies\(P%Nu_mass_eigenstates\) *=" | sed 's/^ */   /'
