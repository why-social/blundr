import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function proxy(request: NextRequest) {
  const path = request.nextUrl.pathname;

  // allow api requests
  if (path.startsWith("/api")) {
    return NextResponse.next();
  }

  // allow static _next resources
  if (path.startsWith("/_next")) {
    return NextResponse.next();
  }

  // allow any other resource (i.e. images, documents)
  if (/\.(.*)$/.test(path)) {
    return NextResponse.next();
  }

  // on refresh or navigation, make sure the first
  // page seen by the user is the homepage
  if (!request.headers.get("next-url") && path !== "/") {
    const url = request.nextUrl.clone();
    url.pathname = "/";

    return NextResponse.redirect(url);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/:path*"],
};
