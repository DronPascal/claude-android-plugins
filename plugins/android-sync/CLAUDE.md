# android-sync

Tooling plugin that keeps the android/skills-derived plugins in sync with upstream. Unlike the other plugins, it ships no ported content of its own — it maintains the others (android-core, android-migrations, android-performance, and the topic plugins).

## Components

- **`/android-sync:update`** (skill `update`) — runs the upstream sync: fetches github.com/android/skills, refreshes ported skill bodies + references, bumps plugin versions, updates NOTICE.md.
- **`scripts/sync_upstream.py`** — refreshes already-ported skills listed in NOTICE.md (body + references), preserving our hand-written frontmatter. Used by `/android-sync:update`.
- **`scripts/port_skill.py`** — ports a NEW upstream skill into a target plugin (frontmatter stub + upstream body + references + NOTICE row). Separate from sync.
- **`scripts/frontmatter.py`, `scripts/notice.py`** — shared helpers (frontmatter split/build with `upstream` block, NOTICE table upsert).
- **`agents/upstream-diff-analyzer.md`** — summarises each per-skill upstream diff into a changelog during a sync run (one instance per changed skill).

## Invariant

Our frontmatter (trigger phrases + `upstream` block) is maintained manually; skill bodies and `references/` are upstream-owned and overwritten on every sync. Never hand-edit a ported body — the next `/android-sync:update` will revert it.
