import { NextRequest } from "next/server";
import { Context, proxy } from "@/app/api/proxy";

const LOCATION = `${process.env.CHATROOM_URL}/api/v1`;

export async function GET(req: NextRequest, context: Context) {
  return proxy(LOCATION, req, context);
}

export async function POST(req: NextRequest, context: Context) {
  return proxy(LOCATION, req, context);
}

export async function PUT(req: NextRequest, context: Context) {
  return proxy(LOCATION, req, context);
}

export async function DELETE(req: NextRequest, context: Context) {
  return proxy(LOCATION, req, context);
}
