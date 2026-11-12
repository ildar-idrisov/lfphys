# Review of the licensing fixes (commit 9462d8b): the lfphys Research Licence 1.0, CLA, PUBLICATIONS

Date: 2026-10-29. Type: internal. Author: Claude (Opus), an independent reviewer subagent that took no part in the
earlier review, its processing or the drafting of the new texts. Status: **awaiting processing**. The reviewer has not
edited any file outside this folder and does not process this review.

Scope: whether `RESPONSE.md` of `reviews/archive/2026-10-29_internal_licensing/` (findings R1–R10, addendum points
1–4) is implemented as claimed; the new licence text against the owner's goal (REVIEW.md line 7 of that review: allow
academic research; commercial use only by separate permission; limit liability as far as possible; attribution and
citation in publications); the CLA; consistency of all licence-related files; what was dropped. Read in full:
`LICENSE.md`, `PUBLICATIONS.md`, `COMMERCIAL.md`, `CONTRIBUTING.md`, `CLA.md`, the three `NOTICE` and `CITATION.cff`
files, `README.md`, the licence sections of `lfphys/README.md` and `visualizations/README.md`,
`lfphys/sources/dependencies.md` §1–§8, `visualizations/player/legal.html`, `player/js/legal.js`, the `/legal` route
in `visualizations/server/lfviz/app.py` and its test, `STATUS.md` V20–V21, `AGENTS.md` §1 and §3 rule 8,
`git show 9462d8b`. Line numbers refer to commit 9462d8b (the licence files are unchanged in the working tree; the
only later commit, `ecec6de`, touches the research tree's root `AGENTS.md`).

Limits. This is a reviewer's reading, not legal advice. Points marked **⚖** need a lawyer of the Republic of Cyprus
(STATUS V20 already plans that check; the marks say what to put in front of the lawyer). Statutes are quoted from the
official sources listed at the end, downloaded today; translations from Greek are the reviewer's own and unofficial.
The test suites were not run (no Docker for this review); the route and its test were read. Mechanical checks are in
`checks.sh` with their output in `checks.out` (read-only; run from `engine/`).

Tags per item (as in the earlier review): [useful], [neutral], [weakens], [error in earlier].

## Кратко (по-русски)

Переход на собственную лицензию сделан всерьёз: всё, что заявлено в RESPONSE.md, в файлах есть, копии в `lfphys/`
и `visualizations/` побайтно совпадают, PolyForm не осталось (кроме строк истории), у каждого исходника SPDX-строка,
страница `/legal` отдаёт тексты из фиксированного списка. Но в текстах есть одна ошибка, 18 мест, которые стоит
поправить до показа юристу, и 9 мелочей. **Ошибка:** в CLA «Licensor» — это любой, кому владелец «licenses his rights», то
есть каждый пользователь исследовательской лицензии и каждый коммерческий лицензиат; формально все они получают от
участников право перелицензировать вклады на любых условиях (L21). **Главное к исправлению:** (1) разрешение на
скриншоты плеера дано «под CC BY-NC-SA», а плеер — это код под LICENSE.md (L14); (2) формулировка о заказных
исследованиях одновременно оставляет лазейку (оплаченный бизнесом расчёт без прав на результат) и задевает обычную
академическую работу (консорциумы с промышленными партнёрами, окно согласования публикации, код в приложении к
платному журналу) (L1, L2); (3) «Noncommercial Research» ограничено перечнем типов организаций — некоммерческие
общества, музеи, научные центры остаются вне лицензии (L3); (4) хостинг по сети: неясно, коммерческий ли бесплатный,
и пользователи сервиса не получают ни условий, ни требования цитировать (L4); (5) нет условия о принятии лицензии,
а суд Кипра по умолчанию исключительный — это вопросы к юристу, как и цепочка прав самого владельца (работодатель,
заказчик, код, написанный ИИ-сессиями) (L9–L11). Тексты сделаны добросовестно; ни одно из замечаний не требует
возвращаться к PolyForm.

## Summary of findings

| id | severity | tag | location | one line |
|---|---|---|---|---|
| L1 | should-fix | [weakens] | LICENSE.md:27–29, 33–38 | the sponsored-research test leaves paid contract research without rights in results open, by an a-contrario reading |
| L2 | should-fix | [weakens] | LICENSE.md:27–29, 32–38, 57 | ordinary academic work caught: consortia with industry, publication-review windows, supplementary code in paywalled journals, cost recovery |
| L3 | should-fix | [weakens] | LICENSE.md:19–21 | Noncommercial Research limited to five kinds of user; non-profits, societies, museums fall outside any licence |
| L4 | should-fix | [weakens] | LICENSE.md:30–31, 55–61; COMMERCIAL.md:10–11 | network use: free hosting ambiguous; hosts need not pass the licence, disclaimer or citation duty to users |
| L5 | should-fix | [neutral] | LICENSE.md:44–45, 58 | modifications by others: nobody licenses them to recipients; the Licensor gets no rights in them |
| L6 | should-fix | [weakens] | LICENSE.md:76–77; PUBLICATIONS.md:45–48 | "or selling them" (results) is circular and contradicts §6's first sentence |
| L7 | should-fix | [weakens] | LICENSE.md:65–70; summaries | "substantially" undefined and dropped by four summaries; which version to cite is unclear |
| L8 | should-fix | [weakens] | LICENSE.md:109–112 | the 30-day cure can be read to reinstate a commercial infringer with no claim for the past |
| L9 | should-fix ⚖ | [weakens] | LICENSE.md:121–123 | Cyprus courts become exclusive by default; formation "in writing"; infringement law cannot be chosen |
| L10 | should-fix ⚖ | [weakens] | LICENSE.md (no clause); §2 | no acceptance clause (PolyForm had one); contract vs bare permission; Cyprus research exception |
| L11 | should-fix ⚖ | [weakens] | LICENSE.md:5–6; STATUS V20 | the owner's own chain of title (employer, commissioning client, AI-produced code) is not recorded — addendum point 1 |
| L12 | nit ⚖ | [neutral] | LICENSE.md:86–98 | EU Product Liability Directive 2024/2853; no "no endorsement / no validation" clause |
| L13 | should-fix | [weakens] | lfphys/README.md:174–177 (also :8, :133) | an affirmative accuracy statement inside the "No warranty" bullet |
| L14 | should-fix | [weakens] | PUBLICATIONS.md:28–41, :8–12; LICENSE.md:74–77 | the screenshot permission is granted under CC, but the player is code under LICENSE.md |
| L15 | should-fix | [weakens] | PUBLICATIONS.md:31–38 | the publication permission does not fit open-access (CC BY) journals or the publisher's needs |
| L16 | nit | [neutral] | PUBLICATIONS.md:34 | short code excerpts in papers not covered |
| L17 | should-fix | [weakens] | CONTRIBUTING.md:41–48 | "every source file starts with" the owner's copyright line, also in a contributor's own file (R6 partly) |
| L18 | nit | [neutral] / [error in earlier] | COMMERCIAL.md:10, PUBLICATIONS.md:46, RESPONSE.md | summaries drift from the licence; two small inaccuracies in RESPONSE.md |
| L19 | nit | [neutral] | dependencies.md:312–313; STATUS.md:32 | §8 item 6 and V21 keep wording that R7 corrected elsewhere |
| L20 | nit | [neutral] | CITATION.cff; lfphys/pyproject.toml | `license-url`, a REUSE-style licence file, `Private :: Do Not Upload` |
| L21 | **error** | [weakens] | CLA.md:13–14 (also LICENSE.md:5–6) | the CLA's "Licensor" includes every licensee of the owner |
| L22 | should-fix ⚖ | [weakens] | CLA.md (preamble, §2, §5) | consideration and irrevocability of the CLA under Cap. 149 §25 |
| L23 | should-fix | [weakens] | CLA.md:37–39, 58–63 | employer/client consent: evidence stays with the contributor; the organisational agreement does not exist |
| L24 | nit | [neutral] | CLA.md:18–21, 35–43 | acts in the grant (making available, rental), moral rights, enforcement, AI-generated material |
| L25 | nit | [neutral] | CLA.md:55–63; CONTRIBUTING.md:46–47 | record keeping, GDPR notice, e-mail in SPDX lines |
| L26 | should-fix | [weakens] | STATUS V20; COMMERCIAL.md | the commercial-agreement template lacks two Cyprus-specific requirements (transfer to a company; commissioned-work default) — addendum point 4 |
| L27 | nit | [neutral] | LICENSE.md:111–112, 117–118 | survival list; "unless the Licensor offers it under another" |
| L28 | nit | [neutral] | LICENSE.md:25–26 | businesses cannot evaluate before asking for a commercial licence (owner's decision) |

Totals: 1 error, 18 should-fix (4 of them, L9–L11 and L22, need a lawyer), 9 nits (L12 also for the lawyer).

## Part A. Is each fix in place as RESPONSE.md claims?

| id | claimed | found | remarks |
|---|---|---|---|
| R1 | own licence; Commercial Use by purpose, any user, any funding; sponsored research included; salary, grants, publishing, teaching excluded | **yes** [useful]: LICENSE.md:22–38 | the drafting has holes in both directions: L1, L2, L3 |
| R2 | citation a condition (§5); CFF says required; no invented URL/DOI | **yes** [useful]: LICENSE.md:65–70, CITATION.cff:2 ×3 | "substantially" and the version: L7; CFF `license-url`: L20 |
| R3 | COMMERCIAL.md as procedure; code and docs separate; "separate written agreement signed by the Licensor" | **yes** [useful]: COMMERCIAL.md:3–31 | the network example lacks the fee qualifier: L4; summary drift: L18 |
| R4 | §8 disclaimer, no zero cap, savings clause; READMEs; player line and `/legal` | **yes** [useful]: LICENSE.md:86–98, README.md:28–35, index.html:27–29, legal.html:26–31 | lfphys/README keeps affirmative accuracy wording: L13; PLD: L12 |
| R5 | scope table; §6 no ownership; PUBLICATIONS additional permission | **yes, but** [weakens]: README.md:42–47, LICENSE.md:74–77, PUBLICATIONS.md:28–41 | the screenshot permission sits under the wrong licence (L14), does not fit OA journals (L15); "selling them" (L6) |
| R6 | CLA (copyright, patent, assurances, successors, consent record); notice rule fixed | **yes, partly** [weakens]: CLA.md, CONTRIBUTING.md:7–18, 41–49 | Licensor definition (L21, error); consideration (L22); consent evidence (L23); notice rule still says every file starts with the owner's line (L17) |
| R7 | §3.3, §3.4, §3.5, §4, §8 item 9; CONTRIBUTING; AGENTS rule 8 | **yes** [useful]: dependencies.md:184–190, 209–213, 217–221, 225–241, 319–323; CONTRIBUTING.md:22–34; AGENTS.md:109–115 | §8 item 6 and STATUS V21 keep the old scope/wording: L19 |
| R8 | `/legal` with six texts from a fixed list, linked from three pages | **yes** [useful]: app.py:47–50, 302–309, 320–321; legal.html; legal.js:10–17; index.html, run.html, settings.html; test_server.py `_legal` | lookup is a dict, so no path traversal; the page does not show the version to cite (L7) |
| R9 | distribution free of charge only; fees for software or access are Commercial Use | **yes** [useful]: LICENSE.md:32, 57 | §4 item 1 also bans at-cost and supplementary-material cases: L2 |
| R10 | name, SPDX LicenseRef in every source file, consistent files, PolyForm gone, source-available | **yes** [useful]: checks.out §1–§3 (copies identical; every py/js/mjs/html/css file has the SPDX line, also the untracked new modules) | RESPONSE's grep summary and file description are slightly off: L18 |
| A1 | Licensor an individual, no company named | **yes**, but the addendum's warning about employers', clients' and contributors' rights is not answered for the owner himself [weakens] | L11 |
| A2 | limited scope, no accuracy promise, user verification; commercial terms separate | **yes** [useful]: LICENSE.md:79–98, COMMERCIAL.md:25–28 | — |
| A3 | Cyprus law and courts as a proposal, consumer carve-out, "as far as the law allows" | **yes** [useful]: LICENSE.md:121–123, CLA.md:51 | the court clause becomes exclusive by default and needs agreement in writing; the licence has no acceptance clause: L9, L10 |
| A4 | CLA licences to the owner and later assignees/licensees; licence names successors in title | **yes, too broadly** [weakens]: CLA.md:13–14 | L21 (error); the commercial-agreement side of the addendum's point 4 is not recorded: L26 |

Nothing that RESPONSE.md claims is missing from the files. The defects are in how the new texts are worded.

## Part B. The licence text (`LICENSE.md`)

### L1 — should-fix [weakens]. Paid contract research without rights in the results can be read as allowed

Location: LICENSE.md:22–29 (item 4 and 4.2), 33–38 (item 5).

Item 4.2 makes research "under a contract with, with sponsorship from, or for the benefit of a business" Commercial
Use only "where that business obtains rights in, exclusive or early access to, or confidential use of the results".
A university that is paid by a company to run lfphys and publish the result at once, with no rights or early access
for the company, falls outside 4.2. It may still fall under the general test ("directed towards … monetary
compensation", line 23) or 4.1 ("use … for a business … consulting and services"). But because 4.2 deals with the
case specifically and adds a qualifier, a reader can argue that the drafter meant paid research to be commercial
**only** with that qualifier (an a-contrario reading). Item 5 adds "by themselves", and nothing says which item wins
when items 4 and 5 both apply. In a standard-form text the Licensor wrote, ambiguity is likely to be resolved
against him. "For the benefit of a business" is too vague to help: all applied research benefits some business.

Proposed fix (owner's decision on the exact line):

> 2. research, computation or development that a business pays for or provides other consideration for, or that is
> carried out at the request or under the direction of a business, whatever rights the business obtains in the
> results; and research sponsored by a business in which the business obtains rights in, an option on, exclusive
> access to, or access before publication to the results (other than a review period of up to 60 days to identify its
> confidential information or patentable inventions, see item 5);

and add to item 5: "Item 5 applies only where none of items 4.1–4.4 applies." Drop "for the benefit of".

### L2 — should-fix [weakens]. Ordinary academic work that the text catches by mistake

Location: LICENSE.md:27–29, 32, 33–38, 57.

The response says ordinary academic work is protected (R1). Four common cases are not:

1. **Publicly funded consortia with industrial partners.** In EU and national programmes, industrial partners usually
   get access rights to the results under the grant agreement. Item 5 says public grants are not commercial "whose
   results are … made publicly available without being reserved for a business". But item 4.2 makes research "with
   sponsorship from … a business, where that business obtains rights in … the results" commercial, and a partner's
   in-kind contribution is arguably sponsorship. A university in such a consortium cannot tell whether it is
   licensed.
2. **Review periods before publication.** Almost every university–industry agreement gives the sponsor 30–60 days to
   review a manuscript. That is "early access to … the results" under 4.2 if the sponsor is a business. If this is
   intended, say so. If not, carve out a review period (the wording in L1 does).
3. **Supplementary material in paywalled journals.** A researcher who publishes modified lfphys scripts as
   supplementary material of a subscription journal makes the publisher distribute the Software, or access to it,
   "for a fee" (4.4; §4 item 1). Item 5 covers "publishing results", not software. The publisher becomes a commercial
   user in breach, and a careful journal or author will avoid the material, which defeats reproducibility.
4. **Cost recovery and fee-charging teaching.** §4 item 1 forbids any charge "for a service based on it". This catches
   an institution's at-cost charges for computing time, and a fee-charging summer school that hands out a copy.
   Item 5 exempts tuition but only from the definition of Commercial Use, not from §4. A for-profit educational
   institution is both "a business" (4.1) and "an educational institution … that charges tuition" (item 5), and the
   text does not say which applies.

Proposed fix: add to item 5 (each line is the owner's choice; the defaults below protect ordinary academic work
without opening commercial use):

> — participation of a research organisation in a publicly funded collaborative project, even where business partners
> in the project receive the access rights to results that the programme's rules give them (the business partners'
> own use remains Commercial Use);
> — a review period of up to 60 days before publication in which a sponsor may identify its confidential information
> or patentable inventions;
> — including the Software, or parts of it, in the supplementary material of a scholarly publication or in a public
> data or software repository, even where the publisher charges for access to the publication, if the Software is not
> offered separately for a fee;
> — charges at cost made inside or between noncommercial institutions for computing time, and fees of courses at an
> educational institution, where the Software itself is not sold.

and state for for-profit schools either "an educational institution that is a business is a business for item 4" or
the opposite.

### L3 — should-fix [weakens]. Noncommercial users outside the five listed kinds get no licence at all

Location: LICENSE.md:19–21.

"Noncommercial Research" requires the work to be carried out "by an individual or by an educational institution, a
public research organisation, a charitable organisation or a government body". A non-profit association that is not
a registered charity, a learned society, a museum, a library, a science centre, a planetarium or a non-profit
hospital is not on the list. Its noncommercial use is neither Noncommercial Research nor Commercial Use, so it is
**unlicensed**. COMMERCIAL.md has no procedure for that middle category. PolyForm, which this replaced, also listed
organisations, but more of them ("public safety or health organization, environmental protection organization"; old
LICENSE.md:41), and it covered personal research and amateur use separately. The new list is narrower, and nothing in
the response says that was intended. The owner's goal ("allow academic research") is defined by purpose, and the
Commercial Use definition already applies "whatever the user's legal status", so the list adds risk without adding
protection.

Proposed fix:

> 3. **Noncommercial Research** means research, study, teaching, learning, outreach and personal experimentation
> that is not Commercial Use, whoever carries it out, including individuals, educational institutions, public research
> organisations, non-profit and charitable organisations, learned societies, museums, libraries, science centres and
> government bodies.

(A business's own use stays commercial under 4.1. Decide whether "outreach" should include ad-funded popular-science
channels; under 4.3 "in support of a commercial activity" they are commercial now.)

### L4 — should-fix [weakens]. Network use: free hosting is ambiguous, and users of a hosted copy get no terms

Location: LICENSE.md:30–31 (4.3), 55–61 (§4); COMMERCIAL.md:10–11.

(a) Item 4.3 reads "including the Software … in a product or a service, or using it to provide a service, to anyone
for a fee or in support of a commercial activity, including making it available over a network". It is unclear
whether "making it available over a network" is a standalone case or an example that still needs the fee or the
commercial activity. COMMERCIAL.md:10–11 lists "offering the software over a network" as commercial with **no**
qualifier. So a university that hosts the player free of charge for its students is told by COMMERCIAL.md that it
needs an agreement, and by the licence probably not.

(b) Network users of a hosted copy are not distributees, so §4 (licence text, NOTICE, notices) does not reach them.
They also never accept §5, so their publications need not cite lfphys. Today the player shows `/legal` (R8). A host
running a modified copy may remove the page, and nothing in the licence stops it. This is the usual SaaS gap, and it
defeats the citation goal for exactly the users the player is built for.

Proposed fix: in 4.3, "including the Software or any part of it in a product or service that is offered for a fee
or in support of a commercial activity, or using it to provide such a service, including by making it available to
users over a network". Add §4 item 5 (or a new §4A):

> If You let others use the Software, modified or not, over a network, You must give them, through the interface, the
> text of this licence, the file `NOTICE`, the statement of section 8 and the requirement of section 5 (the page
> `/legal` of the original player does this), and You must not remove or hide that page. Users of such a service who
> publish results obtained with it must cite the Software as section 5 requires.

(The last sentence binds hosts' users only if they accept the terms; the interface notice is what makes that
plausible. ⚖ part of L10.) Align COMMERCIAL.md:10–11 with the new 4.3.

### L5 — should-fix [neutral]. Modifications made by others: who licenses them, and to whom

Location: LICENSE.md:44–45 ("every recipient of a copy receives its licence directly from the Licensor"), 58 ("under
this licence only").

A modified copy contains the modifier's own copyright material. The Licensor cannot license it, so the sentence on
line 45 is wrong for those parts. §4 item 2 requires distribution "under this licence only", but this licence names
Ildar Idrisov as the only licensor, so it is not clear what licence the modifier grants recipients for their changes.
The Licensor also receives no right to fold a published improvement back into the dual-licensed product without a
CLA. (Contributors who sign the CLA are covered; others who only publish forks are not.)

Proposed fix:

> §2, last sentence: "You may not sublicense. Every recipient of a copy receives its licence for the Licensor's
> material directly from the Licensor under this licence."
> §4, new item: "You license Your own modifications to every recipient on the terms of this licence, with You in the
> place of the Licensor for them."

Owner's decision (state it either way): whether to add a grant-back ("… and You grant the Licensor a perpetual,
worldwide, royalty-free licence to use, modify and relicense Your distributed modifications under any terms"). It
helps dual licensing, but some institutions refuse grant-back clauses, and it reads as one-sided. The neutral default
is no grant-back, with improvements coming in through the CLA.

### L6 — should-fix [weakens]. "Producing results for a business, or selling them, is Commercial Use when it falls under item 4"

Location: LICENSE.md:76–77; PUBLICATIONS.md:45–48.

The sentence is circular: selling results is commercial "when it falls under item 4", but item 4 defines uses of the
**Software**, and selling a dataset is not one unless it falls under 4.2. A reader can conclude that selling results
of noncommercial research is allowed. §6's first sentence ("claims no ownership … no rights in Your publications")
points the same way. The earlier review (R5) warned that controlling later commercial use of outputs is "a separate
contractual task, not automatically solved by the code licence", and that it binds only the licensee. Decide
explicitly:

* if selling results is acceptable, write: "Results You obtain in Noncommercial Research are Yours, including to
  license or sell; carrying out research or computation for a business is Commercial Use under item 4.2." and delete
  "or selling them";
* if it is not, write a plain covenant: "You may not sell, or license for a fee, data sets or other results that
  consist substantially of output of the Software without a commercial agreement; this does not restrict publication
  under section 6 or anyone who obtains the results from a publication."

### L7 — should-fix [weakens]. The citation condition: "substantially", its summaries, and which version

Location: LICENSE.md:65–70; README.md:46; visualizations/README.md:170; visualizations/player/legal.html:38–40;
index.html:27–29 (checks.out §4); CITATION.cff:13; lfviz `__version__` "1.0"; each world's "версия 1.0" in the catalogue.

* "Obtained substantially with the Software" is undefined. A user can argue that one cross-check run was not
  substantial, while a careful user may read it as covering a single plotted line. The four user-facing summaries
  (README table, Russian README, `/legal`, catalogue footer) drop the word and say the duty is broader than the
  licence does. Define it and keep one wording everywhere:

  > "obtained substantially with the Software" means that the Software computed, simulated or rendered a result,
  > figure, table or data set that the publication reports, or was used to check one.

* "Any other publication" (line 66) covers posts and slides. That is probably intended, but say that for informal
  media "lfphys (Ildar Idrisov)" with the version or address is enough.
* **Which version.** CITATION.cff and `lfphys.__version__` say 0.1.0. The player shows the server version 1.0 and a
  "версия 1.0" per world, and `/legal` asks for "версия" without saying which. A player user will cite "lfphys 1.0".
  State in §5/PUBLICATIONS §2 "the version in `CITATION.cff` and, for an unreleased copy, the commit identifier or
  date", and show that string on `/legal` (the server knows it).
* Breach and cure: say that a correction (erratum, updated preprint, corrected repository record) within the cure
  period of §10 remedies a missing citation. Otherwise "remedy it" has no meaning for a printed paper.

### L8 — should-fix [weakens]. The cure can reinstate a commercial infringer with no claim for the past

Location: LICENSE.md:109–112.

"If it is Your first breach and You stop it and remedy it within 30 days … Your rights are reinstated." A company
that uses lfphys commercially for a year, receives a notice and stops can argue that its rights are reinstated
retroactively and the matter is closed. Neither "remedy" nor reinstatement mentions past use. (CC 4.0 §6(b), in
`LICENSE-DOCS.txt` lines 363–374, says expressly that its reinstatement "does not affect any right the Licensor may
have to seek remedies for Your violations".)

Proposed fix: "Reinstatement does not affect the Licensor's right to seek remedies for the breach. The cure does not
apply to Commercial Use, which needs a written agreement under section 7 that may also cover past use." Also say how
notice is given ("by e-mail or by any other means that reaches You").

### L9 — should-fix ⚖ [weakens]. Courts, formation, and what the choice of law can reach

Location: LICENSE.md:121–123 (also CLA.md:51).

* "The courts of the Republic of Cyprus have jurisdiction" does not say exclusive or non-exclusive. Under
  Brussels Ia art. 25(1), an agreed jurisdiction "shall be exclusive unless the parties have agreed otherwise". So the
  Licensor too would have to sue in Cyprus over "disputes arising from" the licence. That could include an
  infringement claim against a licensee who exceeds it, which is the main enforcement case. For defendants outside
  the EU, a Cyprus judgment must then be recognised abroad.
* Art. 25(1) also requires the agreement to be "in writing or evidenced in writing" (25(2): an electronic record that
  provides "a durable record" counts). A licence that is never actively accepted (see L10) may not meet this.
* The choice of Cyprus law reaches the contract. Infringement is governed by "the law of the country for which
  protection is claimed", and the parties cannot choose otherwise (Rome II art. 8(1), 8(3)). The README/licence should
  not suggest that Cyprus law governs every dispute.

Proposed fix (for the lawyer): "The courts of the Republic of Cyprus have non-exclusive jurisdiction over disputes
arising from this licence; this does not limit the Licensor's right to bring proceedings, in particular for
infringement, in any other court that has jurisdiction." Ask the lawyer whether an asymmetric clause is advisable and
valid, and how acceptance is evidenced (L10).

### L10 — should-fix ⚖ [weakens]. How the licence binds: no acceptance clause; bare permission vs contract; the Cyprus research exception

Location: LICENSE.md, whole text (no acceptance clause); §2 "Subject to the conditions"; §5 "You must".

* PolyForm Noncommercial, which this replaced, opened with an acceptance clause ("you must agree to them as both
  strict obligations and conditions to all your licenses"). The new text has none. Without it, a user can argue that
  §5 (citation) and §6 are not obligations they accepted, only conditions of a permission they did not need for their
  acts (for example running a copy they did not make). Cyprus contract law accepts contracts "inferred from the
  conduct of the parties" (Cap. 149 §10(1)), and a contract requires "lawful consideration" (§10(1), §25(1)). Whether
  using free software under these terms forms a contract is for the lawyer.

  Proposed text (top of the licence): "To receive any right under this licence You must accept its terms. By using,
  copying, modifying or distributing the Software You accept them, as conditions of Your licence and as obligations
  You undertake."

* **Statutory exceptions.** Copyright does not cover acts the law permits without a licence, and the licence cannot
  change that (CC 4.0 §8(a) states this expressly for the documentation). In Cyprus, §7(2)(α) of Law 59/1976 exempts
  acts done "in good faith for the purpose of research, private use, critical review or reporting of current events"
  (with acknowledgement of title and authorship if the use is public). §7Β(4), the computer-program article, applies
  "without prejudice to the exceptions of subsection (2) of section 7". The text of §7(2)(α) has no noncommercial
  limit, only the three-step test of §7(6). If the lawyer confirms that §7(2)(α) reaches programs, a company's
  good-faith in-house **research** in Cyprus may need no licence from copyright's side, and the commercial goal there
  rests on contract (L10's acceptance clause) and on distribution control. Put this question to the lawyer. The
  reviewer is not stating how a Cyprus court would decide.

### L11 — should-fix ⚖ [weakens]. The owner's own chain of title is not recorded (addendum point 1)

Location: LICENSE.md:5–6 ("his copyright in the Software"); STATUS.md V20; RESPONSE.md A1.

The addendum's point 1 says the owner can license his own code but "must take into account the rights of employers,
clients and external participants". The response (A1) applies the first half only. Two things are unrecorded:

1. **Employment and commissioning.** Under §11(1) of Law 59/1976, copyright in a work made by an employee "in the
   course of his employment, as part of his duties", **or a work commissioned by a person who is not the author's
   employer**, "is deemed transferred" to the employer or commissioner, "subject to any agreement between the parties
   excluding or limiting such transfer". The repository records nothing on whether any employer or client of the
   owner (in Cyprus or elsewhere, under its own law) could claim the engine. For example: work done during working
   hours, on an employer's equipment, or in a field covered by an employment contract's IP clause.
2. **Code produced by AI sessions.** `AGENTS.md`:5 states that its rules apply "to every agent and session working in
   `engine/`", and RESPONSE.md says the licence texts were "drafted by the session". Under §3(2) (proviso) and §7Β(1),
   a work, including a program, is protected only if it is "the personal intellectual creation of its author". How
   far code written by AI agents under the owner's detailed direction is his personal intellectual creation is
   unsettled. Where it is not, the licence's copyright lever is weaker, and L10's contractual acceptance matters more.

Proposed fix: add to STATUS V20, as an item for the lawyer, a short chain-of-title note by the owner: (a) a statement
that no employer, client or institution has rights in the engine, or that a written waiver exists; (b) a description
of the owner's own creative contribution (architecture, specifications, selection and arrangement, review and
correction of generated code), which the git history and the verbatim directions in AGENTS.md already partly
document; (c) the lawyer's view on how much of the code copyright protects and whether to rely more on contract.

### L12 — nit ⚖ [neutral]. Liability: the new EU product liability regime, and a missing "no endorsement" clause

Location: LICENSE.md:86–98.

* Directive (EU) 2024/2853 applies "to products placed on the market … after 9 December 2026" (art. 2(1)). "Product"
  includes "software" (art. 4(1)). Liability "is not … limited or excluded by a contractual provision" (art. 15). The
  exemption covers only "free and open-source software that is developed or supplied outside the course of a
  commercial activity" (art. 2(2)), and recital 14 says software supplied for a price is supplied commercially. The
  licence declares the Software "not open source" and the owner will sell commercial licences. Whether the free
  research distribution is then "in the course of a commercial activity" is a question for the lawyer. The damage
  covered (art. 6(1): death or personal injury, damage to property not used exclusively for professional purposes,
  destruction or corruption of non-professional data) is unlikely from a physics engine, and the savings clause
  (lines 97–98) already avoids overreach. Nothing to change now; add the question to V20.
* "Not liable to You or to anyone else" (line 94) cannot bind third parties who never accepted the licence. That is
  harmless, but the real protection against third parties is a duty on the licensee not to present results as
  validated by the author. Add to §5 or §8: "You may not state or imply that the Licensor has checked, validated or
  endorses Your results, products or services, and You may not use his name for that purpose."
* Consumers: Law 112(I)/2021 §50–§51 and Annex IV 1(α) (exclusion of liability for death or personal injury) apply
  only if the Licensor is a "trader" (§2 covers a natural person acting for purposes of his "trade, business, craft or
  profession") and the user a consumer. The savings clause handles this. Nothing to change; the lawyer confirms.

### L13 — should-fix [weakens]. An affirmative accuracy statement inside the "No warranty" bullet

Location: lfphys/README.md:174–177; also :8 and :133–134 (checks.out §9).

R4 asked that "tested/certified" claims be limited to their subject. The new bullet reads: "**No warranty.** … Each
function's accuracy is the one stated in its documentation and tests, within its stated validity". In the very
paragraph meant to disclaim, that reads as a representation that the stated accuracy holds. Lines 8 ("Each law is
computed exactly or with a stated and tested error") and 133 ("an interval that provably contains the exact value")
are equally absolute. An earlier physics review (archive 2026-10-23, E12) found one Arb ball that was not a rigorous
enclosure. Express statements in documentation can be read against a general disclaimer.

Proposed wording: line 174 "Each function documents the accuracy that its tests check within its stated validity;
this describes the tests and is not a promise that any result is accurate." Line 8 "… or with an error that is stated
and tested for the cases in its tests." Line 133 "… an interval that, if the implementation is correct, contains the
exact value."

## Part C. Publications and the documentation licence (`PUBLICATIONS.md`, CC BY-NC-SA 4.0)

The additional-permission mechanism itself is sound [useful]. CC's FAQ says altering terms is "distinct from waiving
existing conditions or granting additional permissions than those in the licenses. Licensors may always do so", and
"Material licensed under a CC license but with additional permissions granted or conditions waived may be compatibly
licensed with other material under the same license". PUBLICATIONS §3 attaches conditions only to the **extra**
permission; anyone can still use the documentation under plain CC BY-NC-SA, so nothing is restricted. LICENSE.md §5
binds users of the code, not users of the documentation, so the documentation licence gains no extra restriction. The
documentation is still unmodified CC BY-NC-SA 4.0 (`LICENSE-DOCS.txt` identical in the three places).

### L14 — should-fix [weakens]. The screenshot permission is granted under a licence that does not cover the player

Location: PUBLICATIONS.md:28–34 (item 1(a)), 8–12 (§1: "section 3 gives the permission You need for publication in
any case"); LICENSE.md:74–77; README.md:44–45; visualizations/README.md:167 (checks.out §7).

PUBLICATIONS §3 grants, "under the Creative Commons … License …, in addition to that licence", permission to reproduce
"(a) screenshots and images of the player and the visualizations produced by Your own runs". The player and the
worlds are **code** under LICENSE.md: the README table lists `*.html`, `*.css`, `*.js` as code, and the in-player help
text lives in `viz.py` files. Their protectable elements in a screenshot (layout, help text, drawn interface) are not
CC-licensed material, so an additional permission to the CC licence grants nothing for them. LICENSE.md §6 ("You may
publish such results, including through commercial publishers") does cover images of runs, but with different
conditions (no per-item attribution) and without rights for the publisher. The two files now give two permissions for
the same images on different terms, and PUBLICATIONS §1 points the user to the wrong one. The Russian README (line
167) adds a third classification: it calls the help ("справка") documentation under CC.

Proposed fix: move item (a) into LICENSE.md §6 as a permission of the code licence, surviving termination:

> You, Your publisher and the publisher's licensees may reproduce, adapt for layout and distribute, as part of a
> publication of any kind and in any medium, screenshots and images of the interface of the Software produced by Your
> runs, attributed "Ildar Idrisov, lfphys <version>". This permission continues for publications made before any
> termination.

Keep PUBLICATIONS §3 for (b) the author's documentation figures and (c) documentation excerpts. Rewrite PUBLICATIONS
§1 to point to LICENSE §6. Decide once whether user-visible help strings in code files are code or documentation, and
write the same in README.md:44–45 and visualizations/README.md:167.

### L15 — should-fix [weakens]. The publication permission does not fit open-access journals or the publisher's rights

Location: PUBLICATIONS.md:31–38.

* Many journals and preprint servers publish under CC BY 4.0 or require the author to grant a broad licence. Item 3
  says NC and SA do not apply "to the publication or to these items as they appear in it". It does not say whether
  readers of a CC BY article may reuse the item commercially "as it appears in it". That is a door to commercial
  reuse of the author's figures, and the opposite of what the owner wants.
* "Reproduce" alone does not cover what publishers do: resize or crop, re-letter, translate, and sublicense to
  indexing, archiving and aggregation services.
* It is unclear whether the full CC attribution elements (licence notice, URI, indication of changes) are still
  required, or whether "Ildar Idrisov, lfphys" with the version suffices.

Proposed addition to §3:

> 4. the items may appear in a publication that is itself licensed under any terms, including CC BY 4.0, if each is
> marked "© Ildar Idrisov, lfphys <version>; used with permission; not covered by the licence of this publication";
> this permission does not extend to any use of the items outside the publication;
> 5. the permission extends to the publisher and to its licensees for indexing, archiving, aggregation and
> translation, and to changes of size, format and lettering that do not change the meaning;
> 6. the attribution of item 2 replaces the attribution elements of section 3(a) of that licence.

### L16 — nit [neutral]. Short code excerpts

Location: PUBLICATIONS.md:34.

Item (c) covers "short excerpts of the documentation for quotation". Papers about methods often quote a few lines of
source code, which is the code licence's subject. Quotation exceptions may cover this, but say it: "and short
excerpts of the source code, for explanation or criticism, with attribution".

## Part D. Consistency between files

Confirmed [useful] (checks.out §1–§3): `LICENSE.md`, `CLA.md`, `COMMERCIAL.md`, `CONTRIBUTING.md`, `PUBLICATIONS.md`
and `LICENSE-DOCS.txt` are byte-identical in the root, `lfphys/` and `visualizations/`. `PolyForm` and "Required
Notice" no longer appear outside review folders except as history (`STATUS.md:31`, `AGENTS.md:40`,
`dependencies.md:281`) and in the third-party licence classifier test. Every `py/js/mjs/html/css` file outside
`vendor/` carries the SPDX line. Cross-references inside LICENSE.md (§1 item 1 → section 9; §2 → section 4; §6 →
section 5 and item 4 of section 1; COMMERCIAL.md → "§1, items 3 and 5"; PUBLICATIONS §4 → "§1, item 4") point to the
right places.

### L17 — should-fix [weakens]. The notice rule still puts the owner's copyright line in contributors' files

Location: CONTRIBUTING.md:41–48 (checks.out §8).

"Every source file of the project starts with the lines `SPDX-FileCopyrightText: 2026 Ildar Idrisov …`". A file that a
contributor writes from scratch then carries a copyright claim of someone who wrote none of it, next to the author's
own line. R6 asked to keep "the notices of the actual rights holders" and noted that a licence does not make the
licensee an author. `test_boundary.py` checks only the licence line, so the fix is textual:

> Every source file carries `SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0` and one
> `SPDX-FileCopyrightText` line for each holder of copyright in it: the owner's line in files he authored; a
> contributor's own line (name; e-mail optional) in a file the contributor authored or substantially changed. Nobody
> removes an existing notice.

### L18 — nit [neutral] / [error in earlier]. Summaries drift from the licence; two small inaccuracies in RESPONSE.md

* COMMERCIAL.md:10 and PUBLICATIONS.md:46 say "rights in or early or confidential access to"; the licence says
  "rights in, exclusive or early access to, or confidential use of". Copy the licence's words, or cite the item
  without paraphrase.
* [error in earlier] RESPONSE.md (R10, "verified") lists the remaining `PolyForm` mentions as "the dependency audit's
  history line and a classifier test". `STATUS.md:31` and `AGENTS.md:40` also keep it, correctly, as history. It also
  says the NOTICE and CITATION.cff copies differ "only in the part's title, abstract and third-party line"; the
  CITATION.cff copies also differ in `keywords`. Neither matters legally; record the corrections when processing.

### L19 — nit [neutral]. Two places keep wording that R7 corrected elsewhere

* dependencies.md:312–313 (§8 item 6): "Distributing a built image triggers the LGPL-3.0 duties for FLINT, GMP, MPFR
  (§4) and the EULA conditions for the NVIDIA files". §4 (lines 237–239) now also names the GPL/LGPL components of the
  Debian base and libquadmath. Add them to item 6.
* STATUS.md:32 (V21, closed) still describes the LGPL duty as "their source or a written offer", the phrase R7 called
  too general. It is a closed item, but the "reopen if an image is ever given out" path will read it first. Point it
  to dependencies.md §4.

### L20 — nit [neutral]. Machine-readable licence metadata

* CITATION.cff: CFF 1.2.0 has a `license-url` key, "only for non-standard licenses not included in the SPDX License
  List". Add it when the repository has a public URL (STATUS V20 already lists URL and DOI).
* For SPDX/REUSE tooling, a `LicenseRef-` identifier is normally resolved through `LICENSES/LicenseRef-lfphys-Research-1.0.txt`.
  Optional; `LICENSE.md` works for people.
* `lfphys/pyproject.toml`: until publication, the classifier `Private :: Do Not Upload` prevents an accidental upload
  (PyPI "will always reject packages with classifiers beginning with `Private ::`"). On publication, use the PEP 639
  form (`license = "LicenseRef-lfphys-Research-1.0"`, `license-files = ["LICENSE.md", "NOTICE"]`); PyPI notes that
  licence classifiers are deprecated.

## Part E. The contributor agreement (`CLA.md`)

What dual licensing needs, and whether the CLA gives it: relicensing under any terms, including sublicensing (§2) —
yes [useful]; a patent licence to the Licensor and every recipient, Apache-style scope, defensive termination (§3) —
yes [useful]; assurances on authority, employer consent and third-party material (§4) — yes, with an evidence gap
(L23); successors (§1.3, §2) — yes, too broadly (L21). The licence is non-exclusive, which Cyprus law lets be granted
"in writing, or orally, or … inferred from conduct" (Law 59/1976 §12(6)) and for future works (§12(7)). So the
e-mail/commit-trailer procedure needs no signed paper for the grant itself [useful]. Assignment or an exclusive licence
would need writing (§12(5)); the CLA rightly does not ask for either.

### L21 — error [weakens]. The CLA's "Licensor" includes every licensee of the owner

Location: CLA.md:13–14 (checks.out §5); consequences in §2 (18–21) and §3 (25–31). Related: LICENSE.md:5–6.

"**Licensor**: Ildar Idrisov, and any person or entity to which he later assigns **or licenses** his rights in the
Project". The owner licenses his rights in the Project to every user under the Research Licence and to every
commercial licensee. Read literally, each of them is a "Licensor" under the CLA. Under §2 each then holds a perpetual,
irrevocable licence from every contributor to "sublicense and relicense Your Contributions … under any terms" —
including commercially, which defeats the dual-licensing model for contributed code. Under §6 a contribution sent to
any of them would also count as a submission "to the Licensor". This is the response's implementation of addendum
point 4 going too far. A contributor who notices it may also refuse to sign.

Proposed fix:

> 3. **Licensor**: Ildar Idrisov, and any person or entity to which he assigns his copyright in the Project, or grants
> an exclusive licence of it, by a written instrument (a **Successor**).

and in §2 "… and to transfer this licence to a Successor". In LICENSE.md:5–6 cover the same case: "and any person to
whom he assigns his copyright in the Software, or grants an exclusive licence of it, in writing". As written, a future
company that receives an exclusive licence rather than an assignment would not be the Licensor of the research
licence.

### L22 — should-fix ⚖ [weakens]. Consideration and irrevocability

Location: CLA.md, whole (no consideration recited); §2 "irrevocable".

Cap. 149 §25(1): "An agreement made without consideration is void" unless one of three exceptions applies, none of
which obviously fits a CLA. Whether the Licensor's review and possible inclusion of a contribution count as
consideration (§2(d): an act done "at the desire of the promisor") is for the lawyer. The CLA has one promise from the Licensor (§5.1: keep the contributor's notices) and otherwise only
the contributor's grants and assurances. The copyright grant might survive as a non-contractual licence (§12(6)), but
whether a gratuitous licence can be **irrevocable** is the question that matters for relicensing. It is for the
lawyer.

Proposed fix: a recital and one reciprocal promise, which also make the CLA look less one-sided:

> In consideration of the Licensor's review of Your Contributions, their possible inclusion in lfphys and the
> attribution of section 5.1, You agree as follows. […] 5.4 The Licensor will keep every Contribution that he
> distributes available under a licence that permits noncommercial research at least as broadly as the lfphys Research
> Licence 1.0.

(The 5.4 promise is the owner's choice; it costs him nothing he has not already decided, and it is the usual
counterweight in "outbound-licence" CLAs.)

### L23 — should-fix [weakens]. Employer and client consent: evidence, the form, and the missing organisational agreement

Location: CLA.md:37–39, 58–59, 62–63.

* §4.2 leaves the employer's written permission with the contributor ("You keep the evidence and give it to the
  Licensor on request"). If the contributor leaves or the permission was never obtained, the Licensor has nothing. In
  Cyprus the risk is concrete: §11(1) of Law 59/1976 deems copyright in employees' work done as part of their duties,
  **and in commissioned work**, transferred to the employer or commissioner unless agreed otherwise. Other countries
  and most university IP policies have similar rules.
* The statement form asks only for "Employer or institution with rights in my work". §4.2 also names "client". Use the
  same words in both.
* §6 says "an agreement for organisations is available on request", but there is none. Either write it before the
  first contribution from an employed person, or delete the sentence and accept organisations' consent by a short
  signed waiver.

Proposed fix: "If You are employed or are carrying out commissioned work in a related field, the Licensor accepts Your
Contribution only after receiving the written consent or waiver of Your employer, institution or client (a template is
in `CLA.md` §7 / `CCLA.md`)." Keep the consent with the CLA record, not only with the contributor.

### L24 — nit [neutral]. Scope of the grant and related clauses

Location: CLA.md:18–21, 35–43, 47–51.

* §2 lists US-style acts ("publicly display and perform"). Add the EU/Cyprus ones the owner needs for a hosted player
  and for commercial distribution: "communicate to the public, including making available online, rent and lend, and
  run". Law 59/1976 §7(1)(a)(vi) and §7Β(3) name these separately. Under some laws an unnamed use is construed against
  the grantee.
* Moral rights: Law 59/1976 §7(4) keeps the author's right to object to modifications that harm "honour or
  reputation". Add: "to the extent the law allows, You agree not to object to modifications of Your Contributions made
  in the course of the Project".
* Enforcement: a non-exclusive licensee usually cannot sue infringers of contributed code. Add: "You will, at the
  Licensor's request and cost, give reasonable help in enforcing rights in Your Contributions". Optional.
* §4.1/§4.3: ask contributors to identify material produced with AI tools, since the originality question of L11 then
  applies to it too.

### L25 — nit [neutral]. Running the consent procedure

Location: CLA.md:55–63; CONTRIBUTING.md:46–47.

* A statement placed in a pull-request description can be edited or deleted. Archive it, with the date and the
  commit identifiers, in the record the Licensor keeps.
* Keep an immutable copy (or hash) of the exact CLA 1.0 text that was agreed, since `CLA.md` may change.
* The record holds names, employers and e-mail addresses. GDPR does not apply only to "processing … by a natural person
  in the course of a purely personal or household activity" (art. 2(2)(c)). Recital 18 adds "with no connection to a
  professional or commercial activity", which dual licensing is. A three-line notice in §6 (what is kept, why, for how
  long, contact) is enough.
* CONTRIBUTING.md:47 makes contributors put their e-mail into every file they touch. Make the e-mail optional.
* Minors: "if You are under the age of majority, a parent or guardian must agree as well". Optional.

### L26 — should-fix [weakens]. Two Cyprus-specific requirements for the commercial agreement are not recorded (addendum point 4)

Location: STATUS.md V20 ("a template of the commercial agreement before the first commercial grant"); COMMERCIAL.md:25–28.

The addendum's point 4 also covers existing commercial contracts: what can be transferred to a future company and
what consents that needs. Cap. 149 §62 (novation) needs the other party's agreement. Two points belong in the V20
requirements for the template, so that they are not rediscovered at the first sale:

1. an assignment clause that lets the owner transfer the agreement to a company he controls, without the licensee's
   further consent;
2. for any custom development a commercial client pays for, an express clause that copyright stays with the owner
   (or is licensed to the client). Otherwise Law 59/1976 §11(1)(α) deems copyright in a commissioned work
   **transferred to the commissioner**, and a paid feature would leave the dual-licensed code base.

### L27 — nit [neutral]. Survival and new versions

Location: LICENSE.md:111–112, 117–118.

* Survival lists §§5, 8, 11. Add §1 (the definitions §5 and §8 use), §6 for results obtained before termination (and
  the screenshot permission of L14), and §10 itself.
* "A copy … remains under the version it came with, unless the Licensor offers it under another" can be read as
  letting the Licensor move existing copies to new terms unilaterally. Annex IV 1(ι) of Law 112(I)/2021 lists clauses
  letting the trader "unilaterally modify the terms … without a valid reason" as possibly unfair. Write: "… the
  Licensor may also offer it under a later version, which You may choose to accept."

### L28 — nit [neutral]. Evaluation by businesses (owner's decision)

Location: LICENSE.md:25–26 (4.1 "internal research and development, … testing").

A company cannot try lfphys before asking for a commercial licence; even a one-day trial is Commercial Use. If the
owner wants commercial enquiries, a short evaluation permission ("a business may evaluate the Software for up to 30
days to decide whether to request a commercial agreement, without using its results in its activity") makes the
COMMERCIAL.md route usable. If not, leave it as is; the current text is consistent.

## Part F. Recommendations of the earlier review that were dropped or only partly applied

| earlier item | what was recommended | what happened | here |
|---|---|---|---|
| Addendum §1 | take into account employers', clients' and contributors' rights | contributors: CLA; the owner's own employer/clients: not addressed | L11 |
| Addendum §4 (second paragraph) | commercial contracts: transfer, consents, novation (Cap. 149 §62) | CLA side done; commercial template not given these requirements | L26 |
| R4 (last paragraphs) | keep tested/certified claims within their subject | done in README.md and the bullet's second half; lfphys/README keeps three absolute statements | L13 |
| R5 | controlling commercial use of outputs is a separate contractual task, binding only the licensee | replaced by the circular "or selling them" | L6 |
| R6 | keep the notices of the actual rights holders | half done (own line added, no removal), the "every file starts with the owner's line" rule kept | L17 |
| R7 (bullet 2) | "written offer" too general | fixed in dependencies.md §4, still in STATUS V21 and §8 item 6 scope | L19 |
| R10 | "Сначала установить историю фактических передач" | answered (private repository) | — [useful] |

Nothing else recommended by the earlier review and its addendum was dropped. DISCLAIMER.md (optional there) was
reasonably folded into README and `/legal`. The commercial template and the lawyer's check are tracked in V20.

## Sources (downloaded 2026-10-29; quotations checked against the downloaded text)

* Cyprus, Law 59/1976 on copyright and related rights, consolidated on CyLaw:
  <https://www.cylaw.org/nomoi/enop/non-ind/1976_1_59/full.html>.
  §3(2) proviso: «έργο είναι πρωτότυπο, αν είναι προσωπικό πνευματικό δημιούργημα του δημιουργού του» ("a work is
  original if it is the personal intellectual creation of its author"). §7(2)(α): «Της τελέσεως οιασδήποτε των
  πράξεων … με πνεύμα καλής πίστεως για το σκοπό έρευνας, ατομικής χρήσεως, κριτικής ανασκοπήσεως ή αναφοράς σε
  επίκαιρα γεγονότα, υπό τον όρο ότι, εάν η χρήση αυτή γίνεται δημόσια, αυτή συνοδεύεται από αναγνώριση του τίτλου
  και της πατρότητας του έργου» (copyright does not control acts done "in good faith for the purpose of research,
  private use, critical review or reporting current events, provided that, if the use is public, it is accompanied by
  acknowledgement of title and authorship"). §7(4): the author's right "to claim authorship … and to object to any
  distortion … which would prejudice his honour or reputation". §7Β(1): programs protected «υπό τη μόνη προϋπόθεση ότι
  είναι προσωπικά πνευματικά δημιουργήματα του δημιουργού τους». §7Β(4): «Επιφυλασσομένων των προβλεπομένων στο
  εδάφιο (2) του άρθρου 7 εξαιρέσεων, επιτρέπεται στο νόμιμο χρήστη να προβεί, χωρίς την άδεια του δικαιούχου … και
  στις ακόλουθες πράξεις» ("without prejudice to the exceptions of §7(2), the lawful user may also, without
  authorisation …"). §11(1) proviso (α)–(β): a work made to the commission of a person who is not the author's
  employer, or in the course of employment as part of the author's duties, «το δικαίωμα πνευματικής ιδιοκτησίας
  λογίζεται ως μεταβιβασθέν εις το πρόσωπον … όστις παρήγγειλε το έργον ή εις τον εργοδότην …, επιφυλασσομένης
  οιασδήποτε μεταξύ των μερών συμφωνίας αποκλειούσης ή περιοριζούσης την τοιαύτην μεταβίβασιν». §12(5): assignment and
  exclusive licence valid only in writing. §12(6): a non-exclusive licence «δύναται να χορηγήται είτε εγγράφως, είτε
  προφορικώς, ή έτι αύτη να συνάγηται εκ της συμπεριφοράς». §12(7): licences of future works are valid.
* Cyprus, Contracts Law Cap. 149, CyLaw: <https://www.cylaw.org/nomoi/enop/non-ind/0_149/full.html>. §2(δ):
  «όταν, με απαίτηση του οφειλέτη, ο δανειστής ή οποιοσδήποτε τρίτος προέβηκε ή προβαίνει ή υπόσχεται να προβεί σε
  πράξη ή αποχή, η πράξη αυτή ή αποχή καλείται “αντιπαροχή”» (an act or abstinence at the desire of the promisor is
  "consideration"). §10(1):
  contracts are agreements made «για νόμιμη αντιπαροχή και νόμιμο σκοπό» and «δύνανται να συνάγονται από τη
  συμπεριφορά των μερών». §25(1): «Συμφωνία που συνάφθηκε χωρίς αντιπαροχή είναι άκυρη, εκτός αν» (three exceptions:
  natural love and affection in writing; compensation for something already done; a written promise to pay a
  time-barred debt). §62: novation, rescission and alteration by agreement of the parties.
* Cyprus, Law 112(I)/2021 (consumer protection), CyLaw: <https://www.cylaw.org/nomoi/enop/non-ind/2021_1_112/full.html>.
  §2: «καταναλωτής» a natural person acting outside his trade/business/profession; «εμπορευόμενος» "any natural or
  legal person … acting for purposes relating to his trade, business, craft or profession". §50(1), (4); §51(1): an
  unfair term "does not bind the consumer". Annex IV 1(α) (exclusion of liability for death or personal injury),
  1(ι) (unilateral modification of terms without a valid reason).
* Regulation (EU) No 1215/2012 (Brussels Ia), art. 25(1): "Such jurisdiction shall be exclusive unless the parties
  have agreed otherwise. The agreement conferring jurisdiction shall be either: (a) in writing or evidenced in writing
  …"; 25(2): "Any communication by electronic means which provides a durable record of the agreement shall be
  equivalent to 'writing'." Publications Office: <https://publications.europa.eu/resource/celex/32012R1215>.
* Regulation (EC) No 864/2007 (Rome II), art. 8(1): "the law of the country for which protection is claimed"; 8(3):
  "may not be derogated from by an agreement pursuant to Article 14."
  <https://publications.europa.eu/resource/celex/32007R0864>.
* Directive (EU) 2024/2853 (product liability): art. 2(1) "products placed on the market or put into service after 9
  December 2026"; 2(2) "does not apply to free and open-source software that is developed or supplied outside the
  course of a commercial activity"; 4(1) product "includes … software"; 4(7) "making available on the market" means
  "any supply … in the course of a commercial activity, whether in return for payment or free of charge"; 6(1) the
  types of damage; 15 "not … limited or excluded by a contractual provision"; recital 14 (software "supplied in
  exchange for a price … is therefore supplied in the course of a commercial activity").
  <https://publications.europa.eu/resource/celex/32024L2853>.
* Regulation (EU) 2016/679 (GDPR), art. 2(2)(c) and recital 18 ("purely personal or household activity and thus with
  no connection to a professional or commercial activity"). <https://publications.europa.eu/resource/celex/32016R0679>.
* Creative Commons FAQ, "Can I change the license terms or conditions?" and "Can I waive license terms or
  conditions?": <https://creativecommons.org/faq/>. CC BY-NC-SA 4.0 legal code as in `LICENSE-DOCS.txt` §6(b), §7,
  §8(a), §8(c).
* Citation File Format 1.2.0 schema, `license-url`:
  <https://raw.githubusercontent.com/citation-file-format/citation-file-format/1.2.0/schema.json>.
* PyPI classifiers page ("PyPI will always reject packages with classifiers beginning with `Private ::`"; licence
  classifiers deprecated by PEP 639): <https://pypi.org/classifiers/>.

No personal identifier was sent to any of these services. Rome I art. 6, cited by the addendum, was not re-checked
here.
