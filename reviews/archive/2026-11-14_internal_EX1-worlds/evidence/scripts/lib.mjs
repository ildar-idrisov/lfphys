// helpers: a static server for the built site under /lfphys/ (inside the container's network namespace), logging
import http from "node:http";
import { readFile, stat } from "node:fs/promises";
import { extname, join, normalize } from "node:path";
const TYPES = { ".html": "text/html; charset=utf-8", ".js": "text/javascript", ".mjs": "text/javascript", ".css": "text/css",
  ".json": "application/json", ".gz": "application/gzip", ".png": "image/png", ".jpg": "image/jpeg", ".svg": "image/svg+xml", ".txt": "text/plain", ".md": "text/plain" };
export function startStatic(root = "/site", port = 8090, base = "/lfphys/") {
  const srv = http.createServer(async (req, res) => {
    const u = new URL(req.url, "http://x");
    if (!u.pathname.startsWith(base)) { res.writeHead(404); res.end("outside base: " + u.pathname); return; }
    let p = normalize(join(root, decodeURIComponent(u.pathname.slice(base.length))));
    try { const s = await stat(p); if (s.isDirectory()) p = join(p, "index.html"); } catch (e) { /* 404 below */ }
    try { const b = await readFile(p); res.writeHead(200, { "content-type": TYPES[extname(p)] || "application/octet-stream" }); res.end(b); }
    catch (e) { try { const b = await readFile(join(root, "404.html")); res.writeHead(404, { "content-type": "text/html" }); res.end(b); } catch (e2) { res.writeHead(404); res.end(); } }
  });
  return new Promise((r) => srv.listen(port, "127.0.0.1", () => r(srv)));
}
export const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
export const SRV = "http://127.0.0.1:8479";
export const SITE = "http://127.0.0.1:8090/lfphys";
export function watchErrors(page, errs) {
  page.on("pageerror", (e) => errs.push("pageerror: " + e.message));
  page.on("console", (m) => { if (m.type() === "error") errs.push("console: " + m.text().slice(0, 300)); });
  page.on("requestfailed", (r) => errs.push("reqfail: " + r.url()));
}
import { chromium as _ch } from "playwright";
export async function launch() {  // Chromium sometimes dies with SIGSEGV at start on this host: retry
  for (let i = 0; ; i++) { try { return await _ch.launch(); } catch (e) { if (i >= 4) throw e; await sleep(1500); } }
}
