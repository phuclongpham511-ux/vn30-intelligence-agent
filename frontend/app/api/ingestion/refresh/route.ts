export async function POST() {
  const base = process.env.BACKEND_URL || "http://127.0.0.1:8000";
  try {
    const response = await fetch(`${base}/ingestion/refresh`, {
      method: "POST", cache: "no-store", signal: AbortSignal.timeout(15000),
    });
    return new Response(await response.text(), {
      status: response.status, headers: { "Content-Type": "application/json" },
    });
  } catch {
    return Response.json({ detail: "Data refresh is temporarily unavailable. Please retry." }, { status: 502 });
  }
}
