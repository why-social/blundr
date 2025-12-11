import { NextRequest, NextResponse } from "next/server";

type Context = { params: Promise<{ path?: string[] }> };
interface NodeFetchInit extends RequestInit {
  duplex?: "half";
}

export async function GET(req: NextRequest, context: Context) {
  return proxy(req, context);
}

export async function POST(req: NextRequest, context: Context) {
  return proxy(req, context);
}

export async function PUT(req: NextRequest, context: Context) {
  return proxy(req, context);
}

export async function DELETE(req: NextRequest, context: Context) {
  return proxy(req, context);
}

async function proxy(req: NextRequest, context: Context) {
  const { path } = await context.params;
  const backendUrl = `${process.env.CHATROOM_URL}/api/v1/${path?.join("/") ?? ""}`;

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
