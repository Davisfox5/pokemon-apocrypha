#!/usr/bin/env python3
"""Resolved move inventory and signature-move candidate pools.

Move data in pokeemerald-expansion is generation-dependent: a field reads
`B_UPDATED_MOVE_DATA >= GEN_6 ? 90 : 80`. Reading the largest numeral out of the
source text answers a question nobody asked, and was wrong for 39 of the 559
Gen 1-5 moves in this build -- always high.

This tool runs the real preprocessor with the build's own flags, so every such
expression arrives here as a pure-numeric C expression that is evaluated exactly.
Do not re-derive move power by scanning the source; use this.

Outputs gba/evidence/move-inventory.json:
  moves                 resolved power/type/category/accuracy/pp/effect,
                        introducing generation, and breadth
  breadth               compiled-in base species that can learn the move, which
                        is availability; form entries inherit and are excluded
  tms / hms             the built lists, read from constants/tms_hms.h
  signature_pools       Tier 2 candidates per region, with the reasons entries
                        are excluded from the teachable pool

Usage: python3 tools/gba/move_inventory.py [--check]
  --check  recompute and fail if the tracked evidence file is stale
"""
import argparse
import ast
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GAME = ROOT / 'game'
LOCK = json.loads((ROOT / 'tools/gba/toolchain.json').read_text())
CPP = ROOT / 'tools/vendor/gba' / LOCK['directory'] / 'bin/arm-none-eabi-cpp'
EVIDENCE = ROOT / 'gba/evidence/move-inventory.json'

# Must match the Makefile's CPPFLAGS; a different set can resolve differently.
CPPFLAGS = ['-iquote', 'include', '-Wno-trigraphs', '-DMODERN=1', '-DTESTING=0',
            '-DEMERALD', '-std=gnu17']

# Region <- the generation whose moves it stocks, in story order.
REGIONS = [('Johto', 2), ('Kanto', 1), ('Hoenn', 3), ('Sinnoh', 4), ('Unova', 5)]
SIGNATURE_MIN_POWER = 86   # one above the TM table-power cap
FIELDS = ('power', 'type', 'accuracy', 'pp', 'priority', 'category', 'effect')


def preprocess(source, out):
    subprocess.run([str(CPP), *CPPFLAGS, source, '-o', out],
                   cwd=GAME, check=True)
    return Path(out).read_text()


def c_eval(expr):
    """Evaluate a purely numeric C expression; return None if it names anything."""
    e = expr.strip()
    if re.fullmatch(r'-?\d+', e):
        return int(e)
    if not re.fullmatch(r'[\d\s()?:<>=!&|+\-*/]+', e):
        return None
    py = e.replace('&&', ' and ').replace('||', ' or ')
    while True:  # collapse parenthesised comparisons so ternaries read flat
        m = re.search(r'\(([^()?:]*[<>=!][^()?:]*)\)', py)
        if not m:
            break
        try:
            py = py[:m.start()] + str(int(bool(eval(m.group(1), {'__builtins__': {}})))) + py[m.end():]
        except Exception:
            return None
    while '?' in py:
        m = re.search(r'([^?:()]+)\?([^?:()]+):([^?:()]+)', py)
        if not m:
            break
        py = f'{py[:m.start()]}(({m.group(2)}) if ({m.group(1)}) else ({m.group(3)})){py[m.end():]}'
    try:
        return int(eval(compile(ast.parse(py, mode='eval'), '<c>', 'eval'), {'__builtins__': {}}))
    except Exception:
        return None


def resolve_enum(expr):
    """Resolve `<numeric condition> ? NAME_A : NAME_B` down to one name.

    Type and category are generation-dependent too, not just power: Curse is
    Ghost or Mystery, and Charm, Moonlight and Sweet Kiss are Fairy or Normal
    depending on P_UPDATED_TYPES. Leaving these unresolved silently drops them
    out of any type-based analysis.
    """
    e = expr.strip()
    while '?' in e:
        m = re.match(r'\s*([^?]+?)\s*\?\s*([A-Za-z_][\w]*)\s*:\s*(.+)\s*$', e)
        if not m:
            break
        cond = c_eval(m.group(1))
        if cond is None:
            break
        e = m.group(2) if cond else m.group(3).strip()
    return e


def parse_moves(text):
    body = text[text.index('gMovesInfo[MOVES_COUNT_ALL] ='):]
    moves, cur = {}, None
    for line in body.splitlines():
        m = re.match(r'\s*\[(MOVE_[A-Z0-9_]+)\]\s*=', line)
        if m:
            cur = {'id': m.group(1)}
            moves[m.group(1)] = cur
        if cur is None:
            continue
        m = re.match(r'\s*\.name = COMPOUND_STRING\("(.*)"\)', line)
        if m:
            cur['name'] = m.group(1)
        m = re.match(r'\s*\.(\w+)\s*=\s*(.+?),?\s*$', line)
        if not m:
            continue
        key, raw = m.group(1), m.group(2).rstrip(',')
        if key in FIELDS and key not in cur:
            val = c_eval(raw)
            cur[key] = val if val is not None else raw
        elif key in ('multiHit', 'strikeCount') and key not in cur:
            cur[key] = c_eval(raw)
    return moves


def move_generations():
    gen, cur = {}, 1
    for line in (GAME / 'include/constants/moves.h').read_text().splitlines():
        m = re.match(r'\s*// Gen (\d)', line)
        if m:
            cur = int(m.group(1))
            continue
        m = re.match(r'\s*(MOVE_[A-Z0-9_]+)\s*(?:=|,)', line)
        if m:
            gen[m.group(1)] = cur
    return gen


def machine_lists():
    text = (GAME / 'include/constants/tms_hms.h').read_text()
    def block(name):
        part = text.split(f'#define {name}(F)', 1)[1].split('\n\n', 1)[0]
        return ['MOVE_' + x for x in re.findall(r'F\((\w+)\)', part)]
    return block('FOREACH_TM'), block('FOREACH_HM')


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--check', action='store_true',
                    help='fail if the tracked evidence file is stale')
    args = ap.parse_args()
    if not CPP.exists():
        ap.error('Run python3 tools/gba/setup.py first.')

    with tempfile.TemporaryDirectory() as tmp:
        moves = parse_moves(preprocess('src/move.c', f'{tmp}/move.i'))
        species_text = preprocess('src/pokemon.c', f'{tmp}/pokemon.i')

    unresolved = [k for k, v in moves.items() if not isinstance(v.get('power'), int)]
    if unresolved:
        sys.exit(f'Unresolved power expressions, refusing to emit: {unresolved}')

    # Compiled-in species only. Filtering by name suffix misses Sirfetch'd and
    # Ursaluna, which carry no form suffix but are compiled out anyway.
    tail = species_text[species_text.index('const struct SpeciesInfo gSpeciesInfo'):]
    enabled = set(re.findall(r'^    \[SPECIES_([A-Z0-9_]+)\]', tail, re.M)) - {'NONE', 'EGG'}

    learn = json.loads((GAME / 'src/data/pokemon/all_learnables.json').read_text())
    base = sorted(enabled & set(learn))     # forms inherit their base learnset
    breadth = {}
    for sp in base:
        for mv in learn[sp]:
            breadth[mv] = breadth.get(mv, 0) + 1

    gen = move_generations()
    tms, hms = machine_lists()
    special = json.loads((GAME / 'src/data/pokemon/special_movesets.json').read_text())
    tutors = set(json.loads((GAME / 'tools/learnset_helpers/build/all_tutors.json').read_text()))
    already = tutors | set(special['universalMoves']) | set(special['signatureTeachables'])

    inv = {}
    for mid, d in moves.items():
        if mid == 'MOVE_NONE':
            continue
        inv[mid] = {
            'name': d.get('name', mid),
            'power': d['power'],
            'type': resolve_enum(str(d.get('type', ''))).replace('TYPE_', ''),
            'category': resolve_enum(str(d.get('category', ''))).replace('DAMAGE_CATEGORY_', ''),
            'accuracy': d.get('accuracy'),
            'pp': d.get('pp'),
            'effect': str(d.get('effect', '')).replace('EFFECT_', ''),
            'generation': gen.get(mid),
            'breadth': breadth.get(mid, 0),
            'multiHit': bool(d.get('multiHit')),
        }

    still = [k for k, v in inv.items() if '?' in v['type'] or '?' in v['category']]
    if still:
        sys.exit(f'Unresolved type/category expressions, refusing to emit: {still}')

    machines = set(tms) | set(hms)
    pools = {}
    for region, g in REGIONS:
        entries = []
        for mid, v in inv.items():
            if v['generation'] != g or mid in machines:
                continue
            if v['power'] < SIGNATURE_MIN_POWER or v['breadth'] == 0:
                continue
            reasons = []
            if v['breadth'] == 1:
                reasons.append('single-species: the one learner already gets it, '
                               'so a tutor adds nothing')
            if mid in already:
                reasons.append('already taught outside Tier 2, so it is neither '
                               'origin-locked nor late')
            entries.append({'id': mid, **{k: v[k] for k in
                            ('name', 'power', 'type', 'category', 'breadth')},
                            'excluded_because': reasons})
        entries.sort(key=lambda e: (-e['power'], -e['breadth']))
        pools[region] = {
            'candidates': entries,
            'teachable': sum(1 for e in entries if not e['excluded_because']),
        }

    payload = {
        'generated_by': 'tools/gba/move_inventory.py',
        'method': 'arm-none-eabi-cpp with the Makefile CPPFLAGS, then exact '
                  'evaluation of the resolved numeric expressions',
        'upstream_commit': LOCK['upstream_commit'],
        'counts': {'moves': len(inv), 'base_species': len(base),
                   'tms': len(tms), 'hms': len(hms)},
        'signature_pool_rule': {
            'power_at_least': SIGNATURE_MIN_POWER,
            'note': 'Table power only. It ranks nothing about conditional damage, '
                    'setup or utility; that classification is still owed.',
        },
        'signature_pools': pools,
        'moves': inv,
    }

    text = json.dumps(payload, indent=1, sort_keys=True) + '\n'
    if args.check:
        if not EVIDENCE.exists() or EVIDENCE.read_text() != text:
            sys.exit('gba/evidence/move-inventory.json is stale; rerun without --check.')
        print('move-inventory.json is current.')
        return
    EVIDENCE.write_text(text)
    print(f"{len(inv)} moves, {len(base)} base species, {len(tms)} TMs, {len(hms)} HMs")
    for region, _ in REGIONS:
        p = pools[region]
        print(f"  {region:7} {len(p['candidates']):>2} candidates, "
              f"{p['teachable']:>2} teachable")


if __name__ == '__main__':
    main()
