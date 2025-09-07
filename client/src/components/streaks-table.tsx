import { useState } from "react";
import { type StreakWithPlayer } from "@shared/schema";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { ChevronDown, ChevronUp, Search, ArrowUpDown } from "lucide-react";
import { Badge } from "@/components/ui/badge";

type SortField = "probability" | "rating" | "streakLength" | "player";
type SortDirection = "asc" | "desc";

const getProbabilityTierStyle = (tier: string) => {
  switch (tier) {
    case "extreme":
      return "tier-extreme";
    case "high":
      return "tier-high";
    case "moderate":
      return "tier-moderate";
    case "low":
      return "tier-low";
    default:
      return "tier-low";
  }
};

const getProbabilityTierLabel = (tier: string, probability: number) => {
  switch (tier) {
    case "extreme":
      return `${probability}% (≤0.01%)`;
    case "high":
      return `${probability}% (≤0.1%)`;
    case "moderate":
      return `${probability}% (≤1%)`;
    case "low":
      return `${probability}% (≤5%)`;
    default:
      return `${probability}%`;
  }
};

interface StreaksTableProps {
  streaks: StreakWithPlayer[];
}

export default function StreaksTable({ streaks }: StreaksTableProps) {
  const [searchTerm, setSearchTerm] = useState("");
  const [titleFilter, setTitleFilter] = useState<string>("all");
  const [sortField, setSortField] = useState<SortField>("probability");
  const [sortDirection, setSortDirection] = useState<SortDirection>("asc");
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());
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
  };

  const tiers = [
    { id: "extreme", label: "🔴 Extreme", color: "tier-extreme" },
    { id: "high", label: "🟠 High", color: "tier-high" },
    { id: "moderate", label: "🟡 Moderate", color: "tier-moderate" },
    { id: "low", label: "🟢 Low", color: "tier-low" },
  ];


  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === "asc" ? "desc" : "asc");
    } else {
      setSortField(field);
      setSortDirection("asc");
    }
  };

  const toggleExpand = (streakId: string) => {
    const newExpanded = new Set(expandedRows);
    if (newExpanded.has(streakId)) {
      newExpanded.delete(streakId);
    } else {
      newExpanded.add(streakId);
    }
    setExpandedRows(newExpanded);
  };

  const filteredAndSortedStreaks = streaks
    ?.filter((streak) => {
      const matchesSearch = 
        streak.player.username.toLowerCase().includes(searchTerm.toLowerCase()) ||
        streak.player.title.toLowerCase().includes(searchTerm.toLowerCase());
      
      const matchesTier = enabledTiers.has(streak.probabilityTier);
      const matchesTitle = titleFilter === "all" || streak.player.title === titleFilter;
      
      return matchesSearch && matchesTier && matchesTitle;
    })
    ?.sort((a, b) => {
      let comparison = 0;
      
      switch (sortField) {
        case "probability":
          comparison = a.probability - b.probability;
          break;
        case "rating":
          comparison = a.player.rating - b.player.rating;
          break;
        case "streakLength":
          comparison = a.streakLength - b.streakLength;
          break;
        case "player":
          comparison = a.player.username.localeCompare(b.player.username);
          break;
      }
      
      return sortDirection === "asc" ? comparison : -comparison;
    });


  return (
    <section id="streaks" className="mb-12">
      {/* Search and Filters */}
      <div className="mb-6">
        <div className="flex flex-col lg:flex-row gap-4 items-start lg:items-center justify-between">
          <div className="flex-1 max-w-md">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
              <Input
                type="text"
                placeholder="Search players..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
                data-testid="search-players"
              />
            </div>
          </div>
          <div className="flex flex-wrap gap-2 items-center">
            {/* Tier Toggle Buttons */}
            <div className="flex gap-1 mr-2">
              {tiers.map((tier) => (
                <Button
                  key={tier.id}
                  variant={enabledTiers.has(tier.id) ? "default" : "outline"}
                  size="sm"
                  onClick={() => toggleTier(tier.id)}
                  className={`text-xs px-2 py-1 h-7 ${tier.color} ${enabledTiers.has(tier.id) ? "opacity-100" : "opacity-50"}`}
                  data-testid={`tier-toggle-${tier.id}`}
                >
                  {tier.label}
                </Button>
              ))}
            </div>
            <Select value={titleFilter} onValueChange={setTitleFilter}>
              <SelectTrigger className="w-40" data-testid="filter-title">
                <SelectValue placeholder="All Titles" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Titles</SelectItem>
                <SelectItem value="GM">GM (Grandmaster)</SelectItem>
                <SelectItem value="IM">IM (International Master)</SelectItem>
                <SelectItem value="FM">FM (FIDE Master)</SelectItem>
                <SelectItem value="NM">NM (National Master)</SelectItem>
                <SelectItem value="WGM">WGM (Woman Grandmaster)</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </div>

      {/* Streaks Table */}
      <div className="bg-card rounded-lg shadow-sm border border-border overflow-hidden max-h-[600px] overflow-y-auto">
        <div className="px-6 py-4 border-b border-border">
          <h2 className="text-xl font-semibold text-foreground" data-testid="table-title">
            Interesting Win Streaks (Last 30 Days)
          </h2>
          <p className="text-sm text-muted-foreground mt-1">
            Click rows to expand game details • Showing {enabledTiers.size} of 4 probability tiers
          </p>
        </div>
        
        <div className="overflow-x-auto">
            <table className="w-full chess-table">
              <thead className="bg-muted">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleSort("player")}
                      className="h-auto p-0 font-medium hover:bg-accent"
                      data-testid="sort-player"
                    >
                      <span className="flex items-center">
                        Player <ArrowUpDown className="ml-1 h-3 w-3" />
                      </span>
                    </Button>
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleSort("rating")}
                      className="h-auto p-0 font-medium hover:bg-accent"
                      data-testid="sort-rating"
                    >
                      <span className="flex items-center">
                        Rating <ArrowUpDown className="ml-1 h-3 w-3" />
                      </span>
                    </Button>
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleSort("streakLength")}
                      className="h-auto p-0 font-medium hover:bg-accent"
                      data-testid="sort-streak"
                    >
                      <span className="flex items-center">
                        Streak <ArrowUpDown className="ml-1 h-3 w-3" />
                      </span>
                    </Button>
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleSort("probability")}
                      className="h-auto p-0 font-medium hover:bg-accent"
                      data-testid="sort-probability"
                    >
                      <span className="flex items-center">
                        Probability <ArrowUpDown className="ml-1 h-3 w-3" />
                      </span>
                    </Button>
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                    Period
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                    
                  </th>
                </tr>
              </thead>
              <tbody className="bg-card divide-y divide-border">
                {filteredAndSortedStreaks?.map((streak) => [
                  <tr
                    key={`main-${streak.id}`}
                    className="table-row cursor-pointer hover:bg-muted/50"
                    onClick={() => toggleExpand(streak.id)}
                    data-testid={`streak-row-${streak.id}`}
                  >
                    <td className="px-6 py-4">
                      <div className="flex items-center">
                        <img
                          src={streak.player.avatarUrl || "https://www.chess.com/bundles/web/images/user-image.007dad08.svg"}
                          alt={`${streak.player.username} avatar`}
                          className="w-8 h-8 rounded-full mr-3"
                          data-testid={`avatar-${streak.player.username}`}
                        />
                        <div>
                          <div className="text-sm font-medium text-foreground">
                            {streak.player.username}
                          </div>
                          <div className="text-xs text-muted-foreground">
                            {streak.player.title}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm text-foreground font-medium">
                        {streak.player.rating}
                      </div>
                      <div className="text-xs text-muted-foreground capitalize">
                        {streak.player.ratingCategory}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm font-semibold text-foreground">
                        {streak.streakLength} wins
                      </div>
                      <div className="text-xs text-muted-foreground">
                        vs {streak.averageOpponentRating}+ avg
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <Badge className={getProbabilityTierStyle(streak.probabilityTier)}>
                        {getProbabilityTierLabel(streak.probabilityTier, streak.probability)}
                      </Badge>
                    </td>
                    <td className="px-6 py-4 text-sm text-muted-foreground">
                      {new Date(streak.startDate).toLocaleDateString()} - {new Date(streak.endDate).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4">
                      {expandedRows.has(streak.id) ? (
                        <ChevronUp className="h-4 w-4 text-muted-foreground" />
                      ) : (
                        <ChevronDown className="h-4 w-4 text-muted-foreground" />
                      )}
                    </td>
                  </tr>,
                  expandedRows.has(streak.id) && (
                    <tr key={`expanded-${streak.id}`}>
                      <td colSpan={6} className="px-6 py-4 bg-muted">
                        <div className="space-y-2">
                          <h4 className="font-medium text-foreground mb-3">Game Breakdown:</h4>
                          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                            {streak.games.map((game, index) => (
                              <div
                                key={game.id}
                                className="bg-card rounded p-3 border border-border"
                                data-testid={`game-${game.id}`}
                              >
                                <div className="text-xs text-muted-foreground">
                                  Game {index + 1}
                                </div>
                                <div className="text-sm">
                                  vs {game.opponentUsername} ({game.opponentRating}) -{" "}
                                  <span className="text-primary font-medium">Win</span>
                                </div>
                                <div className="text-xs text-muted-foreground">
                                  Win probability: {game.winProbability}%
                                </div>
                                {game.gameUrl && (
                                  <a
                                    href={game.gameUrl}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-xs text-primary hover:underline"
                                    data-testid={`game-link-${game.id}`}
                                  >
                                    View Game
                                  </a>
                                )}
                              </div>
                            ))}
                          </div>
                          {streak.games.length < streak.streakLength && (
                            <p className="text-xs text-muted-foreground mt-2">
                              + {streak.streakLength - streak.games.length} more games
                            </p>
                          )}
                        </div>
                      </td>
                    </tr>
                  )
                ].filter(Boolean))}
              </tbody>
            </table>
        </div>
        
        {filteredAndSortedStreaks && filteredAndSortedStreaks.length === 0 && (
          <div className="px-6 py-8 text-center">
            <p className="text-muted-foreground">No interesting streaks found matching your criteria.</p>
          </div>
        )}
      </div>
    </section>
  );
}