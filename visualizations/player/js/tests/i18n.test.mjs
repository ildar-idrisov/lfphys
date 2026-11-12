// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// The player's renderer of texts (i18n.js): msgids and T objects, nested texts, plural forms by the language's rules,
// the placeholder formats and the numbers of each language. Run: node --test player/js/tests/*.test.mjs
import { test } from "node:test";
import assert from "node:assert/strict";
import { fmt, setCatalogue, t } from "../i18n.js";

const RU = {  // i18n-ok: a catalogue under test
  "Slit {what}": "Щель {what}", open: "открыта", "{n:d} slits": { one: "{n:d} щель", few: "{n:d} щели", many: "{n:d} щелей", other: "{n:d} щели" },  // i18n-ok
  "{text}. What to change: {hint}": "{text}. Что изменить: {hint}",  // i18n-ok
};

test("English: msgids pass through, numbers with a point, the sign flag, m·10ⁿ", () => {
  setCatalogue("en", {});
  assert.equal(t("Run"), "Run");
  assert.equal(t({ $t: "Slit width {w:.3g} µm", a: { w: 0.123456 } }), "Slit width 0.123 µm");
  assert.equal(fmt(1234567.5), "1,234,570");
  assert.equal(fmt(-0.5, "+.2f"), "−0.50");
  assert.equal(fmt(2, "+d"), "+2");
  assert.equal(fmt(1.5e-7, ".3g"), "1.5·10⁻⁷");
  assert.equal(fmt(12345, ".2e"), "1.23·10⁴");
  assert.equal(t({ $t: "{text}. What to change: {hint}", a: { text: { $t: "Too wide." }, hint: "x" } }), "Too wide. What to change: x");
  assert.equal(t({ $t: "{b:cap}", a: { b: { $t: "out of memory" } } }), "Out of memory");
  assert.equal(t({ $t: "{l:unit}", a: { l: { $t: "Mass, M☉" } } }), "M☉");
  assert.equal(t("No such msgid {x}"), "No such msgid {x}");
});

test("Russian: the catalogue, nested texts, plural forms, decimal comma and narrow spaces", () => {
  setCatalogue("ru", RU);
  assert.equal(t({ $t: "Slit {what}", a: { what: { $t: "open" } } }), "Щель открыта");  // i18n-ok
  assert.deepEqual([1, 3, 5, 21, 1.5].map((n) => t({ $t: "{n:d} slits", a: { n } })),
    ["1 щель", "3 щели", "5 щелей", "21 щель", "2 щели"]);  // i18n-ok: 1.5 is "other", rounded by :d
  assert.equal(fmt(0.5), "0,5");
  assert.equal(fmt(1234567.5), "1 234 570");
  assert.equal(fmt(-1.25, ".2f"), "−1,25");
  assert.equal(fmt(3.5e9, ".2g"), "3,5·10⁹");
  assert.equal(t({ $t: "{text}. What to change: {hint}", a: { text: "a", hint: "b" } }), "a. Что изменить: b");  // i18n-ok
});
