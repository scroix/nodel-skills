# Common Nodel Recipe Patterns

Reusable patterns for common device control scenarios.

## Device Control with TCP

### Basic Power Control

```python
param_ipAddress = Parameter({'title': 'IP Address', 'schema': {'type': 'string'}})
param_port = Parameter({'title': 'Port', 'schema': {'type': 'integer'}, 'default': 9999})

tcp = None

# Track connection state - must be defined by user and updated in callbacks
_isConnected = False

def main():
    global tcp
    tcp = TCP(dest='%s:%s' % (param_ipAddress or '0.0.0.0', param_port or 9999),
              connected=on_connected,
              disconnected=on_disconnected,
              received=on_data)

@after_main
def setup():
    if param_ipAddress:
        tcp.setDest('%s:%s' % (param_ipAddress, param_port or 9999))

def on_connected():
    global _isConnected
    _isConnected = True
    console.info('Connected')
    poll_status()

def on_disconnected():
    global _isConnected
    _isConnected = False
    console.warn('Disconnected')

def on_data(data):
    if 'POWER=' in data:
        value = data.split('=')[1].strip()
        local_event_Power.emit(value)

local_event_Power = LocalEvent({'schema': {'type': 'string'}})

@local_action({'schema': {'type': 'string', 'enum': ['On', 'Off']}})
def Power(arg):
    '''{"group": "Power"}'''
    tcp.send('POWER %s\r\n' % arg)

def poll_status():
    tcp.send('POWER?\r\n')

Timer(poll_status, 30)
```

## Status Monitoring

### Health Status Pattern

```python
local_event_Status = LocalEvent({
    'group': 'Status',
    'order': 9990,
    'schema': {
        'type': 'object',
        'properties': {
            'level': {'type': 'integer'},  # 0=OK, 1=warn, 2=error
            'message': {'type': 'string'}
        }
    }
})

local_event_LastContact = LocalEvent({
    'group': 'Status',
    'schema': {'type': 'string'}
})

_lastReceive = 0
STATUS_CHECK_INTERVAL = 75  # seconds

def statusCheck():
    global _lastReceive
    diff = (system_clock() - _lastReceive) / 1000.0

    if diff > STATUS_CHECK_INTERVAL + 15:
        previousContact = local_event_LastContact.getArg()
        if previousContact is None:
            message = 'Never responded'
        else:
            message = 'No response since %s' % previousContact
        local_event_Status.emit({'level': 2, 'message': message})
        return

    local_event_Status.emit({'level': 0, 'message': 'OK'})
    local_event_LastContact.emit(str(date_now()))

Timer(statusCheck, STATUS_CHECK_INTERVAL)

# Call this on any successful communication
def mark_received():
    global _lastReceive
    _lastReceive = system_clock()
```

## HTTP API Integration

### JSON-RPC Pattern

```python
HTTP_PORT = 9999

def api_call(method, params):
    req = {
        'id': str(next_seq()),
        'jsonrpc': '2.0',
        'method': method,
        'params': params
    }

    try:
        raw_response = get_url('http://%s:%s' % (param_ipAddress, HTTP_PORT),
                               post=json_encode(req),
                               contentType='application/json')

        response = json_decode(raw_response)

        if response.get('error'):
            raise Exception(response['error'].get('message', 'Unknown error'))

        mark_received()
        return response.get('result')

    except Exception, e:
        console.error('API call failed: %s' % e)
        raise
```

### REST API Pattern

```python
BASE_URL = None

@after_main
def setup():
    global BASE_URL
    BASE_URL = 'http://%s:%s/api/v1' % (param_ipAddress, param_port or 80)

def api_get(endpoint):
    try:
        response = get_url('%s%s' % (BASE_URL, endpoint))
        mark_received()
        return json_decode(response)
    except Exception, e:
        console.error('GET %s failed: %s' % (endpoint, e))
        return None

def api_post(endpoint, data):
    try:
        response = get_url('%s%s' % (BASE_URL, endpoint),
                          method='POST',
                          post=json_encode(data),
                          contentType='application/json')
        mark_received()
        return json_decode(response)
    except Exception, e:
        console.error('POST %s failed: %s' % (endpoint, e))
        return None
```

## Dynamic Actions/Events

### Build from Device Discovery

```python
SOURCES = []
SOURCE_NAMES = []

def discover_sources():
    global SOURCES, SOURCE_NAMES
    response = api_get('/sources')

    SOURCES = response or []
    SOURCE_NAMES = [s['name'] for s in SOURCES]

    # Build action with dynamic enum
    global source_action
    if lookup_local_action('Source'):
        return  # Already created

    source_action = create_local_action('Source',
        lambda arg: select_source(arg),
        {
            'group': 'Sources',
            'schema': {'type': 'string', 'enum': SOURCE_NAMES}
        })

    # Create discrete join for each source
    for source in SOURCE_NAMES:
        create_discrete_source(source)

def create_discrete_source(name):
    event = create_local_event('Source %s' % name,
        {'group': 'Sources', 'schema': {'type': 'boolean'}})

    action = create_local_action('Source %s' % name,
        lambda arg, n=name: select_source(n),
        {'group': 'Sources'})

    # Update discrete event when main event changes
    main_event = lookup_local_event('Source')
    if main_event:
        main_event.addEmitHandler(lambda arg, e=event, n=name: e.emitIfDifferent(arg == n))
```

## Process Control

### Application Launcher

```python
param_command = Parameter({
    'title': 'Command',
    'schema': {'type': 'string'},
    'default': '/usr/bin/app'
})

param_workingDir = Parameter({
    'title': 'Working Directory',
    'schema': {'type': 'string'},
    'default': '/opt/app'
})

_process = None

local_event_Running = LocalEvent({'schema': {'type': 'boolean'}})

@local_action
def Start(arg=None):
    '''{"group": "Control"}'''
    global _process
    if _process:
        console.warn('Already running')
        return

    _process = Process(param_command,
                       working=param_workingDir,
                       stdout=on_stdout,
                       stopped=on_stopped)
    local_event_Running.emit(True)

@local_action
def Stop(arg=None):
    '''{"group": "Control"}'''
    global _process
    if _process:
        _process.close()
        _process = None

def on_stdout(line):
    console.log(line)

def on_stopped():
    global _process
    _process = None
    local_event_Running.emit(False)
    console.warn('Process stopped')
```

## Chained Operations

### Sequential Operations with Callbacks

```python
def sync_all():
    '''Chain: add -> commit -> pull -> push'''
    git_add(lambda: git_commit(lambda: git_pull(lambda: git_push(done))))

def done():
    console.info('Sync complete')

def git_add(complete):
    quick_process(['git', 'add', '-A'],
                  working=param_workingDir,
                  finished=lambda r: complete())

def git_commit(complete):
    quick_process(['git', 'commit', '-a', '-m', 'auto'],
                  working=param_workingDir,
                  finished=lambda r: complete())

def git_pull(complete):
    quick_process(['git', 'pull'],
                  working=param_workingDir,
                  finished=lambda r: complete())

def git_push(complete):
    quick_process(['git', 'push'],
                  working=param_workingDir,
                  finished=lambda r: complete())
```

## Logging Levels

### Debug Log Pattern

```python
local_event_LogLevel = LocalEvent({
    'group': 'Debug',
    'order': 10000,
    'schema': {'type': 'integer'}
})

def log(level, msg):
    '''Log if current level >= threshold'''
    if (local_event_LogLevel.getArg() or 0) >= level:
        console.log(('  ' * level) + msg)

def warn(level, msg):
    if (local_event_LogLevel.getArg() or 0) >= level:
        console.warn(('  ' * level) + msg)

# Usage:
# log(1, 'Basic debug')
# log(2, 'Detailed debug')
# log(3, 'Verbose trace')
```

## Parameter Validation

### Safe Parameter Access

```python
def get_dest():
    '''Safely construct destination address'''
    if is_blank(param_ipAddress):
        return None
    port = param_port if param_port else 9999
    return '%s:%s' % (param_ipAddress, port)

@after_main
def setup():
    dest = get_dest()
    if dest:
        tcp.setDest(dest)
        console.info('Configured: %s' % dest)
    else:
        console.warn('IP address not configured')
```
