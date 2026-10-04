import Image from "next/image";
import type { ReactNode } from "react";
import { mascotAssets, mascotUiStates, type MascotUiState } from "@/lib/mascot";

export function MascotIllustration({ state, size = 64, className = "" }: {
  state: MascotUiState; size?: 48 | 64 | 128 | 160; className?: string;
}) {
  // Nearby text communicates the state; the artwork adds no screen-reader noise.
  return <Image src={mascotAssets[mascotUiStates[state]]} alt="" aria-hidden="true"
    width={size} height={size} unoptimized draggable={false}
    className={`shrink-0 object-contain ${className}`} style={{ imageRendering: "pixelated" }}/>
}

export function MascotState({ state, children, role }: {
  state: MascotUiState; children: ReactNode; role?: "status" | "alert";
}) {
  return <div role={role} className="flex items-center gap-3 py-4 text-sm text-muted-foreground">
    <MascotIllustration state={state}/><div className="min-w-0 flex-1 leading-6">{children}</div>
  </div>;
}
