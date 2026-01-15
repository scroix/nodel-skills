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
# Decorator style with schema
@local_action({'schema': {'type': 'string', 'enum': ['On', 'Off']}})
def power(arg):
    '''{"group": "Power", "order": 1}'''
    tcp.send('POWER %s\r\n' % arg)

# No argument action
@local_action
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
```

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
```

## Events

### Local Events

State this node emits:

```python
# Simple event
local_event_Power = LocalEvent({'schema': {'type': 'string'}})
local_event_Power.emit('On')

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
```

### Remote Events

Receive events from other nodes:

```python
# Define handler function with naming convention: remote_event_{Name}
def remote_event_DisplayStatus(arg):
    '''Handler called when bound remote event emits'''
    console.info('Display status: %s' % arg)

# With metadata (handler uses same naming convention)
remote_event_ProjectorStatus = RemoteEvent({'group': 'Projector'})

def remote_event_ProjectorStatus(arg):
    '''Nodel binds this function automatically by name'''
    console.info('Projector: %s' % arg)
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
```

### One-time Call

```python
# Execute after 5 seconds
call(setup_connection, 5)
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

# Create TCP connection with auto-reconnect
tcp = TCP(
    dest='192.168.1.100:9999',
    connected=on_connected,
    disconnected=on_disconnected,
    received=on_data,
    timeout=30,
    sendDelimiters='\r\n',
    receiveDelimiters='\r\n'
)

# Send data
tcp.send('COMMAND\r\n')
tcp.send('RAW DATA')

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

# Asynchronous with callback
get_url('http://api.example.com/status',
    complete=on_response,
    timeout=10)

def on_response(response):
    data = json_decode(response)
    console.info('Status: %s' % data)

# With headers
get_url('http://api.example.com/api',
    headers={'Authorization': 'Bearer token123'})

# Basic auth
get_url('http://api.example.com/api',
    username='user',
    password='pass')
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
```

### String Utilities

```python
# Check if blank (None, empty, or whitespace)
if is_blank(value):
    pass

# Safe string conversion
text = str(value) if value is not None else ''
```

### Sequence Generator

```python
# Get next sequence number (useful for ordering)
order = next_seq()
```

## Lifecycle Decorators

```python
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
```
