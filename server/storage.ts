import { type Player, type InsertPlayer, type WinStreak, type InsertWinStreak, type Game, type InsertGame, type StreakWithPlayer, type AnalyticsData } from "@shared/schema";
import { randomUUID } from "crypto";

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
}

export class MemStorage implements IStorage {
  private players: Map<string, Player>;
  private winStreaks: Map<string, WinStreak>;
  private games: Map<string, Game>;

  constructor() {
    this.players = new Map();
    this.winStreaks = new Map();
    this.games = new Map();
    
    // Initialize with realistic sample data
    this.initializeSampleData();
  }

  private async initializeSampleData() {
    // Create sample players
    const samplePlayers: InsertPlayer[] = [
      {
        username: "GM_Alexandra_Chess",
        title: "GM",
        rating: 2687,
        ratingCategory: "blitz",
        avatarUrl: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?ixlib=rb-4.0.3&auto=format&fit=crop&w=50&h=50",
        country: "US",
        profileUrl: "https://chess.com/member/GM_Alexandra_Chess"
      },
      {
        username: "IM_Vladimir_Tactics",
        title: "IM", 
        rating: 2456,
        ratingCategory: "rapid",
        avatarUrl: "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?ixlib=rb-4.0.3&auto=format&fit=crop&w=50&h=50",
        country: "RU",
        profileUrl: "https://chess.com/member/IM_Vladimir_Tactics"
      },
      {
        username: "WGM_Sofia_Endgame",
        title: "WGM",
        rating: 2389,
        ratingCategory: "blitz", 
        avatarUrl: "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?ixlib=rb-4.0.3&auto=format&fit=crop&w=50&h=50",
        country: "BG",
        profileUrl: "https://chess.com/member/WGM_Sofia_Endgame"
      },
      {
        username: "FM_Robert_Opening",
        title: "FM",
        rating: 2234,
        ratingCategory: "bullet",
        avatarUrl: "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?ixlib=rb-4.0.3&auto=format&fit=crop&w=50&h=50",
        country: "DE",
        profileUrl: "https://chess.com/member/FM_Robert_Opening"
      },
      {
        username: "GM_Chen_Strategy",
        title: "GM",
        rating: 2598,
        ratingCategory: "rapid",
        avatarUrl: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?ixlib=rb-4.0.3&auto=format&fit=crop&w=50&h=50",
        country: "CN", 
        profileUrl: "https://chess.com/member/GM_Chen_Strategy"
      }
    ];

    // Create players
    const createdPlayers = await Promise.all(
      samplePlayers.map(player => this.createPlayer(player))
    );

    // Create sample win streaks
    const sampleStreaks: InsertWinStreak[] = [
      {
        playerId: createdPlayers[0].id,
        streakLength: 8,
        probability: 0.008,
        probabilityTier: "extreme",
        startDate: new Date("2024-12-10"),
        endDate: new Date("2024-12-12"),
        averageOpponentRating: 2500
      },
      {
        playerId: createdPlayers[1].id,
        streakLength: 6,
        probability: 0.08,
        probabilityTier: "high", 
        startDate: new Date("2024-12-08"),
        endDate: new Date("2024-12-09"),
        averageOpponentRating: 2400
      },
      {
        playerId: createdPlayers[2].id,
        streakLength: 5,
        probability: 0.7,
        probabilityTier: "moderate",
        startDate: new Date("2024-12-13"),
        endDate: new Date("2024-12-14"),
        averageOpponentRating: 2350
      },
      {
        playerId: createdPlayers[3].id,
        streakLength: 4,
        probability: 3.2,
        probabilityTier: "low",
        startDate: new Date("2024-12-11"),
        endDate: new Date("2024-12-11"),
        averageOpponentRating: 2200
      },
      {
        playerId: createdPlayers[4].id,
        streakLength: 7,
        probability: 0.9,
        probabilityTier: "moderate",
        startDate: new Date("2024-12-07"),
        endDate: new Date("2024-12-08"),
        averageOpponentRating: 2450
      }
    ];

    // Create streaks
    const createdStreaks = await Promise.all(
      sampleStreaks.map(streak => this.createWinStreak(streak))
    );

    // Create sample games for each streak
    const sampleGames: InsertGame[] = [
      // Games for streak 1 (GM Alexandra)
      {
        streakId: createdStreaks[0].id,
        opponentUsername: "IM_Boris_Player",
        opponentRating: 2534,
        winProbability: 12.4,
        gameUrl: "https://chess.com/game/123456",
        gameDate: new Date("2024-12-10T14:30:00"),
        result: "win"
      },
      {
        streakId: createdStreaks[0].id,
        opponentUsername: "GM_Carlos_Master",
        opponentRating: 2598,
        winProbability: 35.2,
        gameUrl: "https://chess.com/game/123457",
        gameDate: new Date("2024-12-10T15:45:00"),
        result: "win"
      },
      {
        streakId: createdStreaks[0].id,
        opponentUsername: "GM_Diana_Queen",
        opponentRating: 2612,
        winProbability: 27.8,
        gameUrl: "https://chess.com/game/123458",
        gameDate: new Date("2024-12-11T10:20:00"),
        result: "win"
      }
    ];

    await Promise.all(
      sampleGames.map(game => this.createGame(game))
    );
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

    const totalStreaks = streaks.length;
    const averageStreakLength = streaks.reduce((sum, streak) => sum + streak.streakLength, 0) / totalStreaks;
    
    const probabilityDistribution = {
      extreme: streaks.filter(s => s.probabilityTier === "extreme").length,
      high: streaks.filter(s => s.probabilityTier === "high").length,
      moderate: streaks.filter(s => s.probabilityTier === "moderate").length,
      low: streaks.filter(s => s.probabilityTier === "low").length,
    };

    const extremeCount = probabilityDistribution.extreme;
    const highestRating = Math.max(...streaksWithPlayer.map(s => s.player.rating));
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
}

export const storage = new MemStorage();
