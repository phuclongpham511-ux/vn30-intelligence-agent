// Artwork names are a visual vocabulary, not computed market classifications.
// Branding is text-only; interface-state illustrations remain enabled.
export const showMascot = true;

export const mascotAssets = {
  curiosity: "/assets/mascot/01_curiosity.png",
  analyzing: "/assets/mascot/02_analyzing.png",
  opportunity: "/assets/mascot/03_opportunity.png",
  scanning: "/assets/mascot/04_scanning.png",
  idle: "/assets/mascot/05_idle.png",
  value: "/assets/mascot/06_value.png",
  watching: "/assets/mascot/07_watching.png",
  bullish: "/assets/mascot/08_bullish.png",
  bearish: "/assets/mascot/09_bearish.png",
  uncertain: "/assets/mascot/10_uncertain.png",
  neutral: "/assets/mascot/11_neutral.png",
  insight: "/assets/mascot/12_insight.png",
  identity: "/assets/mascot/13_identity.png",
} as const;

// These are interface states only. Empty content says nothing about the market.
export const mascotUiStates = {
  brand: "identity",
  discovery: "opportunity",
  emptyWatchlist: "idle",
  loading: "scanning",
  notAvailableYet: "idle",
  noMatches: "curiosity",
  dataUnavailable: "uncertain",
} as const satisfies Record<string, keyof typeof mascotAssets>;

export type MascotUiState = keyof typeof mascotUiStates;
