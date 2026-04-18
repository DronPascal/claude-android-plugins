# claude-android-plugins

Claude Code marketplace with Android-development skills ported from [android/skills](https://github.com/android/skills) (Apache 2.0, Google LLC).

## Plugins

- **android-core** — always-on: Navigation-3, edge-to-edge.
- **android-migrations** — on-demand: XML→Compose, AGP-9 upgrade, Play Billing upgrade.
- **android-performance** — R8 analyzer (more to come).
- **android-sync** — `/android-sync:update` keeps ported skills in sync with upstream.

## Install

```bash
/plugin marketplace add DronPascal/claude-android-plugins
/plugin install android-core@claude-android-plugins
/plugin install android-sync@claude-android-plugins
```

Install migration/performance plugins per-project as needed.

## Upstream sync

Run `/android-sync:update` to pull latest skill content from `android/skills`. Our frontmatter is preserved; body and references are refreshed.

## License

Our adaptations: MIT. Ported skill content: Apache 2.0 (see `NOTICE.md` and `LICENSE-upstream-android-skills.txt`).
