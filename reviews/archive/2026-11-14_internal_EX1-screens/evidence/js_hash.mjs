// the same with the player's api.js (readStream -> decode -> dequantize)
import { readFileSync, readdirSync, statSync, writeFileSync, existsSync } from "node:fs";
import { createHash } from "node:crypto";
import { join, relative } from "node:path";
const { readStream } = await import("/lf/visualizations/player/js/api.js");
const root = process.argv[2];
const files = [];
for (const w of readdirSync(root)) {
  const wd = join(root, w); if (!statSync(wd).isDirectory()) continue;
  for (const f of readdirSync(wd)) if (f.endsWith(".lfrec.gz")) files.push(join(wd, f));
  const ad = join(wd, "atlas");
  if (existsSync(ad)) for (const a of readdirSync(ad)) for (const f of readdirSync(join(ad, a))) if (f.endsWith(".lfpt.gz")) files.push(join(ad, a, f));
}
const out = {}; let nq = 0;
for (const f of files.sort()) {
  const msgs = await readStream(new Uint8Array(readFileSync(f)));
  msgs.forEach((m, k) => {
    for (const d of m.meta.blobs || []) if (d.q) {
      const a = m.blobs[d.name];
      if (!(a instanceof Float32Array)) throw new Error("not f32");
      out[`${relative(root, f)}|${k}|${d.name}`] = createHash("sha256").update(Buffer.from(a.buffer, a.byteOffset, a.byteLength)).digest("hex").slice(0, 16);
      nq++;
    }
  });
}
writeFileSync(process.argv[3], JSON.stringify(out));
console.log(files.length, "files", nq, "quantised blobs");
