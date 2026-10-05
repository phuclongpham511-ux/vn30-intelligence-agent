import { NextRequest } from "next/server";

export async function GET(request: NextRequest) {
  const base = process.env.BACKEND_URL || "http://127.0.0.1:8000";
  try {
    const response = await fetch(`${base}/community/pulse${request.nextUrl.search}`, { cache: "no-store", signal: AbortSignal.timeout(15000) });
    return new Response(await response.text(), { status: response.status, headers: { "Content-Type": "application/json" } });
  } catch {
    return Response.json({ detail: "Community discussion is temporarily unavailable." }, { status: 502 });
  }
}
