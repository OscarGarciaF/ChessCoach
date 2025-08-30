"""
Probability calculations for chess rating systems.

This module implements probability calculations for both Glicko and Elo rating systems
to determine the expected probability of winning games and the likelihood of achieving
consecutive win streaks.
"""

import math
from typing import Optional

from config import GLICKO_SCALE, GLICKO_BASE_RATING, ELO_K_FACTOR


def to_mu(rating: float) -> float:
    """
    Convert a rating to the Glicko μ (mu) scale.
    
    Args:
        rating: Standard rating value
        
    Returns:
        Rating converted to Glicko μ scale
    """
    return (rating - GLICKO_BASE_RATING) / GLICKO_SCALE


def to_phi(rd: float) -> float:
    """
    Convert a rating deviation (RD) to the Glicko φ (phi) scale.
    
    Args:
        rd: Rating deviation value
        
    Returns:
        RD converted to Glicko φ scale
    """
    return rd / GLICKO_SCALE


def g_function(phi: float) -> float:
    """
    Calculate the Glicko g(φ) function.
    
    This function reduces the impact of games against highly uncertain opponents.
    
    Args:
        phi: Rating deviation in φ scale
        
    Returns:
        g(φ) value for Glicko probability calculations
    """
    return 1.0 / math.sqrt(1.0 + 3.0 * (phi ** 2) / (math.pi ** 2))


def expit(x: float) -> float:
    """
    Numerically stable sigmoid function (logistic function).
    
    Equivalent to 1 / (1 + exp(-x)) but avoids overflow for large |x|.
    
    Args:
        x: Input value
        
    Returns:
        Sigmoid of x
    """
    if x >= 0:
        z = math.exp(-x)
        return 1.0 / (1.0 + z)
    else:
        z = math.exp(x)
        return z / (1.0 + z)


def expected_win_prob_glicko(
    r_winner: Optional[int], 
    r_loser: Optional[int],
    rd_loser: Optional[int]
) -> Optional[float]:
    """
    Calculate expected win probability using Glicko rating system.
    
    If the opponent's rating deviation (RD) is available, uses the full Glicko
    probability calculation. Otherwise, falls back to Elo-style calculation.
    
    Args:
        r_winner: Winner's rating after the game
        r_loser: Loser's rating after the game  
        rd_loser: Loser's rating deviation (uncertainty)
        
    Returns:
        Expected probability of the winner winning (0.0 to 1.0),
        or None if ratings are unavailable
        
    Note:
        The Glicko system accounts for rating uncertainty (RD) which makes
        the probability calculation more accurate than pure Elo calculations.
    """
    if r_winner is None or r_loser is None:
        return None
    
    # Fall back to Elo if RD is not available
    if rd_loser is None:
        return expected_win_prob_elo(r_winner, r_loser)

    # Full Glicko calculation
    mu_winner = to_mu(float(r_winner))
    mu_loser = to_mu(float(r_loser))
    phi_loser = to_phi(float(rd_loser))
    g = g_function(phi_loser)
    
    return expit(g * (mu_winner - mu_loser))


def expected_win_prob_elo(r_winner: int, r_loser: int) -> float:
    """
    Calculate expected win probability using classic Elo formula.
    
    Args:
        r_winner: Winner's rating
        r_loser: Loser's rating
        
    Returns:
        Expected probability of the winner winning (0.0 to 1.0)
    """
    rating_diff = r_winner - r_loser
    return 1.0 / (1.0 + 10.0 ** (-rating_diff / ELO_K_FACTOR))


def classify_streak_probability(probability: float, thresholds: list) -> Optional[str]:
    """
    Classify a streak probability into human-readable threshold categories.
    
    Args:
        probability: Combined probability of achieving the streak
        thresholds: List of (label, cutoff) tuples in ascending order of rarity
        
    Returns:
        Threshold label if the probability meets any threshold, None otherwise
        
    Example:
        >>> classify_streak_probability(0.005, [("≤1%", 0.01), ("≤0.1%", 0.001)])
        "≤1%"
    """
    for label, cutoff in thresholds:
        if probability <= cutoff:
            return label
    return None


def calculate_streak_probability(win_probabilities: list) -> float:
    """
    Calculate the combined probability of achieving a streak of wins.
    
    Uses log-space arithmetic to avoid numerical underflow for long streaks.
    
    Args:
        win_probabilities: List of individual game win probabilities
        
    Returns:
        Combined probability of achieving all wins in sequence
        
    Note:
        Individual probabilities are clamped to avoid log(0) and maintain
        numerical stability.
    """
    if not win_probabilities:
        return 1.0
    
    # Use log-space to avoid underflow
    log_prob_sum = 0.0
    for p in win_probabilities:
        # Clamp probability to avoid log(0) and extreme values
        clamped_p = max(min(p, 1.0 - 1e-15), 1e-15)
        log_prob_sum += math.log(clamped_p)
    
    # Convert back from log-space, handling underflow
    return math.exp(log_prob_sum) if log_prob_sum > -1e9 else 0.0
