# -*- coding: utf-8 -*-
"""
IMPD — value-map review: every mapped code read with its source label against the target label.

A value map that is copied from one survey to another by variable name and code list looks right by every structural
check (valid codes, plausible counts, universes) and can still be wrong when the two questionnaires use the same codes
for opposite answers (SING 2009 ANDLAND 1 'direct naar Nederland gekomen' mapped like SPVN 2003 ANDLAND 1 'ja', into
'stayed in other countries' = yes). This check makes such rows visible and refuses the ones it can decide against:

  1. REUSE     the same source name maps into the same target in two surveys with the same code -> value rows, but the
               source labels of those codes do not say the same thing (no common polarity, no common word, neither
               contains the other), or the labels agree and the rows differ: the rows were copied across
               questionnaires that differ - review
  2. POLARITY  a two-valued target (yesno, mentioned, 0/1 sets): a source label that reads as a negation ('nee',
               'niet', 'geen', 'nooit', 'not mentioned') mapped to the affirmative code, or 'ja' / 'mentioned' to the
               negative code - FAIL
  3. APPROVAL  a source label of a two-valued target that the cue lists cannot classify ('direct naar Nederland
               gekomen') mapped to a value, a polarity contradiction that is intended (SIM 2006 GEENLID 'none of
               these' inverted into soc_mem), and every REUSE pair: must be listed in crosswalks/label_approvals.csv
               (kind, target, source_var, source_value, survey, target_value, reason; kind = polarity with one survey,
               kind = reuse with 'survey_a|survey_b') - FAIL until a person has read the labels against the target label
               and written the reason; the approval is bound to the target value that was read (the shared mapping for a
               reuse pair, 'a/b' when the surveys map differently), so a changed mapping is a new row to read
  4. REVIEW    docs/value_map_review.csv: every value-map row with the source label and the target label side by side,
               so that the review reads labels, not codes
  5. OVERLAP   value-set labels that state numeric ranges ('1991-2000', '2000 or later', 'under 15', '70+') must not
               overlap within a value set (yr_cat5 4 '1991-2000' and 5 '2000 or later' both held 2000) - FAIL, unless
               approved (kind overlap, target = the value set, source_value = 'code1|code2': answer options whose
               wording is fuzzy by design, e.g. 'binnen 1-2 jaar' / 'tussen 2 en 5 jaar')

Run:  python code/tools/value_map_review.py [<crosswalks folder>]     (default: crosswalks/; exit status 1 on FAIL)
"""
import csv, os, re, sys, collections

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
CW = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'crosswalks')
OUT = os.path.join(ROOT, 'docs', 'value_map_review%s.csv' % ('' if CW.rstrip('/\\').endswith('crosswalks') else '_' + os.path.basename(CW.rstrip('/\\'))))


def read_csv(path):
    if not os.path.exists(path):
        return []
    for enc in ('utf-8-sig', 'cp1252', 'latin1'):
        try:
            with open(path, encoding=enc, newline='') as f:
                return list(csv.DictReader(f))
        except UnicodeDecodeError:
            continue
    raise RuntimeError('cannot decode ' + path)


def num(s):
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


def norm(s):
    s = (s or '').strip().lower().replace('\\', '/')
    s = re.sub(r'^vraag\s*[0-9a-z_.]*\s*[:\-]?\s*', '', s)
    s = re.sub(r'\s*/\s*', '/', re.sub(r'\s+', ' ', s))
    return re.sub(r'[\s.:;,?!]+$', '', s)


vmap = read_csv(os.path.join(CW, 'value_map.csv'))
vsets = collections.defaultdict(dict)
for r in read_csv(os.path.join(CW, 'valuesets.csv')):
    vsets[r['valueset']][r['code']] = r['label_en']
varmap = {r['target']: r for r in read_csv(os.path.join(CW, 'variable_map.csv'))}
labels = collections.defaultdict(dict)
for r in read_csv(os.path.join(CW, 'source_labels.csv')):
    labels[(r['survey'], r['source_var'].upper())][r['code'].strip()] = r['label_nl']
# an approval is bound to the mapping that was read: its target_value must equal the row's target value (polarity), the
# shared mapping of the pair (reuse, 'a/b' when the two surveys map differently); a changed mapping is a new row to read
# (follow-up audit of v0.4.7: without the value, inverting an approved row still passed)
approvals = {(r.get('kind', 'polarity'), r['survey'], r['source_var'].upper(), r['source_value'], r['target']): (r.get('target_value', '') or '').strip()
             for r in read_csv(os.path.join(CW, 'label_approvals.csv'))}
unbound = []                                                                  # approvals used without a target value
changed = []                                                                  # approved rows whose mapping differs from the approved value


def approved(key, value):
    """True when the key is approved for exactly this target value; an approval without a value is reported, not used"""
    if key not in approvals:
        return False
    if approvals[key] == '':
        unbound.append(key); return False
    return approvals[key] == value

TWO = {vs for vs, codes in vsets.items() if set(codes) == {'0', '1'}}          # yes/no-like value sets
NEG = re.compile(r"^(nee\b|neen\b|niet\b|geen\b|nooit\b|not mentioned|no\b|non\b)", re.I)
AFF = re.compile(r"^(ja\b|yes\b|mentioned|genoemd|wel\b)", re.I)
STOP = {'ja', 'nee', 'niet', 'geen', 'wel', 'een', 'van', 'het', 'met', 'naar', 'ook', 'nog', 'als', 'dan', 'voor', 'deze',
        'dit', 'die', 'dat', 'uw', 'heeft', 'hebt', 'bent', 'zijn', 'over', 'door', 'maar', 'anders', 'alleen', 'zowel'}


def polarity(lab):
    lab = (lab or '').strip()
    return 'neg' if NEG.search(lab) else ('aff' if AFF.search(lab) else None)


def compatible(la, lb):
    """two source labels that can carry the same mapping: same polarity, a common content word, or one inside the other"""
    pa, pb = polarity(la), polarity(lb)
    if pa and pb:
        return pa == pb
    if la in lb or lb in la:
        return True
    ta = {w for w in re.findall(r'[a-z]{4,}', la) if w not in STOP}
    tb = {w for w in re.findall(r'[a-z]{4,}', lb) if w not in STOP}
    return bool(ta & tb)


def src_label(survey, sv, value):
    d = labels.get((survey, sv.upper()), {})
    v = value.strip().strip("'")
    if v in d:
        return d[v]
    n = num(v)
    if n is not None:
        for k, lab in d.items():
            if num(k) == n:
                return lab
    return ''


# ---- 4. review table ---------------------------------------------------------------------------------------------
rows = []
for r in vmap:
    t = r['target']; vs = varmap.get(t, {}).get('valueset', '')
    tv = r['target_value']
    rows.append(dict(target=t, target_label=varmap.get(t, {}).get('label_en', ''), survey=r['survey'], source_var=r['source_var'],
                     source_value=r['source_value'], source_label=src_label(r['survey'], r['source_var'], r['source_value']),
                     target_value=tv, target_value_label=vsets.get(vs, {}).get(tv, '' if tv.startswith('.') else ''), valueset=vs))
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w', encoding='utf-8', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else ['target'])
    w.writeheader(); w.writerows(rows)

# ---- 0. approved rows still map as approved: a row that was read and signed with one value and now carries another was
#         changed after the reading - FAIL whatever the cue lists make of the new value (an inverted 'none of these' item
#         reads as a plain yes/no); the same for an approved reuse pair whose shared mapping changed
for r in vmap:
    key = ('polarity', r['survey'], r['source_var'].upper(), r['source_value'], r['target'])
    if key in approvals and approvals[key] not in ('', r['target_value']):
        changed.append((r['survey'], r['target'], r['source_var'], r['source_value'], approvals[key], r['target_value']))

# ---- 1. reuse across surveys -------------------------------------------------------------------------------------
by = collections.defaultdict(lambda: collections.defaultdict(dict))        # (target, SOURCE) -> survey -> {code: tv}
for r in vmap:
    if not r['source_value'].startswith("'") and r['source_value'] not in ('*', '.') and '-' not in r['source_value'].lstrip('-'):
        by[(r['target'], r['source_var'].upper())][r['survey']][r['source_value']] = r['target_value']
reuse = []
for (t, sv), per in by.items():
    svys = sorted(per)
    for i, a in enumerate(svys):
        for b in svys[i + 1:]:
            for code in sorted(set(per[a]) & set(per[b]), key=lambda x: num(x) or 0):
                la, lb = norm(src_label(a, sv, code)), norm(src_label(b, sv, code))
                if not la or not lb:
                    continue
                rkey = ('reuse', '%s|%s' % (a, b), sv, code, t)
                now = per[a][code] if per[a][code] == per[b][code] else '%s/%s' % (per[a][code], per[b][code])
                if rkey in approvals and approvals[rkey] not in ('', now):
                    changed.append(('%s|%s' % (a, b), t, sv, code, approvals[rkey], now))
                if la != lb and per[a][code] == per[b][code] and not compatible(la, lb):
                    if not approved(rkey, per[a][code]):
                        reuse.append((t, sv, code, a, la, b, lb, per[a][code], 'same mapping, labels that do not say the same'))
                elif la == lb and per[a][code] != per[b][code]:
                    if not approved(rkey, '%s/%s' % (per[a][code], per[b][code])):
                        reuse.append((t, sv, code, a, la, b, lb, '%s / %s' % (per[a][code], per[b][code]), 'same label, different mapping'))

# ---- 2. polarity and 3. approvals for two-valued targets ----------------------------------------------------------
fails, needs = [], []
for r in vmap:
    t = r['target']; vs = varmap.get(t, {}).get('valueset', '')
    if vs not in TWO or r['target_value'].startswith('.') or r['source_value'] in ('*', '.'):
        continue
    lab = src_label(r['survey'], r['source_var'], r['source_value'])
    if not lab:
        continue
    kind = polarity(lab)
    key = ('polarity', r['survey'], r['source_var'].upper(), r['source_value'], t)
    if kind == 'neg' and r['target_value'] == '1' or kind == 'aff' and r['target_value'] == '0':
        if not approved(key, r['target_value']):
            fails.append((r['survey'], t, r['source_var'], r['source_value'], lab, r['target_value'], vsets[vs][r['target_value']]))
    elif kind is None and not approved(key, r['target_value']):
        needs.append((r['survey'], t, r['source_var'], r['source_value'], lab, r['target_value'], vsets[vs][r['target_value']]))

# ---- 5. overlapping numeric ranges in the labels of one value set ---------------------------------------------------
def interval(label):
    l = label.lower().replace(',', '')
    m = re.search(r'(?<![\d.])(\d{1,4})\s*(?:-|to|tot|t/m)\s*(\d{1,4})(?![\d.])', l)
    if m:
        return float(m.group(1)), float(m.group(2))
    m = re.search(r'(?<![\d.])(\d{1,4})\s*(?:or later|or more|or older|and over|en ouder|en meer|of meer|of ouder|\+)', l)
    if m:
        return float(m.group(1)), 1e9
    m = re.search(r'(?:under|less than|below|jonger dan|minder dan|tot)\s*(\d{1,4})(?![\d.])', l)
    if m:
        return -1e9, float(m.group(1)) - 1
    return None
overlaps = []
for vs, codes in vsets.items():
    iv = [(c, lab, interval(lab)) for c, lab in codes.items()]
    iv = [x for x in iv if x[2] and 'undivided' not in x[1].lower()]
    for i in range(len(iv)):
        for j in range(i + 1, len(iv)):
            (c1, l1, (a1, b1)), (c2, l2, (a2, b2)) = iv[i], iv[j]
            # amounts, hours and durations share a boundary by convention ('750-950', '950-1150'); years, ages and
            # counts are integers, where a shared endpoint is an overlap ('1991-2000', '2000 or later')
            amount = re.search(r'euro|€|gulden|guilder|uur|hour|minut|km|month|maand|week|percent|%', (l1 + ' ' + l2).lower())
            if ('overlap', '', '', '%s|%s' % (c1, c2), vs) in approvals:      # answer options with fuzzy boundaries, read (no value to bind)
                continue
            if (max(a1, a2) < min(b1, b2)) if amount else (max(a1, a2) <= min(b1, b2)):
                overlaps.append((vs, c1, l1, c2, l2))

print('value-map review: %d rows -> %s' % (len(rows), os.path.relpath(OUT, ROOT)))
print('OVERLAP  %d pair(s) of value-set labels whose numeric ranges overlap:' % len(overlaps))
for x in overlaps:
    print('   %s: %s "%s" | %s "%s"' % x)
print('REUSE  %d code(s) mapped alike in two surveys whose labels do not say the same (or alike labels mapped differently), not '
      'yet approved (kind reuse, survey "a|b"):' % len(reuse))
for x in reuse:
    print('   %s <- %s %s: %s "%s" | %s "%s" -> %s (%s)' % x)
print('POLARITY FAIL  %d row(s): a negation mapped to the affirmative code or the reverse:' % len(fails))
for x in fails:
    print('   %s %s <- %s %s "%s" -> %s %s' % x)
print('APPROVAL  %d row(s) of two-valued targets whose source label the cue lists cannot read: list them in crosswalks/label_approvals.csv '
      '(survey, source_var, source_value, target, target_value, reason) after reading the label against the target label:' % len(needs))
for x in needs:
    print('   %s %s <- %s %s "%s" -> %s %s' % x)
print('CHANGED  %d approved row(s) or pair(s) whose mapping differs from the approved value (read the row again and re-sign it):' % len(changed))
for x in changed:
    print('   %s %s <- %s %s: approved -> %s, now -> %s' % x)
unbound = sorted(set(unbound))
print('UNBOUND  %d approval(s) without a target_value (an approval is bound to the mapping that was read; add the value):' % len(unbound))
for x in unbound:
    print('   %s %s %s %s -> %s' % (x[0], x[1], x[2], x[3], x[4]))
if fails or needs or reuse or overlaps or unbound or changed:
    print('FAIL value-map review: %d polarity, %d unread two-valued labels, %d reuse pairs to approve, %d overlapping ranges, %d unbound approvals, %d changed after approval' % (len(fails), len(needs), len(reuse), len(overlaps), len(unbound), len(changed)))
    sys.exit(1)
print('PASS value-map review: every two-valued mapping reads as a yes/no or is approved; every cross-survey reuse with differing labels is approved')
