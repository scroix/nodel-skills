---
name: nodel-frontend
description: Build or modify Nodel node dashboards with content/index.xml, CSS, JavaScript, and Nodel XSL components. Use for dashboard layouts, controls, action and event bindings, responsive styling, and browser-side behavior. Do not use for generic web apps, script.py recipe logic, live-host REST operations, or Nodel platform source changes.
---

# Nodel Frontend Development

Build and revise the XML dashboards served from a Nodel node's `content` directory.

## Workflow

1. Inspect the node's actions, events, and existing `content` files before choosing controls.
2. Create or update `content/index.xml`, keeping custom CSS and JavaScript optional.
3. Start with the minimal dashboard below and bind components to the node's real action and event names.
4. Read the component reference before choosing tags or relying on an attribute.
5. Read the pattern guide when composing a complete dashboard, adding custom styling, or handling dynamic behavior.
6. Render the page against a running Nodel node and check the browser console as well as the node console.

## File Layout

```text
nodes/My Node/
├── script.py
├── nodeConfig.json
└── content
    ├── index.xml
    ├── css
    │   └── custom.css
    └── js
        └── custom.js
```

## Minimal Dashboard

```xml
<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet type="text/xsl" href="v1/index.xsl"?>
<pages title='Dashboard' css='css/custom.css' js='js/custom.js'>
  <page title='Main'>
    <row>
      <column xs='12' sm='6'>
        <title>Power</title>
        <button action='Power' arg='On'>Turn On</button>
        <status event='Power'>Current power</status>
      </column>
    </row>
  </page>
</pages>
```

Remove the `css` or `js` attribute when the corresponding file does not exist.

## Critical Renderer Constraints

- Keep the `v1/index.xsl` processing instruction. Nodel transforms the XML through that stylesheet.
- Use the stock component tags and attributes instead of assuming arbitrary HTML passes through.
- Lay out pages with the Bootstrap 3 twelve-column grid (`xs`, `sm`, `md`, and `lg`).
- Use `<image source='...'>`, not `<img>`. Always provide `source`, including for event-backed images.
- Place `<input>` directly under `<header>`; the built-in rendered input type is `checkbox`.
- Put `<row>` elements directly under `<footer>`.
- Setting `core` on `<pages>` skips custom CSS and JavaScript loading.
- Do not listen for a `nodel-event` DOM event. The renderer updates bound elements directly; observe the property it changes when custom JavaScript must react.

## Binding Conventions

- Use `event` to display node state and `action` to send a value.
- Use `join` when the action and event share a name.
- Use `data` for dynamic option or button collections emitted by the node.
- Use `showevent` and `showvalue` for conditional visibility. Some layout components also support `event` and `value`.

## References

- Read [`references/components.md`](references/components.md) when selecting a component, checking supported children, or confirming attributes, sizing, bindings, and renderer caveats.
- Read [`references/patterns.md`](references/patterns.md) when assembling full dashboards, admin locks, dynamic controls, responsive layouts, confirmation flows, or custom CSS and JavaScript.

## Completion Check

- Confirm every bound action and event exists on the target node.
- Confirm optional asset paths match the `content` directory layout.
- Check the page at phone and desktop widths when the layout is responsive.
- Treat XML/XSL errors and browser-console errors as implementation failures.
