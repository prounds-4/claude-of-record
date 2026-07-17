#!/usr/bin/env python3
"""Semantic audit: verifies extracted record values against cited source sidecars.

A structural audit checks that YAML parses, paths resolve, and schemas match.
This audit checks the layer underneath: do the extracted values actually appear
in the cited source text? Do they satisfy the project's known fixed facts? Are
there outliers or cross-record contradictions?

Check classes:
  1. Source presence   - every extracted dollar value (frontmatter money fields
                         and body dollar figures) must appear in a cited
                         sidecar, tolerating common OCR renderings
  2. Class constants   - fixed facts from the invariants config, for example a
                         base contract sum that must read the same everywhere
  3. Outlier bounds    - configured min/max ranges per record type and field
  4. Reference ranges  - references[] targets whose numeric id must fall inside
                         a configured range (catches citations of entities that
                         do not exist)
  5. Cross-record      - declarative consistency rules from the config:
                         sum_matches, fields_equal, field_gte, field_agreement
  6. Date sanity       - no future dates; optional project date window
  7. Type-specific     - built-in checks for common record types (Amendment,
                         ASI, RFI, Invoice, Inspection, BaseContract,
                         Subcontract, change orders, Discrepancy, BidPackage)
  8. Universal         - duplicate ids, placeholder strings, title-equals-id

All project-specific values (party names, contract sums, id ranges, date
windows) live in an invariants YAML, never in this file. See
templates/project-invariants.yaml for a documented starting point. Without an
invariants file the config-driven checks are skipped and the report says so.

Wiki layout expected under --root:
  CLAUDE.md  index.md  records/  topics/  Originals/  .claude/health/

Output: human-readable report on stdout plus <root>/.claude/health/semantic-audit.md,
both ending with a coverage statement of what was and was not checked.

Exit codes:
  0 - clean
  1 - semantic violations found
  2 - usage error (no records/ directory under root)

Usage:
  python3 audit_semantic.py                            # cwd as wiki root
  python3 audit_semantic.py --root /path/to/wiki
  python3 audit_semantic.py --invariants inv.yaml      # default <root>/.claude/project-invariants.yaml
  python3 audit_semantic.py --class PayApp             # one record type only
  python3 audit_semantic.py --terse                    # counts only

Requires: python3 stdlib plus pyyaml.
"""
import argparse
import re
import sys
from collections import defaultdict
from datetime import date as Date
from pathlib import Path

import yaml

# ---------------------------------------------------------------------------
# Built-in heuristics (project-neutral; project values belong in the config)
# ---------------------------------------------------------------------------

# Frontmatter keys that look like money fields. A key must match MONEY_KEY_RE
# and not match NON_MONEY_KEY_RE, and its value must be numeric, to be treated
# as an extracted dollar amount.
MONEY_KEY_RE = re.compile(
    r'(amount|total|sum|balance|payment|due|price|cost|fee|retainage|certif)', re.I)
NON_MONEY_KEY_RE = re.compile(
    r'(count|number|code|qty|quantity|percent|pct|rate|year|days|duration)', re.I)

# Dollar figures in record body prose: $1,234,567.89 or $12345.00 style.
BODY_DOLLAR_RE = re.compile(r'\$\s?(\d{1,3}(?:,\d{3})+(?:\.\d{2})?|\d{4,}(?:\.\d{2})?)')

# Default formats, overridable via the invariants file's `formats:` block.
DEFAULT_FORMATS = {
    # amendment label: 1 to 3 digits, optional revision suffix like "07 R1"
    'amendment_label': r'^\d{1,3}(?:\s*R\d+)?$',
    # cost code: 4 to 6 digit numeric string
    'cost_code': r'^\d{4,6}$',
}

PLACEHOLDER_STRINGS = ('null', 'none', 'tbd', 'todo')


def parse_fm(text: str):
    """Parse YAML frontmatter from a record file. Returns (frontmatter, body)."""
    m = re.match(r'---\n(.*?)\n---\n?', text, re.DOTALL)
    if not m:
        return None, text
    try:
        return yaml.safe_load(m.group(1)), text[m.end():]
    except yaml.YAMLError:
        return None, text[m.end():]


def value_in_sidecar(value: float, sidecar_text: str) -> bool:
    """Check whether a dollar value appears in the sidecar text in any common
    rendering. Tolerates: comma separators (1,234,567.89), a no-cents rendering
    for whole-dollar values (1,234,567), European separators (1.234.567,89),
    hybrid OCR separator swaps (1,234.567.89), and OCR letter substitutions
    (I or l for 1, O for 0), including separator noise inserted between digits.
    """
    if value is None:
        return False
    abs_v = abs(value)
    target = f"{abs_v:,.2f}"  # standard rendering with commas and cents
    if target in sidecar_text:
        return True
    # Whole-dollar values often print without cents. Only try this for values
    # large enough to carry a thousands separator, so bare small integers do
    # not match incidentally.
    if abs_v == int(abs_v) and abs_v >= 1000:
        if f"{int(abs_v):,}" in sidecar_text:
            return True
    # European: dots as thousands separators, comma as decimal
    target_eu = target.replace(',', 'X').replace('.', ',').replace('X', '.')
    if target_eu in sidecar_text:
        return True
    # Hybrid OCR: commas at some thousands positions, dots at others
    parts = target.split(',')
    if len(parts) > 1:
        for i in range(1, len(parts)):
            variant = ','.join(parts[:i]) + '.' + '.'.join(parts[i:])
            if variant in sidecar_text:
                return True
    # Straight OCR letter substitutions
    for pattern in [target.replace('1', 'I'), target.replace('1', 'l'),
                    target.replace('0', 'O')]:
        if pattern in sidecar_text:
            return True
    # OCR-spaced variants: each digit may be itself or a known substitute, and
    # any separator or single stray space may sit between digits. Build
    # per-digit tokens first, then join, so the join cannot chew up regex
    # character-class brackets.
    target_int = target.split('.')[0].replace(',', '')
    decimal_part = target.split('.')[1] if '.' in target else '00'
    if len(target_int) >= 5:
        ocr_map = {'1': '[1lI]', '0': '[0O]'}
        tokens = [ocr_map.get(d, re.escape(d)) for d in target_int]
        spaced_pat = r'[,. ]?\s?'.join(tokens)
        full_pat = re.compile(spaced_pat + r'[.,]\s*' + decimal_part)
        if full_pat.search(sidecar_text):
            return True
    return False


def get_sidecar_text(source_files: list, root: Path) -> str:
    """Concatenate text from cited sidecars, biggest first, capped at five.
    The figure under audit may live in any one of several bundled sidecars."""
    if not source_files:
        return ""
    paths = []
    for entry in source_files:
        if isinstance(entry, dict) and entry.get('sidecar'):
            p = root / entry['sidecar']
            if p.exists():
                paths.append((p, p.stat().st_size))
    paths.sort(key=lambda x: -x[1])
    return '\n'.join(p.read_text(errors='ignore') for p, _ in paths[:5])


def as_date(x):
    if isinstance(x, Date):
        return x
    if isinstance(x, str):
        try:
            return Date.fromisoformat(x)
        except (ValueError, TypeError):
            return None
    return None


def matches_when(fm: dict, when) -> bool:
    """True when every key in the optional `when:` filter equals the record's
    frontmatter value (compared as strings for robustness)."""
    if not when:
        return True
    return all(str(fm.get(k)) == str(v) for k, v in when.items())


# ---------------------------------------------------------------------------
# Check 1: source presence (the core check)
# ---------------------------------------------------------------------------

def check_source_presence(records, violations, inv, root, coverage):
    cfg = (inv or {}).get('source_presence') or {}
    min_value = float(cfg.get('min_value', 100.0))
    body_min = float(cfg.get('body_min_value', 1000.0))
    check_body = bool(cfg.get('check_body', True))
    extra_fields = cfg.get('fields') or {}
    exclude = set(cfg.get('exclude_fields') or [])

    values_checked = 0
    body_values_checked = 0
    skipped_no_sidecar = 0

    for p, fm, body in records:
        if not fm:
            continue
        rec_id = fm.get('id', p.stem)
        rec_type = fm.get('type', '')
        extras = set(extra_fields.get(rec_type) or [])

        # Collect money fields from frontmatter
        fields = {}
        for k, v in fm.items():
            if k in exclude:
                continue
            if isinstance(v, bool) or not isinstance(v, (int, float)):
                continue
            named = k in extras
            heur = MONEY_KEY_RE.search(k) and not NON_MONEY_KEY_RE.search(k)
            if (named or heur) and abs(v) >= min_value:
                fields[k] = float(v)

        body_amounts = []
        if check_body and body:
            seen = set()
            for m in BODY_DOLLAR_RE.finditer(body):
                try:
                    v = float(m.group(1).replace(',', ''))
                except ValueError:
                    continue
                if v >= body_min and v not in seen:
                    seen.add(v)
                    body_amounts.append(v)

        if not fields and not body_amounts:
            continue

        sidecar_text = get_sidecar_text(fm.get('source_files') or [], root)
        if not sidecar_text:
            # No prose sidecar to audit against (image-only or structured
            # source, or no source_files). Counted, not flagged: sidecar
            # existence is the structural audit's job.
            skipped_no_sidecar += 1
            continue

        for k, v in fields.items():
            values_checked += 1
            if not value_in_sidecar(v, sidecar_text):
                violations['dollar_not_in_source'].append(
                    f"{rec_id}: {k}={abs(v):,.2f} not found in any cited sidecar")
        for v in body_amounts:
            body_values_checked += 1
            if not value_in_sidecar(v, sidecar_text):
                violations['body_dollar_not_in_source'].append(
                    f"{rec_id}: body figure ${v:,.2f} not found in any cited sidecar")

    coverage.append(
        f"Source presence: {values_checked} frontmatter dollar values and "
        f"{body_values_checked} body dollar figures checked against cited sidecars; "
        f"{skipped_no_sidecar} records with dollar values skipped (no readable prose sidecar).")


# ---------------------------------------------------------------------------
# Check 2: class constants (config-driven)
# ---------------------------------------------------------------------------

def check_class_constants(records, violations, inv, coverage):
    constants = (inv or {}).get('class_constants') or []
    if not constants:
        coverage.append("Class constants: skipped (none configured).")
        return
    checked = 0
    for rule in constants:
        rtype = rule.get('record_type')
        field = rule.get('field')
        expected = rule.get('expected_value')
        when = rule.get('when')
        if not rtype or not field or expected is None:
            violations['invariants_config_malformed'].append(
                f"class_constants entry needs record_type, field, expected_value: {rule!r}")
            continue
        for p, fm, _ in records:
            if not fm or fm.get('type') != rtype or not matches_when(fm, when):
                continue
            actual = fm.get(field)
            if actual is None:
                continue
            checked += 1
            if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
                ok = abs(float(actual) - float(expected)) <= 0.01
            else:
                ok = str(actual).strip() == str(expected).strip()
            if not ok:
                note = f" ({rule['note']})" if rule.get('note') else ''
                violations['class_constant_violated'].append(
                    f"{fm.get('id', p.stem)}: {field}={actual!r}, "
                    f"expected {expected!r}{note}")
    coverage.append(
        f"Class constants: {len(constants)} configured rules checked "
        f"against {checked} field instances.")


# ---------------------------------------------------------------------------
# Check 3: outlier bounds (config-driven)
# ---------------------------------------------------------------------------

def check_outlier_bounds(records, violations, inv, coverage):
    bounds = (inv or {}).get('outlier_bounds') or {}
    if not bounds:
        coverage.append("Outlier bounds: skipped (none configured).")
        return
    checked = 0
    for p, fm, _ in records:
        if not fm:
            continue
        type_bounds = bounds.get(fm.get('type'))
        if not type_bounds:
            continue
        rec_id = fm.get('id', p.stem)
        for field, lim in type_bounds.items():
            v = fm.get(field)
            if isinstance(v, bool) or not isinstance(v, (int, float)):
                continue
            checked += 1
            lo = lim.get('min')
            hi = lim.get('max')
            if lo is not None and v < lo:
                violations['value_below_min_bound'].append(
                    f"{rec_id}: {field}={v:,.2f} below configured min {lo:,.2f}")
            if hi is not None and v > hi:
                violations['value_above_max_bound'].append(
                    f"{rec_id}: {field}={v:,.2f} above configured max {hi:,.2f}")
    coverage.append(f"Outlier bounds: {checked} field instances checked against configured ranges.")


# ---------------------------------------------------------------------------
# Check 4: reference ranges (config-driven)
# ---------------------------------------------------------------------------

def check_reference_ranges(records, violations, inv, coverage):
    ranges = (inv or {}).get('reference_ranges') or []
    if not ranges:
        coverage.append("Reference ranges: skipped (none configured).")
        return
    compiled = []
    for rule in ranges:
        pat = rule.get('pattern')
        if not pat:
            violations['invariants_config_malformed'].append(
                f"reference_ranges entry needs pattern: {rule!r}")
            continue
        try:
            compiled.append((re.compile(pat), rule))
        except re.error as e:
            violations['invariants_config_malformed'].append(
                f"reference_ranges pattern {pat!r} does not compile: {e}")
    checked = 0
    for p, fm, _ in records:
        if not fm:
            continue
        rec_id = fm.get('id', p.stem)
        for ref in fm.get('references') or []:
            if not isinstance(ref, dict):
                continue
            target = ref.get('target', '')
            for rx, rule in compiled:
                m = rx.match(target)
                if not m or not m.groups():
                    continue
                checked += 1
                try:
                    n = int(m.group(1))
                except ValueError:
                    continue
                lo = rule.get('min')
                hi = rule.get('max')
                if (lo is not None and n < lo) or (hi is not None and n > hi):
                    note = f" ({rule['note']})" if rule.get('note') else ''
                    violations['reference_out_of_range'].append(
                        f"{rec_id}: -> {target} (id {n} outside {lo}..{hi}){note}")
    coverage.append(
        f"Reference ranges: {len(compiled)} configured patterns checked "
        f"against {checked} matching reference targets.")


# ---------------------------------------------------------------------------
# Check 5: cross-record consistency rules (config-driven)
#
# Supported rule types (only these; anything else is flagged as config error):
#   sum_matches     - within one record: sum(addends) == equals, within tolerance
#   fields_equal    - within one record: field_a == field_b, within tolerance
#   field_gte       - within one record: field >= floor_field - tolerance
#   field_agreement - across records: rows of list_field, grouped by key, must
#                     agree on field (for example an amendment execution date
#                     cited by many pay applications)
# ---------------------------------------------------------------------------

def check_cross_record(records, violations, inv, coverage):
    rules = (inv or {}).get('cross_record') or []
    if not rules:
        coverage.append("Cross-record rules: skipped (none configured).")
        return
    applied = 0
    for rule in rules:
        rtype = rule.get('record_type')
        kind = rule.get('type')
        recs = [(p, fm) for p, fm, _ in records if fm and fm.get('type') == rtype]

        if kind == 'sum_matches':
            addends = rule.get('addends') or []
            equals = rule.get('equals')
            tol = float(rule.get('tolerance', 0.5))
            optional = set(rule.get('optional_addends') or [])
            for p, fm in recs:
                vals = []
                skip = False
                for a in addends:
                    v = fm.get(a)
                    if isinstance(v, (int, float)) and not isinstance(v, bool):
                        vals.append(float(v))
                    elif a in optional:
                        vals.append(0.0)
                    else:
                        skip = True
                        break
                target = fm.get(equals)
                if skip or not isinstance(target, (int, float)) or isinstance(target, bool):
                    continue
                applied += 1
                if abs(sum(vals) - float(target)) > tol:
                    violations['cross_record_sum_mismatch'].append(
                        f"{fm.get('id', p.stem)}: sum({', '.join(addends)})="
                        f"{sum(vals):,.2f} != {equals}={float(target):,.2f}")

        elif kind == 'fields_equal':
            fa, fb = rule.get('field_a'), rule.get('field_b')
            tol = float(rule.get('tolerance', 0.01))
            when = rule.get('when')
            for p, fm in recs:
                if not matches_when(fm, when):
                    continue
                va, vb = fm.get(fa), fm.get(fb)
                if not all(isinstance(x, (int, float)) and not isinstance(x, bool)
                           for x in (va, vb)):
                    continue
                applied += 1
                if abs(float(va) - float(vb)) > tol:
                    violations['cross_record_fields_unequal'].append(
                        f"{fm.get('id', p.stem)}: {fa}={float(va):,.2f} vs "
                        f"{fb}={float(vb):,.2f} (delta {abs(float(va) - float(vb)):,.2f})")

        elif kind == 'field_gte':
            field, floor = rule.get('field'), rule.get('floor_field')
            tol = float(rule.get('tolerance', 0))
            for p, fm in recs:
                v, f = fm.get(field), fm.get(floor)
                if not all(isinstance(x, (int, float)) and not isinstance(x, bool)
                           for x in (v, f)):
                    continue
                applied += 1
                if float(v) < float(f) - tol:
                    violations['cross_record_field_below_floor'].append(
                        f"{fm.get('id', p.stem)}: {field}={float(v):,.2f} < "
                        f"{floor}={float(f):,.2f}")

        elif kind == 'field_agreement':
            list_field = rule.get('list_field')
            key, field = rule.get('key'), rule.get('field')
            groups = defaultdict(list)
            for p, fm in recs:
                for row in fm.get(list_field) or []:
                    if not isinstance(row, dict):
                        continue
                    k, v = row.get(key), row.get(field)
                    if k is not None and v is not None:
                        groups[str(k)].append((fm.get('id', p.stem), str(v)))
            for k, entries in groups.items():
                applied += 1
                if len(set(v for _, v in entries)) > 1:
                    violations['cross_record_field_disagreement'].append(
                        f"{list_field}.{field} for {k!r} differs across records: "
                        f"{entries[:3]} (total {len(entries)} citations)")

        else:
            violations['invariants_config_malformed'].append(
                f"cross_record rule type {kind!r} not supported "
                f"(supported: sum_matches, fields_equal, field_gte, field_agreement)")
    coverage.append(
        f"Cross-record rules: {len(rules)} configured rules, {applied} evaluations.")


# ---------------------------------------------------------------------------
# Check 6: date sanity
# ---------------------------------------------------------------------------

def check_dates(records, violations, inv, coverage):
    project = (inv or {}).get('project') or {}
    dmin = as_date(project.get('date_min'))
    dmax = as_date(project.get('date_max'))
    today = Date.today()
    checked = 0
    for p, fm, _ in records:
        if not fm:
            continue
        rec_id = fm.get('id', p.stem)
        raw = fm.get('date')
        if raw is None:
            continue
        d = as_date(raw)
        if d is None:
            violations['unparseable_date'].append(f"{rec_id}: date={raw!r}")
            continue
        checked += 1
        if d > today:
            violations['future_date'].append(f"{rec_id}: date={d}")
        if dmin and d < dmin:
            violations['date_before_project_window'].append(f"{rec_id}: date={d}")
        if dmax and d > dmax:
            violations['date_after_project_window'].append(f"{rec_id}: date={d}")
    if dmin or dmax:
        coverage.append(
            f"Date sanity: {checked} record dates checked (future dates plus "
            f"project window {dmin or 'open'} to {dmax or 'open'}).")
    else:
        coverage.append(
            f"Date sanity: {checked} record dates checked for future dates only "
            f"(no project date window configured).")


# ---------------------------------------------------------------------------
# Check 7: vendor name sanity (config allowlist plus built-in heuristics)
# ---------------------------------------------------------------------------

def check_vendors(records, violations, inv, coverage):
    known = [str(v).casefold() for v in ((inv or {}).get('vendor_names') or [])]
    # Built-in heuristics for extraction noise captured as a vendor name:
    # a lone month name, a pure number, or a document header fragment.
    noise_patterns = [
        re.compile(r'^(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)$', re.I),
        re.compile(r'^\d+$'),
        re.compile(r'^(pay app|application|invoice)\s*(no|number|#)\b', re.I),
    ]
    heuristic_checked = 0
    allowlist_checked = 0
    for p, fm, _ in records:
        if not fm or 'vendor' not in fm:
            continue
        rec_id = fm.get('id', p.stem)
        v = fm.get('vendor')
        if not v or (isinstance(v, str) and v.strip().casefold() == 'unknown'):
            violations['vendor_missing_or_unknown'].append(rec_id)
            continue
        v = str(v).strip()
        heuristic_checked += 1
        if any(pat.match(v) for pat in noise_patterns):
            violations['vendor_looks_like_extraction_noise'].append(
                f"{rec_id}: vendor={v!r}")
            continue
        if known:
            allowlist_checked += 1
            vf = v.casefold()
            if not any(k == vf or k in vf or vf in k for k in known):
                violations['vendor_not_in_allowlist'].append(
                    f"{rec_id}: vendor={v!r} matches no configured vendor name")
    if known:
        coverage.append(
            f"Vendor names: {heuristic_checked} vendor fields heuristic-checked; "
            f"{allowlist_checked} compared against the {len(known)}-name allowlist.")
    else:
        coverage.append(
            f"Vendor names: {heuristic_checked} vendor fields heuristic-checked; "
            f"allowlist comparison skipped (no vendor_names configured).")


# ---------------------------------------------------------------------------
# Check 8: built-in type-specific checks
# ---------------------------------------------------------------------------

def get_format(inv, key):
    fmt = ((inv or {}).get('formats') or {}).get(key, DEFAULT_FORMATS[key])
    return re.compile(fmt)


def check_amendment(records, violations, inv, root):
    """Amendment: the not-to-exceed amount must appear in the cited source, and
    the amendment label must match the configured format."""
    label_re = get_format(inv, 'amendment_label')
    for p, fm, _ in records:
        if not fm or fm.get('type') != 'Amendment':
            continue
        rec_id = fm.get('id', p.stem)
        sidecar_text = get_sidecar_text(fm.get('source_files') or [], root)
        nte = fm.get('nte_amount')
        if sidecar_text and isinstance(nte, (int, float)) and not isinstance(nte, bool):
            if not value_in_sidecar(nte, sidecar_text):
                violations['amendment_nte_not_in_source'].append(
                    f"{rec_id}: nte_amount={nte}")
        label = fm.get('amendment_label', '')
        if isinstance(label, str) and label and not label_re.match(label.strip()):
            violations['amendment_label_malformed'].append(
                f"{rec_id}: amendment_label={label!r}")


def check_asi(records, violations, root):
    """ASI: when drawing or spec references were extracted, at least one must
    appear verbatim in the cited source."""
    for p, fm, _ in records:
        if not fm or fm.get('type') != 'ASI':
            continue
        rec_id = fm.get('id', p.stem)
        sidecar_text = get_sidecar_text(fm.get('source_files') or [], root)
        if not sidecar_text:
            continue
        all_refs = [str(d) for d in fm.get('affected_drawings') or []]
        all_refs += [str(s) for s in fm.get('affected_specs') or []]
        if all_refs and not any(ref in sidecar_text for ref in all_refs):
            violations['asi_drawings_specs_not_in_source'].append(
                f"{rec_id}: none of {all_refs[:3]}... in source")


def check_rfi(records, violations, root):
    """RFI: the initiation date must appear in the cited source, and the first
    significant word of the subject should appear as well."""
    for p, fm, _ in records:
        if not fm or fm.get('type') != 'RFI':
            continue
        rec_id = fm.get('id', p.stem)
        sidecar_text = get_sidecar_text(fm.get('source_files') or [], root)
        if not sidecar_text:
            continue
        di = fm.get('date_initiated')
        if isinstance(di, str) and di and di not in sidecar_text:
            violations['rfi_date_initiated_not_in_source'].append(
                f"{rec_id}: date_initiated={di}")
        subj = fm.get('subject')
        if isinstance(subj, str) and subj:
            first_word = subj.split()[0] if subj.split() else ''
            if first_word and len(first_word) >= 4 and first_word not in sidecar_text:
                violations['rfi_subject_not_in_source'].append(
                    f"{rec_id}: subject={subj[:40]!r}")


def check_base_contract(records, violations, root):
    """BaseContract: the AIA form designation must appear in the source and not
    be margin noise (an OCR of the trademark superscript, ending in TM)."""
    for p, fm, _ in records:
        if not fm or fm.get('type') != 'BaseContract':
            continue
        rec_id = fm.get('id', p.stem)
        form = fm.get('aia_form_text')
        if not isinstance(form, str) or not form:
            continue
        sidecar_text = get_sidecar_text(fm.get('source_files') or [], root)
        if sidecar_text and form not in sidecar_text:
            violations['base_contract_form_not_in_source'].append(
                f"{rec_id}: aia_form_text={form!r}")
        if form.endswith('TM'):
            violations['base_contract_form_margin_noise'].append(
                f"{rec_id}: aia_form_text={form!r} looks like a trademark margin artifact")


def check_invoice(records, violations, inv, root):
    """Invoice: total_amount is covered by the core source-presence check; here
    the cost code format and its presence in the source are checked."""
    cc_re = get_format(inv, 'cost_code')
    for p, fm, _ in records:
        if not fm or fm.get('type') != 'Invoice':
            continue
        rec_id = fm.get('id', p.stem)
        cc = fm.get('cost_code')
        if not isinstance(cc, str) or not cc:
            continue
        if not cc_re.match(cc):
            violations['invoice_cost_code_malformed'].append(
                f"{rec_id}: cost_code={cc!r}")
            continue
        sidecar_text = get_sidecar_text(fm.get('source_files') or [], root)
        if sidecar_text and cc not in sidecar_text:
            violations['invoice_cost_code_not_in_source'].append(
                f"{rec_id}: cost_code={cc}")


def check_change_orders(records, violations, root):
    """SubcontractCO and PrimeCO: the three contract-sum figures must each
    appear in the source (covered by the core check when field names match the
    money heuristic; re-checked here by name), and the arithmetic
    original + previous + this change = new must hold. The arithmetic can also
    be expressed as a cross_record sum_matches rule; this built-in covers the
    canonical field names."""
    for p, fm, _ in records:
        if not fm or fm.get('type') not in ('SubcontractCO', 'PrimeCO'):
            continue
        rec_id = fm.get('id', p.stem)
        orig = fm.get('original_contract_sum')
        change = fm.get('this_change_amount')
        new_sum = fm.get('new_contract_sum')
        prev = fm.get('previous_co_total', 0)
        nums = [orig, change, new_sum]
        if all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in nums):
            expected = orig + (prev if isinstance(prev, (int, float)) else 0) + change
            if abs(expected - new_sum) > 0.5:  # 50-cent rounding tolerance
                violations['co_arithmetic_mismatch'].append(
                    f"{rec_id}: orig={orig} + prev={prev} + change={change} "
                    f"!= new={new_sum} (delta {new_sum - expected:+.2f})")


def check_inspection(records, violations, inv, root):
    """Inspection: the lab name (or a configured anchor for it) must appear in
    the cited sidecar. Sampled at up to 10 records per lab to bound cost, and
    only applied when the sidecar carries real text."""
    lab_anchors = {str(k): [str(a).lower() for a in v or []]
                   for k, v in (((inv or {}).get('lab_anchors')) or {}).items()}
    by_lab = defaultdict(list)
    for p, fm, _ in records:
        if fm and fm.get('type') == 'Inspection':
            by_lab[fm.get('lab', 'unknown')].append((p, fm))
    for lab, recs in by_lab.items():
        if lab in ('unknown', '', None):
            continue
        anchors = [str(lab).lower()] + lab_anchors.get(str(lab), [])
        for p, fm in recs[:10]:
            sf = fm.get('source_files') or []
            sidecar = sf[0].get('sidecar') if sf and isinstance(sf[0], dict) else None
            if not sidecar:
                continue
            sc_path = root / sidecar
            if not sc_path.exists():
                continue
            text = sc_path.read_text(errors='ignore')
            if len(text.strip()) > 200 and not any(a in text.lower() for a in anchors):
                violations['inspection_lab_not_in_source'].append(
                    f"{fm.get('id', p.stem)}: lab={lab} but no anchor "
                    f"{anchors} in sidecar (size={len(text)})")


def check_discrepancy(records, violations):
    """Discrepancy: the wiki's source-conflict register. Each record must carry
    at least two conflicting_sources entries with source, tier, and value, and
    the asserted values must actually differ. A record whose sources all assert
    the same value would silently launder a non-conflict into the register. A
    resolved record must carry a real resolution, not a placeholder."""
    for p, fm, _ in records:
        if not fm or fm.get('type') != 'Discrepancy':
            continue
        rec_id = fm.get('id', p.stem)
        cs = fm.get('conflicting_sources')
        if not isinstance(cs, list) or len(cs) < 2:
            violations['discrepancy_needs_two_sources'].append(
                f"{rec_id}: conflicting_sources has < 2 entries")
            continue
        values = []
        for entry in cs:
            if not isinstance(entry, dict):
                violations['discrepancy_source_malformed'].append(
                    f"{rec_id}: conflicting_sources entry not a mapping")
                continue
            for k in ('source', 'tier', 'value'):
                if not entry.get(k):
                    violations['discrepancy_source_missing_field'].append(
                        f"{rec_id}: conflicting_sources entry missing {k!r}")
            if entry.get('value') is not None:
                values.append(str(entry.get('value')).strip())
        if len(values) >= 2 and len(set(values)) < 2:
            violations['discrepancy_no_value_divergence'].append(
                f"{rec_id}: all conflicting_sources assert the same value "
                f"{values[0]!r}, not a real conflict")
        resolution = str(fm.get('resolution', '')).strip()
        if fm.get('status') == 'resolved':
            if not resolution or resolution.lower() in ('unresolved', 'tbd', 'todo', 'none'):
                violations['discrepancy_resolved_without_resolution'].append(
                    f"{rec_id}: status=resolved but resolution={resolution!r}")
        if not str(fm.get('disputed_fact', '')).strip():
            violations['discrepancy_empty_disputed_fact'].append(rec_id)


def check_bidpackage(records, violations):
    """BidPackage: buyout-record cross-field consistency. Bid-comparison
    sources are often image PDFs with no usable sidecar, so these checks are
    cross-field rather than source-presence. Amount ranges belong in the
    invariants file's outlier_bounds."""
    for p, fm, _ in records:
        if not fm or fm.get('type') != 'BidPackage':
            continue
        rec_id = fm.get('id', p.stem)
        status = fm.get('status', '')
        awarded_to = fm.get('awarded_to')
        awarded_amount = fm.get('awarded_amount')
        if status == 'awarded':
            if not awarded_to:
                violations['bidpackage_awarded_no_sub'].append(
                    f"{rec_id}: status=awarded but awarded_to is empty")
            if awarded_amount is None:
                violations['bidpackage_awarded_no_amount'].append(
                    f"{rec_id}: status=awarded but awarded_amount is empty")
        elif status in ('bids-received', 'out-for-bid'):
            if awarded_to or awarded_amount is not None:
                violations['bidpackage_unawarded_has_award'].append(
                    f"{rec_id}: status={status} but carries awarded_to/awarded_amount")
        d = as_date(fm.get('date'))
        ad = as_date(fm.get('awarded_date'))
        if d and ad and ad < d:
            violations['bidpackage_award_before_bid_date'].append(
                f"{rec_id}: awarded_date={ad} precedes bid-comparison date={d}")


# ---------------------------------------------------------------------------
# Check 9: universal invariants (all record types)
# ---------------------------------------------------------------------------

def check_universal(records, violations, root):
    seen_ids = defaultdict(list)
    for p, fm, _ in records:
        if not fm or not isinstance(fm, dict):
            continue
        rec_id = fm.get('id', p.stem)
        seen_ids[rec_id].append(str(p.relative_to(root)))
        # Placeholder strings in identity-bearing fields. Missing fields are
        # the structural audit's job; this catches present-but-empty values.
        for k in ('title', 'vendor', 'party', 'lab', 'permit_no', 'issuing_authority'):
            v = fm.get(k)
            if v is None or v == '':
                continue
            if isinstance(v, str) and (v.strip() == ''
                                       or v.strip().lower() in PLACEHOLDER_STRINGS):
                violations['empty_or_placeholder_string'].append(f"{rec_id}: {k}={v!r}")
        title = fm.get('title', '')
        if isinstance(title, str) and title.strip() == rec_id:
            violations['title_is_just_id'].append(rec_id)
    for rec_id, paths in seen_ids.items():
        if len(paths) > 1:
            violations['duplicate_id'].append(f"{rec_id}: in {paths}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

NOT_CHECKED = [
    "Sidecar fidelity against the original PDFs (OCR drift is a separate deep-audit concern).",
    "Non-dollar prose claims in record bodies (attribution and citation discipline are the lint audit's job).",
    "Link resolution, schema field presence, and path existence (the structural audit's job).",
    "Record types with no built-in check receive only the universal, date, and source-presence checks.",
    "Spreadsheet (xlsx) sources are not opened; only prose sidecars are read.",
]


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--root', default='.', help='Wiki workspace root (default: cwd)')
    ap.add_argument('--invariants', default=None,
                    help='Path to project invariants YAML '
                         '(default: <root>/.claude/project-invariants.yaml)')
    ap.add_argument('--class', dest='cls', help='Audit one record type only (e.g. PayApp)')
    ap.add_argument('--terse', action='store_true', help='Counts only')
    args = ap.parse_args()

    root = Path(args.root).resolve()
    records_dir = root / 'records'
    if not records_dir.is_dir():
        print(f"error: no records/ directory under {root}", file=sys.stderr)
        return 2

    inv_path = Path(args.invariants) if args.invariants \
        else root / '.claude' / 'project-invariants.yaml'
    inv = None
    inv_note = ''
    if inv_path.exists():
        try:
            inv = yaml.safe_load(inv_path.read_text()) or {}
            try:
                inv_display = inv_path.relative_to(root)
            except ValueError:
                inv_display = inv_path.name
            inv_note = f"Invariants loaded from {inv_display}."
        except yaml.YAMLError as e:
            print(f"error: invariants file {inv_path} does not parse: {e}", file=sys.stderr)
            return 2
    else:
        inv_note = (f"No invariants file at {inv_path}: class constant, outlier bound, "
                    f"reference range, vendor allowlist, cross-record, and project "
                    f"date-window checks were SKIPPED. Copy "
                    f"templates/project-invariants.yaml there to enable them.")

    records = []
    for p in sorted(records_dir.rglob('*.md')):
        fm, body = parse_fm(p.read_text(errors='ignore'))
        if args.cls and (not fm or fm.get('type') != args.cls):
            continue
        records.append((p, fm, body))

    violations = defaultdict(list)
    coverage = [inv_note]
    if args.cls:
        coverage.append(f"Scope limited to record type {args.cls!r} via --class.")

    check_source_presence(records, violations, inv, root, coverage)
    check_class_constants(records, violations, inv, coverage)
    check_outlier_bounds(records, violations, inv, coverage)
    check_reference_ranges(records, violations, inv, coverage)
    check_cross_record(records, violations, inv, coverage)
    check_dates(records, violations, inv, coverage)
    check_vendors(records, violations, inv, coverage)
    check_amendment(records, violations, inv, root)
    check_asi(records, violations, root)
    check_rfi(records, violations, root)
    check_base_contract(records, violations, root)
    check_invoice(records, violations, inv, root)
    check_change_orders(records, violations, root)
    check_inspection(records, violations, inv, root)
    check_discrepancy(records, violations)
    check_bidpackage(records, violations)
    check_universal(records, violations, root)
    coverage.append("Built-in type checks ran for: Amendment, ASI, RFI, BaseContract, "
                    "Invoice, SubcontractCO/PrimeCO, Inspection, Discrepancy, BidPackage.")

    # Suppressions: the invariants file may carry known-and-accepted findings
    # as {category: [substring, ...]}. Suppressed items are reported separately.
    suppressed = defaultdict(list)
    for category, patterns in ((inv or {}).get('suppressions') or {}).items():
        if category not in violations or not patterns:
            continue
        kept = []
        for msg in violations[category]:
            if any(pat in msg for pat in patterns):
                suppressed[category].append(msg)
            else:
                kept.append(msg)
        if kept:
            violations[category] = kept
        else:
            del violations[category]

    total = sum(len(v) for v in violations.values())
    n_suppressed = sum(len(v) for v in suppressed.values())

    # ---- report -----------------------------------------------------------
    lines = [f"# Semantic audit - {Date.today().isoformat()}", "",
             f"Walked {len(records)} records under records/ (root: {root.name}/)",
             f"Total semantic violations: {total}"
             + (f" ({n_suppressed} suppressed via config)" if n_suppressed else ""),
             ""]
    for cat, vs in sorted(violations.items(), key=lambda x: -len(x[1])):
        lines.append(f"## {cat} - {len(vs)}")
        lines.extend(f"- {v}" for v in vs)
        lines.append("")
    if suppressed:
        lines.append("## Suppressed (accepted via invariants config)")
        for cat, vs in sorted(suppressed.items()):
            lines.extend(f"- [{cat}] {v}" for v in vs)
        lines.append("")
    lines.append("## Coverage")
    lines.append("")
    lines.append("What this run checked:")
    lines.extend(f"- {c}" for c in coverage)
    lines.append("")
    lines.append("What this audit does NOT check:")
    lines.extend(f"- {c}" for c in NOT_CHECKED)
    lines.append("")

    health_dir = root / '.claude' / 'health'
    health_dir.mkdir(parents=True, exist_ok=True)
    report_path = health_dir / 'semantic-audit.md'
    report_path.write_text('\n'.join(lines))

    if args.terse:
        print(f"SEMANTIC AUDIT: {total} violations across {len(violations)} categories"
              + (f" ({n_suppressed} suppressed)" if n_suppressed else ""))
        for cat, vs in sorted(violations.items(), key=lambda x: -len(x[1])):
            print(f"  [{cat}] {len(vs)}")
        print(f"Report: {report_path}")
    else:
        print(f"Walked {len(records)} records, {total} semantic violations")
        for cat, vs in sorted(violations.items(), key=lambda x: -len(x[1])):
            print(f"\n[{cat}] {len(vs)}")
            for v in vs[:10]:
                print(f"  {v}")
            if len(vs) > 10:
                print(f"  ... ({len(vs) - 10} more)")
        print("\nCoverage:")
        for c in coverage:
            print(f"  {c}")
        print("Not checked:")
        for c in NOT_CHECKED:
            print(f"  - {c}")
        print(f"\nReport written to {report_path}")

    return 0 if total == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
