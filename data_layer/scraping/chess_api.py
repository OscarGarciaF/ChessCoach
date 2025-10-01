"""
Chess.com API interaction functions.

This module provides high-level functions for interacting withdef fetch_player_stats(username: str) -> dict:c API,
including fetching player data, game archives, and statistics.

Uses the official chess.com Python module for reliable API interactions.
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

import logging
import chessdotcom
from chessdotcom import Client
from player_games_by_basetime_increment import get_player_games_by_basetime_increment
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

from models import PlayerInfo

# Common time controls (base time in seconds, increment in seconds)
TIME_CONTROLS = [(180,0), (600,0), (60,0), (300,0), (180,1), (180,2)]


logger = logging.getLogger(__name__)


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
                    logger.warning("No response for title %s", title)
                continue
                
            data = response.json
            if not data or "players" not in data:
                if verbose:
                    logger.warning("No players found for title %s", title)
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
                logger.warning("Error fetching title %s: %s", title, e, exc_info=True)
            continue
    
    return players

time_out = 7  # seconds

def fetch_games_by_basetime_increment(
    username: str, 
    basetime: int, 
    increment: int,
    start_time: int,
    end_time: int
) -> List[dict]:
    """
    Fetch all games for a player by specific basetime and increment within time window.
    
    Args:
        username: Chess.com username
        basetime: Base time in seconds
        increment: Increment in seconds
        start_time: Window start timestamp
        end_time: Window end timestamp
        
    Returns:
        List of game dictionaries filtered by time window and rated status
    """
    try:
        # The helper does not accept a timeout argument; run it in a thread and enforce a 10s timeout
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(get_player_games_by_basetime_increment, username, basetime, increment)
            try:
                response = future.result(timeout=time_out)
            except FutureTimeoutError:
                future.cancel()
                logger.error(
                    f"Timeout fetching games for {username} with {basetime}+{increment} after {time_out}s"
                )
                return []

        if not response or not hasattr(response, 'games'):
            return []

        included_rules = ['chess', 'chess960']

        # Convert games to dictionary format and apply filters
        games = []
        for game in response.games:
            # Filter by rules
            if game.rules not in included_rules:
                continue
            
            # Filter by rated status - only include rated games
            if not game.rated:
                continue
            
            # Filter by time window
            if not isinstance(game.end_time, int) or not (start_time <= game.end_time <= end_time):
                continue
            
            game_dict = {
                'url': game.url,
                'pgn': game.pgn,
                'time_control': game.time_control,
                #'start_time': game.start_time, #live increment does not have start_time
                'end_time': game.end_time,
                'rules': game.rules,
                'time_class': game.time_class,
                'fen': game.fen,
                'rated': game.rated,
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
    except Exception as e:
        #logger.error(f"Error fetching games for {username} with {basetime}+{increment}: {e}", exc_info=True)
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


time_controls_count = {}

def fetch_games_in_window(
    username: str,
    start_time: int,
    end_time: int
) -> List[dict]:
    """
    Fetch all games for a player within the specified time window.
    Uses get_player_games_by_basetime_increment for each time control.
    
    Args:
        username: Chess.com username
        start_time: Window start timestamp
        end_time: Window end timestamp
        
    Returns:
        List of game dictionaries sorted by end_time, filtered for rated games only
    """
    all_games = []
    
    # Fetch games for each time control
    for basetime, increment in TIME_CONTROLS:
        games = fetch_games_by_basetime_increment(username, basetime, increment, start_time, end_time)
        all_games.extend(games)
        
        # Update time controls count for tracking
        for game in games:
            time_control = game.get("time_control")
            if time_control:
                time_controls_count[time_control] = time_controls_count.get(time_control, 0) + 1
    
    #deduplicate games by URL
    seen_urls = set()
    deduplicated_games = []
    for game in all_games:
        url = game.get("url")
        if url and url not in seen_urls:
            seen_urls.add(url)
            deduplicated_games.append(game)
        
    # Sort by end_time to ensure chronological order
    deduplicated_games.sort(key=lambda g: g.get("end_time", 0))

    return deduplicated_games


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
