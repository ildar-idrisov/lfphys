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

Quantised blobs (design ``lfphys/sources/explore_2026-11-14_design.md`` §1.3; the atlases' points and recordings with a
``quantize`` map). A blob's descriptor may carry ``q``; the blob is then stored as unsigned integers and every decoder
(``decode`` here, ``player/js/api.js decode``) returns floats::

    descriptor  {"name", "dtype": "u1" | "u2", "shape", "offset", "nbytes",
                 "q": {"enc": "lin" | "sqrt", "lo": L, "hi": H[, "nan": true]}}
    M           255 for "u1", 65535 for "u2"
    top         M - 1 when "nan" is true (the code M then means NaN), else M
    L, H        JSON numbers (finite), or arrays of numbers of length shape[-1]: one range per column of the last
                axis (element k of the row-major data belongs to column k % shape[-1])
    decoding    v = the stored unsigned integer; when nan and v == M: NaN; else, in IEEE double,
                    r = v / top
                    lin:  x = L + r * (H - L)      (H - L evaluated first, then r * that, then L + that)
                    sqrt: x = H * (r * r)          (L is 0 and unused)
                then x is rounded to float32 (round to nearest, ties to even): the result is a float32 array of the
                blob's shape (a Float32Array in the browser), equal bit for bit in Python and in JavaScript
    encoding    (``quantize``; only the packers encode) lin: v = rint((x - L) / (H - L) * top), sqrt: v =
                rint(sqrt(x / H) * top), clipped to [0, top]; L ≤ min, H ≥ max of the finite values (per column for a
                per-column range), widened to a short decimal form (at most 2·10⁻³ of the span); sqrt: L = 0, negative
                values clipped to 0; H == L gives v = 0 everywhere, which decodes to L (lin) or 0 (sqrt)

``QUANT_ENCODINGS`` names the encodings a ``quantize`` map may ask for (``u16``, ``u8``, ``u8sqrt``, ``u16sqrt``, each
optionally with ``:col`` — one range per column of the last axis — or ``:all`` — one range; without a suffix a 2-D
blob with at most ``COL_MAX`` columns, a table of samples, gets one range per column, anything else one range).
Nothing else in the format changes; a decoder that ignores ``q`` would see the raw integers.

Pooled blobs (design ``lfphys/sources/explore_EX2_2026-11-18_design.md`` §5 F10; an atlas's points, never a live point or
a recording). A blob that two or more points of an atlas store with the same bytes is kept once in the atlas's pool, one
message ``{"type": "pool"}`` whose blobs are named by their ``pool_id`` (the first 16 hex digits of the sha256 of the
blob's descriptor ``{dtype, shape, q?}`` as compact sorted JSON, a newline, and its stored bytes); a point's message names
it by a descriptor without data::

    descriptor  {"name", "pool": "<16 hex>"}

``decode(buf, pool=...)`` resolves it from ``read_pool`` of the pool's message (the descriptor in the decoded ``meta``
gains the pool's ``dtype``, ``shape``, ``nbytes`` and ``q``); a reader without the pool refuses such a message
(``KeyError``).
``encode`` writes a ``PoolRef`` blob as such a descriptor.
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


# --- quantised blobs (design §1.3; the layout is in the module's docstring) -----------------------------------------
#: the encodings a ``quantize`` map may ask for: name -> (stored dtype, enc)
QUANT_ENCODINGS = {"u16": ("u2", "lin"), "u8": ("u1", "lin"), "u8sqrt": ("u1", "sqrt"), "u16sqrt": ("u2", "sqrt")}
QUANT_SUFFIXES = ("", ":col", ":all")
#: a 2-D blob with at most this many columns (a table of samples: t, x, y, vx, vy, ax, ay, W) gets one range per
#: column unless its encoding says ":all"
COL_MAX = 8
_QMAX = {"u1": 255, "u2": 65535}


def quant_encoding_ok(name) -> bool:
    """Whether ``name`` is an encoding of a ``quantize`` map (``u16``, ``u8sqrt:col``, …)."""
    if not isinstance(name, str):
        return False
    base, _, suf = name.partition(":")
    return base in QUANT_ENCODINGS and (":" + suf if suf else "") in QUANT_SUFFIXES


class Quantized:
    """A blob stored quantised: its codes (``u1``/``u2``) and its ``q`` descriptor (see the module's docstring).
    ``encode`` writes it as such; ``max_err`` is the largest absolute error of the decoded values against the source
    (per column for a per-column range), ``span`` the range's width (H - L) per column."""

    __slots__ = ("codes", "q", "max_err", "span")

    def __init__(self, codes: np.ndarray, q: dict, max_err=None, span=None):
        self.codes, self.q, self.max_err, self.span = codes, q, max_err, span


def _num_list(a):
    return [float(x) for x in np.asarray(a, dtype=np.float64).ravel()]


def quantize(arr, encoding: str) -> "Quantized | np.ndarray":
    """Quantise an array by an encoding of ``QUANT_ENCODINGS`` (with ``:col`` / ``:all``). An integer array that
    already fits the stored type (``u1`` into u8, ``u1``/``u2``/``i1`` … that fit) is returned unchanged: nothing would be
    gained or lost. NaN values make the code M mean NaN (``nan: true``); ±inf is refused (ValueError): it would decode as NaN."""
    if not quant_encoding_ok(encoding):
        raise ValueError(f"unknown quantisation {encoding!r}: one of {sorted(QUANT_ENCODINGS)} [':col' | ':all']")
    base, _, suf = encoding.partition(":")
    code, enc = QUANT_ENCODINGS[base]
    arr = np.asarray(arr)
    if arr.dtype.kind in "ui" and arr.size and _QMAX[code] >= int(arr.max()) and int(arr.min()) >= 0 \
            and arr.dtype.itemsize <= np.dtype(_DTYPES[code]).itemsize:
        return arr  # lossless already: an integer blob that fits (flags)
    x = arr.astype(np.float64)
    if np.isinf(x).any():  # ±inf would decode as NaN, an error no max_err could state (review R-F F9)
        raise ValueError(f"a blob with ±inf values cannot be quantised ({int(np.isinf(x).sum())} of {x.size}): "
                         f"leave it unquantised, or send NaN for a missing value")
    percol = (suf == "col") or (suf == "" and x.ndim == 2 and 0 < x.shape[-1] <= COL_MAX)
    if suf == "col" and x.ndim < 2:
        percol = False
    finite = np.isfinite(x)
    has_nan = not bool(finite.all())
    M = _QMAX[code]
    top = M - 1 if has_nan else M
    axis = tuple(range(x.ndim - 1)) if percol else None
    big = np.where(finite, x, np.nan)
    with np.errstate(all="ignore"):
        if x.size and finite.any():
            import warnings  # noqa: PLC0415
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)  # an all-NaN column
                lo = np.nanmin(big, axis=axis)
                hi = np.nanmax(big, axis=axis)
            lo = np.where(np.isfinite(lo), lo, 0.0)
            hi = np.where(np.isfinite(hi), hi, 0.0)
        else:
            lo = np.zeros(x.shape[-1]) if percol else np.float64(0.0)
            hi = lo.copy() if percol else np.float64(0.0)
        lo, hi = _short_range(lo, hi)
        if enc == "sqrt":
            lo = np.zeros_like(lo)
            hi = np.maximum(hi, 0.0)
            ratio = np.where(hi > 0, np.clip(np.where(finite, x, 0.0), 0.0, None) / np.where(hi > 0, hi, 1.0), 0.0)
            v = np.rint(np.sqrt(ratio) * top)
        else:
            span = hi - lo
            v = np.where(span > 0, np.rint((np.where(finite, x, lo) - lo) / np.where(span > 0, span, 1.0) * top), 0.0)
        v = np.clip(v, 0, top)
    codes = v.astype(_DTYPES[code])
    if has_nan:
        codes[~finite] = M
    q = {"enc": enc, "lo": _num_list(lo) if percol else float(lo), "hi": _num_list(hi) if percol else float(hi)}
    if has_nan:
        q["nan"] = True
    dec = dequantize(codes, code, q).astype(np.float64)
    err = np.where(finite, np.abs(dec - np.where(finite, x, 0.0)), 0.0)
    if percol:
        max_err = _num_list(err.max(axis=axis)) if err.size else [0.0] * x.shape[-1]
    else:
        max_err = float(err.max()) if err.size else 0.0
    span = (np.asarray(hi) - np.asarray(lo))
    return Quantized(codes, q, max_err, _num_list(span) if percol else float(span))


#: ``_short_range`` widens a range only when its step ``q`` is at least this many ulps of the range's largest magnitude;
#: a narrower range (a nearly constant column: a conserved quantity, two detections at "the same" time) is kept exact,
#: as a zero span is (review R-F F3: the widening loop never ended when ``q`` was below an ulp)
SHORT_MIN_ULPS = 64


def _short(x: float, q: float, up: bool) -> float:
    """``x`` moved outward to a multiple of ``q`` (a power of ten), as a float with a short decimal form; ``x`` itself
    when that takes more than a few steps (the caller keeps ``q`` well above an ulp, so it never does)."""
    nd = max(0, -int(math.floor(math.log10(q))))
    v = (math.ceil(x / q) if up else math.floor(x / q)) * q
    v = round(v, nd)
    for _ in range(4):
        if not ((v < x) if up else (v > x)):  # outward (or equal): done
            return v
        v = round(v + (q if up else -q), nd)  # a rounding that went inward
    return v if ((v >= x) if up else (v <= x)) else x


def _short_range(lo, hi):
    """The range widened to 4–5 significant digits of its span, so that it is written in a few characters (the JSON of a
    small chunk's ranges would otherwise outweigh its data); a range of zero width, or one whose step would be below
    ``SHORT_MIN_ULPS`` ulps of its values, is kept exact. The widening is at most 2·10⁻³ of the span: the resolution
    changes by as much, the decoding stays exact for the written range."""
    lo = np.array(lo, dtype=np.float64, copy=True)
    hi = np.array(hi, dtype=np.float64, copy=True)
    flo, fhi = lo.reshape(-1), hi.reshape(-1)
    for k in range(flo.size):
        span = fhi[k] - flo[k]
        if span > 0 and math.isfinite(span):
            q = 10.0 ** (math.floor(math.log10(span)) - 3)
            if q < SHORT_MIN_ULPS * math.ulp(max(abs(float(flo[k])), abs(float(fhi[k])))):
                continue  # too narrow for a short decimal form: exact
            a, b = _short(float(flo[k]), q, False), _short(float(fhi[k]), q, True)
            if a <= flo[k] and b >= fhi[k] and (b - a) <= span * (1 + 4e-3):  # a sanity bound: never wide
                flo[k], fhi[k] = a, b
    return lo, hi


def dequantize(codes: np.ndarray, dtype_code: str, q: dict) -> np.ndarray:
    """The float32 values of a quantised blob (the module's docstring): exactly what ``player/js/api.js`` computes."""
    M = _QMAX[dtype_code]
    nan = bool(q.get("nan"))
    top = float(M - 1 if nan else M)
    v = np.asarray(codes).astype(np.float64)
    r = v / top
    lo = np.asarray(q.get("lo", 0.0), dtype=np.float64)
    hi = np.asarray(q["hi"], dtype=np.float64)
    if q["enc"] == "sqrt":
        x = hi * (r * r)
    elif q["enc"] == "lin":
        x = lo + r * (hi - lo)
    else:
        raise ValueError(f"unknown quantised encoding {q['enc']!r}")
    out = x.astype(np.float32)
    if nan:
        out[np.asarray(codes) == M] = np.nan
    return out


class PoolRef:
    """A blob kept in an atlas's pool (the module's docstring, «Pooled blobs»): ``encode`` writes ``{"name", "pool":
    id}`` and no data."""

    def __init__(self, pool_id: str):
        self.pool_id = str(pool_id)

    def __eq__(self, other):
        return isinstance(other, PoolRef) and other.pool_id == self.pool_id

    def __hash__(self):
        return hash(("PoolRef", self.pool_id))


def stored(arr) -> tuple[dict, bytes]:
    """A blob as ``encode`` stores it: its descriptor's ``{dtype, shape, q?}`` and its bytes (a ``Quantized`` as its
    codes)."""
    q = None
    if isinstance(arr, Quantized):
        arr, q = arr.codes, arr.q
    arr = np.asarray(arr)
    code = _code(arr.dtype)
    arr = np.ascontiguousarray(arr, dtype=_DTYPES[code])
    d = {"dtype": code, "shape": list(arr.shape)}
    if q is not None:
        d["q"] = clean(q)
    return d, arr.tobytes()


def pool_id(arr) -> str:
    """A blob's name in an atlas's pool: the first 16 hex digits of sha256(its descriptor as compact sorted JSON, a
    newline, its stored bytes)."""
    import hashlib  # noqa: PLC0415
    d, raw = stored(arr)
    head = json.dumps(d, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(head + b"\n" + raw).hexdigest()[:16]


def read_pool(buf: bytes) -> dict:
    """An atlas's pool from its message: ``{pool id: (stored array, descriptor)}`` (the arrays as stored: codes for a
    quantised blob)."""
    meta, blobs = decode(buf, raw=True)
    by_name = {d["name"]: d for d in meta.get("blobs", [])}
    return {k: (v, by_name[k]) for k, v in blobs.items()}


def encode(meta: dict, blobs: dict[str, np.ndarray] | None = None) -> bytes:
    """Encode one message. A blob may be a ``Quantized`` (its codes are stored, its ``q`` goes into the descriptor) or
    a ``PoolRef`` (only its descriptor ``{name, pool}``: the blob is in the atlas's pool)."""
    descr = []
    chunks = []
    offset = 0
    for name, arr in (blobs or {}).items():
        if isinstance(arr, PoolRef):
            descr.append({"name": name, "pool": arr.pool_id})
            continue
        q = None
        if isinstance(arr, Quantized):
            arr, q = arr.codes, arr.q
        arr = np.asarray(arr)
        code = _code(arr.dtype)
        arr = np.ascontiguousarray(arr, dtype=_DTYPES[code])
        raw = arr.tobytes()
        pad = (-len(raw)) % ALIGN
        descr.append({"name": name, "dtype": code, "shape": list(arr.shape), "offset": offset, "nbytes": len(raw)})
        if q is not None:
            if code not in _QMAX:
                raise TypeError(f"a quantised blob is stored as u1 or u2, not {code}")
            descr[-1]["q"] = q
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


def decode(buf: bytes, raw: bool = False, pool: dict | None = None) -> tuple[dict, dict[str, np.ndarray]]:
    """Decode one message (inverse of ``encode``). A quantised blob (``q`` in its descriptor) comes back as float32
    values (``dequantize``), or as its stored codes with ``raw``. A pooled blob (``{"name", "pool"}``) is taken from
    ``pool`` (``read_pool``), its descriptor in ``meta`` replaced by the pool's (KeyError without the pool)."""
    (jlen,) = struct.unpack_from("<I", buf, 0)
    meta = json.loads(bytes(buf[4 : 4 + jlen]).decode("utf-8"), object_hook=json_hook)
    base = 4 + jlen
    base += (-base) % ALIGN
    blobs = {}
    for i, d in enumerate(meta.get("blobs", [])):
        if "pool" in d:
            if pool is None or d["pool"] not in pool:
                raise KeyError(f"the blob {d.get('name')!r} is in the atlas's pool ({d['pool']}), which was not given")
            arr, pd = pool[d["pool"]]
            meta["blobs"][i] = {"name": d["name"], "pool": d["pool"],
                                **{k: v for k, v in pd.items() if k in ("dtype", "shape", "nbytes", "q")}}
            if pd.get("q") is not None and not raw:
                arr = dequantize(arr, pd["dtype"], pd["q"])
            blobs[d["name"]] = arr
            continue
        dt = _DTYPES[d["dtype"]]
        start = base + d["offset"]
        arr = np.frombuffer(buf, dtype=dt, count=d["nbytes"] // dt.itemsize, offset=start).reshape(d["shape"])
        if d.get("q") is not None and not raw:
            arr = dequantize(arr, d["dtype"], d["q"])
        blobs[d["name"]] = arr
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
