// The player's renderer: integers without a format, plural selection on a value that is displayed rounded
import { t, setCatalogue, fmt } from "/w/visualizations/player/js/i18n.js";
import fs from "node:fs";
const ru = JSON.parse(fs.readFileSync("/w/visualizations/p03_molecules/locales/ru.json", "utf8"));
setCatalogue("en", {});
const ev = { $t: "{n} atoms, {e} events", a: { n: 400, e: 12345678 } };
console.log("en p03 cost note, 12 345 678 events:", t(ev));
console.log("en {n} with n = 1234567:", t({ $t: "{n} coordinates", a: { n: 1234567 } }));
setCatalogue("ru", ru);
console.log("ru p03 cost note:", t(ev));
setCatalogue("ru", { "{n:d} days": { one: "{n:d} день", few: "{n:d} дня", many: "{n:d} дней", other: "{n:d} дня" } });
for (const n of [4.6, 21.4, 1.0004]) console.log(`ru {n:d} days, n = ${n}:`, t({ $t: "{n:d} days", a: { n } }));
