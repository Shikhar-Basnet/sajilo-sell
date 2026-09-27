"use client";

import { useEffect, useState } from "react";

export default function Home() {
  const [status, setStatus] = useState<string>("Checking backend...");

  useEffect(() => {
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
    </main>
  );
}