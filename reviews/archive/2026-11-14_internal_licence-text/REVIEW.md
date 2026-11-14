# Review of the licence amendment "lfphys Research Licence 1.0, text of 14 November 2026"

Date: 2026-11-14. Type: independent review (licence lawyer's reading and a teacher's reading). Reviewer did not draft
the amendment and edited no repository file. Read in full: the new `LICENSE.md` (and checked the two copies), `NOTICE`
×3, `PUBLICATIONS.md` ×3, `COMMERCIAL.md` ×3, `CITATION.cff` ×3, the blocks "Licence and citation" of `README.md` and
`README.ru.md`, the drafter's `LICENSE.diff`, `other_files.diff`, `NOTES.md`, the originals in `orig/`, the review
`reviews/archive/2026-10-29_internal_licensing/` (REVIEW, RESPONSE, ADDENDUM_CYPRUS), the CC BY-NC-SA 4.0 text in
`LICENSE-DOCS.txt`, `visualizations/player/js/legal.js`, `js/worksheet.js`, `locales/ru.json`, the licence sections of
`visualizations/README*.md`, `lfphys/README.md`, `lfphys/LAYERS.md`, `AGENTS.md`, `CLA.md` §5, `STATUS.md` V20, the
site scripts (`visualizations/site/`), `visualizations/s03_projectile/viz.py` (where a worksheet lives) and
`lfphys/sources/explore_2026-11-14_design.md`.

This is a legal analysis of the texts, not the opinion of a Cyprus lawyer (STATUS V20 stays open).

Tags after the severity: [useful] the amendment's idea is right and only the wording needs work; [weakens] the text, as
written, weakens what 1.0 or the owner's goal secures; [neutral]; [error in earlier] a defect already in the text of
12 November that the amendment makes visible.

Counts: **2 error, 15 should-fix, 8 nit** (25 findings).

---

## Findings

### F1 — error [weakens]. The conditions of `LICENSE.md` are imposed on the Site Materials, which §9 licenses under CC BY-NC-SA 4.0

**Where:** `LICENSE.md` §1 item 9 ("distributing the Software, Images of Runs **or Site Materials**"), §5A item 1
("Every Public Use must carry this line"), §5A item 7 ("a condition of the licence under which You use the Software
**and the Site Materials**"), §10 (termination and cure); echoed in `NOTICE` ("any public use ... of the materials of the
public site must carry this line (LICENSE.md section 5A ...)"), `PUBLICATIONS.md` §5 first paragraph, both READMEs.

**What is wrong.** §1 item 1 takes the Site Materials out of the Software and §9 licenses them under the standard CC
BY-NC-SA 4.0. Their terms are then those of CC, and only those:
- A person who downloads a poster or a recording from the site receives the CC offer (CC §2(a)(5)(A)) and never
  accepts `LICENSE.md`; the Acceptance clause of `LICENSE.md` ("By using, copying ... the Software") does not reach him.
  For such a person §5A is not a term at all.
- For a person who has accepted `LICENSE.md`, CC §7(b) makes any other arrangement about the Licensed Material
  "separate from and independent of" the CC licence. §5A then works, at best, as a separate contract, and the CC notice
  at the end of `LICENSE-DOCS.txt` says Creative Commons does not allow its marks to be used "in connection with any
  unauthorized modifications to any of its public licenses or any other arrangements ... concerning use of licensed
  material". Material labelled "CC BY-NC-SA 4.0" with extra conditions is no longer a clean CC licence — the 2026-10-29
  review (R10) already warned that a substantively changed CC must not be presented as standard CC.
- The extra conditions are real, not cosmetic: (a) "Public Use" includes "showing them in a class, lecture, talk", which
  is wider than CC's "Share" (to provide material *to the public*); a closed class is often not "the public", and CC
  then requires no attribution at all; (b) §5A item 1 fixes the exact line, while CC §3(a)(2) lets the reuser satisfy
  attribution "in any reasonable manner based on the medium, means, and context"; (c) `LICENSE.md` §10 ends rights on a
  breach and reinstates them only on the first breach and only after notice, while CC §6(b) reinstates automatically
  on a cure within 30 days of discovery, every time.
- §9 itself states the correct mechanism (the line is what the Licensor "requests under section 3(a)(1)(A)(i)"), so §9
  and §5A items 1 and 7 contradict each other on what binds the reuser of a Site Material.

**Proposed wording.**
- §1 item 9: "**Public Use** means distributing the Software or Images of Runs, displaying or performing them in public,
  ... Use that only You ... see is not Public Use." (delete "or Site Materials").
- §5A item 7, first sentence: "The line is a condition of this licence for the Software and Images of Runs."
- New §5A item 9 (or a sentence at the end of §9): "**Site Materials.** This section does not apply to the Site
  Materials. Their use is governed by CC BY-NC-SA 4.0 alone (section 9), under which the line is the attribution that
  the Licensor supplies and requests; a breach of that licence has the consequences that licence gives it."
- `NOTICE`, Attribution paragraph: "Attribution: any public use of the software or of screenshots, images and videos of
  its runs must carry this line (LICENSE.md section 5A) ... The materials of the public site carry the same line as
  the attribution that their licence, CC BY-NC-SA 4.0, asks You to keep (LICENSE.md section 9)."
- `PUBLICATIONS.md` §5, first sentence: drop "or the materials of the public site" from the list governed by §5A; the
  second paragraph (on CC) already says the rest.

### F2 — error [weakens]. Worksheets (and "guides") are at once Software and Site Materials; the same text has two licences

**Where:** `LICENSE.md` §1 item 1 (Software includes "the texts and images that the program itself shows when it runs
(its interface and help)") against §1 item 8 (Site Materials include "worksheets and guides"); §9.

**What is wrong.** A worksheet is not a separate document: `visualizations/player/js/worksheet.js` says it is "data,
not a separate document", generated by the player from the world's registry entry; the text is `WORKSHEET = {...}` in
`visualizations/s03_projectile/viz.py`, a file whose header says `SPDX-License-Identifier:
LicenseRef-lfphys-Research-1.0`. The design (`lfphys/sources/explore_2026-11-14_design.md`, §5) says the same of the
guided steps ("The guide is data in `viz.py`"). So the worksheet text is "text that the program itself shows when it
runs" (Software, §1 item 1) and, once the site serves it, a "worksheet that the Licensor makes and publishes on the
public site" (Site Material, §1 item 8), which item 1 then excludes from the Software. Result:
- the licence of a given worksheet depends on whether it is, at the moment, on the site, and the file's SPDX line says
  the opposite of §9;
- a teacher who copies the worksheet into a handout cannot tell whether he needs CC's notices and ShareAlike or
  `LICENSE.md` §4 (full licence text and `NOTICE` with every copy) — and §4 would make a printed handout impractical;
- the earlier review (R5) asked precisely for clear boundaries between code, the author's material and the user's
  results; this re-blurs them.

"Guides" is a second instance: the READMEs' guides are already documentation (§9), the player's guided steps are
Software, and §1 item 8 does not say which "guides" it means.

**Proposed wording.** Choose by location, not by publication:
- §1 item 8: "**Site Materials** means the recordings, the posters, the Explore and lab-work atlases, and the texts of
  the worksheets and of the guided steps of the worlds, that the Licensor makes, wherever they are stored — on the
  project's public site (https://ildar-idrisov.github.io/lfphys/), in its build or in the source files of the worlds —
  and anything else that the site marks as licensed under CC BY-NC-SA 4.0. It does not include the program that plays,
  shows or prints them."
- §1 item 1, second sentence: "... together with the texts and images that the program itself shows when it runs (its
  interface and help), other than the Site Materials. It does not include the documentation (section 9), the Site
  Materials (item 8) or the third-party components ..."
- In each `viz.py` that holds a worksheet or guided steps: a second SPDX expression or a comment above the data, e.g.
  `# The texts of WORKSHEET and STEPS are Site Materials: CC-BY-NC-SA-4.0 (LICENSE.md §1 item 8, §9).`, and
  `lfphys/tests/test_boundary.py` taught to accept it.

If the owner prefers to keep worksheets under `LICENSE.md`, then delete "worksheets and guides" from item 8 and add to
§5A item 3 an explicit permission to print and hand out worksheets for teaching, with the line, without §4.

### F3 — should-fix [neutral]. "Images of Runs" also covers the Licensor's own posters, recordings and atlas frames

**Where:** `LICENSE.md` §1 item 7 against item 8.

**What is wrong.** Item 7 is not limited to images *You* make: "screenshots, still images, animations and video
captures of the Software's runs". The posters (`site/posters.mjs` renders the worlds into `docs/images/`) and the
recordings are exactly that, so they are both Images of Runs (§5A item 3: Noncommercial Research only, `LICENSE.md` §10)
and Site Materials (§9: CC BY-NC-SA 4.0, CC §6). Two regimes for the same file.

**Proposed wording.** Item 7: "**Images of Runs** means screenshots, still images, animations and video captures that
You make of the Software's runs or of its interface, whole or in part, including those that You resize, crop or
annotate. The Site Materials are not Images of Runs; a screenshot of the Software playing a Site Material is an Image
of Runs for the Software's interface and remains a Site Material for its content."

### F4 — should-fix [useful]. §6.1 disclaims rights in "the figures and images of Your runs", while §5A item 3 licenses them on a condition; the basis of the line on images is not stated

**Where:** `LICENSE.md` §6 item 1 ("claims no ownership of ... the figures and images of Your runs"), §5A item 3, §6
item 3(a) ("screenshots and images of the interface of the Software produced by Your runs"), §1 item 7. Also flagged
in the drafter's `NOTES.md`.

**What is wrong.** Three phrasings for overlapping things. Under §6.1 the user owns "images of Your runs"; under §5A.3
he "may make Public Use of Images of Runs ... on the condition of this section" — a permission for something the
Licensor has just said he does not own. A court will ask what right is licensed. For a screenshot that reproduces the
interface (copyright material of the Licensor) the line is a licence condition; for a plot of the user's numbers it can
only be a contractual obligation accepted under the Acceptance clause. The text should say so, otherwise a user can
argue the condition has no object, and the sentence added to §6.1 ("The attribution of section 5A is a condition of the
licence to use the Software, not a claim to these results") does not close the gap.

**Proposed wording.**
- §6 item 1: "The Licensor claims no ownership of the results You obtain with the Software in Noncommercial Research
  (numbers, data, and the figures You make from them) and no rights in Your publications. Images of Runs may reproduce
  the Software's interface, in which the Licensor keeps his rights; their use is governed by section 5A, item 3, and
  item 3 of this section."
- §5A item 3: "You may make Public Use of Images of Runs for Noncommercial Research, without the conditions of section
  4, if each carries the line. Whether or not an Image of Runs reproduces material in which the Licensor holds rights,
  You undertake to carry the line as an obligation of this licence (Acceptance)."
- §6 item 3(a): "Images of Runs (section 1, item 7) produced by Your runs".

### F5 — should-fix [weakens; error in earlier]. §6.3 ("a publication of any kind and in any medium") swallows §5A item 3 and its noncommercial limit

**Where:** `LICENSE.md` §5A item 3, last sentence ("Item 6.3 continues to govern their use in publications"), §5A item
4, §6 item 3.

**What is wrong.** §6.3 lets You, Your publisher and the publisher's licensees reproduce Images of Runs "as part of a
publication of any kind and in any medium — including one licensed under any terms", attributed only "Ildar Idrisov,
lfphys <version>", with no noncommercial limit (1.0 wanted commercial scholarly publishers). A video, a web page, a
blog post or a popular book is "a publication of any kind". Since §5A.3 defers to §6.3 "in publications", a monetised
video or a commercial textbook can rely on §6.3 and escape both the Noncommercial Research limit of §5A.3 and, arguably,
the line (only §5A.4 says what replaces the line, and only for §5 publications, so the two attributions now overlap
unclearly). The player's own summary already reads §6.3 as "may be published anywhere" (F15). This is against the
owner's "commercial use is forbidden" and "attribution on any public use".

**Proposed wording.**
- §6 item 3, opening: "You, Your publisher and the publisher's licensees may reproduce ... as part of a publication of
  the kinds listed in section 5 (articles, preprints, theses, books, reports, conference contributions, datasets),
  including one published by a commercial publisher and one licensed under any terms ..." (keep the rest).
- §5A item 3, last sentence: "Item 6.3 governs their use in the publications that it covers; every other Public Use,
  including a video, a web page or a post, is governed by this item."
- §5A item 4: "In a publication covered by item 6.3, the attribution of item 6.3 for each item reproduced, together
  with the citation of section 5 where that section applies, takes the place of the line for the items and results it
  covers."

### F6 — should-fix [useful]. A research talk needs less attribution than a school lesson

**Where:** `LICENSE.md` §5 ("in informal media (a post, slides) 'lfphys (Ildar Idrisov)' with the version suffices")
with §5A item 4 (the §5 citation "takes the place of the line"), against §5A item 5 (the full line once in a lesson).

**What is wrong.** Slides reporting results are a §5 publication in informal media; by §5A.4 the short form "lfphys
(Ildar Idrisov)" replaces the line, so no address is needed. A teacher's slides need the full line with the address.
Also a "post" with a result: short form, no address; the same post with a screenshot but no result: full line. Users
will not follow that distinction.

**Proposed wording.** §5, sentence on informal media: "... in informal media (a post, slides, a talk) the line of
section 5A, item 1, with the version, suffices."

### F7 — should-fix [weakens for users]. "Public Use" catches homework, correspondence and peer review, and a forgotten line ends the licence

**Where:** `LICENSE.md` §1 item 9 (last sentence), §10.

**What is wrong.** Only use "that only You, or only the members of Your own research or working group, see" is outside
Public Use. A student's homework or lab report handed to a teacher, a screenshot e-mailed to a colleague in another
group, a manuscript under review or a thesis draft read by a committee are all "material that others see". Each then
needs the line, and under §10 a missing line ends all rights automatically; the cure works only for the first breach
and only within 30 days *after the Licensor's notice*. A student who forgets the line twice has lost the licence to use
the Software in his course. CC BY-NC-SA, which the same project uses for its documentation, reinstates automatically
on cure within 30 days of discovery, every time (CC §6(b)). This is disproportionate for the audience the owner wants
(teachers and students) and invites ignoring the clause.

**Proposed wording.**
- §1 item 9, last sentence: "Use that only You, the members of Your own research or working group, or Your teachers,
  examiners, supervisors, reviewers and correspondents see — such as coursework handed in for assessment, a manuscript
  under review, or a private message — is not Public Use."
- §10, after the first sentence: "Where the breach is only a missing or incomplete citation or attribution line, Your
  rights are reinstated automatically if You correct it within 30 days after You learn of it (an erratum, an updated
  preprint, a corrected repository record, the line added to the material); this applies to every such breach."
  (Keep the first-breach-after-notice rule for other breaches.)

### F8 — should-fix [weakens]. §10 makes the whole of §5A survive termination, including the permission of item 3

**Where:** `LICENSE.md` §10, last sentence ("Sections 1, 5, 5A, 6 (...) ... survive termination").

**What is wrong.** §5A.3 is a grant ("You may make Public Use of Images of Runs"). Unqualified survival lets a
terminated licensee argue that he may go on making new Public Use of Images of Runs. What should survive is the
obligation to keep the line on what was already made public, and the name clause.

**Proposed wording.** "Sections 1, 5, 5A (items 1, 2, 4, 7 and 8, and item 3 only for material made public before
termination), 6 (for results and publications made before termination), 8, 10 and 11 survive termination."

### F9 — should-fix [useful]. The line is not supplied where the licence and CC assume it is

**Where:** `LICENSE.md` §5A item 5 ("Showing the Software running, with its interface unaltered, needs no further
line"), §9 ("the Licensor supplies ... the attribution line"); the player and the site (`visualizations/player/`,
`visualizations/site/build.py`).

**What is wrong.**
- The player's interface does not show the line. `start.js`, `player.js`, `demo.js` have a "GitHub"/"Source (GitHub)"
  link; no page shows "lfphys — Ildar Idrisov — https://…". So "needs no *further* line" leaves a teacher who only
  projects the player unsure whether he must add the line himself (the word "further" implies a first one exists).
- The printable worksheet (`js/worksheet.js`) prints no line and no CC notice. CC §3(a)(1)(A) requires the reuser to
  retain the creator identification and the other notices only "if it is supplied by the Licensor with the Licensed
  Material". If the site, the worksheet print, the poster files and the recording player do not carry the line and the
  notices, the reuser owes only CC §3(a)(1)(B)–(C), and the §9 request has no effect. The drafter's NOTES say this too;
  it should be done before the amended text is relied on.

**Proposed wording.** §5A item 5, last sentence: "Showing the Software running, with its interface unaltered, meets
item 1 by itself." Implementation (STATUS item): the player's footer (start page, run page, `/legal`) shows the line;
the worksheet print, every poster page and the recording player show "lfphys — Ildar Idrisov —
https://ildar-idrisov.github.io/lfphys/ — CC BY-NC-SA 4.0" with a link to the licence.

### F10 — should-fix [useful]. §9 maps the line only to CC §3(a)(1)(A)(i); the address belongs to (v), and the other notices should be supplied too

**Where:** `LICENSE.md` §9, third sentence; `PUBLICATIONS.md` §5, second paragraph.

**What is wrong.** CC §3(a)(1)(A)(i) is "identification of the creator(s) ... and any others designated to receive
attribution". The project name may be designated, but the web address is (v), "a URI or hyperlink to the Licensed
Material" — and the repository address is not the address of the Site Materials; the site's is. For Site Materials
the line with the repository URL is therefore a less accurate request than the one with the site URL. The copyright
notice (ii), the notice referring to the licence (iii) and to its disclaimer (iv) are also retained only if supplied.

**Proposed wording.** §9: "For the Site Materials the Licensor supplies, and requests under section 3(a)(1)(A) of that
licence, the line of section 5A, item 1, with the address of the public site, as the identification of the creator
and of the project (i) and the URI of the material (v), together with the notices of its items (ii)–(iv); sections
3(a)(1)(B) and (C) and 3(b) of that licence apply as it states." One practical line for teachers, in `PUBLICATIONS.md`
§5: "For a Site Material, this one line satisfies all of it: `lfphys — Ildar Idrisov —
https://ildar-idrisov.github.io/lfphys/ — CC BY-NC-SA 4.0 (https://creativecommons.org/licenses/by-nc-sa/4.0/)`, plus
'changed by <You>' if You changed it."

### F11 — should-fix [useful]. `PUBLICATIONS.md` §5 does not tell a teacher that an adapted worksheet must stay under CC BY-NC-SA

**Where:** `PUBLICATIONS.md` §5, second paragraph.

**What is wrong.** The most common teacher action — editing a worksheet and sharing the edited copy — triggers CC
§3(b) (ShareAlike): the adaptation must be licensed under BY-NC-SA 4.0 (or a later or compatible licence), with no
additional restrictions (CC §3(b)(3)). The paragraph lists only the licence notice and the change notice. A teacher who
puts an edited worksheet into a course pack "all rights reserved" or under CC BY breaches CC.

**Proposed wording.** Add: "If You adapt a Site Material — for example, edit a worksheet — and share the result, You
must license Your adaptation under CC BY-NC-SA 4.0 (or a later version or a compatible licence) and add no terms that
restrict it (that licence, section 3(b)). Quoting short parts in Your own material is not an adaptation."

### F12 — should-fix [weakens: promises differ from the licence]. The README blocks (EN and RU) over- and under-state the licence

**Where:** `README.md` and `README.ru.md`, "Licence and citation" / «Лицензия и цитирование», bullets "Required" /
«Обязательно» and "Not allowed" / «Запрещено».

**What is wrong.**
1. "a link to lfphys" — the licence requires the full *line* (name, author, address), and in print a "link" is not a
   thing; RU «ссылка» is ambiguous between reference and hyperlink.
2. "Screenshots ..., the materials of its site, teaching materials, websites, presentations, videos and posts carry the
   line" reads as if every teaching material, website and post must carry it, not only those that use lfphys.
3. It does not say that in a publication of results the citation takes the place of the line (§5A.4), so a researcher
   reads both as required.
4. For the site's materials, it promises that the line is enough; CC also requires the licence notice and a change
   notice, and ShareAlike for adaptations (F10, F11).
5. The name: "naming ... after lfphys so that it seems to come from the project" is a qualified ban; `LICENSE.md` §5A.8
   bans the name in the name of a product, service, course, website or other work outright, and separately any other
   implication of origin (see F13). `NOTICE` and `PUBLICATIONS.md` §5 have the same qualified wording.

EN and RU are otherwise consistent with each other (same items, same order, same date of the text).

**Proposed wording (EN).**
"* **Required:** credit lfphys whenever you use it in public, and cite it in publications. Anything public that uses
  lfphys — a screenshot, image or video of its runs, a material of its site, or teaching materials, a website, a
  presentation, a video or a post that includes them — carries the line `lfphys — Ildar Idrisov —
  https://github.com/ildar-idrisov/lfphys` (the site's address will do too; in a lesson, once on the material you show
  or hand out). A publication of results obtained with lfphys cites it with its version instead
  ([`CITATION.cff`](CITATION.cff); the player shows the version on its page "Licence"). The site's materials are under
  CC BY-NC-SA 4.0: also name that licence, mark your changes, and share adapted copies under the same licence. Keep the
  author's notices when you share lfphys or its documentation.
* **Not allowed:** any commercial use, by anyone, without a separate written agreement
  ([`COMMERCIAL.md`](COMMERCIAL.md)); using the name lfphys as the name of your own product, service, course or site, or
  so that it seems to come from or be endorsed by the project (saying that you use lfphys is fine)."

**Proposed wording (RU).**
"* **Обязательно:** указывать lfphys при любом публичном использовании и цитировать его в публикациях. Всё публичное,
  что использует lfphys, — скриншот, изображение или видео его запусков, материал его сайта, а также учебные
  материалы, сайт, презентация, видео или пост, в которые они входят, — несёт строку `lfphys — Ildar Idrisov —
  https://github.com/ildar-idrisov/lfphys` (подойдёт и адрес сайта; на уроке — один раз на материале, который вы
  показываете или раздаёте). Публикация полученных с lfphys результатов вместо этого цитирует его с версией (...).
  Материалы сайта — под CC BY-NC-SA 4.0: укажите и эту лицензию, отметьте свои изменения, а изменённые копии
  распространяйте под той же лицензией. Когда вы передаёте lfphys или его документацию, сохраняйте уведомления автора.
* **Запрещено:** любое коммерческое использование кем бы то ни было без отдельного письменного соглашения (...);
  называть именем lfphys свой продукт, сервис, курс или сайт или использовать имя так, будто они исходят от проекта
  или одобрены им (сказать, что вы используете lfphys, можно)."

### F13 — should-fix [useful]. The name clause: draw the line between "naming" and "factual reference" more precisely, and do not reserve more than the Licensor has

**Where:** `LICENSE.md` §5A item 8; its summaries in `NOTICE`, `PUBLICATIONS.md` §5, READMEs.

**What is wrong.**
- Without a registered mark the clause binds only those who accept the licence (as a contractual term) and otherwise
  rests on passing off / unfair competition; that is sensible, and §5A.8 rightly avoids the words "trademark" and "™".
  But "the Licensor reserves them" asserts a reservation of rights he may not have in a bare word; safer "reserves
  whatever rights he has in them".
- "in the name of a product, service, course, website or other work or activity" is a per se ban, yet titles such as
  "Simulating optics with lfphys" (a talk, a paper, a student project repository "lfphys-homework") are both "the name
  of a work" and a factual reference. The example covers only the extremes.
- The fork exception covers a copy "that You distribute under section 4", not a copy that a school hosts under item 4.3
  (hosting is not distribution); a hosted unmodified player shows "lfphys" in its interface.

**Proposed wording.** "8. **The name.** This licence grants no right in the name "lfphys" or in any logo of the
project, now or later; the Licensor reserves whatever rights he has in them. You may not use the name or a logo, or a
name or sign confusingly similar to them, as the name or as a distinguishing part of the name of a product, service,
course, website, organisation, event or software of Your own, or in any other way that states or implies that
something comes from, or is endorsed by, the Licensor or the project. You may use the name in a factual way: in the
attribution line, in a citation, and in a title or text that says truthfully that You use the Software, that Your work
is based on it, or that Your results were obtained with it ("Simulating optics with lfphys", "a course on optics using
lfphys"); "lfphys Optics Course" is not factual. A copy of the Software, modified or not, that You distribute under
section 4 or let others use under item 4.3 may keep the name in its files, identifiers, interface and notices, if it
is marked as section 4 requires and a modified copy is not presented as the Licensor's version. ..." — and the three
summaries say "using the name lfphys as (part of) the name of your own product, service, course or site, or so that it
seems to come from or be endorsed by the project".

### F14 — should-fix [error in earlier]. `CITATION.cff` gives no address, although §5 makes it the source of the address to cite, and the repository has been public since 12 November

**Where:** `CITATION.cff` ×3 (no `url`, `repository-code`, `license-url`); `LICENSE.md` §5 ("the persistent identifier or
web address that the Licensor gives in `CITATION.cff`"); `PUBLICATIONS.md` §2 ("Until the repository is published,
`CITATION.cff` gives no web address or DOI"); `STATUS.md` V20 ("before the repository is published: a persistent
address ... in `CITATION.cff` with its `license-url`").

**What is wrong.** The repository is public; the attribution line now names an address, but the citation the licence
requires still has none, `PUBLICATIONS.md` §2 is stale, and GitHub's "Cite this repository" produces a reference with
no address. V20's pre-publication item is overdue.

**Proposed wording.** `CITATION.cff` ×3: add
`repository-code: "https://github.com/ildar-idrisov/lfphys"`, `url: "https://ildar-idrisov.github.io/lfphys/"`,
`license-url: "https://github.com/ildar-idrisov/lfphys/blob/main/LICENSE.md"` (a DOI later, not invented).
`PUBLICATIONS.md` §2: "`CITATION.cff` gives the repository's address (a DOI will be added when one exists). A form that
fits most journals: I. Idrisov, lfphys: a physics engine and interactive visualizations of physical hypotheses, version
<version>, https://github.com/ildar-idrisov/lfphys." Mark the V20 sub-item done.

### F15 — should-fix [weakens: the player tells users the old terms]. The player's licence page and `visualizations/README*.md` contradict §5A

**Where:** `visualizations/player/js/legal.js` lines 21–25 and the `TEXTS` labels (32–37); `visualizations/locales/ru.json`
lines 30 and 335–336 and the legacy snapshot `player/legacy/ru-2026-11-12.json` (per NOTES); `visualizations/README.md`
"Licence, citation, contact" (~l. 385) and `visualizations/README.ru.md` (~l. 361).

**What is wrong.** The page `/legal` is the one §4.3 requires every host to show. Its summary says "Snapshots of your
runs and short excerpts of the code may be published anywhere, including under CC BY, with the credit 'Ildar Idrisov,
lfphys <version>'". After the amendment that is wrong: outside the publications of §6.3 they need the line and are
noncommercial only (F5). The page says nothing about the line, the name or the site's materials; its documentation
bullet and the label "Licence of the documentation: CC BY-NC-SA 4.0" omit the site's materials. `visualizations/README.md`
says the same ("may be published anywhere"), while `README.ru.md` says «в любых изданиях» ("in any publications") —
EN and RU already differ.

**Proposed wording (EN msgids; RU in `ru.json`).**
- Results bullet, replace the snapshot sentence: "Snapshots of your runs and short excerpts of the code may be
  reproduced in a scholarly publication, including under CC BY, with the credit “Ildar Idrisov, lfphys &lt;version&gt;”.
  Any other public use of snapshots and videos of your runs — teaching materials, websites, presentations, videos,
  posts — is allowed for noncommercial purposes with the line <span class=\"mono\">lfphys — Ildar Idrisov —
  https://github.com/ildar-idrisov/lfphys</span>."
- New bullet: "<b>The name</b> “lfphys” is not licensed: do not use it as the name of your own product, course or site;
  saying that you use lfphys is fine."
- Documentation bullet: "<b>The author's documentation, figures and the materials of the public site</b> (recordings,
  posters, atlases, worksheets) — CC BY-NC-SA 4.0, with the line above as the credit; ..."
- Labels: "Licence of the code: lfphys Research Licence 1.0 (text of 14 November 2026)"; "Licence of the documentation
  and the site's materials: CC BY-NC-SA 4.0".
- `visualizations/README.md` / `.ru.md`: the same change to the snapshot sentence, identical in both languages.

### F16 — should-fix [neutral]. `CLA.md` §5.4 now points at two texts

**Where:** `CLA.md` §5 item 4 ("at least as broadly as the lfphys Research Licence 1.0"), copies in `lfphys/` and
`visualizations/`.

**What is wrong.** §5.4 is the Licensor's promise to contributors (added as consideration, STATUS V20). "1.0" now names
both the text of 12 November and the text of 14 November; the newer one is *narrower* for users (the line, the name
clause). If any contribution was accepted under the earlier text, keeping it only under the new text could be argued
to break the promise. With 0 forks and no external contributors that is theoretical, but the reference should be
exact.

**Proposed wording.** "... under a licence that permits noncommercial research at least as broadly as the lfphys
Research Licence 1.0, text of 14 November 2026 (conditions of attribution and of the use of the project's name aside)."
And record in the response that no contribution was accepted between 12 and 14 November.

### F17 — should-fix [weakens; owner's decision]. Moving worksheets, atlases and recordings under CC changes the meaning of "commercial" for them

**Where:** `LICENSE.md` §1 item 1, item 8, §9; `PUBLICATIONS.md` §3 item 1 (now "including the materials of the public
site"); README "Not allowed: any commercial use, by anyone".

**What is wrong.** Under `LICENSE.md` §1 item 4, use by or for a business, including internal R&D and for-profit
schools ("An educational institution that is itself a business is a business"), is Commercial Use whatever the purpose.
Under CC, NonCommercial is "not *primarily* intended for or directed towards commercial advantage" — a purpose test
that the CC FAQ itself treats case by case. Worksheet texts were Software (interface/help) under the text of 12
November; now a business's internal training or a for-profit tutor's handout is a grey zone rather than clearly
commercial. In addition, `PUBLICATIONS.md` §3 now lifts NC and SA for site materials reproduced in scholarly
publications. This is a legitimate choice (teachers gain clear CC terms), but it is a weakening against the owner's
"keep everything noncommercial ... commercial use is forbidden", and the README's "any commercial use, by anyone" is
then accurate for the code only (`COMMERCIAL.md` already says this correctly).

**Proposed wording.** Owner decides. If accepted, README "Not allowed": "any commercial use of the code, by anyone,
without a separate written agreement; for the documentation and the site's materials, commercial use as CC BY-NC-SA
4.0 defines it (`COMMERCIAL.md`)". If not accepted, keep worksheets and guided steps in the Software (F2, second option).

### F18 — nit [neutral]. The "Note on this text": make the earlier text identifiable; keep the date true

**Where:** `LICENSE.md`, "Note on this text"; header "Text of 14 November 2026."

**What is wrong.** Two different texts now share the name, the version and the SPDX identifier
`LicenseRef-lfphys-Research-1.0`; "A copy obtained under the earlier text remains under it" is workable only if the
earlier text can be found. Item 11.2 speaks of "new versions"; an in-place text is not one, so "(item 11.2)" is an
analogy. The working tree is uncommitted: if it is committed or pushed after 14 November, the dated heading is false.

**Proposed wording.** "... A copy obtained under the earlier text (commit <hash>, https://github.com/ildar-idrisov/lfphys/blob/<hash>/LICENSE.md)
remains under it, as item 11.2 provides for versions; the Licensor also offers that copy under this text, which You may
choose to accept." Commit and push on the date in the heading, or change the date.

### F19 — nit [useful]. §2 does not list public display and performance; short code excerpts in teaching materials still fall under §4

**Where:** `LICENSE.md` §2; §5A item 3.

**What is wrong.** §5A presupposes that showing the Software in a class or talk is permitted, but §2 grants "use, run,
copy and modify ... distribute"; public display/performance of the interface is only implied. A teacher who puts a
20-line excerpt of the code on a course page distributes part of the Software and, by the letter, needs §4 (licence
text and `NOTICE` with it); §6.3(b) covers excerpts only inside publications.

**Proposed wording.** §2: "... to use, run, copy and modify the Software, to display and perform it in public, to make
works based on it ...". §5A item 3: "You may make Public Use of Images of Runs, and of short excerpts of the source
code for explanation or criticism, for Noncommercial Research ...".

### F20 — nit [neutral]. "Explore atlases" and "guides" are project jargon in a definition

**Where:** `LICENSE.md` §1 item 8.

**What is wrong.** A reader of the licence does not know what an "Explore atlas" is; "guides" is ambiguous (F2).

**Proposed wording.** "... the recordings of runs, the posters, the atlases of precomputed points (Explore and lab
work), the worksheets and the texts of guided steps ..." (or the definition proposed in F2).

### F21 — nit [neutral]. Small cross-reference and attribution-form inconsistencies in `PUBLICATIONS.md`

**Where:** `PUBLICATIONS.md` §1 last sentence; §3 item 2; §5.

**What is wrong.** §1: "The attribution line of section 5" — in a file that cites `LICENSE.md` §5 for citation two
paragraphs below, "section 5" reads as the licence's §5. §3 item 2 requires "© Ildar Idrisov, lfphys <version>" while
`LICENSE.md` §6.3 and `PUBLICATIONS.md` §5 use "Ildar Idrisov, lfphys <version>" (no ©). A teacher reproducing a poster
has no "<version>" to put.

**Proposed wording.** §1: "The attribution line of section 5 below (`LICENSE.md` §5A) is ...". Use one form, e.g.
"© Ildar Idrisov, lfphys <version or date>", in §3 item 2, §5 and `LICENSE.md` §6.3.

### F22 — nit [useful]. "Teaching that is not published": say where a course platform stands

**Where:** `LICENSE.md` §5A item 5.

**What is wrong.** A course page on a learning platform (Moodle, Google Classroom) or a recorded lecture visible only to
enrolled students is the typical case; "not published" is undefined.

**Proposed wording.** "In teaching that is not published, such as a lesson, a lecture or a course for its own students
— including material on a platform open only to those students — ...".

### F23 — nit [useful]. Tell teachers and video authors where the commercial line runs

**Where:** `LICENSE.md` §1 item 4/5, or `PUBLICATIONS.md` §5 / README.

**What is wrong.** The two questions a teacher or science communicator will ask first are not answered: is a video on a
monetised channel, or a handout at a fee-charging tutoring business, Commercial Use? By §1 item 4.1/4.3 the answer is
"yes" for a business and probably "yes" for monetisation ("in support of a commercial activity"), but nothing says so.

**Proposed wording.** `PUBLICATIONS.md` §5 (explanatory): "Using lfphys or its images in a video or a channel that
earns advertising or sponsorship income, or in teaching by a business (a paid tutoring company, a commercial course
provider), is commercial use and needs an agreement (`LICENSE.md` §1, item 4)." If the owner wants monetised
popular-science videos allowed, that needs a sentence in §1 item 5 instead.

### F24 — nit [neutral]. `NOTICE` attribution paragraph: publications and the CC basis

**Where:** `NOTICE` ×3, paragraphs "Attribution" and "Documentation ...".

**What is wrong.** "any public use ... must carry this line" without the publication exception of §5A.4, and it cites
§5A for the site's materials (F1).

**Proposed wording.** Append to the Attribution paragraph: "In a publication of results, the citation of LICENSE.md
section 5 takes its place." Site materials: as in F1.

### F25 — nit [neutral]. Remaining places with the old summary

**Where:** `lfphys/README.md` "Licence, citation, contact"; `lfphys/LAYERS.md` §4; `AGENTS.md` table row of licence files;
`STATUS.md` V20.

**What is wrong.** They are still correct but incomplete: no line, no name clause, no site materials, no date of the
text. V20's lawyer checklist does not yet list the new questions.

**Proposed wording.** In each summary add: "public use carries the line `lfphys — Ildar Idrisov —
https://github.com/ildar-idrisov/lfphys` (`LICENSE.md` §5A); the name is not licensed; the site's materials are under
CC BY-NC-SA 4.0". V20, add to the lawyer's list: "§5A — the line as a condition on Images of Runs that may carry no
copyright of the Licensor (contract under the Acceptance clause), the name clause without a registered mark (passing
off in Cyprus), the interplay of §5A and §9 with CC BY-NC-SA 4.0 §§3, 6, 7(b); the in-place amendment of 14 November
under one SPDX identifier".

---

## RU wording nit (folded into F12)

«название своего продукта, сервиса, курса или сайта по имени lfphys» is not idiomatic Russian; F12 gives «называть
именем lfphys свой продукт, сервис, курс или сайт».

## Note for the integrator (not a finding)

The brief cites CC "§2(a)(5)(B)" for "no additional restrictions". In CC BY-NC-SA 4.0 (`LICENSE-DOCS.txt` l. 200) that
clause is **§2(a)(5)(C)**; (B) is the "Additional offer from the Licensor — Adapted Material". (B) is the numbering of
CC BY 4.0. No repository file cites the clause, so nothing to fix, but the response should cite (C).

---

## Checked and found fine

- Copies: `LICENSE.md`, `PUBLICATIONS.md`, `COMMERCIAL.md` are byte-identical in root, `lfphys/`, `visualizations/`;
  `NOTICE` and `CITATION.cff` differ only in the part's title, abstract, keywords and third-party line, as before.
- The attribution line and the site address are spelled identically in `LICENSE.md`, `NOTICE`, `PUBLICATIONS.md`,
  `CITATION.cff` and both READMEs.
- Owner's request coverage: noncommercial only, teaching/academic/research allowed, citation obligatory, commercial
  use forbidden, results at the user's own risk (§8 unchanged) — all present; nothing of 1.0's §§2–4, 7, 8, 11 was
  removed or changed.
- §1 item 5 (what is not commercial) and §1 item 4 (Commercial Use) are untouched and still consistent with §4.1.1.
- §5A item 6 (`NOTICE` meets the line on distribution and hosting): consistent with §4.1.2 and §4.3; all three `NOTICE`
  copies carry the line.
- §5A item 2 (placement "reasonable for the medium") matches CC §3(a)(2) in spirit and is practical for slides,
  videos, web pages and print.
- §5A item 7 and the new sentence of §6.1: the line is correctly separated from authorship, ownership and endorsement
  (apart from the Site Materials point in F1).
- §10's cure now names the attribution line and "the line added to the material" as a remedy; the Commercial Use
  carve-out from the cure is kept.
- Cross-references in the amended text point to existing items (§1 items 7–9, §5A items 1–8, item 6.1, item 6.3,
  item 4.3, item 11.2); none dangles.
- `COMMERCIAL.md`: the code/documentation split is kept and correctly extended to the site's materials; it does not
  overstate the CC NonCommercial test.
- `CITATION.cff` ×3 message: consistent with §5 and §5A; valid YAML per the drafter's check (not re-run here).
- The choice to amend 1.0 in place: defensible with 0 forks and two days of publication, provided the earlier text
  stays identifiable (F18) and the CLA reference is made exact (F16).
- Governing law, jurisdiction, warranty and liability clauses: unchanged; the amendment adds nothing that interacts
  with Rome I art. 6 or Law 112(I)/2021 beyond what V20 already lists.
