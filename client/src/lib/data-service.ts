import { type Player, type WinStreak, type Game, type StreakWithPlayer, type AnalyticsData } from "@shared/schema";
import resultsData from "@/assets/results.json";

// Types for the JSON data structure
interface JsonPlayer {
  username: string;
  title: string;
  avatar: string | null;
  max_rating: number;
  country: string;
}

interface JsonGame {
  end_time: number;
  rules: string;
  time_class: string;
  opponent: {
    username: string;
    rating: number;
  };
  winner_rating: number;
  p_win: number;
  url: string;
}

interface JsonStreak {
  username: string;
  player_title: string;
  player_max_rating: number;
  streak: {
    length: number;
    prob: number;
    threshold: string;
    start_time: number;
    end_time: number;
    games: JsonGame[];
  };
}

interface JsonData {
  summary: {
    window_days: number;
    players_processed: number;
    games_processed: number;
    streaks_found: number;
    counts_by_threshold: {
      [key: string]: number;
    };
    generated_at: number;
  };
  players: { [username: string]: JsonPlayer };
  interesting_streaks: JsonStreak[];
}

class DataService {
  private data: JsonData;
  private processedPlayers: Map<string, Player> = new Map();
  private processedStreaks: StreakWithPlayer[] = [];

  constructor() {
    this.data = resultsData as JsonData;
    this.processData();
  }

  private processData() {
    // Process each streak and create the normalized data structures
    for (const jsonStreak of this.data.interesting_streaks) {
      const username = jsonStreak.username;
      const playerData = this.data.players[username];
      
      if (!playerData) continue;

      // Create or get player
      let player = this.processedPlayers.get(username);
      if (!player) {
        player = {
          id: `player-${username}`,
          username: playerData.username,
          title: playerData.title,
          rating: playerData.max_rating,
          ratingCategory: jsonStreak.streak.games[0]?.time_class || "blitz",
          avatarUrl: playerData.avatar,
          country: playerData.country,
          profileUrl: `https://chess.com/member/${playerData.username}`
        };
        this.processedPlayers.set(username, player);
      }

      // Create games for this streak
      const games: Game[] = jsonStreak.streak.games.map((jsonGame, index) => ({
        id: `game-${username}-${index}`,
        streakId: `streak-${username}`,
        opponentUsername: jsonGame.opponent.username,
        opponentRating: jsonGame.opponent.rating,
        winProbability: jsonGame.p_win * 100, // Convert to percentage
        gameUrl: jsonGame.url,
        gameDate: new Date(jsonGame.end_time * 1000),
        result: "win" as const
      }));

      // Create streak with player and games
      const streak: StreakWithPlayer = {
        id: `streak-${username}`,
        playerId: player.id,
        streakLength: jsonStreak.streak.length,
        probability: jsonStreak.streak.prob * 100, // Convert to percentage
        probabilityTier: this.mapThresholdToTier(jsonStreak.streak.threshold),
        startDate: new Date(jsonStreak.streak.start_time * 1000),
        endDate: new Date(jsonStreak.streak.end_time * 1000),
        averageOpponentRating: this.calculateAverageOpponentRating(jsonStreak.streak.games),
        createdAt: null,
        player,
        games: games.map(game => ({
          ...game,
          gameDate: new Date(game.gameDate)
        }))
      };

      this.processedStreaks.push(streak);
    }

    // Sort streaks by probability (most extreme first)
    this.processedStreaks.sort((a, b) => a.probability - b.probability);
  }

  private mapThresholdToTier(threshold: string): 'extreme' | 'high' | 'moderate' | 'low' {
    switch (threshold) {
      case "≤0.01%": return "extreme";
      case "≤0.1%": return "high";
      case "≤1%": return "moderate";
      case "≤5%": return "low";
      default: return "low";
    }
  }

  private calculateAverageOpponentRating(games: JsonGame[]): number {
    if (games.length === 0) return 0;
    const sum = games.reduce((acc, game) => acc + game.opponent.rating, 0);
    return Math.round(sum / games.length);
  }

  // Public methods that match the original API
  getStreaksWithPlayer(): StreakWithPlayer[] {
    return this.processedStreaks;
  }

  getAnalyticsData(): AnalyticsData {
    const streaks = this.processedStreaks;
    const totalStreaks = streaks.length || this.data.summary.streaks_found || 0;
    const averageStreakLength = totalStreaks > 0 
      ? streaks.reduce((sum, streak) => sum + streak.streakLength, 0) / totalStreaks 
      : 0;
    
    // Use data from JSON file for accurate counts
    const counts = this.data.summary.counts_by_threshold || {};
    const probabilityDistribution = {
      extreme: counts["≤0.01%"] || 0,
      high: counts["≤0.1%"] || 0,
      moderate: counts["≤1%"] || 0,
      low: counts["≤5%"] || 0,
    };

    const extremeCount = probabilityDistribution.extreme;
    const highestRating = streaks.length > 0 
      ? Math.max(...streaks.map(s => s.player.rating)) 
      : 0;
    const topStreaks = streaks.slice(0, 3);

    return {
      totalStreaks,
      averageStreakLength: Math.round(averageStreakLength * 10) / 10,
      extremeCount,
      highestRating,
      probabilityDistribution,
      topStreaks
    };
  }

  getSummaryData() {
    return this.data.summary;
  }

  getStreakById(id: string): StreakWithPlayer | undefined {
    return this.processedStreaks.find(streak => streak.id === id);
  }
}

// Create and export a singleton instance
export const dataService = new DataService();