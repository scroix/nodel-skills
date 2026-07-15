# Nodel Test Infrastructure

All host tests live in `nodel-jyhost/src/test/java/org/nodel/` and run with
JUnit 5 + Playwright for Java 1.52.0 (Chromium). Task wiring is in
`nodel-jyhost/build.gradle`; the human-oriented walkthrough is the TESTING
section of the repo's `BUILDING.md`.

## The three test tasks

| Task | Selection | Purpose |
|------|-----------|---------|
| `:nodel-jyhost:integrationTest` | `excludeTags 'e2e'` | API, smoke, and browser-assisted integration tests |
| `:nodel-jyhost:e2eTest` | `includeTags 'e2e'` | Real user journeys (click, type, navigate) |
| `:nodel-jyhost:test` | no filter | Full suite — this is what `./gradlew build` runs |

E2E classes carry `@Tag("e2e")` (e.g. `E2EUserJourneyTests`,
`TemplateSelectionE2ETests`, `LocalsNameReductionE2ETests`). Everything shares
`TestBase`, which hard-codes `BASE_URL = http://127.0.0.1:18085` and creates
the Playwright browser.

## The test host lifecycle

Every test task `dependsOn 'startNodelhost'` and is `finalizedBy
'stopNodelhost'`:

1. `cleanNodelhostTemp` deletes `nodel-jyhost/nodelhost-temp/`.
2. Anything already listening on port **18085** is killed (`lsof`/PowerShell).
3. A real host (`org.nodel.jyhost.Launch -p 18085`) starts with
   `nodel-jyhost/nodelhost-temp/` as its working directory, stdout/stderr
   redirected to `output.log` / `error.log` in that directory. On Unix stdin
   is held open with `tail -f /dev/null` (an EOF on stdin shuts the host
   down).
4. Gradle polls `http://127.0.0.1:18085/` for up to 60 s; failure to reach
   HTTP 200 aborts with a pointer at the two log files.

Nodes created during tests appear under `nodelhost-temp/nodes/`.

## Discovery in tests

By default the host is started with
`-Dorg.nodel.discovery.impl='org.nodel.discovery.LocalAutoDNS;instance'`.
`LocalAutoDNS` is an in-JVM discovery registry shipped as a **test fixture**
of `nodel-framework` and put on the host classpath via the `discoveryFixture`
configuration — it never ships in a production JAR. Only the e2e suite fails
fast if it didn't load (`TestBase.assertLocalDiscoveryActive()`); integration
runs would silently fall back to multicast (a load failure only logs a WARN).

To exercise real multicast discovery:

```bash
NODEL_TEST_DISCOVERY=1 ./gradlew :nodel-jyhost:integrationTest \
    --tests org.nodel.DiscoverySmokeTests --rerun
```

## Visual debugging

`TestBase` reads two environment variables:

- `HEADED=1` — run Chromium visibly (headless is the default; the check is
  merely "is HEADED set").
- `SLOWMO=500` — milliseconds of delay between Playwright actions.

Neither is a Gradle task input, so **always add `--rerun`** — otherwise an
up-to-date task silently skips and no browser appears:

```bash
HEADED=1 SLOWMO=500 ./gradlew :nodel-jyhost:e2eTest --rerun
```

`PWDEBUG=1` opens the Playwright inspector for step-through debugging.

## When tests fail

1. Read `nodel-jyhost/nodelhost-temp/output.log` and `error.log` — most
   "impossible" failures are the host having died or never started.
2. Re-run headed (`HEADED=1 ... --rerun`) to watch the browser.
3. JUnit HTML reports: `nodel-jyhost/build/reports/tests/<taskName>/`.
4. Port conflicts self-heal (startNodelhost kills 18085 first), but a
   half-dead Gradle daemon holding the port is worth ruling out.

## Playwright browser install

CI-oriented helper tasks (Playwright CLI via the test classpath):

```bash
./gradlew :nodel-jyhost:playwrightInstall      # install Chromium
./gradlew :nodel-jyhost:playwrightInstallDeps  # OS-level deps (Linux CI)
./gradlew :nodel-jyhost:playwright --args='...' # raw Playwright CLI
```
