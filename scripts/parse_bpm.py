"""Parse Basketball-Reference 'Advanced' table text -> data/bpm_2026.csv.

BPM (Box Plus/Minus) is a published, RAPM-informed estimate of a player's
points-per-100-possessions impact above league average; VORP uses a -2.0
replacement level. We keep name, team, games, minutes, BPM, VORP.

Input: a text file with the advanced table (as fetched from
basketball-reference.com/leagues/NBA_2026_advanced.html). Multi-team players
appear as a 2TM total row followed by per-team splits; we keep the first
(total) row per player.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# BBRef team codes -> our abbreviations
TEAM_FIX = {'BRK': 'BKN', 'CHO': 'CHA', 'PHO': 'PHX'}

# record: rk name age team pos then 23 numeric cols; BPM=-2, VORP=-1 of numeric run
REC = re.compile(
    r'(?P<rk>\d+)\s+'
    r'(?P<name>[A-Za-zÀ-ž.\'\-]+(?:\s+[A-Za-zÀ-ž.\'\-]+)*?)\s+'
    r'(?P<age>\d{2})\s+'
    r'(?P<team>[A-Z]{2,3}|2TM|3TM|4TM)\s+'
    r'(?P<pos>PG|SG|SF|PF|C|G|F)\s+'
    r'(?P<nums>(?:-?\d+\.?\d*\s+){22}-?\d+\.?\d*)'
)


def main(txt_path):
    text = Path(txt_path).read_text()
    # focus on the table region
    if 'Rk Player' in text:
        text = text[text.index('Rk Player'):]
    rows = {}
    order = []
    for m in REC.finditer(text):
        name = m.group('name').strip()
        if name in rows:
            continue  # keep first (2TM total) occurrence
        nums = [float(x) for x in m.group('nums').split()]
        if len(nums) < 23:
            continue
        g, mp = nums[0], nums[2]
        bpm, vorp = nums[-2], nums[-1]
        team = m.group('team')
        team = TEAM_FIX.get(team, team)
        rows[name] = {'player': name, 'team': team, 'g': int(g),
                      'mp_total': mp, 'min_pg': round(mp / g, 1) if g else 0,
                      'bpm': bpm, 'vorp': vorp, 'pos': m.group('pos')}
        order.append(name)

    import csv
    out = ROOT / 'data' / 'bpm_2026.csv'
    with open(out, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['player', 'team', 'pos', 'g',
                                          'mp_total', 'min_pg', 'bpm', 'vorp'])
        w.writeheader()
        for n in order:
            w.writerow(rows[n])
    print(f'parsed {len(order)} players -> {out}')
    top = sorted(rows.values(), key=lambda r: -r['bpm'])[:10]
    for r in top:
        print(f"  {r['player']:26s} {r['team']:4s} BPM {r['bpm']:+5.1f}  "
              f"{r['min_pg']:.0f} min")


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else '/tmp/bbref_adv.txt')
