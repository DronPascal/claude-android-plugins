# NOTICE

This marketplace contains skills adapted from [android/skills](https://github.com/android/skills) under the Apache License 2.0.

## Ported skills

<!-- table-start -->
| Plugin | Skill | Upstream path | Last synced commit |
|---|---|---|---|
| android-ai | appfunctions | device-ai/appfunctions/ | 07302ca15e21d827cab5ca64d46407fb51dbe0aa |
| android-core | adaptive | jetpack-compose/adaptive/ | 07302ca15e21d827cab5ca64d46407fb51dbe0aa |
| android-core | compose-styles | jetpack-compose/theming/styles/ | 07302ca15e21d827cab5ca64d46407fb51dbe0aa |
| android-core | edge-to-edge | system/edge-to-edge/ | 07302ca15e21d827cab5ca64d46407fb51dbe0aa |
| android-core | navigation-3 | navigation/navigation-3/ | 07302ca15e21d827cab5ca64d46407fb51dbe0aa |
| android-devtools | android-cli | devtools/android-cli/ | 07302ca15e21d827cab5ca64d46407fb51dbe0aa |
| android-identity | verified-email | identity/verified-email/ | 07302ca15e21d827cab5ca64d46407fb51dbe0aa |
| android-migrations | agp-9-upgrade | build/agp/agp-9-upgrade/ | 07302ca15e21d827cab5ca64d46407fb51dbe0aa |
| android-migrations | camera1-to-camerax | camera/camera1-to-camerax/ | 07302ca15e21d827cab5ca64d46407fb51dbe0aa |
| android-migrations | migrate-xml-views-to-compose | jetpack-compose/migration/migrate-xml-views-to-jetpack-compose/ | 07302ca15e21d827cab5ca64d46407fb51dbe0aa |
| android-migrations | play-billing-upgrade | play/play-billing-library-version-upgrade/ | 07302ca15e21d827cab5ca64d46407fb51dbe0aa |
| android-performance | perfetto-sql | profilers/perfetto-sql/ | 07302ca15e21d827cab5ca64d46407fb51dbe0aa |
| android-performance | perfetto-trace-analysis | profilers/perfetto-trace-analysis/ | 07302ca15e21d827cab5ca64d46407fb51dbe0aa |
| android-performance | r8-analyzer | performance/r8-analyzer/ | 07302ca15e21d827cab5ca64d46407fb51dbe0aa |
| android-play | engage-sdk-integration | play/engage-sdk-integration/ | 07302ca15e21d827cab5ca64d46407fb51dbe0aa |
| android-security | intent-security | security/android-intent-security/ | 07302ca15e21d827cab5ca64d46407fb51dbe0aa |
| android-testing | testing-setup | testing/testing-setup/ | 07302ca15e21d827cab5ca64d46407fb51dbe0aa |
| android-wear | wear-compose-m3 | wear/wear-compose-m3/ | 07302ca15e21d827cab5ca64d46407fb51dbe0aa |
| android-xr | display-glasses-glimmer | xr/display-glasses-with-jetpack-compose-glimmer/ | 07302ca15e21d827cab5ca64d46407fb51dbe0aa |
<!-- table-end -->

## Modifications from upstream

- Frontmatter rewritten for Claude Code skill API (auto-trigger phrases, `upstream` block).
- Directory layout flattened to `plugins/<plugin>/skills/<skill>/SKILL.md`.
- Body and `references/` preserved as-is from upstream.

Full upstream license: `LICENSE-upstream-android-skills.txt`
