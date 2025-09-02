"""
Chess.com API interaction functions.

This module provides high-level functions for interacting with the Chess.com Public API,
including fetching player data, game archives, and statistics.

Uses the official chess.com Python module for reliable API interactions.
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

import chessdotcom
from chessdotcom import Client

from models import PlayerInfo


def setup_chess_client(user_agent: str) -> None:
    """
    Initialize the chess.com client with proper User-Agent.
    
    Args:
        user_agent: User-Agent string identifying your application and contact info
    """
    Client.request_config["headers"]["User-Agent"] = user_agent


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
    titles: List[str], 
    verbose: bool = False
) -> Dict[str, str]:
    """
    Fetch all players with the specified chess titles.
    
    Args:
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
        try:
            response = chessdotcom.get_titled_players(title)
            if not response or not hasattr(response, 'json'):
                if verbose:
                    print(f"[WARN] No response for title {title}")
                continue
                
            data = response.json
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
        except Exception as e:
            if verbose:
                print(f"[WARN] Error fetching title {title}: {e}")
            continue
    
    return players


def fetch_player_archives(username: str) -> List[str]:
    """
    Fetch the list of monthly game archive URLs for a player.
    
    Args:
        username: Chess.com username
        
    Returns:
        List of archive URLs in chronological order
    """
    try:
        response = chessdotcom.get_player_game_archives(username)
        if not response or not hasattr(response, 'archives'):
            return []
        return response.archives
    except Exception:
        return []


def fetch_month_games(archive_url: str) -> List[dict]:
    """
    Fetch all games from a monthly archive.
    
    Args:
        archive_url: URL to the monthly archive (not used with chess.com module)
        
    Returns:
        List of game dictionaries
        
    Note:
        This function needs to be called differently with the chess.com module.
        The archive_url format is: https://api.chess.com/pub/player/{username}/games/{year}/{month}
        We extract the username, year, and month from the URL.
    """
    try:
        # Extract username, year, month from URL
        # URL format: https://api.chess.com/pub/player/{username}/games/{year}/{month}
        parts = archive_url.split('/')
        if len(parts) < 7:
            return []
        
        username = parts[5]  # player/{username}
        year = parts[7]      # games/{year}
        month = parts[8]     # {year}/{month}
        
        response = chessdotcom.get_player_games_by_month(username, year, month)
        if not response or not hasattr(response, 'games'):
            return []
        
        # Convert games to dictionary format
        games = []
        for game in response.games:
            game_dict = {
                'url': game.url,
                'pgn': game.pgn,
                'time_control': game.time_control,
                'start_time': game.start_time,
                'end_time': game.end_time,
                'rules': game.rules,
                'time_class': game.time_class,
                'fen': game.fen,
                'white': {
                    'username': game.white.username if game.white else None,
                    'rating': game.white.rating if game.white else None,
                    'result': game.white.result if game.white else None,
                },
                'black': {
                    'username': game.black.username if game.black else None,
                    'rating': game.black.rating if game.black else None,
                    'result': game.black.result if game.black else None,
                }
            }
            games.append(game_dict)
        
        return games
    except Exception:
        return []


def fetch_player_stats(username: str) -> dict:
    """
    Fetch player statistics including ratings and rating deviations.
    
    Args:
        username: Chess.com username
        
    Returns:
        Player statistics dictionary
    """
    try:
        response = chessdotcom.get_player_stats(username)
        if not response or not hasattr(response, 'json'):
            return {}
        return response.json.get('stats', {})
    except Exception:
        return {}


def fetch_player_profile(username: str) -> dict:
    """
    Fetch player profile information including avatar.
    
    Args:
        username: Chess.com username
        
    Returns:
        Player profile dictionary
    """
    try:
        response = chessdotcom.get_player_profile(username)
        if not response or not hasattr(response, 'json'):
            return {}
        return response.json.get('player', {})
    except Exception:
        return {}


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
    username: str,
    start_time: int,
    end_time: int
) -> List[dict]:
    """
    Fetch all games for a player within the specified time window.
    
    Args:
        username: Chess.com username
        start_time: Window start timestamp
        end_time: Window end timestamp
        
    Returns:
        List of game dictionaries sorted by end_time
    """
    archives = fetch_player_archives(username)
    if not archives:
        return []
    
    # Get only relevant monthly archives
    relevant_urls = month_urls_for_window(archives, start_time, end_time)
    
    # Fetch games from relevant archives
    all_games = []
    for archive_url in relevant_urls:
        games = fetch_month_games(archive_url)
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
    # Extract country code from Chess.com country URL
    country = profile.get("country")
    country_code = None
    if country and isinstance(country, str):
        # Country comes as "https://api.chess.com/pub/country/XX" where XX is the country code
        country_code = country.split("/")[-1] if "/" in country else country
    
    return PlayerInfo(
        username=username,
        title=title,
        avatar=profile.get("avatar"),
        max_rating=extract_max_rating(stats),
        country=country_code
    )
