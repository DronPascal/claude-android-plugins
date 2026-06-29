---
name: update
description: >
  This skill should be used when the user asks to "update android skills",
  "sync android plugins", "pull upstream android skills", "refresh android
  plugins from upstream", "обнови android плагины", or wants to refresh
  the content of android-core / android-migrations / android-performance
  plugins from github.com/android/skills.
user-invocable: true
argument-hint: "[--dry-run] [--plugin <name>] [--force]"
allowed-tools: [Bash, Read, Edit, Task]
---

Run the upstream sync for the claude-android-plugins marketplace. Besides refreshing already-ported skills, the script reports upstream skills that are **not yet ported**, so this skill can offer to add the missing ones.

## Steps

1. Locate the marketplace root by walking up from `${CLAUDE_PLUGIN_ROOT}` until a `.claude-plugin/marketplace.json` is found.
2. Invoke the sync script via Bash, forwarding user arguments:
   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/sync_upstream.py \
     --marketplace <marketplace-root> $ARGUMENTS
   ```
3. Read `/tmp/android-sync-run-<timestamp>/summary.md` that the script writes. The timestamp is printed on stdout.
4. For each changed skill listed in `summary.md`, dispatch the `upstream-diff-analyzer` agent in parallel. Pass the agent the paths to `diff.patch`, old SKILL.md, new SKILL.md, and the upstream path.
5. Collect agent outputs into a consolidated changelog. Append it to `summary.md` or present it directly to the user.
6. Surface to the user: list of changed skills, plugins needing version bump (script already updates `plugin.json` in non-dry-run mode), per-skill changelogs.
7. **Offer new (not-yet-ported) upstream skills.** If `summary.md` contains a `## New upstream skills not yet ported` section, surface that list — these exist in `android/skills` but are absent from this marketplace. For the ones the user wants, help port each:
   - Propose a target plugin — an existing one if it fits (profiler → `android-performance`, migration → `android-migrations`, UI → `android-core`), or a new `android-<topic>` plugin (create its `.claude-plugin/plugin.json` + `CLAUDE.md` skeleton first).
   - Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/port_skill.py --upstream /tmp/android-skills-upstream --upstream-path <path> --target-plugin <plugin> --name <skill> --marketplace <marketplace-root>`.
   - Rewrite the stub `description` (the script leaves a `TODO`) into a third-person trigger with quoted phrases, and register any NEW plugin in `marketplace.json`.
   - Do NOT port automatically — taxonomy (which plugin, new vs existing) is the user's call. Ask first.
8. Print the git review hint:
   ```
   Review with: git -C <marketplace> diff
   Commit with: git -C <marketplace> add -A && git commit -m "sync: update from upstream <short-sha>"
   ```

## Flags

- `--dry-run` — the script analyses and writes to `/tmp` only; no files in the marketplace are modified.
- `--plugin <name>` — sync only the named plugin's skills.
- `--force` — proceed even if the marketplace working tree is dirty.

## When NOT to run

- If the marketplace has uncommitted changes (script will abort unless `--force`).
- Without network access to github.com (clone/fetch will fail).
