"""Input contracts for date-only, completed-game backtests."""
import numpy as np
import pandas as pd


def validate_games(games):
    required = ['date', 'season', 'home', 'away', 'home_pts', 'away_pts', 'home_win']
    if not set(required).issubset(games.columns):
        raise ValueError('Missing required game columns')
    if games.empty or games[required].isna().any().any():
        raise ValueError('Games must be nonempty and complete')
    if not pd.api.types.is_datetime64_any_dtype(games.date):
        raise ValueError('Parse date as datetime before validation')
    numeric = games[['season', 'home_pts', 'away_pts', 'home_win']].to_numpy(dtype=float)
    if not np.isfinite(numeric).all() or (games.season % 1 != 0).any():
        raise ValueError('Game numbers must be finite; seasons must be integers')
    if (games[['home_pts', 'away_pts']] < 0).any().any():
        raise ValueError('Scores cannot be negative')
    if (games.home == games.away).any() or (games.home_pts == games.away_pts).any():
        raise ValueError('Completed games need distinct teams and a winner')
    if not games.home_win.isin([0, 1]).all() or not ((games.home_pts > games.away_pts).astype(int) == games.home_win).all():
        raise ValueError('Winner must agree with final scores')
    days = games.date.dt.normalize()
    team_days = pd.concat([pd.DataFrame({'date': days, 'team': games[side]})
                           for side in ['home', 'away']])
    if team_days.duplicated().any():
        raise ValueError('Duplicate team/date: date-only pre-game ordering is ambiguous')
    ordered = games.sort_values('date')
    if not ordered.season.is_monotonic_increasing:
        raise ValueError('Season labels must increase chronologically')


def temporal_split(frame, test_seasons):
    """Only seasons strictly earlier than the first evaluation season may fit."""
    if not test_seasons:
        raise ValueError('Specify at least one evaluation season')
    train = frame[frame.season < min(test_seasons)].copy()
    test = frame[frame.season.isin(test_seasons)].copy()
    if train.empty or test.empty or train.date.max() >= test.date.min():
        raise ValueError('Need nonempty, strictly chronological train/test partitions')
    if set(test.season.unique()) != set(test_seasons):
        raise ValueError('Missing requested evaluation season')
    return train, test
