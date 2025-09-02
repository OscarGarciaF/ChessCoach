"""
Data models for the Interesting Chess data scraper.

This module defines the data structures used to represent games, streaks,
and player information throughout the application.
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class GameView:
    """
    Represents a single chess game from a player's perspective.
    
    Attributes:
        end_time: Unix timestamp when the game ended
        rules: Chess variant (e.g., 'chess', 'chess960')
        time_class: Time control category (e.g., 'blitz', 'rapid', 'bullet')
        url: Chess.com URL for the game
        opponent_username: Username of the opponent
        opponent_rating: Opponent's rating after the game
        winner_rating: Winner's rating after the game
        p_win: Expected probability of winning this game (0.0 to 1.0)
    """
    end_time: int
    rules: str
    time_class: str
    url: str
    opponent_username: str
    opponent_rating: Optional[int]
    winner_rating: Optional[int]
    p_win: float


@dataclass
class PlayerInfo:
    """
    Represents basic player information.
    
    Attributes:
        username: Player's Chess.com username
        title: Chess title (GM, IM, etc.)
        avatar: URL to player's avatar image
        max_rating: Highest rating across all time controls
        country: Player's country code
    """
    username: str
    title: Optional[str] = None
    avatar: Optional[str] = None
    max_rating: Optional[int] = None
    country: Optional[str] = None


@dataclass
class Streak:
    """
    Represents a consecutive win streak for a player.
    
    Attributes:
        player: Player information
        start_time: Unix timestamp when the streak started
        end_time: Unix timestamp when the streak ended
        length: Number of consecutive wins
        p_combined: Combined probability of achieving this streak
        threshold_label: Human-readable threshold classification
        games: List of games in the streak
    """
    player: PlayerInfo
    start_time: int
    end_time: int
    length: int
    p_combined: float
    threshold_label: Optional[str]
    games: List[GameView] = field(default_factory=list)


@dataclass
class StreakSummary:
    """
    Summary statistics for a streak analysis run.
    
    Attributes:
        window_days: Number of days analyzed
        players_processed: Total number of players analyzed
        streaks_found: Total number of interesting streaks found
        counts_by_threshold: Breakdown of streaks by probability threshold
        generated_at: Unix timestamp when analysis was completed
    """
    window_days: int
    players_processed: int
    streaks_found: int
    counts_by_threshold: dict
    generated_at: int
