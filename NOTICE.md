# NOTICE

This marketplace contains skills adapted from [android/skills](https://github.com/android/skills) under the Apache License 2.0.

## Ported skills

<!-- table-start -->
| Plugin | Skill | Upstream path | Last synced commit |
|---|---|---|---|
| android-core | edge-to-edge | system/edge-to-edge/ | 07302ca15e21d827cab5ca64d46407fb51dbe0aa |
| android-core | navigation-3 | navigation/navigation-3/ | 07302ca15e21d827cab5ca64d46407fb51dbe0aa |
| android-migrations | agp-9-upgrade | build/agp/agp-9-upgrade/ | 07302ca15e21d827cab5ca64d46407fb51dbe0aa |
| android-migrations | migrate-xml-views-to-compose | jetpack-compose/migration/migrate-xml-views-to-jetpack-compose/ | 07302ca15e21d827cab5ca64d46407fb51dbe0aa |
| android-migrations | play-billing-upgrade | play/play-billing-library-version-upgrade/ | 07302ca15e21d827cab5ca64d46407fb51dbe0aa |
| android-performance | r8-analyzer | performance/r8-analyzer/ | 07302ca15e21d827cab5ca64d46407fb51dbe0aa |
<!-- table-end -->

## Modifications from upstream

- Frontmatter rewritten for Claude Code skill API (auto-trigger phrases, `upstream` block).
- Directory layout flattened to `plugins/<plugin>/skills/<skill>/SKILL.md`.
- Body and `references/` preserved as-is from upstream.

Full upstream license: `LICENSE-upstream-android-skills.txt`
