type ApiResponse<T> =
  | {
      status: "ok";
      data: T;
    }
  | {
      status: "error";
      data: { code: number; message: string };
    };

export async function chatroomRequest<T>(
  method: "POST" | "GET" | "PUT" | "DELETE",
  path: string,
  body?: unknown,
): Promise<ApiResponse<T>> {
  return request(method, `api/chatroom/${path}`, body);
}

export async function analysisRequest<T>(
  method: "POST" | "GET" | "PUT" | "DELETE",
  path: string,
  body?: unknown,
): Promise<ApiResponse<T>> {
  return request(method, `api/analysis/${path}`, body);
}

async function request<T>(
  method: "POST" | "GET" | "PUT" | "DELETE",
  path: string,
  body?: unknown,
): Promise<ApiResponse<T>> {
  try {
    const res = await fetch(path, {
      method,
      headers: { "Content-Type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body),
    });

    const text = await res.text();
    let parsedData: T | null;

    try {
      parsedData = text ? JSON.parse(text) : null;
    } catch {
      parsedData = null;
    }

    if (res.ok) {
      return { status: "ok", data: parsedData as T };
    }

    return {
      status: "error",
      data: { code: res.status, message: text || res.statusText },
    };
  } catch (error) {
    return {
      status: "error",
      data: {
        code: 0,
        message: error instanceof Error ? error.message : String(error),
      },
    };
  }
}
