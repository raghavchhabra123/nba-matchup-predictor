"""Free, deterministic 'analyst take' generated from the engine's own numbers.

No LLM, no API key, no cost, and it can't hallucinate — every clause is derived
directly from the model output, so the words always match the math.
"""
from __future__ import annotations


def _tier(edge: float) -> str:
    if edge >= 0.80:
        return 'a heavy favorite'
    if edge >= 0.667:
        return 'a clear favorite'
    if edge >= 0.57:
        return 'a modest favorite'
    if edge >= 0.52:
        return 'a slight favorite'
    return 'a coin-flip pick'


def _join(items: list[str]) -> str:
    if not items:
        return ''
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f'{items[0]} and {items[1]}'
    return ', '.join(items[:-1]) + f', and {items[-1]}'


def build_summary(res: dict, home: str, away: str, name, *, home_court: bool,
                  home_rest: int, away_rest: int,
                  out_home: list, out_away: list, travel: dict | None = None,
                  simple: bool = False) -> str:
    """Return a short markdown paragraph describing the matchup.

    `name` maps abbreviation -> full team name.
    out_home/out_away are lists of (player_name, impact) tuples.
    """
    def poss(n):   # possessive that respects team names ending in s
        return n + ('’' if n.endswith('s') else '’s')

    p = res['prob_home']
    comp = res['components']
    H, A = name(home), name(away)
    Hn, An = H.split()[-1], A.split()[-1]          # nicknames (Thunder, Nuggets…)
    fav_home = p >= 0.5
    fav_n, dog_n = (Hn, An) if fav_home else (An, Hn)
    edge = max(p, 1 - p)
    tier = _tier(edge)

    # --- lead sentence (plain, no betting line — that's shown in the hero) ---
    if fav_home:
        lead = f'**{H}** host **{A}** and come out {tier}, winning **{p:.0%}** of the time.'
    else:
        lead = (f'**{A}** are the pick on the road over **{H}** — {tier}, '
                f'winning **{1-p:.0%}** of the time.')

    # --- collect factors, each tagged with the team (nickname) it favors ---
    factors = []
    if abs(comp['power']) >= 0.4:
        factors.append((Hn if comp['power'] > 0 else An, 'the stronger roster',
                        abs(comp['power'])))
    if home_court and comp['home_court'] >= 0.1:
        factors.append((Hn, 'home court', comp['home_court']))
    if abs(comp['rest']) >= 0.1:
        if home_rest == 1 and away_rest != 1:
            factors.append((An, f'{poss(Hn)} back-to-back', abs(comp['rest'])))
        elif away_rest == 1 and home_rest != 1:
            factors.append((Hn, f'{poss(An)} back-to-back', abs(comp['rest'])))
    if abs(comp['players']) >= 0.3:
        if comp['players'] > 0:   # away players out -> helps home
            who_out = _join([n for n, _ in out_away][:2]) or 'key players'
            factors.append((Hn, f'**{who_out}** sitting for {An}', abs(comp['players'])))
        else:                     # home players out -> helps away
            who_out = _join([n for n, _ in out_home][:2]) or 'key players'
            factors.append((An, f'**{who_out}** sitting for {Hn}', abs(comp['players'])))
    if travel and abs(comp.get('travel', 0)) >= 0.4:
        t = comp['travel']
        if travel.get('altitude_ft', 0) >= 4000:
            phrase = f'the {Hn} altitude'
        elif travel.get('tz_shift', 0) > 0:
            phrase = f'{poss(An)} trip east'
        else:
            phrase = f'{poss(An)} travel'
        factors.append((Hn if t > 0 else An, phrase, abs(t)))

    pro = [ph for team, ph, _ in sorted(factors, key=lambda f: -f[2]) if team == fav_n]
    con = [ph for team, ph, _ in sorted(factors, key=lambda f: -f[2]) if team == dog_n]

    body = ''
    if pro:
        body += f' {poss(fav_n)} edge is {_join(pro)}.'
    if con:
        opener = f'{dog_n} claw back with' if pro else f'{dog_n} get a lift from'
        body += f' {opener} {_join(con)}.'

    # --- neutral-court swing, always framed from the favorite's side ---
    ctx = ''
    if home_court and not simple:
        if abs(p - res['prob_neutral']) >= 0.03:
            fav_neutral = res['prob_neutral'] if fav_home else 1 - res['prob_neutral']
            ctx = f' On a neutral floor {fav_n} would be **{fav_neutral:.0%}**.'

    # --- caveat when close, in plain English ---
    caveat = ' Close enough that either side could take it.' if edge < 0.60 else ''

    return lead + body + ctx + caveat
