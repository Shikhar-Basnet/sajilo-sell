"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch, ApiError, clearTokens, isAuthenticated } from "@/lib/api";
import type { StoreOut } from "@/lib/types";

type ViewState =
  | { status: "loading" }
  | { status: "no-store" }
  | { status: "has-store"; store: StoreOut }
  | { status: "error"; message: string };

export default function DashboardPage() {
  const router = useRouter();
  const [view, setView] = useState<ViewState>({ status: "loading" });

  // Create-store form state
  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace("/login");
      return;
    }
    loadStore();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function loadStore() {
    setView({ status: "loading" });
    try {
      const store = await apiFetch<StoreOut>("/v1/stores/me");
      setView({ status: "has-store", store });
    } catch (err) {
      if (err instanceof ApiError && err.status === 404) {
        setView({ status: "no-store" });
      } else if (err instanceof ApiError && err.status === 401) {
        router.replace("/login");
      } else {
        setView({
          status: "error",
          message: err instanceof ApiError ? err.message : "Failed to load your store.",
        });
      }
    }
  }

  async function handleCreateStore(e: React.FormEvent) {
    e.preventDefault();
    setFormError(null);
    setSubmitting(true);
    try {
      const store = await apiFetch<StoreOut>("/v1/stores", {
        method: "POST",
        body: JSON.stringify({ name, slug }),
      });
      setView({ status: "has-store", store });
    } catch (err) {
      setFormError(err instanceof ApiError ? err.message : "Failed to create store.");
    } finally {
      setSubmitting(false);
    }
  }

  function handleLogout() {
    clearTokens();
    router.push("/login");
  }

  return (
    <main className="min-h-screen flex flex-col items-center p-8 font-sans">
      <div className="w-full max-w-lg">
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-2xl font-bold">Dashboard</h1>
          <button
            onClick={handleLogout}
            className="text-sm text-gray-600 underline hover:text-black"
          >
            Log out
          </button>
        </div>

        {view.status === "loading" && <p className="text-gray-600">Loading...</p>}

        {view.status === "error" && (
          <div className="flex flex-col gap-3">
            <p className="text-red-600">{view.message}</p>
            <button
              onClick={loadStore}
              className="self-start bg-black text-white rounded-md px-4 py-2 text-sm font-medium"
            >
              Retry
            </button>
          </div>
        )}

        {view.status === "has-store" && (
          <div className="border border-gray-200 rounded-lg p-6">
            <h2 className="text-lg font-semibold mb-4">{view.store.name}</h2>
            <dl className="flex flex-col gap-2 text-sm">
              <div className="flex justify-between">
                <dt className="text-gray-500">Slug</dt>
                <dd className="font-mono">{view.store.slug}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">Store ID</dt>
                <dd className="font-mono text-xs">{view.store.id}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">Created</dt>
                <dd>{new Date(view.store.created_at).toLocaleDateString()}</dd>
              </div>
            </dl>
          </div>
        )}

        {view.status === "no-store" && (
          <div>
            <p className="text-gray-600 mb-4">
              You don&apos;t have a store yet. Create one to get started.
            </p>
            <form onSubmit={handleCreateStore} className="flex flex-col gap-4">
              <div className="flex flex-col gap-1">
                <label htmlFor="name" className="text-sm font-medium text-gray-700">
                  Store name
                </label>
                <input
                  id="name"
                  type="text"
                  required
                  minLength={2}
                  maxLength={255}
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-black"
                />
              </div>

              <div className="flex flex-col gap-1">
                <label htmlFor="slug" className="text-sm font-medium text-gray-700">
                  Slug
                </label>
                <input
                  id="slug"
                  type="text"
                  required
                  minLength={2}
                  maxLength={255}
                  pattern="[a-z0-9-]+"
                  title="Lowercase letters, numbers, and hyphens only"
                  value={slug}
                  onChange={(e) => setSlug(e.target.value)}
                  className="border border-gray-300 rounded-md px-3 py-2 font-mono focus:outline-none focus:ring-2 focus:ring-black"
                />
                <p className="text-xs text-gray-500">Lowercase letters, numbers, and hyphens only.</p>
              </div>

              {formError && <p className="text-sm text-red-600">{formError}</p>}

              <button
                type="submit"
                disabled={submitting}
                className="bg-black text-white rounded-md py-2 font-medium disabled:opacity-50"
              >
                {submitting ? "Creating..." : "Create store"}
              </button>
            </form>
          </div>
        )}
      </div>
    </main>
  );
}