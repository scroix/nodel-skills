# Validation harness

The harness builds and starts a disposable Nodel host, validates the runtime examples in the skills, and removes its temporary host root when it exits.

## Run it

Requirements:

- a JDK 11 or newer (`java` and `javac`)
- `curl`, `python3`, `lsof`, and the Python `websocket-client` package
- Google Chrome or Chromium (set `CHROME_BIN` if it is not in a standard macOS location)
- a Nodel source checkout; the default is `/Users/scroix/sandbox/nodel/host/nodel-scroix`

From the repository root:

```bash
tests/validate.sh
```

Override the source checkout or test port when needed:

```bash
NODEL_SOURCE=/path/to/nodel NODEL_PORT=18086 tests/validate.sh
```

## Check implicit skill selection

[`fixtures/skill-selection.json`](fixtures/skill-selection.json) records positive, negative, and ambiguous prompts with the Nodel skills each prompt should select. Codex chooses skills by matching the task against their frontmatter descriptions. This repository does not replace that model decision with a keyword matcher.

Until Codex exposes a deterministic skill-selection runner, check the fixture in fresh tasks:

1. From the repository root, create a temporary Codex workspace containing only this checkout's Nodel skills:

   ```bash
   EVAL_ROOT="$(mktemp -d)"
   mkdir -p "$EVAL_ROOT/.agents/skills"
   for skill in nodel-recipes nodel-use nodel-frontend nodel-dev; do
     cp -R "$PWD/skills/$skill" "$EVAL_ROOT/.agents/skills/$skill"
   done
   ```

2. Open Codex from `$EVAL_ROOT` and use `/skills` to confirm exactly one copy of each Nodel skill is available. Disable any separately installed copy of the Nodel plugin for this check.
3. Start a fresh Codex task from `$EVAL_ROOT` for each case and paste its `prompt` exactly, without explicitly naming a skill. A read-only task is sufficient because the check concerns selection rather than the generated implementation:

   ```bash
   codex -s read-only -C "$EVAL_ROOT"
   ```

4. Record the Nodel skills Codex announces or loads for the original prompt. Compare that set with `expected_nodel_skills`; order does not matter, and other non-Nodel skills are outside this fixture's scope.
5. Record the Codex version, model, date, and any mismatch. Re-run a mismatch in another fresh task before changing a description because implicit selection is model-driven.

Validate the fixture's JSON syntax with `python3 -m json.tool tests/fixtures/skill-selection.json >/dev/null`. This only checks the fixture format; it is not a selection test.

The script refuses to take over an occupied port. It asks Gradle for the `nodel-jyhost` fat jar, compiles a temporary override that binds Nodel's HTTP listener to loopback only, copies the fixture into a temporary `nodes` and `recipes` root, keeps the Java process attached until validation finishes, and terminates that process on handled exits and interruption signals. The Nodel checkout itself is not modified.

## What it validates

- Every `curl` token in `skills/nodel-use/SKILL.md` and its references must be extractable. An independent Markdown scan guards the inventory. Fenced shell commands and inline curl snippets are executed with the real `curl` binary, restricted to the disposable host and fixture uploads, checked for a 2xx response, and checked against endpoint-specific JSON or text shapes. Action, exec, and restart examples must also leave no new `err` console entries. The pretty-printing pipeline in `curl ... | python -m json.tool` is presentation-only; the curl invocation itself is what is captured and asserted.
- Documentation placeholders are adapted to the disposable host: port 8085 becomes the selected test port, `...` becomes the fixture node REST path, the PJLink recipe path becomes the local sample recipe, generated node names are made unique, and long-poll timeouts are shortened without removing the timeout query.
- Mutating examples are real. Persistent mutations—script, parameter, binding, file, restart, rename, and removal operations—run against freshly created fixture nodes, so no mutation can leak into the next example. The entire host root is discarded afterward.
- The independent `Harness Fixture` recipe must expose the documented parameter, action, and event bindings. Its console must show both `main()` and `Timer` markers and no `err` entries.
- The fixture `index.xml` is fetched with Nodel's XSL renderer and opened in headless Chromium. The check requires transformed component markup, custom JavaScript execution, and no XML/XSL or browser-console renderer errors.

Any new curl example automatically joins the inventory. If its syntax or response shape is unsupported, the harness fails at its documentation file and line instead of silently skipping it.
