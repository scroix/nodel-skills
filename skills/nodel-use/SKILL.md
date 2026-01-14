---
name: nodel-use
description: Use when interacting with running Nodel instances - checking node status, viewing console logs, invoking actions, debugging nodes, or managing nodes via the REST API. Applies to curl commands, API calls, or troubleshooting Nodel deployments.
---

# Interacting with Running Nodel Instances

This skill provides guidance for interacting with Nodel via its REST API, debugging nodes, and managing running instances.

## Quick Reference

**Default Base URL:** `http://localhost:8085`

```bash
# List all nodes
curl http://localhost:8085/REST/nodes

# Get node console logs
curl "http://localhost:8085/REST/nodes/My%20Node/console?from=0&max=50"

# Invoke an action
curl -X POST "http://localhost:8085/REST/nodes/My%20Node/actions/Power/call" \
  -H "Content-Type: application/json" -d '"On"'

# Restart a node
curl -X POST "http://localhost:8085/REST/nodes/My%20Node/restart"

# Get node script source
curl http://localhost:8085/REST/nodes/My%20Node/script/raw
```

**Important:** URL-encode node names with spaces (`%20`).

## REST API Endpoints

See `references/rest-api.md` for complete endpoint reference.

### Host-Level Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/REST/nodes` | GET | Map of all nodes |
| `/REST/allNodes` | GET | Discovered nodes on network |
| `/REST/logs` | GET | Framework logs |
| `/REST/diagnostics` | GET | System diagnostics |
| `/REST/recipes/list` | GET | Available node recipes |
| `/REST/toolkit` | GET | Python toolkit reference |

### Node-Level Endpoints

Base: `/REST/nodes/{nodeName}/`

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/console` | GET | Console logs |
| `/logs` | GET | Action/event activity |
| `/actions` | GET | List actions |
| `/actions/{name}/call` | POST | Invoke action |
| `/events` | GET | List events |
| `/events/{name}` | GET | Event metadata + last value |
| `/params/value` | GET | Current parameters |
| `/script/raw` | GET | Script source |
| `/restart` | POST | Restart node |

## Debugging Workflows

### Check Node Health

```bash
# 1. Get console output
curl "http://localhost:8085/REST/nodes/My%20Node/console?from=0&max=100"

# 2. Look for error patterns in response
# Console levels: info (blue), out (gray), warn (orange), err (red)

# 3. Check action/event activity
curl "http://localhost:8085/REST/nodes/My%20Node/logs?from=0&max=50"

# 4. Inspect current parameters
curl http://localhost:8085/REST/nodes/My%20Node/params/value
```

### Live Log Tailing (Long-Polling)

```bash
# Initial fetch - note the highest 'seq' value in response
curl "http://localhost:8085/REST/nodes/My%20Node/console?from=0&max=50"

# Poll for new logs (waits up to 5 seconds)
curl "http://localhost:8085/REST/nodes/My%20Node/console?from=12345&max=50&timeout=5000"
```

Response format:
```json
[
  {"seq": 12346, "timestamp": "2024-01-15T10:30:00", "console": "info", "comment": "Connected"},
  {"seq": 12347, "timestamp": "2024-01-15T10:30:01", "console": "err", "comment": "Error message"}
]
```

### Inspect and Test Actions

```bash
# List available actions
curl http://localhost:8085/REST/nodes/My%20Node/actions

# Get action schema
curl http://localhost:8085/REST/nodes/My%20Node/actions/Power

# Test action - string argument
curl -X POST "http://localhost:8085/REST/nodes/My%20Node/actions/Power/call" \
  -H "Content-Type: application/json" -d '"On"'

# Test action - object argument
curl -X POST "http://localhost:8085/REST/nodes/My%20Node/actions/SetLevel/call" \
  -H "Content-Type: application/json" -d '{"channel": 1, "value": 50}'

# Test action - no argument
curl -X POST "http://localhost:8085/REST/nodes/My%20Node/actions/Refresh/call"
```

### Evaluate Python Expressions

```bash
# Check variable value
curl "http://localhost:8085/REST/nodes/My%20Node/eval?expr=param_ipAddress"

# Check connection state
curl "http://localhost:8085/REST/nodes/My%20Node/eval?expr=tcp.isConnected()"

# Execute diagnostic code
curl -X POST "http://localhost:8085/REST/nodes/My%20Node/exec" \
  -H "Content-Type: text/plain" \
  -d 'console.info("TCP connected: %s" % tcp.isConnected())'
```

## Console Message Types

| Level | Color | Purpose |
|-------|-------|---------|
| `info` | Blue | Informational messages |
| `out` | Gray | Verbose/debug output |
| `warn` | Orange | Warnings |
| `err` | Red | Errors |

## Common Issues

### Node Not Responding

1. Check if node exists: `curl http://localhost:8085/REST/nodes`
2. Check console for startup errors
3. Verify parameters are configured
4. Check network connectivity to device

### Action Not Working

1. Check action exists: `curl .../actions`
2. Verify argument format matches schema
3. Check console for errors after calling
4. Test with simple action first (Refresh, Status)

### Connection Issues

1. Use `/eval` to check connection state
2. Look for "disconnected" in console logs
3. Verify IP/port parameters
4. Test network connectivity from Nodel host

## Node Management

### Create Node from Recipe

```bash
# List recipes
curl http://localhost:8085/REST/recipes/list

# Create node
curl -X POST "http://localhost:8085/REST/newNode?base=recipes/device-control&name=New%20Node"
```

### Update Node Parameters

```bash
# Get current values
curl http://localhost:8085/REST/nodes/My%20Node/params/value

# Save new values
curl -X POST "http://localhost:8085/REST/nodes/My%20Node/params/save" \
  -H "Content-Type: application/json" \
  -d '{"ipAddress": "192.168.1.100", "port": 9999}'
```

### Restart/Rename/Delete

```bash
# Restart
curl -X POST "http://localhost:8085/REST/nodes/My%20Node/restart"

# Rename
curl -X POST "http://localhost:8085/REST/nodes/My%20Node/rename?newName=New%20Name"

# Delete (requires confirmation)
curl -X POST "http://localhost:8085/REST/nodes/My%20Node/remove?confirm=true"
```

## Tips

1. **URL-encode node names** - Spaces become `%20`
2. **Use `?trace` for debugging** - Adds stack traces to error responses
3. **Action arguments** - Strings need quotes: `-d '"On"'`
4. **Long-poll timeout** - Use 5000-10000ms for log tailing
5. **Check restart completion** - Use `/hasRestarted?timestamp={before}&timeout=5000`
