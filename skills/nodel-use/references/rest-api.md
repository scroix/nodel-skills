# Nodel REST API Reference

Complete reference for all Nodel REST API endpoints.

## Contents

- [Base URL](#base-url)
- [Host-level endpoints](#host-level-endpoints)
- [Node-level endpoints](#node-level-endpoints)
- [WebSocket API](#websocket-api)
- [Error responses](#error-responses)
- [Common HTTP status codes](#common-http-status-codes)
- [Query parameters](#query-parameters)

## Base URL

Common: `http://localhost:8085`. With no configured port, the host first reuses its cached last port and otherwise tries 8085; an explicitly configured port takes precedence.

The port can be configured with `-p` flag when starting Nodel.

For most service `POST` endpoints, send JSON in the request body. If there is no explicit payload,
send an empty object (`-d '{}'`) to avoid request parsing errors. File upload endpoints accept raw file content instead.

## Host-Level Endpoints

### Node Discovery

```bash
# Get all local nodes
curl http://localhost:8085/REST/nodes
# Returns: {"Node Name": {...}, "Other Node": {...}}

# Get all discovered nodes on network
curl http://localhost:8085/REST/allNodes
# Returns nodes from all Nodel hosts on the multicast group

# Discovery service state
curl http://localhost:8085/REST/discovery

# Advertised node URLs (optional text filter)
curl "http://localhost:8085/REST/nodeURLs?filter=Display"

# Advertised URLs for a specific node name
curl "http://localhost:8085/REST/nodeURLsForNode?name=Display%20Node"
```

### Framework Logs

```bash
# Get framework logs
curl "http://localhost:8085/REST/logs?from=0&max=50"

# Warning logs only
curl "http://localhost:8085/REST/warningLogs?from=0&max=50"
```

### System Information

```bash
# Diagnostics (thread pools, memory, etc.)
curl http://localhost:8085/REST/diagnostics

# Python toolkit reference
curl http://localhost:8085/REST/toolkit

# Host metadata, including startup timestamp
curl http://localhost:8085/REST
# Returns: {"started": "...", "nodes": {...}}
```

### Recipe Management

```bash
# List available recipes
curl http://localhost:8085/REST/recipes/list
# Returns: [{"path":"nodel-official-recipes/PJLink", "modified":"..."}, ...]

# Create node from recipe
curl -X POST "http://localhost:8085/REST/newNode?base=nodel-official-recipes/PJLink" \
  -H "Content-Type: application/json" \
  -d '{"value":"My New Node"}'
```

## Node-Level Endpoints

Base: `/REST/nodes/{nodeName}/`

**Important:** URL-encode node names with spaces (`My Node` → `My%20Node`)

### Console & Logs

```bash
# Console output
curl "http://localhost:8085/REST/nodes/My%20Node/console?from=0&max=50"

# Long-poll for new console messages
curl "http://localhost:8085/REST/nodes/My%20Node/console?from=12345&max=50&timeout=5000"

# Action/event activity log
curl "http://localhost:8085/REST/nodes/My%20Node/logs?from=0&max=50"

# Syncable activity (for dashboards)
curl "http://localhost:8085/REST/nodes/My%20Node/activity?from=0"
```

Console response format:
```json
[
  {
    "seq": 12345,
    "timestamp": "2024-01-15T10:30:00.123",
    "console": "info",
    "comment": "Log message here"
  }
]
```

Console types: `info` (blue), `out` (gray), `warn` (orange), `err` (red)

### Actions

```bash
# List all actions
curl http://localhost:8085/REST/nodes/My%20Node/actions
# Returns: {"Power": {...}, "Volume": {...}}

# Get action metadata
curl http://localhost:8085/REST/nodes/My%20Node/actions/Power
# Returns: {"name": "Power", "schema": {...}, "group": "...", ...}

# Invoke action with string argument
curl -X POST "http://localhost:8085/REST/nodes/My%20Node/actions/Power/call" \
  -H "Content-Type: application/json" \
  -d '{"arg":"On"}'

# Invoke action with object argument
curl -X POST "http://localhost:8085/REST/nodes/My%20Node/actions/SetLevel/call" \
  -H "Content-Type: application/json" \
  -d '{"arg":{"channel": 1, "value": 75}}'

# Invoke action with no argument
curl -X POST "http://localhost:8085/REST/nodes/My%20Node/actions/Refresh/call" \
  -H "Content-Type: application/json" \
  -d '{}'
```

### Events

```bash
# List all events
curl http://localhost:8085/REST/nodes/My%20Node/events
# Returns: {"Status": {...}, "Power": {...}}

# Get event metadata and last value
curl http://localhost:8085/REST/nodes/My%20Node/events/Status
# Returns: {"name": "Status", "schema": {...}, "arg": <last-value>}
```

### Parameters

```bash
# Get parameter schema
curl http://localhost:8085/REST/nodes/My%20Node/params/schema

# Get current parameter values
curl http://localhost:8085/REST/nodes/My%20Node/params
# Returns: {"ipAddress": "192.168.1.100", "port": 9999}

# Save parameter values
curl -X POST "http://localhost:8085/REST/nodes/My%20Node/params/save" \
  -H "Content-Type: application/json" \
  -d '{"ipAddress": "192.168.1.101", "port": 9999}'
```

### Remote Bindings

```bash
# Get remote binding schema
curl http://localhost:8085/REST/nodes/My%20Node/remote/schema

# Get current bindings
curl http://localhost:8085/REST/nodes/My%20Node/remote
# Returns: {"actions": {...}, "events": {...}}

# Save remote bindings
curl -X POST "http://localhost:8085/REST/nodes/My%20Node/remote/save" \
  -H "Content-Type: application/json" \
  -d '{"actions":{"DisplayPower":{"node":"Display Node","action":"Power"}},"events":{"DisplayStatus":{"node":"Display Node","event":"Status"}}}'
```

### Script Management

```bash
# Get raw script source
curl http://localhost:8085/REST/nodes/My%20Node/script/raw
# Returns: plain text Python script

# Save script
curl -X POST "http://localhost:8085/REST/nodes/My%20Node/script/save" \
  -H "Content-Type: application/json" \
  -d '{"script":"console.info(\"updated\")\n"}'

# Restart after saving when you need the new script bindings to run
curl -X POST "http://localhost:8085/REST/nodes/My%20Node/restart" \
  -H "Content-Type: application/json" \
  -d '{}'

# Evaluate Python expression
curl "http://localhost:8085/REST/nodes/My%20Node/eval?expr=param_ipAddress"
curl "http://localhost:8085/REST/nodes/My%20Node/eval?expr=_isConnected"

# Execute Python code
curl -X POST "http://localhost:8085/REST/nodes/My%20Node/exec" \
  -H "Content-Type: application/json" \
  -d '{"code":"console.info(\"Debug: %s\" % param_ipAddress)"}'
```

### Node Management

```bash
# Restart node
curl -X POST "http://localhost:8085/REST/nodes/My%20Node/restart" \
  -H "Content-Type: application/json" \
  -d '{}'

# Check if restarted (for waiting after restart)
curl "http://localhost:8085/REST/nodes/My%20Node/hasRestarted?timestamp=2026-06-27T19%3A21%3A42.391%2B10%3A00&timeout=5000"
# Returns: {"timestamp":"2026-06-27T19:21:42.391+10:00"}

# Rename node
curl -X POST "http://localhost:8085/REST/nodes/My%20Node/rename" \
  -H "Content-Type: application/json" \
  -d '{"value":"New Name"}'

# Delete node (requires confirmation)
curl -X POST "http://localhost:8085/REST/nodes/My%20Node/remove?confirm=true" \
  -H "Content-Type: application/json" \
  -d '{}'
```

### File Management

```bash
# List node files
curl http://localhost:8085/REST/nodes/My%20Node/files
# Returns: [{"path": "script.py", "modified": "..."}, ...]

# Get file content
curl "http://localhost:8085/REST/nodes/My%20Node/files/contents?path=custom.css"

# Save file
curl -X POST "http://localhost:8085/REST/nodes/My%20Node/files/save?path=custom.css" \
  -H "Content-Type: text/plain" \
  --data-binary @custom.css

# Delete file
curl -X POST "http://localhost:8085/REST/nodes/My%20Node/files/delete?path=old-file.txt" \
  -H "Content-Type: application/json" \
  -d '{}'
```

## WebSocket API

Real-time activity streaming:

```
ws://localhost:8085/nodes/{nodeName}
```

Message types:
- `activityHistory` - Initial array of all activity (sent on connect)
- `activity` - Single activity entry (sent on changes)

The server also sends a WebSocket protocol ping frame every 45 seconds. `ping` is not a JSON message type.

## Error Responses

```json
{
  "error": "EndpointNotFoundException",
  "message": "Node not found",
  "cause": null,
  "stackTrace": null
}
```

Fields with null values may be omitted by serialization. REST errors use the HTTP status for 404/500; the `code` field is populated by the separate non-REST node-path not-found response, not the normal REST exception path.

Add `?trace` when diagnosing serialization, Python, or unexpected server errors. Those 500 paths may include one stack trace; routing, file-not-found, and unknown-service errors deliberately do not.

## Common HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 404 | Node or endpoint not found |
| 500 | Server error (check console) |

## Query Parameters

| Parameter | Endpoints | Purpose |
|-----------|-----------|---------|
| `from` | console, logs, activity | Start sequence number |
| `max` | console, logs | Maximum entries to return |
| `timeout` | node console, node logs, hasRestarted | Long-poll timeout in ms |
| `filter` | `nodeURLs` | Optional string filter |
| `name` | `nodeURLsForNode` | Node name lookup |
| `trace` | Serialization, Python, and unexpected 500 paths | Include one stack trace in those error responses |
