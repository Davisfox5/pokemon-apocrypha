"""Master inventory of every HGSS map, with per-map port status (gate G0 of docs/MAP_CHECKLIST.md).

    python3 tools/gba/maps/inventory/build_inventory.py PHG_CHECKOUT            # regenerate
    python3 tools/gba/maps/inventory/build_inventory.py PHG_CHECKOUT --check    # validate only
    python3 tools/gba/maps/inventory/build_inventory.py PHG_CHECKOUT --check --engine ENGINE_CHECKOUT

Columns: `pr` and `branch` are the game-source PR/branch on Davisfox5/pokeemerald-expansion;
`hub_pr` is the matching docs/tools/evidence PR on Davisfox5/pokemon-apocrypha.

Rows come from pokeheartgold's own map table (include/constants/maps.h + src/data/map_headers.h).
Unused, Japanese-only, debug and Wi-Fi placeholder entries are dropped. Regenerating keeps every
hand-edited column (gba_map, status, pr, hub_pr, branch, accepted, notes, scope) by HGSS constant, so the
CSV can be edited by hand and regenerated safely.

--check fails on: an unknown status; a map with more than one open PR or branch; a row past
"sourcing plan" with no gba_map; a "merged" row whose gba_map is missing from ENGINE_CHECKOUT
(when given); an HGSS map missing from the CSV.
"""
from __future__ import annotations
import csv, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / 'docs/maps/HGSS_MAP_INVENTORY.csv'

STATUSES = ['not started', 'sourcing plan', 'building', 'in review', 'accepted', 'merged']
COLUMNS = ['hgss_id', 'hgss_const', 'hgss_code', 'region', 'mapsec', 'type', 'kit', 'scope', 'batch',
           'gba_map', 'status', 'pr', 'hub_pr', 'branch', 'accepted', 'notes']
KEEP = ['scope', 'gba_map', 'status', 'pr', 'hub_pr', 'branch', 'accepted', 'notes']

SKIP = re.compile(r'UNUSED|FIGHT_AREA|_JP$|^MAP_EVERYWHERE$|^MAP_NOTHING$|WIFI|^MAP_UNION$|^MAP_UNDERGROUND$|BATTLE_PARK')

# Batches: finish and merge one area at a time so neighbours share tilesets and seams are checked once.
BATCHES = {
    'A New Bark-Violet': 'NEW_BARK_TOWN ROUTE_29 CHERRYGROVE_CITY ROUTE_30 ROUTE_31 DARK_CAVE VIOLET_CITY SPROUT_TOWER ROUTE_46',
    'B Route 32-Azalea': 'ROUTE_32 RUINS_OF_ALPH UNION_CAVE ROUTE_33 AZALEA_TOWN SLOWPOKE_WELL ILEX_FOREST',
    'C Route 34-Goldenrod': 'ROUTE_34 GOLDENROD_CITY GOLDENROD_TUNNEL RADIO_TOWER GLOBAL_TERMINAL',
    'D Route 35-Ecruteak': 'ROUTE_35 NATIONAL_PARK ROUTE_36 ROUTE_37 ECRUTEAK_CITY BURNED_TOWER BELL_TOWER BELLCHIME_TRAIL',
    'E Route 38-Cianwood': 'ROUTE_38 ROUTE_39 OLIVINE_CITY LIGHTHOUSE SS_AQUA ROUTE_40 ROUTE_41 WHIRL_ISLANDS CIANWOOD_CITY ROUTE_47 ROUTE_48 CLIFF_EDGE_GATE CLIFF_CAVE EMBEDDED_TOWER',
    'F Route 42-Blackthorn': 'ROUTE_42 MT_MORTAR MAHOGANY_TOWN ROUTE_43 LAKE_OF_RAGE TEAM_ROCKET_HQ ROUTE_44 ICE_PATH BLACKTHORN_CITY DRAGONS_DEN ROUTE_45',
    'G League and Mt. Silver': 'ROUTE_27 ROUTE_26 TOHJO_FALLS VICTORY_ROAD_JK POKEMON_LEAGUE INDIGO_PLATEAU ROUTE_28 MT_SILVER MT_SILVER_CAVE SINJOH_RUINS',
    'K1 Pallet-Mt. Moon': 'PALLET_TOWN ROUTE_1 VIRIDIAN_CITY ROUTE_2 ROUTE_22 VIRIDIAN_FOREST PEWTER_CITY ROUTE_3 MT_MOON ROUTE_4',
    'K2 Cerulean-Lavender': 'CERULEAN_CITY ROUTE_24 ROUTE_25 CERULEAN_CAVE ROUTE_9 ROUTE_10 ROCK_TUNNEL POWER_PLANT LAVENDER_TOWN ROUTE_8',
    'K3 Saffron-Celadon': 'SAFFRON_CITY ROUTE_5 ROUTE_6 ROUTE_7 VERMILION_CITY ROUTE_11 DIGLETTS_CAVE CELADON_CITY ROUTE_16 ROUTE_17 ROUTE_18 ROTOMS_ROOM',
    'K4 Fuchsia-Cinnabar': 'FUCHSIA_CITY ROUTE_12 ROUTE_13 ROUTE_14 ROUTE_15 ROUTE_19 ROUTE_20 SEAFOAM_ISLANDS CINNABAR_ISLAND ROUTE_21',
    'X Optional facilities': 'BATTLE_FRONTIER BATTLE_TOWER BATTLE_FACTORY BATTLE_HALL BATTLE_CASTLE BATTLE_ARCADE FRONTIER_ACCESS POKEATHLON_DOME SAFARI_ZONE SAFARI_ZONE_GATE PAL_PARK',
}
BATCH_OF = {sec: b for b, secs in BATCHES.items() for sec in secs.split()}
OPTIONAL = {sec for sec in BATCHES['X Optional facilities'].split()}

def kit(const, region):
    """Shared-kit family a map instantiates. Each region has its own kit (owner, 2026-11-20): Johto's
    Center, Mart, houses and gates differ from Kanto's. Built once per region, then placed per town."""
    for k, pat in (('gatehouse', r'GATEHOUSE|_GATE$|RECEPTION_GATE'), ('center', r'POKECENTER'), ('mart', r'POKEMART'),
                   ('gym', r'_GYM'), ('house', r'HOUSE')):
        if re.search(pat, const):
            return f'{region.lower()}-{k}'
    return ''

def hgss_maps(phg: Path):
    codes = {m.group(1): (int(m.group(2)), m.group(3)) for m in re.finditer(
        r'#define (MAP_\w+)\s+(\d+)\s*//\s*(\S+)', (phg / 'include/constants/maps.h').read_text())}
    src = (phg / 'src/data/map_headers.h').read_text()
    for m in re.finditer(r'\[(MAP_\w+)\]\s*=\s*\{(.*?)\n\s*\},', src, re.S):
        const, body = m.groups()
        if SKIP.search(const):
            continue
        g = lambda k: (re.search(r'\.' + k + r'\s*=\s*(\w+)', body) or [None, ''])[1]
        sec = g('mapsec').replace('MAPSEC_', '')
        typ = g('mapType').replace('MAP_TYPE_', '').lower()
        hid, code = codes.get(const, ('', ''))
        b8 = 'B1F' in const and 'POKECENTER' in const        # HGSS Wi-Fi basement of every Center
        yield dict(hgss_id=hid, hgss_const=const, hgss_code=code, region=g('regionNo').replace('MAP_REGION_', '').title(),
                   mapsec=sec, type=typ, kit=kit(const, g('regionNo').replace('MAP_REGION_', '')),
                   scope='optional' if sec in OPTIONAL or b8 else 'core',
                   batch=BATCH_OF.get(sec, '?'), status='not started')

def read(path=OUT):
    if not path.exists():
        return {}
    with path.open(newline='') as f:
        return {r['hgss_const']: r for r in csv.DictReader(f)}

def build(phg):
    old = read()
    rows = []
    for r in hgss_maps(phg):
        prev = old.get(r['hgss_const'], {})
        for k in KEEP:
            if prev.get(k):
                r[k] = prev[k]
        rows.append({c: r.get(c, '') for c in COLUMNS})
    rows.sort(key=lambda r: (r['batch'], r['mapsec'], int(r['hgss_id'] or 0)))
    with OUT.open('w', newline='') as f:
        w = csv.DictWriter(f, COLUMNS, lineterminator='\n'); w.writeheader(); w.writerows(rows)
    return rows

def check(phg, engine=None):
    rows = read()
    errs = []
    want = {r['hgss_const'] for r in hgss_maps(phg)}
    for c in sorted(want - rows.keys()):
        errs.append(f'{c}: in HGSS but missing from the inventory (regenerate)')
    for c, r in rows.items():
        if r['status'] not in STATUSES:
            errs.append(f'{c}: unknown status {r["status"]!r} (use one of {STATUSES})')
        if r['batch'] == '?':
            errs.append(f'{c}: no batch for mapsec {r["mapsec"]}')
        if len(r.get('hub_pr', '').split()) > 1:
            errs.append(f'{c}: more than one open pokemon-apocrypha PR ({r["hub_pr"]})')
        if len([p for p in r['pr'].split() if p]) > 1 or len([b for b in r['branch'].split() if b]) > 1:
            errs.append(f'{c}: more than one open PR/branch ({r["pr"]} {r["branch"]}); pick one and close the rest')
        if STATUSES.index(r['status']) >= STATUSES.index('building') if r['status'] in STATUSES else False:
            if not r['gba_map']:
                errs.append(f'{c}: status {r["status"]} but no gba_map')
        if engine and r['status'] == 'merged' and r['gba_map'] and not (engine / 'data/maps' / r['gba_map']).is_dir():
            errs.append(f'{c}: merged but {r["gba_map"]} is not in {engine}')
    gba = {}
    for c, r in rows.items():
        for g in r['gba_map'].split():
            gba.setdefault(g, []).append(c)
    for g, cs in gba.items():
        if len(cs) > 1:
            errs.append(f'{g}: claimed by more than one HGSS map ({" ".join(cs)})')
    return rows, errs

def summary(rows):
    from collections import Counter
    core = [r for r in rows.values()] if isinstance(rows, dict) else rows
    by = Counter((r['batch'], r['status']) for r in core if r['scope'] == 'core')
    batches = sorted({r['batch'] for r in core})
    print(f"{'batch':26}" + ''.join(f'{s:>14}' for s in STATUSES))
    for b in batches:
        print(f'{b:26}' + ''.join(f'{by[(b, s)]:>14}' for s in STATUSES))
    print(f"core maps: {sum(1 for r in core if r['scope'] == 'core')}, optional: {sum(1 for r in core if r['scope'] != 'core')}")

def main(argv):
    phg = Path(argv[1]).resolve()
    engine = Path(argv[argv.index('--engine') + 1]).resolve() if '--engine' in argv else None
    if '--check' not in argv:
        build(phg)
    rows, errs = check(phg, engine)
    summary(rows)
    for e in errs:
        print('FAIL', e)
    print('inventory clean' if not errs else f'{len(errs)} problem(s)')
    return 0 if not errs else 1

if __name__ == '__main__':
    sys.exit(main(sys.argv))
