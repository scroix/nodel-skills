# Nodel UI Component Reference

Complete reference for all Nodel frontend UI components.

## Layout Components

### pages (Root Element)

```xml
<pages title='Dashboard' theme='dark' logo='logo.png' css='custom.css' js='custom.js'>
  ...
</pages>
```

| Attribute | Description |
|-----------|-------------|
| `title` | Dashboard title displayed in header |
| `theme` | Passed through to Bootstrap navbar style (`navbar-{theme}`) and CSS file selection (`components.{theme}.css`) |
| `logo` | Path to custom logo image |
| `css` | Path to custom CSS file |
| `js` | Path to custom JavaScript file |
| `core` | Core/admin mode. Skips custom `css`/`js` loading and adds `core` class on `<body>` |

### page

```xml
<page title='Control' action='PageLoad'>
  ...
</page>
```

| Attribute | Description |
|-----------|-------------|
| `title` | Page tab title |
| `action` | Action to call when the page is selected, including the initial programmatic selection |

### pagegroup

```xml
<pagegroup title='Settings'>
  <page title='Audio'>...</page>
  <page title='Video'>...</page>
</pagegroup>
```

Creates dropdown menu for child pages.

### row

```xml
<row>
  <column>...</column>
</row>
```

Horizontal row container for columns.

| Attribute | Description |
|-----------|-------------|
| `showevent` | Event name for row visibility |
| `showvalue` | Value(s) that make the row visible |

### column

```xml
<column sm='6' md='4' lg='3'>
  ...
</column>
```

| Attribute | Description |
|-----------|-------------|
| `xs` | Extra small screen width (1-12) |
| `sm` | Small screen width (1-12) |
| `md` | Medium screen width (1-12) |
| `lg` | Large screen width (1-12) |
| `event` | Show column when event equals value |
| `value` | Value to match for visibility |
| `showevent` | Alternative visibility event |
| `showvalue` | Alternative visibility value |
| `push` | Bootstrap `col-sm-push-*` class |
| `pull` | Bootstrap `col-sm-pull-*` class |

### group

```xml
<group>
  <title>Group Title</title>
  ...
</group>
```

Visual grouping container with background.

### grid

```xml
<grid>
  <row>
    <cell><button action='1'>1</button></cell>
    <cell><button action='2'>2</button></cell>
    <cell><button action='3'>3</button></cell>
  </row>
</grid>
```

Table-style layout for keypad/matrix controls.

### header

```xml
<header>
  <nodel type='nav'/>
  <input type='checkbox' event='AdminMode' action='AdminMode'>Admin</input>
  <button action='Refresh'>Refresh</button>
</header>
```

Header is special-cased. Supported direct children are `nodel`, `input`, `button`, `switch`.

### footer

```xml
<footer>
  <row>
    <column sm='12'>
      <text>Footer content</text>
    </column>
  </row>
</footer>
```

Fixed footer at bottom. Footer renders `row` children.

## Button Components

### button

```xml
<button action='Power' arg='On' class='btn-success'>Turn On</button>
```

| Attribute | Description |
|-----------|-------------|
| `action` | Action to invoke |
| `arg` | Argument to pass |
| `class` | CSS class (btn-default, btn-primary, btn-success, btn-warning, btn-danger) |
| `confirm` | Require confirmation (`true`, `code` for PIN) |
| `confirmtext` | Custom confirmation message |
| `confirmtitle` | Custom confirmation title |
| `showevent` | Event for visibility |
| `showvalue` | Value for visibility |
| `type` | `momentary` for press-and-hold |
| `action-on` | Action when pressed (momentary) |
| `action-off` | Action when released (momentary) |
| `join` | Combined action/event binding |

### buttongroup

```xml
<buttongroup showevent='Power' showvalue='On'>
  <button action='Source' arg='HDMI1'>HDMI 1</button>
  <button action='Source' arg='HDMI2'>HDMI 2</button>
</buttongroup>
```

Groups buttons horizontally.

### dynamicbuttongroup

```xml
<dynamicbuttongroup join='Source' data='sourceList' confirmtext='Switch?'/>
```

| Attribute | Description |
|-----------|-------------|
| `join` | Action and event name |
| `data` | Event containing button data array |
| `confirmtext` | Confirmation message |
| `confirmtitle` | Confirmation title |

## Switch Components

### switch

```xml
<switch event='Power' action='Power' class='btn-primary'/>
```

Toggle between On/Off states.

| Attribute | Description |
|-----------|-------------|
| `event` | Event to monitor |
| `action` | Action to invoke |
| `class` | CSS class |

### partialswitch

```xml
<partialswitch event='Power' action='Power' confirm='true'/>
```

Shows current value, toggles on click.

| Attribute | Description |
|-----------|-------------|
| `event` | Event to monitor |
| `action` | Action to invoke |
| `confirm` | Require confirmation |
| `join` | Combined action/event |

## Selection Components

### pills

```xml
<pills event='Source' action='Source' confirm='true'>
  <pill value='HDMI1'>HDMI 1</pill>
  <pill value='HDMI2' showevent='HDMI2Enabled' showvalue='true'>HDMI 2</pill>
</pills>
```

Radio button style selection.

### select

```xml
<select event='Source' action='Source' class='btn-default'>
  <item value='HDMI1'>HDMI 1</item>
  <item value='HDMI2'>HDMI 2</item>
</select>
```

Dropdown selection.

### dynamicselect

```xml
<dynamicselect data='SourceList' event='Source' action='Source' class='btn-default'/>
```

| Attribute | Description |
|-----------|-------------|
| `data` | Event containing options array |
| `event` | Event for current value |
| `action` | Action to invoke |

## Range Components

### range

```xml
<range event='Volume' action='Volume' min='0' max='100' step='1'/>
```

| Attribute | Description |
|-----------|-------------|
| `event` | Event for current value |
| `action` | Action to invoke |
| `min` | Minimum value |
| `max` | Maximum value |
| `step` | Step increment |
| `nudge` | Nudge increment. Buttons render only when `action` or `join` is set |
| `type` | `mute` (adds mute button), `vertical` |
| `height` | Height for vertical slider |

`type='mute'` appends `Muting` to the base event/action name. Example: `Volume` -> `VolumeMuting`.

## Status Components

### status

```xml
<status event='DeviceStatus' page='Details'>
  <badge event='Online'/>
  <link url='http://device.local'>Open</link>
  Device Status
</status>
```

| Attribute | Description |
|-----------|-------------|
| `event` | Event for status value |
| `page` | Navigate to page on click |

### badge

```xml
<badge event='OnlineStatus'/>
```

Small colored indicator based on event value.

### partialbadge

```xml
<partialbadge event='PartialStatus'/>
```

Maps `On`, `Off`, `PartiallyOn`, and `PartiallyOff` event strings to a compact label. The optional `on` and `off` attributes replace the displayed labels.

### meter

```xml
<meter event='AudioLevel'/>
<meter event='dBLevel' range='db'/>
```

| Attribute | Description |
|-----------|-------------|
| `event` | Event for meter value |
| `range` | Value range type (`db` for decibels) |

### signal

```xml
<signal event='SignalLevel'>Signal</signal>
<signal event='SignalLevel' range='db'>Signal dB</signal>
```

Signal badge with meter color classes.

### statussleep

```xml
<status event='DisplayStatus'>
  <statussleep action='SleepDisplay'/>
  Display Status
</status>
```

Sleep action button rendered in the status footer.

## Text Components

### title

```xml
<title showevent='AdminMode' showvalue='true'>Admin Settings</title>
```

Section heading.

### subtitle

```xml
<subtitle>Additional information</subtitle>
```

Smaller heading.

### text

```xml
<text>Descriptive text here</text>
```

Paragraph text.

### field

```xml
<field event='CurrentValue'/>
```

Displays event value as text.

### panel

```xml
<panel height='100' event='LogOutput'/>
```

Scrollable text area.

| Attribute | Description |
|-----------|-------------|
| `event` | Event for content |
| `height` | Height in pixels |

## Input Components

### input

```xml
<header>
  <input type='checkbox' event='AdminMode' action='AdminMode'>Admin</input>
</header>
```

`input` is header-only in Nodel dashboards. Use it directly under `<header>`.

| Attribute | Description |
|-----------|-------------|
| `type` | `checkbox` is explicitly handled by default templates |
| `event` | Event for current value |
| `action` | Action to invoke |

## Media Components

### image

```xml
<image source='screenshot.png'/>
<image source='placeholder.png' event='ImageURL'/>
<image source='photo.jpg' width='320' height='180'/>
```

`source` is static image URL/path. `event` can supply a dynamic image URL.

Always provide `source`, including for event-backed images. The XSL renderer emits an `src` attribute immediately; without `source` it becomes `src=""`, so the browser may show a broken image or request the current page until the first string event replaces `src`. Use a real placeholder or a transparent data URI when the initial image should be blank.

`image` is an inline-style exception: `width` and `height` are rendered as `max-width` and `max-height` pixel declarations on the generated `<img>`. A raw XML `style` attribute is not copied through.

### qrcode

```xml
<qrcode text='https://example.com' height='128' help='Scan to connect'/>
<qrcode event='DynamicURL' height='128'/>
```

| Attribute | Description |
|-----------|-------------|
| `text` | Static QR content |
| `event` | Dynamic QR content from event |
| `height` | Size in pixels |
| `help` | Help text tooltip |

## Special Components

### nodel

```xml
<nodel type='nav'/>     <!-- Node navigation -->
<nodel type='edit'/>    <!-- Edit functions -->
<nodel type='hosticon'/> <!-- Host icon in header -->
```

### link

```xml
<!-- Link to another node UI -->
<link node='Display Node'>Open Display Node</link>

<!-- External URL -->
<link url='http://example.com'>Open URL</link>

<!-- Follow the node bound to the parent remote event -->
<status event='DisplayStatus'>
  <link>Open bound display node</link>
</status>
```

A `link` with neither `node` nor `url` uses its parent component's `event` alias, looks that alias up in `/REST/remote`, and opens the node bound to that remote event. It does not treat the event value as a URL.

### icon

```xml
<icon lib='fa' type='power-off' style='fas' size='2'/>
```

| Attribute | Description |
|-----------|-------------|
| `lib` | Icon library (`fa` for Font Awesome) |
| `type` | Icon name |
| `style` | `fas` (solid), `far` (regular), `fab` (brands) |
| `size` | Size multiplier (1-5) |

### lighting

```xml
<lighting action='Color' options='rgbkwaui'/>
<lighting event='ColorEvent' options='rgbkwaui'/>
```

Color selection for lighting control.

`options` supports channel modifiers:
- `k` = colour temperature
- `w` = white
- `a` = amber
- `u` = UV
- `i` = infrared

### gap

```xml
<gap/>           <!-- default 20px -->
<gap value='32'/> <!-- 32px -->
```

Vertical spacing helper.

## Shared Attributes

These attributes are shared by many stock templates, but support is per-component:

| Attribute | Description |
|-----------|-------------|
| `showevent` | Event name for visibility control where the component renders it |
| `showvalue` | Value(s) that make the element visible where the component renders it |
| `class` | CSS class names only on components that explicitly pass classes through |

`showeventarg` support is per-component: the checked source renders it only in templates that explicitly test that attribute. Inline `style` is not generally copied through; the `image` `width`/`height`, `gap` `value`, vertical `range` `height`, and `panel` `height` templates generate their own inline styles. Use the documented sizing attributes or custom CSS for other styling.
