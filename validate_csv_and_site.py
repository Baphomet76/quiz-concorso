#!/usr/bin/env python3
"""
validate_csv_and_site.py
Validate a CSV file against the parser rules used in index.html and check simple site compatibility.
Usage: python validate_csv_and_site.py [--csv database.csv] [--html index.html]
Exits with code 0 when OK, non-zero otherwise.
"""
import argparse
import sys
import re
from collections import Counter


def normalize_header(value):
    v = (value or '').lower()
    # mimic JS: normalize('NFD'), remove diacritics, replace non-alnum with '_', trim
    import unicodedata
    v = unicodedata.normalize('NFD', v)
    v = re.sub(r'[\u0300-\u036f]+', '', v)
    v = re.sub(r'[^a-z0-9]+', '_', v)
    v = re.sub(r'^_|_$', '', v)
    return v


def parse_csv_line(line, sep):
    cells = []
    cur = ''
    in_quotes = False
    i = 0
    while i < len(line):
        ch = line[i]
        if ch == '"':
            if in_quotes and i + 1 < len(line) and line[i+1] == '"':
                cur += '"'
                i += 1
            else:
                in_quotes = not in_quotes
            i += 1
            continue
        if ch == sep and not in_quotes:
            cells.append(cur.strip())
            cur = ''
            i += 1
            continue
        cur += ch
        i += 1
    cells.append(cur.strip())
    return cells


def parse_records(text, sep):
    text = text.replace('\ufeff', '')
    # normalize newlines
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    lines = text.split('\n')
    rows = [parse_csv_line(line, sep) for line in lines]
    rows = [r for r in rows if any(str(c).strip() != '' for c in r)]
    return rows


def find_header_index(rows):
    for idx, row in enumerate(rows):
        if any('domanda' in normalize_header(c) for c in row) and any('risposta' in normalize_header(c) for c in row):
            return idx
    return -1


def validate(csv_path, html_path):
    errors = []
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            text = f.read()
    except Exception as e:
        errors.append(f"Cannot read CSV: {e}")
        return False, errors

    sep = ';' if ';' in text else ','
    rows = parse_records(text, sep)
    if len(rows) < 2:
        errors.append('CSV must contain a header and at least one row')
        return False, errors

    header_idx = find_header_index(rows)
    if header_idx == -1:
        errors.append('Header not found (needs a row with fields containing "domanda" and "risposta")')
        return False, errors

    header = rows[header_idx]
    data_rows = rows[header_idx+1:]

    # Basic structural checks: each data row must have at least 5 columns and non-empty domanda/correct/w1/w2
    problems = []
    ids = []
    for i, r in enumerate(data_rows, start=header_idx+2):
        if len(r) < 5:
            problems.append(f'Line {i}: only {len(r)} columns (need >=5)')
            continue
        idv = (r[0] or '').strip()
        domanda = (r[1] or '').strip()
        correct = (r[2] or '').strip()
        w1 = (r[3] or '').strip()
        w2 = (r[4] or '').strip()
        if not domanda or not correct or not w1 or not w2:
            problems.append(f'Line {i}: missing required fields (domanda/corretta/errata1/errata2)')
        ids.append(idv or f'__noid_line_{i}')

    dupes = [k for k,v in Counter(ids).items() if v > 1]
    if dupes:
        problems.append(f'Duplicate IDs found (examples): {dupes[:10]}')

    if problems:
        errors.extend(problems)
    else:
        # OK structural
        pass

    # Check compatibility with index.html: DATABASE_FILE constant
    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            html = f.read()
    except Exception as e:
        errors.append(f'Cannot read HTML file: {e}')
        return False, errors

    m = re.search(r"const\s+DATABASE_FILE\s*=\s*['\"]([^'\"]+)['\"]", html)
    if m:
        dbfile = m.group(1)
        if dbfile != csv_path.split('/')[-1] and dbfile != csv_path.split('\\')[-1]:
            errors.append(f"index.html expects DATABASE_FILE='{dbfile}' but CSV path is '{csv_path}'. Consider updating index.html or supplying csv='{dbfile}'")
    else:
        errors.append('DATABASE_FILE constant not found in index.html')

    ok = len(errors) == 0
    summary = {
        'total_rows': len(data_rows),
        'header_index': header_idx + 1,
        'sep': sep,
        'duplicates': dupes[:10]
    }
    return ok, (errors, summary)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--csv', default='database.csv', help='Path to CSV file')
    p.add_argument('--html', default='index.html', help='Path to index.html')
    args = p.parse_args()

    ok, result = validate(args.csv, args.html)
    if ok:
        errors, summary = result if isinstance(result, tuple) else ([], result)
        print(f"OK: CSV compatible. Total questions: {summary['total_rows']}. Delimiter: '{summary['sep']}'. Header row: {summary['header_index']}")
        if summary['duplicates']:
            print('Note: duplicate ID examples:', summary['duplicates'])
        sys.exit(0)
    else:
        errs = result
        print('VALIDATION FAILED:')
        for e in errs:
            print(' -', e)
        sys.exit(2)
