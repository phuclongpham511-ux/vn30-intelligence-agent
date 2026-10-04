import { NextRequest } from "next/server";

export async function GET(request: NextRequest, context: { params: Promise<{ path?: string[] }> }) {
  const { path = [] } = await context.params;
  const base = process.env.BACKEND_URL || "http://127.0.0.1:8000";
  try {
    const response = await fetch(`${base}/news/${path.map(encodeURIComponent).join("/")}${request.nextUrl.search}`, {
      cache: "no-store", signal: AbortSignal.timeout(15000),
    });
    return new Response(await response.text(), { status: response.status, headers: { "Content-Type": "application/json" } });
  } catch {
    return Response.json({ detail: "News is temporarily unavailable. Please retry." }, { status: 502 });
  }
}
