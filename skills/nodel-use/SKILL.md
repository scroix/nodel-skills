---
name: nodel-use
description: Inspect, debug, and manage running Nodel hosts and nodes through the REST API. Use for live status, console logs, actions, events, parameters, bindings, scripts, files, restarts, renames, and removals. Do not use for authoring recipe logic, building dashboards, or changing Nodel platform source.
---

# Interacting with Running Nodel Instances

Inspect and manage live Nodel hosts through their REST API.

## Workflow

1. Identify the correct host and port. With no configured port, Nodel reuses its cached last port or falls back to `8085`.
2. List nodes and confirm the exact target name before using a node-scoped endpoint.
3. Read console, activity, parameters, actions, and events before mutating state.
4. Test the narrowest safe action or diagnostic call, then re-read logs and state.
5. Use restart, rename, deletion, script, parameter, binding, or file writes only when the requested change requires them.

## Quick Start

URL-encode node names in paths (`My Node` becomes `My%20Node`).

```bash
# List local nodes
curl http://localhost:8085/REST/nodes

# Read recent console entries
curl "http://localhost:8085/REST/nodes/My%20Node/console?from=0&max=50"

# Invoke a string action
curl -X POST "http://localhost:8085/REST/nodes/My%20Node/actions/Power/call" \
  -H "Content-Type: application/json" \
  -d '{"arg":"On"}'
```

## Safety and Response Rules

- Inspect an action's metadata before choosing its argument shape.
- Send JSON to service endpoints, including `{}` when a POST has no explicit payload.
- Treat `/files/save` as the raw-file-content exception.
- Use the previous ISO `started` timestamp with `hasRestarted` when waiting for a restart.
- Require `confirm=true` for node removal and confirm the target name immediately beforehand.
- Add `?trace` only when diagnosing serialization, Python, or unexpected server errors; routing and not-found failures deliberately omit stack traces.
- Preserve unrelated nodes, parameters, bindings, scripts, and files.

## Debugging Order

1. Confirm the node exists and inspect discovery when remote visibility matters.
2. Read `console` for startup or protocol errors.
3. Read action/event activity and current parameters.
4. Inspect action and event metadata before invoking or evaluating anything.
5. Use `eval` for a narrow expression and `exec` only for deliberate diagnostic code.
6. Re-read the console after every active test.

## References

- Read [`references/rest-api.md`](references/rest-api.md) when choosing an endpoint, method, query parameter, payload shape, response, WebSocket path, or management operation.
- Read [`references/debugging.md`](references/debugging.md) when diagnosing startup, discovery, connectivity, actions, events, timers, live logs, framework health, or restart recovery.

## Completion Check

- Confirm the live response matches the expected shape rather than trusting HTTP status alone.
- Confirm active tests create no new `err` console entries.
- Re-read changed state after any mutation.
