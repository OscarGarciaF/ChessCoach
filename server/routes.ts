import type { Express } from "express";
import { createServer, type Server } from "http";
import { storage } from "./storage";

export async function registerRoutes(app: Express): Promise<Server> {
  // Get all interesting streaks with player data
  app.get("/api/streaks", async (req, res) => {
    try {
      const streaks = await storage.getStreaksWithPlayer();
      res.json(streaks);
    } catch (error) {
      res.status(500).json({ message: "Failed to fetch streaks" });
    }
  });

  // Get analytics data
  app.get("/api/analytics", async (req, res) => {
    try {
      const analytics = await storage.getAnalyticsData();
      res.json(analytics);
    } catch (error) {
      res.status(500).json({ message: "Failed to fetch analytics" });
    }
  });

  // Get summary data for hero section
  app.get("/api/summary", async (req, res) => {
    try {
      const summary = storage.getSummaryData();
      res.json(summary);
    } catch (error) {
      res.status(500).json({ message: "Failed to fetch summary data" });
    }
  });

  // Get specific streak details
  app.get("/api/streaks/:id", async (req, res) => {
    try {
      const streak = await storage.getWinStreak(req.params.id);
      if (!streak) {
        return res.status(404).json({ message: "Streak not found" });
      }
      
      const player = await storage.getPlayer(streak.playerId);
      const games = await storage.getGamesByStreakId(streak.id);
      
      res.json({
        ...streak,
        player,
        games
      });
    } catch (error) {
      res.status(500).json({ message: "Failed to fetch streak details" });
    }
  });

  const httpServer = createServer(app);
  return httpServer;
}
