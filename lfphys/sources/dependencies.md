# lfphys: dependency licence audit — 2026-10-27 (plan item P12)

Purpose: list every package pinned for the Docker image of the engine and the visualizations
(`../../visualizations/docker/requirements.lock`) with its licence, as declared in the installed package metadata and as
published by the project itself, and decide for each whether the owner's rule allows it (`../../AGENTS.md` §3 rule 8,
`../../CONTRIBUTING.md`, `../LAYERS.md` §4).

Method.
* Installed metadata: read with `importlib.metadata` in an image built from the lock (`python:3.11-slim` +
  `pip install -r requirements.lock`, 2026-10-27): `License-Expression`, then `License`, then the `License ::`
  classifiers, and the licence files the wheel ships (`License-File`, `*.libs/`).
* Project site: the licence file in the project's own repository (GitHub licence API and the file itself) or the
  licence page on the project's site, accessed 2026-10-27. Repository files were read on the default branch; for the
  pinned version the licence files inside the installed wheel are the authoritative copy and were read in the image.
* Categories (`../../CONTRIBUTING.md`): **permissive** (MIT, BSD, Apache-2.0, ISC, PSF, zlib, public domain);
  **weak copyleft** (LGPL, MPL-2.0) used unmodified as a separate library: allowed; **strong copyleft** (GPL, AGPL):
  not allowed at run time; **noncommercial / proprietary**: not allowed, except a vendor **platform runtime** whose
  terms permit commercial use and redistribution (§3); **metadata only**: a package that installs no code.
* `../tests/test_licences.py` checks the installed metadata in the image against the same table and fails when a
  pinned package is missing from it, when a declared licence moves to another category, or when this file and the
  lock disagree (§8).

## 1. Pinned packages

Roles: **runtime** (the engine, the server and the worlds), **runtime-GPU** (only the optional GPU backend; the engine
runs without it), **test tooling** (pytest and its dependencies; not used by the engine or the server).

| package | pinned | role | declared licence (installed metadata) | licence on the project's site | category | allowed |
|---|---|---|---|---|---|---|
| `aiohappyeyeballs` | 2.7.1 | runtime | License: PSF-2.0; classifier: Python Software Foundation License | PSF License Version 2 text ([LICENSE](https://github.com/aio-libs/aiohappyeyeballs/blob/main/LICENSE)) | permissive | yes |
| `aiohttp` | 3.14.5 | runtime | License-Expression: Apache-2.0 AND MIT (MIT: vendored llhttp) | Apache-2.0 ([LICENSE.txt](https://github.com/aio-libs/aiohttp/blob/master/LICENSE.txt)) | permissive | yes |
| `aiosignal` | 1.4.0 | runtime | License: Apache 2.0; classifier: Apache Software License | Apache-2.0 ([LICENSE](https://github.com/aio-libs/aiosignal/blob/master/LICENSE)) | permissive | yes |
| `attrs` | 26.1.0 | runtime | License-Expression: MIT | MIT ([LICENSE](https://github.com/python-attrs/attrs/blob/main/LICENSE)) | permissive | yes |
| `cuda-pathfinder` | 1.8.4 | runtime-GPU | License-Expression: Apache-2.0 | Apache-2.0 ([cuda_pathfinder/LICENSE](https://github.com/NVIDIA/cuda-python/blob/main/cuda_pathfinder/LICENSE), `license = "Apache-2.0"` in its pyproject.toml) | permissive | yes |
| `cuda-toolkit` | 12.9.2.0 | runtime-GPU | none: no License-Expression, License, classifier or licence file; the wheel installs only its `dist-info` | NVIDIA's description of the package (its PyPI README): "a meta-package (a package that contains no software and only installs other packages)"; the toolkit itself is under the CUDA EULA (§3) | metadata only | yes: installs no code (§3.5) |
| `cupy-cuda12x` | 14.2.0 | runtime-GPU | License-Expression: MIT (bundled headers: §2.3) | MIT ([LICENSE](https://github.com/cupy/cupy/blob/main/LICENSE)) | permissive | yes |
| `frozenlist` | 1.8.0 | runtime | License: Apache-2.0 | Apache-2.0 ([LICENSE](https://github.com/aio-libs/frozenlist/blob/master/LICENSE)) | permissive | yes |
| `idna` | 3.20 | runtime | License-Expression: BSD-3-Clause | BSD-3-Clause ([LICENSE.md](https://github.com/kjd/idna/blob/master/LICENSE.md)) | permissive | yes |
| `iniconfig` | 2.3.1 | test tooling | License-Expression: MIT | MIT ([LICENSE](https://github.com/pytest-dev/iniconfig/blob/main/LICENSE)) | permissive | yes |
| `mpmath` | 1.3.0 | runtime | License: BSD; classifier: BSD License | BSD-3-Clause ([LICENSE](https://github.com/mpmath/mpmath/blob/master/LICENSE)) | permissive | yes |
| `multidict` | 7.1.0 | runtime | License-Expression: Apache-2.0 | Apache-2.0 ([LICENSE](https://github.com/aio-libs/multidict/blob/master/LICENSE)) | permissive | yes |
| `numpy` | 2.4.6 | runtime | License-Expression: BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0 (bundled shared libraries: §2.2) | BSD-3-Clause ([LICENSE.txt](https://github.com/numpy/numpy/blob/main/LICENSE.txt)) | permissive | yes |
| `nvidia-cublas-cu12` | 12.9.2.10 | runtime-GPU | License-Expression: LicenseRef-NVIDIA-Proprietary; License.txt = CUDA EULA | CUDA Toolkit EULA ([12.9](https://docs.nvidia.com/cuda/archive/12.9.1/eula/index.html)), §3 | platform runtime | yes: optional (GPU only), commercial use permitted; redistribution conditions §3 |
| `nvidia-cuda-nvrtc-cu12` | 12.9.86 | runtime-GPU | License: LicenseRef-NVIDIA-Proprietary; classifier: Other/Proprietary License; License.txt = CUDA EULA | CUDA Toolkit EULA ([12.9](https://docs.nvidia.com/cuda/archive/12.9.1/eula/index.html)), §3 | platform runtime | yes: optional (GPU only), commercial use permitted; redistribution conditions §3 |
| `nvidia-cuda-runtime-cu12` | 12.9.79 | runtime-GPU | License: LicenseRef-NVIDIA-Proprietary; classifier: Other/Proprietary License; License.txt = CUDA EULA | CUDA Toolkit EULA ([12.9](https://docs.nvidia.com/cuda/archive/12.9.1/eula/index.html)), §3 | platform runtime | yes: optional (GPU only), commercial use permitted; redistribution conditions §3 |
| `nvidia-cufft-cu12` | 11.4.1.4 | runtime-GPU | License: LicenseRef-NVIDIA-Proprietary; classifier: Other/Proprietary License; License.txt = CUDA EULA | CUDA Toolkit EULA ([12.9](https://docs.nvidia.com/cuda/archive/12.9.1/eula/index.html)), §3 | platform runtime | yes: optional (GPU only), commercial use permitted; redistribution conditions §3 |
| `nvidia-curand-cu12` | 10.3.10.19 | runtime-GPU | License: NVIDIA Proprietary Software; classifier: Other/Proprietary License; License.txt = CUDA EULA | CUDA Toolkit EULA ([12.9](https://docs.nvidia.com/cuda/archive/12.9.1/eula/index.html)), §3 | platform runtime | yes: optional (GPU only), commercial use permitted; redistribution conditions §3 |
| `nvidia-cusolver-cu12` | 11.7.5.82 | runtime-GPU | License: LicenseRef-NVIDIA-Proprietary; classifier: Other/Proprietary License; License.txt = CUDA EULA | CUDA Toolkit EULA ([12.9](https://docs.nvidia.com/cuda/archive/12.9.1/eula/index.html)), §3 | platform runtime | yes: optional (GPU only), commercial use permitted; redistribution conditions §3 |
| `nvidia-cusparse-cu12` | 12.5.10.65 | runtime-GPU | License: LicenseRef-NVIDIA-Proprietary; classifier: Other/Proprietary License; License.txt = CUDA EULA | CUDA Toolkit EULA ([12.9](https://docs.nvidia.com/cuda/archive/12.9.1/eula/index.html)), §3 | platform runtime | yes: optional (GPU only), commercial use permitted; redistribution conditions §3 |
| `nvidia-nvjitlink-cu12` | 12.9.86 | runtime-GPU | License: LicenseRef-NVIDIA-Proprietary; classifier: Other/Proprietary License; License.txt = CUDA EULA | CUDA Toolkit EULA ([12.9](https://docs.nvidia.com/cuda/archive/12.9.1/eula/index.html)), §3 | platform runtime | yes: optional (GPU only), commercial use permitted; redistribution conditions §3 |
| `packaging` | 26.3 | test tooling | License-Expression: Apache-2.0 OR BSD-2-Clause | either Apache-2.0 or BSD-2-Clause ([LICENSE](https://github.com/pypa/packaging/blob/main/LICENSE)) | permissive | yes |
| `pluggy` | 1.7.0 | test tooling | License: MIT; classifier: MIT License | MIT ([LICENSE](https://github.com/pytest-dev/pluggy/blob/main/LICENSE)) | permissive | yes |
| `propcache` | 0.5.4 | runtime | License: Apache-2.0 | Apache-2.0 ([LICENSE](https://github.com/aio-libs/propcache/blob/master/LICENSE)) | permissive | yes |
| `Pygments` | 2.21.0 | test tooling | License-Expression: BSD-2-Clause | BSD-2-Clause ([LICENSE](https://github.com/pygments/pygments/blob/master/LICENSE)) | permissive | yes |
| `pytest` | 9.1.1 | test tooling | License-Expression: MIT | MIT ([LICENSE](https://github.com/pytest-dev/pytest/blob/main/LICENSE)) | permissive | yes |
| `python-flint` | 0.9.0 | runtime | License-Expression: MIT AND LGPL-3.0-or-later (MIT: the bindings; LGPL: the bundled FLINT, GMP, MPFR, §2.1) | MIT for the bindings ([LICENSE](https://github.com/flintlib/python-flint/blob/main/LICENSE)); the Linux wheel build adds `LGPL-3.0-or-later` and the GMP/MPFR/FLINT licence files ([pyproject.toml at 0.9.0](https://github.com/flintlib/python-flint/blob/0.9.0/pyproject.toml)) | weak copyleft | yes: unmodified, separately installed shared libraries; conditions on redistribution §4 |
| `scipy` | 1.17.1 | runtime | License: the full BSD-3-Clause text followed by the bundled-library notices (47 559 characters); classifier: BSD License | BSD-3-Clause ([LICENSE.txt](https://github.com/scipy/scipy/blob/main/LICENSE.txt)) | permissive | yes |
| `typing_extensions` | 4.16.0 | runtime | License-Expression: PSF-2.0 | PSF License Version 2 text ([LICENSE](https://github.com/python/typing_extensions/blob/main/LICENSE)) | permissive | yes |
| `yarl` | 1.25.1 | runtime | License: Apache-2.0 | Apache-2.0 ([LICENSE](https://github.com/aio-libs/yarl/blob/master/LICENSE)) | permissive | yes |

Who needs what (unconditional requirements in the image): the server needs `aiohttp` → `aiohappyeyeballs`, `aiosignal`,
`attrs`, `frozenlist`, `multidict`, `propcache`, `typing_extensions`, `yarl` (→ `idna`); the engine needs `numpy`,
`scipy`, `mpmath`, `python-flint` (only `core.certified`, imported lazily); the GPU backend needs `cupy-cuda12x` →
`cuda-pathfinder`, and its `ctk` extra → `cuda-toolkit` → the eight `nvidia-*-cu12` wheels; `pytest` → `iniconfig`,
`packaging`, `pluggy`, `Pygments`.

## 2. Libraries bundled inside the wheels

A wheel can carry compiled third-party libraries whose licences are not in its `License-Expression`. Read in the
image from the wheels' own licence files.

### 2.1 python-flint 0.9.0: FLINT, GMP, MPFR

`python_flint.libs/` holds three shared libraries, loaded only when `lfphys.core.certified` is called (the engine
imports `flint` inside that module's functions; importing every `lfphys` module does not load it, checked in the
image):

| bundled library | file in the wheel | licence files shipped (`dist-info/licenses/python-flint.libs/…`) | licence on the project's site | category |
|---|---|---|---|---|
| FLINT 3.6.0 | `libflint-6839011d.so.24.0.0` | `flint-3.6.0/COPYING` (GPL-3.0 text), `COPYING.LESSER` (LGPL-3.0 text) | "freely available under the GNU Lesser General Public License version 3 or later" ([flintlib.org](https://flintlib.org/); [COPYING](https://github.com/flintlib/flint/blob/main/COPYING)) | weak copyleft (LGPL-3.0-or-later) |
| GMP 6.3.0 | `libgmp-e0c82b6b.so.10.5.0` | `gmp-6.3.0/COPYING` (GPL-3.0 text), `COPYING.LESSERv3` | "the GNU MP library is dual licensed, under the conditions of the GNU Lesser General Public License version 3 … or the GNU General Public License version 2" ([gmplib.org/manual/Copying](https://gmplib.org/manual/Copying)); the wheel takes the LGPL-3.0-or-later option | weak copyleft (LGPL-3.0-or-later OR GPL-2.0-or-later) |
| MPFR 4.2.2 | `libmpfr-be332c05.so.6.2.2` | `mpfr-4.2.2/COPYING` (GPL-3.0 text), `COPYING.LESSER` | "distributed under the GNU Lesser General Public License (GNU Lesser GPL), version 3 or later" ([mpfr.org](https://www.mpfr.org/)) | weak copyleft (LGPL-3.0-or-later) |

The GPL-3.0 texts are shipped because LGPL-3.0 is written as additional permissions on top of GPL-3.0; they do not
make the libraries GPL. The python-flint README (0.9.0 and main) still says "FLINT and Arb are LGPL v2.1+"; that
sentence is out of date (FLINT 3 is LGPL-3.0-or-later, as the wheel metadata and flintlib.org state).

### 2.2 numpy 2.4.6 and scipy 1.17.1: OpenBLAS, LAPACK, GCC runtime

Both wheels list the bundled libraries in their own `LICENSE.txt` (numpy: `dist-info/licenses/LICENSE.txt`; scipy:
the `License` field and `dist-info/LICENSE.txt`):

| bundled library | files | licence as declared in the wheel | category |
|---|---|---|---|
| OpenBLAS | `numpy.libs/libscipy_openblas64_-*.so`, `scipy.libs/libscipy_openblas-*.so` | BSD-3-Clause | permissive |
| LAPACK (inside OpenBLAS) | same | BSD-3-Clause-Open-MPI | permissive |
| GCC runtime (libgfortran) | `*.libs/libgfortran-*.so.5.0.0` | GPL-3.0-or-later WITH GCC-exception-3.1 | allowed: the GCC Runtime Library Exception ([gnu.org](https://www.gnu.org/licenses/gcc-exception-3.1.html)): "You have permission to propagate a work of Target Code formed by combining the Runtime Library with Independent Modules, even if such propagation would otherwise violate the terms of GPLv3 … You may then convey such a combination under terms of your choice" |
| libquadmath | `*.libs/libquadmath-*.so.0.0.0` | LGPL-2.1-or-later | weak copyleft, unmodified shared library |

numpy also declares vendored source under 0BSD, MIT, Zlib and CC0-1.0 (in its `License-Expression`); scipy ships
Qhull (`scipy/spatial/qhull_src/COPYING_QHULL.txt`: free copying, modification and redistribution with notice
conditions; permissive), DOP (`LICENSE_DOP`), pocketfft and uarray (BSD).

### 2.3 cupy-cuda12x 14.2.0: headers and kernels

No compiled third-party library is bundled (every `.so` in the wheel is a CuPy extension module). Third-party source
shipped: CCCL headers (`cupy/_core/include/cupy/_cccl/LICENSE`: Thrust Apache-2.0 with Boost-licensed and
FreeBSD-derived parts, libcu++ Apache-2.0 WITH LLVM-exception, CUB BSD-3-Clause), DLPack (Apache-2.0), Jitify
(BSD-3-Clause, NVIDIA), `cupyx/scipy/ndimage/cuda` (MIT); `docs/source/license.rst` lists the NumPy, SciPy and
cuSignal notices (BSD/MIT). All permissive. CuPy can also use cuTENSOR and NCCL (named in `cupy/.data/_wheel.json`);
neither is installed or pinned: adding one is a new pinned package and needs a row here.

### 2.4 aiohttp 3.14.5

Vendored llhttp (MIT, `dist-info/licenses/vendor/llhttp/LICENSE`), declared in its `License-Expression`.

## 3. NVIDIA CUDA runtime libraries: the licence terms

### 3.1 Which text applies

* Every `nvidia-*-cu12` wheel ships the same `License.txt` (identical MD5 in all eight): NVIDIA's "End User License
  Agreement" for the CUDA Toolkit, with chapter 1 "License Agreement for NVIDIA Software Development Kits" (headed
  "Release Date: July 26, 2018") and chapter 2 "CUDA Toolkit Supplement" ("Release date: August 16, 2018").
* NVIDIA publishes the EULA of each toolkit release: CUDA 12.9 at
  <https://docs.nvidia.com/cuda/archive/12.9.1/eula/index.html> ("v12.9", "Last updated: January 7, 2025"), the
  current one at <https://docs.nvidia.com/cuda/eula/index.html> ("v13.4", "Last updated: January 26, 2026").
  Sections 1 and 2.1–2.5 of the two web versions are word for word the same.
* The wheel's 2018 text has the same §1.1.1, §1.1.2, §1.2 items 1–5, §1.6 and §2.1–2.3 as quoted below, word for
  word. It differs in: §1.1.6 (in 2018 "Third Party Licenses", without the sentence on OSI licences), the wording of
  the critical-applications clause, and Attachment A (shorter list, no clause on file-name variations; §3.4).

### 3.2 What the terms say (quoted from the CUDA 12.9 EULA on NVIDIA's site)

* Grant, §1.1.1: "NVIDIA hereby grants you a non-exclusive, non-transferable license, without the right to sublicense
  (except as expressly provided in this Agreement) to: Install and use the SDK, Modify and create derivative works of
  sample source code delivered in the SDK, and Distribute those portions of the SDK that are identified in this
  Agreement as distributable, as incorporated in object code format into a software application that meets the
  distribution requirements indicated in this Agreement."
* Distribution requirements, §1.1.2: "Your application must have material additional functionality, beyond the
  included portions of the SDK." / "The distributable portions of the SDK shall only be accessed by your
  application." / "The following notice shall be included in modifications and derivative works of sample source
  code distributed: 'This software contains source code provided by NVIDIA Corporation.'" / "Unless a developer tool
  is identified in this Agreement as distributable, it is delivered for your internal use only." / "The terms under
  which you distribute your application must be consistent with the terms of this Agreement, including (without
  limitation) terms relating to the license grant and license restrictions and protection of NVIDIA's intellectual
  property rights. Additionally, you agree that you will protect the privacy, security and legal rights of your
  application users." / "You agree to notify NVIDIA in writing of any known or suspected distribution or use of the
  SDK not in compliance with the requirements of this Agreement, and to enforce the terms of your agreements with
  respect to distributed SDK."
* Open-source licences, §1.1.6 (web texts only): "you may use the SDK to develop and test applications released
  under Open Source Initiative (OSI) approved open source software licenses."
* Limitations, §1.2: "You may not reverse engineer, decompile or disassemble, or remove copyright or other proprietary
  notices from any portion of the SDK or copies of the SDK." / "Except as expressly provided in this Agreement, you
  may not copy, sell, rent, sublicense, transfer, distribute, modify, or create derivative works of any portion of the
  SDK. For clarity, you may not distribute or sublicense the SDK as a stand-alone product." / "You may not use the
  SDK in any manner that would cause it to become subject to an open source software license. As examples, licenses
  that require as a condition of use, modification, and/or distribution that the SDK be: Disclosed or distributed in
  source code form; Licensed for the purpose of making derivative works; or Redistributable at no charge."
* Termination, §1.6: NVIDIA may terminate if "(iii) NVIDIA decides to no longer provide the SDK in a country or, in
  NVIDIA's sole discretion, the continued use of it is no longer commercially viable"; "Your prior distributions in
  accordance with this Agreement are not affected by the termination of this Agreement."
* Supplement: §2.1 "The SDK is licensed for you to develop applications only for use in systems with NVIDIA GPUs."
  §2.2 "The portions of the SDK that are distributable under the Agreement are listed in Attachment A." §2.3 Linux
  portions "may be copied and redistributed for use in accordance with this Agreement, provided that the object code
  files are not modified in any way (except for unzipping of compressed files)." §2.5: questions to NVIDIA's licensing
  address given there.
* Also in §1.2 and §1.7: no use in "Critical Applications" without own responsibility (indemnity), US export rules,
  Delaware law.

### 3.3 Conclusion for the owner's rule

* **Commercial use: permitted.** The grant has no noncommercial or field-of-use limit; the only scope limits are
  "only for use in systems with NVIDIA GPUs" (§2.1) and "purposes that are permitted by (a) this Agreement, and (b)
  any applicable law". What is forbidden is selling or distributing the SDK itself, alone ("as a stand-alone
  product"), not selling an application that uses it.
* **Redistribution: permitted, with conditions**: only the files listed in Attachment A, unmodified, inside an
  application with "material additional functionality", accessed only by that application, under terms consistent
  with the EULA (a downstream licence, including a commercial licence of the engine, must not grant rights over the
  NVIDIA files that the EULA withholds, e.g. reverse engineering), with notices kept, and with the export rules.
* **The engine's own code stays licence-clean.** It contains no NVIDIA code; CuPy loads the libraries at run time,
  only when the GPU backend is selected (`lfphys.core.backend` imports `cupy` inside a function; with CuPy blocked
  every `lfphys` module still imports: `test_licences.py`). The rule's exception therefore applies:
  **platform runtime, optional (GPU only), commercial use permitted**.
* **Simplest compliant distribution:** publish the source and `requirements.lock`, so that users install the NVIDIA
  wheels from PyPI themselves (each user then takes the EULA from NVIDIA directly); the project then redistributes no
  NVIDIA file. Publishing a built image that contains the wheels is redistribution and must meet §1.1.2 and §3.4.
  The image this project builds (`visualizations/docker/Dockerfile`) holds only the environment, the engine being
  mounted at run time (`docker-compose.yml`); it is not an application with "material additional functionality", so
  publishing it would not meet §1.1.2 (review of 2026-10-29, R7). The owner decided on 2026-10-29 to distribute no
  image, only the source with its install files (`../../STATUS.md` V21).
* The libcuda driver library is not in the image; the NVIDIA Container Toolkit maps it in from the host at run time.
* **The owner's decision (2026-10-27, verbatim): «библиотеки CUDA можно использовать».** The platform-runtime category
  of `../../AGENTS.md` §3 rule 8 is confirmed by the owner.

### 3.4 Attachment A against the files the wheels install

Installed files (`site-packages/nvidia/*`): `libcublas.so.12`, `libcublasLt.so.12`, `libnvblas.so.12`,
`libnvrtc.so.12`, `libnvrtc-builtins.so.12.9`, `libnvrtc.alt.so.12`, `libnvrtc-builtins.alt.so.12.9`,
`libcudart.so.12`, `libcufft.so.11`, `libcufftw.so.11`, `libcurand.so.10`, `libcusolver.so.11`,
`libcusolverMg.so.11`, `libcusparse.so.12`, `libnvJitLink.so.12`.

* Listed in Attachment A of the CUDA 12.9 EULA (Linux): `libcudart.so`, `libcufft.so`, `libcufftw.so`,
  `libcublas.so`, `libcublasLt.so`, `libnvblas.so`, `libcusparse.so`, `libcusolver.so`, `libcurand.so`,
  `libnvrtc.so`, `libnvrtc-builtins.so`, `libnvJitLink.so` ("including certain variations of these files that have
  version number or architecture specific information embedded in the file name").
* **Not listed** in either the 12.9 web EULA or the wheel's text: `libcusolverMg.so.11`, `libnvrtc.alt.so.12`,
  `libnvrtc-builtins.alt.so.12.9`. Using them is covered (§1.1.1 "Install and use the SDK"); redistributing them in
  a built image is not expressly covered.
* The wheel's own `License.txt` (2018 text) has an older Attachment A that does **not** list `libnvJitLink.so`; the
  CUDA 12.9 EULA on NVIDIA's site does. Which of the two texts governs the files of that wheel is not established, so
  the right to redistribute nvJitLink from it is not established either (a newer web text cannot simply be taken to
  govern a file shipped with another; review of 2026-10-29, R7 — "the 12.9 web text grants it" stood here before
  [error in earlier]). It matters only if an image is distributed, which is not planned.

### 3.5 cuda-toolkit 12.9.2.0

A metapackage: the wheel installs only `cuda_toolkit-12.9.2.0.dist-info/` (METADATA, RECORD, WHEEL, INSTALLER,
REQUESTED) and declares no licence at all. It carries no code; that does not make its metadata texts free of rights
(review of 2026-10-29, R7), but the project redistributes nothing of it (users install it from PyPI). The libraries it
pulls in are pinned separately and audited above. The test checks that it still installs no files outside its
`dist-info`.

## 4. python-flint at run time: conditions under LGPL-3.0

Allowed by the rule (weak copyleft, used unmodified, as separate shared libraries loaded by the separately installed
python-flint; the engine's code does not include or modify them), so the engine's own licence is not bound. Duties
arise only when the project **distributes** the libraries (for example in a built image), from LGPL-3.0 §4
([text](https://www.gnu.org/licenses/lgpl-3.0.txt)): the Combined Work may be conveyed "under terms of your choice
that, taken together, effectively do not restrict modification of the portions of the Library contained in the
Combined Work and reverse engineering for debugging such modifications", with (a) a prominent notice that the
Library is used and covered by the LGPL, (b) copies of the GPL and the LGPL (the wheel ships them), and (d1) "a
suitable shared library mechanism" (the `.so` files in `python_flint.libs/` are such: they can be replaced — one part
of the check of §4(d)(1), not proof that every condition is met: a modified, interface-compatible library must work
with the combined work, and the rights to modify it and to debug such modifications must be kept). The object code of
FLINT, GMP and MPFR itself is conveyed under GPL-3.0 §6, whose permitted ways depend on the channel: for an image
offered for download, access to the corresponding source from the same place (§6(d)), not merely an offer on request
([GPLv3 §6](https://www.gnu.org/licenses/gpl-3.0.html#section6)). In a distributed container the GPL and LGPL
components of the Debian base (§5) and libquadmath (§2.2) bring their own duties too, whether or not the engine
imports them (review of 2026-10-29, R7). A commercial licence of the engine must not forbid the reverse engineering that LGPL-3.0 §4 keeps
open for these libraries. Distributing only the source and the lock (users install python-flint from PyPI) avoids
all of this. Plan item P12 keeps the alternative open: make python-flint a test-only dependency.

## 5. Platform: the Docker base image `python:3.11-slim`

Not part of the engine; the platform it runs on. Checked in the image built on 2026-10-27:

* Debian GNU/Linux 13 (trixie), 87 dpkg packages: the usual Debian base (bash, coreutils, glibc, apt, …) under their
  Debian licences (`/usr/share/doc/*/copyright`; GPL programs such as bash and coreutils are separate programs, not
  linked with the engine).
* CPython 3.11.17 built by the Docker official image ([docker-library/python](https://github.com/docker-library/python),
  build scripts MIT): "Python software and documentation are licensed under the PSF License Agreement"
  ([docs.python.org/3.11/license.html](https://docs.python.org/3.11/license.html)), with the incorporated components
  listed there (expat, libffi, zlib, libmpdec, OpenSSL, …). Permissive.
* Python packages of the base image, not pinned in the lock: `pip` 24.0 (MIT, [LICENSE.txt](https://github.com/pypa/pip/blob/main/LICENSE.txt)),
  `setuptools` 79.0.1 (declares no licence in its metadata; MIT, [LICENSE](https://github.com/pypa/setuptools/blob/main/LICENSE)),
  `wheel` 0.46.3 (License-Expression MIT, [LICENSE.txt](https://github.com/pypa/wheel/blob/main/LICENSE.txt)).
  Tooling; the test allows exactly these three besides the pinned packages.
* System libraries that the engine and the server actually load (from `/proc/self/maps` after importing every
  `lfphys` and `lfviz` module): glibc (LGPL-2.1-or-later), libgcc_s and libstdc++ (GPL-3.0-or-later WITH
  GCC-exception-3.1), libbz2 (bzip2 licence, BSD-like), libssl/libcrypto (OpenSSL 3.5, Apache-2.0), libffi (MIT),
  liblzma (0BSD), libuuid (BSD-3-Clause), zlib (Zlib), libzstd (BSD-3-Clause OR GPL-2.0), libpython3.11 (PSF).
  Permissive or weak copyleft / runtime exception.
* Present in the base image but **not loaded**: the CPython modules `readline` (GNU Readline, GPL-3.0-or-later),
  `_gdbm` (GNU dbm, GPL-3.0-or-later) and `_dbm` (Berkeley DB 5.3, Sleepycat licence). They are loaded only on
  `import readline` / `dbm`; no engine or server module imports them, and the test checks that importing every
  `lfphys` and `lfviz` module maps none of them.

## 6. Tooling that is not shipped

* Headless screenshots: the Playwright Docker image (Playwright: Apache-2.0,
  [LICENSE](https://github.com/microsoft/playwright/blob/main/LICENSE)); its browsers keep their own licences. A tool
  run beside the project; nothing of it enters `engine/`.
* The player's codec test (`../../visualizations/player/js/tests/decode.test.mjs`) runs with Node.js's built-in test
  runner (Node.js: MIT, [LICENSE](https://github.com/nodejs/node/blob/main/LICENSE)); no npm packages.
* Docker itself (Moby engine: Apache-2.0, [LICENSE](https://github.com/moby/moby/blob/master/LICENSE)) is the build
  tool.

## 7. The source tree; vendored third-party code (one package)

Checked on 2026-10-27 in `engine/` (excluding `visualizations/runs/`): every SPDX line was
`PolyForm-Noncommercial-1.0.0`, replaced on 2026-10-29 by the project's own `LicenseRef-lfphys-Research-1.0`
(`../../LICENSE.md`; review of 2026-10-29); no copyright line of another holder in the project's own code; no comment marks code
as copied, ported or adapted from a third-party source. Python imports across `engine/` are the standard library,
`numpy`, `scipy`, `mpmath`, `flint`, `aiohttp`, `pytest` and the project's own modules (CuPy only inside
`lfphys.core.backend`); the comparison suite `lfphys/tests/external/` (plan P13, its own image, not collected in the
runtime image) also imports the comparison-only libraries of §10 (`rundec`, `kerrgeopy`, `tmm`, `qutip`, `astropy`).

**Vendored (2026-10-27, for the player's 3-D environment):** `visualizations/player/vendor/three-0.185.1/` — three.js
r185.1 under the MIT licence (permissive: allowed to be copied in, `../../AGENTS.md` §3 rule 8): the two module
builds `three.module.min.js` and `three.core.min.js`, the add-ons `OrbitControls.js` and `TransformControls.js`, and
the licence text, unmodified from the npm package `three@0.185.1`. Their checksums and source are recorded in
`visualizations/player/vendor/README.md`; `../tests/test_licences.py::test_vendored_code_is_permissive_unmodified_and_recorded`
checks the licence, the checksums and this entry. The files keep their own licence (no SPDX line of the project is
added to them); `NOTICE` names them. The player loads nothing from outside the server (the import map points at these
files).

## 8. Findings of this audit

Open items from these findings belong in `../../STATUS.md` (one place for problems).

1. [useful] No runtime dependency is under a strong-copyleft, noncommercial or proprietary licence other than the
   NVIDIA platform runtime; all others are permissive except python-flint (MIT bindings + LGPL-3.0-or-later FLINT,
   GMP, MPFR), which the rule allows.
2. [neutral] The NVIDIA CUDA libraries are allowed as an optional platform runtime: commercial use permitted,
   redistribution permitted only for Attachment A files under §1.1.2 (§3.3).
3. [weakens] Three installed NVIDIA files are not in Attachment A (`libcusolverMg.so.11`, `libnvrtc.alt.so.12`,
   `libnvrtc-builtins.alt.so.12.9`), and the wheels' bundled EULA (2018 text) omits `libnvJitLink.so`, which the
   CUDA 12.9 EULA lists (§3.4). Matters only if a built image is distributed; otherwise distribute source + lock.
4. [neutral] `cuda-toolkit` 12.9.2.0 declares no licence; it installs no code (§3.5).
5. [neutral] numpy and scipy wheels bundle libgfortran (GPL-3.0-or-later WITH GCC-exception-3.1) and libquadmath
   (LGPL-2.1-or-later), not visible in numpy's `License-Expression` (§2.2); both allowed.
6. [neutral] Distributing a built image triggers the LGPL-3.0 duties for FLINT, GMP, MPFR (§4), the duties of the GPL
   and LGPL components of the Debian base (§5) and of libquadmath (§2.2), and the EULA conditions for the NVIDIA files
   (§3); distributing source + lock triggers none of them.
7. [neutral] The python-flint README's licence sentence ("FLINT and Arb are LGPL v2.1+") is out of date; the wheel
   metadata and flintlib.org say LGPL-3.0-or-later (§2.1).
8. [useful] The only vendored third-party code is three.js r185.1 (MIT), unmodified, with its licence and checksums
   (§7; added 2026-10-27 for the 3-D environment).

9. [neutral] The review of 2026-10-29 (R7) refined §3.3, §3.4, §3.5 and §4 (above): the conditions of LGPL-3.0 §4 and
   GPL-3.0 §6 for a downloadable image, the Debian components in a container, the EULA text that governs a wheel's
   files, and the environment-only image. For a release: pin the base image by its digest and keep the licence texts of
   the exact artifacts, since links to `main`/`master` and a mutable Docker tag are no lasting evidence
   (`../../STATUS.md` V20).

## 9. Keeping this file in sync

`../tests/test_licences.py` (run in the lfphys-viz image):

* reads `requirements.lock`, the installed metadata of each pinned package and the table of §1 of this file;
* fails when a pinned package has no row in its allow-table or here, when a row has no pinned package, when the
  pinned version, role, category or decision here differs from the lock or the table, when the declared licence of
  a package falls into a category other than its row's, when a category is not allowed for the package's role, when
  an installed package is neither pinned nor one of the three base-image tools, when a pinned version is not the
  installed one, when a GPL-linked standard-library module (`readline`, `_gdbm`, `_dbm`) is loaded by the engine or
  the server, or when an `lfphys` module needs CuPy at import;
* skips, with a message, a pinned package that the image does not have (a CPU-only build without CuPy and the NVIDIA
  wheels).

A new or upgraded pinned package therefore needs: its licence read in the image and on the project's site, a row in
§1, and the same row in the test's table.

## 10. Comparison-only libraries (plan P13)

Third-party libraries that the comparison suite `../tests/external/` uses to check the engine's accuracy
(`../../AGENTS.md` §3 rule 8: «сравнения со сторонними библиотеками для проверки точность движка, используй сторонние
библиотеки только для тестов сравнения»). They are installed only in the separate image `lfphys-ext`
(`../tests/external/docker/Dockerfile`, pins in `../tests/external/docker/requirements-external.lock`), on top of
`lfphys-viz` with `--no-deps`. They are never imported by engine code and never pinned in
`../../visualizations/docker/requirements.lock`, and they are not in `ALLOWED` of `../tests/test_licences.py`, whose
scope is the runtime image only. The image is for local testing only and is never distributed. Every row below
therefore has the role **comparison tests only, separate image, not distributed**.

Audited 2026-10-27 in two ways:

* the installed metadata in `lfphys-ext`, read as in §1;
* the licence file in each project's repository, through the GitHub licence API and the file itself, fetched
  anonymously.

### 10.1 The comparison libraries

| package | version | licence declared (installed metadata) | licence in the LICENSE file (repository) | category | role |
|---|---|---|---|---|---|
| `rundec` | 0.7 | License: MIT (LICENSE: "MIT License, Copyright (c) 2019 David Straub") | MIT ([LICENSE](https://github.com/DavidMStraub/rundec-python/blob/master/LICENSE)). The wheel's `_rundec.abi3.so` compiles `CRunDec3/CRunDec.3.1.cpp` (setup.py at tag v0.7), whose header reads "License: Copyright (c) 2019 Florian Herren & Matthias Steinhauser / Permission is hereby granted, free of charge, ..." (MIT) and whose change log says "Jan 2019: Changed license from GPLv3 to MIT". The current CRunDec 3.1.3 from TTP Karlsruhe ([ttp17-011](https://www.ttp.kit.edu/preprints/2017/ttp17-011), crundec3.1.3.tar.gz) has the same MIT header | permissive | comparison tests only, separate image, not distributed |
| `kerrgeopy` | 0.9.3 | classifier: MIT License (no License field) | MIT ([LICENSE](https://github.com/BlackHolePerturbationToolkit/KerrGeoPy/blob/main/LICENSE): "MIT License, Copyright (c) 2024 Black Hole Perturbation Toolkit") | permissive | comparison tests only, separate image, not distributed |
| `tmm` | 0.2.0 | License: MIT; classifier: MIT License | MIT text ([LICENSE.txt](https://github.com/sbyrnes321/tmm/blob/master/LICENSE.txt): "Copyright (C) 2012-2024 Steven Byrnes / Permission is hereby granted, free of charge, ...") | permissive | comparison tests only, separate image, not distributed |
| `qutip` | 5.3.1 | License-Expression: BSD-3-Clause | BSD-3-Clause ([LICENSE.txt](https://github.com/qutip/qutip/blob/master/LICENSE.txt): "Copyright (c) 2011 to 2026 inclusive, QuTiP developers and contributors. ... Redistribution and use in source and binary forms, with or without modification, are permitted provided that ...") | permissive | comparison tests only, separate image, not distributed |
| `astropy` | 8.0.2 | License-Expression: BSD-3-Clause (bundled-code licences in `dist-info/licenses/licenses/`, §10.3) | BSD-3-Clause ([LICENSE.rst](https://github.com/astropy/astropy/blob/main/LICENSE.rst): "Copyright (c) 2011-2026, Astropy Developers ... Redistribution and use in source and binary forms, with or without modification, are permitted provided that ...") | permissive (bundles WCSLIB, LGPL-3.0: §10.3) | comparison tests only, separate image, not distributed |
| `miepython` | 3.3.0 | License-Expression: MIT (dist-info/licenses/LICENSE.txt) | MIT ([LICENSE.txt](https://github.com/scottprahl/miepython/blob/main/LICENSE.txt): "Copyright 2017-2021 Scott Prahl / Permission is hereby granted, free of charge, ...") | permissive | comparison tests only, separate image, not distributed (added 2026-11-04, B8, plan P1) |

### 10.2 What they pull in

The table lists the packages that the six libraries add to the runtime image. The comparison tests themselves import
only the five libraries above, with their own imports.

| package | version | needed by | licence declared (installed metadata) | licence in the LICENSE file (repository) | category | role |
|---|---|---|---|---|---|---|
| `astropy-iers-data` | 0.2026.10.19.0.52.1 | astropy | License-Expression: BSD-3-Clause | BSD-3-Clause ([LICENSE.rst](https://github.com/astropy/astropy-iers-data/blob/main/LICENSE.rst)) | permissive | comparison tests only, separate image, not distributed |
| `contourpy` | 1.3.3 | matplotlib | License: the BSD 3-Clause text; classifier: BSD License | BSD-3-Clause ([LICENSE](https://github.com/contourpy/contourpy/blob/main/LICENSE)) | permissive | comparison tests only, separate image, not distributed |
| `cycler` | 0.12.1 | matplotlib | License: the BSD text; classifier: BSD License | BSD-3-Clause ([LICENSE](https://github.com/matplotlib/cycler/blob/main/LICENSE)) | permissive | comparison tests only, separate image, not distributed |
| `fonttools` | 4.68.0 | matplotlib | License: MIT | MIT ([LICENSE](https://github.com/fonttools/fonttools/blob/main/LICENSE)) | permissive | comparison tests only, separate image, not distributed |
| `kiwisolver` | 1.5.1 | matplotlib | License: the Kiwi terms; classifier: BSD License | "Kiwi is licensed under the terms of the Modified BSD License (also known as New or Revised BSD)" ([LICENSE](https://github.com/nucleic/kiwi/blob/main/LICENSE)) | permissive | comparison tests only, separate image, not distributed |
| `matplotlib` | 3.11.2 | kerrgeopy | License: "License agreement for matplotlib versions 1.3.0 and later" (PSF-based); classifier: Python Software Foundation License | the same agreement ([LICENSE/LICENSE](https://github.com/matplotlib/matplotlib/blob/main/LICENSE/LICENSE)) | permissive | comparison tests only, separate image, not distributed |
| `pillow` | 13.0.0 | matplotlib | License-Expression: MIT-CMU | "Like PIL, Pillow is licensed under the open source MIT-CMU License" ([LICENSE](https://github.com/python-pillow/Pillow/blob/main/LICENSE)) | permissive (bundled libraries: §10.3) | comparison tests only, separate image, not distributed |
| `pyerfa` | 2.0.1.5 | astropy | License: BSD 3-Clause License; classifier: BSD License | BSD-3-Clause ([LICENSE.rst](https://github.com/liberfa/pyerfa/blob/main/LICENSE.rst)) | permissive | comparison tests only, separate image, not distributed |
| `pyparsing` | 3.3.3 | matplotlib | License-Expression: MIT | MIT ([LICENSE](https://github.com/pyparsing/pyparsing/blob/master/LICENSE)) | permissive | comparison tests only, separate image, not distributed |
| `python-dateutil` | 3.0.0 | matplotlib | License: Dual License; classifiers: BSD License, Apache Software License | Apache-2.0 for contributions after 2017-12-01, "The above BSD License Applies to all code, even that also covered by Apache 2.0" ([LICENSE](https://github.com/dateutil/dateutil/blob/master/LICENSE)) | permissive | comparison tests only, separate image, not distributed |
| `PyYAML` | 6.0.3 | astropy | License: MIT; classifier: MIT License | MIT ([LICENSE](https://github.com/yaml/pyyaml/blob/main/LICENSE)) | permissive | comparison tests only, separate image, not distributed |
| `six` | 1.17.0 | python-dateutil | License: MIT; classifier: MIT License | MIT ([LICENSE](https://github.com/benjaminp/six/blob/main/LICENSE)) | permissive | comparison tests only, separate image, not distributed |
| `tqdm` | 4.70.1 | kerrgeopy | License: MPL-2.0 AND MIT | MPL-2.0 for files by its main author, MIT for the rest ([LICENCE](https://github.com/tqdm/tqdm/blob/master/LICENCE)) | weak copyleft (MPL-2.0, unmodified) | comparison tests only, separate image, not distributed |
| `tzdata` | 2026.5 | matplotlib (via dateutil) | License: Apache-2.0 | "Apache Software License 2.0" ([LICENSE](https://github.com/python/tzdata/blob/master/LICENSE)) | permissive | comparison tests only, separate image, not distributed |
| `numba` | 0.68.0 | miepython | License: BSD; LICENSE + LICENSES.third-party (MIT, BSD-3-Clause for NetworkX, PSF for CPython-derived code) | BSD-2-Clause ([LICENSE](https://github.com/numba/numba/blob/main/LICENSE): "Copyright (c) 2012, Anaconda, Inc.") | permissive | comparison tests only, separate image, not distributed (B8) |
| `llvmlite` | 0.50.0 | numba | License-Expression: BSD-2-Clause AND Apache-2.0 WITH LLVM-exception | BSD-2-Clause ([LICENSE](https://github.com/numba/llvmlite/blob/main/LICENSE): "Copyright (c) 2014, Anaconda Inc."); LICENSE.thirdparty: LLVM under Apache-2.0 with LLVM exceptions | permissive | comparison tests only, separate image, not distributed (B8) |

### 10.3 Libraries bundled inside these wheels

Read from the wheels' own licence files in the image:

* **astropy**:
  * `dist-info/licenses/licenses/` lists AURA, ConfigObj, DataTables, ERFA, Expat, gatspy, jQuery, NumPy, PLY,
    PyFITS, Python and positional-defaults code under BSD-, MIT- and PSF-style terms.
  * It also lists WCSLIB, under the GNU LGPL-3.0 (`WCSLIB_LICENSE.rst`), compiled into `astropy/wcs/_wcs.abi3.so`.
  * Weak copyleft. The comparison tests use `astropy.constants` and `astropy.units`, not `astropy.wcs`.
* **pillow** (`pillow.libs/`): FreeType, libjpeg-turbo, libtiff, libpng, lcms2, OpenJPEG, libwebp, libavif (with
  dav1d, AOM, libyuv), Brotli, HarfBuzz, libxcb/libXau, liblzma, zstd.
  * Their terms are in `dist-info/licenses/LICENSE`.
  * FreeType is offered under the FreeType License or the GPL-2.0, with "you must choose one of the two licenses".
  * liblzma is in the public domain.
  * The rest are BSD-, MIT-, zlib- or IJG-style.
* **matplotlib**: the DejaVu fonts (Bitstream Vera terms, DejaVu changes in the public domain) and the STIX fonts
  (`mpl-data/fonts/ttf/LICENSE_STIX`).
* **rundec**: CRunDec 3.1 (MIT, §10.1), compiled into `_rundec.abi3.so`.
* **llvmlite** (B8): `binding/libllvmlite.so` links LLVM (Apache-2.0 WITH LLVM-exception). numba's auditwheel SBOM names
  libgomp 8.5.0, but no libgomp file is installed (the whole container searched, 2026-11-04).

### 10.4 Findings

1. [error in earlier] `../PLAN.md` (P13) and `../LAYERS.md` §4 call rundec/CRunDec "GPL-3". CRunDec has been MIT
   since January 2019 (CRunDec.cpp v3.1 change log), and rundec-python is MIT. The plan also names Meep (GPL-2), which
   was not installed then (B8 ran it once in a throwaway image, §10.5). The note in the plan is out of date for CRunDec. The rule does not change: comparison-only
   libraries stay in this suite whatever their licence.
2. [neutral] At the pinned versions no package in `lfphys-ext` is under a strong-copyleft, noncommercial or
   proprietary licence. Only the runtime image's NVIDIA platform runtime (§3) is proprietary, and the base layer is
   unchanged. Weak copyleft appears in tqdm (MPL-2.0) and in astropy's bundled WCSLIB (LGPL-3.0). The image is still
   test-only and is never distributed.
3. [neutral] `../tests/test_licences.py` is not run in `lfphys-ext`. Its check `test_image_has_no_unaudited_packages`
   would rightly flag the 21 packages above as not pinned in the runtime lock. This section is their audit.
4. [neutral] B8 (2026-11-04, plan P1): `pip install -c <base freeze> miepython==3.3.0 numba==0.68.0 llvmlite==0.50.0`
   in a throwaway `lfphys-ext` container added exactly these three packages; `pip check` clean; installed with
   `--no-deps`. matplotlib and scipy were already present. Meep, which the plan also names, is not in this image: it
   is conda-only and was run once in a throwaway image (§10.5), where strong copyleft is present.

### 10.5 Meep (plan P1): a one-off comparison, not in the repository

Meep 1.35.0 (GPL-2.0-or-later) was compared once with `core.em.fdtd`, on 2026-11-04 (record:
`comparison_2026-11-04_meep.md`). By the owner's rule of 2026-11-10 (`../../AGENTS.md` §3 rule 8) a comparison with a
copyleft or restricted library is a one-off run from a script outside the repository, in a throwaway image; its script
(`test_ext_fdtd_meep.py`) and image recipe (`docker/meep/`) were in the repository from 2026-11-04 to 2026-11-10
(commits a55d0fc, 85e3e41) and were removed then, the image `light-funnel-ext-meep` deleted. Running GPL code is not
restricted (GPL-2 §0); nothing of Meep was distributed. The audit of that image, kept as the record of what ran:

* The image (2026-11-04, since deleted) was built from a Dockerfile then in `../tests/external/docker/meep/`: `condaforge/miniforge3:26.7.2-0` pinned by
  digest (sha256:569afc65…), and a conda environment from `meep-explicit.lock` (124 packages by URL and md5; numpy
  2.4.6, scipy 1.17.1, mpmath 1.3.0 and pytest 9.1.1 as in the runtime image).
* Licences from the conda-forge records, audited 2026-11-04:
  * GPL-2.0-or-later: pymeep 1.35.0, mpb 1.12.0, harminv 1.4.3, libctl 4.7.1, libgdsii 0.21, fftw 3.3.11;
  * GPL-3.0-or-later: gsl 2.8; GPL-3.0-only: readline 8.3, ld_impl; the GCC runtime: GPL-3.0 with the GCC exception;
  * LGPL: glib, cairo (LGPL-2.1 or MPL-1.1), libiconv, libnsl, fribidi, keyutils, libxcrypt, graphite2;
  * freetype: GPL-2.0-only or FTL;
  * the remaining packages are permissive (MIT 36, BSD-3 25, Apache-2.0 7 and others).
* Meep's repository `LICENSE` is the GPL v2; a source header reads "either version 2, or (at your option) any later
  version".
* Role: a one-off comparison, in a separate image that was never distributed. Meep is used through its documented
  Python interface; no Meep code was read for the engine (one source header was grepped, for its licence statement).
* The engine never imports Meep. It is not in the runtime image, its lock, `lfphys-ext`, or `ALLOWED`.
