# Interesting Chess Data Scraper

A modular Python application that analyzes Chess.com titled players to identify statistically interesting consecutive win streaks. This tool fetches player data, calculates win probabilities using Glicko/Elo rating systems, and outputs JSON data for frontend consumption.

## Features

- **Modular Architecture**: Clean separation of concerns across multiple modules
- **Rating-Based Probability**: Uses Glicko rating system with RD (rating deviation) when available, falls back to Elo
- **Statistical Analysis**: Identifies streaks with very low probability of occurrence (≤5%, ≤1%, ≤0.1%, ≤0.01%)
- **Rate-Limited API Client**: Respects Chess.com API guidelines with serial requests and proper backoff
- **Docker Support**: Ready for deployment on AWS Batch or other container platforms
- **Comprehensive Logging**: Detailed progress tracking and error handling

## Project Structure

```
scraping/
├── __init__.py              # Package initialization
├── main.py                  # Main application entry point
├── config.py                # Configuration constants
├── models.py                # Data classes and models
├── http_client.py           # Chess.com API HTTP client
├── chess_api.py             # Chess.com API interaction functions
├── probability.py           # Rating probability calculations
├── streak_analyzer.py       # Game analysis and streak detection
├── requirements.txt         # Python dependencies
├── Dockerfile              # Container configuration
├── .dockerignore           # Docker ignore rules
└── README.md               # This file
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

### Docker

1. **Build the Docker image:**
   ```bash
   docker build -t interesting-chess-scraper .
   ```

2. **Run with Docker:**
   ```bash
   docker run -v $(pwd)/data:/app/data \
     -e USERNAME="your_username" \
     -e EMAIL="you@example.com" \
     interesting-chess-scraper --days 30
   ```

## Usage

### Command Line Interface

```bash
python main.py [OPTIONS]
```

**Optional:**
- `--days`: Analysis window in days (default: 30)
- `--out`: Output directory (default: ./data)
- `--sleep`: Seconds between API requests (default: 0.25)
- `--titles`: Comma-separated chess titles (default: all titled players)
- `--limit-players`: Limit number of players for testing
- `--verbose`: Enable detailed logging

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
# Basic usage - analyze last 30 days for all titled players
python main.py

# Quick test with fewer players
python main.py --days 7 --titles "GM,IM" --limit-players 50 --verbose

# Production run with custom output
python main.py --days 60 --out /path/to/output --sleep 0.5
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

## Output Format

The application generates two JSON files:

### `interesting_streaks.json`

Array of streak objects with this structure:

```json
{
  "player": {
    "username": "chess_player",
    "title": "GM",
    "avatar": "https://images.chesscomfiles.com/..."
  },
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
        "p_win": 0.62,
        "url": "https://www.chess.com/game/live/12345"
      }
    ]
  }
}
```

### `summary.json`

Aggregate statistics:

```json
{
  "window_days": 30,
  "players_processed": 1250,
  "streaks_found": 42,
  "counts_by_threshold": {
    "≤5%": 15,
    "≤1%": 8,
    "≤0.1%": 3,
    "≤0.01%": 1
  },
  "generated_at": 1693612800
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

## AWS Batch Deployment

### Building for AWS

1. **Build and tag the image:**
   ```bash
   docker build -t your-registry/interesting-chess-scraper:latest .
   ```

2. **Push to ECR (or your registry):**
   ```bash
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin your-account.dkr.ecr.us-east-1.amazonaws.com
   docker tag interesting-chess-scraper:latest your-account.dkr.ecr.us-east-1.amazonaws.com/interesting-chess-scraper:latest
   docker push your-account.dkr.ecr.us-east-1.amazonaws.com/interesting-chess-scraper:latest
   ```

### Job Definition Example

```json
{
  "jobDefinitionName": "interesting-chess-scraper",
  "type": "container",
  "containerProperties": {
    "image": "your-account.dkr.ecr.us-east-1.amazonaws.com/interesting-chess-scraper:latest",
    "vcpus": 1,
    "memory": 2048,
    "jobRoleArn": "arn:aws:iam::account:role/BatchJobRole",
    "environment": [
      {"name": "APP_NAME", "value": "interesting-chess"},
      {"name": "VERSION", "value": "1.0"},
      {"name": "USERNAME", "value": "production"},
      {"name": "EMAIL", "value": "admin@yoursite.com"}
    ],
    "mountPoints": [
      {
        "sourceVolume": "output",
        "containerPath": "/app/data",
        "readOnly": false
      }
    ],
    "volumes": [
      {
        "name": "output",
        "host": {"sourcePath": "/tmp/chess-data"}
      }
    ]
  }
}
```

### Submitting Jobs

```bash
aws batch submit-job \
  --job-name "chess-scraper-$(date +%Y%m%d)" \
  --job-queue "your-job-queue" \
  --job-definition "interesting-chess-scraper" \
  --parameters "days=30,titles=GM,IM,FM"
```

## API Guidelines Compliance

This application strictly follows Chess.com's Public API guidelines:

- **Serial Access**: All requests are made sequentially, never in parallel
- **Rate Limiting**: Configurable delays between requests (default: 0.25s)
- **User-Agent**: Proper identification with contact information
- **Backoff Strategy**: Exponential backoff for rate-limited responses (429)
- **Error Handling**: Graceful handling of temporary failures

## Development

### Module Overview

- **`config.py`**: Constants and configuration values
- **`models.py`**: Data classes for type safety and structure
- **`http_client.py`**: Rate-limited HTTP client for Chess.com API
- **`chess_api.py`**: High-level API interaction functions
- **`probability.py`**: Statistical probability calculations
- **`streak_analyzer.py`**: Core game analysis and streak detection logic
- **`main.py`**: Application orchestration and CLI interface

### Testing

```bash
# Test with a small subset
APP_NAME="test-chess" VERSION="0.1" USERNAME="test-user" EMAIL="test@example.com" \
python main.py --days 3 --titles "GM" --limit-players 10 --verbose

# Validate Docker build
docker build -t test-scraper .
docker run test-scraper --help
```

### Adding New Features

1. **New probability models**: Extend `probability.py`
2. **Different APIs**: Create new modules following the pattern
3. **Output formats**: Modify serialization functions in `main.py`
4. **Analysis algorithms**: Extend `streak_analyzer.py`

## Troubleshooting

### Common Issues

1. **Rate Limiting (429 errors)**:
   - Increase `--sleep` parameter
   - Check your network connection
   - Verify you're not running multiple instances

2. **Missing RD data**:
   - This is normal; the application falls back to Elo calculations
   - Some players/modes don't have RD data available

3. **Memory usage**:
   - For large datasets, consider processing in smaller batches
   - Use `--limit-players` for testing

4. **Docker permissions**:
   - Ensure output directory is writable
   - Check user permissions in container

### Performance Tips

- Use `--limit-players` for testing
- Adjust `--sleep` based on your use case (faster = higher rate limit risk)
- Monitor memory usage for large datasets
- Consider running analysis for shorter time windows

## License

[Add your license information here]

## Contributing

[Add contribution guidelines here]

## Contact

For questions about this scraper, contact the development team.
For Chess.com API questions, see their [official documentation](https://www.chess.com/news/view/published-data-api).
