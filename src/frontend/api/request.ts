export async function apiRequest<T>(
  method: "POST" | "GET" | "PUT" | "DELETE" | "PATCH",
  path: string,
  body?: unknown,
): Promise<T> {
  const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL;

  if (!BACKEND_URL) {
    console.error("NEXT_PUBLIC_BACKEND_URL is not provided.");
    process.exit(1);
  }

  const res = await fetch(`${BACKEND_URL}/api/v1/${path}`, {
    method,
    headers: {
      "Content-Type": "application/json",
    },
    body: body === undefined ? undefined : JSON.stringify(body),
  });

  if (!res.ok) {
    throw new Error(await res.text());
  }

  return res.json();
}
