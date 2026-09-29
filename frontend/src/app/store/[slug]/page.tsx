"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { apiFetch, ApiError } from "@/lib/api";
import type { ProductPublicOut } from "@/lib/types";

interface StorePublic {
  name: string;
  slug: string;
  created_at: string;
}

type ViewState =
  | { status: "loading" }
  | { status: "not-found" }
  | { status: "found"; store: StorePublic }
  | { status: "error"; message: string };

export default function StorefrontPage() {
  const params = useParams<{ slug: string }>();
  const [view, setView] = useState<ViewState>({ status: "loading" });
  const [products, setProducts] = useState<ProductPublicOut[]>([]);
  const [productsError, setProductsError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const store = await apiFetch<StorePublic>(`/v1/stores/by-slug/${params.slug}`, {
          auth: false,
        });
        if (cancelled) return;
        setView({ status: "found", store });

        try {
          const items = await apiFetch<ProductPublicOut[]>(
            `/v1/products/by-store-slug/${params.slug}`,
            { auth: false }
          );
          if (!cancelled) setProducts(items);
        } catch (err) {
          if (!cancelled) {
            setProductsError(err instanceof ApiError ? err.message : "Failed to load products.");
          }
        }
      } catch (err) {
        if (cancelled) return;
        if (err instanceof ApiError && err.status === 404) {
          setView({ status: "not-found" });
        } else {
          setView({
            status: "error",
            message: err instanceof ApiError ? err.message : "Something went wrong.",
          });
        }
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [params.slug]);

  if (view.status === "loading") {
    return (
      <main className="min-h-screen flex items-center justify-center font-sans">
        <p className="text-gray-500">Loading store...</p>
      </main>
    );
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
    return (
      <main className="min-h-screen flex items-center justify-center font-sans">
        <p className="text-red-600">{view.message}</p>
      </main>
    );
  }

  const { store } = view;

  return (
    <main className="min-h-screen flex flex-col items-center p-8 font-sans">
      <div className="w-full max-w-2xl">
        <header className="border-b border-gray-200 pb-6 mb-8 text-center">
          <h1 className="text-3xl font-bold">{store.name}</h1>
          <p className="text-gray-500 text-sm mt-1">/store/{store.slug}</p>
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
            {products.map((product) => (
              <li key={product.id} className="border border-gray-200 rounded-lg p-4 flex flex-col gap-1">
                <h2 className="font-semibold">{product.name}</h2>
                {product.description && <p className="text-sm text-gray-600">{product.description}</p>}
                <p className="mt-2 font-mono text-sm">Rs. {(product.price_cents / 100).toFixed(2)}</p>
              </li>
            ))}
          </ul>
        )}
      </div>
    </main>
  );
}