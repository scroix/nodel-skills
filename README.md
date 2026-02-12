Agent skills for working with Nodel - Museums Victoria's distributed digital media control framework.

These skills follow the [Agent Skills specification](https://agentskills.io/specification) so they can be used by any skills-compatible agent, including Claude Code and Codex CLI.

## Installation

### Option 1: CLI Install (Recommended)

Use [npx skills](https://github.com/vercel-labs/skills) to install directly:

```bash
# Install all skills from this repository
npx skills add scroix/nodel-skills

# Install specific skills
npx skills add scroix/nodel-skills --skill nodel-recipes nodel-use nodel-frontend

# List available skills
npx skills add scroix/nodel-skills --list
```

### Option 2: Claude Code Plugin

```bash
/plugin marketplace add scroix/nodel-skills
/plugin install nodel@nodel-skills
```

### Option 3: Manual Installation

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

Each directory under `skills/` follows the Agent Skills format.

```text
skills/[skill-name]/
├── SKILL.md      - Required instructions and trigger metadata
├── scripts/      - Optional executable utilities
├── references/   - Optional domain/reference docs
└── assets/       - Optional templates and bundled files
```
