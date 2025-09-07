import { dataService } from "@/lib/data-service";
import { type AnalyticsData } from "@shared/schema";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import { useState, useEffect } from "react";

export default function AnalyticsSection() {
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const loadAnalytics = async () => {
      try {
        const analyticsData = await dataService.getAnalyticsData();
        setAnalytics(analyticsData);
      } catch (error) {
        console.error('Failed to load analytics:', error);
      } finally {
        setIsLoading(false);
      }
    };
    loadAnalytics();
  }, []);


  return (
    <section id="analytics" className="mb-12">
      <h2 className="text-2xl font-bold text-foreground mb-6" data-testid="analytics-title">
        Analytics & Insights
      </h2>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Probability Distribution Chart */}
        <Card>
          <CardHeader>
            <CardTitle>Probability Tier Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="space-y-4">
                {[...Array(4)].map((_, i) => (
                  <div key={i} className="flex items-center justify-between">
                    <Skeleton className="h-4 w-32" />
                    <Skeleton className="h-2 w-32" />
                    <Skeleton className="h-4 w-8" />
                  </div>
                ))}
              </div>
            ) : analytics ? (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <div className="w-4 h-4 rounded tier-extreme"></div>
                    <span className="text-sm">≤0.01% (Extreme)</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Progress value={analytics ? (analytics.probabilityDistribution.extreme / analytics.totalStreaks) * 100 : 0} className="w-32" />
                    <span className="text-sm font-medium text-foreground" data-testid="extreme-count">
                      {analytics?.probabilityDistribution.extreme || 0}
                    </span>
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <div className="w-4 h-4 rounded tier-high"></div>
                    <span className="text-sm">≤0.1% (High)</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Progress value={analytics ? (analytics.probabilityDistribution.high / analytics.totalStreaks) * 100 : 0} className="w-32" />
                    <span className="text-sm font-medium text-foreground" data-testid="high-count">
                      {analytics?.probabilityDistribution.high || 0}
                    </span>
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <div className="w-4 h-4 rounded tier-moderate"></div>
                    <span className="text-sm">≤1% (Moderate)</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Progress value={analytics ? (analytics.probabilityDistribution.moderate / analytics.totalStreaks) * 100 : 0} className="w-32" />
                    <span className="text-sm font-medium text-foreground" data-testid="moderate-count">
                      {analytics?.probabilityDistribution.moderate || 0}
                    </span>
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <div className="w-4 h-4 rounded tier-low"></div>
                    <span className="text-sm">≤5% (Low)</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Progress value={analytics ? (analytics.probabilityDistribution.low / analytics.totalStreaks) * 100 : 0} className="w-32" />
                    <span className="text-sm font-medium text-foreground" data-testid="low-count">
                      {analytics?.probabilityDistribution.low || 0}
                    </span>
                  </div>
                </div>
              </div>
            ) : null}
          </CardContent>
        </Card>

        {/* Top Performers */}
        <Card>
          <CardHeader>
            <CardTitle>Most Extreme Streaks</CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="space-y-3">
                {[...Array(3)].map((_, i) => (
                  <div key={i} className="flex items-center justify-between py-2 border-b border-border">
                    <div className="flex items-center space-x-3">
                      <Skeleton className="w-6 h-6 rounded-full" />
                      <Skeleton className="h-4 w-24" />
                    </div>
                    <Skeleton className="h-6 w-16" />
                  </div>
                ))}
              </div>
            ) : analytics?.topStreaks ? (
              <div className="space-y-3">
                {analytics.topStreaks.map((streak) => (
                  <div
                    key={streak.id}
                    className="flex items-center justify-between py-2 border-b border-border"
                    data-testid={`top-streak-${streak.id}`}
                  >
                    <div className="flex items-center space-x-3">
                      <img
                        src={streak.player.avatarUrl || "https://www.chess.com/bundles/web/images/user-image.007dad08.svg"}
                        alt={streak.player.username}
                        className="w-6 h-6 rounded-full"
                      />
                      <span className="text-sm font-medium">{streak.player.username}</span>
                    </div>
                    <span className={`text-xs px-2 py-1 rounded ${streak.probabilityTier === 'extreme' ? 'tier-extreme' : streak.probabilityTier === 'high' ? 'tier-high' : 'tier-moderate'}`}>
                      {streak.probability}%
                    </span>
                  </div>
                ))}
              </div>
            ) : null}
          </CardContent>
        </Card>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-6 text-center">
            <div className="text-2xl font-bold text-primary" data-testid="total-streaks">
              {isLoading ? <Skeleton className="h-8 w-12 mx-auto" /> : analytics?.totalStreaks}
            </div>
            <div className="text-sm text-muted-foreground">Total Interesting Streaks</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6 text-center">
            <div className="text-2xl font-bold text-primary" data-testid="average-length">
              {isLoading ? <Skeleton className="h-8 w-12 mx-auto" /> : analytics?.averageStreakLength}
            </div>
            <div className="text-sm text-muted-foreground">Average Streak Length</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6 text-center">
            <div className="text-2xl font-bold text-primary" data-testid="extreme-streaks">
              {isLoading ? <Skeleton className="h-8 w-12 mx-auto" /> : analytics?.extremeCount}
            </div>
            <div className="text-sm text-muted-foreground">Extreme Probability (≤0.01%)</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6 text-center">
            <div className="text-2xl font-bold text-primary" data-testid="highest-rating">
              {isLoading ? <Skeleton className="h-8 w-12 mx-auto" /> : analytics?.highestRating}
            </div>
            <div className="text-sm text-muted-foreground">Highest Rating with Streak</div>
          </CardContent>
        </Card>
      </div>
    </section>
  );
}
