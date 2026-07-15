# Nodel Platform Architecture

Paths are relative to the Nodel repository root. Package `org.nodel.*` lives in
`nodel-framework/src/main/java/`, package `org.nodel.jyhost.*` in
`nodel-jyhost/src/main/java/`.

## Nodel points: servers and clients

A "nodel point" is a named action or event on a node (`org.nodel.core.NodelPoint`).
Two singletons manage them (package `org.nodel.core`):

- **`NodelServers`** — the server side. A node registers its local actions and
  events here (`NodelServerAction`, `NodelServerEvent`); this is what makes
  them callable/observable by other nodes.
- **`NodelClients`** — the client side. A node binds to *remote* actions and
  events (`NodelClientAction`, `NodelClientEvent`); the client resolves the
  hosting node via discovery and maintains the channel.

Bindings between nodes in the same JVM never touch the network: they go
through `LoopbackChannelClient` / `LoopbackChannelServer` instead of
`TCPChannelClient` / `TCPChannelServer` (all four extend the same
`ChannelClient` / channel-server machinery).

## Wire protocol: line-delimited JSON

`ChannelMessage` (`org.nodel.core`) is a flat class of `@Value`-annotated
public fields — `node`, `actions`, `events`, `action`, `arg`, `event`, etc.
One instance is one protocol message:

- Serialized to JSON via `org.nodel.reflection.Serialisation`.
- `TCPChannelClient.sendMessage` writes the JSON followed by `\r\n` — one
  message per line.
- The receive side parses the byte stream incrementally with
  `JSONStreamReader`.
- `ChannelServerSocket` accepts connections for `TCPChannelServer`.

The messaging TCP port is ephemeral by default (see the bootstrap table
below) and advertised via discovery.

## Discovery: multicast on 224.0.0.252:5354

Package `org.nodel.discovery`:

- `Discovery.java` — constants: `MDNS_GROUP = 224.0.0.252`, `MDNS_PORT = 5354`.
- `NodelAutoDNS.java` — the production implementation: advertises local nodes
  (`NodelAdvertiser`) and discovers remote ones by multicast probing
  (`NodelDiscoverer`), exchanging `NameServicesChannelMessage`s over the
  group. `TopologyWatcher` tracks network-interface topology changes.
- `AutoDNS.java` — abstract facade. The implementation is chosen by system
  property **`org.nodel.discovery.impl`** (`AutoDNS.IMPL_SYSTEMPROP`), format
  `"<className>"` or `"<className>;<staticMethod>"`. This is how the test
  suite substitutes `LocalAutoDNS` (an in-JVM registry shipped as a
  `nodel-framework` **test fixture**, wired onto the test host's classpath via
  the `discoveryFixture` configuration in `nodel-jyhost/build.gradle`).

## PyNode: one interpreter per node, one global exec lock

`org.nodel.jyhost.PyNode` is a running node:

- Each node constructs its own interpreter:
  `_python = PythonInterpreter.threadLocalStateInterpreter(_globals)`.
  Node scripts therefore do not share globals — but they do share the host's
  single bundled Jython runtime.
- Script `exec` and `main()` calls are serialized **across all nodes** through
  a static `ReentrantLock` (`s_currentGlobalRentrantLock`, guarded by
  `s_globalLock`). The comment marks it as a workaround for a Jython
  class-loading bug in the XML parser. `getAReentrantLock()` waits up to
  60 s; if the current holder takes longer, a *new* lock replaces the old one
  so remaining nodes can initialise (the stuck node keeps the stale lock).
- Consequence: node startup is deliberately near-serial. Long-running work in
  a recipe's top level or `main()` stalls every other node's startup — keep
  that in mind when changing host startup or writing tests that create nodes.

`NodelHost` (same package) scans the nodes directory and manages `PyNode`
lifecycles; `org.nodel.host.BaseNode` holds the host-agnostic node model
(bindings, console, logs).

## REST: reflection-routed, no route table

- HTTP server: `org.nodel.jyhost.NodelHostHTTPD` `extends NanoHTTPD`.
  NanoHTTPD is **vendored** into the framework at
  `nodel-framework/src/main/java/org/nanohttpd/` (HTTP + websocket protocol
  packages) — do not add it as an external dependency.
- Routing: `REST.resolveRESTcall` (`org.nodel.rest.REST`) receives the URL
  split into parts and walks them over a live object graph:
  - `@Service` marks a field/method as a sub-endpoint; methods take
    `@Param`-annotated arguments filled from query params or the request
    body.
  - `@Value` marks plain data fields (also the serialization schema).
  - Metadata is gathered/cached by `org.nodel.reflection.Reflection`
    (`getServiceInfosByName`, `getValueInfosByName`, `getDefaultService`).
- So `GET /REST/nodes/<node>/console?from=0` resolves segment-by-segment from
  the root graph object to `BaseNode`'s `@Service(name = "console")` member.
  Adding an endpoint = adding an annotated member on a reachable object; there
  is no separate route registration to update.

## Web UI build pipeline (nodel-webui-js)

`nodel-webui-js/build.gradle`, plugin `com.github.node-gradle.node` 7.0.2:

1. `npmInstall` — downloads Node.js **20.12.0** into `build/nodejs`, runs npm
   with `--legacy-peer-deps`; a `doLast` deletes
   `node_modules/bootstrap/node_modules` so grunt-twbs reinstalls cleanly.
2. `gruntRun` (`NpxTask`) — runs `grunt` over `src/` (JS, LESS themes, XSL
   templates) producing `build/grunt/`. Sets
   `NODE_OPTIONS=--no-network-family-autoselection` (grunt-google-fonts
   download races under Node 20).
3. `copyContent` + `filterContentTemplates` — stage into
   `build/www-content_stage`, token-filtering `build.json` with build/git
   metadata.
4. `zipContentInterface` — zips the stage into
   `build/www-content/org/nodel/host/content.zip`; `copyBuildInfo` places
   `build.json` at `org/nodel/`.
5. `sourceSets.main.resources.srcDirs = build/www-content`, and
   `compileJava`/`processResources` depend on the zip — the UI ships inside
   the module JAR as classpath resource `org/nodel/host/content.zip`.

At runtime the host extracts the embedded content into its working directory
when the version changes or the directory is empty (`Launch`'s
embedded-content check), so a stale-looking UI after a rebuild usually means
that check found an existing content directory.

## Host bootstrap

`org.nodel.jyhost.Launch` (main class, `nodel-jyhost/build.gradle
application` block) parses `org.nodel.host.BootstrapConfig`:

| Setting | Default | Flag |
|---------|---------|------|
| Web/REST port | `8085` | `-p` / `--NodelHostPort` |
| Messaging TCP port | `0` (ephemeral) | `--messagingPort` |
| Nodes root | `./nodes` | `-r` / `--nodelRoot` |
| Recipes root | `./recipes` | `--recipes` |

All directories are created relative to the process working directory.
