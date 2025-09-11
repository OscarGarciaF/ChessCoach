import { sql } from "drizzle-orm";
import { pgTable, text, varchar, integer, real, timestamp } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod";

export const players = pgTable("players", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  username: text("username").notNull().unique(),
  title: text("title").notNull(), // GM, IM, FM, etc.
  rating: integer("rating").notNull(),
  ratingCategory: text("rating_category").notNull(), // blitz, rapid, bullet, daily
  avatarUrl: text("avatar_url"),
  country: text("country"),
  profileUrl: text("profile_url"),
});

export const winStreaks = pgTable("win_streaks", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  playerId: varchar("player_id").notNull().references(() => players.id),
  streakLength: integer("streak_length").notNull(),
  probability: real("probability").notNull(), // Combined probability as percentage
  probabilityTier: text("probability_tier").notNull(), // "extreme", "high", "moderate", "low"
  startDate: timestamp("start_date").notNull(),
  endDate: timestamp("end_date").notNull(),
  averageOpponentRating: integer("average_opponent_rating").notNull(),
  createdAt: timestamp("created_at").default(sql`now()`),
});

export const games = pgTable("games", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  streakId: varchar("streak_id").notNull().references(() => winStreaks.id),
  opponentUsername: text("opponent_username").notNull(),
  opponentRating: integer("opponent_rating").notNull(),
  winnerRating: integer("winner_rating").notNull(),
  winProbability: real("win_probability").notNull(), // Individual game win probability
  gameUrl: text("game_url"),
  gameDate: timestamp("game_date").notNull(),
  result: text("result").notNull(), // "win", "loss", "draw"
});

export const insertPlayerSchema = createInsertSchema(players).omit({
  id: true,
});

export const insertWinStreakSchema = createInsertSchema(winStreaks).omit({
  id: true,
  createdAt: true,
});

export const insertGameSchema = createInsertSchema(games).omit({
  id: true,
});

export type Player = typeof players.$inferSelect;
export type InsertPlayer = z.infer<typeof insertPlayerSchema>;
export type WinStreak = typeof winStreaks.$inferSelect;
export type InsertWinStreak = z.infer<typeof insertWinStreakSchema>;
export type Game = typeof games.$inferSelect;
export type InsertGame = z.infer<typeof insertGameSchema>;

// Combined types for API responses
export type StreakWithPlayer = WinStreak & {
  player: Player;
  games: Game[];
};

export type AnalyticsData = {
  totalStreaks: number;
  averageStreakLength: number;
  extremeCount: number;
  highestRating: number;
  probabilityDistribution: {
    extreme: number;
    high: number;
    moderate: number;
    low: number;
  };
  topStreaks: StreakWithPlayer[];
};
