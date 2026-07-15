param_ipAddress = Parameter({
    'title': 'IP Address',
    'schema': {'type': 'string'},
    'default': '127.0.0.1'
})

param_port = Parameter({
    'title': 'Port',
    'schema': {'type': 'integer'},
    'default': 9999
})

_isConnected = False
_lastReceive = 0
SOURCES = ['HDMI1', 'HDMI2']

tcp = TCP()

local_event_Status = LocalEvent({'schema': {'type': 'object'}})
local_event_Power = LocalEvent({'schema': {'type': 'string'}})
local_event_Source = LocalEvent({'schema': {'type': 'string'}})
local_event_Volume = LocalEvent({'schema': {'type': 'integer'}})
local_event_AdminMode = LocalEvent({'schema': {'type': 'boolean'}})
local_event_DeviceStatus = LocalEvent({'schema': {'type': 'string'}})
local_event_AudioLevel = LocalEvent({'schema': {'type': 'integer'}})
local_event_CurrentValue = LocalEvent({'schema': {'type': 'string'}})
local_event_LongText = LocalEvent({'schema': {'type': 'string'}})


@local_action({'schema': {'type': 'string', 'enum': ['On', 'Off']}})
def power(arg):
    console.info('Power requested: %s' % arg)
    local_event_Power.emit(arg)
    return arg


@local_action({'schema': {
    'type': 'object',
    'properties': {
        'channel': {'type': 'integer'},
        'value': {'type': 'number'}
    }
}})
def setLevel(arg):
    console.info('Level requested: %s' % arg)
    local_event_Status.emit({'level': 0, 'message': 'Level updated'})
    return arg


@local_action({})
def refresh(arg=None):
    poll_status()
    return 'refreshed'


@local_action({'schema': {'type': 'string'}})
def source(arg):
    local_event_Source.emit(arg)


@local_action({'schema': {'type': 'integer'}})
def volume(arg):
    local_event_Volume.emit(arg)


@local_action({'schema': {'type': 'boolean'}})
def adminMode(arg):
    local_event_AdminMode.emit(arg)


def poll_status():
    global _lastReceive
    _lastReceive = system_clock()
    local_event_Status.emit({'level': 0, 'message': 'Ready'})
    console.log('Status polled')


def timer_tick():
    local_event_AudioLevel.emit(25)
    console.info('HARNESS_TIMER_FIRED')


validation_timer = Timer(timer_tick, 3600, 0.05)


def main():
    console.info('HARNESS_RECIPE_STARTED')
    local_event_Power.emit('Off')
    local_event_Source.emit('HDMI1')
    local_event_Volume.emit(40)
    local_event_AdminMode.emit(False)
    local_event_DeviceStatus.emit('Ready')
    local_event_CurrentValue.emit('Fixture value')
    local_event_LongText.emit('The validation fixture is running.')
    poll_status()
