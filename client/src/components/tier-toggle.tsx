import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface TierToggleProps {
  onTierToggle: (enabledTiers: Set<string>) => void;
}

export default function TierToggle({ onTierToggle }: TierToggleProps) {
  const [enabledTiers, setEnabledTiers] = useState<Set<string>>(
    new Set(["extreme", "high", "moderate"]) // Low tier disabled by default
  );

  const toggleTier = (tier: string) => {
    const newEnabledTiers = new Set(enabledTiers);
    if (newEnabledTiers.has(tier)) {
      newEnabledTiers.delete(tier);
    } else {
      newEnabledTiers.add(tier);
    }
    setEnabledTiers(newEnabledTiers);
    onTierToggle(newEnabledTiers);
  };

  const tiers = [
    { id: "extreme", label: "🔴 Extreme (≤0.01%)", color: "tier-extreme" },
    { id: "high", label: "🟠 High (≤0.1%)", color: "tier-high" },
    { id: "moderate", label: "🟡 Moderate (≤1%)", color: "tier-moderate" },
    { id: "low", label: "🟢 Low (≤5%)", color: "tier-low" },
  ];

  return (
    <Card className="mb-6">
      <CardHeader>
        <CardTitle className="text-lg">Probability Tier Filter</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex flex-wrap gap-2">
          {tiers.map((tier) => (
            <Button
              key={tier.id}
              variant={enabledTiers.has(tier.id) ? "default" : "outline"}
              size="sm"
              onClick={() => toggleTier(tier.id)}
              className={`${tier.color} ${enabledTiers.has(tier.id) ? "opacity-100" : "opacity-50"}`}
              data-testid={`tier-toggle-${tier.id}`}
            >
              {tier.label}
            </Button>
          ))}
        </div>
        <p className="text-sm text-muted-foreground mt-2">
          Click tiers to toggle visibility. Showing {enabledTiers.size} of 4 probability levels.
        </p>
      </CardContent>
    </Card>
  );
}