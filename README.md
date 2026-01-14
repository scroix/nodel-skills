# nodel-skills

Agent skills for working with Nodel - Museums Victoria's distributed digital media control framework.

## Installation

### Claude Code

```bash
/plugin marketplace add scroix/nodel-skills
/plugin install scroix@nodel-skills
```

### Manual Installation

Copy the `skills/` directory to your `.claude/skills/` folder.

## Available Skills

| Skill | Description |
|-------|-------------|
| `nodel-recipes` | Write Nodel node recipes using Jython 2.5 with the toolkit API |
| `nodel-use` | Interact with running Nodel instances via REST API |
| `nodel-frontend` | Build custom frontends and dashboards for Nodel nodes |

## About Nodel

Nodel is an open-source digital media control system designed for museums, galleries, and corporate environments. It provides a distributed, node-based architecture for controlling programmable devices across a network.

Key technologies:
- **Core**: Java 11+ with Jython 2.5.4 scripting
- **Web UI**: Bootstrap-based with XSL templates
- **Discovery**: Multicast DNS for automatic node discovery
- **API**: REST endpoints for programmatic access

## License

MIT License - see [LICENSE](LICENSE) for details.
