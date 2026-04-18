# NOTICE

This marketplace contains skills adapted from [android/skills](https://github.com/android/skills) under the Apache License 2.0.

## Ported skills

<!-- table-start -->
| Plugin | Skill | Upstream path | Last synced commit |
|---|---|---|---|
| android-core | edge-to-edge | system/edge-to-edge/ | b281881e3fbe044d29b4ea757de06758a4ca81ec |
| android-core | navigation-3 | navigation/navigation-3/ | b281881e3fbe044d29b4ea757de06758a4ca81ec |
| android-migrations | agp-9-upgrade | build/agp/agp-9-upgrade/ | b281881e3fbe044d29b4ea757de06758a4ca81ec |
| android-migrations | migrate-xml-views-to-compose | jetpack-compose/migration/migrate-xml-views-to-jetpack-compose/ | b281881e3fbe044d29b4ea757de06758a4ca81ec |
| android-migrations | play-billing-upgrade | play/play-billing-library-version-upgrade/ | b281881e3fbe044d29b4ea757de06758a4ca81ec |
| android-performance | r8-analyzer | performance/r8-analyzer/ | b281881e3fbe044d29b4ea757de06758a4ca81ec |
<!-- table-end -->

## Modifications from upstream

- Frontmatter rewritten for Claude Code skill API (auto-trigger phrases, `upstream` block).
- Directory layout flattened to `plugins/<plugin>/skills/<skill>/SKILL.md`.
- Body and `references/` preserved as-is from upstream.

Full upstream license: `LICENSE-upstream-android-skills.txt`
