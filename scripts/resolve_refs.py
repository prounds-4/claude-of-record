#!/usr/bin/env python3
"""Resolve outbound cross-references into inbound referenced_by[] blocks.

What this script checks and does:
  - Walks every .md under <root>/records/ and <root>/topics/ (topics
    README.md excluded).
  - Collects outbound edges from two places: markdown body links to other
    records/topics, and the frontmatter references[] block.
  - Rewrites the referenced_by[] frontmatter block on every target so the
    inbound side of the graph matches the outbound side.
  - Writes two reports to <root>/.claude/health/:
      broken-refs.md   links whose target does not exist and is not marked
                       pending-target
      pending-refs.md  frontmatter refs marked status: pending-target whose
                       target has not been ingested yet
  - Links into outputs/ are existence-checked and reported when broken, but
    frozen deliverables never receive an inbound referenced_by[] edge.
  - Links into Originals/ are treated as source citations, not cross-refs,
    and are skipped entirely.

What this script does NOT check:
  - It does not validate frontmatter against schemas (that is audit.py).
  - It does not verify that a link's anchor text matches its target.
  - It does not verify source citations into Originals/ resolve on disk
    (audit.py checks declared source_files paths).

Dependencies: python3 stdlib only.

Usage:
  python3 resolve_refs.py [--root PATH]

--root defaults to the current working directory.
"""
import argparse
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

LINK_RE = re.compile(r'\[[^\]]+\]\(([^)]+\.md)\)')


def split_frontmatter(text: str):
    if not text.startswith('---'):
        return '', text
    m = re.match(r'---\n(.*?)\n---\n?', text, re.DOTALL)
    if not m:
        return '', text
    return m.group(1), text[m.end():]


def parse_references_block(fm_text: str):
    """Parse the frontmatter references: list.
    Returns [(target, relationship, status_or_empty)]."""
    out = []
    in_block = False
    cur_target = None
    cur_rel = None
    cur_status = ''
    for raw_line in fm_text.splitlines():
        if raw_line.startswith('references:'):
            in_block = True
            continue
        if in_block:
            # End of block: a non-indented key
            if (raw_line and not raw_line.startswith(' ')
                    and not raw_line.startswith('\t')
                    and not raw_line.startswith('-')):
                if cur_target:
                    out.append((cur_target, cur_rel or 'references', cur_status))
                    cur_target, cur_rel, cur_status = None, None, ''
                in_block = False
                continue
            stripped = raw_line.strip()
            if stripped.startswith('- '):
                # New list item; flush the previous one
                if cur_target:
                    out.append((cur_target, cur_rel or 'references', cur_status))
                    cur_target, cur_rel, cur_status = None, None, ''
                stripped = stripped[2:].strip()
                m = re.match(r'target:\s*(.*)$', stripped)
                if m:
                    cur_target = m.group(1).strip().strip('"').strip("'")
                    continue
            m = re.match(r'^\s*target:\s*(.*)$', raw_line)
            if m:
                cur_target = m.group(1).strip().strip('"').strip("'")
                continue
            m = re.match(r'^\s*relationship:\s*(.*)$', raw_line)
            if m:
                cur_rel = m.group(1).strip().strip('"').strip("'")
                continue
            m = re.match(r'^\s*status:\s*(.*)$', raw_line)
            if m:
                cur_status = m.group(1).strip().strip('"').strip("'")
                continue
    if cur_target:
        out.append((cur_target, cur_rel or 'references', cur_status))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--root', default='.',
                    help='Wiki workspace root (default: current directory).')
    args = ap.parse_args()
    root = Path(args.root).expanduser().resolve()

    records_dir = root / 'records'
    topics_dir = root / 'topics'
    if not records_dir.exists():
        print(f"ERROR: {records_dir} does not exist; is --root a wiki workspace?",
              file=sys.stderr)
        return 2

    health = root / '.claude' / 'health'
    health.mkdir(parents=True, exist_ok=True)

    all_records = list(records_dir.rglob('*.md'))
    all_topics = []
    if topics_dir.exists():
        all_topics = [p for p in topics_dir.glob('*.md')
                      if p.name.lower() != 'readme.md']
    all_files = all_records + all_topics

    valid_targets = set(str(p.relative_to(root)) for p in all_files)

    edges = []                       # (source_rel, target_rel, relationship)
    broken = defaultdict(list)       # source_rel -> [(target, reason)]
    pending = defaultdict(list)      # source_rel -> [(target, relationship)]

    # Pass 1: collect outbound edges
    for src_path in all_files:
        src_rel = str(src_path.relative_to(root))
        text = src_path.read_text(errors='ignore')
        fm_text, body = split_frontmatter(text)

        # Body markdown links
        for m in LINK_RE.finditer(body):
            link = m.group(1).strip().split('#')[0]
            # Skip URLs, anchor-only links, and links into Originals/
            # (those are source citations, not cross-refs)
            if not link or link.startswith('http') or 'Originals/' in link:
                continue
            # Normalize relative paths against the source file's directory
            if link.startswith('../') or not link.startswith(('records/', 'topics/')):
                target_path = (src_path.parent / link).resolve()
                try:
                    target_rel = str(target_path.relative_to(root))
                except ValueError:
                    continue
            else:
                target_rel = link
            # Links into outputs/: existence-check only. Frozen deliverables
            # receive no inbound edge, but a broken link into outputs/ must
            # still be reported.
            if target_rel.startswith('outputs/'):
                if not (root / target_rel).exists():
                    broken[src_rel].append((target_rel, 'outputs link does not exist'))
                continue
            if not (target_rel.startswith('records/') or target_rel.startswith('topics/')):
                continue
            if target_rel == src_rel:
                continue
            if target_rel in valid_targets:
                edges.append((src_rel, target_rel, 'mentions'))
            else:
                broken[src_rel].append((target_rel, 'does not exist'))

        # Frontmatter references[]
        for target, rel, status in parse_references_block(fm_text):
            target_rel = target
            if target_rel.startswith('../'):
                target_path = (src_path.parent / target_rel).resolve()
                try:
                    target_rel = str(target_path.relative_to(root))
                except ValueError:
                    pass
            if target_rel == src_rel:
                continue
            if target_rel in valid_targets:
                edges.append((src_rel, target_rel, rel))
            else:
                if status == 'pending-target':
                    pending[src_rel].append((target_rel, rel))
                else:
                    broken[src_rel].append(
                        (target_rel, f'frontmatter ref (rel={rel}) does not exist'))

    edges = list(set(edges))

    # Pass 2: build the inbound map
    inbound = defaultdict(list)
    for src, tgt, rel in edges:
        inbound[tgt].append((src, rel))

    for tgt in inbound:
        seen = set()
        out = []
        for src, rel in sorted(inbound[tgt]):
            key = (src, rel)
            if key in seen:
                continue
            seen.add(key)
            out.append((src, rel))
        inbound[tgt] = out

    # Pass 2b: write referenced_by[] back to each target
    written = 0
    for tgt_rel, refs in inbound.items():
        tgt_path = root / tgt_rel
        text = tgt_path.read_text(errors='ignore')
        fm_text, body = split_frontmatter(text)
        if not fm_text:
            continue
        new_block_lines = ['referenced_by:']
        for src, rel in refs:
            new_block_lines.append(f'  - source: {src}')
            new_block_lines.append(f'    relationship: {rel}')
        new_block = '\n'.join(new_block_lines)

        # Match either single-line "referenced_by: []" or a multi-line block
        pattern = re.compile(r'^referenced_by:.*?(?=^\w|\Z)', re.MULTILINE | re.DOTALL)
        if pattern.search(fm_text):
            new_fm = pattern.sub(new_block + '\n', fm_text)
        else:
            new_fm = fm_text.rstrip() + '\n' + new_block + '\n'

        if new_fm != fm_text:
            new_text = '---\n' + new_fm.rstrip('\n') + '\n---\n' + body
            tgt_path.write_text(new_text)
            written += 1

    # Pass 3: write reports
    now = datetime.now().strftime('%Y-%m-%d %H:%M')

    broken_lines = ['# Broken outbound references', '',
                    f'_Regenerated {now} by resolve_refs.py._', '']
    for src in sorted(broken):
        broken_lines.append(f'## {src}')
        for tgt, reason in broken[src]:
            broken_lines.append(f'- `{tgt}` ({reason})')
        broken_lines.append('')
    total_broken = sum(len(v) for v in broken.values())
    broken_lines.insert(4, f'**Total: {total_broken} broken refs across '
                           f'{len(broken)} sources.**')
    broken_lines.insert(5, '')
    (health / 'broken-refs.md').write_text('\n'.join(broken_lines))

    pending_lines = ['# Pending-target references', '',
                     f'_Regenerated {now} by resolve_refs.py._', '']
    for src in sorted(pending):
        pending_lines.append(f'## {src}')
        for tgt, rel in pending[src]:
            pending_lines.append(f'- `{tgt}` (relationship: {rel})')
        pending_lines.append('')
    total_pending = sum(len(v) for v in pending.values())
    pending_lines.insert(4, f'**Total: {total_pending} pending-target refs across '
                            f'{len(pending)} sources.**')
    pending_lines.insert(5, '')
    (health / 'pending-refs.md').write_text('\n'.join(pending_lines))

    print(f'Walked {len(all_files)} files (records {len(all_records)} '
          f'+ topics {len(all_topics)})')
    print(f'Edges (deduped): {len(edges)}')
    print(f'Targets with inbound refs: {len(inbound)}')
    print(f'Files updated with referenced_by: {written}')
    print(f'Broken refs: {total_broken} across {len(broken)} sources')
    print(f'Pending-target refs: {total_pending} across {len(pending)} sources')
    return 0


if __name__ == '__main__':
    sys.exit(main())
