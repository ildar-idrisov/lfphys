// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// The player's renderer of texts (i18n.js): msgids and T objects, nested texts, plural forms by the language's rules,
// the placeholder formats and the numbers of each language. Run: node --test player/js/tests/*.test.mjs
import { test } from "node:test";
import assert from "node:assert/strict";
import { fmt, fmtField, isLegacy, parseNum, setCatalogue, setLegacy, t } from "../i18n.js";

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

test("whole numbers exactly, the plural form of the number as shown, own arguments only (review i18n-code F3, F10, F11)", () => {
  setCatalogue("en", { "{n:d} days": { one: "{n:d} day", other: "{n:d} days" }, "{n:.3g} years": { one: "{n:.3g} year", other: "{n:.3g} years" } });
  assert.equal(fmt(12345678), "12,345,678");
  assert.equal(t("{n} atoms, {e} events", { n: 400, e: 12345678 }), "400 atoms, 12,345,678 events");
  assert.equal(fmt(1234567.5), "1,234,570");  // not a whole number: 6 significant digits
  assert.equal(t("{n:.3g} years", { n: 1.0004 }), "1 year");
  assert.equal(t("{n:d} days", { n: 1.4 }), "1 day");
  assert.equal(t("{constructor}", {}), "{constructor}");
  assert.equal(t("{x}", { x: true }), "true");
  setCatalogue("ru", { "{n:d} days": { one: "{n:d} день", few: "{n:d} дня", many: "{n:d} дней", other: "{n:d} дня" } });  // i18n-ok
  assert.deepEqual([4.6, 21.4].map((n) => t("{n:d} days", { n })), ["5 дней", "21 день"]);  // i18n-ok
  assert.equal(fmt(12345678), "12\u202f345\u202f678");
});

test("number fields: both decimal separators, the language's format, an ambiguous text refused (review i18n-browser F1, F2)", () => {
  setCatalogue("ru", {});
  assert.deepEqual(parseNum("650,5"), { value: 650.5 });
  assert.deepEqual(parseNum("650.5"), { value: 650.5 });
  assert.deepEqual(parseNum("−8,1"), { value: -8.1 });
  assert.deepEqual(parseNum("4\u202f000\u202f000\u202f000"), { value: 4e9 });  // a read-out copied (narrow spaces)
  assert.deepEqual(parseNum("1,5·10⁻⁵"), { value: 1.5e-5 });
  assert.deepEqual(parseNum("1,5e-5"), { value: 1.5e-5 });
  assert.deepEqual(parseNum("1,500"), { value: 1.5 });  // Russian: a comma is decimal
  assert.deepEqual(parseNum(""), { err: "empty" });
  assert.equal(parseNum("1,2,3").err, "nan");
  assert.equal(parseNum("abc").err, "nan");
  assert.deepEqual([fmtField(632.8), fmtField(-8.1), fmtField(4e9), fmtField(1.5e-5), fmtField(7, true)],
    ["632,8", "−8,1", "4\u202f000\u202f000\u202f000", "1,5·10⁻⁵", "7"]);
  for (const v of [632.8, -8.1, 4e9, 1.5e-5, 0.52, 1234.5]) assert.equal(parseNum(fmtField(v)).value, v);
  setCatalogue("en", {});
  assert.deepEqual(parseNum("1,500"), { err: "ambiguous", a: "1500", b: "1.500" });
  assert.deepEqual(parseNum("650,5"), { value: 650.5 });
  assert.deepEqual(parseNum("0,500"), { value: 0.5 });
  assert.deepEqual(parseNum("1,234.5"), { value: 1234.5 });
  assert.deepEqual(parseNum("1.234,5"), { value: 1234.5 });
  assert.deepEqual(parseNum("12,345,678"), { value: 12345678 });
  assert.deepEqual([fmtField(1234.5), fmtField(4e9), fmtField(-0.5)], ["1234.5", "4000000000", "−0.5"]);
  for (const v of [632.8, -8.1, 4e9, 1.5e-5, 1234.5]) assert.equal(parseNum(fmtField(v)).value, v);
});

test("a record made before the translation: its Russian labels in English (review i18n-browser F3)", () => {
  setCatalogue("en", {});
  assert.equal(isLegacy({ title: "Двухщелевой опыт", a: [{ $t: "Run" }] }), true);  // i18n-ok
  assert.equal(isLegacy({ title: { $t: "Run" }, note: "plain English" }), false);
  setLegacy({ Run: "Запуск", "Slit width": "Ширина щели" });  // i18n-ok
  assert.equal(t("Ширина щели"), "Slit width");  // i18n-ok
  assert.equal(t("Ширина щели 0.5 мкм"), "Ширина щели 0.5 мкм");  // i18n-ok: a formatted sentence stays as recorded
});
