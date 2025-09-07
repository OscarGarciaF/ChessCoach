"""
Probability calculations for chess rating systems.

This module implements probability calculations for both Glicko and Elo rating systems
to determine the expected probability of winning games and the likelihood of achieving
consecutive win streaks.
"""

import math
from typing import Optional, Tuple
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

def _expected_prob_symmetric(mu_w: float, mu_l: float, phi_w: float, phi_l: float) -> float:
    """
    Symmetric Glicko-style win probability using *combined* uncertainty.
    Uses g(phi_combined) with phi_combined = sqrt(phi_w^2 + phi_l^2).
    """
    phi_comb = math.sqrt(phi_w * phi_w + phi_l * phi_l)
    g_comb = g_function(phi_comb)
    return expit(g_comb * (mu_w - mu_l))


def _estimate_pre_diff_from_post(
    mu_w_post: float,
    mu_l_post: float,
    phi_w_est: float,
    phi_l_est: float,
    max_iter: int = 50,
    tol: float = 1e-12,
    damping: float = 0.5
) -> Tuple[float, float, float, float, float]:
    """
    Heuristically estimate the *pre-game* rating difference (mu_w - mu_l) from post-game mus,
    assuming a single Glicko (not Glicko-2) update for each player and using today's RD as
    a proxy for the match-time RD.

    We solve for d_pre in the scalar fixed-point equation:
        d_post = d_pre + Δ_w(d_pre) + Δ_l(d_pre)

    where
        Δ_w = φ_w'² * g(φ_l) * (1 - E_w)      with E_w = σ(g(φ_l) * d_pre)
        Δ_l = φ_l'² * g(φ_w) * E_l            with E_l = σ(g(φ_w) * (-d_pre))

    and
        φ'² = 1 / ( 1/φ² + g(φ_op)² * E * (1 - E) )

    Returns:
        d_pre, mu_w_pre, mu_l_pre, delta_w, delta_l   (all in μ-units)
    """
    d_post = mu_w_post - mu_l_post
    d_pre = d_post  # start from "no bias" guess

    for _ in range(max_iter):
        g_w = g_function(phi_l_est)  # winner's update sees opponent RD
        g_l = g_function(phi_w_est)  # loser's  update sees opponent RD

        E_w = expit(g_w * d_pre)      # asymmetric expectations (winner's vantage)
        E_l = expit(g_l * (-d_pre))   # loser's vantage

        # RD updates in μ/φ space (Glicko-1)
        phi_w_prime_sq = 1.0 / (1.0 / (phi_w_est ** 2) + (g_w ** 2) * E_w * (1.0 - E_w))
        phi_l_prime_sq = 1.0 / (1.0 / (phi_l_est ** 2) + (g_l ** 2) * E_l * (1.0 - E_l))

        delta_w = phi_w_prime_sq * g_w * (1.0 - E_w)  # winner's μ increase
        delta_l = phi_l_prime_sq * g_l * E_l          # loser's  μ decrease magnitude

        d_pre_new = d_post - (delta_w + delta_l)
        if abs(d_pre_new - d_pre) < tol:
            d_pre = d_pre_new
            break
        # damping improves robustness in extreme RD or lopsided cases
        d_pre = damping * d_pre + (1.0 - damping) * d_pre_new

    # Recompute final deltas with the converged d_pre
    g_w = g_function(phi_l_est)
    g_l = g_function(phi_w_est)
    E_w = expit(g_w * d_pre)
    E_l = expit(g_l * (-d_pre))
    phi_w_prime_sq = 1.0 / (1.0 / (phi_w_est ** 2) + (g_w ** 2) * E_w * (1.0 - E_w))
    phi_l_prime_sq = 1.0 / (1.0 / (phi_l_est ** 2) + (g_l ** 2) * E_l * (1.0 - E_l))
    delta_w = phi_w_prime_sq * g_w * (1.0 - E_w)
    delta_l = phi_l_prime_sq * g_l * E_l

    mu_w_pre = mu_w_post - delta_w
    mu_l_pre = mu_l_post + delta_l
    return d_pre, mu_w_pre, mu_l_pre, delta_w, delta_l


def expected_win_prob_glicko(
    r_winner: Optional[int]=None,
    r_loser: Optional[int]=None,
    rd_winner: Optional[int]=None,
    rd_loser: Optional[int]=None,
    estimate_pregame: bool = True,
    rd_inflation_factor: float = 1.0
) -> Optional[float]:
    """
    Best-approximation Glicko win probability for the *winner* of a completed game.

    Backward-compatible: if called with only (r_winner, r_loser, rd_loser) it behaves
    like before, but if `rd_winner` is provided it will use both RDs and (by default)
    estimate the pre-game gap to reduce post-game bias.

    Args:
        r_winner: Winner's *post-game* rating (standard scale).
        r_loser:  Loser's  *post-game* rating (standard scale).
        rd_loser: Loser's  (live) RD, best available approximation.
        rd_winner: Winner's (live) RD, best available approximation. If not given,
                   falls back to the legacy "use opponent RD only" path.
        estimate_pregame: If True, estimate pre-game rating difference via a fixed-point
                   Glicko inversion using both RDs; otherwise use post-game ratings directly.
        rd_inflation_factor: Optional multiplier to slightly inflate both RDs if you suspect
                   today's RDs are lower than at match time (e.g., 1.05).

    Returns:
        float in [0, 1] — estimated *pre-game* probability that the winner would win;
        or None if ratings are unavailable.
    """
    if r_winner is None or r_loser is None:
        return None

    # Legacy path: only loser's RD available → original behavior (opponent RD only)
    if rd_loser is None:
        p = expected_win_prob_elo(r_winner, r_loser)
        return p
    
    if rd_winner is None:
        # Only loser's RD available → use original Glicko logic (no pre-game debias)
        mu_w = to_mu(float(r_winner))
        mu_l = to_mu(float(r_loser))
        phi_l = to_phi(float(rd_loser))
        g = g_function(phi_l)
        p = expit(g * (mu_w - mu_l))  # original logic
        # If user asked to "debias" but we lack winner RD, we cannot reliably invert.
        return p

    # Best path: both RDs available → use both in expectancy and pre-game debias
    mu_w_post = to_mu(float(r_winner))
    mu_l_post = to_mu(float(r_loser))
    phi_w = to_phi(float(rd_winner) * rd_inflation_factor)
    phi_l = to_phi(float(rd_loser) * rd_inflation_factor)

    if estimate_pregame:
        d_pre, mu_w_pre, mu_l_pre, delta_w, delta_l = _estimate_pre_diff_from_post(
            mu_w_post, mu_l_post, phi_w, phi_l
        )
        # Use symmetric probability with combined RD (complements to 1)
        p = _expected_prob_symmetric(mu_w_pre, mu_l_pre, phi_w, phi_l)

        return p
    else:
        # No debiasing: use post-game ratings with symmetric combined-RD probability
        p = _expected_prob_symmetric(mu_w_post, mu_l_post, phi_w, phi_l)
        return p



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
