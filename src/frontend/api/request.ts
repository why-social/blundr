export async function chatroomRequest<T>(
  method: "POST" | "GET" | "PUT" | "DELETE" | "PATCH",
  path: string,
  body?: unknown,
): Promise<T> {
  const BACKEND_URL = process.env.NEXT_PUBLIC_CHATROOM_URL;

  if (!BACKEND_URL) {
    throw Error("NEXT_PUBLIC_CHATROOM_URL is not provided.");
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

// TODO: Add aggregator request function
