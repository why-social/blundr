import { NextRequest, NextResponse } from "next/server";

export type Context = { params: Promise<{ path?: string[] }> };
interface NodeFetchInit extends RequestInit {
  duplex?: "half";
}

export async function proxy(
  location: string,
  req: NextRequest,
  context: Context,
) {
  const { path } = await context.params;

  const pathname = path?.join("/") ?? "";
  const search = req.nextUrl.search;

  const backendUrl = `${location}/${pathname}${search}`;

  // node 18+ requires a duples attribute to be set
  const init: NodeFetchInit = {
    method: req.method,
    headers: req.headers,
  };

  if (!["GET", "HEAD"].includes(req.method)) {
    init.body = req.body;
    init.duplex = "half";
  }

  const backendRes = await fetch(backendUrl, init);

  const data = await backendRes.arrayBuffer();
  const res = new NextResponse(Buffer.from(data), {
    status: backendRes.status,
  });

  backendRes.headers.forEach((value, key) => {
    res.headers.set(key, value);
  });

  return res;
}
