#!/usr/bin/env python3
"""Structural schema audit of a wiki workspace.

What this script checks:
  - Required-field presence per entity-type schema
  - Enum value validation (a field declared as enum [...] must hold one of
    the declared values)
  - Closed-world frontmatter keys: a record of a governed type (its schema
    carries schema_version) may only carry keys the schema declares
  - Declared source_files paths and sidecars resolve on disk
  - id matches filename
  - type matches directory (schema directory: key, or intra-type consistency)
  - Date sanity (no future dates, no dates outside a configurable range)
  - Index integrity (every record indexed, no stale index entries)
  - Duplicate top-level frontmatter keys (raw-text scan; YAML parsing hides
    them by keeping the last value)
  - Unquoted-value truncation at a YAML comment marker (an unquoted '#'
    silently chops the value)
  - Body markdown links resolve on disk
  - Topic-page freshness (last_synthesized at or after the newest source
    record's ingested_at or updated_at)
  - No dollar amounts or percentages in index.md or topic section headers
  - outputs/ stream-folder naming and shipped-frozen immutability

What this script does NOT check:
  - Semantic correctness: whether extracted values match what the cited
    source documents actually say (that is a separate semantic audit)
  - Sidecar staleness relative to the source PDF
  - Provenance of figures inside deliverables
  - Anything about content quality, attribution tags, or prose

Dependencies: python3 with pyyaml.

Usage:
  python3 audit.py [--root PATH] [--schemas PATH] [--terse]
                   [--min-year N] [--max-year N]
                   [--closed-world {off,warn,fail}]

--root defaults to the current working directory. Schemas are read from
--schemas if given, otherwise <root>/.claude/skills/_schemas/. A whitelist
of known non-violations is read from <root>/.claude/whitelist.yaml if it
exists; an absent file means an empty whitelist.

Exit codes:
  0  clean (or only whitelisted violations / non-blocking warnings)
  1  blocking violations found
  2  environment error (bad root, missing pyyaml)
"""
import argparse
import datetime
import re
import sys
import urllib.parse
from collections import defaultdict, Counter
from datetime import date as Date
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: pyyaml required. Install with: pip3 install pyyaml")
    sys.exit(2)


# Cross-type optional keys allowed on any governed record without being
# re-declared in every schema. updated_at is the date a record's content
# last changed via an enrich or edit operation; the topic-freshness check
# consumes it.
UNIVERSAL_OPTIONAL_KEYS = {'updated_at'}

_STREAM_SLUG_RE = re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')
# Iteration token: optional [v|r]N- prefix, then YYYY-MM-DD, optional -note
_ITERATION_DIR_RE = re.compile(
    r'^(?:(?:v|r)\d+-)?\d{4}-\d{2}-\d{2}(?:-[a-z0-9]+(?:-[a-z0-9]+)*)?$'
)
_ITERATION_FILE_RE = re.compile(
    r'^(?:(?:v|r)\d+-)?\d{4}-\d{2}-\d{2}(?:-[a-z0-9]+(?:-[a-z0-9]+)*)?\.[a-z0-9]+$'
)
_OUTPUTS_ROOT_ALLOWLIST = {'_archive', '_index.md', 'README.md'}


def parse_schema_required(text: str) -> dict:
    """Return {field_name: enum_values_or_None} for the required: block."""
    out = {}
    section = None
    for line in text.splitlines():
        if line.lstrip().startswith('#'):
            continue
        if line.startswith('required:'):
            section = 'required'
            continue
        if re.match(r'^\S', line):
            section = None
            continue
        if section == 'required':
            m = re.match(r'^\s+(\w+):\s*(.*?)$', line)
            if m:
                fname, rest = m.group(1), m.group(2).strip()
                rest = re.sub(r'#.*$', '', rest).strip()
                enum_match = re.match(r'enum\s*\[([^\]]+)\]', rest)
                if enum_match:
                    vals = [v.strip() for v in enum_match.group(1).split(',')]
                    out[fname] = vals
                else:
                    out[fname] = None
    return out


def parse_schema_meta(text: str):
    """Return (allowed_top_level_keys, schema_version_or_None, directory_or_None).

    Allowed keys = field names under required: plus those under optional:.
    Other top-level blocks describe nested structure, not top-level record
    keys, so they are not collected. An optional top-level directory: key
    names the records/ subdirectory this type must live in.
    """
    allowed = set()
    schema_version = None
    directory = None
    section = None
    for line in text.splitlines():
        if line.lstrip().startswith('#'):
            continue
        sv = re.match(r'^schema_version:\s*(\S+)', line)
        if sv:
            schema_version = sv.group(1)
            continue
        dv = re.match(r'^directory:\s*(\S+)', line)
        if dv:
            directory = dv.group(1).strip('"').strip("'")
            continue
        if line.startswith('required:'):
            section = 'required'
            continue
        if line.startswith('optional:'):
            section = 'optional'
            continue
        if re.match(r'^\S', line) and line.rstrip().endswith(':'):
            section = None
            continue
        if section in ('required', 'optional'):
            m = re.match(r'^\s+(\w+):', line)
            if m:
                allowed.add(m.group(1))
    return allowed, schema_version, directory


def parse_fm(text: str):
    m = re.match(r'---\n(.*?)\n---', text, re.DOTALL)
    if not m:
        return None
    try:
        return yaml.safe_load(m.group(1))
    except yaml.YAMLError:
        return {}


def audit_outputs_directory(root: Path, flag):
    """Stream-folder naming plus shipped-frozen immutability for outputs/.

    Naming: immediate children of outputs/ are kebab-case stream folders or
    the allowlisted set. Inside a stream, children are iteration files or
    iteration folders matching [v|r]N-YYYY-MM-DD[-note] or YYYY-MM-DD[-note].

    Immutability: every .md inside a stream folder with status:
    shipped-frozen has mtime <= shipped_date + 1 day (clock-skew and
    file-sync grace).
    """
    outputs_dir = root / 'outputs'
    if not outputs_dir.exists():
        return

    for child in outputs_dir.iterdir():
        if child.name in _OUTPUTS_ROOT_ALLOWLIST or child.name.startswith('.'):
            continue
        rel = child.relative_to(root)
        if not child.is_dir():
            flag('rule5_outputs_naming',
                 f"{rel}: file at outputs/ root; must live inside a stream folder")
            continue
        if not _STREAM_SLUG_RE.match(child.name):
            flag('rule5_outputs_naming',
                 f"{rel}: not a valid kebab-case stream slug")
            continue
        for iter_child in child.iterdir():
            if iter_child.name.startswith('.'):
                continue
            iter_rel = iter_child.relative_to(root)
            if iter_child.is_dir():
                if not _ITERATION_DIR_RE.match(iter_child.name):
                    flag('rule5_outputs_naming',
                         f"{iter_rel}: invalid iteration folder name "
                         f"(expected [v|r]N-YYYY-MM-DD[-note] or YYYY-MM-DD[-note])")
            else:
                if not _ITERATION_FILE_RE.match(iter_child.name):
                    flag('rule5_outputs_naming',
                         f"{iter_rel}: invalid iteration filename "
                         f"(expected [v|r]N-YYYY-MM-DD[-note].ext or YYYY-MM-DD[-note].ext)")

    for md in outputs_dir.rglob('*.md'):
        rel = md.relative_to(root)
        if '_archive' in rel.parts:
            continue
        if md.name == '_index.md':
            continue
        fm = parse_fm(md.read_text(errors='ignore'))
        if not fm or not isinstance(fm, dict):
            continue
        if fm.get('status') != 'shipped-frozen':
            continue
        sd = fm.get('shipped_date')
        if not sd:
            continue
        try:
            sd_date = sd if isinstance(sd, Date) else Date.fromisoformat(str(sd))
        except (ValueError, TypeError):
            continue
        mtime = datetime.date.fromtimestamp(md.stat().st_mtime)
        grace = sd_date + datetime.timedelta(days=1)
        if mtime > grace:
            flag('rule9_immutability',
                 f"{rel}: mtime {mtime} > shipped_date+1d {grace} "
                 f"(shipped-frozen modified post-ship)")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--root', default='.',
                    help='Wiki workspace root (default: current directory).')
    ap.add_argument('--schemas', default=None,
                    help='Schema directory override '
                         '(default: <root>/.claude/skills/_schemas).')
    ap.add_argument('--terse', action='store_true',
                    help='One-line summary only.')
    ap.add_argument('--min-year', type=int, default=1990,
                    help='Earliest plausible record year (default: 1990).')
    ap.add_argument('--max-year', type=int, default=Date.today().year + 5,
                    help='Latest plausible record year (default: current year + 5).')
    ap.add_argument('--closed-world', choices=['off', 'warn', 'fail'],
                    default='fail',
                    help='Enforcement for undeclared frontmatter keys on '
                         'governed types (default: fail).')
    args = ap.parse_args()

    root = Path(args.root).expanduser().resolve()
    records_dir = root / 'records'
    if not records_dir.exists():
        print(f"ERROR: {records_dir} does not exist; is --root a wiki workspace?",
              file=sys.stderr)
        return 2

    schemas_dir = (Path(args.schemas).expanduser().resolve()
                   if args.schemas else root / '.claude' / 'skills' / '_schemas')

    required_by_type = {}
    schema_meta = {}
    if schemas_dir.exists():
        for sf in sorted(schemas_dir.glob('*.yaml')):
            text = sf.read_text(errors='ignore')
            required_by_type[sf.stem] = parse_schema_required(text)
            schema_meta[sf.stem] = parse_schema_meta(text)
    else:
        print(f"WARN: schema directory {schemas_dir} does not exist; "
              f"every record will flag unknown_type", file=sys.stderr)

    # Whitelist: known non-violations. Format is {category: [substrings]};
    # a violation whose message contains a listed substring is suppressed.
    whitelist = {}
    whitelist_file = root / '.claude' / 'whitelist.yaml'
    if whitelist_file.exists():
        try:
            whitelist = yaml.safe_load(whitelist_file.read_text()) or {}
        except yaml.YAMLError as e:
            print(f"WARN: whitelist.yaml parse error: {e}", file=sys.stderr)

    def is_whitelisted(category: str, message: str) -> bool:
        for substring in whitelist.get(category, []) or []:
            if substring in message:
                return True
        return False

    records = []
    for p in records_dir.rglob('*.md'):
        text = p.read_text(errors='ignore')
        fm = parse_fm(text)
        records.append((p, fm, text))

    violations = defaultdict(list)
    suppressed = defaultdict(list)
    warnings = defaultdict(list)

    def flag(category, message):
        if is_whitelisted(category, message):
            suppressed[category].append(message)
        else:
            violations[category].append(message)

    def warn(category, message):
        # Non-blocking: warnings never count toward the exit code.
        if not is_whitelisted(category, message):
            warnings[category].append(message)

    # --- Required fields + enums -----------------------------------------
    for p, fm, _ in records:
        if fm is None:
            flag('no_frontmatter', str(p.relative_to(root)))
            continue
        if not isinstance(fm, dict):
            flag('frontmatter_not_dict', str(p.relative_to(root)))
            continue
        t = fm.get('type', '')
        req = required_by_type.get(t)
        if not req:
            flag('unknown_type', f"{p.relative_to(root)}: type={t!r}")
            continue
        for fname, enum_vals in req.items():
            if fname not in fm:
                flag('missing_required',
                     f"{p.relative_to(root)}: missing '{fname}' (type={t})")
            elif enum_vals:
                v = fm[fname]
                if isinstance(v, str) and v not in enum_vals:
                    flag('enum_violation',
                         f"{p.relative_to(root)}: {fname}={v!r} not in "
                         f"{enum_vals} (type={t})")

    # --- Closed-world key check -------------------------------------------
    # Runs only for governed types (schema carries schema_version); this lets
    # a workspace phase the check in one type at a time.
    if args.closed_world != 'off':
        emit = flag if args.closed_world == 'fail' else warn
        for p, fm, _ in records:
            if not fm or not isinstance(fm, dict):
                continue
            t = fm.get('type', '')
            allowed, sv, _dir = schema_meta.get(t, (None, None, None))
            if not sv or not allowed:
                continue
            for key in fm.keys():
                if key not in allowed and key not in UNIVERSAL_OPTIONAL_KEYS:
                    emit('undeclared_key',
                         f"{p.relative_to(root)}: '{key}' not declared in "
                         f"{t} schema v{sv}")

    # --- id vs filename -----------------------------------------------------
    for p, fm, _ in records:
        if not fm or not isinstance(fm, dict):
            continue
        if 'id' in fm and p.name != str(fm['id']) + '.md':
            flag('id_filename_mismatch',
                 f"{p.relative_to(root)}: id={fm['id']!r} but filename={p.stem!r}")

    # --- type vs directory ---------------------------------------------------
    # A schema may pin its type to a records/ subdirectory with a top-level
    # directory: key. Types without one are checked for internal consistency:
    # all records of a type should live under a single records/ subdirectory.
    dirs_by_type = defaultdict(Counter)
    for p, fm, _ in records:
        if not fm or not isinstance(fm, dict):
            continue
        t = fm.get('type', '')
        if not t:
            continue
        dirs_by_type[t][p.parent.name] += 1
    for p, fm, _ in records:
        if not fm or not isinstance(fm, dict):
            continue
        t = fm.get('type', '')
        _allowed, _sv, expected_dir = schema_meta.get(t, (None, None, None))
        if expected_dir:
            if p.parent.name != expected_dir:
                flag('type_dir_mismatch',
                     f"{p.relative_to(root)}: type={t} but in {p.parent.name}/ "
                     f"(schema declares {expected_dir}/)")
        elif t in dirs_by_type and len(dirs_by_type[t]) > 1:
            majority_dir = dirs_by_type[t].most_common(1)[0][0]
            if p.parent.name != majority_dir:
                flag('type_dir_mismatch',
                     f"{p.relative_to(root)}: type={t} but in {p.parent.name}/ "
                     f"(most {t} records live in {majority_dir}/)")

    # --- source_files paths + sidecars -----------------------------------
    for p, fm, _ in records:
        if not fm or not isinstance(fm, dict):
            continue
        sf = fm.get('source_files') or []
        if not isinstance(sf, list):
            flag('source_files_not_list', str(p.relative_to(root)))
            continue
        if not sf:
            flag('empty_source_files', str(p.relative_to(root)))
            continue
        for entry in sf:
            if not isinstance(entry, dict):
                flag('source_files_entry_malformed',
                     f"{p.relative_to(root)}: {entry!r}")
                continue
            path = entry.get('path')
            if path and not (root / path).exists():
                flag('source_path_missing', f"{p.relative_to(root)}: {path}")
            sidecar = entry.get('sidecar')
            if sidecar and not (root / sidecar).exists():
                flag('sidecar_missing', f"{p.relative_to(root)}: {sidecar}")

    # --- Date sanity ---------------------------------------------------------
    today = Date.today()
    for p, fm, _ in records:
        if not fm or not isinstance(fm, dict):
            continue
        d = fm.get('date')
        if isinstance(d, Date):
            dd = d
        elif isinstance(d, str):
            try:
                dd = Date.fromisoformat(d)
            except (ValueError, TypeError):
                flag('date_unparseable', f"{p.relative_to(root)}: date={d!r}")
                continue
        else:
            flag('date_missing_or_bad', f"{p.relative_to(root)}: date={d!r}")
            continue
        if dd > today:
            flag('future_date', f"{p.relative_to(root)}: date={dd} (today={today})")
        if dd.year < args.min_year or dd.year > args.max_year:
            flag('date_out_of_range', f"{p.relative_to(root)}: date={dd}")

    # --- Index integrity ------------------------------------------------------
    index_path = root / 'index.md'
    if index_path.exists():
        index_text = index_path.read_text(errors='ignore')
        indexed = set()
        for m in re.finditer(r'\[([^\]]+)\]\((records/[^)]+\.md)\)', index_text):
            indexed.add(m.group(2))
        all_record_paths = set(str(p.relative_to(root)) for p, _, _ in records)
        for r in sorted(all_record_paths - indexed):
            flag('record_not_indexed', r)
        for r in sorted(indexed - all_record_paths):
            flag('index_stale_entry', r)
    else:
        flag('index_missing', 'index.md does not exist (run rebuild_index.py)')

    # --- Stray / empty files ---------------------------------------------------
    for p in records_dir.rglob('.DS_Store'):
        flag('ds_store_in_records', str(p.relative_to(root)))
    for p in records_dir.rglob('*.md'):
        if p.stat().st_size == 0:
            flag('empty_record_file', str(p.relative_to(root)))

    # --- Duplicate top-level YAML keys --------------------------------------
    # yaml.safe_load silently keeps the last value, so the parsed state hides
    # the bug; the raw text must be scanned.
    dup_key_re = re.compile(r'^([A-Za-z_][A-Za-z0-9_]*):', re.MULTILINE)
    for p, _, text in records:
        m = re.match(r'---\n(.*?)\n---', text, re.DOTALL)
        if not m:
            continue
        seen = set()
        dups = set()
        for km in dup_key_re.finditer(m.group(1)):
            k = km.group(1)
            if k in seen:
                dups.add(k)
            seen.add(k)
        for k in sorted(dups):
            flag('duplicate_frontmatter_key',
                 f"{p.relative_to(root)}: '{k}' appears multiple times")

    # --- YAML '#' truncation --------------------------------------------------
    # An unquoted top-level string whose parsed value is shorter than its raw
    # line content is being silently chopped at YAML's comment marker.
    title_line = re.compile(r'^([A-Za-z_][A-Za-z0-9_]*):\s+(.+?)\s*$', re.MULTILINE)
    for p, fm, text in records:
        m = re.match(r'---\n(.*?)\n---', text, re.DOTALL)
        if not m or not isinstance(fm, dict):
            continue
        for km in title_line.finditer(m.group(1)):
            key, raw_value = km.group(1), km.group(2)
            if raw_value.startswith(('"', "'")) and raw_value.endswith(('"', "'")):
                continue
            if ' #' not in raw_value:
                continue
            parsed = fm.get(key)
            if isinstance(parsed, str) and len(parsed.strip()) < len(raw_value.strip()):
                flag('yaml_hash_truncation',
                     f"{p.relative_to(root)}: {key!r} truncated from "
                     f"{len(raw_value.strip())} chars to {len(parsed.strip())} "
                     f"by unquoted '#' (quote the value)")

    # NOTE: the reference system also ran a project-specific heuristic that
    # flagged suspiciously round extracted dollar values. That check encoded
    # domain knowledge about one project's contract sums and was removed
    # rather than genericized. A semantic audit is the right home for value
    # plausibility checks.

    # --- Source cited by multiple records (informational) ----------------------
    # Snapshot and structured tabular sources are legitimately cited by many
    # records (each row is its own entity), so those source types are skipped.
    # Non-blocking: cross-citation can be intentional; whitelist or review.
    src_to_records = defaultdict(list)
    src_types = defaultdict(set)
    for p, fm, _ in records:
        if not fm or not isinstance(fm, dict):
            continue
        for entry in (fm.get('source_files') or []):
            if isinstance(entry, dict) and entry.get('path'):
                src_to_records[entry['path']].append(str(p.relative_to(root)))
                if entry.get('type'):
                    src_types[entry['path']].add(entry['type'])
    for src, recs in src_to_records.items():
        types = src_types.get(src, set())
        if 'prose-snapshot' in types or 'structured-canonical' in types:
            continue
        if len(set(recs)) > 1:
            classes = set(r.split('/')[1] for r in recs if r.count('/') >= 2)
            if len(classes) > 1 or len(set(recs)) > 2:
                warn('source_cited_by_multiple_records',
                     f"{src} -> {sorted(set(recs))}")

    # --- Body link resolution ------------------------------------------------
    link_re = re.compile(r'\[[^\]]+\]\((?!https?:|#)([^)]+)\)')
    for p, fm, text in records:
        if text.startswith('---'):
            fm_end = text.find('---', 3) + 3
            body = text[fm_end:]
        else:
            body = text
        for m in link_re.finditer(body):
            link = m.group(1).strip().split('#')[0]
            if not link:
                continue
            # Percent-encoded links (%20 spaces, %23 for '#' in filenames)
            link = urllib.parse.unquote(link)
            target = (p.parent / link).resolve()
            try:
                target.relative_to(root)
            except ValueError:
                continue
            if not target.exists():
                flag('broken_body_link', f"{p.relative_to(root)}: -> {link}")

    # --- Topic-page freshness ---------------------------------------------------
    # last_synthesized must be at or after the most recent change date among
    # declared source_records[]. The change date is the later of ingested_at
    # and updated_at, so an enrichment that refreshed a record without
    # bumping ingested_at still marks dependent topics stale.
    record_ingest_dates = {}
    for p, fm, _ in records:
        if not fm or not isinstance(fm, dict):
            continue
        cand = []
        for _k in ('ingested_at', 'updated_at'):
            d = fm.get(_k)
            if isinstance(d, Date):
                cand.append(d)
            elif isinstance(d, str):
                try:
                    cand.append(Date.fromisoformat(d))
                except ValueError:
                    pass
        if cand:
            record_ingest_dates[str(p.relative_to(root))] = max(cand)
    topics_dir = root / 'topics'
    if topics_dir.exists():
        for tp in topics_dir.glob('*.md'):
            if tp.name.lower().startswith('readme'):
                continue
            tfm = parse_fm(tp.read_text(errors='ignore'))
            if not tfm or not isinstance(tfm, dict):
                continue
            srs = tfm.get('source_records') or []
            ls = tfm.get('last_synthesized')
            if isinstance(ls, str):
                try:
                    ls = Date.fromisoformat(ls)
                except ValueError:
                    flag('topic_unparseable_last_synthesized',
                         f"{tp.relative_to(root)}: last_synthesized="
                         f"{tfm.get('last_synthesized')!r}")
                    continue
            if not isinstance(ls, Date):
                flag('topic_missing_last_synthesized', str(tp.relative_to(root)))
                continue
            for sr in srs:
                ri = record_ingest_dates.get(sr)
                if ri and ri > ls:
                    flag('topic_stale',
                         f"{tp.relative_to(root)}: source {sr} ingested {ri} "
                         f"> last_synthesized {ls}")

    # --- No numbers in navigation surfaces -----------------------------------
    # index.md headers and topic section headers must not carry dollar
    # figures, large counts, or percentages; numbers drift and belong in
    # cited records.
    number_in_prose = re.compile(
        r'(\$[\d,.]+(?:M|K|B)?|\b\d{1,3}(?:,\d{3}){2,}\b|\b\d+\s*%)')
    if index_path.exists():
        idx_text = index_path.read_text(errors='ignore')
        for line in idx_text.splitlines():
            stripped = line.strip()
            if stripped.startswith('#') and number_in_prose.search(stripped):
                flag('index_numbers_in_header', f"index.md: {stripped[:80]}")
    if topics_dir.exists():
        for tp in topics_dir.glob('*.md'):
            ttext = tp.read_text(errors='ignore')
            for line in ttext.splitlines():
                if line.startswith('##') and number_in_prose.search(line):
                    flag('topic_numbers_in_section_header',
                         f"{tp.relative_to(root)}: {line.strip()[:80]}")

    # --- outputs/ naming + immutability -----------------------------------
    audit_outputs_directory(root, flag)

    # --- Report ------------------------------------------------------------------
    total = sum(len(v) for v in violations.values())
    total_supp = sum(len(v) for v in suppressed.values())
    total_warn = sum(len(v) for v in warnings.values())

    if args.terse:
        if total == 0:
            print(f"AUDIT: clean ({len(records)} records, {total_supp} "
                  f"whitelisted, {total_warn} warnings)")
        else:
            print(f"AUDIT: {total} violations across {len(violations)} "
                  f"categories ({total_supp} whitelisted, {total_warn} warnings)")
            for cat, vs in sorted(violations.items(), key=lambda x: -len(x[1])):
                print(f"  [{cat}] {len(vs)}")
        return 0 if total == 0 else 1

    print(f"Walked {len(records)} records")
    print(f"Schemas loaded: {len(required_by_type)} (from {schemas_dir})")
    print(f"Whitelist categories: {len(whitelist)}")
    print()
    print(f"Total violations (excluding whitelisted): {total}")
    print(f"Suppressed by whitelist: {total_supp}")
    print(f"Warnings (non-blocking): {total_warn}")
    print()

    if violations:
        print("=" * 60)
        print("VIOLATIONS")
        print("=" * 60)
        for cat, vs in sorted(violations.items(), key=lambda x: -len(x[1])):
            print(f"\n[{cat}] {len(vs)}")
            for v in vs[:8]:
                print(f"  {v}")
            if len(vs) > 8:
                print(f"  ... ({len(vs)-8} more)")

    if warnings:
        print("\n" + "=" * 60)
        print("WARNINGS (non-blocking)")
        print("=" * 60)
        for cat, vs in sorted(warnings.items(), key=lambda x: -len(x[1])):
            print(f"\n[{cat}] {len(vs)}")
            for v in vs[:8]:
                print(f"  {v}")
            if len(vs) > 8:
                print(f"  ... ({len(vs)-8} more)")

    if suppressed:
        print("\n" + "=" * 60)
        print("SUPPRESSED (whitelisted)")
        print("=" * 60)
        for cat, vs in sorted(suppressed.items(), key=lambda x: -len(x[1])):
            print(f"  [{cat}] {len(vs)}")

    print("\n" + "=" * 60)
    print("RECORD TYPE COUNTS")
    print("=" * 60)
    type_counts = Counter(fm.get('type', 'Unknown')
                          for _, fm, _ in records
                          if fm and isinstance(fm, dict))
    for t, c in sorted(type_counts.items(), key=lambda x: -x[1]):
        print(f"  {c:5d} {t}")
    print(f"  {'-':>5} TOTAL: {sum(type_counts.values())}")

    return 0 if total == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
