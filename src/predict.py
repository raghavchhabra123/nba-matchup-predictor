"""Prediction helpers: HCA toggle via mirror-averaging + player-impact adjustment."""
import numpy as np

from .features import matchup_features

# Empirical NBA conversion: ~1 point of margin ≈ 0.13 shift in win-prob logit near even.
LOGIT_PER_POINT = 0.13


def _logit(p):
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p))


def _sigmoid(x):
    return 1 / (1 + np.exp(-x))


def predict_home_prob(model, home_row, away_row, home_rest=2, away_rest=2) -> float:
    X = matchup_features(home_row, away_row, home_rest, away_rest)
    return float(model.predict_proba(X)[0, 1])


def predict_matchup(model, home_row, away_row, home_rest=2, away_rest=2,
                    home_court=True, margin_shift_home=0.0) -> dict:
    """Win probability for `home_row`'s team vs `away_row`'s team.

    home_court=False -> neutral court, estimated by mirror-averaging:
        P_neutral(A vs B) = mean( P(A hosts B), 1 - P(B hosts A) )
    margin_shift_home: expected point-margin change for the home side from
        player availability (negative = home side weakened). Applied on the
        logit scale.
    """
    p_hosted = predict_home_prob(model, home_row, away_row, home_rest, away_rest)
    p_mirror = predict_home_prob(model, away_row, home_row, away_rest, home_rest)
    p_neutral = 0.5 * (p_hosted + (1 - p_mirror))
    base = p_hosted if home_court else p_neutral
    adj = _sigmoid(_logit(base) + LOGIT_PER_POINT * margin_shift_home)
    return {
        'prob_home': float(adj),
        'prob_home_base': float(base),
        'prob_with_hca': float(p_hosted),
        'prob_neutral': float(p_neutral),
        'hca_edge': float(p_hosted - p_neutral),
    }


def players_margin_shift(out_impacts_home, out_impacts_away) -> float:
    """Net expected margin change for the HOME side when listed players sit.

    Each impact = player's estimated points-per-game value above a
    replacement-level fill-in (see players_2026.csv `impact`).
    """
    return -float(np.sum(out_impacts_home)) + float(np.sum(out_impacts_away))
