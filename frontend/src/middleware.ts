import { NextRequest, NextResponse } from "next/server";

const AUTH_COOKIE_NAME = "sajilo_authed";
const PROTECTED_PATHS = ["/dashboard"];
const AUTH_ONLY_PATHS = ["/login", "/register"];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const isAuthed = request.cookies.get(AUTH_COOKIE_NAME)?.value === "1";

  const isProtected = PROTECTED_PATHS.some(
    (p) => pathname === p || pathname.startsWith(`${p}/`)
  );
  const isAuthOnlyPage = AUTH_ONLY_PATHS.some((p) => pathname === p);

  if (isProtected && !isAuthed) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("from", pathname);
    return NextResponse.redirect(loginUrl);
  }

  // Already logged in? Don't show the login/register forms again.
  if (isAuthOnlyPage && isAuthed) {
    return NextResponse.redirect(new URL("/dashboard", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/dashboard/:path*", "/login", "/register"],
};