#!/usr/bin/env bash
# validate.sh: pre-completion validation suite for a wiki workspace.
#
# WHAT THIS CHECKS (four steps, in order):
#   1. Index rebuild        rebuild_index.py regenerates index.md from the
#                           current records/ and topics/ state
#   2. Cross-reference      resolve_refs.py recomputes the inbound graph and
#      resolution           writes broken/pending reports to .claude/health/
#   3. Structural audit     audit.py validates every record against its
#                           type schema (required fields, enums, paths,
#                           dates, links, closed-world keys)
#   4. Semantic audit       audit_semantic.py checks extracted values
#                           against cited sources
#
# All four steps are blocking: any nonzero exit fails the suite. A workspace
# is not "done" until this script exits 0. Note that steps 1 and 2 mutate
# the workspace (index.md, referenced_by[] blocks, health reports); run the
# writelock helper first if the workspace is shared.
#
# WHAT THIS DOES NOT CHECK: sidecar staleness, provenance of figures inside
# shipped deliverables, attribution tagging, or anything a human ships
# outside the workspace. Structural validity plus semantic spot-checks is
# the floor, not the ceiling.
#
# Usage:
#   validate.sh [--root PATH] [--schemas PATH]
#
# --root defaults to the current working directory. --schemas is passed
# through to audit.py to point at a schema directory outside the workspace
# (for example this repository's schemas/ directory).

set -uo pipefail

SCRIPTS_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$PWD"
SCHEMAS=""

while [ $# -gt 0 ]; do
  case "$1" in
    --root)
      ROOT="${2:?--root requires a path}"; shift 2 ;;
    --schemas)
      SCHEMAS="${2:?--schemas requires a path}"; shift 2 ;;
    -h|--help)
      sed -n '2,32p' "$0" | sed 's/^# \{0,1\}//'
      exit 0 ;;
    *)
      echo "validate.sh: unknown argument: $1" >&2
      exit 2 ;;
  esac
done

if [ ! -d "$ROOT/records" ]; then
  echo "ERROR: $ROOT/records does not exist; is --root a wiki workspace?" >&2
  exit 2
fi

FAILED=0
STEP=0

run_step() {
  local name="$1"; shift
  STEP=$((STEP + 1))
  echo ""
  echo "=== Step $STEP: $name ==="
  if "$@"; then
    echo "--- Step $STEP ($name): PASS"
  else
    local rc=$?
    echo "--- Step $STEP ($name): FAIL (exit $rc)"
    FAILED=1
  fi
}

AUDIT_ARGS=(--root "$ROOT")
if [ -n "$SCHEMAS" ]; then
  AUDIT_ARGS+=(--schemas "$SCHEMAS")
fi

run_step "index rebuild"       python3 "$SCRIPTS_DIR/rebuild_index.py" --root "$ROOT"
run_step "cross-reference resolution" python3 "$SCRIPTS_DIR/resolve_refs.py" --root "$ROOT"
run_step "structural audit"    python3 "$SCRIPTS_DIR/audit.py" "${AUDIT_ARGS[@]}"
run_step "semantic audit"      python3 "$SCRIPTS_DIR/audit_semantic.py" --root "$ROOT"

echo ""
if [ "$FAILED" -eq 0 ]; then
  echo "validate.sh: ALL STEPS PASS"
  exit 0
else
  echo "validate.sh: FAILURES PRESENT (see steps above). Fix before declaring the work complete."
  exit 1
fi
