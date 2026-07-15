---
name: nodel-dev
description: Develop the Nodel platform source itself - build the Java framework, Jython host, and web UI with Gradle, run a dev host, run Playwright integration/E2E tests, and navigate the core architecture. Use when modifying Nodel platform code (Java/web UI), not when writing recipes.
---

# Nodel Platform Development

For working on the Nodel source tree (github.com/museumsvictoria/nodel), not on
recipes. The build has three Gradle modules (`settings.gradle`):

| Module | What it is |
|--------|------------|
| `nodel-framework` | Core Java library: nodel points, channels, discovery, REST/reflection, vendored NanoHTTPD |
| `nodel-jyhost` | The host process: embeds Jython 2.5.4-rc1, runs nodes, serves the web UI and REST API |
| `nodel-webui-js` | The web UI: Grunt-built JS/LESS, packaged as a Java resource JAR |

Other top-level directories (`nodel-framework-dotnet`, `nodel-windows`, etc.) are
not part of the Gradle build.

## Building

Requires **JDK 11+** on PATH (the toolchain compiles with `options.release = 11`).
The Gradle **8.14.5** wrapper (`gradle/wrapper/gradle-wrapper.properties`) fetches
itself; never install Gradle manually.

```bash
./gradlew build          # full build INCLUDING the whole test suite
./gradlew build -x test  # build only (skips integration + E2E tests)
```

The runnable fat JAR lands in `nodel-jyhost/build/distributions/standalone/` as
`nodelhost-<branch>-<version>-rev<N>.jar` (`fatJar` task; `build` is finalized by
it). The first build downloads Node.js 20.12.0 and npm packages for the web UI.

### How the web UI gets into the JAR

`nodel-webui-js` uses the `com.github.node-gradle.node` plugin: `npmInstall`
(with `--legacy-peer-deps`) then `gruntRun` (npx `grunt`) compile `src/` into
`build/grunt/`. The output is staged and zipped by `zipContentInterface` into
`build/www-content/org/nodel/host/content.zip`, and `build/www-content` is the
module's Java *resources* source dir — so the UI ships inside the JAR as a
classpath resource. `compileJava`/`processResources` depend on the zip task; a
UI change means rebuilding `nodel-webui-js`, not just `nodel-jyhost`.

## Running a dev host

```bash
mkdir -p ~/nodel-dev && cd ~/nodel-dev   # host creates dirs in its cwd
java -jar <repo>/nodel-jyhost/build/distributions/standalone/nodelhost-*-rev*.jar
```

- Web interface on port **8085** by default (`BootstrapConfig.DEFAULT_NODELHOST_PORT`);
  override with `-p <port>`.
- Nodes live in `./nodes` (override `-r` / `--nodelRoot`); recipes in `./recipes`
  (`--recipes`).
- Press Enter in the console to shut down cleanly.
- Alternatively `./gradlew :nodel-jyhost:run` runs `org.nodel.jyhost.Launch`
  directly with stdin wired up (but cwd is the module dir — it will litter
  `nodel-jyhost/` with runtime dirs).

## Testing

Tests live in `nodel-jyhost/src/test/java/org/nodel/` and are JUnit 5 +
Playwright 1.52.0 (Java). Gradle starts a real nodelhost on port **18085** in
`nodel-jyhost/nodelhost-temp/` (`startNodelhost` task: kills anything on the
port, waits up to 60 s for HTTP 200, logs to `output.log`/`error.log` there).

```bash
./gradlew :nodel-jyhost:integrationTest   # everything NOT tagged @Tag("e2e")
./gradlew :nodel-jyhost:e2eTest           # only @Tag("e2e") user-journey tests
./gradlew build -x test                   # skip the suite entirely
```

The default `test` task (run by `build`) runs the full suite. First run may need
Chromium: `./gradlew :nodel-jyhost:playwrightInstall`.

### Watching the browser

`HEADED` and `SLOWMO` are read by the test JVM but are **not Gradle task
inputs** — always add `--rerun` or an up-to-date task silently skips:

```bash
HEADED=1 SLOWMO=500 ./gradlew :nodel-jyhost:e2eTest --rerun
```

Tests use `LocalAutoDNS` (in-JVM discovery, from `nodel-framework` test
fixtures) for determinism; set `NODEL_TEST_DISCOVERY=1` to exercise real
multicast. On failure check `nodel-jyhost/nodelhost-temp/{output,error}.log` and
the HTML reports in `nodel-jyhost/build/reports/tests/`.

See `references/testing.md` for the task wiring and debugging recipes.

## Architecture essentials

Full detail with file paths in `references/architecture.md`.

- **Nodel points**: `NodelServers` publishes a node's local actions/events
  (`NodelServerAction`/`NodelServerEvent`); `NodelClients` binds to remote ones
  (`NodelClientAction`/`NodelClientEvent`). All in
  `nodel-framework/src/main/java/org/nodel/core/`.
- **Wire protocol**: `ChannelMessage` — a flat `@Value`-annotated class — is
  serialized to JSON and sent one-message-per-CRLF-terminated-line over TCP
  (`TCPChannelClient`/`TCPChannelServer`, parsed by `JSONStreamReader`).
  Same-JVM bindings short-circuit through
  `LoopbackChannelClient`/`LoopbackChannelServer`.
- **Discovery**: multicast group **224.0.0.252 : 5354** (`Discovery.MDNS_GROUP`
  / `MDNS_PORT`), implemented by `NodelAutoDNS`; the implementation is pluggable
  via system property `org.nodel.discovery.impl` (how tests inject
  `LocalAutoDNS`).
- **PyNode** (`nodel-jyhost`): each node gets its own
  `PythonInterpreter.threadLocalStateInterpreter(...)`. Script `exec` and
  `main()` calls across ALL nodes are serialized through one static global
  `ReentrantLock` (Jython XML-parser loading bug workaround); if a node holds
  it > 60 s the lock is replaced so others can proceed. Anything touching node
  startup ordering must respect this.
- **REST**: `NodelHostHTTPD` extends a vendored NanoHTTPD
  (`nodel-framework/src/main/java/org/nanohttpd/`). There is no route table:
  `REST.resolveRESTcall` walks URL path segments over the live object graph
  using reflection metadata from `@Service` (sub-endpoints/methods), `@Value`
  (fields), and `@Param` (method args) annotations. Adding an endpoint =
  annotating a member on a reachable object (see `BaseNode` for examples).

## Conventions

- **License header**: every Java source starts with the MPL 2.0 comment block
  immediately after the `package` statement — copy it from any existing file.
- **Name reduction**: node/action/event names are matched case-, space- and
  punctuation-insensitively. `Nodel.reduce` keeps letters/digits, strips
  `(...)` comments (nested) and truncates at `--` or `//`; `SimpleName` holds
  original + reduced forms and compares via the flattened (lowercased) one.
  Never compare raw name strings.
- **Callbacks**: use the `Handler.H0`–`H5` / `F0`–`F3` interfaces
  (`org.nodel.Handler`) with the null-safe static `Handler.handle(...)`
  dispatchers; `Handlers` manages multi-subscriber lists.
- **Serialization = API surface**: `@Value`/`@Service` annotations drive both
  JSON serialization (`Serialisation`) and the REST tree — renaming an
  annotation's `name` is a wire/API-breaking change.

See `references/conventions.md` for examples of each.
