import { dataService } from "@/lib/data-service";
import { type AnalyticsData } from "@shared/schema";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { useMemo } from "react";

export default function AnalyticsSection() {
  const analytics = useMemo(() => dataService.getAnalyticsData(), []);


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
            {analytics ? (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <div className="w-4 h-4 rounded tier-extreme"></div>
                    <span className="text-sm">≤0.01% (Extreme)</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Progress value={(analytics.probabilityDistribution.extreme / analytics.totalStreaks) * 100} className="w-32" />
                    <span className="text-sm font-medium text-foreground" data-testid="extreme-count">
                      {analytics.probabilityDistribution.extreme}
                    </span>
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <div className="w-4 h-4 rounded tier-high"></div>
                    <span className="text-sm">≤0.1% (High)</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Progress value={(analytics.probabilityDistribution.high / analytics.totalStreaks) * 100} className="w-32" />
                    <span className="text-sm font-medium text-foreground" data-testid="high-count">
                      {analytics.probabilityDistribution.high}
                    </span>
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <div className="w-4 h-4 rounded tier-moderate"></div>
                    <span className="text-sm">≤1% (Moderate)</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Progress value={(analytics.probabilityDistribution.moderate / analytics.totalStreaks) * 100} className="w-32" />
                    <span className="text-sm font-medium text-foreground" data-testid="moderate-count">
                      {analytics.probabilityDistribution.moderate}
                    </span>
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <div className="w-4 h-4 rounded tier-low"></div>
                    <span className="text-sm">≤5% (Low)</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Progress value={(analytics.probabilityDistribution.low / analytics.totalStreaks) * 100} className="w-32" />
                    <span className="text-sm font-medium text-foreground" data-testid="low-count">
                      {analytics.probabilityDistribution.low}
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
            {analytics.topStreaks ? (
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
              {analytics.totalStreaks}
            </div>
            <div className="text-sm text-muted-foreground">Total Interesting Streaks</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6 text-center">
            <div className="text-2xl font-bold text-primary" data-testid="average-length">
              {analytics.averageStreakLength}
            </div>
            <div className="text-sm text-muted-foreground">Average Streak Length</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6 text-center">
            <div className="text-2xl font-bold text-primary" data-testid="extreme-streaks">
              {analytics.extremeCount}
            </div>
            <div className="text-sm text-muted-foreground">Extreme Probability (≤0.01%)</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6 text-center">
            <div className="text-2xl font-bold text-primary" data-testid="highest-rating">
              {analytics.highestRating}
            </div>
            <div className="text-sm text-muted-foreground">Highest Rating with Streak</div>
          </CardContent>
        </Card>
      </div>
    </section>
  );
}
