# Interesting Chess Data Scraper

A modular Python application that analyzes Chess.com titled players to identify statistically interesting consecutive win streaks. This tool fetches player data using the [`chess.com` Python module](https://github.com/sarartur/chess.com), calculates win probabilities using Glicko/Elo rating systems, and outputs JSON data for frontend consumption.

## Features

- **Official Chess.com API Integration**: Uses the official `chess.com` Python module for reliable API interactions
- **Modular Architecture**: Clean separation of concerns across multiple modules  
- **Time Control Filtering**: Analyzes specific time controls (3+0, 10+0, 1+0, 5+0, 3+1, 3+2) for more focused analysis
- **Rating-Based Probability**: Uses Glicko rating system with RD (rating deviation) when available, falls back to Elo
- **Statistical Analysis**: Identifies streaks with very low probability of occurrence (≤5%, ≤1%, ≤0.1%, ≤0.01%)
- **Automatic Rate Limiting**: Built-in rate limiting and retry logic handled by the official module
- **AWS S3 Integration**: Optional automatic upload of results to Amazon S3
- **Progress Tracking**: Detailed progress reporting with ETA calculations
- **Comprehensive Logging**: Detailed progress tracking and error handling

## Project Structure

```
scraping/
├── __init__.py                                    # Package initialization
├── main.py                                        # Main application entry point
├── config.py                                      # Configuration constants
├── models.py                                      # Data classes and models
├── chess_api.py                                   # Chess.com API interaction using official module
├── probability.py                                 # Rating probability calculations
├── streak_analyzer.py                             # Game analysis and streak detection
├── player_games_by_basetime_increment.py          # Specialized game fetching by time control
├── http_client.py                                 # HTTP client utilities
├── requirements.txt                               # Python dependencies (includes chess.com module)
├── data/                                          # Output directory for results
│   └── results.json                              # Generated analysis results
└── README.md                                      # This file
```

## Installation

### Local Development

1. **Clone the repository:**

   ```bash
   git clone <repository-url>
   cd ChessCoach/data_layer/scraping
   ```

2. **Create a virtual environment:**

   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate     # Windows
   ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

   This will install:
   - `chess.com==3.11.1` - Official Chess.com API client
   - `requests==2.32.5` - HTTP client (used by chess.com module)
   - `python-dateutil==2.9.0.post0` - Date parsing utilities
   - `boto3==1.40.23` - AWS SDK for S3 uploads (optional)
   - `botocore==1.40.23` - AWS core library

## Usage

### Command Line Interface

```bash
python main.py [OPTIONS]
```

**Optional Arguments:**

- `--days`: Analysis window in days (default: 30)
- `--out`: Output directory (default: ./data)
- `--titles`: Comma-separated chess titles (default: GM,WGM,IM,WIM)
- `--limit-players`: Limit number of players for testing
- `--verbose`: Enable detailed logging (default: True)

**Examples:**

Set environment variables first:

```bash
export APP_NAME="interesting-chess"
export VERSION="1.0"
export USERNAME="your_username"
export EMAIL="you@example.com"
```

Then run:

```bash
# Basic usage - analyze last 30 days for default titled players (GM,WGM,IM,WIM)
python main.py

# Quick test with fewer players
python main.py --days 7 --titles "GM,IM" --limit-players 50 --verbose

# Production run with custom output
python main.py --days 60 --out /path/to/output
```

### Environment Variables

You can set user agent information via environment variables:

```bash
export APP_NAME="interesting-chess"
export VERSION="1.0"
export USERNAME="your_username"
export EMAIL="you@example.com"
python main.py --days 30
```

The user agent will be formatted as: `APP_NAME/VERSION (username: USERNAME; contact: EMAIL)`

Defaults if not set:
- `APP_NAME`: "interesting-chess"
- `VERSION`: "0.0"
- `USERNAME`: "alienoscar"
- `EMAIL`: "garcia.oscar1729@gmail.com"

#### Optional S3 Upload

If you want the generated `results.json` to be uploaded to Amazon S3 automatically, set the `S3_LOCATION` environment variable. If not set, the upload is skipped.

- `S3_LOCATION` must be in the form `s3://<bucket>/<key>` or `s3://<bucket>/<prefix>/` (if a prefix is provided, the file name `results.json` is appended).
- AWS authentication follows standard boto3 credential resolution (env vars, shared credentials file, IAM role, etc.). You may also set `AWS_REGION` if needed.

Examples:

```bash
export S3_LOCATION="s3://my-bucket/interesting-chess/"
export AWS_REGION="us-east-1"  # optional, if not already configured
python main.py --days 7 --out ./data
```

With environment file:

```env
S3_LOCATION=s3://my-bucket/interesting-chess/
AWS_REGION=us-east-1
```

## Output Format

The application generates a single `results.json` file with four main sections:

### Structure Overview

```json
{
  "summary": { ... },
  "players": { ... },
  "interesting_streaks": [ ... ],
  "time_controls_count": { ... }
}
```

### Summary Section

Contains aggregate statistics about the analysis run:

```json
{
  "summary": {
    "window_days": 30,
    "players_processed": 1250,
    "games_processed": 45203,
    "streaks_found": 42,
    "counts_by_threshold": {
      "≤5%": 15,
      "≤1%": 8,
      "≤0.1%": 3,
      "≤0.01%": 1
    },
    "generated_at": 1693612800
  }
}
```

### Players Section

Dictionary of all processed players with their information:

```json
{
  "players": {
    "chess_player": {
      "username": "chess_player",
      "title": "GM",
      "avatar": "https://images.chesscomfiles.com/...",
      "max_rating": 2750,
      "country": "US"
    },
    "another_player": {
      "username": "another_player",
      "title": "IM",
      "avatar": null,
      "max_rating": 2650,
      "country": "GB"
    }
  }
}
```

### Interesting Streaks Section

Array of streak objects with detailed information:

```json
{
  "interesting_streaks": [
    {
      "username": "chess_player",
      "player_title": "GM",
      "player_max_rating": 2750,
      "streak": {
        "length": 8,
        "prob": 0.0023,
        "threshold": "≤0.1%",
        "start_time": 1693440000,
        "end_time": 1693526400,
        "games": [
          {
            "end_time": 1693440000,
            "rules": "chess",
            "time_class": "blitz",
            "opponent": {
              "username": "opponent_name",
              "rating": 2650
            },
            "winner_rating": 2740,
            "estimated_winner_rating": 2735,
            "estimated_loser_rating": 2645,
            "p_win": 0.62,
            "url": "https://www.chess.com/game/live/12345"
          }
        ]
      }
    }
  ]
}
```

### Time Controls Count Section

Statistics about the frequency of different time controls encountered:

```json
{
  "time_controls_count": {
    "180": 15420,
    "600": 12850,
    "60": 8930,
    "300": 5640,
    "180+1": 1890,
    "180+2": 473
  }
}
```

## Probability Calculations

The application uses sophisticated rating-based probability calculations:

### Glicko System (Preferred)

When rating deviation (RD) is available:

- Converts ratings to μ-scale: `μ = (R - 1500) / 173.7178`
- Converts RD to φ-scale: `φ = RD / 173.7178`
- Calculates uncertainty factor: `g(φ) = 1 / √(1 + 3φ²/π²)`
- Expected win probability: `E = 1 / (1 + exp(-g(φ_opp) × (μ_winner - μ_loser)))`

### Elo System (Fallback)

When RD is unavailable:

- Classic Elo expectation: `E = 1 / (1 + 10^(-(R_winner - R_loser)/400))`

### Streak Probability

- Combined probability = product of individual game probabilities
- Uses log-space arithmetic to prevent numerical underflow
- Classifies streaks into rarity thresholds

## API Guidelines Compliance

This application strictly follows Chess.com's Public API guidelines by using the official `chess.com` Python module:

- **Official Module**: Uses Chess.com's recommended API client
- **Automatic Rate Limiting**: Built-in rate limiting handled by the module
- **Serial Access**: All requests are made sequentially, never in parallel
- **User-Agent**: Proper identification with contact information
- **Backoff Strategy**: Exponential backoff for rate-limited responses (429)
- **Error Handling**: Graceful handling of temporary failures with retry logic

## Development

### Module Overview

- **`config.py`**: Constants and configuration values (thresholds, titles, time controls)
- **`models.py`**: Data classes for type safety and structure (PlayerInfo, GameView, Streak)
- **`chess_api.py`**: High-level API interaction using official chess.com module
- **`probability.py`**: Statistical probability calculations for Glicko/Elo systems
- **`streak_analyzer.py`**: Core game analysis and streak detection logic
- **`player_games_by_basetime_increment.py`**: Specialized fetching for specific time controls
- **`http_client.py`**: HTTP client utilities and helper functions
- **`main.py`**: Application orchestration, CLI interface, and S3 upload functionality

### Testing

```bash
# Test with a small subset
APP_NAME="test-chess" VERSION="0.1" USERNAME="test-user" EMAIL="test@example.com" \
python main.py --days 3 --titles "GM" --limit-players 10 --verbose

# Test chess.com module integration
python -c "
from chess_api import setup_chess_client, fetch_titled_players
setup_chess_client('TestApp/1.0 (contact: test@example.com)')
players = fetch_titled_players(['GM'], verbose=False)
print(f'Found {len(players)} GM players')
"
```

### Adding New Features

1. **New probability models**: Extend `probability.py`
2. **Different time controls**: Modify `TIME_CONTROLS` in `chess_api.py`
3. **Output formats**: Modify serialization functions in `main.py`
4. **Analysis algorithms**: Extend `streak_analyzer.py`
5. **New data sources**: Create new modules following the `chess_api.py` pattern

## Troubleshooting

### Common Issues

1. **Rate Limiting (429 errors)**:
   - The chess.com module handles this automatically with exponential backoff
   - Check your network connection
   - Verify you're not running multiple instances

2. **Missing RD data**:
   - This is normal; the application falls back to Elo calculations
   - Some players/modes don't have RD data available

3. **Memory usage**:
   - For large datasets, consider processing in smaller batches
   - Use `--limit-players` for testing

4. **Import errors**:
   - Ensure `chess.com` module is installed: `pip install chess.com==3.11.1`
   - Check that all dependencies from requirements.txt are installed

5. **S3 Upload failures**:
   - Verify AWS credentials are properly configured
   - Check S3_LOCATION format (must start with s3://)
   - Ensure bucket exists and you have write permissions

6. **Timeout issues**:
   - Individual game fetches timeout after 7 seconds
   - Increase timeout in `chess_api.py` if needed for slow connections

### Performance Tips

- Use `--limit-players` for testing and development
- The chess.com module handles rate limiting automatically
- Monitor memory usage for large datasets (many players over long time periods)
- Consider running analysis for shorter time windows initially
- Progress is logged every 10 players with ETA calculations when `--verbose` is enabled
- Time controls are processed in parallel but rate-limited per the API guidelines

## License

[Add your license information here]

## Contributing

[Add contribution guidelines here]

## Contact

For questions about this scraper, contact the development team.
For Chess.com API questions, see their [official documentation](https://www.chess.com/news/view/published-data-api).
