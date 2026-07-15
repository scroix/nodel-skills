# Debugging Nodel Nodes

Comprehensive guide to troubleshooting and debugging Nodel nodes.

## Contents

- [Debugging workflow](#debugging-workflow)
- [Common issues](#common-issues)
- [Using eval for debugging](#using-eval-for-debugging)
- [Using exec for testing](#using-exec-for-testing)
- [Live log tailing](#live-log-tailing)
- [Framework diagnostics](#framework-diagnostics)
- [Restart and recovery](#restart-and-recovery)

## Debugging Workflow

### 1. Check Node Exists

```bash
curl http://localhost:8085/REST/nodes | python -m json.tool
```

If node is missing:
- Check the nodes/ directory for the node folder
- Check framework logs for folder discovery or host startup errors

A managed node normally remains listed even when its script has load errors; in that case inspect the node's `/console` output instead.

### 1b. Check Discovery and Advertised URLs

```bash
# Discovery service state
curl http://localhost:8085/REST/discovery

# All advertised node URLs
curl "http://localhost:8085/REST/nodeURLs"

# One node's advertised URLs
curl "http://localhost:8085/REST/nodeURLsForNode?name=My%20Node"
```

Use this when a node appears locally but remote bindings cannot resolve it on the network.

### 2. Check Console Output

```bash
# Get last 100 console entries
curl "http://localhost:8085/REST/nodes/My%20Node/console?from=0&max=100"
```

Look for:
- `err` entries (red) - errors during execution
- `warn` entries (orange) - warnings
- Startup messages - confirm node initialized
- Connection status messages

### 3. Check Parameters

```bash
curl http://localhost:8085/REST/nodes/My%20Node/params
```

Verify:
- IP addresses are set
- Ports are correct
- Required parameters have values

### 4. Test Actions

```bash
# List available actions
curl http://localhost:8085/REST/nodes/My%20Node/actions

# Call a simple action
curl -X POST ".../actions/Refresh/call" \
  -H "Content-Type: application/json" \
  -d '{}'

# Check console for results
curl ".../console?from=0&max=20"
```

### 5. Inspect State

```bash
# Check Python variables
curl ".../eval?expr=_isConnected"
curl ".../eval?expr=param_ipAddress"
curl ".../eval?expr=local_event_Status.getArg()"
```

## Common Issues

### Script Won't Start Cleanly

**Symptoms:**
- Node is listed but has script errors in `/console`
- Expected actions, events, or parameters are missing

**Causes:**
1. **Syntax error in script.py**
   ```bash
   # Check framework logs
   curl "http://localhost:8085/REST/logs?from=0&max=50"
   ```
   Look for Python exceptions mentioning your node name.

2. **Top-level load failure**
   `main()` is optional. Nodel explicitly continues when it is absent, so inspect the framework error for the actual script load or binding failure.

3. **Import error**
   Using modules not available in Jython 2.5.

**Fix:** Correct the script.py syntax and wait for auto-reload (or restart Nodel).

### Device Not Responding

**Symptoms:**
- Actions complete but device doesn't respond
- Status shows "No response" or level 2

**Debugging:**
```bash
# Check connection state (requires _isConnected variable set by TCP callbacks)
curl ".../eval?expr=_isConnected"

# Check configured destination inputs (ManagedTCP has no public destination getter)
curl ".../eval?expr=param_ipAddress"
curl ".../eval?expr=param_port"

# Check last receive time
curl ".../eval?expr=_lastReceive"

# Test network from host
ping 192.168.1.100
telnet 192.168.1.100 9999
```

**Common causes:**
- Wrong IP address/port
- Device firewall blocking
- Network routing issue
- Device protocol mismatch

### Actions Not Working

**Symptoms:**
- Action calls return 200 but nothing happens
- No errors in console

**Debugging:**
```bash
# Check action exists
curl ".../actions/Power"

# Check action was called (in logs)
curl ".../logs?from=0&max=20"

# Add debug logging
curl -X POST ".../exec" \
  -H "Content-Type: application/json" \
  -d '{"code":"console.info(\"Connection state: %s, dest: %s:%s\" % (_isConnected, param_ipAddress, param_port))"}'
```

**Common causes:**
- Connection not established
- Wrong command format
- Device not accepting commands

### Events Not Updating

**Symptoms:**
- Event value doesn't change
- Dashboard shows stale data

**Debugging:**
```bash
# Get current event value
curl ".../events/Status"

# Check if emit is being called
curl -X POST ".../exec" \
  -H "Content-Type: application/json" \
  -d '{"code":"console.info(\"Last emit: %s\" % local_event_Status.getArg())"}'

# Force emit to test
curl -X POST ".../exec" \
  -H "Content-Type: application/json" \
  -d '{"code":"local_event_Status.emit({\"level\": 0, \"message\": \"Test\"})"}'
```

**Common causes:**
- Response parsing not triggering emit
- emitIfDifferent not detecting change
- Event not created

### Timer Not Running

**Symptoms:**
- Polling not happening
- No periodic console output

**Debugging:**
```bash
# Check if timer exists and is running
curl ".../eval?expr=dir()"  # Look for timer variables

# Manually call poll function
curl -X POST ".../exec" -H "Content-Type: application/json" -d '{"code":"poll_status()"}'
```

**Common causes:**
- Timer created with `stopped=True`
- Timer function has error
- Timer interval too long

## Using Eval for Debugging

The `/eval` endpoint is powerful for inspection:

```bash
# Check any variable
curl ".../eval?expr=param_ipAddress"

# Check configured destination inputs
curl ".../eval?expr=param_ipAddress"
curl ".../eval?expr=param_port"
curl ".../eval?expr=_isConnected"

# Check event state
curl ".../eval?expr=local_event_Status.getArg()"

# Check list contents
curl ".../eval?expr=len(SOURCES)"
curl ".../eval?expr=SOURCES%5B0%5D%20if%20SOURCES%20else%20None"

# Check global state
curl ".../eval?expr=_lastReceive"
```

## Using Exec for Testing

The `/exec` endpoint runs Python code (requires JSON body with `code` field):

```bash
# Log diagnostic info
curl -X POST ".../exec" \
  -H "Content-Type: application/json" \
  -d '{"code":"console.info(\"Connection state: %s\" % _isConnected)"}'

# Manually trigger poll
curl -X POST ".../exec" \
  -H "Content-Type: application/json" \
  -d '{"code":"poll_status()"}'

# Test emit
curl -X POST ".../exec" \
  -H "Content-Type: application/json" \
  -d '{"code":"local_event_Power.emit(\"On\")"}'

# Reset connection
curl -X POST ".../exec" \
  -H "Content-Type: application/json" \
  -d '{"code":"tcp.setDest(\"%s:%s\" % (param_ipAddress, param_port))"}'
```

## Live Log Tailing

For continuous monitoring, pass the highest returned `seq` plus one as the next `from` value. Sequence numbers are counters, not row offsets; do not increment them by the requested `max` page size.

```bash
curl ".../console?from=0&max=50"
# Read max(entry.seq) from the JSON response, then long-poll with:
curl ".../console?from=<highest-seq-plus-one>&max=50&timeout=5000"
```

## Framework Diagnostics

```bash
# Get system diagnostics
curl http://localhost:8085/REST/diagnostics

# Check thread pools
# Look for "slow-or-dead-locked" warnings

# Check memory usage
# Look for heap statistics
```

## Restart and Recovery

```bash
# Restart single node
curl -X POST ".../restart" \
  -H "Content-Type: application/json" \
  -d '{}'

# Wait for restart to complete using the node's previous ISO started timestamp
curl ".../hasRestarted?timestamp=2026-06-27T19%3A21%3A42.391%2B10%3A00&timeout=10000"

# Verify node is back
curl ".../console?from=0&max=5"
```
