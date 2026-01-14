# Debugging Nodel Nodes

Comprehensive guide to troubleshooting and debugging Nodel nodes.

## Debugging Workflow

### 1. Check Node Exists

```bash
curl http://localhost:8085/REST/nodes | python -m json.tool
```

If node is missing:
- Check the nodes/ directory for the node folder
- Look for script.py syntax errors (node won't load)
- Check framework logs for startup errors

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
curl http://localhost:8085/REST/nodes/My%20Node/params/value
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
curl -X POST ".../actions/Refresh/call"

# Check console for results
curl ".../console?from=0&max=20"
```

### 5. Inspect State

```bash
# Check Python variables
curl ".../eval?expr=tcp.isConnected()"
curl ".../eval?expr=param_ipAddress"
curl ".../eval?expr=local_event_Status.getArg()"
```

## Common Issues

### Node Won't Start

**Symptoms:**
- Node missing from `/REST/nodes`
- No console output

**Causes:**
1. **Syntax error in script.py**
   ```bash
   # Check framework logs
   curl "http://localhost:8085/REST/logs?from=0&max=50"
   ```
   Look for Python exceptions mentioning your node name.

2. **Missing main() function**
   Every node needs `def main():` even if empty.

3. **Import error**
   Using modules not available in Jython 2.5.

**Fix:** Correct the script.py syntax and wait for auto-reload (or restart Nodel).

### Device Not Responding

**Symptoms:**
- Actions complete but device doesn't respond
- Status shows "No response" or level 2

**Debugging:**
```bash
# Check connection state
curl ".../eval?expr=tcp.isConnected()"

# Check destination
curl ".../eval?expr=tcp._dest"

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
  -H "Content-Type: text/plain" \
  -d 'console.info("TCP connected: %s, dest: %s" % (tcp.isConnected(), tcp._dest))'
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
  -d 'console.info("Last emit: %s" % local_event_Status.getArg())'

# Force emit to test
curl -X POST ".../exec" \
  -d 'local_event_Status.emit({"level": 0, "message": "Test"})'
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
curl -X POST ".../exec" -d 'poll_status()'
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

# Check object properties
curl ".../eval?expr=tcp._dest"
curl ".../eval?expr=tcp.isConnected()"

# Check event state
curl ".../eval?expr=local_event_Status.getArg()"

# Check list contents
curl ".../eval?expr=len(SOURCES)"
curl ".../eval?expr=SOURCES[0] if SOURCES else None"

# Check global state
curl ".../eval?expr=_lastReceive"
```

## Using Exec for Testing

The `/exec` endpoint runs Python code:

```bash
# Log diagnostic info
curl -X POST ".../exec" \
  -d 'console.info("TCP state: %s" % tcp.isConnected())'

# Manually trigger poll
curl -X POST ".../exec" \
  -d 'poll_status()'

# Test emit
curl -X POST ".../exec" \
  -d 'local_event_Power.emit("On")'

# Reset connection
curl -X POST ".../exec" \
  -d 'tcp.setDest("%s:%s" % (param_ipAddress, param_port))'
```

## Live Log Tailing

For continuous monitoring:

```bash
#!/bin/bash
SEQ=0
while true; do
  RESPONSE=$(curl -s ".../console?from=$SEQ&max=50&timeout=5000")
  echo "$RESPONSE" | python -c "
import sys, json
for entry in json.load(sys.stdin):
    print('[%s] %s: %s' % (entry['console'], entry['timestamp'], entry['comment']))
"
  # Update SEQ from response (would need parsing)
  SEQ=$((SEQ + 50))
done
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
curl -X POST ".../restart"

# Wait for restart to complete
curl ".../hasRestarted?timestamp=$(date +%s)000&timeout=10000"

# Verify node is back
curl ".../console?from=0&max=5"
```
