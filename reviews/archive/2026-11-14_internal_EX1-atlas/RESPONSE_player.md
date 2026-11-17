# Response to review R-F (EX1-atlas): the player's part

**Responder:** QP, the processing agent for the player (`visualizations/player/**`, `visualizations/tests/browser/**`;
containers `lf-qp-*`, private port 8706). It wrote neither the review nor the code under review. **Date:** 2026-11-17.

**Scope.** Only the client side of D13 (F2). Every finding of this review is QF's (`RESPONSE_framework.md`).

| # | finding | outcome (this part) | where | test |
|---|---|---|---|---|
| F2 | a live point is a delta against the server's base, but the player merges it with the local base; its passport names the atlas's | **fixed, player side** (D13). Every packed header names its base file (`$base`, the base's sha256; QF). `atlas.js` merges a delta only when `$base` is the manifest's `base.sha256`; a live point packed against another base is asked again with `full_header: true` and comes whole; an atlas point that does not match is an error. `$base` is dropped from the merged header like `$delta`. A live point keeps its own passport from the headers (`X-LF-Source`, `X-LF-Key`, `X-LF-Code`, `X-LF-Made`), and Explore's drawer shows it: the point's key, the code that computed it, the time with its zone, and whether it was computed now, taken from the server's cache, or is the atlas's own on-grid point. A screen uses only an atlas whose key is the one the server would build now (D11), so a stale local base is not opened at all | `player/js/atlas.js` (`baseMatches`, `build`, `live`, `mergeHeader`), `player/js/explore.js` (drawer) | `atlas.test.mjs` «(server) a live point's own passport; another base asks for the full header; a 429 in the viewer's language»; `demo_screens.mjs` «the passport says «computed live», with the point's own key, code and time with its zone (D13)» |
