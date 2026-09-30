"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { apiFetch, ApiError } from "@/lib/api";
import type { ProductPublicOut, StorePublicOut } from "@/lib/types";

type ViewState =
  | { status: "loading" }
  | { status: "not-found" }
  | { status: "found"; store: StorePublicOut }
  | { status: "error"; message: string };

function Storefront() {
  const slug = useSearchParams().get("slug");
  const [view, setView] = useState<ViewState>({ status: "loading" });
  const [products, setProducts] = useState<ProductPublicOut[]>([]);
  const [productsError, setProductsError] = useState<string | null>(null);

  useEffect(() => {
    if (!slug) {
      setView({ status: "not-found" });
      return;
    }
    let cancelled = false;
    const s = encodeURIComponent(slug);

    (async () => {
      // Both requests leave at the same time: one round trip instead of two.
      const [storeRes, productsRes] = await Promise.allSettled([
        apiFetch<StorePublicOut>(`/v1/stores/by-slug/${s}`, { auth: false }),
        apiFetch<ProductPublicOut[]>(`/v1/products/by-store-slug/${s}`, { auth: false }),
      ]);
      if (cancelled) return;

      if (storeRes.status === "rejected") {
        const err = storeRes.reason;
        if (err instanceof ApiError && err.status === 404) setView({ status: "not-found" });
        else setView({ status: "error", message: err instanceof ApiError ? err.message : "Something went wrong." });
        return;
      }
      setView({ status: "found", store: storeRes.value });

      if (productsRes.status === "fulfilled") setProducts(productsRes.value);
      else setProductsError(productsRes.reason instanceof ApiError ? productsRes.reason.message : "Failed to load products.");
    })();

    return () => {
      cancelled = true;
    };
  }, [slug]);

  if (view.status === "loading") {
    return <main className="min-h-screen flex items-center justify-center font-sans"><p className="text-gray-500">Loading store...</p></main>;
  }
  if (view.status === "not-found") {
    return (
      <main className="min-h-screen flex flex-col items-center justify-center gap-2 font-sans">
        <h1 className="text-2xl font-bold">Store not found</h1>
        <p className="text-gray-600">There&apos;s no store at this address.</p>
      </main>
    );
  }
  if (view.status === "error") {
    return <main className="min-h-screen flex items-center justify-center font-sans"><p className="text-red-600">{view.message}</p></main>;
  }

  const { store } = view;
  return (
    <main className="min-h-screen flex flex-col items-center p-8 font-sans">
      <div className="w-full max-w-2xl">
        <header className="border-b border-gray-200 pb-6 mb-8 text-center">
          <h1 className="text-3xl font-bold">{store.name}</h1>
          {store.description && <p className="text-gray-600 text-sm mt-2">{store.description}</p>}
        </header>

        {productsError && <p className="text-red-600 text-center">{productsError}</p>}
        {!productsError && products.length === 0 && (
          <div className="flex flex-col items-center gap-2 text-gray-500 py-16">
            <p className="text-lg">No products listed yet.</p>
            <p className="text-sm">Check back soon!</p>
          </div>
        )}
        {products.length > 0 && (
          <ul className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {products.map((p) => (
              <li key={p.id} className="border border-gray-200 rounded-lg p-4 flex flex-col gap-1">
                <h2 className="font-semibold">{p.name}</h2>
                {p.description && <p className="text-sm text-gray-600">{p.description}</p>}
                <p className="mt-2 font-mono text-sm">Rs. {(p.price_cents / 100).toFixed(2)}</p>
              </li>
            ))}
          </ul>
        )}
      </div>
    </main>
  );
}

// useSearchParams requires a Suspense boundary in a static export build.
export default function StorefrontPage() {
  return (
    <Suspense fallback={<main className="min-h-screen flex items-center justify-center font-sans"><p className="text-gray-500">Loading store...</p></main>}>
      <Storefront />
    </Suspense>
  );
}