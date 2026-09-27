"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { isAuthenticated } from "@/lib/api";

export default function Home() {
  const [status, setStatus] = useState<string>("Checking backend...");
  const [authed, setAuthed] = useState(false);

  useEffect(() => {
    setAuthed(isAuthenticated());
    fetch("/api/health")
      .then((res) => res.json())
      .then((data) =>
        setStatus(`Backend response: ${data.status} (${data.service})`)
      )
      .catch(() => setStatus("Backend unreachable"));
  }, []);

  return (
    <main className="min-h-screen flex flex-col items-center justify-center gap-4 p-8 font-sans">
      <h1 className="text-3xl font-bold">Cloud-based Application Development</h1>
      <p className="text-gray-600">Frontend is live.</p>
      <p className="text-lg">{status}</p>

      <div className="flex gap-4 mt-4">
        {authed ? (
          <Link
            href="/dashboard"
            className="bg-black text-white rounded-md px-4 py-2 text-sm font-medium"
          >
            Go to dashboard
          </Link>
        ) : (
          <>
            <Link
              href="/login"
              className="border border-black rounded-md px-4 py-2 text-sm font-medium"
            >
              Log in
            </Link>
            <Link
              href="/register"
              className="bg-black text-white rounded-md px-4 py-2 text-sm font-medium"
            >
              Sign up
            </Link>
          </>
        )}
      </div>
    </main>
  );
}