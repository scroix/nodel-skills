# Nodel Toolkit API Reference

Complete reference for the Nodel Python toolkit available in node scripts.

## Parameters

Define configurable values that appear in the node's web interface.

```python
# String parameter
param_ipAddress = Parameter({
    'title': 'IP Address',
    'schema': {'type': 'string'},
    'order': 1
})

# Integer with default
param_port = Parameter({
    'title': 'Port',
    'schema': {'type': 'integer'},
    'default': 9999,
    'order': 2
})

# Dropdown selection
param_protocol = Parameter({
    'title': 'Protocol',
    'schema': {'type': 'string', 'enum': ['TCP', 'UDP', 'HTTP']},
    'default': 'TCP',
    'order': 3
})

# Boolean toggle
param_enabled = Parameter({
    'title': 'Enabled',
    'schema': {'type': 'boolean'},
    'default': True
})

# Object with nested properties
param_config = Parameter({
    'title': 'Configuration',
    'schema': {
        'type': 'object',
        'properties': {
            'host': {'type': 'string'},
            'port': {'type': 'integer'}
        }
    }
})
```

## Actions

### Local Actions

Commands this node exposes:

```python
# Decorator style
@local_action({'schema': {'type': 'string', 'enum': ['On', 'Off']}})
def power(arg):
    '''{"group": "Power", "order": 1}'''
    tcp.send('POWER %s\r\n' % arg)

# No argument action
@local_action({})
def refresh(arg=None):
    '''{"group": "Status"}'''
    poll_status()

# Complex argument
@local_action({'schema': {
    'type': 'object',
    'properties': {
        'channel': {'type': 'integer'},
        'value': {'type': 'number'}
    }
}})
def setLevel(arg):
    channel = arg.get('channel', 1)
    value = arg.get('value', 0)
    tcp.send('LEVEL %d %d\r\n' % (channel, value))

# Naming-convention style (equivalent)
def local_action_PowerOn(arg=None):
    '''{"title":"On", "group":"Power"}'''
    tcp.send('POWER ON\r\n')
```

Both decorator style and `local_action_{Name}` naming convention are valid.

### Dynamic Action Creation

```python
# Create actions at runtime
action = create_local_action('Preset 1',
    lambda arg: activate_preset(1),
    {'group': 'Presets', 'order': 1, 'schema': {'type': 'null'}})

# Lookup existing action
existing = lookup_local_action('Preset 1')
if existing:
    existing.call(None)
    last_called = existing.getTimestamp()

# Legacy alias (still supported in existing recipes)
Action('Preset 2', lambda arg: activate_preset(2), {'group': 'Presets'})
```

### Remote Actions

Call actions on other nodes:

```python
# Define remote action (bound via web interface)
remote_action_DisplayPower = RemoteAction()

# Call it
remote_action_DisplayPower.call('On')

# With metadata
remote_action_ProjectorPower = RemoteAction({'group': 'Projector'})

# Create remote action dynamically (optionally suggest binding target)
remote_action_DynPower = create_remote_action(
    'DynPower',
    {'group': 'Projector'},
    suggestedNode='Display Node',
    suggestedAction='Power')

# Lookup by name
same_action = lookup_remote_action('DynPower')
```

## Events

### Local Events

State this node emits:

```python
# Simple event
local_event_Power = LocalEvent({'schema': {'type': 'string'}})
local_event_Power.emit('On')

# Alias for event creation
signal = Signal('Heartbeat', {'group': 'Status'})

# Object event
local_event_Status = LocalEvent({
    'schema': {
        'type': 'object',
        'properties': {
            'level': {'type': 'integer'},
            'message': {'type': 'string'}
        }
    }
})
local_event_Status.emit({'level': 0, 'message': 'OK'})

# Get current value
current = local_event_Status.getArg()
last_update = local_event_Status.getTimestamp()

# Emit only if different
local_event_Power.emitIfDifferent('On')
```

### Dynamic Event Creation

```python
event = create_local_event('Channel 1 Level',
    {'group': 'Channels', 'schema': {'type': 'number'}})

# Add emit handler
def on_emit(value):
    console.info('Channel 1 changed to %s' % value)
event.addEmitHandler(on_emit)

# Legacy alias (still supported)
legacy_event = Event('Channel 2 Level', {'group': 'Channels'})
```

### Remote Events

Receive events from other nodes:

```python
# Define handler function with naming convention: remote_event_{Name}
def remote_event_DisplayStatus(arg):
    '''Handler called when bound remote event emits'''
    console.info('Display status: %s' % arg)

# With metadata via docstring JSON
def remote_event_ProjectorStatus(arg):
    '''{"group":"Projector"}'''
    console.info('Projector: %s' % arg)

# Decorator style
@remote_event({'group': 'Projector'}, suggestedNode='Display Node', suggestedEvent='Status')
def DisplayStatus2(arg):
    console.info('Display status 2: %s' % arg)

# Runtime creation
create_remote_event('DynStatus', lambda arg: console.info(arg),
    {'group': 'Projector'}, suggestedNode='Display Node', suggestedEvent='Status')

event_ref = lookup_remote_event('DynStatus')
```

## Console Logging

```python
console.log("Light gray - verbose/debug")
console.info("Blue - informational")
console.warn("Orange - warning")
console.error("Red - error")
```

## Timers

### Repeating Timer

```python
# Poll every 30 seconds
def poll():
    tcp.send('STATUS?\r\n')

Timer(poll, 30)

# With initial delay (poll after 10s, then every 30s)
Timer(poll, 30, 10)

# Stoppable timer
poller = Timer(poll, 30, stopped=True)
poller.start()
poller.stop()
poller.setInterval(60)  # Change interval
poller.setDelayAndInterval(5, 30)
poller.reset()

# Read timer state
delay_s = poller.getDelay()
interval_s = poller.getInterval()
running = poller.isStarted()
stopped = poller.isStopped()
```

### One-time Call

```python
# Execute after 5 seconds
call(setup_connection, 5)

# Execute thread-safe callback
call_safe(refresh_ui, 0.25)
```

### Request Queue

```python
queue = request_queue(
    received=lambda arg: console.info('Received: %s' % arg),
    sent=lambda: console.log('Sent'),
    timeout=lambda: console.warn('Timeout'))

# Send request and wait for next received packet
queue.request(lambda: udp.send('?'), lambda arg: console.info('Reply: %s' % arg))

# From protocol callback:
# queue.handle((source, data))
```

## Network Protocols

### TCP

```python
# Track connection state via callbacks
_isConnected = False

def on_connected():
    global _isConnected
    _isConnected = True
    console.info('TCP connected')
    poll_status()

def on_disconnected():
    global _isConnected
    _isConnected = False
    console.warn('TCP disconnected')

def on_data(data):
    # data is string without delimiters
    console.log('Received: %s' % data)

def on_sent(data):
    console.log('Sent: %s' % data)

def on_timeout():
    console.warn('TCP timeout')

# Create TCP connection with auto-reconnect
tcp = TCP(
    dest='192.168.1.100:9999',
    connected=on_connected,
    disconnected=on_disconnected,
    received=on_data,
    sent=on_sent,
    timeout=on_timeout,
    sendDelimiters='\r\n',
    receiveDelimiters='\r\n'
)

# Send data
tcp.send('COMMAND\r\n')
tcp.send('RAW DATA')

# Configure connection / receive timeout (milliseconds)
tcp.setTimeout(30000)

# Request/response queue helpers
tcp.request('STATUS?\r\n', lambda resp: console.info('STATUS: %s' % resp))
resp = tcp.requestWaitAndReceive('STATUS?\r\n')
tcp.receive(lambda resp: console.info('Unsolicited: %s' % resp))
tcp.clearQueue()

# Change destination
tcp.setDest('192.168.1.101:9999')

# Check connection state via callback-managed variable
if _isConnected:
    tcp.send('STATUS?\r\n')

# Close
tcp.close()
```

### UDP

```python
udp = UDP(
    dest='192.168.1.100:9999',
    received=on_packet
)

def on_packet(src, data):
    # src is source address:port
    console.info('From %s: %s' % (src, data))

udp.send('DISCOVER')
udp.close()
```

### SSH

```python
def on_ssh_data(data):
    console.info('SSH: %s' % data)

ssh = SSH(
    dest='192.168.1.150:22',
    username='admin',
    password='secret',
    received=on_ssh_data,
    sendDelimiters='\n',
    receiveDelimiters='\n'
)

ssh.send('show version')
ssh.close()
```

### HTTP

```python
# Synchronous GET
response = get_url('http://api.example.com/status')

# Synchronous POST
response = get_url('http://api.example.com/command',
    method='POST',
    post='data here',
    contentType='application/x-www-form-urlencoded')

# JSON POST
response = get_url('http://api.example.com/api',
    method='POST',
    post=json_encode({'action': 'power', 'value': 'on'}),
    contentType='application/json')

# Timeouts are connectTimeout/readTimeout (seconds)
response = get_url('http://api.example.com/status',
    connectTimeout=5,
    readTimeout=10)

# Include response metadata + headers
full = get_url('http://api.example.com/status', fullResponse=True)
console.info('HTTP status: %s %s' % (full.statusCode, full.reason))
body = full.content

# With headers
get_url('http://api.example.com/api',
    headers={'Authorization': 'Bearer token123'})

# Basic auth
get_url('http://api.example.com/api',
    username='user',
    password='pass')

# Optional HTTP client settings (set before first request)
_toolkit.getHttpClient().setProxy('proxy.host:8080', None, None)
_toolkit.getHttpClient().setIgnoreSSL(True)
```

## Process Management

### Long-running Process

```python
# Process with auto-restart
process = Process('tail -f /var/log/syslog',
    stdout=on_stdout,
    stderr=on_stderr,
    started=on_started,
    stopped=on_stopped)

def on_stdout(line):
    console.log('OUT: %s' % line)

def on_stderr(line):
    console.warn('ERR: %s' % line)

process.close()
```

### Quick Process

```python
# One-shot command
quick_process('ls -la',
    finished=on_complete,
    working='/tmp')

def on_complete(result):
    console.info('Exit: %d' % result.code)
    console.info('Stdout: %s' % result.stdout)
    console.info('Stderr: %s' % result.stderr)

# With list arguments
quick_process(['git', 'status'],
    working='/opt/myproject',
    finished=lambda r: console.info(r.stdout))
```

## Utilities

### JSON

```python
# Encode to JSON string
text = json_encode({'key': 'value', 'number': 42})

# Decode from JSON string
obj = json_decode('{"key": "value"}')
```

### Date/Time

```python
# Current datetime
now = date_now()

# Format datetime
formatted = now.toString('yyyy-MM-dd HH:mm:ss')

# Parse datetime
parsed = date_parse('2024-01-15T10:30:00')

# System clock (milliseconds since epoch)
millis = system_clock()

# Create datetime from epoch milliseconds
instant = date_instant(millis)
```

### String Utilities

```python
# Check if blank (None, empty, or whitespace)
if is_blank(value):
    pass

# Safe string conversion
text = str(value) if value is not None else ''

# Collection helpers
if is_empty([]):
    pass

# Constant empty value for comparisons
if value == EMPTY:
    pass

# Deep equality comparison
if same_value(obj_a, obj_b):
    pass
```

### Sequence Generator

```python
# Get next sequence number (useful for ordering)
order = next_seq()
```

## Lifecycle Decorators

```python
@before_main
def bootstrap():
    '''Called before main().'''
    console.info('Bootstrapping...')

def main():
    '''Called when node starts, before parameters are loaded.'''
    console.info('Node starting')

@after_main
def setup():
    '''Called after main() and parameter values are available.'''
    tcp.setDest('%s:%s' % (param_ipAddress, param_port))

@at_cleanup
def cleanup():
    '''Called when node is stopping.'''
    tcp.close()
```

## Node State

```python
# Check if parameter has value
if param_ipAddress is not None and len(param_ipAddress) > 0:
    pass

# Get node name
name = _node.getName()

# Lookup parameter dynamically
ip = lookup_parameter('ipAddress')

# Dynamic node creation
child = Node('Temporary Child')
sub = Subnode('Diagnostics')
release_node(child)
release_node(sub)
```
