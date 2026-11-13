import { t } from "/static/js/i18n.js";
const LABELS = ["First untranslated label", "Second untranslated label"];
export const a = t(LABELS[0]);
export const b = t(cond ? "Ternary untranslated A" : "Ternary untranslated B");
export const c = t(`Template ${x} untranslated`);
