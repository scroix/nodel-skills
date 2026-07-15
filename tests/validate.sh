#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
NODEL_SOURCE="${NODEL_SOURCE:-/Users/scroix/sandbox/nodel/host/nodel-scroix}"
NODEL_PORT="${NODEL_PORT:-18085}"

if [[ ! -x "$NODEL_SOURCE/gradlew" ]]; then
  echo "Nodel source was not found at $NODEL_SOURCE (override with NODEL_SOURCE)." >&2
  exit 1
fi

if lsof -nP -iTCP:"$NODEL_PORT" -sTCP:LISTEN >/dev/null 2>&1; then
  echo "Port $NODEL_PORT is already in use; refusing to stop an unrelated process." >&2
  exit 1
fi

echo "[build] Building the Nodel host fat jar from $NODEL_SOURCE"
(
  cd "$NODEL_SOURCE"
  ./gradlew -q :nodel-jyhost:fatJar
)

shopt -s nullglob
JARS=("$NODEL_SOURCE"/nodel-jyhost/build/distributions/standalone/nodelhost-*.jar)

if ((${#JARS[@]} == 0)); then
  echo "Gradle completed but no nodelhost fat jar was found." >&2
  exit 1
fi

JAR="$(ls -t "${JARS[@]}" | head -n 1)"

cd "$REPO_ROOT"
exec python3 tests/validate.py \
  --jar "$JAR" \
  --nodel-source "$NODEL_SOURCE" \
  --port "$NODEL_PORT"
