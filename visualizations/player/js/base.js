// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// Where the player lives (DESIGN of the start page §4.5; the contract between the recorder/site build and the start
// page, 2026-11-13). Every player page carries <meta name="lf-mode" content="server|static"> and
// <meta name="lf-base" content="/">: the server serves them as they are, the site build writes "static" and the site's
// base (such as "/lfphys/"). Every fetch, href and location of the player goes through url() or page(), so that the same
// files work at the server's root and under a sub-path of the public site. Imported by i18n.js (which cannot import
// api.js: api.js imports it, and i18n.js loads its catalogue at the top level); api.js re-exports all of it.
//
//   MODE                 "server" | "static" (the public site: recordings only, no API)
//   BASE                 the base path, ending with "/"
//   url("static/x.js")   BASE + the path without its leading "/"
//   page("run", {rec})   the address of a player page: "/run?rec=…" on the server, "<base>run.html?rec=…" on the site;
//                        page("") and page("index") are the start page; "settings" and "runs" exist on the server only;
//                        page("worksheet", {demo}) is a lab's printable worksheet (design of the screens §2.3)

const doc = typeof document !== "undefined" ? document : null;
const metaOf = (name) => (doc && doc.querySelector(`meta[name="${name}"]`)?.getAttribute("content")) || "";

export const MODE = metaOf("lf-mode") === "static" ? "static" : "server";
export const BASE = (() => { const b = metaOf("lf-base") || "/"; return b.endsWith("/") ? b : b + "/"; })();

export function url(path) { return BASE + String(path || "").replace(/^\/+/, ""); }

// the pages of the player, by name: the server's address and the site's file
const SITE_FILES = { "": "", index: "", run: "run.html", legal: "legal.html", worksheet: "worksheet.html", "404": "404.html" };
export function page(name, query) {
  name = String(name || "").replace(/^\/+/, "");
  let p;
  if (MODE === "static") p = url(name in SITE_FILES ? SITE_FILES[name] : `${name}.html`);
  else p = url(name === "index" ? "" : name);
  let q = "";
  if (query && typeof query === "object") {
    const u = new URLSearchParams();
    for (const [k, v] of Object.entries(query)) if (v !== undefined && v !== null) u.set(k, String(v));
    q = u.toString();
  } else if (typeof query === "string") q = query.replace(/^\?/, "");
  return q ? `${p}?${q}` : p;
}

// the pages a link in the player may lead to, by pathname (for i18n.js: a link's language goes along)
export function isPagePath(pathname) {
  for (const n of ["", "run", "runs", "settings", "legal", "worksheet"]) if (page(n) === pathname) return true;
  return MODE === "static" && pathname === url("index.html");
}

// The links written in a page's HTML name their target as data-page="settings" (their href is the server's, so the page
// also works before this module runs); on the site they are rewritten, and those marked data-server-only are removed.
if (doc) {
  for (const a of doc.querySelectorAll("a[data-page]")) a.setAttribute("href", page(a.dataset.page));
  if (MODE === "static") for (const e of doc.querySelectorAll("[data-server-only]")) e.remove();
}
