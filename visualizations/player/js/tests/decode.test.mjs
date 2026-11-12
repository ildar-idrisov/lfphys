// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// The message layout lives in two implementations (server/lfviz/protocol.py and player/js/api.js); this test reads
// bytes written by the Python codec (tests/make_js_fixture.py). Run: node --test player/js/tests/
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { decode } from "../api.js";

test("decode a message written by the Python codec", () => {
  const b = readFileSync(new URL("./fixtures/message.bin", import.meta.url));
  const buf = b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength);
  const { meta, blobs } = decode(buf);
  assert.equal(meta.type, "probe");
  assert.equal(meta.text, "кириллица ✓");  // UTF-8 across the two codecs, i18n-ok
  assert.equal(meta.v, null);  // non-finite floats become null
  assert.deepEqual(Array.from(blobs.f8), [1.5, -2.25, 1e300]);
  assert.deepEqual(Array.from(blobs.u1), [1, 2, 3]);
  assert.deepEqual(Array.from(blobs.f4), [0.5, 1, 2, 3, 4, 5]);
  assert.deepEqual(Array.from(blobs.i4), [-7, 8]);
});
