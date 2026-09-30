"use client";

import { useEffect, useState } from "react";
import { apiFetch, ApiError } from "@/lib/api";
import type { StorePublicOut } from "@/lib/types";

export default function BrowsePage() {
  const [stores, setStores] = useState<StorePublicOut[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiFetch<StorePublicOut[]>("/v1/stores", { auth: false })
      .then(setStores)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Failed to load stores."));
  }, []);

  return (
    <main className="min-h-screen flex flex-col items-center p-8 font-sans">
      <div className="w-full max-w-2xl">
        <h1 className="text-2xl font-bold mb-6 text-center">Browse stores</h1>
        {error && <p className="text-red-600 text-center">{error}</p>}
        {stores === null && !error && <p className="text-gray-500 text-center">Loading...</p>}
        {stores !== null && stores.length === 0 && <p className="text-gray-500 text-center">No stores yet.</p>}
        <ul className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {stores?.map((store) => (
            <li key={store.slug} className="border border-gray-200 rounded-lg p-4">
              <a href={`/store?slug=${store.slug}`} className="font-semibold underline">{store.name}</a>
              {store.description && <p className="text-sm text-gray-600 mt-1">{store.description}</p>}
            </li>
          ))}
        </ul>
      </div>
    </main>
  );
}