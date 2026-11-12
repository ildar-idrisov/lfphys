// Review 2026-10-29, check k03 (node only, no browser): the key frames kept after the cap, with player.js's own rule
// (takeKey, copied below verbatim apart from the snapshot): a key every KEY_EVERY messages; beyond MAX_KEYS, every
// other one is dropped (`j % 2 === 1 || last`). The rule thins the OLD keys again at every overflow while the new ones
// arrive at the full rate, so the spacing at the start of a long record grows as 2^(number of overflows): a step back
// there replays almost as many messages as a rebuild from the record (review C1-12 found the same with the frames).
//   node k03_key_thinning.mjs
import { writeFileSync } from "fs";

const KEY_EVERY = 100, MAX_KEYS = 256;
function run(N) {
  const W = { prefix: 0, keys: [] };
  const takeKey = () => {
    const last = W.keys.length ? W.keys[W.keys.length - 1] : null;
    if (W.prefix - (last ? last.i : 0) < KEY_EVERY || (last && last.i >= W.prefix)) return;
    W.keys.push({ i: W.prefix });
    if (W.keys.length > MAX_KEYS) W.keys = W.keys.filter((k, j) => j % 2 === 1 || j === W.keys.length - 1);
  };
  for (let i = 0; i < N; i++) { W.prefix++; takeKey(); }
  const pos = W.keys.map((k) => k.i);
  const firstKey = pos[0];
  const gaps = pos.map((p, j) => p - (j ? pos[j - 1] : 0));
  // the messages a step back at message m replays: m minus the latest key at or before m
  const replay = (m) => { let k = 0; for (const p of pos) if (p <= m) k = p; return m - k; };
  const at = (f) => replay(Math.floor(f * N));
  return { N, keys: pos.length, first_key_at: firstKey, first_key_at_fraction: +(firstKey / N).toFixed(3), first_gaps: gaps.slice(0, 6), last_gaps: gaps.slice(-4),
           max_gap_first_quarter: Math.max(...gaps.filter((g, j) => pos[j] <= N / 4)),
           replay_at: { "5%": at(0.05), "25%": at(0.25), "50%": at(0.5), "90%": at(0.9) },
           uniform_spacing_would_be: Math.ceil(N / MAX_KEYS) };
}
const out = [];
for (const N of [10000, 30000, 50000, 72000, 100000, 144000, 300000, 1000000]) { const r = run(N); out.push(JSON.stringify(r)); console.log(JSON.stringify(r)); }
writeFileSync("out/k03_key_thinning.txt", out.join("\n") + "\n");
