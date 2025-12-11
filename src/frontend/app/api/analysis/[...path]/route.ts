import { NextRequest } from "next/server";
import { Context, proxy } from "@/app/api/proxy";

const LOCATION = `${process.env.ANALYSIS_IP_ADDRESS}/analyze`;

export async function GET(req: NextRequest, context: Context) {
  return proxy(LOCATION, req, context);
}
