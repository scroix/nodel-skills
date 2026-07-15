Agent Skills for use with [Nodel](https://nodel.io/).

These skills follow the [Agent Skills](https://agentskills.io/home) specification so they can be used by any skills-compatible agent.

## Installation

### [npx skills](https://skills.sh) (Recommended)

> a multi-agent installer (Claude Code, Codex CLI, Cursor, OpenCode, and others).

```bash
npx skills add scroix/nodel-skills
```

### Claude Code Plugin

```bash
/plugin marketplace add scroix/nodel-skills
/plugin install nodel@nodel-skills
```

## Available Skills

| Skill | Description |
|-------|-------------|
| [`nodel-recipes`](skills/nodel-recipes/) | Write Nodel node recipes using Jython 2.5 with the toolkit API |
| [`nodel-use`](skills/nodel-use/) | Interact with running Nodel instances via REST API |
| [`nodel-frontend`](skills/nodel-frontend/) | Build custom frontends and dashboards for Nodel nodes |
| [`nodel-dev`](skills/nodel-dev/) | Develop the Nodel platform source itself - build, test, and architecture |
