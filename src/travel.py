"""Travel & altitude adjustments (Tier 3).

For a hypothetical matchup we assume the visitor flies in from their own city
and the host is at home. Home court (+2.5) already includes *average* travel,
so this models only the deviations that research shows actually matter:

  • Altitude — Denver (5,280 ft) and Utah (4,300 ft) get a documented extra
    home edge; visitors tire in thin air. Denver's home net rating is ~2.6 pts
    better than the league-average home edge.
    (sportico.com Denver altitude study)
  • Long eastward travel — flying east (body clock advanced) is the harmful
    direction; home point differential drops up to ~4.5 pts for a 2-hour
    eastward shift. Distance matters, westward barely.
    (PMC9245584; ScienceDaily 2024)

Only trips beyond a threshold count, so typical games get ~0 and the number
stays honest. Everything is in points added to the HOME expected margin.
"""
from __future__ import annotations

import math

# abbr -> (lat, lon, utc_offset_hours, altitude_ft)
ARENAS = {
    'ATL': (33.757, -84.396, -5, 1050), 'BOS': (42.366, -71.062, -5, 20),
    'BKN': (40.683, -73.975, -5, 30), 'CHA': (35.225, -80.839, -5, 750),
    'CHI': (41.881, -87.674, -6, 590), 'CLE': (41.497, -81.688, -5, 650),
    'DAL': (32.790, -96.810, -6, 430), 'DEN': (39.749, -105.008, -7, 5280),
    'DET': (42.341, -83.055, -5, 600), 'GSW': (37.768, -122.388, -8, 10),
    'HOU': (29.751, -95.362, -6, 50), 'IND': (39.764, -86.155, -5, 720),
    'LAC': (33.945, -118.342, -8, 120), 'LAL': (34.043, -118.267, -8, 300),
    'MEM': (35.138, -90.051, -6, 260), 'MIA': (25.781, -80.187, -5, 10),
    'MIL': (43.045, -87.917, -6, 600), 'MIN': (44.980, -93.276, -6, 830),
    'NOP': (29.949, -90.082, -6, 5), 'NYK': (40.751, -73.993, -5, 30),
    'OKC': (35.463, -97.515, -6, 1200), 'ORL': (28.539, -81.384, -5, 100),
    'PHI': (39.901, -75.172, -5, 40), 'PHX': (33.446, -112.071, -7, 1090),
    'POR': (45.532, -122.667, -8, 50), 'SAC': (38.580, -121.500, -8, 30),
    'SAS': (29.427, -98.437, -6, 650), 'TOR': (43.643, -79.379, -5, 250),
    'UTA': (40.768, -111.901, -7, 4300), 'WAS': (38.898, -77.021, -5, 30),
}

ALTITUDE_BONUS = {'DEN': 2.2, 'UTA': 1.2}   # extra home edge from thin air


def haversine_miles(a, b) -> float:
    lat1, lon1 = math.radians(a[0]), math.radians(a[1])
    lat2, lon2 = math.radians(b[0]), math.radians(b[1])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 3959 * 2 * math.asin(math.sqrt(h))


def compute_travel(home: str, away: str) -> dict:
    """Points added to the HOME margin from the visitor's trip + host altitude."""
    if home not in ARENAS or away not in ARENAS:
        return {'points': 0.0, 'distance': 0, 'tz_shift': 0, 'altitude_ft': 0,
                'dist_pts': 0.0, 'tz_pts': 0.0, 'alt_pts': 0.0}
    H, A = ARENAS[home], ARENAS[away]
    distance = haversine_miles(A, H)

    # visitor's body clock shift: host east of home => positive (harder)
    tz_shift = H[2] - A[2]

    # distance only counts beyond 800 mi (typical trips ~0), capped near cross-country
    dist_pts = 0.6 * max(0.0, distance - 800) / 2200
    dist_pts = min(dist_pts, 0.8)

    # eastward travel penalises the visitor; westward roughly half
    if tz_shift > 0:
        tz_pts = 0.55 * tz_shift        # away flew east -> helps home
    else:
        tz_pts = 0.22 * (-tz_shift)     # away flew west -> smaller help to home
    tz_pts = min(tz_pts, 1.6)

    alt_pts = ALTITUDE_BONUS.get(home, 0.0)

    return {
        'points': round(dist_pts + tz_pts + alt_pts, 2),
        'distance': round(distance),
        'tz_shift': tz_shift,
        'altitude_ft': H[3],
        'dist_pts': round(dist_pts, 2),
        'tz_pts': round(tz_pts, 2),
        'alt_pts': round(alt_pts, 2),
    }
