import { type Player, type InsertPlayer, type WinStreak, type InsertWinStreak, type Game, type InsertGame, type StreakWithPlayer, type AnalyticsData } from "@shared/schema";
import { randomUUID } from "crypto";
import { readFileSync } from "fs";
import path from "path";

export interface IStorage {
  // Player methods
  getPlayer(id: string): Promise<Player | undefined>;
  getPlayerByUsername(username: string): Promise<Player | undefined>;
  createPlayer(player: InsertPlayer): Promise<Player>;
  getAllPlayers(): Promise<Player[]>;

  // Win streak methods
  getWinStreak(id: string): Promise<WinStreak | undefined>;
  createWinStreak(streak: InsertWinStreak): Promise<WinStreak>;
  getAllWinStreaks(): Promise<WinStreak[]>;
  getStreaksWithPlayer(): Promise<StreakWithPlayer[]>;

  // Game methods
  createGame(game: InsertGame): Promise<Game>;
  getGamesByStreakId(streakId: string): Promise<Game[]>;

  // Analytics
  getAnalyticsData(): Promise<AnalyticsData>;
  
  // Summary data for hero section
  getSummaryData(): any;
}

export class MemStorage implements IStorage {
  private players: Map<string, Player>;
  private winStreaks: Map<string, WinStreak>;
  private games: Map<string, Game>;
  private rawResultsData: any;

  constructor() {
    this.players = new Map();
    this.winStreaks = new Map();
    this.games = new Map();
    
    // Load data from results.json file
    this.loadDataFromFile();
  }

  private loadDataFromFile() {
    try {
      // Load and parse the results.json file
      const resultsPath = path.join(process.cwd(), 'data', 'results.json');
      const resultsData = JSON.parse(readFileSync(resultsPath, 'utf-8'));
      
      // Store the raw data for analytics
      this.rawResultsData = resultsData;
      
      // Transform and load the data
      this.transformAndLoadData(resultsData);
    } catch (error) {
      console.error('Failed to load results.json, using fallback data:', error);
      // Fallback to empty data if file doesn't exist
      this.rawResultsData = {
        summary: {
          window_days: 30,
          players_processed: 0,
          games_processed: 0,
          streaks_found: 0,
          counts_by_threshold: {
            "≤5%": 0,
            "≤1%": 0,
            "≤0.1%": 0,
            "≤0.01%": 0
          }
        },
        players: {},
        interesting_streaks: []
      };
    }
  }
  
  private transformAndLoadData(resultsData: any) {
    const createdPlayers = new Map<string, Player>();
    
    // Process streaks and create players as needed
    for (const streak of resultsData.interesting_streaks || []) {
      const username = streak.username;
      const playerData = resultsData.players[username];
      
      if (!playerData) continue;
      
      // Create player if not exists
      if (!createdPlayers.has(username)) {
        const player = this.createPlayerSync({
          username: playerData.username,
          title: playerData.title,
          rating: playerData.max_rating,
          ratingCategory: streak.streak.games[0]?.time_class || "blitz",
          avatarUrl: playerData.avatar,
          country: playerData.country,
          profileUrl: `https://chess.com/member/${playerData.username}`
        });
        createdPlayers.set(username, player);
      }
      
      const player = createdPlayers.get(username)!;
      
      // Create win streak
      const winStreak = this.createWinStreakSync({
        playerId: player.id,
        streakLength: streak.streak.length,
        probability: streak.streak.prob * 100, // Convert to percentage
        probabilityTier: this.mapThresholdToTier(streak.streak.threshold),
        startDate: new Date(streak.streak.start_time * 1000),
        endDate: new Date(streak.streak.end_time * 1000),
        averageOpponentRating: this.calculateAverageOpponentRating(streak.streak.games)
      });
      
      // Create games for this streak
      for (const game of streak.streak.games) {
        this.createGameSync({
          streakId: winStreak.id,
          opponentUsername: game.opponent.username,
          opponentRating: game.opponent.rating,
          winProbability: game.p_win * 100, // Convert to percentage
          gameUrl: game.url,
          gameDate: new Date(game.end_time * 1000),
          result: "win"
        });
      }
    }
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
  
  private calculateAverageOpponentRating(games: any[]): number {
    if (games.length === 0) return 0;
    const sum = games.reduce((acc, game) => acc + game.opponent.rating, 0);
    return Math.round(sum / games.length);
  }
  
  private createPlayerSync(insertPlayer: InsertPlayer): Player {
    const id = randomUUID();
    const player: Player = { 
      ...insertPlayer, 
      id,
      avatarUrl: insertPlayer.avatarUrl || null,
      country: insertPlayer.country || null,
      profileUrl: insertPlayer.profileUrl || null
    };
    this.players.set(id, player);
    return player;
  }
  
  private createWinStreakSync(insertStreak: InsertWinStreak): WinStreak {
    const id = randomUUID();
    const streak: WinStreak = { 
      ...insertStreak, 
      id,
      createdAt: new Date()
    };
    this.winStreaks.set(id, streak);
    return streak;
  }
  
  private createGameSync(insertGame: InsertGame): Game {
    const id = randomUUID();
    const game: Game = { 
      ...insertGame, 
      id,
      gameUrl: insertGame.gameUrl || null
    };
    this.games.set(id, game);
    return game;
  }

  async getPlayer(id: string): Promise<Player | undefined> {
    return this.players.get(id);
  }

  async getPlayerByUsername(username: string): Promise<Player | undefined> {
    return Array.from(this.players.values()).find(
      (player) => player.username === username,
    );
  }

  async createPlayer(insertPlayer: InsertPlayer): Promise<Player> {
    const id = randomUUID();
    const player: Player = { 
      ...insertPlayer, 
      id,
      avatarUrl: insertPlayer.avatarUrl || null,
      country: insertPlayer.country || null,
      profileUrl: insertPlayer.profileUrl || null
    };
    this.players.set(id, player);
    return player;
  }

  async getAllPlayers(): Promise<Player[]> {
    return Array.from(this.players.values());
  }

  async getWinStreak(id: string): Promise<WinStreak | undefined> {
    return this.winStreaks.get(id);
  }

  async createWinStreak(insertStreak: InsertWinStreak): Promise<WinStreak> {
    const id = randomUUID();
    const streak: WinStreak = { 
      ...insertStreak, 
      id,
      createdAt: new Date()
    };
    this.winStreaks.set(id, streak);
    return streak;
  }

  async getAllWinStreaks(): Promise<WinStreak[]> {
    return Array.from(this.winStreaks.values());
  }

  async getStreaksWithPlayer(): Promise<StreakWithPlayer[]> {
    const streaks = await this.getAllWinStreaks();
    const streaksWithPlayer: StreakWithPlayer[] = [];

    for (const streak of streaks) {
      const player = await this.getPlayer(streak.playerId);
      const games = await this.getGamesByStreakId(streak.id);
      
      if (player) {
        streaksWithPlayer.push({
          ...streak,
          startDate: new Date(streak.startDate),
          endDate: new Date(streak.endDate),
          createdAt: streak.createdAt ? new Date(streak.createdAt) : null,
          player,
          games: games.map(game => ({
            ...game,
            gameDate: new Date(game.gameDate)
          }))
        });
      }
    }

    // Sort by probability (most extreme first)
    return streaksWithPlayer.sort((a, b) => a.probability - b.probability);
  }

  async createGame(insertGame: InsertGame): Promise<Game> {
    const id = randomUUID();
    const game: Game = { 
      ...insertGame, 
      id,
      gameUrl: insertGame.gameUrl || null
    };
    this.games.set(id, game);
    return game;
  }

  async getGamesByStreakId(streakId: string): Promise<Game[]> {
    return Array.from(this.games.values()).filter(
      game => game.streakId === streakId
    );
  }

  async getAnalyticsData(): Promise<AnalyticsData> {
    const streaks = await this.getAllWinStreaks();
    const streaksWithPlayer = await this.getStreaksWithPlayer();

    const totalStreaks = streaks.length || this.rawResultsData?.summary?.streaks_found || 0;
    const averageStreakLength = totalStreaks > 0 
      ? streaks.reduce((sum, streak) => sum + streak.streakLength, 0) / totalStreaks 
      : 0;
    
    // Use data from JSON file for accurate counts
    const counts = this.rawResultsData?.summary?.counts_by_threshold || {};
    const probabilityDistribution = {
      extreme: counts["≤0.01%"] || 0,
      high: counts["≤0.1%"] || 0,
      moderate: counts["≤1%"] || 0,
      low: counts["≤5%"] || 0,
    };

    const extremeCount = probabilityDistribution.extreme;
    const highestRating = streaksWithPlayer.length > 0 
      ? Math.max(...streaksWithPlayer.map(s => s.player.rating)) 
      : 0;
    const topStreaks = streaksWithPlayer.slice(0, 3);

    return {
      totalStreaks,
      averageStreakLength: Math.round(averageStreakLength * 10) / 10,
      extremeCount,
      highestRating,
      probabilityDistribution,
      topStreaks
    };
  }
  
  // Method to get summary data for hero section
  getSummaryData() {
    return this.rawResultsData?.summary || {
      players_processed: 0,
      games_processed: 0,
      generated_at: Date.now() / 1000
    };
  }
}

export const storage = new MemStorage();