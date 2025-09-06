export default function AboutSection() {
  return (
    <section id="about" className="mb-0">
      <div className="bg-card rounded-lg shadow-sm border border-border p-6">
        <h2 className="text-xl font-semibold text-foreground mb-4" data-testid="about-title">
          About Interesting Chess
        </h2>
        <div className="prose prose-sm text-muted-foreground max-w-none">
          <p className="mb-0">
            Interesting Chess automatically analyzes win streaks by titled chess players using Chess.com's public API. 
            We calculate the probability of each streak using Glicko rating system formulas, identifying statistically 
            unlikely performances.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-0">
            <div>
              <h3 className="font-medium text-foreground mb-2">Data Sources</h3>
              <ul className="text-sm space-y-1">
                <li>• Chess.com Public API</li>
                <li>• Titled players list (GM, IM, FM, etc.)</li>
                <li>• Last 30 days of game data</li>
                <li>• Glicko rating calculations</li>
              </ul>
            </div>
            <div>
              <h3 className="font-medium text-foreground mb-2">Probability Tiers</h3>
              <ul className="text-sm space-y-1">
                <li>• ≤0.01%: Extreme anomaly</li>
                <li>• ≤0.1%: High anomaly</li>
                <li>• ≤1%: Moderate anomaly</li>
                <li>• ≤5%: Low anomaly</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
