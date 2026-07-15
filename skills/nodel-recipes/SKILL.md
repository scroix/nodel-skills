---
name: nodel-recipes
description: Author or modify Nodel script.py recipes with the bundled Jython 2.5 runtime and Nodel toolkit. Use for recipe actions, events, parameters, timers, device protocols, automation, and integration logic. Do not use for Nodel platform source changes, live-host REST operations, or index.xml, CSS, and JavaScript dashboard work.
---

# Nodel Recipe Development

Create and revise Nodel `script.py` recipes for device control, automation, and integration work.

## Workflow

1. Inspect the existing recipe, parameter values, bindings, and node logs before changing behavior.
2. Define parameters and public action/event schemas before protocol or device logic.
3. Initialize connections and timers only after parameters are available.
4. Keep protocol callbacks small: parse input, update connection state, and emit stable events.
5. Add cleanup for long-running connections, timers, or processes.
6. Exercise the recipe on a disposable or non-production node and inspect `err` console entries.

## Recipe Layout

```text
My Recipe/
├── script.py
└── content
    ├── index.xml
    ├── css
    │   └── custom.css
    └── js
        └── custom.js
```

Only `script.py` is required.

## Critical Runtime Constraint

Nodel runs node scripts with the bundled Jython 2.5.4-rc1 runtime. Use Python 2.5-era syntax and APIs.

```python
try:
    value = int('42')
except Exception, e:
    console.error('Operation failed: %s' % e)
```

Do not use Python 3 exception syntax, f-strings, dictionary comprehensions, set literals, or APIs added after Python 2.5. Do not assume CPython packages are available.

## Minimal Recipe Shape

```python
param_ipAddress = Parameter({
    'title': 'IP Address',
    'schema': {'type': 'string'}
})

local_event_Status = LocalEvent({'schema': {'type': 'string'}})

@local_action({'schema': {'type': 'string'}})
def Power(arg):
    local_event_Status.emit(arg)

def main():
    console.info('Node starting')

@after_main
def setup():
    local_event_Status.emit('Ready')

@at_cleanup
def cleanup():
    console.info('Node stopping')
```

Use schemas that match the values actions accept and events emit. Prefer explicit state variables updated by protocol callbacks over probing undocumented internals.

## References

- Read [`references/jython-syntax.md`](references/jython-syntax.md) whenever writing language syntax, imports, exception handling, collection code, or standard-library calls.
- Read [`references/toolkit-api.md`](references/toolkit-api.md) when using parameters, actions, events, timers, lifecycle decorators, network protocols, HTTP, processes, utilities, or node-state helpers.
- Read [`references/patterns.md`](references/patterns.md) when implementing polling, health status, state arbitration, binary protocols, HTTP integrations, dynamic bindings, process control, chained operations, logging, or parameter validation.

## Completion Check

- Keep syntax compatible with Jython 2.5.
- Confirm every toolkit symbol and option against the toolkit reference.
- Emit event values that match their declared schemas.
- Handle connection failure, malformed responses, and shutdown without leaving background work running.
