#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Interesting Chess – Chess.com Data Scraper

A modular data scraper that analyzes Chess.com titled players to identify
statistically interesting consecutive win streaks.

This application:
1. Fetches titled players from Chess.com's public API
2. Analyzes their recent games to find consecutive win streaks  
3. Calculates the statistical probability of each streak using Glicko/Elo ratings
4. Outputs interesting streaks (those with very low probabilities) as JSON

The output can be consumed by frontend applications to display remarkable
chess achievements in an engaging way.

Usage:
    python main.py --days 30 --out ./data --contact "Your Name <you@example.com>"

For more options, run: python main.py --help
"""

import argparse
import json
import os
import sys
import time
from typing import Dict, List

from chess_api import (
    create_player_info,
    fetch_games_in_window,
    fetch_player_profile,
    fetch_player_stats,
    fetch_titled_players,
    parse_time_window,
)
from config import DEFAULT_SLEEP, THRESHOLDS, TITLE_ABBREVS
from http_client import ChessComHttpClient
from models import StreakSummary
from streak_analyzer import analyze_player_streaks

def setup_user_agent(contact_info: str) -> str:
    """
    Create a proper User-Agent string for Chess.com API requests.
    
    Args:
        contact_info: Contact information to include in User-Agent
        
    Returns:
        Formatted User-Agent string
    """
    if contact_info.strip():
        return f"interesting-chess/1.0 ({contact_info.strip()})"
    else:
        print("[WARN] No contact info set. Set --contact or IC_USER_AGENT to be a good API citizen.", 
              file=sys.stderr)
        return "interesting-chess/1.0 (contact: set IC_USER_AGENT env or --contact)"


def serialize_streak_for_output(streak):
    """Convert a Streak object to JSON-serializable format."""
    return {
        "player": {
            "username": streak.player.username,
            "title": streak.player.title,
            "avatar": streak.player.avatar
        },
        "player_max_rating": streak.player.max_rating,
        "streak": {
            "length": streak.length,
            "prob": streak.p_combined,
            "threshold": streak.threshold_label,
            "start_time": streak.start_time,
            "end_time": streak.end_time,
            "games": [{
                "end_time": game.end_time,
                "rules": game.rules,
                "time_class": game.time_class,
                "opponent": {
                    "username": game.opponent_username, 
                    "rating": game.opponent_rating
                },
                "winner_rating": game.winner_rating,
                "p_win": game.p_win,
                "url": game.url
            } for game in streak.games]
        }
    }


def calculate_threshold_counts(streaks) -> Dict[str, int]:
    """Calculate counts of streaks by threshold category."""
    counts = {"≤5%": 0, "≤1%": 0, "≤0.1%": 0, "≤0.01%": 0}
    
    for streak in streaks:
        label = streak.threshold_label
        if label and label in counts:
            counts[label] += 1
    
    return counts


def main():
    """
    Main application entry point.
    
    Processes command line arguments, fetches data from Chess.com API,
    analyzes games for interesting win streaks, and outputs results.
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Interesting Chess – Chess.com Data Scraper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --days 30 --contact "Your Name <you@example.com>"
  python main.py --days 7 --titles "GM,IM" --limit-players 100 --verbose
        """
    )
    
    parser.add_argument(
        "--days", type=int, default=30,
        help="Window size in days (default: 30)"
    )
    parser.add_argument(
        "--out", type=str, default="./data",
        help="Output directory (default: ./data)"
    )
    parser.add_argument(
        "--sleep", type=float, default=DEFAULT_SLEEP,
        help=f"Sleep seconds between requests (default: {DEFAULT_SLEEP})"
    )
    parser.add_argument(
        "--titles", type=str, default=",".join(TITLE_ABBREVS),
        help="Comma-separated titles to include"
    )
    parser.add_argument(
        "--limit-players", type=int, default=None,
        help="Limit number of players for testing"
    )
    parser.add_argument(
        "--contact", type=str, default=None,
        help='Contact info for User-Agent (e.g., "Your Name <you@example.com>")'
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()

    # Setup output directory
    os.makedirs(args.out, exist_ok=True)

    # Setup HTTP client
    contact = args.contact or os.environ.get("IC_USER_AGENT", "")
    user_agent = setup_user_agent(contact)
    http = ChessComHttpClient(user_agent=user_agent, sleep_s=args.sleep)

    # Parse time window
    start_time, end_time = parse_time_window(args.days)
    if args.verbose:
        from datetime import datetime, timezone
        start_dt = datetime.fromtimestamp(start_time, tz=timezone.utc)
        end_dt = datetime.fromtimestamp(end_time, tz=timezone.utc)
        print(f"[INFO] Time window: {start_dt} -> {end_dt}")

    # Fetch titled players
    title_list = [title.strip().upper() for title in args.titles.split(",") if title.strip()]
    titled_players = fetch_titled_players(http, title_list, verbose=args.verbose)
    player_usernames = sorted(titled_players.keys())
    
    if args.limit_players is not None:
        player_usernames = player_usernames[:args.limit_players]

    if args.verbose:
        print(f"[INFO] Processing {len(player_usernames)} players")

    # Process each player
    all_streaks = []
    stats_cache: Dict[str, dict] = {}
    processed_count = 0

    for username in player_usernames:
        try:
            # Get player info
            title = titled_players.get(username)
            profile = fetch_player_profile(http, username)
            stats = fetch_player_stats(http, username)
            
            player_info = create_player_info(username, title, profile, stats)
            
            # Get games in time window
            games = fetch_games_in_window(http, username, start_time, end_time)
            if not games:
                processed_count += 1
                continue

            # Analyze streaks
            streaks = analyze_player_streaks(
                player_info, games, stats_cache, http, THRESHOLDS, args.verbose
            )
            all_streaks.extend(streaks)
            processed_count += 1

            if args.verbose and (processed_count % 25 == 0):
                print(f"[INFO] Processed {processed_count}/{len(player_usernames)} players; "
                      f"found {len(all_streaks)} interesting streaks so far")

        except Exception as e:
            print(f"[ERROR] Failed to process player {username}: {e}", file=sys.stderr)
            processed_count += 1
            continue

    # Sort streaks: highest rating first, then rarest probability, then longest
    def streak_sort_key(streak):
        rating = streak.player.max_rating or -1
        return (-rating, streak.p_combined, -streak.length, streak.player.username)

    all_streaks.sort(key=streak_sort_key)

    # Serialize results
    output_streaks = [serialize_streak_for_output(streak) for streak in all_streaks]
    
    streaks_file = os.path.join(args.out, "interesting_streaks.json")
    with open(streaks_file, "w", encoding="utf-8") as f:
        json.dump(output_streaks, f, ensure_ascii=False, separators=(",", ":"), indent=2)

    # Create summary
    summary = StreakSummary(
        window_days=args.days,
        players_processed=processed_count,
        streaks_found=len(all_streaks),
        counts_by_threshold=calculate_threshold_counts(all_streaks),
        generated_at=int(time.time())
    )
    
    summary_file = os.path.join(args.out, "summary.json")
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary.__dict__, f, ensure_ascii=False, separators=(",", ":"), indent=2)

    # Print results
    print(f"[DONE] Processed {processed_count} players")
    print(f"[DONE] Found {len(all_streaks)} interesting streaks")
    print(f"[DONE] Output written to: {streaks_file}")
    print(f"[DONE] Summary written to: {summary_file}")


if __name__ == "__main__":
    main()
