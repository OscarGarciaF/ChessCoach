"""
Chess.com API interaction functions.

This module provides high-level functions for interacting with the Chess.com Public API,
including fetching player data, game archives, and statistics.
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

from config import PUBAPI
from http_client import ChessComHttpClient
from models import PlayerInfo


def now_utc_timestamp() -> int:
    """Get current UTC timestamp as integer."""
    return int(datetime.now(timezone.utc).timestamp())


def parse_time_window(days: int) -> Tuple[int, int]:
    """
    Parse a time window in days into start and end timestamps.
    
    Args:
        days: Number of days back from now
        
    Returns:
        Tuple of (start_timestamp, end_timestamp)
    """
    end_time = now_utc_timestamp()
    start_time = int((datetime.now(timezone.utc) - timedelta(days=days)).timestamp())
    return start_time, end_time


def fetch_titled_players(
    http: ChessComHttpClient, 
    titles: List[str], 
    verbose: bool = False
) -> Dict[str, str]:
    """
    Fetch all players with the specified chess titles.
    
    Args:
        http: HTTP client instance
        titles: List of title abbreviations (e.g., ['GM', 'IM'])
        verbose: Whether to print verbose logging
        
    Returns:
        Dictionary mapping lowercase username to title
        
    Note:
        If a player has multiple titles, the highest-ranked title is kept.
    """
    from config import TITLE_RANK
    
    players: Dict[str, str] = {}
    
    for title in titles:
        url = f"{PUBAPI}/titled/{title}"
        data = http.get_json(url)
        
        if not data or "players" not in data:
            if verbose:
                print(f"[WARN] No players found for title {title}")
            continue
            
        for username in data["players"]:
            username_lower = username.lower()
            
            # Keep the highest-ranked title if player has multiple
            existing_title = players.get(username_lower)
            if (existing_title is None or 
                TITLE_RANK.get(title, 999) < TITLE_RANK.get(existing_title, 999)):
                players[username_lower] = title
    
    return players


def fetch_player_archives(http: ChessComHttpClient, username: str) -> List[str]:
    """
    Fetch the list of monthly game archive URLs for a player.
    
    Args:
        http: HTTP client instance
        username: Chess.com username
        
    Returns:
        List of archive URLs in chronological order
    """
    url = f"{PUBAPI}/player/{username}/games/archives"
    data = http.get_json(url)
    
    if not data or "archives" not in data:
        return []
    
    return data["archives"]


def fetch_month_games(http: ChessComHttpClient, archive_url: str) -> List[dict]:
    """
    Fetch all games from a monthly archive.
    
    Args:
        http: HTTP client instance
        archive_url: URL to the monthly archive
        
    Returns:
        List of game dictionaries
    """
    data = http.get_json(archive_url)
    
    if not data or "games" not in data:
        return []
    
    return data["games"]


def fetch_player_stats(http: ChessComHttpClient, username: str) -> dict:
    """
    Fetch player statistics including ratings and rating deviations.
    
    Args:
        http: HTTP client instance
        username: Chess.com username
        
    Returns:
        Player statistics dictionary
    """
    url = f"{PUBAPI}/player/{username}/stats"
    data = http.get_json(url)
    return data or {}


def fetch_player_profile(http: ChessComHttpClient, username: str) -> dict:
    """
    Fetch player profile information including avatar.
    
    Args:
        http: HTTP client instance
        username: Chess.com username
        
    Returns:
        Player profile dictionary
    """
    url = f"{PUBAPI}/player/{username}"
    data = http.get_json(url)
    return data or {}


def month_urls_for_window(
    archives: List[str], 
    start_time: int, 
    end_time: int
) -> List[str]:
    """
    Filter archive URLs to only those that might contain games in the time window.
    
    Args:
        archives: List of monthly archive URLs in chronological order
        start_time: Window start timestamp
        end_time: Window end timestamp
        
    Returns:
        List of archive URLs that intersect the time window
        
    Note:
        Returns the last 2-3 months that could contain games in the window
        to avoid fetching unnecessary historical data.
    """
    start_dt = datetime.fromtimestamp(start_time, tz=timezone.utc)
    end_dt = datetime.fromtimestamp(end_time, tz=timezone.utc)

    def year_month(dt: datetime) -> Tuple[int, int]:
        return dt.year, dt.month

    # Get all year-month combinations that could contain relevant games
    target_months = set()
    target_months.add(year_month(start_dt))
    target_months.add(year_month(end_dt))
    
    # Include month in between if crossing month boundary
    mid_dt = start_dt + timedelta(days=15)
    target_months.add(year_month(mid_dt))

    # Find matching archive URLs
    relevant_urls = []
    for url in archives:
        for year, month in target_months:
            month_suffix = f"/{year}/{month:02d}"
            if url.endswith(month_suffix):
                relevant_urls.append(url)
                break

    # Remove duplicates while preserving chronological order
    seen = set()
    filtered_urls = []
    for url in relevant_urls:
        if url not in seen:
            filtered_urls.append(url)
            seen.add(url)

    return filtered_urls


def fetch_games_in_window(
    http: ChessComHttpClient,
    username: str,
    start_time: int,
    end_time: int
) -> List[dict]:
    """
    Fetch all games for a player within the specified time window.
    
    Args:
        http: HTTP client instance
        username: Chess.com username
        start_time: Window start timestamp
        end_time: Window end timestamp
        
    Returns:
        List of game dictionaries sorted by end_time
    """
    archives = fetch_player_archives(http, username)
    if not archives:
        return []
    
    # Get only relevant monthly archives
    relevant_urls = month_urls_for_window(archives, start_time, end_time)
    
    # Fetch games from relevant archives
    all_games = []
    for archive_url in relevant_urls:
        games = fetch_month_games(http, archive_url)
        all_games.extend(games)
    
    # Filter games to the exact time window
    filtered_games = []
    for game in all_games:
        game_end_time = game.get("end_time")
        if isinstance(game_end_time, int) and start_time <= game_end_time <= end_time:
            filtered_games.append(game)
    
    # Sort by end_time to ensure chronological order
    filtered_games.sort(key=lambda g: g.get("end_time", 0))
    
    return filtered_games


def extract_rating_deviation(stats: dict, rules: str, time_class: str) -> Optional[int]:
    """
    Extract rating deviation (RD) for a specific game mode from player stats.
    
    Args:
        stats: Player statistics dictionary
        rules: Game rules (e.g., 'chess', 'chess960')
        time_class: Time control (e.g., 'blitz', 'rapid')
        
    Returns:
        Rating deviation as integer, or None if not available
        
    Example:
        For chess blitz, looks for stats['chess_blitz']['last']['rd']
    """
    stats_key = f"{rules}_{time_class}"
    mode_stats = stats.get(stats_key, {})
    last_stats = mode_stats.get("last", {})
    rd_value = last_stats.get("rd")
    
    return int(rd_value) if isinstance(rd_value, (int, float)) else None


def extract_max_rating(stats: dict) -> Optional[int]:
    """
    Extract the highest rating across all game modes from player stats.
    
    Args:
        stats: Player statistics dictionary
        
    Returns:
        Highest rating found, or None if no ratings available
    """
    max_rating = None
    
    # Look through all chess-related stats keys
    for key in stats.keys():
        if key.startswith("chess"):
            last_stats = stats[key].get("last", {})
            rating = last_stats.get("rating")
            
            if isinstance(rating, (int, float)):
                rating = int(rating)
                if max_rating is None or rating > max_rating:
                    max_rating = rating
    
    return max_rating


def create_player_info(
    username: str,
    title: Optional[str],
    profile: dict,
    stats: dict
) -> PlayerInfo:
    """
    Create a PlayerInfo object from API data.
    
    Args:
        username: Player's username
        title: Player's chess title
        profile: Player profile data from API
        stats: Player statistics data from API
        
    Returns:
        PlayerInfo object with extracted data
    """
    return PlayerInfo(
        username=username,
        title=title,
        avatar=profile.get("avatar"),
        max_rating=extract_max_rating(stats)
    )
