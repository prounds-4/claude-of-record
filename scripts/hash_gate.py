#!/usr/bin/env python3
"""Content-hash gate for staging new source documents into a wiki workspace.

Problem: upstream document systems detect "new" files by path, size, and
mtime, so a renamed or re-filed copy of a document already in Originals/
looks new, gets pulled again, and lands in the triage queue as false work.

What this script checks and does:
  - Judges candidate files by content (SHA-256) against everything already
    in <root>/Originals/.
  - index: builds or refreshes the hash index of Originals/. Incremental:
    only rehashes files whose size or mtime changed; drops entries for
    deleted files. Index lives at
    <root>/.claude/health/originals-hash-index.json (regenerable tool
    output, not wiki content).
  - check <paths...>: hashes candidate files (or directories, recursed) and
    classifies each against the index:
      duplicate       byte-identical file already in Originals/
      name-collision  same filename exists but bytes differ (likely a
                      revision; worth a look)
      novel           content not in Originals/
    Writes <root>/.claude/health/hash-gate-report.md and prints a summary.
    Duplicates are reported, never silently dropped: a re-upload's location
    and timing can themselves be interesting.
    --stage DEST copies novel files (only) into DEST, preserving each
    candidate's relative path.

What this script does NOT check:
  - It does not classify or ingest anything; it only gates staging.
  - It does not compare file contents beyond the hash (no near-duplicate or
    revision diffing).
  - It does not verify that staged files are valid documents of any kind.

Dependencies: python3 stdlib only.

Usage:
  python3 hash_gate.py [--root PATH] index
  python3 hash_gate.py [--root PATH] check <paths...> [--stage DEST]

--root defaults to the current working directory. Directories named in
--exclude-dir (default: external) at the top level of Originals/ are
skipped when indexing; the default matches the convention of keeping
placeholder stubs for not-downloaded upstream files under
Originals/external/.
"""

import argparse
import hashlib
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

EXCLUDE_NAMES = {".DS_Store", "Icon\r"}
CHUNK = 4 * 1024 * 1024


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            b = f.read(CHUNK)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def iter_originals(originals: Path, exclude_dirs: set):
    for p in sorted(originals.rglob("*")):
        if not p.is_file() or p.is_symlink():
            continue
        if p.name in EXCLUDE_NAMES:
            continue
        rel = p.relative_to(originals)
        if rel.parts and rel.parts[0] in exclude_dirs:
            continue
        yield p


def load_index(index_path: Path) -> dict:
    if index_path.exists():
        return json.loads(index_path.read_text())
    return {"generated_at": None, "files": {}}


def cmd_index(args, root: Path) -> int:
    originals = root / "Originals"
    if not originals.exists():
        print(f"ERROR: {originals} does not exist; is --root a wiki workspace?",
              file=sys.stderr)
        return 2
    health = root / ".claude" / "health"
    index_path = health / "originals-hash-index.json"

    idx = load_index(index_path)
    files = idx["files"]
    seen = set()
    rehashed = kept = failed = 0
    for p in iter_originals(originals, set(args.exclude_dir)):
        rel = str(p.relative_to(originals))
        seen.add(rel)
        st = p.stat()
        prev = files.get(rel)
        if prev and prev["size"] == st.st_size and prev["mtime"] == int(st.st_mtime):
            kept += 1
            continue
        try:
            digest = sha256_file(p)
        except OSError as e:
            print(f"  UNREADABLE (skipped): {rel} ({e})", file=sys.stderr)
            failed += 1
            continue
        files[rel] = {"sha256": digest, "size": st.st_size, "mtime": int(st.st_mtime)}
        rehashed += 1
        if rehashed % 500 == 0:
            print(f"  ...hashed {rehashed}")
    removed = [rel for rel in list(files) if rel not in seen]
    for rel in removed:
        del files[rel]
    idx["generated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    health.mkdir(parents=True, exist_ok=True)
    index_path.write_text(json.dumps(idx, indent=0))
    print(f"Index: {len(files)} files ({rehashed} hashed, {kept} unchanged, "
          f"{len(removed)} removed, {failed} unreadable)")
    return 1 if failed else 0


def iter_candidates(paths):
    for raw in paths:
        p = Path(raw).expanduser()
        if p.is_file():
            yield p.parent, p
        elif p.is_dir():
            for f in sorted(p.rglob("*")):
                if f.is_file() and not f.is_symlink() and f.name not in EXCLUDE_NAMES:
                    yield p, f
        else:
            print(f"  WARNING: no such path, skipped: {raw}", file=sys.stderr)


def cmd_check(args, root: Path) -> int:
    health = root / ".claude" / "health"
    index_path = health / "originals-hash-index.json"
    report_path = health / "hash-gate-report.md"

    idx = load_index(index_path)
    files = idx["files"]
    if not files:
        print("ERROR: index is empty. Run `hash_gate.py index` first.",
              file=sys.stderr)
        return 2
    by_hash = {}
    by_name = {}
    for rel, meta in files.items():
        by_hash.setdefault(meta["sha256"], []).append(rel)
        by_name.setdefault(Path(rel).name, []).append(rel)

    duplicates, collisions, novel, unreadable = [], [], [], []
    seen_cand = {}   # candidate-vs-candidate dedup
    for base, cand in iter_candidates(args.paths):
        try:
            digest = sha256_file(cand)
        except OSError as e:
            unreadable.append((cand, str(e)))
            continue
        if digest in by_hash:
            duplicates.append((cand, by_hash[digest]))
        elif digest in seen_cand:
            duplicates.append((cand, [f"(candidate) {seen_cand[digest]}"]))
        elif cand.name in by_name:
            collisions.append((cand, by_name[cand.name]))
            seen_cand[digest] = cand
        else:
            novel.append((base, cand))
            seen_cand[digest] = cand

    staged = []
    if args.stage:
        dest_root = Path(args.stage).expanduser()
        for base, cand in novel:
            rel = (cand.relative_to(base)
                   if base in cand.parents or base == cand.parent
                   else Path(cand.name))
            dest = dest_root / rel
            if dest.exists():
                print(f"  stage skipped (already at destination): {dest}",
                      file=sys.stderr)
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(cand, dest)
            staged.append(dest)

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        "# Hash-gate report",
        "",
        f"_Regenerated {now} by hash_gate.py check. Index of {len(files)} "
        f"Originals/ files (built {idx['generated_at']})._",
        "",
        f"**Candidates: {len(duplicates) + len(collisions) + len(novel) + len(unreadable)}: "
        f"{len(novel)} novel, {len(duplicates)} byte-identical duplicates, "
        f"{len(collisions)} name collisions (same name, different bytes), "
        f"{len(unreadable)} unreadable.**",
        "",
        "## Novel (content not in Originals/)",
        "",
    ]
    lines += [f"- `{c}`" for _, c in novel] or ["_none_"]
    lines += ["", "## Name collisions: same filename in Originals/, "
                  "different bytes (likely revisions; review)", ""]
    lines += [f"- `{c}` vs " + ", ".join(f"`Originals/{r}`" for r in rels)
              for c, rels in collisions] or ["_none_"]
    lines += ["", "## Byte-identical duplicates (already in corpus; NOT staged)", ""]
    lines += [f"- `{c}` = " + ", ".join(f"`Originals/{r}`" for r in rels)
              for c, rels in duplicates] or ["_none_"]
    if unreadable:
        lines += ["", "## Unreadable", ""] + [f"- `{c}` ({e})" for c, e in unreadable]
    if args.stage:
        lines += ["", f"## Staged to `{args.stage}`", ""]
        lines += [f"- `{d}`" for d in staged] or ["_none_"]
    lines.append("")
    health.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines))

    print(f"novel={len(novel)} duplicate={len(duplicates)} "
          f"name-collision={len(collisions)} unreadable={len(unreadable)}"
          + (f" staged={len(staged)}" if args.stage else ""))
    print(f"Report: {report_path}")
    return 0


def main():
    # The common flags use SUPPRESS defaults so a value given before the
    # subcommand is not clobbered by the subparser re-applying defaults.
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--root", default=argparse.SUPPRESS,
                        help="Wiki workspace root (default: current directory).")
    common.add_argument("--exclude-dir", action="append",
                        default=argparse.SUPPRESS, metavar="NAME",
                        help="Top-level Originals/ subdirectory to skip when "
                             "indexing (repeatable; default: external).")

    ap = argparse.ArgumentParser(
        description=__doc__, parents=[common],
        formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("index", parents=[common],
                   help="Build/refresh the Originals/ hash index (incremental).")
    ck = sub.add_parser("check", parents=[common],
                        help="Classify candidate files against the index.")
    ck.add_argument("paths", nargs="+", help="Candidate files or directories.")
    ck.add_argument("--stage",
                    help="Copy novel files (only) into this directory, "
                         "preserving relative paths.")
    args = ap.parse_args()
    if not hasattr(args, "root"):
        args.root = "."
    if not hasattr(args, "exclude_dir"):
        args.exclude_dir = ["external"]

    root = Path(args.root).expanduser().resolve()
    if args.cmd == "index":
        sys.exit(cmd_index(args, root))
    sys.exit(cmd_check(args, root))


if __name__ == "__main__":
    main()
