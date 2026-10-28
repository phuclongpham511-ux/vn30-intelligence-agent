import { NextRequest } from "next/server";

export async function POST(request: NextRequest) {
  const base = process.env.BACKEND_URL || "http://127.0.0.1:8000";
  try {
    const response = await fetch(`${base}/watchlists/monitoring`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: await request.text(), cache: "no-store", signal: AbortSignal.timeout(15000),
    });
    return new Response(await response.text(), { status: response.status, headers: { "Content-Type": "application/json" } });
  } catch {
    return Response.json({ detail: "Watchlist updates are temporarily unavailable. Please retry." }, { status: 502 });
  }
}
