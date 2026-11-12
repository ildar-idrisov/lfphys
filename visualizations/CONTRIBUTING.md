# Contributing

Contributions are accepted only on the terms below. Please write to idrisov.sci@gmail.com before You start.

## Licence of contributions

Every contributor agrees to the lfphys Individual Contributor Licence Agreement 1.0 (`CLA.md`) before the first
Contribution is accepted, with the agreement recorded as section 6 of `CLA.md` describes. In short:

1. You keep the copyright in Your Contribution and grant the Licensor, Ildar Idrisov, and a successor to whom he
   assigns his copyright or grants an exclusive licence in writing, a perpetual, non-exclusive, irrevocable licence to
   use and relicense it under any terms, including the lfphys Research Licence (`LICENSE.md`), Creative Commons licences
   and separate commercial licences;
2. You grant a patent licence limited to Your patent claims that Your Contribution, alone or combined with the project
   as it was when You submitted it, necessarily infringes;
3. You confirm that You have the right to grant all of this; where Your employer, university or client may have rights
   in Your work, the Licensor needs its written consent or waiver before accepting the Contribution (the form is in
   `CLA.md` §7); You identify any third-party material with its source and licence, and any part made with AI tools.

The full text is in `CLA.md`; this summary does not replace it.

## Third-party code and libraries

* The Licensor can relicense his own code and the project as a whole under any terms only while the licences of the
  third-party material in it are respected (for example the notices that Apache-2.0 requires). Code and data copied
  into the project must therefore be under permissive licences (MIT, BSD, Apache-2.0, ISC, PSF, zlib or public domain),
  with their notices kept and any changes to them marked. No code under noncommercial, proprietary or copyleft (GPL,
  AGPL, LGPL, MPL, CC BY-SA, CC BY-NC) licences is copied in; such algorithms are reimplemented from their published
  descriptions. A permissively licensed component stays available under its own licence, also for commercial use.
* Runtime dependencies are permissive, or weak copyleft (LGPL, MPL-2.0) used unmodified as separate installed
  libraries, which does not bind the project's own licence (python-flint / FLINT: MIT / LGPL-3); whoever distributes
  such a library, for example inside a built image, takes on the duties of its licence
  (`lfphys/sources/dependencies.md`).
* Libraries under strong copyleft (GPL, AGPL), noncommercial or proprietary licences may be used only in tests that
  compare the project's results with them, and only where their own licences allow that use: "tests only" creates no
  permission. They are never used by the library or the visualizations themselves.
* Platform runtimes: the NVIDIA CUDA libraries used by the optional GPU backend are installed from PyPI under the
  NVIDIA EULA. They are never copied into the source tree; the engine works without them
  (`lfphys/sources/dependencies.md`).

## Notices

Every source file of the project carries, as comments at its top, the line

    SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0

and one `SPDX-FileCopyrightText` line for each holder of copyright in it: the owner's line

    SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>

in files he authored, and a contributor's own line (`SPDX-FileCopyrightText: <year> <name>`, an e-mail address
optional) in a file the contributor authored or changed substantially. Nobody removes an existing notice. Third-party
files (`visualizations/player/vendor/`) keep their own notices and licences and carry no project lines. Keep `NOTICE`
with every copy (`LICENSE.md` §4).
