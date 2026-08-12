"""NBA Matchup Win-Probability Dashboard — point-spread engine (Tier 1).

Predicts an expected margin from Elo power ratings, then adds home court,
rest, and player availability as point adjustments before converting once to a
win probability. Run:  streamlit run app.py
"""
import json
import os
import re
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

from src.chat import ask as chat_ask
from src.engine import SpreadEngine
from src.injuries import by_team, load_injuries, norm_name
from src.knowledge import load_kb
from src.lineups import home_player_points, team_delta
from src.summary import build_summary
from src.travel import compute_travel

ROOT = Path(__file__).resolve().parent
DATA, LIVE = ROOT / 'data', ROOT / 'data' / 'live'
HOME_C, AWAY_C = '#e8590c', '#1971c2'

st.set_page_config(page_title='NBA Matchup Predictor', page_icon='🏀', layout='wide')

st.markdown("""
<style>
/* force a consistent dark theme regardless of the user's system setting */
.stApp {background-color:#0e1117;}
section[data-testid="stSidebar"] {background-color:#141922;}
.stApp, .stApp p, .stApp li, .stApp label, .stApp span {color:#e6e9ef;}
[data-testid="stCaptionContainer"], .stCaption {color:#9aa6b6 !important;}
.block-container {padding-top: 2rem; max-width: 1180px;}
#MainMenu, footer {visibility: hidden;}
/* bigger, friendlier buttons */
.stButton>button {border-radius:12px; padding:.6rem 1rem; font-weight:600;
                  font-size:1rem; border:1px solid #2f3846;}
.stButton>button:hover {border-color:#e8590c;}
/* bigger picker labels */
label p {font-size:1rem !important; font-weight:600 !important;}
.card {background:#151a23; border:1px solid #262d3a; border-radius:16px;
       padding:18px 22px; height:100%;}
.teamstrip {display:flex; align-items:center; gap:10px; margin-top:8px;}
.teamstrip img {width:34px; height:34px; object-fit:contain;}
.teamstrip .tsub {color:#aeb8c6; font-size:.95rem; font-weight:600;}
.hero {background:linear-gradient(180deg,#171d27,#12161e); border:1px solid #2a3342;
       border-radius:22px; padding:30px 34px; box-shadow:0 8px 30px rgba(0,0,0,.25);}
.pctrow {display:flex; justify-content:space-between; align-items:center; gap:10px;}
.heroteam {display:flex; align-items:center; gap:14px; min-width:0;}
.heroteam img {width:52px; height:52px; object-fit:contain; flex-shrink:0;}
.heromid {text-align:center; margin:14px 0 4px;}
.pct {font-size:3.8rem; font-weight:800; line-height:.95; letter-spacing:-1px;}
.plabel {font-size:.95rem; color:#93a0b4; font-weight:600;}
/* --- mobile: shrink so nothing overlaps on a phone --- */
@media (max-width:640px){
  .hero {padding:18px 16px; border-radius:16px;}
  .pct {font-size:2.4rem;}
  .heroteam {gap:8px;}
  .heroteam img {width:34px; height:34px;}
  .plabel {font-size:.72rem;}
  .verdict {font-size:1.05rem;}
  .spreadpill {font-size:.95rem; padding:5px 14px;}
  .teamstrip img {width:26px; height:26px;}
  .teamstrip .tsub {font-size:.8rem;}
}
.probbar {height:34px; border-radius:17px; overflow:hidden; display:flex; margin:20px 0 10px;
          box-shadow:inset 0 0 0 1px rgba(255,255,255,.05);}
.verdict {font-size:1.35rem; font-weight:700; margin-top:8px; color:#eef2f7;}
.spreadpill {display:inline-block; background:#e8590c; color:#fff;
             border-radius:22px; padding:7px 18px; font-weight:700; font-size:1.05rem;
             box-shadow:0 2px 10px rgba(232,89,12,.35);}
.upsetbadge {display:inline-block; background:#3a2a12; border:1px solid #e8850c;
             color:#ffb454; border-radius:20px; padding:3px 12px; font-weight:700;
             font-size:.85rem; margin-bottom:6px;}
.starrow {display:flex; align-items:center; justify-content:center; gap:10px;
          margin:12px 0 2px; color:#c9d1dc; font-weight:600;}
.starrow img {width:44px; height:44px; border-radius:50%; object-fit:cover;
              background:#222a38; border:2px solid #2f3846;}
.starrow .vs {color:#8b95a5; font-weight:700; margin:0 6px;}
.takecard {background:#151a23; border:1px solid #262d3a; border-left:4px solid #e8590c;
           border-radius:14px; padding:18px 22px;}
.takelbl {font-size:.82rem; color:#93a0b4; text-transform:uppercase;
          letter-spacing:.06em; margin-bottom:8px; font-weight:700;}
.taketxt {font-size:1.12rem; line-height:1.6; color:#dde3ec;}
.wf-row {display:flex; align-items:center; gap:14px; margin:12px 0;}
.wf-lab {width:190px; font-size:1rem; color:#cdd5e0; flex-shrink:0;}
.wf-track {flex:1; position:relative; height:32px; background:#0e1219;
           border-radius:7px; overflow:hidden;}
.wf-mid {position:absolute; left:50%; top:0; bottom:0; width:1px; background:#3a4353;}
.wf-fill {position:absolute; top:5px; height:22px; border-radius:5px;}
.wf-val {width:60px; text-align:right; font-variant-numeric:tabular-nums;
         font-weight:700; font-size:1.05rem; flex-shrink:0;}
.wf-total .wf-lab {font-weight:800; color:#fff; font-size:1.05rem;}
.wf-total .wf-val {font-size:1.15rem;}
.wf-total .wf-track {background:#141a24; height:36px;}
.stTabs [data-baseweb="tab"] {font-size:1.05rem; font-weight:600;}
</style>
""", unsafe_allow_html=True)


# ------------------------------------------------------------------ loading
@st.cache_resource
def load_engine():
    return SpreadEngine()


@st.cache_resource
def get_kb():
    return load_kb()


@st.cache_data
def load_meta():
    m = ROOT / 'models' / 'metrics_tier1.json'
    return json.loads(m.read_text()) if m.exists() else None


@st.cache_data
def load_data(live_stamp: str):
    teams = pd.read_csv(DATA / 'teams.csv')
    snap = pd.read_csv(DATA / 'team_snapshot_2026.csv')
    proj = DATA / 'players_2027.csv'          # current rosters (post-offseason)
    live_players = LIVE / 'players.csv'
    if live_players.exists() and 'bpm' in pd.read_csv(live_players, nrows=1).columns:
        players = pd.read_csv(live_players)
        season_lbl, fetched, _ = (LIVE / 'meta.txt').read_text().split('|')
        source = f'Live · {season_lbl}'
    elif proj.exists():
        players = pd.read_csv(proj)
        source = '2026-27 (projected rosters)'
    else:
        players = pd.read_csv(DATA / 'players_2026.csv')
        source = '2025-26 (final)'
    return teams, snap, players, source


def live_stamp():
    m = LIVE / 'meta.txt'
    return m.read_text() if m.exists() else 'none'


eng = load_engine()
meta = load_meta()
teams, snap, players, source = load_data(live_stamp())
abbr2name = dict(zip(teams.abbr, teams.name))
abbr2logo = dict(zip(teams.abbr, teams.logo))
snap_by_team = {r.team: r for r in snap.itertuples()}

# injury report: map team names (and nicknames) -> abbr, then group by team
name2abbr = dict(zip(teams.name, teams.abbr))
for nm, ab in list(name2abbr.items()):
    name2abbr[nm.split()[-1]] = ab           # nickname fallback (e.g. "Lakers")
    name2abbr[nm.replace('Los Angeles', 'LA')] = ab
injury_report = load_injuries()
injuries = by_team(injury_report, name2abbr) if injury_report else {}
BUCKET_ICON = {'out': '🔴', 'gtd': '🟡', 'probable': '🟢'}


def injury_of(abbr, name):
    return injuries.get(abbr, {}).get(norm_name(name))


def plays_by_default(abbr, name):
    inj = injury_of(abbr, name)
    return not (inj and inj['bucket'] == 'out')


# ------------------------------------------------------------------ helpers
def verdict_text(p: float, home: str, away: str) -> str:
    fav = home if p >= 0.5 else away
    edge = max(p, 1 - p)
    if edge >= 0.80:
        tier = 'a heavy favorite'
    elif edge >= 0.667:
        tier = 'a clear favorite'
    elif edge >= 0.57:
        tier = 'a modest favorite'
    elif edge >= 0.52:
        tier = 'a slight favorite'
    else:
        return "Too close to call — essentially a coin flip."
    return f'{abbr2name.get(fav, fav)} is {tier}, winning about {edge:.0%} of the time.'


def team_card_html(abbr: str, align: str = 'left', level: int = 1) -> str:
    strength = eng.team_strength(abbr)
    tier = ('title contender' if strength >= 6 else 'solid' if strength >= 2
            else 'middle of the pack' if strength >= -2
            else 'rebuilding' if strength >= -6 else 'lottery-bound')
    if level >= 1:
        sub = f'proj power {strength:+.1f} · {tier}'
    else:
        sub = tier
    logo = abbr2logo.get(abbr, '')
    img = f'<img src="{logo}">' if isinstance(logo, str) and logo.startswith('http') else ''
    span = f'<span class="tsub">{sub}</span>'
    inner = f'{img}{span}' if align == 'left' else f'{span}{img}'
    justify = 'flex-start' if align == 'left' else 'flex-end'
    return f'<div class="teamstrip" style="justify-content:{justify}">{inner}</div>'


def waterfall_html(comp: dict, margin: float) -> str:
    rows = [
        ('Team strength', comp['power'], 'Elo power-rating gap'),
        ('Home court', comp['home_court'], 'worth ~2.5 pts to any host'),
        ('Rest', comp['rest'], 'back-to-back fatigue'),
        ('Players out', comp['players'], 'impact of who is sitting'),
        ('Travel & altitude', comp.get('travel', 0.0), 'trip + Denver/Utah air'),
    ]
    scale = max(8.0, max(abs(v) for _, v, _ in rows + [('', margin, '')]))
    html = ''
    for lab, val, _ in rows:
        w = abs(val) / scale * 50
        if val >= 0:
            fill = f'left:50%; width:{w:.1f}%; background:{HOME_C};'
        else:
            fill = f'right:50%; width:{w:.1f}%; background:{AWAY_C};'
        html += (f'<div class="wf-row"><div class="wf-lab">{lab}</div>'
                 f'<div class="wf-track"><div class="wf-mid"></div>'
                 f'<div class="wf-fill" style="{fill}"></div></div>'
                 f'<div class="wf-val">{val:+.1f}</div></div>')
    w = abs(margin) / scale * 50
    side = (f'left:50%; width:{w:.1f}%; background:{HOME_C};' if margin >= 0
            else f'right:50%; width:{w:.1f}%; background:{AWAY_C};')
    html += (f'<div class="wf-row wf-total"><div class="wf-lab">Expected margin</div>'
             f'<div class="wf-track"><div class="wf-mid"></div>'
             f'<div class="wf-fill" style="{side}"></div></div>'
             f'<div class="wf-val">{margin:+.1f}</div></div>')
    return html


# ------------------------------------------------------------------ sidebar
LEVELS = {'🙂 Casual': 0, '🏀 Fan': 1, '🔬 Analyst': 2}
with st.sidebar:
    st.markdown('### 🎚️ View')
    try:
        choice = st.segmented_control('detail', list(LEVELS), default='🏀 Fan',
                                      key='view_level', label_visibility='collapsed')
    except Exception:
        choice = st.radio('detail', list(LEVELS), index=1, key='view_level',
                          label_visibility='collapsed')
    level = LEVELS.get(choice, 1)
    st.caption({0: 'Just the pick and why, in plain English.',
                1: 'Add game conditions, injuries, and the point breakdown.',
                2: 'Everything — ratings, calibration, and the math.'}[level])

    # defaults (used directly at Casual, adjustable at Fan/Analyst)
    hca, home_rest, away_rest, use_travel = True, 2, 2, True
    rest_opts = {'Rested': 2, 'Back-to-back': 1}

    if level >= 1:
        st.divider()
        st.markdown('**🏟️ Game conditions**')
        hca = st.toggle('Home court', value=True,
                        help='On adds the home team’s edge (~2.5 pts). Off = neutral floor.')
        home_rest = rest_opts[st.radio('🏠 Home rest', list(rest_opts),
                                       horizontal=True, key='hr')]
        away_rest = rest_opts[st.radio('✈️ Away rest', list(rest_opts),
                                       horizontal=True, key='ar')]
        use_travel = st.toggle('✈️ Travel & altitude', value=True,
                               help='Visitor flies in from their city. Adds Denver/Utah '
                                    'altitude and long eastward-trip fatigue.')

    st.divider()
    st.markdown('**🔌 Live data**')
    st.caption(f'Source: {source}')
    if st.button('🩹 Load injury report', use_container_width=True):
        try:
            from src.injuries import fetch_injuries
            with st.spinner('Fetching injuries from ESPN…'):
                rep = fetch_injuries()
            for k in [k for k in st.session_state if k[:2] in ('h_', 'a_')]:
                del st.session_state[k]
            st.success(f"Loaded · {rep['count']} listed")
            st.rerun()
        except Exception as e:
            st.warning(f'Injury fetch failed ({type(e).__name__}).')
    if injury_report:
        st.caption(f"🩹 {injury_report['count']} players listed · "
                   f"{injury_report['fetched'][:16].replace('T', ' ')}")
    if level >= 2:
        if st.button('🔄 Refresh team stats (nba_api)', use_container_width=True):
            try:
                from src.live import refresh
                with st.spinner('Fetching from NBA.com…'):
                    info = refresh()
                st.success(f"Updated · {info['games']} games")
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.warning(f'Live fetch failed ({type(e).__name__}).')

    if level >= 2:
        st.divider()
        with st.expander('⚙️ Model coefficients', expanded=False):
            st.caption(f'Home court **+{eng.hca:.1f} pts**  \n'
                       f'**{eng.b_elo*100:.1f} pts** per 100 Elo  \n'
                       f'Back-to-back **{eng.home_b2b:+.1f} pts**  \n'
                       f'Margin noise σ **{eng.sigma:.1f} pts**')

# ------------------------------------------------------------------ header
st.markdown("<h1 style='font-size:2.4rem; margin-bottom:2px'>🏀 NBA Matchup Predictor</h1>",
            unsafe_allow_html=True)
st.caption('Who wins, by how much, and exactly why — built the way the betting market builds a number.')

opts = sorted(eng.teams(), key=lambda a: abbr2name.get(a, a))
c1, cmid, c2 = st.columns([6, 1, 6])
with c1:
    home_team = st.selectbox('🏠 Home', opts,
                             index=opts.index('OKC') if 'OKC' in opts else 0,
                             format_func=lambda a: abbr2name.get(a, a))
    st.markdown(team_card_html(home_team, 'left', level), unsafe_allow_html=True)
with cmid:
    st.markdown("<div style='text-align:center;font-size:1.4rem;padding-top:2.1rem;"
                "color:#8b95a5'>vs</div>", unsafe_allow_html=True)
with c2:
    away_opts = [t for t in opts if t != home_team]
    away_team = st.selectbox('✈️ Away', away_opts,
                             index=away_opts.index('DEN') if 'DEN' in away_opts else 0,
                             format_func=lambda a: abbr2name.get(a, a))
    st.markdown(team_card_html(away_team, 'right', level), unsafe_allow_html=True)

# ------------------------------------------------------------------ players state
def roster_out(abbr, key):
    roster = players[players.team == abbr].sort_values('min_pg', ascending=False).head(12)
    out = []
    for r in roster.itertuples():
        default = plays_by_default(abbr, r.athlete_display_name)
        if not st.session_state.get(f'{key}_{r.athlete_id}', default):
            out.append((r.athlete_display_name, r.bpm))
    return out


out_home = roster_out(home_team, 'h')
out_away = roster_out(away_team, 'a')
home_roster = players[players.team == home_team]
away_roster = players[players.team == away_team]
player_points = home_player_points(
    home_roster, away_roster,
    [n for n, _ in out_home], [n for n, _ in out_away])

travel = compute_travel(home_team, away_team)
travel_points = travel['points'] if use_travel else 0.0
res = eng.predict(home_team, away_team, home_court=hca,
                  home_rest=home_rest, away_rest=away_rest,
                  player_points=player_points, travel_points=travel_points)
p = res['prob_home']
comp = res['components']

# ------------------------------------------------------------------ hero
st.write('')
hp, ap = p, 1 - p


def hero_logo(abbr):
    lg = abbr2logo.get(abbr, '')
    return f'<img src="{lg}">' if isinstance(lg, str) and lg.startswith('http') else ''


def top_player(abbr):
    r = players[players.team == abbr].sort_values('bpm', ascending=False)
    if r.empty:
        return None
    row = r.iloc[0]
    return row.athlete_display_name, str(row.get('headshot', '') or '')


upset = ('<div class="upsetbadge">🔥 Coin-flip — upset watch</div>'
         if abs(p - 0.5) <= 0.055 else '')
mid = (f'{upset}<br><span class="spreadpill">{res["spread_str"]}</span>'
       f'<span class="plabel" style="margin-left:10px">exp. margin {res["margin"]:+.1f}</span>'
       ) if level >= 1 else f'{upset}<span class="plabel">win probability</span>'
st.markdown(f"""
<div class="hero">
  <div class="pctrow">
    <div class="heroteam">{hero_logo(home_team)}
      <div><div class="plabel">🏠 {home_team}</div>
        <div class="pct" style="color:{HOME_C}">{hp:.0%}</div></div>
    </div>
    <div class="heroteam" style="flex-direction:row-reverse">{hero_logo(away_team)}
      <div style="text-align:right"><div class="plabel">{away_team} ✈️</div>
        <div class="pct" style="color:{AWAY_C}">{ap:.0%}</div></div>
    </div>
  </div>
  <div class="heromid">{mid}</div>
  <div class="probbar">
    <div style="width:{hp*100:.1f}%; background:{HOME_C}"></div>
    <div style="width:{ap*100:.1f}%; background:{AWAY_C}"></div>
  </div>
  <div class="verdict">{verdict_text(p, home_team, away_team)}</div>
</div>
""", unsafe_allow_html=True)

# star matchup strip (top player each side)
_hs, _as = top_player(home_team), top_player(away_team)
if _hs and _as:
    def _star(sp, color):
        img = (f'<img src="{sp[1]}">' if sp[1].startswith('http') else '')
        return f'{img}<span style="color:{color}">{sp[0]}</span>'
    st.markdown(
        f'<div class="starrow">{_star(_hs, HOME_C)}<span class="vs">vs</span>'
        f'{_star(_as, AWAY_C)}</div>', unsafe_allow_html=True)

# ------------------------------------------------------------------ the take
take = build_summary(res, home_team, away_team, lambda a: abbr2name.get(a, a),
                     home_court=hca, home_rest=home_rest, away_rest=away_rest,
                     out_home=out_home, out_away=out_away,
                     travel=travel if use_travel else None, simple=(level == 0))
take_html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', take)
st.write('')
st.markdown(
    f"<div class='takecard'><div class='takelbl'>📝 The take</div>"
    f"<div class='taketxt'>{take_html}</div></div>",
    unsafe_allow_html=True)

# facts injected into the chatbot so it answers from real numbers only
HN, AN = abbr2name.get(home_team), abbr2name.get(away_team)
_facts = f"""Season: 2026-27 (projected rosters after the 2026 offseason).
Matchup: {HN} at home vs {AN} away.
{HN} projected power: {eng.team_strength(home_team):+.1f} pts vs an average team.
{AN} projected power: {eng.team_strength(away_team):+.1f} pts.
Prediction: {HN} win probability {p:.0%}, {AN} {1-p:.0%}. Model line {res['spread_str']}, expected margin {res['margin']:+.1f} for the home team.
Point breakdown (+ favors {HN}): team strength {comp['power']:+.1f}, home court {comp['home_court']:+.1f}, rest {comp['rest']:+.1f}, players sitting {comp['players']:+.1f}, travel/altitude {comp.get('travel', 0):+.1f}.
Sitting out: {', '.join(n for n, _ in out_home) or 'nobody'} for {HN}; {', '.join(n for n, _ in out_away) or 'nobody'} for {AN}.
How the model works: win probability = normal CDF of (expected margin / {eng.sigma:.1f}). Home court is worth +{eng.hca:.1f} pts. A back-to-back costs ~2 pts. Team strength is {eng.b_elo*100:.1f} pts per 100 Elo. Denver and Utah get an altitude bonus (+2.2 / +1.2). Player value = BPM (points per 100 possessions above average); a star is worth ~4-6 pts and their minutes redistribute to the bench, so depth matters. 2026-27 team ratings blend current-roster BPM with regressed Elo. On a 2024-26 holdout the engine hit 68% accuracy, matching the Vegas/FiveThirtyEight ceiling. Plain summary: {re.sub(r'[*]', '', take)}"""

# ------------------------------------------------------------------ tabs
def roster_ui(col, abbr, key, out_list, lvl):
    roster = (players[players.team == abbr]
              .sort_values('min_pg', ascending=False).head(12))
    d = team_delta(players[players.team == abbr], [n for n, _ in out_list])
    with col:
        hit = f'  ·  lineup {d:+.1f} pts' if out_list else ''
        st.markdown(f'**{abbr2name.get(abbr, abbr)}**{hit}')
        for r in roster.itertuples():
            inj = injury_of(abbr, r.athlete_display_name)
            badge = f'  ·  {BUCKET_ICON[inj["bucket"]]} {inj["status"]}' if inj else ''
            stat = (f'BPM {r.bpm:+.1f}' if lvl >= 2 else f'{r.pts_pg:.0f} ppg')
            st.checkbox(
                f'{r.athlete_display_name}  ·  {stat}{badge}',
                value=st.session_state.get(
                    f'{key}_{r.athlete_id}',
                    plays_by_default(abbr, r.athlete_display_name)),
                key=f'{key}_{r.athlete_id}',
                help=f'{r.min_pg:.0f} min, {r.pts_pg:.1f} pts per game'
                     + (f' · {inj["detail"]}' if inj and inj['detail'] else ''))


def render_why():
    left, right = st.columns([3, 2])
    with left:
        st.markdown(waterfall_html(comp, res['margin']), unsafe_allow_html=True)
    with right:
        st.markdown(
            f"<span style='color:{HOME_C};font-weight:700'>● {home_team}</span> &nbsp; "
            f"<span style='color:{AWAY_C};font-weight:700'>● {away_team}</span>"
            "<br><span style='color:#9aa6b6'>Each bar is points; they add to the margin.</span>",
            unsafe_allow_html=True)
        st.write('')
        d1, d2 = st.columns(2)
        d1.metric('If neutral court', f"{res['prob_neutral']:.0%}")
        d2.metric('If home court', f"{res['prob_with_hca']:.0%}")
        if use_travel and travel['points'] != 0:
            bits = [f"{travel['distance']:,} mi"]
            if travel['tz_shift']:
                bits.append(f"{abs(travel['tz_shift'])}h {'east' if travel['tz_shift'] > 0 else 'west'}")
            if travel['altitude_ft'] >= 4000:
                bits.append(f"{travel['altitude_ft']:,} ft")
            st.caption('✈️ ' + ' · '.join(bits))


def render_players(lvl):
    cap = ('Uncheck anyone sitting out. Their minutes flow to the bench, so '
           '**depth matters** — a deep team barely feels a star resting.')
    if lvl >= 2:
        cap = ('Value = **BPM** (points per 100 above average, Basketball-Reference). '
               + cap)
    if injuries:
        cap += '  \n🩹 **Injuries loaded** — Out players are pre-unchecked.'
    else:
        cap += '  \nTip: **Load injury report** (sidebar) to auto-sit injured players.'
    st.caption(cap)
    pc1, pc2 = st.columns(2)
    roster_ui(pc1, home_team, 'h', out_home, lvl)
    roster_ui(pc2, away_team, 'a', out_away, lvl)
    if out_home or out_away:
        st.info(f'With those absences, the home team’s expected margin shifts '
                f'**{player_points:+.1f} pts** (bench quality already factored in).')


def render_quality():
    if meta:
        m = meta['metrics']
        best = m.get('Spread engine (Elo+HCA+rest)', {})
        st.markdown('**Graded on 2,462 games from 2024-26 the model never saw '
                    'during training.**')
        k1, k2, k3 = st.columns(3)
        k1.metric('Accuracy', f"{best.get('accuracy', 0):.1%}",
                  help='Share of games where the favorite won.')
        k2.metric('Always-home → us', '55% → 68%',
                  help='Simplest baseline — always pick the home team — already wins ~55% '
                       'because of home-court advantage (not 50%). Our engine reaches 68%.')
        k3.metric('Calibration', 'On target',
                  help='When it says 65%, home teams really win ~63%.')
        st.caption('~68% is the realistic ceiling — Vegas and FiveThirtyEight land there '
                   'too. Single games are just noisy.')

        rel = pd.DataFrame(meta.get('reliability_spread_engine', []))
        if not rel.empty:
            try:
                import altair as alt
                diag = alt.Chart(pd.DataFrame({'x': [0, 1], 'y': [0, 1]})).mark_line(
                    strokeDash=[6, 4], color='#5c6672').encode(x='x', y='y')
                pts = alt.Chart(rel).mark_circle(size=110, color=HOME_C).encode(
                    x=alt.X('predicted', title='Model said',
                            scale=alt.Scale(domain=[0, 1]), axis=alt.Axis(format='%')),
                    y=alt.Y('observed', title='Actually happened',
                            scale=alt.Scale(domain=[0, 1]), axis=alt.Axis(format='%')),
                    tooltip=['predicted', 'observed', 'n'])
                ln = pts.mark_line(color=HOME_C, opacity=0.5)
                st.altair_chart((diag + ln + pts).properties(height=300),
                                use_container_width=True)
                st.caption('Dots on the dashed line = the probabilities are honest.')
            except Exception:
                st.line_chart(rel.set_index('predicted')[['observed']])

    with st.expander('Full power ratings & method'):
        rt = pd.DataFrame([{'Team': abbr2name.get(t, t),
                            'Proj. power': round(eng.team_strength(t), 1)}
                           for t in eng.teams()])
        rt = rt.sort_values('Proj. power', ascending=False).reset_index(drop=True)
        rt.index = rt.index + 1
        st.dataframe(rt, width='stretch', height=320)
        if getattr(eng, 'projected', False):
            st.caption('**2026-27 projection:** each team = its current roster’s value '
                       '(2025-26 BPM reassigned to post-offseason teams + rookies) blended '
                       'with regressed 538-style Elo. Accuracy (68%) was measured on the '
                       'Elo engine over 2003-2026; the fresh-roster projection can’t be '
                       'back-tested until games are played. For analysis and fun, not betting.')
        else:
            st.caption('538-style Elo over 30,905 games, 2003-2026. For analysis, not betting.')


def render_ask(facts):
    key = ''
    try:
        key = st.secrets.get('GROQ_API_KEY', '')
    except Exception:
        key = os.environ.get('GROQ_API_KEY', '')
    if not key:
        st.info('💬 **Assistant not enabled.** Add a free Groq API key to chat about '
                'this matchup (why a team’s favored, what a factor means, what-ifs).')
        st.caption('Get a free key at console.groq.com → add it as `GROQ_API_KEY` in '
                   '`.streamlit/secrets.toml` (local) or the app’s Secrets (Streamlit Cloud).')
        return
    st.caption('Ask about this matchup — grounded on the model’s real numbers.')
    for m in st.session_state.get('chat', []):
        st.chat_message(m['role']).write(m['content'])
    pills = ['Why is the home team favored?', 'How much is home court worth?',
             'What if the away team was rested?', 'What is BPM?']
    pcols = st.columns(2)
    clicked = None
    for i, pl in enumerate(pills):
        if pcols[i % 2].button(pl, key=f'pill{i}', use_container_width=True):
            clicked = pl
    with st.form('askform', clear_on_submit=True):
        q = st.text_input('Your question', placeholder='Ask anything about this matchup…',
                          label_visibility='collapsed')
        sent = st.form_submit_button('Ask')
    q = clicked or (q if sent else '')
    if q:
        hist = st.session_state.get('chat', [])
        pairs = [(hist[i]['content'], hist[i + 1]['content'])
                 for i in range(0, len(hist) - 1, 2)]
        ctx = facts
        kb = get_kb()
        if kb is not None:
            hits = kb.retrieve(q, k=3)
            if hits:
                ctx += ('\n\nKNOWLEDGE (basketball concepts/strategy — use for '
                        'concept questions and cite the source name):\n')
                for title, cat, text, _ in hits:
                    ctx += f'[{title}] {text[:700]}\n'
        try:
            with st.spinner('Thinking…'):
                ans = chat_ask(q, ctx, pairs, key)
        except Exception as e:
            ans = f'(Assistant error: {type(e).__name__}. Check your GROQ_API_KEY.)'
        st.session_state.chat = hist + [{'role': 'user', 'content': q},
                                        {'role': 'assistant', 'content': ans}]
        st.rerun()


if level == 0:
    outs = [n for n, _ in out_home] + [n for n, _ in out_away]
    if outs:
        st.info('🩹 Out: ' + ', '.join(outs[:8]))
    st.caption('Switch to **🏀 Fan** or **🔬 Analyst** on the left for game '
               'conditions, injuries, and the full breakdown.')
else:
    labels = ['🔑 Keys to the matchup', '🧍 Players']
    if level >= 2:
        labels.append('✅ How good is it')
    labels.append('💬 Ask')
    _tabs = st.tabs(labels)
    with _tabs[0]:
        render_why()
    with _tabs[1]:
        render_players(level)
    ask_idx = 2
    if level >= 2:
        with _tabs[2]:
            render_quality()
        ask_idx = 3
    with _tabs[ask_idx]:
        render_ask(_facts)
