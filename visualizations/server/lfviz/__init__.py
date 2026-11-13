# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""lfviz: the one server, player protocol and run machinery for the lfphys visualizations.

Layout (see ../../RULES.md for the rules and the API):

* ``protocol``  - binary message format shared by worker, server, recording file and browser;
* ``params``    - parameter schema (world parameters vs live actions, standard-physics markers);
* ``sim``       - base class of a simulation and the real-time runner (transport, frames);
* ``worker``    - the process that runs one simulation and talks to the server over stdin/stdout;
* ``registry``  - discovery of visualization folders ``visualizations/{s,u,r,p}NN_*`` (their audiences; the old ``vNN_*`` ids are aliases);
* ``runs``      - run manager: spawn, record, broadcast, limits;
* ``app``       - HTTP + WebSocket API and static files.
"""

__version__ = "1.0"
