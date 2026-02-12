A collection of [Agent Skills](https://agentskills.io/home) for working with Nodel.

## Installation

### Option 1: CLI Install (Recommended)

Use [npx skills](https://skills.sh) to open an interactive installer and choose the skills you want:

```bash
npx skills add scroix/nodel-skills
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
| [`nodel-recipes`](skills/nodel-recipes/) | Write Nodel node recipes using Jython 2.5 with the toolkit API |
| [`nodel-use`](skills/nodel-use/) | Interact with running Nodel instances via REST API |
| [`nodel-frontend`](skills/nodel-frontend/) | Build custom frontends and dashboards for Nodel nodes |
