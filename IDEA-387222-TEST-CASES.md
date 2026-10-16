# IDEA-387222 — QA Test Cases

**Issue:** [IDEA-387222 — Spring Boot: revise collecting config files for placeholder references](https://youtrack.jetbrains.com/issue/IDEA-387222)
**Type:** Bug · **State:** Fixed · **Verified:** In Progress · **Subsystem:** Spring. Boot. Configuration · **Planned for:** 2026.3
**Fix commit:** `07a6a90f71e0e8615c9a7db09ce6ef618182367a` (master, 271.x, 2026-10-07) "IDEA-387222 use test config files for placeholders only in test sources" · review 227337
**Earlier quickfix:** `1352dd5a3f989` (2026-03-18) "IDEA-387222: quickfix, de-duplicate results", in 262 and 263, not in 261
**Included in builds (YouTrack, 2026-10-16):** `262.2213`, `262.9437.274`, `271.117` · **Backport to 263:** review reopened on 2026-10-13, not merged on 2026-10-16
**Related:** IDEA-311513 (regression source, 2023) · IDEA-394315 (follow-up `SpringCommonUtils.isInTestSources()`, master only, needed for TC-07)
**Plan:** `temp.md` (agent handoff, 2026-10-16). This file implements section 8, steps 1, 2, 3 and 5. Step 4 is open: every IDE cell is "not run".
**Runtime oracle:** [`runtime-oracle.txt`](runtime-oracle.txt), written by `oracle.py` · **Prepared:** 2026-10-16
**Projects:** `gradle-project/`, `maven-project/`, `maven-single-module/` in `~/qa/IDEA-387222/`. This file is the same in all three.

---

## 1. Summary

### The defect
A `${key}` placeholder in production code (`@Value`, Kotlin string, config file value) resolved to, completed from,
and folded values from `src/test/resources`. IDEA-311513 (2023) removed the test-sources check from
`SpringBootPlaceholderReference.findConfigFiles`. Since then the method included the test scope for the module of the
reference and for every module that depends on it. In Gradle that walk also visits `app.test`, which returns the
resource roots of `app.main` again, so the files of `main` came twice (the March quickfix removed the duplicates, the
order stayed unstable). In a Maven module, the fallback in `multiResolve` searched the whole module content scope,
test resources included.

### The rule being verified
The developer's comment on the issue (2026-10-06):

> How to check it in the IDE:
> - Gradle: put my.key only in src/test/resources/application.properties or .yml.
>   - @Value("${my.key}") in src/main/java should not resolve, complete or fold.
>   - The same placeholder in src/test/java should still work.
>
> Single Maven module: foo=${my.key} in src/main/resources/application.properties should not resolve.

So the fixed IDE must:
* **resolve production code against `src/main/resources` only**: NC-01 to NC-05, TC-01 to TC-03, TC-12, RL-01, RL-02;
* **keep the test config for test code, test files first**: TC-04 to TC-07, TC-09, TC-13, TC-14, RL-03;
* **keep IDEA-311513**: library code still resolves against the config of the application (TC-08).

### Interpretation
The runtime is the ground truth (§3.3). A key that is absent at runtime but has an IDE target, a completion item, or a
fold in production code ⇒ IDE leak. In test code the IDE is more permissive than the runtime by design of the fix (R2);
XP-06 records that outside the verdict.

---

## 2. Runtime findings that correct `temp.md`

`temp.md` section 8 step 2 says not to change a key or a marker, so the corrections are recorded here. Every row is
backed by `runtime-oracle.txt` (probe runs P1 to P13, see §3.3).

| # | `temp.md` says | Spring Boot 4.0.0 does | What changed here |
|---|---|---|---|
| R1 | 5.6: "The test classpath sees the test config, the imported file, and the main config." `./gradlew test` and `mvn -q test` must pass | The test classpath has two copies of `application.properties` and two of `application.yml` (P3, P9). Boot reads only the first copy of a name: the test copy. Keys that only the main copies define (`main.only.property`, `yaml.main-only`) are **absent in tests**. The test context fails while it creates the bean `mainService`: `Could not resolve placeholder 'main.only.property'`. Gradle `:app` fails 4 of 4, Maven `app` 3 of 3. Both `lib` modules and the single module pass | Nothing in the projects: green tests need a key or a layout change. The runtime truth of each row comes from the probe (§3.3). The Runtime row of the report says "tests fail (R1)" |
| R2 | TC-02T: "Test code keeps the main config." TC-04 and TC-06: NAV ends with the main file. TC-13: NAV main file | Test code never reads the main copy of a file name that `src/test/resources` also has: `main.only.property` is absent and `test.url=${main.only.property}/path` is unresolvable in tests (P3, P9) | IDE expectations unchanged: the fix and `SpringBootPlaceholderReferenceTestScopeTestCase` define the test scope as the test files first, then the main files. The Runtime column marks the difference. New candidate XP-06 |
| R3 | 5.1: the `integrationTest` context "fails on `test.only.property`" | A third copy of `application.properties` (`src/integrationTest/resources`) shadows the main copy, so `my.property` and `main.only.property` are absent there too (P5) | The task is still not run. P5 is the runtime truth of XP-03 |
| R4 | Sections 1 and 10: the issue text was unreadable; compare the reporter's layout with section 5 | Read on 2026-10-16 (read only). The developer's check (§1) uses a **single** Maven module. Section 5.2 is a reactor. The Gradle part of the check matches NC-01, NC-02, TC-05, TC-05Y | New project `maven-single-module/` with rows RL-01 to RL-03. The verdict rule includes them |

Other changes, without contradicting `temp.md`:
- Gradle wrapper `9.8.1` instead of `9.1.0`. Section 5.1 allows the newest 9.x; 9.8.1 is the newest 9.x in the
  local Gradle cache and the version start.spring.io generated on 2026-10-16. Gradle 9.6+ deprecates `by project` and `by sourceSets.creating`: warnings
  only, the build scripts are unchanged.
- All version pins resolved as written (§3.1). Nothing was bumped.
- `MainApplication` ran from the command line on the production runtime classpath of `app` (`oracle.py`), not from
  the IDE. The classpath is the one of an IDE run of `app.main`.
- `.gitignore` in every project; `.gitattributes` in `gradle-project` keeps `gradlew` LF.
- Outside the projects: `gen.py` (generator), `oracle.py` (runtime oracle), `probe/RuntimeProbe.java`,
  `probe/classpath.init.gradle`.

---

## 3. Projects under test

### 3.1 Build

| Item | Value (resolved on 2026-10-16) |
|---|---|
| Spring Boot | `4.0.0` (Spring Framework `7.0.1`). Gradle: `spring-boot-dependencies` platform; Maven: `spring-boot-starter-parent` |
| Kotlin | `2.2.20` (`gradle-project` only) |
| Gradle | wrapper `9.8.1`, Kotlin DSL |
| Maven | `3.9.6`, Surefire `3.5.4` (from the Boot parent) |
| JDK | toolchain 21; the oracle ran on Corretto `21.0.3` |

### 3.2 Layout

`[marker]` = the rows whose placeholder sits in the file. Section 5 of `temp.md` has the full file contents;
`gen.py` writes them. The IDE module names are the expected import result (not yet imported; the Gradle names carry
the prefix `idea-387222.`).

```
~/qa/IDEA-387222/
├── gen.py · oracle.py · runtime-oracle.txt · probe/ (RuntimeProbe.java, classpath.init.gradle)
├── gradle-project/                 IDE modules: idea-387222, app, app.main, app.test, app.integrationTest, lib, lib.main, lib.test
│   ├── settings.gradle.kts · build.gradle.kts · gradle.properties (springBootVersion=4.0.0) · gradlew
│   ├── lib/                        java-library + kotlin("jvm")
│   │   ├── src/main/java/demo/lib/LibService.java                [TC-08 NC-04 NC-05 XP-01]
│   │   ├── src/test/java/demo/lib/LibServiceTest.java            [TC-09 XP-02]
│   │   └── src/test/resources/application.properties             lib.test.only=lib-test
│   └── app/                        java + idea + kotlin("jvm"); source set integrationTest; XP-03b block commented out
│       ├── src/main/java/demo/MainApplication.java · MainService.java   [TC-01 TC-02 TC-03 NC-01 NC-02 NC-03 XP-01 XP-03]
│       ├── src/main/kotlin/demo/MainKotlinService.kt                    [TC-01K NC-01K]
│       ├── src/main/resources/application.properties             my.property=main, main.only.property, main.url [TC-12]
│       ├── src/main/resources/application-dev.properties · application.yml (yaml.property, yaml.main-only)
│       ├── src/test/java/demo/MainServiceTest.java               [TC-04 TC-05 TC-05Y TC-14 TC-02T]
│       ├── src/test/java/demo/ProfiledTest.java · PropertiesAttributeTest.java   [TC-06] · [TC-07]
│       ├── src/test/kotlin/demo/MainKotlinServiceTest.kt         [TC-05K]
│       ├── src/test/resources/application.properties             my.property=test, test.only.property, test.url [TC-13], spring.config.import [TC-14]
│       ├── src/test/resources/application-test.properties · application.yml (yaml.test-only) · extra-config.properties · extra.properties [XP-01]
│       ├── src/integrationTest/java/demo/IntegrationSmokeTest.java   [XP-03]
│       └── src/integrationTest/resources/application.properties  integration.only.property=it
├── maven-project/                  IDE modules: idea-387222 (pom, no sources), lib, app; app depends on lib
│   └── lib/ and app/ as above, without Kotlin and without integrationTest
└── maven-single-module/            IDE module: idea-387222-single (the developer's check)
    ├── src/main/java/demo/single/SingleApplication.java · SingleService.java   [RL-02]
    ├── src/main/resources/application.properties                 foo=${my.key} [RL-01]
    ├── src/test/java/demo/single/SingleServiceTest.java          [RL-03]
    └── src/test/resources/application.properties                 my.key=test-value
```

### 3.3 Runtime model

What Spring Boot itself resolves on each classpath, from `runtime-oracle.txt`. The probe starts a `SpringApplication`
without component scan, so no bean of the project fails first. Probe runs: P1 Gradle `app` production · P2 P1 with
profile `test` · P3 Gradle `app` tests · P4 P3 with profile `test` (as `@ActiveProfiles("test")`) · P5 Gradle
`app` integrationTest · P6 Gradle `lib` tests · P7 to P11 the same for `maven-project` (P7 production, P8 + profile,
P9 tests, P10 + profile, P11 `lib` tests) · P12 single module production · P13 single module tests.

**Bold**: the runtime differs from what `temp.md` assumed (R1). `LibService` has no config of its own at runtime; it
runs inside the application, so its production column is P1 and P7.

| Key | Defined in | Production (P1, P7) | Production, profile `test` (P2, P8) | `app` tests (P3, P9) | `app` tests, profile `test` (P4, P10) | `lib` tests (P6, P11) | `integrationTest` (P5) |
|---|---|---|---|---|---|---|---|
| `my.property` | main `application.properties` (`main`), test `application.properties` (`test`), `application-test.properties` (`test-profile`), `application-dev.properties` (`main-dev`) | `main` | `main` | `test` | `test-profile` | absent | **absent** |
| `main.only.property` | main `application.properties` | `main-only` | `main-only` | **absent** | **absent** | absent | absent |
| `main.url` | main `application.properties`: `${test.only.property}/path` | unresolvable | unresolvable | absent | absent | absent | absent |
| `yaml.property` | main `application.yml` (`main-yaml`), test `application.yml` (`test-yaml`) | `main-yaml` | `main-yaml` | `test-yaml` | `test-yaml` | absent | `main-yaml` |
| `yaml.main-only` | main `application.yml` | `main-yaml-only` | `main-yaml-only` | **absent** | **absent** | absent | `main-yaml-only` |
| `test.only.property` | test `application.properties` | absent | absent | `test-only` | `test-only` | absent | absent |
| `test.url` | test `application.properties`: `${main.only.property}/path` | absent | absent | **unresolvable** | **unresolvable** | absent | absent |
| `yaml.test-only` | test `application.yml` | absent | absent | `test-yaml-only` | `test-yaml-only` | absent | absent |
| `imported.test.property` | test `extra-config.properties`, imported by the test config | absent | absent | `imported` | `imported` | absent | absent |
| `extra.key` | test `extra.properties` (not a Boot config file) | absent | absent | absent | absent | absent | absent |
| `lib.test.only` | `lib/src/test/resources/application.properties` | absent | absent | absent | absent | `lib-test` | absent |
| `integration.only.property` | `app/src/integrationTest/resources/application.properties` | absent | absent | absent | absent | absent | `it` |

Single module: `my.key` is absent in production (P12) and `test-value` in tests (P13). `foo=${my.key}` is unresolvable
in production; in tests the main copy is shadowed, so `foo` is absent.

---

## 4. Environment and procedure

| Item | Value |
|---|---|
| Fixed build | IntelliJ IDEA Ultimate 2027.1 (271.x) built after 2026-10-07; the YouTrack field "Included in builds" lists `271.117`. This machine runs `271.676` (from `idea.log`). TC-07 also needs IDEA-394315 (master after 2026-10-13): check the build date in *Help → About* |
| Baseline B | 2026.2.x (262) or 2026.3 EAP (263) without the backport. Before a 263 run, check that the backport is still unmerged: `git log origin/263 --grep='use test config files for placeholders'` in `ultimate`, or the review timeline |
| Baseline A | 2026.1.x (261), optional: shows the Gradle duplicates |
| Plugins | Spring, Spring Boot, Gradle, Maven, Kotlin, Properties, YAML: enabled |
| Folding | Defaults (*Settings → Editor → General → Code Folding*). The placeholder folding follows the Java "I18n messages" switch |
| JDK | 21 for the Gradle JVM and the Maven runner |
| Import | One IDE window per project: open `gradle-project/settings.gradle.kts`, `maven-project/pom.xml`, `maven-single-module/pom.xml`. Wait for sync and indexing. Same projects and machine for every build |

How to observe, per row, in this order:
- **NAV**: caret on the key, *Go to Declaration* (`Ctrl+B` / `⌘B`). Record the target file(s). More than one target
  opens a chooser: record every entry, its order, and whether an entry repeats.
- **CMP**: delete the key, leave the caret between `${` and `}`, *Basic Completion* (`Ctrl+Space` / `⌃Space`). Record
  the key list and the file column. Undo.
- **FOLD**: read the folded text of the annotation value (the IDE shows the value instead of `${key}`). If the region
  is expanded, use *Collapse All* (`Ctrl+Shift+-` / `⌘⇧-`) or hover.
- **HL**: record the highlighting of the key (none, weak warning, warning, error) and the message. The text is not
  verified here; do not fail a row on the message alone.
- TC-04 order is strict (`assertOrderedEquals`): the test file first, because the test classpath wins at runtime.

---

## 5. Test cases

`TC` = positive, the placeholder must resolve. `NC` = negative, it must not resolve to a test file. `RL` = the
developer's check (R4). Layout "both" = `gradle-project` and `maven-project`; "single" = `maven-single-module`.
The Runtime column is the ground truth from §3.3.

| ID | Layout | File / key | Runtime (§3.3) | Fixed build | Baseline B (262, 263) | Baseline A (261) |
|---|---|---|---|---|---|---|
| TC-01 | both | `MainService` / `my.property` | `main` (P1, P7) | NAV: `app/src/main/resources/application.properties` only. CMP: `my.property`, `main.only.property`, `main.url`, `yaml.property`, `yaml.main-only`; no `test.*`, no `yaml.test-only`, no `imported.*`. FOLD: `main`. | NAV: main and test file. CMP has `test.only.property`. FOLD: `main` or `test`, order unstable. | As B, plus duplicate rows (Gradle). |
| TC-01K | Gradle | `MainKotlinService` / `my.property` | `main` (P1) | As TC-01. | As TC-01. | As TC-01. |
| TC-02 | both | `MainService` / `main.only.property` | `main-only` (P1, P7) | NAV: main file. FOLD: `main-only`. | Same. | Same. |
| TC-02T | both | `MainServiceTest` / `main.only.property` | **absent**: the test copy of `application.properties` shadows the main copy (P3, P9; R1, R2) | NAV: main file. FOLD: `main-only`. Test code keeps the main config. | Same. | Same. |
| TC-03 | both | `MainService` / `yaml.property` | `main-yaml` (P1, P7) | NAV: `app/src/main/resources/application.yml` only. FOLD: `main-yaml`. | NAV: main and test YAML. FOLD unstable. | As B, plus duplicates. |
| TC-04 | both | `MainServiceTest` / `my.property` | `test`, from the test file only; the main copy is shadowed (P3, P9; R2) | NAV: two targets, the test file first, then the main file. CMP: keys of both scopes; `my.property` appears twice with two different files. FOLD: `test`. | Same set. Order unstable. | Duplicates of the same file (Gradle). |
| TC-05 | both | `MainServiceTest` / `test.only.property` | `test-only` (P3, P9) | NAV: test file. FOLD: `test-only`. | Same. | Same. |
| TC-05Y | both | `MainServiceTest` / `yaml.test-only` | `test-yaml-only` (P3, P9) | NAV: test YAML. FOLD: `test-yaml-only`. | Same. | Same. |
| TC-05K | Gradle | `MainKotlinServiceTest` / `test.only.property` | `test-only` (P3) | NAV: test file. FOLD: `test-only`. | Same. | Same. |
| TC-06 | both | `ProfiledTest` / `my.property` | `test-profile` from `application-test.properties` (P4, P10); main copy shadowed (R2) | FOLD: `test-profile` (the `@ActiveProfiles("test")` of the class picks `application-test.properties` from the test resources). NAV lists the test file, the profile file, and the main file. | FOLD: `test-profile`. | Same. |
| TC-07 | both | `PropertiesAttributeTest` / `test.only.property` inside `properties = "demo.injected=${...}"` | `test.only.property` = `test-only`, `my.property` = `test` (P3, P9) | CMP offers `test.only.property` and `my.property` from the test file. Needs IDEA-394315 (master after 2026-10-13). On a 263 backport build, record the result; a miss is IDEA-394315, not this issue. | CMP offers the keys (the test scope was always on). | Same. |
| TC-08 | both | `LibService` / `my.property` | `main`: `LibService` runs in the application (P1, P7) | NAV: `app/src/main/resources/application.properties` only (IDEA-311513: a library resolves against the application). FOLD: `main`. | NAV: app main and app test files. | Plus duplicates. |
| TC-09 | both | `LibServiceTest` / `lib.test.only` | `lib-test` (P6, P11) | NAV: `lib/src/test/resources/application.properties`. FOLD: `lib-test`. | Same. | Same. |
| TC-12 | both | `app/src/main/resources/application.properties` / `${test.only.property}` in `main.url` | `main.url` unresolvable: `Could not resolve placeholder 'test.only.property'` (P1, P7) | NAV: no target. CMP inside `${}`: main keys only. HL: record. | NAV: test file. | Same as B. |
| TC-13 | both | `app/src/test/resources/application.properties` / `${main.only.property}` in `test.url` | **`test.url` unresolvable**: `Could not resolve placeholder 'main.only.property'` (P3, P9; R2) | NAV: main file. | Same. | Same. |
| TC-14 | both | `MainServiceTest` / `imported.test.property` | `imported` from `extra-config.properties` (P3, P9) | NAV: `extra-config.properties` (reached through `spring.config.import` of the test config). FOLD: `imported`. | Same. | Same. |
| NC-01 | both | `MainService` / `test.only.property` | absent; `MainApplication` fails on it (§7) | NAV: no target ("Cannot find declaration to go to"). CMP: key absent. FOLD: no fold. HL: record. See XP-01 for a Gradle fold. | NAV: test file. FOLD: `test-only`. | Same as B. |
| NC-01K | Gradle | `MainKotlinService` / `test.only.property` | absent (P1) | As NC-01. | As NC-01. | As NC-01. |
| NC-02 | both | `MainService` / `yaml.test-only` | absent (P1, P7) | NAV: no target. CMP: absent. FOLD: no fold or the default `none`. | NAV: test YAML. | Same as B. |
| NC-03 | both | `MainService` / `imported.test.property` | absent (P1, P7) | NAV: no target. The import of the test config stays in the test scope. | NAV: `extra-config.properties`. | Same as B. |
| NC-04 | both | `LibService` / `test.only.property` | absent (P1, P7) | NAV: no target. The app test config is not visible from library production code. | NAV: app test file. | Same as B. |
| NC-05 | both | `LibService` / `lib.test.only` | absent (P1, P7) | NAV: no target. | NAV: lib test file. | Same as B. |
| RL-01 | single | `src/main/resources/application.properties` / `${my.key}` in `foo` | `foo` unresolvable: `Could not resolve placeholder 'my.key'` (P12) | NAV: no target. CMP inside `${}`: no `my.key`. HL: record. | NAV: test file (the module content scope contains the test resources). | Same as B. |
| RL-02 | single | `SingleService` / `my.key` | absent; `SingleApplication` fails on it (§7) | NAV: no target. CMP: absent. FOLD: no fold. HL: record. | NAV: test file. FOLD: `test-value`. | Same as B. |
| RL-03 | single | `SingleServiceTest` / `my.key` | `test-value` (P13); `mvn test` passes | NAV: test file. FOLD: `test-value`. | Same. | Same. |

---

## 6. Candidate problems the fix does not cover

Probe each one on the fixed build and record the evidence (screenshot or the exact NAV, CMP, FOLD results). These are
hypotheses from the source; the fixed build decides. A reproduced XP-01 or XP-02 is a new issue, not a reopen of
IDEA-387222.

| ID | Layout | Hypothesis | Evidence in the source | How to probe | Runtime (§3.3) |
|---|---|---|---|---|---|
| XP-01 | Gradle (both modules), Maven `lib` only | **Folding in production code still shows a test value.** `PlaceholderPropertyReference.getFoldingValue()` asks the Boot resolvers first (fixed), then the Spring model, then a fallback over every `.properties` file in `getScope(module)`. That scope unites `module.getModuleWithDependenciesAndLibrariesScope(false)` with `getModuleScope()` of each dependent module. `Module.getModuleScope()` includes the test roots. In Gradle, `app.test` depends on `app.main`, so the scope of `app.main` gains `app/src/test/resources`. In Maven, `app` depends on `lib`, so `lib` gains the test resources of `app`; the single module `app` has no dependents and is clean. | `PlaceholderPropertyReference.java:455-484` and `:527-539`; `Module.java:107-111`. The folding builder `XmlPropertyPlaceholderFoldingBuilder.java:95-108` folds without a resolve check. | On the fixed build, in the Gradle `MainService`: NC-01 NAV has no target, but FOLD shows `test-only`. Same for `extra.key` (FOLD `from-test-extra`, the file is not a Boot config file). In Maven, `LibService` / `test.only.property` folds to `test-only`, while `MainService` does not. A fold without a NAV target is the defect. | `test.only.property` and `extra.key` absent in production (P1, P7) |
| XP-02 | Maven | **Test code in `lib` sees the test config of `app`.** `findConfigFiles` applies `includeTestScope = true` to every dependent module, not only to the module of the reference. In Maven the dependents of `lib` include `app`, so `lib/src/test` reads `app/src/test/resources`. At runtime the tests of `lib` do not have the resources of `app` on the classpath. Gradle is not affected, because no module depends on `lib.test`. | `SpringBootPlaceholderReference.java:192-207` | `LibServiceTest` / `test.only.property`: Gradle: NAV no target (correct). Maven: NAV `app/src/test/resources/application.properties` (leak). | `test.only.property` absent in `lib` tests (P6, P11) |
| XP-03 | Gradle | **A custom source set that the IDE does not mark as tests leaks into production.** The fix trusts `TestSourcesFilter.isTestSources`. A hand-made source set `integrationTest` without the `idea.module.testSources` block may import as production roots. Then `integration.only.property` is a production key for the IDE. A limitation, not a defect of the fix, but on record. | `SpringBootPlaceholderReference.java:199` | XP-03a: default import. *Project Structure → Modules → `app.integrationTest`*: are the roots green (Tests)? Then `MainService` / `integration.only.property`: NAV target or not. XP-03b: uncomment the `idea { module { ... } }` block, reload Gradle, repeat. Expected after 03b: no target from `MainService`; a target from `IntegrationSmokeTest`. | `integration.only.property` = `it` only on the integrationTest classpath (P5); absent in production (P1) |
| XP-04 | both | **Production code with an active profile named like a test profile.** Set the active profile `test` for `app` (Spring tool window or the "Change active Spring profiles" action). `MainService` / `my.property` FOLD must stay `main`, because `application-test.properties` lives only in the test resources. The profile lookup uses `guessActiveProfiles(module)`, which reads the facet file set. | `SpringBootApplicationPropertiesPlaceholderReferenceResolver.java:197-232` | FOLD `main`: pass. FOLD `test-profile`: leak through the profile files. Reset the profile afterwards. | `my.property` = `main` in production with profile `test` (P2, P8) |
| XP-05 | both | **Find Usages from a test config key shows the production usages.** From `test.only.property` in `app/src/test/resources/application.properties`, *Find Usages* (`Alt+F7` / `⌥F7`) should list `MainServiceTest` and `PropertiesAttributeTest`. Whether it also lists `MainService` depends on the reference resolve, which the fix changed. A listing of `MainService` means the usage search uses another scope than the resolve. | `SpringBootConfigFileUsageTypeProvider.java:68` passes `true` for the test scope. | Record the usage list. Not a defect by itself; report as an inconsistency if `MainService` appears while NC-01 has no NAV target. | `test.only.property` exists for test code only (P1, P3) |
| XP-06 | both | *New (R2).* **Test code resolves to main config files that the test runtime never reads.** The fix keeps the main files in the test scope, after the test files. At runtime, a test copy of `application.properties` or `application.yml` shadows the main copy, so the keys of the main copy are not visible in tests. By design of the fix, not a defect of IDEA-387222. | `findConfigFiles(reference)` for a test reference: the test files, then the main files (`temp.md` section 3); `SpringBootPlaceholderReferenceTestScopeTestCase` asserts that order. | Read TC-02T, TC-04 (second target), TC-06 (main file in NAV), and TC-13 on the fixed build. Reproduced = the IDE resolves to the main copy of a file name that `src/test/resources` also has. Report separately, only if you decide it matters. | `main.only.property`, `yaml.main-only` absent and `test.url` unresolvable in tests (P3, P9) |

If XP-01 reproduces, it is the most important finding: the issue title says "folded", and the folding path still has
a scope without the fix.

---

## 7. Runtime cross-check

```bash
cd ~/qa/IDEA-387222
python -I oracle.py     # JAVA_HOME = JDK 21, mvn on the PATH; ~3 minutes; writes runtime-oracle.txt
```

The script runs `gradlew test`, `mvn -q test` (both Maven projects), the application class on the production
classpath, and the probe P1 to P13. It never runs the `integrationTest` task.

Observed on 2026-10-16 (Corretto 21.0.3):

| Check | `gradle-project` | `maven-project` | `maven-single-module` |
|---|---|---|---|
| Tests | `:lib` PASS. `:app` FAIL 4 of 4: `MainServiceTest`, `ProfiledTest`, `PropertiesAttributeTest`: `Could not resolve placeholder 'main.only.property'`; `MainKotlinServiceTest`: `failure threshold (1) exceeded` (same context) | `lib` PASS. `app` FAIL 3 of 3, same message | `SingleServiceTest` PASS |
| Application class, production classpath | `MainApplication` exit 1: `Could not resolve placeholder 'test.only.property' in value "${test.only.property}"` | same | `SingleApplication` exit 1: `Could not resolve placeholder 'my.key' in value "${my.key}"` |

Interpretation: production code does not see `src/test/resources`, as `temp.md` says, and the IDE must agree after the
fix. Test code sees the test config and its import, but not the main copy of a shadowed file name (R1).

---

## 8. Results matrix

The report template of `temp.md` section 9, expanded. One line per row, project, and build. Status: pass, fail,
or not run. For XP rows: reproduced or not reproduced. XP-05: write the usage list into NAV.

**IDE build:** `__________` · **Date:** `__________` · **Tester:** `__________`

| ID | Project | Build | NAV | CMP | FOLD | HL | Status |
|---|---|---|---|---|---|---|---|
| TC-01 | gradle | baseline B | | | | | not run |
| TC-01 | gradle | fixed 271.x | | | | | not run |
| TC-01 | maven | baseline B | | | | | not run |
| TC-01 | maven | fixed 271.x | | | | | not run |
| TC-01K | gradle | baseline B | | | | | not run |
| TC-01K | gradle | fixed 271.x | | | | | not run |
| TC-02 | gradle | baseline B | | | | | not run |
| TC-02 | gradle | fixed 271.x | | | | | not run |
| TC-02 | maven | baseline B | | | | | not run |
| TC-02 | maven | fixed 271.x | | | | | not run |
| TC-02T | gradle | baseline B | | | | | not run |
| TC-02T | gradle | fixed 271.x | | | | | not run |
| TC-02T | maven | baseline B | | | | | not run |
| TC-02T | maven | fixed 271.x | | | | | not run |
| TC-03 | gradle | baseline B | | | | | not run |
| TC-03 | gradle | fixed 271.x | | | | | not run |
| TC-03 | maven | baseline B | | | | | not run |
| TC-03 | maven | fixed 271.x | | | | | not run |
| TC-04 | gradle | baseline B | | | | | not run |
| TC-04 | gradle | fixed 271.x | | | | | not run |
| TC-04 | maven | baseline B | | | | | not run |
| TC-04 | maven | fixed 271.x | | | | | not run |
| TC-05 | gradle | baseline B | | | | | not run |
| TC-05 | gradle | fixed 271.x | | | | | not run |
| TC-05 | maven | baseline B | | | | | not run |
| TC-05 | maven | fixed 271.x | | | | | not run |
| TC-05Y | gradle | baseline B | | | | | not run |
| TC-05Y | gradle | fixed 271.x | | | | | not run |
| TC-05Y | maven | baseline B | | | | | not run |
| TC-05Y | maven | fixed 271.x | | | | | not run |
| TC-05K | gradle | baseline B | | | | | not run |
| TC-05K | gradle | fixed 271.x | | | | | not run |
| TC-06 | gradle | baseline B | | | | | not run |
| TC-06 | gradle | fixed 271.x | | | | | not run |
| TC-06 | maven | baseline B | | | | | not run |
| TC-06 | maven | fixed 271.x | | | | | not run |
| TC-07 | gradle | baseline B | | | | | not run |
| TC-07 | gradle | fixed 271.x | | | | | not run |
| TC-07 | maven | baseline B | | | | | not run |
| TC-07 | maven | fixed 271.x | | | | | not run |
| TC-08 | gradle | baseline B | | | | | not run |
| TC-08 | gradle | fixed 271.x | | | | | not run |
| TC-08 | maven | baseline B | | | | | not run |
| TC-08 | maven | fixed 271.x | | | | | not run |
| TC-09 | gradle | baseline B | | | | | not run |
| TC-09 | gradle | fixed 271.x | | | | | not run |
| TC-09 | maven | baseline B | | | | | not run |
| TC-09 | maven | fixed 271.x | | | | | not run |
| TC-12 | gradle | baseline B | | | | | not run |
| TC-12 | gradle | fixed 271.x | | | | | not run |
| TC-12 | maven | baseline B | | | | | not run |
| TC-12 | maven | fixed 271.x | | | | | not run |
| TC-13 | gradle | baseline B | | | | | not run |
| TC-13 | gradle | fixed 271.x | | | | | not run |
| TC-13 | maven | baseline B | | | | | not run |
| TC-13 | maven | fixed 271.x | | | | | not run |
| TC-14 | gradle | baseline B | | | | | not run |
| TC-14 | gradle | fixed 271.x | | | | | not run |
| TC-14 | maven | baseline B | | | | | not run |
| TC-14 | maven | fixed 271.x | | | | | not run |
| NC-01 | gradle | baseline B | | | | | not run |
| NC-01 | gradle | fixed 271.x | | | | | not run |
| NC-01 | maven | baseline B | | | | | not run |
| NC-01 | maven | fixed 271.x | | | | | not run |
| NC-01K | gradle | baseline B | | | | | not run |
| NC-01K | gradle | fixed 271.x | | | | | not run |
| NC-02 | gradle | baseline B | | | | | not run |
| NC-02 | gradle | fixed 271.x | | | | | not run |
| NC-02 | maven | baseline B | | | | | not run |
| NC-02 | maven | fixed 271.x | | | | | not run |
| NC-03 | gradle | baseline B | | | | | not run |
| NC-03 | gradle | fixed 271.x | | | | | not run |
| NC-03 | maven | baseline B | | | | | not run |
| NC-03 | maven | fixed 271.x | | | | | not run |
| NC-04 | gradle | baseline B | | | | | not run |
| NC-04 | gradle | fixed 271.x | | | | | not run |
| NC-04 | maven | baseline B | | | | | not run |
| NC-04 | maven | fixed 271.x | | | | | not run |
| NC-05 | gradle | baseline B | | | | | not run |
| NC-05 | gradle | fixed 271.x | | | | | not run |
| NC-05 | maven | baseline B | | | | | not run |
| NC-05 | maven | fixed 271.x | | | | | not run |
| RL-01 | single | baseline B | | | | | not run |
| RL-01 | single | fixed 271.x | | | | | not run |
| RL-02 | single | baseline B | | | | | not run |
| RL-02 | single | fixed 271.x | | | | | not run |
| RL-03 | single | baseline B | | | | | not run |
| RL-03 | single | fixed 271.x | | | | | not run |
| XP-01 | gradle | fixed 271.x | | n/a | | n/a | not run |
| XP-01 | maven | fixed 271.x | | n/a | | n/a | not run |
| XP-02 | gradle (control) | fixed 271.x | | | | | not run |
| XP-02 | maven | fixed 271.x | | | | | not run |
| XP-03a | gradle | fixed 271.x | | | | | not run |
| XP-03b | gradle | fixed 271.x | | | | | not run |
| XP-04 | gradle | fixed 271.x | n/a | n/a | | n/a | not run |
| XP-04 | maven | fixed 271.x | n/a | n/a | | n/a | not run |
| XP-05 | gradle | fixed 271.x | | n/a | n/a | n/a | not run |
| XP-05 | maven | fixed 271.x | | n/a | n/a | n/a | not run |
| XP-06 | gradle | fixed 271.x | | | | | not run |
| XP-06 | maven | fixed 271.x | | | | | not run |
| Runtime | all three | n/a | Tests: `lib` PASS; `app` FAIL on `main.only.property` (R1); single PASS. `MainApplication`: `Could not resolve placeholder 'test.only.property'`. `SingleApplication`: `... 'my.key'` | | | | production check pass; test check fail (R1) |

Add baseline A (261) lines if you run it.

**Verdict rule** (`temp.md` section 9, plus R4): the fix is confirmed when every TC, NC and RL row passes on the fixed
build in every project of its layout, and NC-01, NC-02, NC-03, NC-04, TC-01 and RL-01 fail on baseline B as the table
predicts. Report each XP row separately as "reproduced" or "not reproduced" with the evidence. A reproduced XP-01 or
XP-02 is a new issue, not a reopen of IDEA-387222.
