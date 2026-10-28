# Shared white wolf mascot

These 13 transparent PNGs are the sole mascot set for both light and dark themes.
Filenames preserve the original numbered vocabulary, 01_curiosity through 13_identity.

Source: owner-provided white wolf reference sheet, October 5, 2026.
Background extraction used the built-in imagegen tool with this instruction:
remove the exterior background and text labels; preserve all 13 white/grey wolf
poses, glasses, red capes, gold stars and state icons; retain opaque white fur,
faces, paws, eyes, ears, chests and speech bubble interiors.

The transparent sheet was split into its 13 cells. Sprites are proportionally
scaled using nearest-neighbor sampling and centered on transparent 512 × 512
canvases. The runtime uses object-contain without clipping or theme variants.
Registry: frontend/lib/mascot.ts. Branding remains text-only.
