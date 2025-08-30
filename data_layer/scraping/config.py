"""
Configuration constants for the Interesting Chess data scraper.

This module contains all the configuration constants used throughout the application,
including API endpoints, thresholds, and default values.
"""

from typing import List, Tuple

# Chess.com Public API base URL
PUBAPI = "https://api.chess.com/pub"

# Available chess titles in order of preference (highest first)
TITLE_ABBREVS = ["GM", "WGM", "IM", "WIM", "FM", "WFM", "NM", "WNM", "CM", "WCM"]

# Probability thresholds for classifying interesting streaks
# Format: (label, decimal_probability)
THRESHOLDS: List[Tuple[str, float]] = [
    ("≤0.01%", 0.0001),
    ("≤0.1%",  0.001),
    ("≤1%",    0.01),
    ("≤5%",    0.05),
]

# Title ranking for display ordering (lower number = higher rank)
TITLE_RANK = {t: i for i, t in enumerate(TITLE_ABBREVS, start=1)}

# Default sleep time between API requests (seconds)
DEFAULT_SLEEP = 0.25

# HTTP request configuration
DEFAULT_TIMEOUT = 20
DEFAULT_RETRIES = 3

# Glicko rating system constants
GLICKO_SCALE = 173.7178  # Conversion factor between Glicko and standard rating scales
GLICKO_BASE_RATING = 1500  # Base rating in Glicko system
ELO_K_FACTOR = 400  # K-factor for Elo probability calculations
