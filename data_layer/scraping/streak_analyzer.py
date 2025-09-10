"""
Chess game analysis and streak detection.

This module analyzes chess games to identify consecutive win streaks and calculate
their statistical significance based on rating-based win probabilities.
"""

import logging
import sys
from typing import Dict, List, Optional, Tuple

from chess_api import extract_rating_deviation, fetch_player_stats
from models import GameView, PlayerInfo, Streak
from probability import (
    calculate_streak_probability,
    classify_streak_probability,
    expected_win_prob_glicko
)

logger = logging.getLogger(__name__)

def analyze_game_from_perspective(
    username: str, 
    game: dict
) -> Optional[Tuple[bool, str, str, int, Optional[int], Optional[int], str, str]]:
    """
    Analyze a game from a specific player's perspective.
    
    Args:
        username: Username of the player whose perspective to analyze
        game: Game dictionary from Chess.com API
        
    Returns:
        Tuple of (won, rules, time_class, end_time, my_rating, opp_rating, opp_username, url)
        or None if the game cannot be analyzed
        
    Note:
        A 'win' is only counted when the player's result is explicitly 'win'.
        All other results (draws, losses, etc.) break win streaks.
    """
    end_time = game.get("end_time")
    rules = game.get("rules")
    time_class = game.get("time_class")
    url = game.get("url", "")
    
    white_player = game.get("white", {}) or {}
    black_player = game.get("black", {}) or {}

    # Validate required game data
    if not isinstance(end_time, int) or not rules or not time_class:
        return None

    username_lower = username.lower()
    is_white = white_player.get("username", "").lower() == username_lower
    is_black = black_player.get("username", "").lower() == username_lower

    # Player must be in the game
    if not (is_white or is_black):
        return None

    # Determine if this player won
    white_won = (white_player.get("result") == "win")
    black_won = (black_player.get("result") == "win")

    if is_white:
        my_rating = white_player.get("rating")
        opponent_rating = black_player.get("rating")
        opponent_username = black_player.get("username", "")
        won = white_won
    else:
        my_rating = black_player.get("rating")
        opponent_rating = white_player.get("rating")
        opponent_username = white_player.get("username", "")
        won = black_won

    return (won, rules, time_class, end_time, my_rating, opponent_rating, opponent_username, url)


def detect_win_streaks(
    player: PlayerInfo,
    games: List[dict],
    stats_cache: Dict[str, dict],
    thresholds: List[Tuple[str, float]],
    verbose: bool = False
) -> List[Streak]:
    """
    Detect and analyze consecutive win streaks for a player.
    
    Args:
        player: Player information
        games: List of games in chronological order
        stats_cache: Cache of player statistics to avoid redundant API calls
        thresholds: Probability thresholds for classifying interesting streaks
        verbose: Whether to enable verbose logging
        
    Returns:
        List of statistically interesting win streaks
        
    Note:
        Only streaks that meet the probability thresholds are returned.
        The algorithm uses rating-based probability calculations to determine
        how unlikely each streak is to occur.
    """
    streaks: List[Streak] = []
    current_streak_games: List[GameView] = []
    current_win_probabilities: List[float] = []
    streak_start_time: Optional[int] = None
    player_username_lower = player.username.lower()

    def finalize_current_streak():
        """Finalize the current streak if it's interesting."""
        nonlocal current_streak_games, current_win_probabilities, streak_start_time
        
        if not current_streak_games:
            return

        # Calculate combined probability
        combined_prob = calculate_streak_probability(current_win_probabilities)
        threshold_label = classify_streak_probability(combined_prob, thresholds)

        # Only keep statistically interesting streaks
        if threshold_label is not None:
            streak = Streak(
                player=player,
                start_time=streak_start_time or current_streak_games[0].end_time,
                end_time=current_streak_games[-1].end_time,
                length=len(current_streak_games),
                p_combined=combined_prob,
                threshold_label=threshold_label,
                games=current_streak_games.copy()
            )
            streaks.append(streak)

        # Reset for next streak
        current_streak_games = []
        current_win_probabilities = []
        streak_start_time = None

    # Process each game
    for game in games:
        game_analysis = analyze_game_from_perspective(player.username, game)
        if game_analysis is None:
            continue

        (won, rules, time_class, end_time, my_rating, 
         opponent_rating, opponent_username, game_url) = game_analysis

        if not won:
            # Streak broken - finalize current streak and continue
            finalize_current_streak()
            continue

        # This is a win - add to current streak
        
        # Fetch opponent stats for RD calculation (with caching)
        opponent_username_lower = opponent_username.lower()
        if opponent_username_lower not in stats_cache:
            opponent_stats = fetch_player_stats(opponent_username_lower)
            stats_cache[opponent_username_lower] = opponent_stats

        opponent_stats = stats_cache.get(opponent_username_lower, {})
        opponent_rd = extract_rating_deviation(opponent_stats, rules, time_class)
        my_stats = stats_cache.get(player_username_lower, {})
        my_rd = extract_rating_deviation(my_stats, rules, time_class)

        # Calculate win probability and estimated ratings
        win_probability, estimated_winner_rating, estimated_loser_rating = expected_win_prob_glicko(
            my_rating, opponent_rating, my_rd, opponent_rd
        )
        if win_probability is None:
            # If we can't calculate probability, use neutral value to avoid bias
            win_probability = 0.5
            estimated_winner_rating = my_rating
            estimated_loser_rating = opponent_rating

        # Initialize streak if this is the first win
        if not current_streak_games:
            streak_start_time = end_time

        # Add game to current streak
        game_view = GameView(
            end_time=end_time,
            rules=rules,
            time_class=time_class,
            url=game_url,
            opponent_username=opponent_username,
            opponent_rating=opponent_rating if isinstance(opponent_rating, int) else None,
            winner_rating=my_rating if isinstance(my_rating, int) else None,
            p_win=float(win_probability),
            estimated_winner_rating=estimated_winner_rating,
            estimated_loser_rating=estimated_loser_rating
        )
        
        current_streak_games.append(game_view)
        current_win_probabilities.append(win_probability)

    # Finalize any remaining streak
    finalize_current_streak()

    return streaks


def analyze_player_streaks(
    player: PlayerInfo,
    games: List[dict],
    stats_cache: Dict[str, dict],
    thresholds: List[Tuple[str, float]],
    verbose: bool = False
) -> List[Streak]:
    """
    High-level function to analyze all streaks for a single player.
    
    Args:
        player: Player information
        games: List of games in chronological order  
        stats_cache: Shared cache for player statistics
        thresholds: Probability thresholds for interesting streaks
        verbose: Whether to enable verbose logging
        
    Returns:
        List of interesting win streaks found for this player
    """
    if not games:
        return []

    if verbose:
        logger.info("Analyzing %d games for %s", len(games), player.username)

    streaks = detect_win_streaks(player, games, stats_cache, thresholds, verbose)

    if verbose and streaks:
        logger.info("Found %d interesting streaks for %s", len(streaks), player.username)

    return streaks
