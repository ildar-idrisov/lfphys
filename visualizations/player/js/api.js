// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// REST + WebSocket client of the lfphys visualization server, and the message decoder.
// Message layout (server/lfviz/protocol.py): u32 json_len | json | pad to 8 | blobs (each 8-aligned).
import { t } from "./i18n.js";

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

export async function getJSON(url) {
  const r = await fetch(url);
  const j = await r.json();
  if (!r.ok) throw apiError(j, r.statusText);
  return j;
}

export async function postJSON(url, body, method = "POST") {
  const r = await fetch(url, { method, headers: { "Content-Type": "application/json" },
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
    ws = new WebSocket(`${proto}://${location.host}/ws/runs/${encodeURIComponent(id)}`);
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
