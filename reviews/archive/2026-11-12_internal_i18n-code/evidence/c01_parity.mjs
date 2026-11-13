// JS renderer on the same cases (the player's i18n.js, en with en.json overrides)
import fs from "node:fs";
import { t, setCatalogue, fmt } from "/w/visualizations/player/js/i18n.js";
const cases = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const EN = { ...JSON.parse(fs.readFileSync("/w/visualizations/locales/en.json", "utf8")), ...JSON.parse(fs.readFileSync("/w/visualizations/p01_gravity/locales/en.json", "utf8")) };
setCatalogue("en", EN);
const out = {};
for (const [name, x] of cases) { try { out[name] = t(x); } catch (e) { out[name] = "EXC " + e; } }
console.log(JSON.stringify(out, null, 0).replace(/","/g, '",\n"'));
console.log("--- non-JSON values");
for (const v of [NaN, Infinity, -Infinity]) console.log(String(v), "default:", t({ $t: "x = {x}", a: { x: v } }), "| .3g:", t({ $t: "{x:.3g}", a: { x: v } }));
setCatalogue("ru", { "{n:d} days": { one: "{n:d} день", few: "{n:d} дня", many: "{n:d} дней", other: "{n:d} дня" } });
for (const v of [NaN, Infinity, 1e300, 2.5]) console.log("ru plural n=", v, "->", t({ $t: "{n:d} days", a: { n: v } }));
console.log("ru 9999999.7 default:", fmt(9999999.7), "| ru 0.5:", fmt(0.5), "| ru 1e21 d:", fmt(1e21, "d"));
