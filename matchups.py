"""Transparent, illustrative independent matchup probability model."""
import math
from dataclasses import dataclass
from scipy.stats import norm

@dataclass
class MatchupInputs:
    sport: str
    away: str
    home: str
    away_offense: float
    away_defense: float
    home_offense: float
    home_defense: float
    away_pace: float
    home_pace: float
    home_advantage: float
    away_adjustment: float = 0.0
    home_adjustment: float = 0.0
    margin_sd: float = 12.0
    total_sd: float = 18.0


def project_matchup(x: MatchupInputs):
    """NBA inputs: points per 100 possessions; NFL inputs: points per game.

    Defense input is points ALLOWED (higher is worse). Pace is possessions/48
    for NBA; NFL pace input is offensive plays per game (proxy, not drives).
    Injury adjustments are signed points added to expected score.
    """
    if x.sport == 'NBA':
        pace = (x.away_pace + x.home_pace) / 2
        away_pts = (x.away_offense + x.home_defense) / 2 * pace / 100
        home_pts = (x.home_offense + x.away_defense) / 2 * pace / 100
    elif x.sport == 'NFL':
        pace = (x.away_pace + x.home_pace) / 2
        # Scoring averages are points/game, so pace is used only for context.
        away_pts = (x.away_offense + x.home_defense) / 2
        home_pts = (x.home_offense + x.away_defense) / 2
    else:
        raise ValueError('Unsupported sport')
    away_pts += x.away_adjustment
    home_pts += x.home_adjustment + x.home_advantage
    margin = home_pts - away_pts
    total = home_pts + away_pts
    home_win = float(norm.cdf(margin / x.margin_sd))
    return {'away_points': away_pts, 'home_points': home_pts, 'home_margin': margin,
            'total': total, 'home_win': home_win, 'away_win': 1-home_win,
            'pace': pace}


def market_probability(mean, sd, line, side='Over'):
    return float(norm.sf(line, loc=mean, scale=sd) if side == 'Over'
                 else norm.cdf(line, loc=mean, scale=sd))


def american_to_prob(odds):
    if odds == 0: raise ValueError('American odds cannot be zero')
    return 100/(odds+100) if odds > 0 else -odds/(-odds+100)


def fair_odds(prob):
    if not 0 < prob < 1: return 'N/A'
    value = 100*(1-prob)/prob if prob < .5 else -100*prob/(1-prob)
    return f'{value:+.0f}'


def expected_roi(prob, odds):
    return prob * (odds/100 if odds > 0 else 100/-odds) - (1-prob)
