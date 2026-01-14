# Nodel Frontend Patterns

Common patterns and examples for building Nodel dashboards.

## Source Selection Dashboard

```xml
<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet type="text/xsl" href="v1/index.xsl"?>
<pages title='AV Control' theme='dark'>
  <page title='Sources'>
    <row>
      <column sm='6'>
        <title>Video Source</title>
        <pills event='VideoSource' action='VideoSource'>
          <pill value='HDMI1'>HDMI 1</pill>
          <pill value='HDMI2'>HDMI 2</pill>
          <pill value='DP1'>DisplayPort</pill>
          <pill value='USB'>USB-C</pill>
        </pills>
      </column>
      <column sm='6'>
        <title>Audio Source</title>
        <pills event='AudioSource' action='AudioSource'>
          <pill value='HDMI'>HDMI</pill>
          <pill value='Analog'>Analog</pill>
          <pill value='Bluetooth'>Bluetooth</pill>
        </pills>
      </column>
    </row>
  </page>
</pages>
```

## Power and Volume Control

```xml
<page title='Control'>
  <row>
    <column sm='4'>
      <title>Display Power</title>
      <buttongroup>
        <button action='DisplayPower' arg='On' class='btn-success'>
          <icon lib='fa' type='power-off' style='fas'/> On
        </button>
        <button action='DisplayPower' arg='Off' class='btn-danger'>
          <icon lib='fa' type='power-off' style='fas'/> Off
        </button>
      </buttongroup>
      <status event='DisplayStatus'>Current Status</status>
    </column>
    <column sm='4'>
      <title>Volume</title>
      <range event='Volume' action='Volume' type='mute' min='0' max='100' nudge='5'/>
    </column>
    <column sm='4'>
      <title>Display</title>
      <status event='DisplayStatus'>
        <badge event='DisplayOnline'/>
        Display Status
      </status>
    </column>
  </row>
</page>
```

## Admin Lock Pattern

Protect settings with PIN code:

```xml
<row>
  <!-- Lock/Unlock Buttons -->
  <column sm='2'>
    <button join='AdminEnabled' confirm='code' arg='true' showevent='AdminDisabled'>
      <icon lib='fa' size='3' type='lock' style='fas'/>
    </button>
    <button join='AdminEnabled' arg='false' showevent='AdminEnabled'>
      <icon lib='fa' size='3' type='lock-open' style='fas'/>
    </button>
  </column>

  <!-- Protected Controls (only visible when unlocked) -->
  <column sm='10' showevent='AdminEnabled' showvalue='true'>
    <title>Admin Settings</title>
    <button action='Reboot' confirm='true' class='btn-danger'>Reboot System</button>
    <button action='FactoryReset' confirm='true' class='btn-danger'>Factory Reset</button>
  </column>
</row>
```

Supporting Python code:
```python
local_event_AdminEnabled = LocalEvent({'schema': {'type': 'boolean'}})
local_event_AdminDisabled = LocalEvent({'schema': {'type': 'boolean'}})
local_event_ConfirmCode = LocalEvent({'schema': {'type': 'string'}})

ADMIN_TIMEOUT = 5  # minutes

@after_main
def initAdmin():
    local_event_AdminEnabled.emit(False)
    local_event_AdminDisabled.emit(True)
    admin_timer.stop()

admin_timer = Timer(lambda: AdminEnabled(False), ADMIN_TIMEOUT * 60, stopped=True)

@local_action
def AdminEnabled(arg):
    local_event_AdminEnabled.emit(arg)
    local_event_AdminDisabled.emit(not arg)
    if arg:
        admin_timer.setInterval(ADMIN_TIMEOUT * 60)
        admin_timer.start()
    else:
        admin_timer.stop()
```

## Multi-Room Dashboard

```xml
<pages title='Building Control'>
  <pagegroup title='Level 1'>
    <page title='Reception'>
      <row>
        <column sm='6'>
          <title>Display</title>
          <partialswitch join='L1Reception Display Power'/>
        </column>
        <column sm='6'>
          <title>Lighting</title>
          <pills join='L1Reception Lighting'>
            <pill value='Full'>Full</pill>
            <pill value='Dim'>Dim</pill>
            <pill value='Off'>Off</pill>
          </pills>
        </column>
      </row>
    </page>
    <page title='Meeting Room'>...</page>
  </pagegroup>

  <pagegroup title='Level 2'>
    <page title='Office'>...</page>
    <page title='Break Room'>...</page>
  </pagegroup>
</pages>
```

## Status Overview

```xml
<page title='Status'>
  <row>
    <column sm='3'>
      <status event='Projector1 Status' page='Projector1'>
        <badge event='Projector1 Online'/>
        Projector 1
      </status>
    </column>
    <column sm='3'>
      <status event='Projector2 Status' page='Projector2'>
        <badge event='Projector2 Online'/>
        Projector 2
      </status>
    </column>
    <column sm='3'>
      <status event='Display1 Status' page='Display1'>
        <badge event='Display1 Online'/>
        Display 1
      </status>
    </column>
    <column sm='3'>
      <status event='AudioSystem Status' page='Audio'>
        <badge event='AudioSystem Online'/>
        Audio System
      </status>
    </column>
  </row>
</page>
```

## Dynamic Controls

When device capabilities are discovered at runtime:

```xml
<row>
  <column sm='6'>
    <title>Source</title>
    <!-- Options populated from sourceData event -->
    <dynamicselect data='sourceData' event='Source' action='Source' class='btn-default'/>
  </column>
  <column sm='6'>
    <title>Presets</title>
    <!-- Buttons populated from presetData event -->
    <dynamicbuttongroup join='Preset' data='presetData'/>
  </column>
</row>
```

## Confirmation Dialogs

```xml
<!-- Simple confirmation -->
<button action='Shutdown' confirm='true' class='btn-danger'>
  Shutdown System
</button>

<!-- Custom confirmation text -->
<button action='DeleteAll' confirm='true' confirmtext='This will delete all data. Are you sure?' class='btn-danger'>
  Delete All
</button>

<!-- PIN code confirmation -->
<button action='FactoryReset' confirm='code' confirmtext='Enter admin PIN to proceed'>
  Factory Reset
</button>
```

## Visibility Control

```xml
<!-- Show when power is on -->
<column sm='6' showevent='Power' showvalue='On'>
  <title>Controls</title>
  <!-- These controls only appear when device is on -->
</column>

<!-- Show for multiple values -->
<column sm='6' showevent='Mode' showvalue='["Admin","SuperAdmin"]'>
  <title>Admin Controls</title>
</column>

<!-- Conditional button -->
<button action='Settings' showevent='Power' showvalue='On'>
  Settings (only when on)
</button>
```

## Audio Mixer Layout

```xml
<page title='Audio'>
  <row>
    <column sm='2'>
      <title>Mic 1</title>
      <range event='Mic1Volume' action='Mic1Volume' type='vertical' height='300' min='0' max='100'/>
      <switch event='Mic1Mute' action='Mic1Mute' class='btn-danger'/>
    </column>
    <column sm='2'>
      <title>Mic 2</title>
      <range event='Mic2Volume' action='Mic2Volume' type='vertical' height='300' min='0' max='100'/>
      <switch event='Mic2Mute' action='Mic2Mute' class='btn-danger'/>
    </column>
    <column sm='2'>
      <title>PC</title>
      <range event='PCVolume' action='PCVolume' type='vertical' height='300' min='0' max='100'/>
      <switch event='PCMute' action='PCMute' class='btn-danger'/>
    </column>
    <column sm='2'>
      <title>Video</title>
      <range event='VideoVolume' action='VideoVolume' type='vertical' height='300' min='0' max='100'/>
      <switch event='VideoMute' action='VideoMute' class='btn-danger'/>
    </column>
    <column sm='4'>
      <title>Master</title>
      <range event='MasterVolume' action='MasterVolume' type='mute' min='0' max='100' nudge='5'/>
      <meter event='OutputLevel'/>
    </column>
  </row>
</page>
```

## Custom Styling Examples

### custom.css

```css
/* Dark theme adjustments */
.btn-power-on {
  background-color: #27ae60;
  border-color: #27ae60;
}

.btn-power-off {
  background-color: #c0392b;
  border-color: #c0392b;
}

/* Blur images for privacy */
.privacy-blur img {
  filter: blur(8px);
  transition: filter 0.3s ease;
}

.privacy-blur img:hover {
  filter: blur(0);
}

/* Status color overrides */
.status-critical {
  background-color: #e74c3c !important;
}

.status-warning {
  background-color: #f39c12 !important;
}

.status-ok {
  background-color: #27ae60 !important;
}

/* Make title larger */
.panel-heading h3 {
  font-size: 24px;
}
```

### custom.js

```javascript
$(document).ready(function() {
  // Refresh page periodically
  setInterval(function() {
    // Trigger status refresh
  }, 30000);

  // Handle custom keyboard shortcuts
  $(document).keypress(function(e) {
    if (e.key === 'r') {
      // Refresh action
    }
  });
});
```

## Mobile-Friendly Layout

```xml
<row>
  <!-- Full width on mobile, half on tablet+ -->
  <column xs='12' sm='6'>
    <title>Power</title>
    <buttongroup>
      <button action='Power' arg='On' class='btn-success btn-lg'>On</button>
      <button action='Power' arg='Off' class='btn-danger btn-lg'>Off</button>
    </buttongroup>
  </column>

  <column xs='12' sm='6'>
    <title>Volume</title>
    <range event='Volume' action='Volume' min='0' max='100' nudge='10'/>
  </column>
</row>
```
