---
name: nodel-dev
description: Develop the Nodel platform source itself - build the Java framework, Jython host, and web UI with Gradle, run a dev host, and run the Playwright integration/E2E tests. Use when modifying Nodel platform code, not for authoring script.py recipes, building node dashboards, or inspecting and managing running hosts through REST.
---

# Nodel Platform Development

For working on the Nodel source tree (github.com/museumsvictoria/nodel).
Three Gradle modules (`settings.gradle`):

| Module | What it is |
|--------|------------|
| `nodel-framework` | Core Java library: nodel points, channels, discovery, REST/reflection, vendored NanoHTTPD |
| `nodel-jyhost` | The host process: embeds Jython 2.5.4-rc1, runs nodes, serves the web UI and REST API |
| `nodel-webui-js` | The web UI: Grunt-built JS/LESS, packaged as a Java resource JAR |

Other top-level directories (`nodel-framework-dotnet`, `nodel-windows`, etc.) are
not part of the Gradle build.

## Building

Requires JDK 11+ on PATH; always build through the wrapper (`./gradlew` —
currently Gradle 8.14.5, pinned in `gradle/wrapper/gradle-wrapper.properties`).

```bash
./gradlew build          # full build INCLUDING the whole test suite
./gradlew build -x test  # build only
```

The runnable fat JAR lands in `nodel-jyhost/build/distributions/standalone/` as
`nodelhost-<branch>-<version>-rev<N>.jar`. The first build downloads Node.js
and npm packages for the web UI.

The web UI is Grunt-built and ships inside the JAR as classpath resource
`org/nodel/host/content.zip` — so a UI change means rebuilding
`nodel-webui-js`, not just `nodel-jyhost`. Pipeline details:
`references/architecture.md`.

## Running a dev host

```bash
mkdir -p ~/nodel-dev && cd ~/nodel-dev   # host creates dirs in its cwd
java -jar <repo>/nodel-jyhost/build/distributions/standalone/nodelhost-*-rev*.jar
```

- Web interface on port **8085**; override with `-p <port>`.
- Nodes live in `./nodes` (`-r`/`--nodelRoot`); recipes in `./recipes` (`--recipes`).
- Press Enter in the console to shut down cleanly.
- `./gradlew :nodel-jyhost:run` also works, but litters `nodel-jyhost/` with
  runtime dirs since the module dir is its cwd.

## Testing

JUnit 5 + Playwright tests in `nodel-jyhost/src/test/java/org/nodel/`. Gradle
starts a real nodelhost on port **18085** in `nodel-jyhost/nodelhost-temp/`;
on failure, read `output.log` and `error.log` there first.

```bash
./gradlew :nodel-jyhost:integrationTest   # everything NOT tagged @Tag("e2e")
./gradlew :nodel-jyhost:e2eTest           # only @Tag("e2e") user-journey tests
```

First run may need Chromium: `./gradlew :nodel-jyhost:playwrightInstall`.

To watch the browser (`HEADED`/`SLOWMO` are not Gradle task inputs, so
`--rerun` is mandatory — without it an up-to-date task silently skips):

```bash
HEADED=1 SLOWMO=500 ./gradlew :nodel-jyhost:e2eTest --rerun
```

Host lifecycle, discovery fixtures, and debugging recipes:
`references/testing.md`.

## Architecture essentials

One line each — full detail with file paths in `references/architecture.md`.

- **Nodel points**: `NodelServers` publishes a node's local actions/events;
  `NodelClients` binds to remote ones (package `org.nodel.core`).
- **Wire protocol**: line-delimited JSON (`ChannelMessage`) over TCP; same-JVM
  bindings short-circuit through loopback channels.
- **Discovery**: multicast on **224.0.0.252:5354**; implementation pluggable
  via system property `org.nodel.discovery.impl` (how tests inject
  `LocalAutoDNS`).
- **PyNode**: one Jython interpreter per node, but script `exec`/`main()`
  calls across ALL nodes are serialized through one global lock — node startup
  is near-serial; respect this when touching startup ordering.
- **REST**: `NodelHostHTTPD` extends a vendored NanoHTTPD, and there is no
  route table — URL segments are resolved over the live object graph via
  `@Service`/`@Value`/`@Param` annotations, so adding an endpoint means
  annotating a member on a reachable object.

## Conventions

Examples for each in `references/conventions.md`.

- New Java files get the MPL 2.0 header immediately *after* the `package`
  statement (most files carry it; some legacy ones don't).
- Node/action/event names match case/space/punctuation-insensitively — never
  compare raw name strings; wrap in `SimpleName`.
- Callbacks use the `org.nodel.Handler` interfaces with the null-safe static
  `Handler.handle(...)` dispatchers.
- `@Value`/`@Service` annotation names are wire format AND REST surface —
  renaming one is a breaking change.
