import { NextRequest } from "next/server";
import { Context, proxy } from "@/app/api/proxy";

export async function GET(req: NextRequest, context: Context) {
  const location = process.env.ANALYSIS_IP_ADDRESS;

  if (!location) {
    throw Error("ANALYSIS_IP_ADDRESS is not provided.");
  }

  return proxy(location, req, context);
}
