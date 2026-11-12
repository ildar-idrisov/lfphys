# Response (instruments part) to the review LB1-p02-ux

**Responder:** the instruments processing agent (prefix `lf-lpi-`). It did not write the review and did not write the
code under review. **Date:** 2026-11-11/12.

**Scope of this response:** the sweep side of Q3, and X1, X7, X9. The p02 side of Q3 and the other findings are
answered by their processors (`RESPONSE_p02.md`, `RESPONSE_framework.md`, `RESPONSE_p03.md`, `RESPONSE_p04-p01.md`).

**Environment.** Image `light-funnel-viz`, CPU only, in Docker.
- Private server `lf-lpi-srv` (port 8611, `--memory=6g`, 3 workers, `LFVIZ_PLAYGROUND_CKPT=6`, `LFVIZ_EXTRA` with both
  fixture folders). It was stopped by name; `docker ps -a` shows no `lf-lpi-*` container.
- Browser: Playwright 1.58.2 Chromium (swiftshader), `--shm-size=2g --init --network host`.
- p02 was being edited by its processor at the same time. The p02 checks below show the code as it stood on 2026-11-12.

**Evidence** is in `response_checks_instruments/`: our scripts, and their outputs and screenshot in `after/`.

## Summary

| | count | findings |
|---|---|---|
| fixed | 4 | Q3 (the sweep's side), X1, X7, X9 |
| rejected | 0 | |
| deferred | 0 | |

## Findings

### Q3 (the sweep's side) — p02's `measure()` returned a tuple, and every p02 sweep failed — **fixed** [useful]

**Fix.** `visualizations/server/lfviz/sweep.py`: `_read`, `_Contract`, `main`.
- **The contract is checked.** A world's `measure()` must return a dict {id: number}; a frame's `meas` must be a dict.
  Anything else is the world breaking the instruments' contract. The sweep stops at once and says so: «Свип не
  посчитан: мир «…» нарушает договор приборов (API P16.3 §2) — его measure() вернул tuple, а не словарь {id величины:
  число}. Это ошибка мира, а не выбранных значений…». Before, every value failed with «AttributeError».
- **No longer «готово».** A sweep that measured nothing is state `failed`, «не посчитан»: «Не измерено ни одно из N
  значений: <the first reason> — причины по значениям в таблице» (X7).
- **p02's own side** (returning the dict) is the p02 processor's.

**Verification.**
- `tests/test_sweeps.py::test_a_contract_breaking_measure_is_named`. The fixture p97 with `P97_MEASURE=tuple`:
  - state `failed`, no results, the message names the contract and «measure() вернул tuple», and no «AttributeError»;
  - negative control: with a `measure()` that returns a dict, the sweep is done and reads through `measure`.
- `after/rc_q3_p02_sweep.out`: a sweep of p02's window 76 / 80 / 84 nm in the double slit, measured now: «Готово:
  измерено 3 из 3 значений», sampler `measure`. p02 returns its dict at the time of this check.

### X1 — sweeps over an object's parameter were refused in every playground — **fixed** [useful]

**Fix.** `visualizations/server/lfviz/instruments.py` (`WorldInfo.palette`, from the world's header) and `sweep.py`
(`object_param`, `_param_of`).
- **The cause.** The server checked an object's parameter against the class's `PALETTE`, which is empty: p01–p04 build
  their palettes per world instance.
- **Now** it checks against the palette the world's header gave (`playground.palette`): the parameter is rebuilt from
  its JSON, and the parameter's own range applies. The class's palette remains the fallback.
- The result also says whether the parameter is one of the type's handles. That decides how a sweep applies it:
  `edit` or `set` (LB1-framework F1).

**Verification.**
- `tests/test_sweeps.py::test_object_parameters_of_a_real_playground_are_validated_from_its_header`. On p04
  «cylinder_re20», whose class has no palette:
  - the «Цилиндр» radius is accepted, and its own range still refuses −1;
  - the disk's `x` is reported as a handle;
  - negative control: without the header's palette (the old way) the same request is refused «есть: нет».
- `after/rc_b5b_sweep_api.out` (the review's b5 on our server, the object sweeps also run). Before, both object
  parameters were refused «нет параметра … есть: нет» (`../b5_sweep_api.out`); now:
  - p03 «Аргон» T 100 / 200 K — done;
  - p04 «Цилиндр» radius 0.04 / 0.05 m — done, Mach 0.01824 / 0.01824;
  - p04's law ν — done.

### X7 — the sweep form for a femtosecond world — **fixed** [useful]

**Fix.** `visualizations/player/js/instruments.js` (`defaultDuration`, `tScale`, the form, `submit`) and `sweep.py`
(the state when nothing was measured).
- **The duration and the window** are given in the unit of the world's scale: seconds with an SI prefix down to
  attoseconds («Сколько считать, фс»), converted to the world's time when sent. Another world unit («M») is kept as it
  is.
- **The default duration** is five wall seconds of the world at its chosen speed; else a tenth of what the record
  covers; else one unit. The window's default is half of it.
- **After a start** the estimate's text becomes «Сначала «Оценить»…» and «▶ Запустить свип» is disabled until the next
  estimate.
- **A sweep that measured nothing** is «не посчитан», with the first reason.

**Verification.**
- `after/rc_x7x9_p02_form.out` and `after/p02_sweep_form.png` (looked at), p02's double slit: «Сколько считать, фс»
  with the default 109.982 fs (the speed 2.2·10⁻¹⁴ s/s × 5 s). Before: «1» in seconds, «≈ 2818381528 ч».
- `tests/browser/instruments_checks.mjs`, all passing:
  - «X7 the duration's default follows the world's speed»: p97, 5 s;
  - «X7 a slow world's duration in ms, sent in s»: at speed 0.02, «Сколько считать, мс» = 100, and the request carries
    0.1 s;
  - «X7 after a start the estimate is asked anew»;
  - «X7 nothing measured is «не посчитан»».
- `tests/test_sweeps.py::test_nothing_measured_is_not_done`.

### X9 — «Что менять» doubled units and listed the hidden law — **fixed** [useful]

**Fix.** `visualizations/player/js/instruments.js` (`withUnit`, `hasUnit`, `targets`) and `sweep.py` (`with_unit`, the
same rule for the table's header and CSV).
- **The unit is added only when the label does not name it already:** not after a comma, not in brackets, and not as a
  word of its own («Число щелей»).
- **Hidden laws.** Laws whose `show_if` does not hold for the world's parameters and live values are not offered (n3
  in the plane).
- **Hidden object parameters.** An object's parameter whose `show_if` does not hold for the object's values is not
  offered either.
- **«Что измерять»** uses the same rule.

**Verification.**
- `after/rc_x7x9_p02_form.out`, p02's double slit:
  - no option names a unit twice («Закон: Размер окна, нм», «Высота, эВ»);
  - `law:n3` is not offered, and the schema's `show_if` of n3 is `{"dim": ["3d"]}`.
- `tests/browser/instruments_checks.mjs` «X9 units once, the hidden law not offered», on the fixture p97:
  - its law «Занять память, МБ» with the unit «МБ» is offered once named;
  - its live law `damp`, hidden by `show_if`, is not offered;
  - preconditions checked in the schema, so the check could fail.
- Negative control: the same check fails on the original panel (`../2026-11-11_internal_LB1-framework/
  response_checks_instruments/before/instruments_checks_old_js.out`).

## Changes for the integrator

The texts for RULES §3 and §6, STATUS and the owner guide that these four fixes need are in the framework review's
response: `../2026-11-11_internal_LB1-framework/RESPONSE_instruments.md`, section «Changes for the integrator», items
1–7. They are given once there, to keep one place.

What these findings add to those texts:
- **RULES §6 «Instruments»:** the `measure()` contract and its refusal (Q3); the state `failed` «не посчитан» when
  nothing was measured (X7).
- **RULES §3, the sweep row:** an object's parameter is checked against the palette of the world's header (X1).
- **Owner guide:** the duration in the unit of the world's scale, its default, and the estimate asked anew after a
  start (X7).
