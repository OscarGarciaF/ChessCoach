/**
 * Probability calculation utilities based on Glicko rating system
 * Used to determine the likelihood of chess game outcomes
 */

/**
 * Calculate expected score using simplified Glicko formula
 * @param playerRating - Rating of the player
 * @param opponentRating - Rating of the opponent  
 * @param playerRD - Rating deviation of the player (optional, defaults to 50)
 * @param opponentRD - Rating deviation of the opponent (optional, defaults to 50)
 * @returns Expected score (0 to 1, where 1 is certain win)
 */
export function calculateExpectedScore(
  playerRating: number,
  opponentRating: number,
  playerRD: number = 50,
  opponentRD: number = 50
): number {
  // Glicko g(RD) function - reduces impact of rating difference when RD is high
  const g = (rd: number) => 1 / Math.sqrt(1 + (3 * Math.pow(rd / Math.PI, 2)));
  
  // Combined RD for the calculation
  const combinedRD = Math.sqrt(Math.pow(playerRD, 2) + Math.pow(opponentRD, 2));
  
  // Expected score formula
  const ratingDifference = playerRating - opponentRating;
  const expectedScore = 1 / (1 + Math.pow(10, -g(combinedRD) * ratingDifference / 400));
  
  return expectedScore;
}

/**
 * Calculate win probability percentage from expected score
 * @param playerRating - Rating of the player
 * @param opponentRating - Rating of the opponent
 * @param playerRD - Rating deviation of the player (optional)
 * @param opponentRD - Rating deviation of the opponent (optional)
 * @returns Win probability as percentage (0-100)
 */
export function calculateWinProbability(
  playerRating: number,
  opponentRating: number,
  playerRD?: number,
  opponentRD?: number
): number {
  const expectedScore = calculateExpectedScore(playerRating, opponentRating, playerRD, opponentRD);
  return Math.round(expectedScore * 1000) / 10; // Round to 1 decimal place
}

/**
 * Calculate combined probability of multiple wins in sequence
 * @param winProbabilities - Array of individual win probabilities (as percentages)
 * @returns Combined probability as percentage
 */
export function calculateStreakProbability(winProbabilities: number[]): number {
  const combinedProbability = winProbabilities.reduce((product, probability) => {
    return product * (probability / 100);
  }, 1);
  
  return Math.round(combinedProbability * 100000) / 1000; // Round to 3 decimal places
}

/**
 * Determine probability tier based on streak probability
 * @param probability - Probability percentage
 * @returns Tier classification
 */
export function getProbabilityTier(probability: number): 'extreme' | 'high' | 'moderate' | 'low' {
  if (probability <= 0.01) return 'extreme';
  if (probability <= 0.1) return 'high';
  if (probability <= 1) return 'moderate';
  if (probability <= 5) return 'low';
  return 'low'; // Fallback
}

/**
 * Convert probability to odds ratio (e.g., "1 in 2000")
 * @param probability - Probability percentage
 * @returns Odds ratio as string
 */
export function probabilityToOdds(probability: number): string {
  const odds = Math.round(100 / probability);
  return `1 in ${odds.toLocaleString()}`;
}
