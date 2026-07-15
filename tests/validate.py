#!/usr/bin/env python3
"""Run the Nodel skills against a disposable local Nodel host."""

from __future__ import annotations

import argparse
from collections import Counter
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen


REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE = REPO_ROOT / "tests" / "fixtures" / "validation-node"
DOC_ROOT = REPO_ROOT / "skills" / "nodel-use"
FIXTURE_NODE = "My Node"
RECIPE_NODE = "Harness Fixture"
START_MARKER = "HARNESS_RECIPE_STARTED"
TIMER_MARKER = "HARNESS_TIMER_FIRED"
ACTIVE_PROCESS_GROUPS: set[int] = set()


class ValidationFailure(RuntimeError):
    pass


@dataclass(frozen=True)
class CurlExample:
    path: Path
    line: int
    command: str

    @property
    def location(self) -> str:
        return f"{self.path.relative_to(REPO_ROOT)}:{self.line}"


def report(message: str) -> None:
    print(message, flush=True)


def terminate_process_group(process: subprocess.Popen, timeout: float = 10) -> None:
    try:
        if process.poll() is None:
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                process.wait(timeout=5)
                return
            try:
                process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait(timeout=5)
    finally:
        ACTIVE_PROCESS_GROUPS.discard(process.pid)


def handle_termination_signal(signum, _frame) -> None:
    for process_group in list(ACTIVE_PROCESS_GROUPS):
        try:
            os.killpg(process_group, signal.SIGTERM)
        except ProcessLookupError:
            ACTIVE_PROCESS_GROUPS.discard(process_group)
    raise KeyboardInterrupt(f"received signal {signum}")


def request(base_url: str, path: str, method: str = "GET", body: bytes | None = None,
            content_type: str = "application/json", timeout: float = 5) -> tuple[int, bytes]:
    headers = {"Content-Type": content_type} if body is not None else {}
    req = Request(base_url + path, data=body, headers=headers, method=method)
    try:
        with urlopen(req, timeout=timeout) as response:
            return response.status, response.read()
    except HTTPError as exc:
        return exc.code, exc.read()


def json_request(base_url: str, path: str, method: str = "GET",
                 payload: Any | None = None, timeout: float = 5) -> Any:
    body = json.dumps(payload).encode() if payload is not None else None
    status, raw = request(base_url, path, method, body, timeout=timeout)
    if not 200 <= status < 300:
        raise ValidationFailure(f"{method} {path} returned HTTP {status}: {raw.decode(errors='replace')}")
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValidationFailure(f"{method} {path} did not return JSON: {raw.decode(errors='replace')}") from exc


def wait_for(predicate, description: str, timeout: float = 30, interval: float = 0.25) -> Any:
    deadline = time.monotonic() + timeout
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            value = predicate()
            if value:
                return value
        except (OSError, URLError, ValidationFailure, json.JSONDecodeError) as exc:
            last_error = exc
        time.sleep(interval)
    detail = f"; last error: {last_error}" if last_error else ""
    raise ValidationFailure(f"Timed out waiting for {description}{detail}")


def extract_curl_examples() -> list[CurlExample]:
    docs = [DOC_ROOT / "SKILL.md", *sorted((DOC_ROOT / "references").glob("*.md"))]
    examples: list[CurlExample] = []
    documented_curl_count = 0

    for path in docs:
        text = path.read_text()
        lines = text.splitlines()
        in_shell_fence = False
        outside_fence = [True] * len(lines)
        index = 0

        while index < len(lines):
            line = lines[index]
            stripped = line.strip()
            if stripped.startswith("```"):
                tag = stripped[3:].strip()
                if in_shell_fence:
                    in_shell_fence = False
                else:
                    in_shell_fence = tag in {"bash", "sh", "shell"}
                outside_fence[index] = False
                index += 1
                continue

            if in_shell_fence:
                outside_fence[index] = False
                documented_curl_count += len(re.findall(r"\bcurl\s", line))
                if line.lstrip().startswith("curl "):
                    start = index + 1
                    parts = [line.strip()]
                    while parts[-1].endswith("\\") and index + 1 < len(lines):
                        index += 1
                        outside_fence[index] = False
                        parts.append(lines[index].strip())
                    command = " ".join(
                        part[:-1].rstrip() if part.endswith("\\") else part
                        for part in parts
                    )
                    examples.append(CurlExample(path, start, command))
            index += 1

        for line_number, line in enumerate(lines, 1):
            if not outside_fence[line_number - 1]:
                continue
            matches = list(re.finditer(r"`(curl [^`]+)`", line))
            documented_curl_count += len(matches)
            for match in matches:
                examples.append(CurlExample(path, line_number, match.group(1)))

    if len(examples) != documented_curl_count:
        raise ValidationFailure(
            f"Curl extractor found {len(examples)} commands but the docs contain "
            f"{documented_curl_count} command-like curl tokens; make the new example executable "
            "or extend the extractor"
        )

    command_pattern = re.compile(
        r"\bcurl\s+(?=(?:https?://|[\"'](?:https?://|\.{3}/)|\.{3}/|-))"
    )
    scanned: list[tuple[Path, int]] = []
    for path in sorted(DOC_ROOT.rglob("*.md")):
        for line_number, line in enumerate(path.read_text().splitlines(), 1):
            scanned.extend((path, line_number) for _ in command_pattern.finditer(line))

    extracted = [(example.path, example.line) for example in examples]
    if Counter(scanned) != Counter(extracted):
        missing = list((Counter(scanned) - Counter(extracted)).elements())
        extra = list((Counter(extracted) - Counter(scanned)).elements())
        details = []
        if missing:
            details.append("unextracted: " + ", ".join(
                f"{path.relative_to(REPO_ROOT)}:{line}" for path, line in missing
            ))
        if extra:
            details.append("not recognized by independent scan: " + ", ".join(
                f"{path.relative_to(REPO_ROOT)}:{line}" for path, line in extra
            ))
        raise ValidationFailure("Curl inventory mismatch; " + "; ".join(details))
    return examples


def copy_fixture(destination: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(FIXTURE, destination)


def build_loopback_override(jar: Path, nodel_source: Path, work_root: Path) -> Path:
    """Compile NodelHostHTTPD with NanoHTTPD's local-interface-only constructor."""
    source = (
        nodel_source
        / "nodel-jyhost"
        / "src"
        / "main"
        / "java"
        / "org"
        / "nodel"
        / "jyhost"
        / "NodelHostHTTPD.java"
    )
    if not source.is_file():
        raise ValidationFailure(f"NodelHostHTTPD source was not found: {source}")

    original = source.read_text()
    constructor = "super(port, directory, false);"
    if original.count(constructor) != 1:
        raise ValidationFailure(
            "Could not apply the disposable host's loopback-only HTTP override; "
            f"expected one {constructor!r} in {source}"
        )

    patched_source = (
        work_root / "loopback-source" / "org" / "nodel" / "jyhost" / "NodelHostHTTPD.java"
    )
    patched_source.parent.mkdir(parents=True)
    patched_source.write_text(
        original.replace(constructor, "super(port, directory, false, true);")
    )
    classes = work_root / "loopback-classes"
    classes.mkdir()
    completed = subprocess.run(
        [
            "javac",
            "--release",
            "11",
            "-cp",
            str(jar),
            "-d",
            str(classes),
            str(patched_source),
        ],
        text=True,
        capture_output=True,
        timeout=60,
    )
    if completed.returncode != 0:
        raise ValidationFailure(
            "Could not compile the disposable host's loopback-only HTTP override:\n"
            + completed.stderr.strip()
        )
    return classes


def assert_loopback_listener(process_id: int, port: int) -> None:
    completed = subprocess.run(
        [
            "lsof",
            "-nP",
            "-a",
            "-p",
            str(process_id),
            f"-iTCP:{port}",
            "-sTCP:LISTEN",
        ],
        text=True,
        capture_output=True,
        timeout=10,
    )
    listeners = [line for line in completed.stdout.splitlines() if "(LISTEN)" in line]
    allowed = re.compile(rf" TCP (?:127\.0\.0\.1|\[::1\]):{port} \(LISTEN\)$")
    if completed.returncode != 0 or not listeners or any(not allowed.search(line) for line in listeners):
        details = completed.stdout.strip() or completed.stderr.strip() or "no listener reported"
        raise ValidationFailure(
            "Disposable Nodel HTTP listener is not restricted to loopback:\n" + details
        )


def node_names(base_url: str) -> set[str]:
    data = json_request(base_url, "/REST/nodes")
    if not isinstance(data, dict):
        raise ValidationFailure("/REST/nodes did not return an object")
    return set(data)


def wait_for_node(base_url: str, name: str, timeout: float = 30) -> None:
    wait_for(lambda: name in node_names(base_url), f"node {name!r}", timeout=timeout)


def wait_for_console_marker(base_url: str, name: str, marker: str, timeout: float = 30) -> list[dict[str, Any]]:
    encoded = quote(name)

    def get_matching_console() -> list[dict[str, Any]] | None:
        entries = json_request(base_url, f"/REST/nodes/{encoded}/console?from=0&max=200")
        if not isinstance(entries, list):
            raise ValidationFailure(f"Console for {name!r} was not a list")
        if any(marker in str(entry.get("comment", "")) for entry in entries if isinstance(entry, dict)):
            return entries
        return None

    return wait_for(get_matching_console, f"{marker!r} in {name!r} console", timeout=timeout)


def assert_console_clean(entries: list[dict[str, Any]], name: str) -> None:
    errors = [entry for entry in entries if entry.get("console") == "err"]
    if errors:
        rendered = "\n".join(str(entry.get("comment", entry)) for entry in errors)
        raise ValidationFailure(f"Node {name!r} logged console errors:\n{rendered}")


def validate_recipe(base_url: str) -> None:
    report("[recipe] Checking Parameter, @local_action, LocalEvent, Timer, and console")
    wait_for_node(base_url, RECIPE_NODE)
    encoded = quote(RECIPE_NODE)

    def reduced_keys(value: dict[str, Any]) -> set[str]:
        return {re.sub(r"[^a-z0-9]", "", key.lower()) for key in value}

    def loaded_bindings() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]] | None:
        actions = json_request(base_url, f"/REST/nodes/{encoded}/actions")
        events = json_request(base_url, f"/REST/nodes/{encoded}/events")
        params = json_request(base_url, f"/REST/nodes/{encoded}/params/schema")
        if not isinstance(actions, dict) or not {"power", "setlevel", "refresh"} <= reduced_keys(actions):
            return None
        if not isinstance(events, dict) or not {"power", "status"} <= reduced_keys(events):
            return None
        return actions, events, params

    actions, events, params = wait_for(
        loaded_bindings,
        f"{RECIPE_NODE!r} recipe bindings",
        timeout=30,
    )
    params_text = json.dumps(params)
    if "ipAddress" not in params_text or "port" not in params_text:
        raise ValidationFailure(f"Recipe parameter schema was incomplete: {params}")

    json_request(
        base_url,
        f"/REST/nodes/{encoded}/actions/Power/call",
        method="POST",
        payload={"arg": "On"},
    )
    entries = wait_for_console_marker(base_url, RECIPE_NODE, TIMER_MARKER)
    if not any(START_MARKER in str(entry.get("comment", "")) for entry in entries):
        raise ValidationFailure(f"Recipe console did not contain {START_MARKER}")
    assert_console_clean(entries, RECIPE_NODE)


def ensure_fixture_node(base_url: str, work_root: Path) -> None:
    node_root = work_root / "nodes" / FIXTURE_NODE
    names = node_names(base_url)

    if FIXTURE_NODE not in names or not node_root.exists():
        raise ValidationFailure(f"stable fixture node {FIXTURE_NODE!r} disappeared")



def console_entries(base_url: str, name: str, from_sequence: int = 0) -> list[dict[str, Any]]:
    entries = json_request(
        base_url,
        f"/REST/nodes/{quote(name)}/console?from={from_sequence}&max=200",
    )
    if not isinstance(entries, list) or not all(isinstance(entry, dict) for entry in entries):
        raise ValidationFailure(f"Console for {name!r} was not a list of objects")
    return entries


def console_cursor(base_url: str, name: str) -> int:
    entries = console_entries(base_url, name)
    sequences = [entry.get("seq") for entry in entries if isinstance(entry.get("seq"), int)]
    return max(sequences, default=-1)


def assert_new_console_clean(base_url: str, name: str, cursor: int, location: str) -> None:
    entries = console_entries(base_url, name, cursor + 1)
    errors = [entry for entry in entries if entry.get("console") == "err"]
    if errors:
        rendered = "\n".join(str(entry.get("comment", entry)) for entry in errors)
        raise ValidationFailure(f"{location} caused console errors in {name!r}:\n{rendered}")


def wait_for_clean_restart(base_url: str, name: str, cursor: int, location: str) -> None:
    def restarted() -> bool:
        entries = console_entries(base_url, name, cursor + 1)
        errors = [entry for entry in entries if entry.get("console") == "err"]
        if errors:
            rendered = "\n".join(str(entry.get("comment", entry)) for entry in errors)
            raise ValidationFailure(f"{location} caused console errors in {name!r}:\n{rendered}")
        return any(START_MARKER in str(entry.get("comment", "")) for entry in entries)

    wait_for(restarted, f"clean restart after {location}", timeout=30)


def create_runtime_node(base_url: str, name: str) -> None:
    status, raw = request(
        base_url,
        "/REST/newNode?base=validation/sample",
        method="POST",
        body=json.dumps({"value": name}).encode(),
    )
    if not 200 <= status < 300:
        raise ValidationFailure(
            f"Could not create isolated node {name!r}: HTTP {status} {raw.decode(errors='replace')}"
        )
    wait_for_node(base_url, name, timeout=30)
    wait_for_console_marker(base_url, name, START_MARKER, timeout=30)


def validate_curl_arguments(tokens: list[str], base_url: str, example: CurlExample) -> str:
    options_with_values = {
        "-X", "--request",
        "-H", "--header",
        "-d", "--data", "--data-raw", "--data-binary",
    }
    urls: list[str] = []
    index = 1
    while index < len(tokens):
        token = tokens[index]
        if token.startswith("-"):
            if token not in options_with_values:
                raise ValidationFailure(f"Disallowed curl option {token!r} at {example.location}")
            if index + 1 >= len(tokens):
                raise ValidationFailure(f"Curl option {token!r} lacks a value at {example.location}")
            value = tokens[index + 1]
            if token in {"-X", "--request"} and value != "POST":
                raise ValidationFailure(f"Unsupported curl method {value!r} at {example.location}")
            elif token in {"-H", "--header"} and value.lower() not in {
                "content-type: application/json",
                "content-type: text/plain",
            }:
                raise ValidationFailure(f"Disallowed curl header {value!r} at {example.location}")
            elif token in {"-d", "--data", "--data-raw", "--data-binary"}:
                if value.startswith("@"):
                    upload = (FIXTURE / value[1:]).resolve()
                    try:
                        upload.relative_to(FIXTURE.resolve())
                    except ValueError as exc:
                        raise ValidationFailure(
                            f"Curl upload escapes the fixture at {example.location}: {value}"
                        ) from exc
                    if not upload.is_file():
                        raise ValidationFailure(
                            f"Curl upload is not a fixture file at {example.location}: {value}"
                        )
                else:
                    try:
                        json.loads(value)
                    except json.JSONDecodeError as exc:
                        raise ValidationFailure(
                            f"Curl request body is not JSON or a fixture file at {example.location}"
                        ) from exc
            index += 2
            continue
        urls.append(token)
        index += 1

    if len(urls) != 1:
        raise ValidationFailure(f"Expected exactly one URL at {example.location}, found {len(urls)}")

    url = urls[0]
    try:
        parsed = urlparse(url)
        expected = urlparse(base_url)
        port = parsed.port
    except ValueError as exc:
        raise ValidationFailure(f"Invalid curl URL at {example.location}: {url}") from exc
    if (
        parsed.scheme != expected.scheme
        or parsed.hostname != expected.hostname
        or port != expected.port
        or parsed.username is not None
        or parsed.password is not None
        or parsed.fragment
    ):
        raise ValidationFailure(
            f"Curl URL must target only the disposable host at {example.location}: {url}"
        )
    return url


def normalise_curl(example: CurlExample, base_url: str, sequence: int,
                   node_name: str = FIXTURE_NODE) -> tuple[list[str], str]:
    import shlex

    try:
        tokens = shlex.split(example.command, comments=True, posix=True)
    except ValueError as exc:
        raise ValidationFailure(f"Could not parse {example.location}: {exc}") from exc
    if "|" in tokens:
        tokens = tokens[:tokens.index("|")]
    if not tokens or tokens[0] != "curl":
        raise ValidationFailure(f"Unsupported curl example at {example.location}: {example.command}")

    node_base = f"{base_url}/REST/nodes/{quote(node_name)}"
    for index, token in enumerate(tokens):
        token = token.replace("http://localhost:8085", base_url)
        token = token.replace(
            f"{base_url}/REST/nodes/{quote(FIXTURE_NODE)}",
            node_base,
        )
        if token.startswith("..."):
            token = node_base + token[3:]
        token = token.replace("nodel-official-recipes/PJLink", "validation/sample")
        token = token.replace("<highest-seq-plus-one>", "0")
        token = re.sub(r"([?&]timeout=)\d+", r"\g<1>100", token)
        tokens[index] = token

    candidate_url = next((token for token in tokens if token.startswith(base_url)), "")
    if not candidate_url:
        raise ValidationFailure(f"No runnable URL in {example.location}: {example.command}")

    if "/REST/newNode?" in candidate_url:
        for index, token in enumerate(tokens[:-1]):
            if token in {"-d", "--data", "--data-raw"}:
                try:
                    payload = json.loads(tokens[index + 1])
                except json.JSONDecodeError as exc:
                    raise ValidationFailure(f"Invalid newNode JSON at {example.location}") from exc
                payload["value"] = f"Harness Created {sequence:03d}"
                tokens[index + 1] = json.dumps(payload, separators=(",", ":"))
                break
    elif urlparse(candidate_url).path.endswith("/rename"):
        for index, token in enumerate(tokens[:-1]):
            if token in {"-d", "--data", "--data-raw"}:
                payload = json.loads(tokens[index + 1])
                payload["value"] = f"Harness Renamed {sequence:03d}"
                tokens[index + 1] = json.dumps(payload, separators=(",", ":"))
                break

    url = validate_curl_arguments(tokens, base_url, example)
    return tokens, url


def parse_json_body(body: bytes, example: CurlExample, expected: str) -> Any:
    try:
        value = json.loads(body)
    except json.JSONDecodeError as exc:
        raise ValidationFailure(
            f"{example.location} expected {expected} JSON, got: {body.decode(errors='replace')[:500]}"
        ) from exc
    if expected == "object" and not isinstance(value, dict):
        raise ValidationFailure(f"{example.location} expected an object, got {type(value).__name__}")
    if expected == "list" and not isinstance(value, list):
        raise ValidationFailure(f"{example.location} expected a list, got {type(value).__name__}")
    return value


def validate_response_shape(example: CurlExample, url: str, body: bytes) -> None:
    path = urlparse(url).path
    list_endpoints = {
        "/REST/allNodes",
        "/REST/nodeURLs",
        "/REST/nodeURLsForNode",
        "/REST/logs",
        "/REST/warningLogs",
        "/REST/recipes/list",
    }
    object_endpoints = {
        "/REST",
        "/REST/nodes",
        "/REST/diagnostics",
        "/REST/toolkit",
    }

    boolean_endpoints = (
        path == "/REST/newNode"
        or path.endswith((
            "/exec",
            "/restart",
            "/rename",
            "/remove",
            "/params/save",
            "/remote/save",
            "/script/save",
            "/files/save",
            "/files/delete",
        ))
        or re.search(r"/actions/[^/]+/call$", path) is not None
    )

    if path.endswith("/script/raw") or path.endswith("/files/contents") or path == "/REST/discovery":
        if not body:
            raise ValidationFailure(f"{example.location} expected a non-empty text response")
        if path == "/REST/discovery" and b"AutoDNS" not in body:
            raise ValidationFailure(f"{example.location} discovery response had an unexpected shape")
        return
    if path in list_endpoints or path.endswith(("/console", "/logs", "/activity", "/files")):
        value = parse_json_body(body, example, "list")
    elif (
        path in object_endpoints
        or re.search(r"/(actions|events|params|remote)$", path)
        or re.search(r"/(params|remote)/schema$", path)
        or re.search(r"/(actions|events)/[^/]+$", path)
    ):
        value = parse_json_body(body, example, "object")
    elif path.endswith("/hasRestarted"):
        value = parse_json_body(body, example, "object")
        if "timestamp" not in value:
            raise ValidationFailure(f"{example.location} restart response lacked timestamp: {value}")
    elif path.endswith("/eval"):
        rendered = body.decode(errors="replace").strip()
        if not rendered or "Traceback" in rendered or "Exception" in rendered:
            raise ValidationFailure(
                f"{example.location} expected a successful evaluation result, got: {rendered[:500]}"
            )
        value = rendered
    elif boolean_endpoints:
        value = parse_json_body(body, example, "boolean true")
        if value is not True:
            raise ValidationFailure(f"{example.location} expected JSON true, got {value!r}")
    else:
        raise ValidationFailure(
            f"{example.location} has no response-shape validator for endpoint {path}; "
            "extend the harness when documenting a new endpoint"
        )

    if path == "/REST/nodes" and FIXTURE_NODE not in value:
        raise ValidationFailure(f"{example.location} node list omitted {FIXTURE_NODE!r}")
    if path == "/REST/toolkit" and not isinstance(value.get("script"), str):
        raise ValidationFailure(f"{example.location} toolkit response lacked script text")
    if path == "/REST/recipes/list" and not any(
        isinstance(item, dict) and item.get("path") == "validation/sample" for item in value
    ):
        raise ValidationFailure(f"{example.location} recipe list omitted validation/sample")
    if path.endswith("/actions") and not any(key.lower() == "power" for key in value):
        raise ValidationFailure(f"{example.location} action list omitted Power")
    if path.endswith("/events") and not any(key.lower() == "status" for key in value):
        raise ValidationFailure(f"{example.location} event list omitted Status")
    if path.endswith("/script/raw") and b"Parameter(" not in body:
        raise ValidationFailure(f"{example.location} raw script response did not contain the fixture recipe")


def validate_curl_docs(base_url: str, work_root: Path) -> int:
    examples = extract_curl_examples()
    by_file: dict[Path, int] = {}
    report(f"[curl] Executing {len(examples)} documented curl examples")

    for sequence, example in enumerate(examples, 1):
        if sequence == 1 or sequence % 10 == 0:
            report(f"[curl] {sequence:03d}/{len(examples)} {example.location}")
        try:
            ensure_fixture_node(base_url, work_root)
        except ValidationFailure as exc:
            raise ValidationFailure(f"Before {example.location}: {exc}") from exc
        node_name = FIXTURE_NODE
        persistent_mutators = (
            "/params/save",
            "/remote/save",
            "/script/save",
            "/restart",
            "/rename",
            "/remove",
            "/files/save",
            "/files/delete",
        )
        if any(endpoint in example.command for endpoint in persistent_mutators):
            node_name = f"Harness Mutation {sequence:03d}"
            create_runtime_node(base_url, node_name)
        tokens, url = normalise_curl(example, base_url, sequence, node_name=node_name)
        by_file[example.path] = by_file.get(example.path, 0) + 1

        path = urlparse(url).path
        watches_console = (
            path.endswith(("/exec", "/restart"))
            or re.search(r"/actions/[^/]+/call$", path) is not None
        )
        cursor = console_cursor(base_url, node_name) if watches_console else None

        with tempfile.NamedTemporaryFile() as response_file:
            command = [
                tokens[0],
                "--silent",
                "--show-error",
                "--max-time",
                "15",
                "--output",
                response_file.name,
                "--write-out",
                "%{http_code}",
                *tokens[1:],
            ]
            completed = subprocess.run(
                command,
                cwd=FIXTURE,
                text=True,
                capture_output=True,
                timeout=20,
            )
            response_file.seek(0)
            body = response_file.read()

        status_text = completed.stdout.strip()
        if completed.returncode != 0:
            raise ValidationFailure(
                f"{example.location} curl exited {completed.returncode}: {completed.stderr.strip()}\n"
                f"Command: {example.command}"
            )
        if not re.fullmatch(r"\d{3}", status_text):
            raise ValidationFailure(f"{example.location} did not report an HTTP status: {status_text!r}")
        status = int(status_text)
        if not 200 <= status < 300:
            raise ValidationFailure(
                f"{example.location} returned HTTP {status}: {body.decode(errors='replace')[:1000]}\n"
                f"Command: {example.command}"
            )
        validate_response_shape(example, url, body)

        if cursor is not None:
            if path.endswith("/restart"):
                wait_for_clean_restart(base_url, node_name, cursor, example.location)
            else:
                assert_new_console_clean(base_url, node_name, cursor, example.location)

        if path.endswith("/rename"):
            renamed = f"Harness Renamed {sequence:03d}"
            wait_for(lambda: renamed in node_names(base_url), "documented isolated rename", timeout=20)
        elif path.endswith("/remove"):
            wait_for(
                lambda: node_name not in node_names(base_url),
                "documented isolated removal",
                timeout=20,
            )

    for path, count in by_file.items():
        report(f"[curl] {path.relative_to(REPO_ROOT)}: {count} passed")
    return len(examples)


def find_chrome() -> Path:
    candidates = []
    if os.environ.get("CHROME_BIN"):
        candidates.append(Path(os.environ["CHROME_BIN"]))
    candidates.extend([
        Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
        Path("/Applications/Chromium.app/Contents/MacOS/Chromium"),
    ])
    playwright_cache = Path.home() / "Library" / "Caches" / "ms-playwright"
    candidates.extend(sorted(
        playwright_cache.glob("chromium_headless_shell-*/chrome-mac/headless_shell"),
        reverse=True,
    ))
    for candidate in candidates:
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate
    raise ValidationFailure("No Chromium browser found; set CHROME_BIN to a Chrome/Chromium executable")


def validate_frontend(base_url: str) -> None:
    report("[frontend] Rendering the documented component fixture in headless Chromium")
    reduced_name = re.sub(r"[\s\-_.]", "", RECIPE_NODE)
    page_url = f"{base_url}/nodes/{reduced_name}/"
    status, xml = request(base_url, f"/nodes/{reduced_name}/index.xml")
    if status != 200 or b"<pages" not in xml:
        raise ValidationFailure(f"Fixture index.xml was not served correctly (HTTP {status})")
    status, xsl = request(base_url, f"/nodes/{reduced_name}/v1/index.xsl")
    if status != 200 or b"xsl:stylesheet" not in xsl:
        raise ValidationFailure(f"Nodel renderer XSL was not served correctly (HTTP {status})")

    try:
        import websocket
    except ImportError as exc:
        raise ValidationFailure(
            "The frontend check needs the websocket-client Python package "
            "(`python3 -m pip install websocket-client`)"
        ) from exc

    chrome = find_chrome()
    browser_errors: list[str] = []
    html = ""
    with tempfile.TemporaryDirectory(prefix="nodel-chrome-") as profile:
        chrome_log_path = Path(profile) / "chrome.log"
        with chrome_log_path.open("wb") as chrome_log:
            process = subprocess.Popen(
                [
                    str(chrome),
                    "--headless=new",
                    "--disable-gpu",
                    "--no-first-run",
                    "--no-default-browser-check",
                    "--remote-debugging-port=0",
                    "--remote-debugging-address=127.0.0.1",
                    "--remote-allow-origins=*",
                    f"--user-data-dir={profile}",
                    "about:blank",
                ],
                stdout=chrome_log,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
            ACTIVE_PROCESS_GROUPS.add(process.pid)
            try:
                port_file = Path(profile) / "DevToolsActivePort"
                wait_for(
                    lambda: port_file.is_file() and len(port_file.read_text().splitlines()) >= 2,
                    "Chromium DevTools endpoint",
                    timeout=20,
                )
                devtools_port = int(port_file.read_text().splitlines()[0])
                target_request = Request(
                    f"http://127.0.0.1:{devtools_port}/json/new?{quote(page_url, safe='')}",
                    method="PUT",
                )
                with urlopen(target_request, timeout=5) as response:
                    target = json.load(response)

                ws = websocket.create_connection(
                    target["webSocketDebuggerUrl"],
                    timeout=1,
                    http_proxy_host=None,
                )
                next_id = 0
                load_seen = False

                def handle_event(message: dict[str, Any]) -> None:
                    nonlocal load_seen
                    method = message.get("method")
                    params = message.get("params", {})
                    if method == "Page.loadEventFired":
                        load_seen = True
                    elif method == "Runtime.exceptionThrown":
                        details = params.get("exceptionDetails", {})
                        description = details.get("exception", {}).get("description")
                        browser_errors.append(description or details.get("text", "JavaScript exception"))
                    elif method == "Runtime.consoleAPICalled" and params.get("type") == "error":
                        values = [arg.get("value", arg.get("description", "")) for arg in params.get("args", [])]
                        browser_errors.append("console.error: " + " ".join(map(str, values)))

                def receive(deadline: float) -> dict[str, Any]:
                    while time.monotonic() < deadline:
                        try:
                            message = json.loads(ws.recv())
                        except websocket.WebSocketTimeoutException:
                            continue
                        handle_event(message)
                        return message
                    raise ValidationFailure("Timed out waiting for a Chromium DevTools response")

                def command(method: str, params: dict[str, Any] | None = None,
                            timeout: float = 10) -> dict[str, Any]:
                    nonlocal next_id
                    next_id += 1
                    message_id = next_id
                    ws.send(json.dumps({"id": message_id, "method": method, "params": params or {}}))
                    deadline = time.monotonic() + timeout
                    while True:
                        message = receive(deadline)
                        if message.get("id") == message_id:
                            if "error" in message:
                                raise ValidationFailure(f"Chromium {method} failed: {message['error']}")
                            return message.get("result", {})

                command("Page.enable")
                command("Runtime.enable")
                navigation = command("Page.navigate", {"url": page_url})
                if navigation.get("errorText"):
                    raise ValidationFailure(f"Browser navigation failed: {navigation['errorText']}")

                load_deadline = time.monotonic() + 20
                while not load_seen:
                    receive(load_deadline)

                render_deadline = time.monotonic() + 20
                while time.monotonic() < render_deadline:
                    evaluation = command(
                        "Runtime.evaluate",
                        {
                            "expression": "document.documentElement.outerHTML",
                            "returnByValue": True,
                        },
                    )
                    html = str(evaluation.get("result", {}).get("value", ""))
                    if 'data-validation-js="loaded"' in html and 'class="navbar' in html:
                        break
                    time.sleep(0.25)
                else:
                    raise ValidationFailure("Timed out waiting for Nodel's transformed component DOM")

                settle_deadline = time.monotonic() + 1
                ws.settimeout(0.1)
                while time.monotonic() < settle_deadline:
                    try:
                        handle_event(json.loads(ws.recv()))
                    except websocket.WebSocketTimeoutException:
                        continue
                evaluation = command(
                    "Runtime.evaluate",
                    {
                        "expression": "document.documentElement.outerHTML",
                        "returnByValue": True,
                    },
                )
                html = str(evaluation.get("result", {}).get("value", ""))
                ws.close()
            except Exception:
                chrome_log.flush()
                tail = chrome_log_path.read_text(errors="replace").splitlines()[-40:]
                if tail:
                    report("[frontend] Last Chromium log lines:\n" + "\n".join(tail))
                raise
            finally:
                terminate_process_group(process, timeout=5)

    lowered = html.lower()
    if browser_errors:
        raise ValidationFailure("Browser renderer errors:\n" + "\n".join(browser_errors))
    if "<parsererror" in lowered or "this page contains the following errors" in lowered:
        raise ValidationFailure("Browser returned an XML/XSL parser error")
    if 'data-validation-error=' in lowered:
        raise ValidationFailure("Fixture error listener observed a JavaScript error")

    required_fragments = [
        'data-validation-js="loaded"',
        "Validation Harness",
        'class="navbar',
        'class="btn',
        'class="range',
        'class="status',
        "Validation fixture",
    ]
    missing = [fragment for fragment in required_fragments if fragment not in html]
    if missing:
        raise ValidationFailure(f"Rendered page omitted expected component output: {missing}")


def run(args: argparse.Namespace) -> None:
    base_url = f"http://127.0.0.1:{args.port}"
    with tempfile.TemporaryDirectory(prefix="nodel-skills-validation-") as temporary:
        work_root = Path(temporary)
        copy_fixture(work_root / "nodes" / FIXTURE_NODE)
        copy_fixture(work_root / "nodes" / RECIPE_NODE)
        copy_fixture(work_root / "recipes" / "validation" / "sample")
        loopback_classes = build_loopback_override(args.jar, args.nodel_source, work_root)
        host_log_path = work_root / "host.log"

        report(f"[host] Starting disposable Nodel host on {base_url}")
        with host_log_path.open("wb") as host_log:
            process = subprocess.Popen(
                [
                    "java",
                    "-cp",
                    os.pathsep.join((str(loopback_classes), str(args.jar))),
                    "org.nodel.jyhost.Launch",
                    "-p",
                    str(args.port),
                    "--disableAdvertisements",
                ],
                cwd=work_root,
                stdin=subprocess.PIPE,
                stdout=host_log,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
            ACTIVE_PROCESS_GROUPS.add(process.pid)
            try:
                def host_ready() -> bool:
                    if process.poll() is not None:
                        raise ValidationFailure(f"Nodel host exited early with status {process.returncode}")
                    status, _ = request(base_url, "/REST", timeout=1)
                    return status == 200

                wait_for(host_ready, "Nodel host HTTP readiness", timeout=60)
                assert_loopback_listener(process.pid, args.port)
                wait_for_node(base_url, FIXTURE_NODE, timeout=40)
                wait_for_node(base_url, RECIPE_NODE, timeout=40)
                validate_recipe(base_url)
                curl_count = validate_curl_docs(base_url, work_root)
                validate_frontend(base_url)
            except Exception:
                host_log.flush()
                tail = host_log_path.read_text(errors="replace").splitlines()[-80:]
                if tail:
                    report("[host] Last host log lines:\n" + "\n".join(tail))
                raise
            finally:
                terminate_process_group(process, timeout=10)

    report(
        f"Validation passed: recipe, {curl_count} curl-doc inventory checks, "
        "and frontend render are clean."
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--jar", type=Path, required=True)
    parser.add_argument("--nodel-source", type=Path, required=True)
    parser.add_argument("--port", type=int, default=18085)
    args = parser.parse_args()
    if not args.jar.is_file():
        parser.error(f"Nodel host jar does not exist: {args.jar}")
    if not args.nodel_source.is_dir():
        parser.error(f"Nodel source does not exist: {args.nodel_source}")
    return args


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, handle_termination_signal)
    signal.signal(signal.SIGHUP, handle_termination_signal)
    try:
        run(parse_args())
    except KeyboardInterrupt:
        print("VALIDATION INTERRUPTED", file=sys.stderr, flush=True)
        raise SystemExit(130)
    except (ValidationFailure, subprocess.TimeoutExpired) as exc:
        print(f"VALIDATION FAILED: {exc}", file=sys.stderr, flush=True)
        raise SystemExit(1)
