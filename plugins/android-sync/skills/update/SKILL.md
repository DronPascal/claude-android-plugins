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

Run the upstream sync for the claude-android-plugins marketplace.

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
7. Print the git review hint:
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
