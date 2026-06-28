---
name: r8-analyzer
description: >
  This skill should be used when the user asks about "R8 analyzer",
  "R8 configuration analyzer", "shrinking report", "analyze R8 output",
  "minification issues", "keep rules", "evaluate keep rules",
  "keep rule blast radius", "optimization/obfuscation/shrinking score",
  "quantitative R8 analysis", "ProGuard rules debugging", "R8 diagnostics",
  or mentions missing classes in release builds, shrinker warnings,
  R8 configuration analyzer metrics, or investigating app size regressions.
upstream:
  source: android/skills
  path: performance/r8-analyzer
  commit: 07302ca15e21d827cab5ca64d46407fb51dbe0aa
  license: Apache-2.0
---

> Adapted from [android/skills](https://github.com/android/skills) (Apache 2.0).
> See [../../../../NOTICE.md](../../../../NOTICE.md).


## Step 1. Setup and configuration check

- Inspect `build.gradle`, `build.gradle.kts`, and `gradle.properties`.
- Use [references/CONFIGURATION.md](references/CONFIGURATION.md) to identify missing optimizations.
- **AGP** : If \< 9.0, suggest migration to 9.0 for [build time improvement
  performance](references/android/topic/performance/app-optimization/enable-app-optimization.md)
- **Full Mode** : Verify `android.enableR8.fullMode=false` is removed from gradle.properties.

## Step 2. Analysis path selection

- Inspect `build.gradle`, `build.gradle.kts`, and `gradle.properties` and
  `libs.versions.toml` to get the R8 version

- **If R8 \>= 9.3.7-dev** : Proceed to **Path A (Quantitative)**.

- **If R8 \< 9.3.7-dev** : Proceed to **Path B (Heuristic)**.

### Path A: Quantitative data generation (R8 \>= 9.3.7-dev)

- **Check requirements** : Python and `protobuf` package are mandatory.
- **Generate and analyze** : You MUST run the shell commands described in [references/CONFIGURATION-ANALYZER.md](references/CONFIGURATION-ANALYZER.md) to generate the proto file using R8 configuration analyzer, convert it to json and analyze the result.
- **Report** : Rely entirely on the generated file `analysis.txt` for scores and rule impact metrics. Proceed to Step 3.

### Path B: Heuristic evaluation and recommendation (R8 \< 9.3.7-dev)

*(Use ONLY if quantitative data generation is not possible)*

- **Manual evaluation** : Inspect `proguard-rules.pro`.
- **Library check** : Compare rules against [references/REDUNDANT-RULES.md](references/REDUNDANT-RULES.md). Suggest **Remove** for bundled rules.
- **Custom rule check** : Use [references/KEEP-RULES-IMPACT-HIERARCHY.md](references/KEEP-RULES-IMPACT-HIERARCHY.md) and [references/REFLECTION-GUIDE.md](references/REFLECTION-GUIDE.md) to prioritize and evaluate. Suggest **Refine** for broad rules (for example, package-wide).
- **Validation** : Suggest Macrobenchmark tests using [UI Automator](references/android/training/testing/other-components/ui-automator.md) for any proposed changes. Proceed to Step 3.

## Step 3. Report generation

- **Format** : Follow [references/REPORT_FORMAT.md](references/REPORT_FORMAT.md) strictly.
- **Input**: Extract metrics (Scores, Impacts, Example Classes) directly from generated file analysis.txt if using Path A, or from manual findings if using Path B.
- **Output** : Output ONLY the raw Markdown report in the chat. Do NOT output conversational filler (for example, "Here is your report..."). Do NOT provide recommendations, next steps, or any other text outside of the sections defined in [references/REPORT_FORMAT.md](references/REPORT_FORMAT.md) Do NOT mention the path used for analysis of the configuration

## Constraints

- **Strict output limit**: The final output MUST strictly be the Markdown report and nothing else.
- **No code changes**: Research and suggest only; Do not modify files.
- **No redundancy**: Do not explain R8 benefits or reference skill internal files in the report.
- **Focus**: Omit sections (for example, Subsumed Rules, Configuration) if no issues or items are found.
