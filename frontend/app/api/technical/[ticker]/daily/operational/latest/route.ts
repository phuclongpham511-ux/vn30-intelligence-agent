import { NextRequest } from "next/server";

export async function GET(request: NextRequest, context: { params: Promise<{ ticker: string }> }) {
  const { ticker } = await context.params;
  if (!/^[A-Z0-9]{1,20}$/.test(ticker) || request.nextUrl.search)
    return Response.json({ detail: "Invalid Technical request" }, { status: 422 });
  const base = process.env.BACKEND_URL || "http://127.0.0.1:8000";
  try {
    const response = await fetch(base + "/technical/" + encodeURIComponent(ticker) + "/daily/operational/latest",
      { cache: "no-store", signal: AbortSignal.timeout(10000) });
    return new Response(await response.text(), { status: response.status,
      headers: { "Content-Type": "application/json", "Cache-Control": "no-store" } });
  } catch {
    return Response.json({ detail: "Technical API unavailable" }, { status: 503 });
  }
}
