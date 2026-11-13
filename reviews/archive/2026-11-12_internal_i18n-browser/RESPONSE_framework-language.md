# Response (framework-language part) to the review i18n-browser, 2026-11-12

**Responder:** PR-D, the framework-language processing agent (prefix `lf-pd-`). It wrote neither the review nor the
code under review. **Date:** 2026-11-13.

**Scope.** F5, and the language parts of the nits F7, F9 and F13 in the framework's catalogue. F1–F4 and the player's
nits (layout, CSS, number fields) are PR-A's (`RESPONSE_framework.md`). The worlds' nits (F6, F8 in v07, F10, F15, and
the world entries of F7 and F9) are PR-C1's and PR-C2's. The detail of every catalogue change is in
`../2026-11-12_internal_i18n-language/RESPONSE_framework-language.md`.

| Finding | Outcome |
|---|---|
| F5 two Russian names for the playground | fixed (framework); world and engine entries by PR-C2 and PR-B |
| F7 «а. е.» | nothing to do in the framework (already «а. е.»); v01 and v04 by PR-C1 |
| F9 decimal points in Russian prose | nothing to do in the framework; engine and worlds by their agents |
| F13 Russian labels clipped | language part: no shorter Russian (the owner's wording is the full one); the layout fix is PR-A's |

### F5 — should-fix — two Russian names for the playground

**Fixed by the owner's decision of 2026-11-13** (owner: «Лаборатория / Laboratory»). The name is one word per language:
- "Laboratories" / «Лаборатории» for the catalogue's mode button (the section);
- "laboratory" / «лаборатория» everywhere else.

The framework's entries:
- the mode button `Laboratories` «Лаборатории»;
- its tooltip «Лаборатория для исследований: …»;
- the help line under it «Лаборатория для каждого раздела физики: …» (English "A laboratory for each branch of
  physics", which also removes the calque "by section");
- the run-list badges `Laboratory` / `Laboratory · being kept` «Лаборатория» / «Лаборатория · сохраняется»;
- the badge's tooltip;
- two server messages, «… этой лаборатории …» and «… только у лаборатории».

The catalogue has no «Плейграунд», «Песочница», "playground" or "sandbox" left in a user text. The code's identifiers
stay (`kind: "playground"`, `lfviz.playground`, `pNN`).

The glossary entry the review asked for is in `visualizations/RULES.md` §7 («Glossary», 2026-11-13). The user guides
follow it: the root README.md/README.ru.md, `visualizations/README(.ru).md`, and RULES.md §6.

**Outside this part.**
- The four cards («Песочница гравитации» …) and the world titles are in `p0*/locales` (PR-C2).
- The settings page's «(песочница «Электричество и магнетизм», …)» and «(плейграунд «Жидкости»)» are in the engine's
  kernel notes (PR-B).

Until those land, the catalogue page in Russian shows «Лаборатории» on the button and the help line, and the old words
on the cards.

### F7 — nit — «а. е.» (framework part)
The framework already renders `au` as «а. е.». p01's entry for `au` is the same. The «а.е.» spellings are in v01 and v04
(PR-C1). The clipped «а. е.» on p01's 3-D axis is a layout matter in `scene3d.js` (PR-A).

### F9 — nit — decimal points in Russian prose (framework part)
The framework catalogue has no decimal point in Russian prose. The only matches are version numbers and identifiers:
«r185.1», «Licence 1.0», «4.0», «P16.3». The settings page's «2·10^4», «3·10^5» and the other examples come from the
engine's kernel notes and from v01, v06 and v09.

### F13 — nit — labels clipped in Russian (language part)
The badge now reads «МОДИФИЦИРОВАННАЯ ФИЗИКА: …» in full: this is the owner's wording, and the integrator's glossary
forbids «МОДИФ. ФИЗИКА». So the Russian badge is longer than before, and «стандартная физика» has no shorter correct
form.

The fix is the layout. The review proposes that the physics badge keep its width while `#title`/`#scene` shrink first.
That is in `run.html` and the player's CSS (PR-A), and it was passed to the integrator on 2026-11-13. The badges'
full text stays in their tooltips.

## Tests

The browser checks `tests/browser/i18n_checks.mjs` ran in EN and RU against a private server `lf-pd-srv` on port 8673
(Docker, CPU, `--memory=6g`; Playwright 1.58.2 with `--memory=4g`). The shared 8479 was not used. **Result: all passed**
(87 checks in EN and RU, no page errors). The other tests are listed in the language review's response.
