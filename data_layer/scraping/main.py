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
import logging
import os
import sys
import time
from urllib.parse import urlparse
from typing import Dict

from chess_api import (
    create_player_info,
    fetch_games_in_window,
    fetch_player_profile,
    fetch_player_stats,
    fetch_titled_players,
    parse_time_window,
    setup_chess_client,
)
from config import THRESHOLDS, TITLE_ABBREVS, RELEVANT_TITLES
from streak_analyzer import analyze_player_streaks
import boto3

logger = logging.getLogger(__name__)

def _upload_results_to_s3(local_path: str, s3_location: str, verbose: bool = True) -> None:
    """
    Upload the results file to an S3 location if configured.

    S3_LOCATION must be of the form s3://<bucket>/<key or prefix>/
    If a prefix (ending with "/") is provided, the basename of local_path will be appended.
    """
    try:
        parsed = urlparse(s3_location)
        if parsed.scheme != "s3" or not parsed.netloc:
            raise ValueError("S3_LOCATION must be like s3://bucket/path or s3://bucket/path/")

        bucket = parsed.netloc
        key = parsed.path.lstrip("/")
        if not key or key.endswith("/"):
            # treat as prefix
            key = (key or "") + os.path.basename(local_path)

        s3 = boto3.client("s3")
        if verbose:
            logger.info("Uploading %s to s3://%s/%s", local_path, bucket, key)
        s3.upload_file(local_path, bucket, key)
        if verbose:
            logger.info("Uploaded to s3://%s/%s", bucket, key)
    except Exception as e:  # broaden to catch import and boto errors
        logger.warning("Skipped S3 upload due to error: %s", e, exc_info=True)

def setup_user_agent() -> str:
    """
    Create a proper User-Agent string for Chess.com API requests.
    Uses the format: APP_NAME/VERSION (username: USERNAME; contact: EMAIL)
    
    Returns:
        Formatted User-Agent string
    """
    app_name = os.environ.get("APP_NAME", "interesting-chess")
    version = os.environ.get("VERSION", "0.0")
    username = os.environ.get("USERNAME", "alienoscar")
    email = os.environ.get("EMAIL", "garcia.oscar1729@gmail.com")

    return f"{app_name}/{version} (username: {username}; contact: {email})"


def serialize_streak_for_output(streak):
    """Convert a Streak object to JSON-serializable format."""
    return {
        "username": streak.player.username,
        "player_title": streak.player.title,
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
        "--titles", type=str, default=",".join(RELEVANT_TITLES),
        help="Comma-separated titles to include"
    )
    parser.add_argument(
        "--limit-players", type=int, default=None,
        help="Limit number of players for testing"
    )
    parser.add_argument(
        "--verbose", action="store_true", default=True,
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()

    # Configure logging early using verbose flag
    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    # Setup output directory
    os.makedirs(args.out, exist_ok=True)

    # Setup chess.com client
    user_agent = setup_user_agent()
    setup_chess_client(user_agent)

    # Parse time window
    start_time, end_time = parse_time_window(args.days)
    if args.verbose:
        from datetime import datetime, timezone
        start_dt = datetime.fromtimestamp(start_time, tz=timezone.utc)
        end_dt = datetime.fromtimestamp(end_time, tz=timezone.utc)
        logger.info("Time window: %s -> %s", start_dt, end_dt)

    # Fetch titled players
    title_list = [title.strip().upper() for title in args.titles.split(",") if title.strip()]
    titled_players = fetch_titled_players(title_list, verbose=args.verbose)
    player_usernames = sorted(titled_players.keys())
    
    if args.limit_players is not None and type(args.limit_players) is int:
        if args.limit_players > 0:
            player_usernames = player_usernames[:args.limit_players]

    if args.verbose:
        logger.info("Processing %d players", len(player_usernames))

    # Process each player
    all_streaks = []
    stats_cache: Dict[str, dict] = {}
    processed_count = 0
    total_games_processed = 0
    players_data = {}
    # total players to process (used for progress / ETA)
    total_players = len(player_usernames)
    start_time_main = time.time()

    def _format_duration(s: float) -> str:
        """Format seconds as H:MM:SS"""
        s = int(round(s))
        hours = s // 3600
        minutes = (s % 3600) // 60
        seconds = s % 60
        if hours:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        return f"{minutes}:{seconds:02d}"

    def emit_progress_if_needed(processed: int) -> None:
        """Emit progress logs every 10 players when verbose is enabled.

        Logs: processed/total, progress %, elapsed time, and ETA (derived from
        average time per processed player).
        """
        if not args.verbose or processed == 0:
            return
        if processed % 10 != 0:
            return

        elapsed = time.time() - start_time_main
        avg_per_player = elapsed / processed if processed > 0 else 0.0
        remaining = max(0, total_players - processed)
        eta_seconds = remaining * avg_per_player

        percent = (processed / total_players * 100) if total_players > 0 else 0.0

        logs_string = (
            f"[PROGRESS] Processed {processed}/{total_players} players({percent:.1f}%)\n"
            f"- elapsed: {_format_duration(elapsed)}\n"
            f"- ETA: {_format_duration(eta_seconds)}"
        )

        logger.info(logs_string)

    for username in player_usernames:
        try:
            # Get player info
            title = titled_players.get(username)
            profile = fetch_player_profile(username)
            stats = fetch_player_stats(username)
            
            player_info = create_player_info(username, title, profile, stats)
            
            # Store player data
            players_data[username] = {
                "username": player_info.username,
                "title": player_info.title,
                "avatar": player_info.avatar,
                "max_rating": player_info.max_rating,
                "country": player_info.country
            }
            
            # Get games in time window
            games = fetch_games_in_window(username, start_time, end_time)
            if not games:
                processed_count += 1
                emit_progress_if_needed(processed_count)
                continue

            # Count games processed
            total_games_processed += len(games)

            # Analyze streaks
            streaks = analyze_player_streaks(
                player_info, games, stats_cache, THRESHOLDS, args.verbose
            )
            all_streaks.extend(streaks)
            processed_count += 1
            emit_progress_if_needed(processed_count)

            if args.verbose and (processed_count % 25 == 0):
                processed_string = (
                    f"[PROGRESS] Processed {processed_count}/{len(player_usernames)} players; "
                    f"found {len(all_streaks)} interesting streaks so far; "
                    f"processed {total_games_processed} games"
                )
                logger.info(processed_string)

        except Exception as e:
            logger.exception("Failed to process player %s: %s", username, e)
            processed_count += 1
            emit_progress_if_needed(processed_count)
            continue

    # Sort streaks: highest rating first, then rarest probability, then longest
    def streak_sort_key(streak):
        rating = streak.player.max_rating or -1
        return (-rating, streak.p_combined, -streak.length, streak.player.username)

    all_streaks.sort(key=streak_sort_key)

    # Serialize results
    output_streaks = [serialize_streak_for_output(streak) for streak in all_streaks]
    
    # Additional sort for output to ensure consistent ordering by player_max_rating first
    # Use a safe key that handles None values for player_max_rating and streak.prob
    def _output_sort_key(streak):
        # Keep behavior consistent with streak_sort_key above: treat missing rating as -1
        rating = streak.get("player_max_rating")
        if rating is None:
            rating = -1

        # For probability, smaller is rarer — missing probability should sort last
        prob = None
        if isinstance(streak.get("streak"), dict):
            prob = streak["streak"].get("prob")
        if prob is None:
            prob = 10 # larger than any realistic probability (0 < p <= 1)

        return (-rating, prob)

    output_streaks.sort(key=_output_sort_key)
    
    # Create summary with games count
    summary = {
        "window_days": args.days,
        "players_processed": processed_count,
        "games_processed": total_games_processed,
        "streaks_found": len(all_streaks),
        "counts_by_threshold": calculate_threshold_counts(all_streaks),
        "generated_at": int(time.time())
    }
    
    # Create combined results file with three levels
    results = {
        "summary": summary,
        "players": players_data,
        "interesting_streaks": output_streaks
    }
    
    results_file = os.path.join(args.out, "results.json")
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, separators=(",", ":"), indent=2)

    # Optional: upload to S3 if configured
    s3_location = os.environ.get("S3_LOCATION")
    if s3_location:
        _upload_results_to_s3(results_file, s3_location, verbose=args.verbose)
    else:
        if args.verbose:
            logger.info("S3_LOCATION not set; skipping S3 upload")

    # Print results
    logger.info("Processed %d players", processed_count)
    logger.info("Processed %d games", total_games_processed)
    logger.info("Found %d interesting streaks", len(all_streaks))
    logger.info("Results written to: %s", results_file)


if __name__ == "__main__":
    main()
