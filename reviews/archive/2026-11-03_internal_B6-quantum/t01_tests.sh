#!/bin/bash
# The batch's own tests, run read-only in the image (pytest cache off, no bytecode): the scene, the 3-D sampling fix,
# the wrapper. Output: t01_tests.out
R=/home/ildar/hdd/projects/i/light-funnel/engine/reviews/2026-11-03_internal_B6-quantum
E=/home/ildar/hdd/projects/i/light-funnel/engine
docker run --rm --name lf-b6rq-t01 --user 1000:1000 -e HOME=/tmp --cpus 4 -e OMP_NUM_THREADS=4 \
  -v $E:/lf:ro -v $R:/out -e PYTHONDONTWRITEBYTECODE=1 -e LFPHYS_NO_GPU=1 -w /lf/lfphys light-funnel-viz \
  sh -c 'python3 -m pytest -q -p no:cacheprovider --durations=15 tests/test_quantum_scene.py "tests/test_schrodinger_nd.py::test_sample_in_three_dimensions_and_for_a_spinor" tests/test_bohm_nd.py 2>&1; cd /lf/visualizations && python3 -m pytest -q -p no:cacheprovider --durations=10 p02_quantum/tests 2>&1'
