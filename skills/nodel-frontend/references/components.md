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
| `theme` | `light` or `dark` (default: inverse/dark) |
| `logo` | Path to custom logo image |
| `css` | Path to custom CSS file |
| `js` | Path to custom JavaScript file |
| `core` | Set to enable core/admin mode |

### page

```xml
<page title='Control' action='PageLoad'>
  ...
</page>
```

| Attribute | Description |
|-----------|-------------|
| `title` | Page tab title |
| `action` | Action to call when page loads |

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

### group

```xml
<group>
  <title>Group Title</title>
  ...
</group>
```

Visual grouping container with background.

### header

```xml
<header>
  <nodel type='nav'/>
  <button action='Refresh'>Refresh</button>
</header>
```

Custom header content.

### footer

```xml
<footer>
  <text>Footer content</text>
</footer>
```

Fixed footer at bottom.

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
| `nudge` | Nudge button increment |
| `type` | `mute` (add mute button), `vertical` |
| `height` | Height for vertical slider |

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

Shows abbreviated event value.

### meter

```xml
<meter event='AudioLevel'/>
<meter event='dBLevel' range='db'/>
```

| Attribute | Description |
|-----------|-------------|
| `event` | Event for meter value |
| `range` | Value range type (`db` for decibels) |

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
<input type='text' event='SearchTerm' action='Search' placeholder='Search...'/>
```

| Attribute | Description |
|-----------|-------------|
| `type` | `text`, `number`, `checkbox` |
| `event` | Event for current value |
| `action` | Action on submit |
| `placeholder` | Placeholder text |

## Media Components

### img

```xml
<img src='screenshot.png'/>
<img event='ImageURL'/>
```

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
<link url='http://example.com'>Link Text</link>
<link url='http://example.com' target='_blank'>Open in New Tab</link>
```

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

## Common Attributes

These attributes work on most components:

| Attribute | Description |
|-----------|-------------|
| `showevent` | Event name for visibility control |
| `showvalue` | Value(s) that make element visible |
| `class` | CSS class names |
| `style` | Inline CSS styles |
