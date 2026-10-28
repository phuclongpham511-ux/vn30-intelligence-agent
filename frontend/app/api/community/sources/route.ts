export async function GET() {
  const base = process.env.BACKEND_URL || "http://127.0.0.1:8000";
  try {
    const response = await fetch(`${base}/community/sources`, { cache: "no-store", signal: AbortSignal.timeout(15000) });
    return new Response(await response.text(), { status: response.status, headers: { "Content-Type": "application/json" } });
  } catch {
    return Response.json({ detail: "Community source status is unavailable." }, { status: 502 });
  }
}
