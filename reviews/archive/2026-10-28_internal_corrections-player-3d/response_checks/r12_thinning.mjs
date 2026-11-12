// Response to the C1 review, check 12 redone for the processed player: `addFrame` (player.js) copied as logic, the
// cursor handling left out. Frames arrive at 20 per second of recording; after N hours, frames kept per second of
// recording in each tenth of the history (oldest first). Then the same session reloaded half-way: the server replays
// its history with a uniform stride (HISTORY_FRAMES = 4000, `history_start`), and the live frames are added after it.
// Pure logic, no server. Run: node r12_thinning.mjs   Output: printed (out/r12_thinning.txt)
const MAX_FRAMES = 20000, FPS = 20, HISTORY_FRAMES = 4000;
function addFrame(W, f, replaying, histStride) {  // as player.js
  f.n = W.nArrived;
  W.nArrived += replaying ? histStride : 1;
  const F = W.frames;
  if (F.length && F[F.length - 1].n % W.stride !== 0) F.pop();
  F.push(f);
  if (F.length > MAX_FRAMES) {
    W.stride *= 2;
    let j = 0;
    for (let i = 0; i < F.length; i++) if (F[i].n % W.stride === 0 || i === F.length - 1) F[j++] = F[i];
    F.length = j;
  }
}
const density = (F, T) => {
  const out = [];
  for (let k = 0; k < 10; k++) {
    const a = k * T / 10, b = (k + 1) * T / 10;
    out.push((F.filter((f) => f.t >= a && f.t < b).length / (b - a)).toFixed(2));
  }
  return out.join(" ");
};
const lines = [];
for (const hours of [0.5, 2, 6]) {
  const N = Math.round(hours * 3600 * FPS), T = N / FPS;
  const W = { frames: [], nArrived: 0, stride: 1 };
  for (let i = 0; i < N; i++) addFrame(W, { t: i / FPS }, false, 1);
  lines.push(`${hours} h live: kept ${W.frames.length} (stride ${W.stride}); per second of recording by tenths: ${density(W.frames, T)}`);
  // reloaded half-way: the server's uniform history of the first half, then the second half live
  const half = Math.floor(N / 2), stride = Math.max(1, Math.ceil(half / HISTORY_FRAMES));
  const W2 = { frames: [], nArrived: 0, stride };
  for (let i = 0; i < half; i++) if (i % stride === 0 || i === half - 1) addFrame(W2, { t: i / FPS }, true, stride);
  for (let i = half; i < N; i++) addFrame(W2, { t: i / FPS }, false, 1);
  lines.push(`   reloaded half-way (server stride ${stride}): kept ${W2.frames.length} (stride ${W2.stride}); by tenths: ${density(W2.frames, T)}`);
}
console.log(lines.join("\n"));
