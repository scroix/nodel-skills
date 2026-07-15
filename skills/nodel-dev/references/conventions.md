# Nodel Source Conventions

## MPL 2.0 license header

Every Java source file carries the Mozilla Public License 2.0 notice as a
comment block immediately *after* the `package` statement:

```java
package org.nodel.core;

/* 
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. 
 */
```

Copy it verbatim into new files (note: package line first — this differs from
the more common header-above-package style).

## Name reduction

Nodel matches node/action/event names loosely: `"Main Projector"`,
`mainProjector` and `main-projector` are the same point. Implementation in
`nodel-framework/src/main/java/org/nodel/`:

- `Nodel.reduce(String)` (`core/Nodel.java`) keeps letters/digits (plus
  significant non-space Unicode), drops everything else, removes `(...)`
  comment spans (nesting supported), and truncates at `--` or `//` — so
  `"Screen (left) -- foyer"` reduces to `"Screen"`.
- `SimpleName` wraps a name and precomputes `getReducedName()` (display) and
  `getReducedForMatchingName()` (additionally lowercased via
  `SimpleName.flatten`); `equals`/`hashCode` use only the matching form.
  Wildcard filtering goes through `SimpleName.wildcardMatch`.

**Rule: never compare raw name strings.** Wrap in `SimpleName` (or reduce
both sides) anywhere names meet. There are E2E tests guarding this behavior
(`LocalsNameReductionE2ETests`).

## Handler / Handlers callback pattern

No `java.util.function` here (codebase predates it). Callbacks use the nested
interfaces of `org.nodel.Handler`:

- `Handler.H0` … `Handler.H5` — `void handle(...)` with 0–5 type params.
- `Handler.F0<R>` … `Handler.F3<R,...>` — same but returning `R`.
- Static null-safe dispatch: `Handler.handle(handler, arg)` is a no-op when
  the handler is null — prefer it over manual null checks.
- `org.nodel.Handlers` holds multi-subscriber handler lists.

New framework callbacks should follow this pattern rather than introducing
`Runnable`/`Consumer` mixtures.

## @Value / @Service / @Param: serialization IS the API

The annotations in `nodel-framework/src/main/java/org/nodel/reflection/` do
double duty — `Serialisation` uses them for JSON, and `REST.resolveRESTcall`
uses them as the routing table:

```java
@Service(name = "logs", title = "Logs", genericClassA = LogEntry.class,
         desc = "Retrieves this node's general event/action log.")
public LogEntry[] getLogs(
        @Param(name = "from", title = "From", desc = "The minimum sequence number.")
        long from,
        @Param(name = "max", title = "Max", desc = "The maximum number of rows to return.")
        int max) { ... }
```

(from `org.nodel.host.BaseNode` — reachable as
`GET /REST/nodes/<node>/logs?from=0&max=100`)

Implications:

- `@Value(name = ...)`/`@Service(name = ...)` strings are wire format and
  public REST surface — renaming one is a breaking change for every peer and
  UI build in the field.
- `order =` on `@Value` controls JSON field ordering (see `ChannelMessage`).

## Misc

- Private instance fields use `_camelCase` (`_python`, `_scriptFile`);
  statics use `s_` (`s_globalLock`) — see `PyNode.java`.
- Vendored third-party code keeps its own package (`org.nanohttpd.*` inside
  `nodel-framework`); patch it in place rather than adding a dependency.
- Jython is pinned at `2.5.4-rc1` — anything reaching the script layer must
  stay Python 2.5-compatible (see the `nodel-recipes` skill).
