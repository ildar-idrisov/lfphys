// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// The browser checks in either language (RULES.md «Languages and i18n»): the language under test (env LFVIZ_LANG, en by
// default) and the player's own renderer, fetched from the server under test with its catalogue, so that a check can
// say what the page shows ("tr(msgid, args)") and read the record's texts (T objects) as the page reads them.
// Copied next to the checks (the scripts run next to their node_modules: `cp /t/*.mjs /pw/`).
import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { pathToFileURL } from "node:url";

export const LANG = process.env.LFVIZ_LANG || "en";

// the page's address in the language under test
export function inLang(url) { return url + (url.includes("?") ? "&" : "?") + "lang=" + LANG; }

// {t, fmt}: the player's i18n.js with the catalogue of LANG
export async function loadI18n(base) {
  const src = await (await fetch(`${base}/static/js/i18n.js`)).text();
  const dir = mkdtempSync(join(tmpdir(), "lfi18n-"));
  const f = join(dir, "i18n.mjs");
  writeFileSync(f, src);
  const I = await import(pathToFileURL(f).href);
  const j = await (await fetch(`${base}/api/i18n/${LANG}`)).json();
  I.setCatalogue(LANG, j.messages || {});
  return { t: I.t, fmt: I.fmt, isT: I.isT };
}

// a text for a regular expression
export const esc = (s) => String(s).replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

// whether any msgid inside a structure (a T and its arguments) contains `part`
export function hasMsgid(x, part) {
  if (x && typeof x === "object") {
    if (typeof x.$t === "string" && x.$t.includes(part)) return true;
    return Object.values(x).some((v) => hasMsgid(v, part));
  }
  return false;
}
