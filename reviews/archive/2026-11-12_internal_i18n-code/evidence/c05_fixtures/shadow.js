import { t, fmt } from "/static/js/i18n.js";
// each case below hides the translator t in its scope; the expected verdict is "shadowed" for every one
export function a1(meta) { let x, t; t = meta.t; return t("Run"); }              // case 1: later in a list, no "="
export function a2(meta, cb = make(), t) { return t("Run"); }                   // case 2: parens in a default value
export function t2() {}                                                          // (control)
function t() { return 0; }                                                       // case 3: a function declaration named t
export const a4 = { draw(meta, opts = f(1), t) { return t("Run"); } };          // case 4: method with a call in defaults
export function a5(rows) { for (const { t } of rows) return t("Run"); }         // case 5: destructured loop variable
export function a6(meta) { const tt = 1, t = 2; return t; }                     // control: should be caught (has "=")
