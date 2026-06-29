# claude-android-plugins

Marketplace of Claude Code plugins for Android development, adapted from [android/skills](https://github.com/android/skills) (Apache 2.0). Twelve plugins (`android-core`, `android-migrations`, `android-performance`, and topic plugins such as `android-wear` / `android-xr` / …), kept in sync with upstream via the `android-sync` plugin.

## Version bumping (enforced by hook)

Any change to a plugin's **content** must be accompanied by a version bump in that plugin's `.claude-plugin/plugin.json` **and** the matching entry in `.claude-plugin/marketplace.json`. The bump forces cache invalidation so users actually receive the update via `/plugin update`.

- New skill / plugin / agent / command → **minor** bump (`0.2.0 → 0.3.0`)
- Fix / content refresh → **patch** bump (`0.2.0 → 0.2.1`)

The `.claude/hooks/check-version-bump.sh` PreToolUse hook **blocks** any `git commit` that stages `plugins/**` changes without also staging `plugin.json` + `marketplace.json`.

### Commit gotcha

The hook re-evaluates staged state at commit time. A chained `git add X && git commit -m "…"` can lose staging context and trip the hook. **Stage in a separate Bash call, then commit:**

```bash
git add plugins/… .claude-plugin/marketplace.json   # one call
git commit -m "…"                                    # next call
```

After a version bump, run `git push origin main` — `/plugin update` fetches the manifest from the remote, not from local commits.

## Sync with upstream

`/android-sync:update` refreshes already-ported skills from `android/skills` and also reports upstream skills **not yet ported**, offering to add them. Invariant: our frontmatter (trigger phrases + `upstream` block) is hand-maintained; skill bodies and `references/` are upstream-owned and overwritten on every sync. Details: `plugins/android-sync/CLAUDE.md`.
