# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Binary message format shared by the worker, the server, the recording file and the browser.

One message = a JSON object (``meta``) plus zero or more numeric arrays (``blobs``)::

    u32 little-endian  json_len
    json_len bytes     UTF-8 JSON (meta; carries "blobs": [{name, dtype, shape, offset, nbytes}])
    zero padding       up to the next multiple of 8 from the message start
    blob section       arrays back to back, each padded to a multiple of 8

``offset`` is relative to the start of the blob section, so every array starts on an 8-byte boundary of
the message: the browser can view it with a typed array without copying (``player/js/api.js``).

Streams (worker stdout, recording file) prefix every message with its length (u32 little-endian).
The recording file starts with the 8-byte magic ``LFVREC1\\n``.

Non-finite floats are not valid JSON for the browser; ``clean`` maps them to ``None``. Physics code must
not rely on NaN surviving the trip.

A translatable text (``lfviz.i18n.T``) is written as ``{"$t", "a"}`` and read back as a ``T`` (``decode``,
``peek_meta``), so that the server's code that reads a record compares and renders texts, not dicts (review i18n-code
F2).
"""

from __future__ import annotations

import json
import math
import struct
from typing import Any

import numpy as np

from .i18n import json_hook

ALIGN = 8
MAGIC = b"LFVREC1\n"

_DTYPES = {
    "f8": np.dtype("<f8"),
    "f4": np.dtype("<f4"),
    "i4": np.dtype("<i4"),
    "u4": np.dtype("<u4"),
    "i2": np.dtype("<i2"),
    "u2": np.dtype("<u2"),
    "i1": np.dtype("i1"),
    "u1": np.dtype("u1"),
}


def _code(dtype: np.dtype) -> str:
    code = f"{dtype.kind}{dtype.itemsize}"
    if code not in _DTYPES:
        raise TypeError(f"unsupported blob dtype {dtype}")
    return code


def clean(obj: Any) -> Any:
    """Recursively convert numpy scalars/arrays to JSON types and non-finite floats to None."""
    if isinstance(obj, dict):
        return {str(k): clean(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [clean(v) for v in obj]
    if isinstance(obj, (bool, np.bool_)):
        return bool(obj)
    if isinstance(obj, (int, np.integer)):
        return int(obj)
    if isinstance(obj, (float, np.floating)):
        x = float(obj)
        return x if math.isfinite(x) else None
    if isinstance(obj, np.ndarray):
        return clean(obj.tolist())
    return obj


def encode(meta: dict, blobs: dict[str, np.ndarray] | None = None) -> bytes:
    """Encode one message."""
    descr = []
    chunks = []
    offset = 0
    for name, arr in (blobs or {}).items():
        arr = np.asarray(arr)
        code = _code(arr.dtype)
        arr = np.ascontiguousarray(arr, dtype=_DTYPES[code])
        raw = arr.tobytes()
        pad = (-len(raw)) % ALIGN
        descr.append({"name": name, "dtype": code, "shape": list(arr.shape), "offset": offset, "nbytes": len(raw)})
        chunks.append(raw)
        if pad:
            chunks.append(b"\0" * pad)
        offset += len(raw) + pad
    meta = clean(meta)
    if descr:
        meta["blobs"] = descr
    js = json.dumps(meta, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    head = struct.pack("<I", len(js)) + js
    head += b"\0" * ((-len(head)) % ALIGN)
    return head + b"".join(chunks)


def decode(buf: bytes) -> tuple[dict, dict[str, np.ndarray]]:
    """Decode one message (inverse of ``encode``)."""
    (jlen,) = struct.unpack_from("<I", buf, 0)
    meta = json.loads(bytes(buf[4 : 4 + jlen]).decode("utf-8"), object_hook=json_hook)
    base = 4 + jlen
    base += (-base) % ALIGN
    blobs = {}
    for d in meta.get("blobs", []):
        dt = _DTYPES[d["dtype"]]
        start = base + d["offset"]
        arr = np.frombuffer(buf, dtype=dt, count=d["nbytes"] // dt.itemsize, offset=start)
        blobs[d["name"]] = arr.reshape(d["shape"])
    return meta, blobs


def peek_meta(buf: bytes) -> dict:
    """Only the JSON part of a message (cheap: no array views)."""
    (jlen,) = struct.unpack_from("<I", buf, 0)
    return json.loads(bytes(buf[4 : 4 + jlen]).decode("utf-8"), object_hook=json_hook)


def frame_stream_item(msg: bytes) -> bytes:
    """Length-prefixed item for a stream (pipe or recording file)."""
    return struct.pack("<I", len(msg)) + msg


def iter_stream(data: bytes, start: int = 0):
    """Iterate (offset, message) over a length-prefixed stream held in memory."""
    pos = start
    n = len(data)
    while pos + 4 <= n:
        (ln,) = struct.unpack_from("<I", data, pos)
        if pos + 4 + ln > n:
            break
        yield pos, data[pos + 4 : pos + 4 + ln]
        pos += 4 + ln
