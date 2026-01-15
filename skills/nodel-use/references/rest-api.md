# Nodel REST API Reference

Complete reference for all Nodel REST API endpoints.

## Base URL

Default: `http://localhost:8085`

The port can be configured with `-p` flag when starting Nodel.

## Host-Level Endpoints

### Node Discovery

```bash
# Get all local nodes
curl http://localhost:8085/REST/nodes
# Returns: {"Node Name": {...}, "Other Node": {...}}

# Get all discovered nodes on network
curl http://localhost:8085/REST/allNodes
# Returns nodes from all Nodel hosts on the multicast group
```

### Framework Logs

```bash
# Get framework logs
curl "http://localhost:8085/REST/logs?from=0&max=50"

# Long-poll for new logs
curl "http://localhost:8085/REST/logs?from=12345&max=50&timeout=5000"

# Warning logs only
curl "http://localhost:8085/REST/warningLogs?from=0&max=50"
```

### System Information

```bash
# Diagnostics (thread pools, memory, etc.)
curl http://localhost:8085/REST/diagnostics

# Python toolkit reference
curl http://localhost:8085/REST/toolkit
```

### Recipe Management

```bash
# List available recipes
curl http://localhost:8085/REST/recipes/list
# Returns: ["recipes/device-control", "recipes/http-api", ...]

# Create node from recipe
curl -X POST "http://localhost:8085/REST/newNode?base=recipes/device-control&name=My%20New%20Node"
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
curl -X POST "http://localhost:8085/REST/nodes/My%20Node/actions/Refresh/call"
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
# Returns: {"DisplayPower": {"node": "Display Node", "action": "Power"}}

# Save remote bindings
curl -X POST "http://localhost:8085/REST/nodes/My%20Node/remote/save" \
  -H "Content-Type: application/json" \
  -d '{"DisplayStatus": {"node": "Display Node", "event": "Status"}}'
```

### Script Management

```bash
# Get raw script source
curl http://localhost:8085/REST/nodes/My%20Node/script/raw
# Returns: plain text Python script

# Save script
curl -X POST "http://localhost:8085/REST/nodes/My%20Node/script/save" \
  -H "Content-Type: text/plain" \
  --data-binary @script.py

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
curl -X POST "http://localhost:8085/REST/nodes/My%20Node/restart"

# Check if restarted (for waiting after restart)
curl "http://localhost:8085/REST/nodes/My%20Node/hasRestarted?timestamp=1705312200000&timeout=5000"

# Rename node
curl -X POST "http://localhost:8085/REST/nodes/My%20Node/rename?newName=New%20Name"

# Delete node (requires confirmation)
curl -X POST "http://localhost:8085/REST/nodes/My%20Node/remove?confirm=true"
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
curl -X POST "http://localhost:8085/REST/nodes/My%20Node/files/delete?path=old-file.txt"
```

## WebSocket API

Real-time activity streaming:

```
ws://localhost:8085/nodes/{nodeName}
```

Message types:
- `activityHistory` - Initial array of all activity (sent on connect)
- `activity` - Single activity entry (sent on changes)
- `ping` - Heartbeat every 45 seconds

## Error Responses

```json
{
  "code": "404",
  "error": "EndpointNotFoundException",
  "message": "Node not found",
  "cause": {...}
}
```

Add `?trace` to any endpoint for full stack traces in error responses.

## Common HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad request (invalid parameters) |
| 404 | Node or endpoint not found |
| 500 | Server error (check console) |

## Query Parameters

| Parameter | Endpoints | Purpose |
|-----------|-----------|---------|
| `from` | console, logs, activity | Start sequence number |
| `max` | console, logs | Maximum entries to return |
| `timeout` | console, logs | Long-poll timeout in ms |
| `trace` | Any | Include stack traces in errors |
