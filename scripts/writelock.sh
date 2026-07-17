#!/usr/bin/env bash
# writelock.sh: advisory write-lock for graph-mutating wiki operations.
#
# WHY: a shared wiki workspace (synced folder, multiple machines) can have
# two processes writing the shared graph files (log.md, index.md,
# referenced_by[] blocks) near-simultaneously. File-sync services resolve
# that as a "conflicted copy" rather than a clean merge, silently corrupting
# the cross-reference spine.
#
# WHAT THIS CHECKS: whether an advisory lock file is present, and whether it
# is actively held or stale (older than the staleness window, or its holder
# process is gone on the same host).
#
# WHAT THIS DOES NOT CHECK: it does not enforce anything at the filesystem
# level. Graph-mutating scripts must `acquire` before mutating and `release`
# after. Agents must `check` before any graph-mutating write and refuse,
# telling the user to retry, while the lock is held.
#
# Cross-machine note: PID liveness is only meaningful on the host that took
# the lock. Age-based staleness is the robust cross-machine signal.
#
# Usage:
#   writelock.sh [--root PATH] acquire "<holder>" [pid]   # take the lock; exit 1 if held
#   writelock.sh [--root PATH] release                    # drop the lock (no-op if not held)
#   writelock.sh [--root PATH] check                      # exit 0 if free/stale, 1 if held
#   writelock.sh [--root PATH] status                     # human-readable state; exit 0
#
# --root defaults to the current working directory (or $WIKI_ROOT if set).
# The lock file lives at <root>/.claude/health/.writelock. Staleness window
# defaults to 1800 seconds (30 minutes); override with WRITELOCK_STALE_SECONDS.
#
# [pid] is optional and is the CALLER's long-lived pid (e.g. $$ from the
# wrapping script), NOT this helper's. Pass it only if the caller stays
# alive for the whole critical section; it enables faster same-host stale
# detection. Omit it and staleness is purely age-based, which is the robust
# cross-machine behavior. The helper never derives pid from its own $$
# because that process exits the moment `acquire` returns.

set -euo pipefail

ROOT="${WIKI_ROOT:-$PWD}"
if [ "${1:-}" = "--root" ]; then
  ROOT="${2:?--root requires a path}"
  shift 2
fi

LOCK="$ROOT/.claude/health/.writelock"
STALE_SECONDS="${WRITELOCK_STALE_SECONDS:-1800}"   # 30 min default

now_epoch() { date -u +%s; }
now_iso()   { date -u +%Y-%m-%dT%H:%M:%SZ; }

read_lock_field() {
  # $1 = key; prints value or empty
  [ -f "$LOCK" ] || return 0
  grep -E "^$1=" "$LOCK" 2>/dev/null | head -1 | cut -d= -f2- || true
}

lock_is_stale() {
  # exit 0 (true) if the lock is absent or stale, 1 (false) if actively held
  [ -f "$LOCK" ] || return 0
  local started_epoch host pid age
  started_epoch="$(read_lock_field started_epoch)"
  host="$(read_lock_field host)"
  pid="$(read_lock_field pid)"
  if [ -n "$started_epoch" ]; then
    age=$(( $(now_epoch) - started_epoch ))
    if [ "$age" -ge "$STALE_SECONDS" ]; then
      return 0   # aged out, so stale
    fi
  fi
  # Same-host PID liveness as a faster stale signal.
  if [ "$host" = "$(hostname)" ] && [ -n "$pid" ]; then
    if ! kill -0 "$pid" 2>/dev/null; then
      return 0   # holder process gone, so stale
    fi
  fi
  return 1        # young and (plausibly) alive, so actively held
}

print_status() {
  if [ ! -f "$LOCK" ]; then
    echo "writelock: FREE"
    return
  fi
  local holder started_iso host pid
  holder="$(read_lock_field holder)"
  started_iso="$(read_lock_field started_iso)"
  host="$(read_lock_field host)"
  pid="$(read_lock_field pid)"
  if lock_is_stale; then
    echo "writelock: STALE (held by '${holder:-?}' on ${host:-?} pid ${pid:-?} since ${started_iso:-?}; exceeds ${STALE_SECONDS}s or holder gone; safe to override)"
  else
    echo "writelock: HELD by '${holder:-?}' on ${host:-?} pid ${pid:-?} since ${started_iso:-?}"
  fi
}

cmd="${1:-status}"

case "$cmd" in
  acquire)
    holder="${2:-unknown}"
    caller_pid="${3:-}"
    if [ -f "$LOCK" ] && ! lock_is_stale; then
      echo "writelock: REFUSED. $(print_status)" >&2
      exit 1
    fi
    if [ -f "$LOCK" ]; then
      echo "writelock: overriding stale lock. $(print_status)" >&2
    fi
    mkdir -p "$(dirname "$LOCK")"
    {
      echo "holder=$holder"
      echo "host=$(hostname)"
      echo "pid=$caller_pid"
      echo "started_iso=$(now_iso)"
      echo "started_epoch=$(now_epoch)"
    } > "$LOCK"
    echo "writelock: ACQUIRED by '$holder'"
    ;;
  release)
    if [ -f "$LOCK" ]; then
      rm -f "$LOCK"
      echo "writelock: RELEASED"
    else
      echo "writelock: already free (no-op)"
    fi
    ;;
  check)
    if lock_is_stale; then
      print_status
      exit 0
    else
      print_status
      exit 1
    fi
    ;;
  status)
    print_status
    ;;
  *)
    echo "usage: writelock.sh [--root PATH] {acquire \"<holder>\" [pid]|release|check|status}" >&2
    exit 2
    ;;
esac
