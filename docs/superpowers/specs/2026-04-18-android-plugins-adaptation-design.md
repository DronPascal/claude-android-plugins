# Android Plugins Adaptation — Design

**Дата:** 2026-04-18
**Статус:** Approved (brainstorming complete, ready for implementation plan)
**Маркетплейс:** `claude-android-plugins`
**Remote:** `git@github.com:DronPascal/claude-android-plugins.git`
**Источник:** [android/skills](https://github.com/android/skills) (Apache 2.0)

---

## Цель

Портировать 6 Android-скиллов из формата agentskills.io (используется Gemini / Android Studio) в формат Claude Code-плагина, и сделать инфраструктуру для автоматической синхронизации с апстримом.

**Почему это нужно:**
- Контент качественный и поддерживается Google (Compose migration, Navigation-3, edge-to-edge, AGP upgrade, Play Billing, R8-analyzer).
- Адаптация под CC позволяет использовать их из Claude Code с auto-triggering и прочими фичами плагин-системы.
- Автоматический sync с апстримом избавляет от рутины ручного обновления при развитии android/skills.

---

## Архитектура маркетплейса

Четыре плагина: три контентных + один служебный.

```
claude-android-plugins/
  .claude-plugin/marketplace.json
  LICENSE-upstream-android-skills.txt    # копия Apache 2.0 апстрима
  NOTICE.md                              # атрибуция + таблица портированных скиллов
  README.md
  .gitignore
  docs/
    superpowers/specs/                   # design docs
  plugins/
    android-core/                        # always-on: Navigation-3, edge-to-edge
    android-migrations/                  # on-demand: XML→Compose, AGP-9, Play Billing
    android-performance/                 # R8-analyzer (+ room for growth)
    android-sync/                        # /android-sync:update
```

### Принципы группировки

- `android-core` — навыки постоянного использования; включается в `~/.claude/settings.json` глобально.
- `android-migrations` — крупные пошаговые мигратор-скиллы; включается только на проектах, где реально идёт миграция (иначе их description забивает system prompt).
- `android-performance` — сейчас один скилл, но очевидное место для расширения (baseline profiles, profilers, layout inspector helpers).
- `android-sync` — обслуживающий плагин; живёт отдельно от контента.

### Соответствие апстриму

| Наш плагин | Скилл | Апстрим |
|---|---|---|
| android-core | navigation-3 | navigation/navigation-3/ |
| android-core | edge-to-edge | system/edge-to-edge/ |
| android-migrations | migrate-xml-views-to-compose | jetpack-compose/migration/migrate-xml-views-to-jetpack-compose/ |
| android-migrations | agp-9-upgrade | build/agp/agp-9-upgrade/ |
| android-migrations | play-billing-upgrade | play/play-billing-library-version-upgrade/ |
| android-performance | r8-analyzer | performance/r8-analyzer/ |

---

## Состав плагинов

### android-core (v0.1.0)
```
plugins/android-core/
  .claude-plugin/plugin.json
  CLAUDE.md
  skills/
    navigation-3/
      SKILL.md
      references/                  # deep nesting preserved
    edge-to-edge/
      SKILL.md
```

### android-migrations (v0.1.0)
```
plugins/android-migrations/
  .claude-plugin/plugin.json
  CLAUDE.md
  skills/
    migrate-xml-views-to-compose/
      SKILL.md
      references/
    agp-9-upgrade/
      SKILL.md
    play-billing-upgrade/
      SKILL.md
      references/
```

### android-performance (v0.1.0)
```
plugins/android-performance/
  .claude-plugin/plugin.json
  CLAUDE.md
  skills/
    r8-analyzer/
      SKILL.md
      references/
```

### android-sync (v0.1.0)
```
plugins/android-sync/
  .claude-plugin/plugin.json
  skills/
    update/
      SKILL.md                     # user-invocable: /android-sync:update
  agents/
    upstream-diff-analyzer.md      # Sonnet, read-only (Read, Bash)
  scripts/
    sync-upstream.py               # детерминистичная логика sync
    port-skill.py                  # первичный порт одного скилла
```

---

## Конвенция портирования скиллов

### Что меняется, что сохраняется

| Часть SKILL.md | При портировании | При sync |
|---|---|---|
| Frontmatter — `name`, `description`, `upstream.source/path/license` | ставится вручную | не трогается |
| Frontmatter — `upstream.commit` | ставится из upstream HEAD на момент порта | **обновляется** на новый SHA |
| Body (всё после второго `---`) | копируется as-is | перезаписывается из апстрима |
| `references/` | копируется as-is | rsync из апстрима (удаление orphans) |

### Трансформация frontmatter

**Апстрим (agentskills.io):**
```yaml
---
name: migrate-xml-views-to-jetpack-compose
description: Provides a structured workflow for migrating an Android XML View
  to Jetpack Compose. ... Use this skill when you need to migrate an XML View
  to Jetpack Compose in an Android project.
license: Complete terms in LICENSE.txt
metadata:
  author: Google LLC
  keywords: [Jetpack Compose, migration, XML, Views, ...]
---
```

**Наш (Claude Code):**
```yaml
---
name: migrate-xml-views-to-compose
description: >
  This skill should be used when the user asks to "migrate XML to Compose",
  "convert XML views to Jetpack Compose", "migrate legacy Views",
  "adopt Compose incrementally", or mentions XML-to-Compose migration,
  Compose interop with Views, or replacing XML layouts with Compose.
upstream:
  source: android/skills
  path: jetpack-compose/migration/migrate-xml-views-to-jetpack-compose
  commit: <sha-from-last-sync>
  license: Apache-2.0
---

> Adapted from [android/skills](https://github.com/android/skills) (Apache 2.0).
> See [NOTICE.md](../../../../NOTICE.md).

<!-- Body остаётся как у апстрима, без изменений -->
```

**Правила трансформации:**

1. **`name`** — короткий, без провайдер-префикса. `migrate-xml-views-to-compose` вместо `migrate-xml-views-to-jetpack-compose`. Скилл живёт в `android-migrations`, префикс Jetpack — шум.
2. **`description`** — переписывается под CC-auto-triggering:
   - Third-person: «This skill should be used when…» (а не «Use this skill when…»).
   - 4-6 конкретных trigger phrases в кавычках.
   - Слегка агрессивнее чем апстрим (Claude undertriggers).
   - Минимум 50 символов.
3. **`upstream`** — новый блок:
   - `source` — всегда `android/skills`.
   - `path` — путь относительно корня апстрима.
   - `commit` — SHA commit'а, с которого портировано/синхронизировано. Ключевой enabler для sync (позволяет показать точный diff).
   - `license` — канонический SPDX `Apache-2.0` вместо фразы «Complete terms in LICENSE.txt».
4. **`metadata.author` / `metadata.keywords`** — удаляются (CC не использует).
5. **Attribution pointer** — первая строка body, под `---` frontmatter. Относительная ссылка на `NOTICE.md` из `plugins/<plugin>/skills/<skill>/SKILL.md` → `../../../../NOTICE.md`.

### Сохранение вложенности `references/`

Структура апстрима использует глубокую вложенность, отражающую URL-путь developer.android.com:
```
references/android/guide/navigation/navigation-3/recipes/basic.md
```

Не плющим — тело SKILL.md ссылается на эти пути, и flatten потребовал бы rewrite тела (а договорились тело не трогать).

CC-плагин-система поддерживает произвольную вложенность под `skills/*/references/**` — только файлы не автодискаверятся, что нам и нужно.

---

## NOTICE.md — источник правды для sync

В корне маркетплейса. Содержит таблицу всех портированных скиллов с last-synced commit.

```markdown
# NOTICE

This marketplace contains skills adapted from [android/skills]
(https://github.com/android/skills) under the Apache License 2.0.

## Ported skills

| Plugin | Skill | Upstream path | Last synced commit |
|---|---|---|---|
| android-core | navigation-3 | navigation/navigation-3/ | <sha> |
| android-core | edge-to-edge | system/edge-to-edge/ | <sha> |
| android-migrations | migrate-xml-views-to-compose | jetpack-compose/migration/migrate-xml-views-to-jetpack-compose/ | <sha> |
| android-migrations | agp-9-upgrade | build/agp/agp-9-upgrade/ | <sha> |
| android-migrations | play-billing-upgrade | play/play-billing-library-version-upgrade/ | <sha> |
| android-performance | r8-analyzer | performance/r8-analyzer/ | <sha> |

## Modifications from upstream

- Frontmatter переписан под Claude Code skill API (auto-trigger phrases).
- Layout адаптирован под плоскую структуру `skills/*/SKILL.md`.
- Body и references — без изменений.

Full license: LICENSE-upstream-android-skills.txt
```

**sync-скрипт использует эту таблицу** как источник соответствия наших скиллов ↔ апстрима, и сам обновляет колонку «Last synced commit» после успешного pull.

---

## Sync-плагин — детали

### Skill `/android-sync:update`

```yaml
---
name: update
description: >
  This skill should be used when the user asks to "update android skills",
  "sync android plugins", "pull upstream android skills", "обнови android
  плагины", or wants to refresh portable android/* plugins from upstream.
user-invocable: true
argument-hint: "[--dry-run] [--plugin <name>]"
allowed-tools: [Bash, Read, Edit]
---
```

Body короткий — делегирует в `sync-upstream.py` и `upstream-diff-analyzer` агент.

### Алгоритм `sync-upstream.py`

```
1. Locate marketplace root:
   walk up from ${CLAUDE_PLUGIN_ROOT} searching for .claude-plugin/marketplace.json.

2. Read NOTICE.md — parse ported-skills table
   (plugin, skill, upstream_path, last_commit).

3. Clone or update upstream:
   /tmp/android-skills-upstream/ — cached between runs.

4. Get upstream HEAD sha.

5. For each portable skill:
   a. If last_commit == upstream HEAD → skip (unchanged).
   b. Else:
      - Compute file-level diff for upstream_path between shas.
      - If body OR references changed:
        * Extract body from upstream SKILL.md (everything after second ---).
        * Replace body in our SKILL.md, preserving our frontmatter.
        * rsync references/ (with --delete for orphans).
        * Update upstream.commit in our frontmatter.
        * Mark plugin for version bump (minor if body; patch if only refs).

6. Write diff artifacts:
   /tmp/android-sync-run-<ts>/<skill>/diff.patch

7. Dispatch upstream-diff-analyzer agents in parallel for each changed skill.
   Agent output → /tmp/android-sync-run-<ts>/<skill>/changelog.md

8. Emit summary to stdout: changed skills, plugins needing bump, agent changelogs.

9. If --dry-run: stop (no writes applied).

10. Otherwise:
    - Bump plugin.json versions per rule above.
    - Update NOTICE.md commit shas.
    - Print next-step hint for manual git review + commit.
```

**Инварианты:**
- Из нашего frontmatter sync меняет ТОЛЬКО поле `upstream.commit`. Остальное (name, description, upstream.source/path/license) не трогается.
- sync не коммитит — только меняет рабочее дерево.
- Если git working tree not clean → abort (unless `--force`).
- Если скилл из NOTICE.md исчез в апстриме → warning, не удаление (может быть реорганизация).

### Агент `upstream-diff-analyzer`

```yaml
---
name: upstream-diff-analyzer
description: |
  Use this agent when a diff patch from android/skills upstream needs to be
  summarized into a human-readable changelog for a specific skill.

  <example>
  Context: /android-sync:update detected body changes in navigation-3
  user: (triggered by sync skill)
  assistant: "Launching upstream-diff-analyzer for navigation-3."
  <commentary>Sync flow delegates per-skill changelog to this agent.</commentary>
  </example>
model: sonnet
color: cyan
tools: [Read, Bash]
---

You are a changelog author specializing in Android skills documentation.

**Inputs:** path to diff patch, paths to old and new SKILL.md, upstream path.

**Output:** 3-8 markdown bullets describing what changed and why it matters to
an Android developer. Focus on semantic changes (new patterns, deprecations,
corrected guidance). Do NOT reference file names or diff mechanics.

**Style:** concise, technical, Android-specific jargon OK (Compose, Hilt,
backstack etc.).
```

Запуск агентов — параллельно (один агент на один изменённый скилл).

### Артефакты запуска

`/tmp/android-sync-run-<timestamp>/`:
- `upstream/` — клон апстрима (reused между запусками)
- `<skill>/diff.patch` — сырой git diff
- `<skill>/changelog.md` — вывод агента
- `summary.md` — итоговый отчёт для пользователя

### Безопасность

- Перед любой записью: `git status --porcelain` должен быть clean (или `--force`).
- Флаг `--plugin <name>` — sync только одного скилла (отладка).
- `--dry-run` — только анализ, без записи.

---

## Порядок сборки

Каждый шаг — отдельный commit.

**Шаг 1 — Маркетплейс-скелет.**
- `git init` (уже сделано), remote `git@github.com:DronPascal/claude-android-plugins.git`
- `.claude-plugin/marketplace.json` с `"plugins": []`
- `LICENSE-upstream-android-skills.txt` (копия Apache 2.0 из апстрима)
- `NOTICE.md` с пустой таблицей
- `README.md` — назначение + установка
- `.gitignore` (`/tmp/`, `*.pyc`, `.DS_Store`, `__pycache__/`)
- Commit: `chore: init marketplace skeleton`

**Шаг 2 — android-sync плагин.**
- Скелет плагина (`plugin.json`)
- `scripts/port-skill.py` (первичный порт одного скилла)
- `scripts/sync-upstream.py` (полный sync loop)
- `skills/update/SKILL.md` (user-invocable)
- `agents/upstream-diff-analyzer.md`
- Ручной smoke test: `python3 port-skill.py --upstream /tmp/android-skills-inspect --path navigation/navigation-3 --target-plugin android-core` — один скилл портируется корректно
- Commit: `feat(android-sync): port + sync scripts, skill, agent`

**Шаг 3 — android-core.**
- `plugin.json`, `CLAUDE.md`
- Порт `navigation-3` через `port-skill.py`
- Порт `edge-to-edge` через `port-skill.py`
- Ручной light rewrite description в обоих
- Обновление NOTICE.md (таблица)
- Обновление marketplace.json
- Commit: `feat(android-core): port navigation-3 and edge-to-edge`

**Шаг 4 — android-migrations.**
- `plugin.json`, `CLAUDE.md`
- Три скилла через `port-skill.py`
- Light rewrite description
- NOTICE + marketplace update
- Commit: `feat(android-migrations): port XML→Compose, AGP-9, Play Billing`

**Шаг 5 — android-performance.**
- `plugin.json`, `CLAUDE.md`
- Порт `r8-analyzer` через `port-skill.py`
- NOTICE + marketplace update
- Commit: `feat(android-performance): port r8-analyzer`

**Шаг 6 — Sync end-to-end тест.**
- `/android-sync:update --dry-run` → diff пустой
- Искусственно откатить один `upstream.commit` на предыдущий SHA → `update` → убедиться что тело+refs обновились, NOTICE актуализирован, агент написал changelog
- Fix если нужен

**Шаг 7 — Публикация.**
- `git push -u origin main`
- `/plugin marketplace add DronPascal/claude-android-plugins`
- Установка `android-core` и `android-sync` глобально (`~/.claude/settings.json`)
- `android-migrations` / `android-performance` — per-project

---

## Почему android-sync строится первым

`port-skill.py` содержит ту же логику трансформации frontmatter, что и sync. Если писать отдельный ручной скрипт для первичного портирования, а потом дублировать логику в sync — это два источника правды, которые разойдутся.

Строим `port-skill.py` → используем его для первичного портирования всех 6 скиллов → логика сразу боевым образом протестирована → `sync-upstream.py` переиспользует те же функции.

Light rewrite description делается **после** `port-skill.py` — скрипт ставит минимальный валидный description, руками дописываем CC-trigger phrases.

---

## Риски и митигации

| Риск | Митигация |
|---|---|
| Апстрим переименует/удалит скилл | sync пишет warning, не падает; ручная миграция через обновление NOTICE.md |
| Апстрим переделает frontmatter формат | тело у нас не зависит от frontmatter — sync работает; порядок извлечения body по `---` устойчив |
| Description после sync рассинхронится с новым телом | upstream-diff-analyzer упомянет, что тело сильно изменилось — триггер для ручного пересмотра description |
| CC не поддерживает deep nesting в references | По факту поддерживает — скилл-система читает только `SKILL.md`, остальные файлы — это просто data |
| `/plugin marketplace add` не работает с приватным repo | **Репо должен быть публичным** (подтверждено пользователем имплицитно через согласие на remote) |
| Два запуска sync одновременно → corrupted state | Лок-файл `/tmp/android-sync.lock` с PID-проверкой (crash-safe) |

---

## Открытые вопросы (не блокирующие)

1. **CI для маркетплейса.** Стоит ли добавить GitHub Action, запускающий sync еженедельно и открывающий PR? — Вынести в отдельную итерацию.
2. **Тесты для sync-скриптов.** Bash-тесты по паттерну insights-keeper? — В план шага 2 (со смоук-тестом) + отдельный commit с полным тест-сьютом позже.
3. **Совместимость версий.** Frontmatter `upstream.source_version: 1` на случай breaking changes в формате. — Пока не вводим, добавим если понадобится.

---

## Acceptance criteria

- [ ] 4 плагина установлены в CC (`/plugin list` показывает).
- [ ] `/android-sync:update --dry-run` работает без ошибок, diff пустой сразу после первичного портирования.
- [ ] Искусственный rollback `upstream.commit` → `update` корректно обновляет тело + refs + NOTICE + bumpает версию.
- [ ] Все 6 скиллов триггерятся на релевантных запросах (ручной тест: 3-4 реалистичных промпта на каждый).
- [ ] NOTICE.md отражает все портированные скиллы с актуальными SHA.
- [ ] Публичный репо `DronPascal/claude-android-plugins` доступен для `/plugin marketplace add`.
