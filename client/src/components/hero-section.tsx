import { dataService } from "@/lib/data-service";
import { useMemo } from "react";

export default function HeroSection() {
  const summary = useMemo(() => dataService.getSummaryData(), []);

  const formatNumber = (num: number) => {
    if (num >= 1000000) {
      return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
      return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
  };

  const lastUpdated = summary.generated_at 
    ? new Date(summary.generated_at * 1000).toLocaleDateString() 
    : new Date().toLocaleDateString();

  return (
    <section className="bg-gradient-to-r from-primary to-accent text-primary-foreground py-6">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center">
          <h1 className="text-3xl sm:text-4xl font-bold mb-4" data-testid="hero-title">
            Interesting Win Streaks
          </h1>
          <div className="flex flex-wrap justify-center gap-4 text-sm">
            <div className="bg-white/20 rounded-lg px-3 py-2" data-testid="hero-stat-updated">
              <span className="font-semibold">Last Updated:</span> {lastUpdated}
            </div>
            <div className="bg-white/20 rounded-lg px-3 py-2" data-testid="hero-stat-players">
              <span className="font-semibold">Players Analyzed:</span> {summary.players_processed || 0} titled players
            </div>
            <div className="bg-white/20 rounded-lg px-3 py-2" data-testid="hero-stat-games">
              <span className="font-semibold">Games Processed:</span> {formatNumber(summary.games_processed || 0)} games ({summary.window_days || 30} days)
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
