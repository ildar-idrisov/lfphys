// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// REST + WebSocket client of the lfphys visualization server, the message decoder, and the source of a saved
// recording (the public site and the server's recordings: DESIGN of the start page §4.4, §4.5).
// Message layout (server/lfviz/protocol.py): u32 json_len | json | pad to 8 | blobs (each 8-aligned).
// Paths: MODE, BASE, url() and page() come from base.js; every fetch, href and location of the player uses them.
import { BASE, MODE, page, url } from "./base.js";
import { t } from "./i18n.js";

export { BASE, MODE, page, url };

const DT = { f8: Float64Array, f4: Float32Array, i4: Int32Array, u4: Uint32Array, i2: Int16Array,
             u2: Uint16Array, i1: Int8Array, u1: Uint8Array };
const TD = new TextDecoder();

// An error the server answered with ({error: T or text, text: English, ...}): its message in the viewer's language;
// .body keeps the whole answer (fields, hints, estimates)
export function apiError(j, fallback) {
  const e = new Error(j && j.error !== undefined ? t(j.error) : fallback);
  e.body = j || {};
  e.t = j ? j.error : undefined;
  return e;
}

export function decode(buf) {
  const dv = new DataView(buf);
  const jlen = dv.getUint32(0, true);
  const meta = JSON.parse(TD.decode(new Uint8Array(buf, 4, jlen)));
  let base = 4 + jlen;
  base += (8 - (base % 8)) % 8;
  const blobs = {};
  for (const d of meta.blobs || []) {
    const T = DT[d.dtype];
    blobs[d.name] = new T(buf, base + d.offset, d.nbytes / T.BYTES_PER_ELEMENT);
  }
  return { meta, blobs };
}

export async function getJSON(u) {
  const r = await fetch(u);
  const j = await r.json();
  if (!r.ok) throw apiError(j, r.statusText);
  return j;
}

// The catalogue's data, from the server's API or from the site's static copy of it (the same JSON): the names "viz",
// "viz/<id>", "planned", "recordings" and "health"
export function apiGet(name) {
  name = String(name).replace(/^\/+/, "");
  return getJSON(MODE === "static" ? url(`api/${name}.json`) : url(`api/${name}`));
}

export async function postJSON(u, body, method = "POST") {
  const r = await fetch(u, { method, headers: { "Content-Type": "application/json" },
                               body: body === undefined ? undefined : JSON.stringify(body) });
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw apiError(j, r.statusText);
  return j;
}

// One WebSocket per run; reconnects; every (re)connection starts with the full record ("history"),
// so the caller resets its state on onOpen.
export function connectRun(id, { onOpen, onMessage, onClose }) {
  let ws = null, closedByUs = false, delay = 500;
  function open() {
    const proto = location.protocol === "https:" ? "wss" : "ws";
    ws = new WebSocket(`${proto}://${location.host}${url(`ws/runs/${encodeURIComponent(id)}`)}`);
    ws.binaryType = "arraybuffer";
    ws.onopen = () => { delay = 500; onOpen && onOpen(); };
    ws.onmessage = (e) => {
      if (typeof e.data === "string") {  // the server refused a command: not a message of the record
        const j = JSON.parse(e.data);
        onMessage({ meta: { type: "error", text: j.error || e.data, server: true }, blobs: {} });
        return;
      }
      onMessage(decode(e.data));
    };
    ws.onclose = () => {
      onClose && onClose();
      if (!closedByUs) setTimeout(open, delay = Math.min(delay * 2, 8000));
    };
  }
  open();
  return {
    send(cmd, args = {}) { if (ws && ws.readyState === 1) ws.send(JSON.stringify({ cmd, args })); },
    close() { closedByUs = true; ws && ws.close(); },
  };
}

// A saved recording (DESIGN §4.1, §4.4): an LFVREC1 stream, gzip -9, played with no server. src: its address, or its bytes
// (an ArrayBuffer, a typed array or a Blob: the tests, a local file). The handlers are connectRun's: onOpen() first, then
// onMessage() with history_start {frame_stride}, every message of the file (each copied into its own ArrayBuffer, so
// that its arrays stay 8-aligned as over the WebSocket), and history_end {live: false, resumable: false}: the player's
// state of an ended record. onProgress(loaded, total) follows the download (total from Content-Length, 0 when unknown);
// onError(error) when the file cannot be read (else it is thrown to the console). The file may arrive already inflated
// (a server that sends a .gz with Content-Encoding: gzip): it is recognised by its magic.
const MAGIC = "LFVREC1\n";
export function openRecording(src, { onOpen, onMessage, onClose, onProgress, onError } = {}, { frameStride = 1 } = {}) {
  let closed = false;
  const done = (async () => {
    onOpen && onOpen();
    let bytes;
    if (typeof src === "string") {
      const r = await fetch(src);
      if (!r.ok) throw Object.assign(new Error(`${r.status} ${r.statusText}`), { status: r.status });
      const total = Number(r.headers.get("Content-Length")) || 0;
      const chunks = [];
      let got = 0;
      if (r.body && r.body.getReader) {
        const rd = r.body.getReader();
        for (;;) {
          const { done: end, value } = await rd.read();
          if (end || closed) break;
          chunks.push(value); got += value.byteLength;
          onProgress && onProgress(total ? Math.min(got, total) : got, total);
        }
        bytes = new Uint8Array(got);
        let o = 0;
        for (const c of chunks) { bytes.set(c, o); o += c.byteLength; }
      } else bytes = new Uint8Array(await r.arrayBuffer());
    } else if (typeof Blob !== "undefined" && src instanceof Blob) bytes = new Uint8Array(await src.arrayBuffer());
    else bytes = src instanceof ArrayBuffer ? new Uint8Array(src) : new Uint8Array(src.buffer, src.byteOffset, src.byteLength);
    if (closed) return;
    let buf;
    if (bytes[0] === 0x1f && bytes[1] === 0x8b) {
      const plain = new Blob([bytes]).stream().pipeThrough(new DecompressionStream("gzip"));
      buf = await new Response(plain).arrayBuffer();
    } else buf = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
    if (closed) return;
    if (TD.decode(new Uint8Array(buf, 0, Math.min(8, buf.byteLength))) !== MAGIC) throw new Error("not an lfphys recording (LFVREC1)");
    const dv = new DataView(buf);
    onMessage({ meta: { type: "history_start", frame_stride: Math.max(1, frameStride || 1), recording: true }, blobs: {} });
    let pos = MAGIC.length;
    while (pos + 4 <= buf.byteLength && !closed) {
      const ln = dv.getUint32(pos, true);
      if (pos + 4 + ln > buf.byteLength) break;  // a cut file: what is whole is played
      onMessage(decode(buf.slice(pos + 4, pos + 4 + ln)));
      pos += 4 + ln;
    }
    if (!closed) onMessage({ meta: { type: "history_end", live: false, resumable: false, recording: true }, blobs: {} });
  })().catch((e) => { if (onError) onError(e); else console.error(e); });
  return {
    done,
    send() { /* a recording takes no commands */ },
    close() { closed = true; onClose && onClose(); },
  };
}
