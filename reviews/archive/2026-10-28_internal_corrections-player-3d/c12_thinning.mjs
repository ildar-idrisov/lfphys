// C1 review, check 12: the player's thinning of a long history (player.js thinFrames, MAX_FRAMES = 20000), copied
// verbatim as logic: frames arrive at 20 per second of recording; after N hours, how dense is the kept history in each
// tenth of it (frames kept per second of recording)? Also: what the server sends on a (re)connection (HISTORY_FRAMES
// = 4000, a uniform stride). Pure logic, no server.
// Run: node c12_thinning.mjs   Output: out/c12_thinning.txt (printed)
const MAX_FRAMES = 20000, FPS = 20;
function thinFrames(F) {  // as player.js (the cursor handling left out)
  const n = F.length; let j = 0;
  for (let i = 0; i < n; i++) if (i % 2 === 0 || i === n - 1) F[j++] = F[i];
  F.length = j;
}
const lines = [];
for (const hours of [0.5, 2, 6]) {
  const F = [], N = Math.round(hours * 3600 * FPS);
  for (let i = 0; i < N; i++) { F.push(i / FPS); if (F.length > MAX_FRAMES) thinFrames(F); }
  const T = N / FPS, dens = [];
  for (let k = 0; k < 10; k++) {
    const a = k * T / 10, b = (k + 1) * T / 10;
    dens.push((F.filter((t) => t >= a && t < b).length / (b - a)).toFixed(2));
  }
  const stride = Math.max(1, Math.ceil(N / 4000));
  lines.push(`${hours} h recorded live (${N} frames): kept ${F.length}; frames per second of recording, by tenths of the history (oldest first): ${dens.join(" ")}; after a reload (server history, uniform stride ${stride}): ${(FPS / stride).toFixed(2)} everywhere`);
}
console.log(lines.join("\n"));
