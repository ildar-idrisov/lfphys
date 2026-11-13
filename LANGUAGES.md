# Languages

The languages of everything a user reads (`AGENTS.md` §3 rule 13): the player's interface and the server's messages to
it, the README and the user guides, the public site.

| code | language | status |
|---|---|---|
| `en` | English | default |
| `ru` | Русский | interface and user documents complete (2026-11-12) |

Adding a language: add its row here, its interface catalogues (`locales/<code>.json` next to every catalogue: the engine's, the framework's and each world's; `LANGS` in
`visualizations/server/lfviz/i18n.py` and `visualizations/player/js/i18n.js`) and
the translated documents (`README.<code>.md` next to every user document); the completeness tests list what is missing.
