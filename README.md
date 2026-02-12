Agent skills for working with Nodel - Museums Victoria's distributed digital media control framework.

These skills follow the [Agent Skills specification](https://agentskills.io/specification) so they can be used by any skills-compatible agent, including Claude Code and Codex CLI.

## Installation

### Claude Code

```bash
/plugin marketplace add scroix/nodel-skills
/plugin install nodel@nodel-skills
```

### npx skills

Install individual skills directly from this repo:

```bash
npx skills add https://github.com/scroix/nodel-skills --skill nodel-recipes
npx skills add https://github.com/scroix/nodel-skills --skill nodel-use
npx skills add https://github.com/scroix/nodel-skills --skill nodel-frontend
```

### Manual Installation

#### Claude Code

Copy the `skills/` directory to your `.claude/skills/` folder.

#### Codex CLI

Copy the `skills/` directory to your Codex skills directory: `$CODEX_HOME/skills` (typically `~/.codex/skills`).

## Available Skills

| Skill | Description |
|-------|-------------|
| `nodel-recipes` | Write Nodel node recipes using Jython 2.5 with the toolkit API |
| `nodel-use` | Interact with running Nodel instances via REST API |
| `nodel-frontend` | Build custom frontends and dashboards for Nodel nodes |

## Repository Structure

Each skill directory follows the Agent Skills format with a required `SKILL.md` plus optional resource folders.

```text
nodel-skills/
├── skills/
│   ├── nodel-recipes/
│   │   ├── SKILL.md
│   │   └── references/
│   ├── nodel-use/
│   │   ├── SKILL.md
│   │   └── references/
│   └── nodel-frontend/
│       ├── SKILL.md
│       └── references/
└── .claude-plugin/
    └── marketplace.json
```

## About Nodel

Nodel is an open-source digital media control system designed for museums, galleries, and corporate environments. It provides a distributed, node-based architecture for controlling programmable devices across a network.

Key technologies:
- **Core**: Java 11+ with Jython 2.5.4 scripting
- **Web UI**: Bootstrap-based with XSL templates
- **Discovery**: Multicast DNS for automatic node discovery
- **API**: REST endpoints for programmatic access
