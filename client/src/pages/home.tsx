import Header from "@/components/header";
import HeroSection from "@/components/hero-section";
import StreaksTable from "@/components/streaks-table";
import AnalyticsSection from "@/components/analytics-section";
import AboutSection from "@/components/about-section";
import Footer from "@/components/footer";
import TierToggle from "@/components/tier-toggle";
import { dataService } from "@/lib/data-service";
import { useState, useEffect } from "react";
import { type StreakWithPlayer } from "@shared/schema";

export default function Home() {
  const [streaks, setStreaks] = useState<StreakWithPlayer[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [enabledTiers, setEnabledTiers] = useState<Set<string>>(
    new Set(["extreme", "high", "moderate"]) // Low tier disabled by default
  );

  useEffect(() => {
    const loadData = async () => {
      try {
        const streaksData = await dataService.getStreaksWithPlayer();
        setStreaks(streaksData);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load data');
      } finally {
        setIsLoading(false);
      }
    };

    loadData();
  }, []);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading chess data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <p className="text-destructive mb-4">Failed to load data: {error}</p>
          <button 
            onClick={() => window.location.reload()} 
            className="px-4 py-2 bg-primary text-primary-foreground rounded hover:bg-primary/90"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <Header />
      <HeroSection />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <TierToggle onTierToggle={setEnabledTiers} />
        <StreaksTable streaks={streaks} enabledTiers={enabledTiers} />
        <AnalyticsSection />
        <AboutSection />
      </main>
      <Footer />
    </div>
  );
}
