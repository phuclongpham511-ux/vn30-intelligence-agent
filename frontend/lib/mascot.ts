// Artwork names are a visual vocabulary, not computed market classifications.
export const mascotAssets = {
  curiosity: "/mascots/01_curiosity.png",
  analyzing: "/mascots/02_analyzing.png",
  opportunity: "/mascots/03_opportunity.png",
  scanning: "/mascots/04_scanning.png",
  idle: "/mascots/05_idle.png",
  value: "/mascots/06_value.png",
  watching: "/mascots/07_watching.png",
  bullish: "/mascots/08_bullish.png",
  bearish: "/mascots/09_bearish.png",
  uncertain: "/mascots/10_uncertain.png",
  neutral: "/mascots/11_neutral.png",
  insight: "/mascots/12_insight.png",
  identity: "/mascots/13_identity.png",
} as const;

// These are interface states only. Empty content says nothing about the market.
export const mascotUiStates = {
  brand: "identity",
  discovery: "curiosity",
  loading: "scanning",
  notAvailableYet: "idle",
  noMatches: "curiosity",
  dataUnavailable: "uncertain",
} as const satisfies Record<string, keyof typeof mascotAssets>;

export type MascotUiState = keyof typeof mascotUiStates;
