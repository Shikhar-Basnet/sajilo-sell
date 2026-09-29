"use client";

import Link from "next/link";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch, ApiError, setTokens } from "@/lib/api";
import type { TokenPair } from "@/lib/types";
import { Spinner } from "@/components/Spinner";

type Role = "customer" | "seller";

export default function RegisterPage() {
  const router = useRouter();
  const [role, setRole] = useState<Role>("customer");

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const [storeName, setStoreName] = useState("");
  const [storeSlug, setStoreSlug] = useState("");
  const [storeDescription, setStoreDescription] = useState("");
  const [storePhone, setStorePhone] = useState("");
  const [ownerFullName, setOwnerFullName] = useState("");
  const [legalBusinessName, setLegalBusinessName] = useState("");
  const [panNumber, setPanNumber] = useState("");

  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }
    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }

    setLoading(true);
    try {
      if (role === "customer") {
        await apiFetch("/v1/auth/register/customer", {
          method: "POST",
          auth: false,
          body: JSON.stringify({ email, password }),
        });
      } else {
        await apiFetch("/v1/auth/register/seller", {
          method: "POST",
          auth: false,
          body: JSON.stringify({
            email,
            password,
            store: {
              name: storeName,
              slug: storeSlug,
              description: storeDescription || null,
              contact_phone: storePhone || null,
              owner_full_name: ownerFullName,
              legal_business_name: legalBusinessName,
              pan_number: panNumber,
            },
          }),
        });
      }

      const tokens = await apiFetch<TokenPair>("/v1/auth/login", {
        method: "POST",
        auth: false,
        body: JSON.stringify({ email, password }),
      });
      setTokens(tokens.access_token, tokens.refresh_token);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen flex flex-col items-center justify-center p-8 font-sans">
      <div className="w-full max-w-sm">
        <h1 className="text-2xl font-bold mb-2 text-center">Create your account</h1>

        <div className="flex border border-gray-300 rounded-md overflow-hidden mb-6 text-sm">
          <button
            type="button"
            onClick={() => setRole("customer")}
            className={`flex-1 py-2 font-medium ${role === "customer" ? "bg-black text-white" : "bg-white text-gray-700"}`}
          >
            I&apos;m a customer
          </button>
          <button
            type="button"
            onClick={() => setRole("seller")}
            className={`flex-1 py-2 font-medium ${role === "seller" ? "bg-black text-white" : "bg-white text-gray-700"}`}
          >
            I&apos;m a seller
          </button>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div className="flex flex-col gap-1">
            <label htmlFor="email" className="text-sm font-medium text-gray-700">Email</label>
            <input
              id="email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-black"
            />
          </div>

          <div className="flex flex-col gap-1">
            <label htmlFor="password" className="text-sm font-medium text-gray-700">Password</label>
            <input
              id="password"
              type="password"
              required
              minLength={8}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-black"
            />
          </div>

          <div className="flex flex-col gap-1">
            <label htmlFor="confirmPassword" className="text-sm font-medium text-gray-700">Confirm password</label>
            <input
              id="confirmPassword"
              type="password"
              required
              minLength={8}
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-black"
            />
          </div>

          {role === "seller" && (
            <div className="border-t border-gray-200 pt-4 flex flex-col gap-4">
              <p className="text-xs text-gray-500">
                Shop details — your store will be reviewed by an admin before it&apos;s visible to customers.
              </p>

              <div className="flex flex-col gap-1">
                <label htmlFor="ownerFullName" className="text-sm font-medium text-gray-700">Owner&apos;s full name</label>
                <input
                  id="ownerFullName"
                  type="text"
                  required
                  minLength={2}
                  maxLength={255}
                  value={ownerFullName}
                  onChange={(e) => setOwnerFullName(e.target.value)}
                  className="border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-black"
                />
              </div>

              <div className="flex flex-col gap-1">
                <label htmlFor="legalBusinessName" className="text-sm font-medium text-gray-700">Registered company name</label>
                <input
                  id="legalBusinessName"
                  type="text"
                  required
                  minLength={2}
                  maxLength={255}
                  value={legalBusinessName}
                  onChange={(e) => setLegalBusinessName(e.target.value)}
                  className="border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-black"
                />
              </div>

              <div className="flex flex-col gap-1">
                <label htmlFor="panNumber" className="text-sm font-medium text-gray-700">Business PAN number</label>
                <input
                  id="panNumber"
                  type="text"
                  required
                  minLength={5}
                  maxLength={50}
                  value={panNumber}
                  onChange={(e) => setPanNumber(e.target.value)}
                  className="border border-gray-300 rounded-md px-3 py-2 font-mono focus:outline-none focus:ring-2 focus:ring-black"
                />
              </div>

              <div className="flex flex-col gap-1">
                <label htmlFor="storeName" className="text-sm font-medium text-gray-700">Shop name</label>
                <input
                  id="storeName"
                  type="text"
                  required
                  minLength={2}
                  maxLength={255}
                  value={storeName}
                  onChange={(e) => setStoreName(e.target.value)}
                  className="border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-black"
                />
              </div>

              <div className="flex flex-col gap-1">
                <label htmlFor="storeSlug" className="text-sm font-medium text-gray-700">Shop URL slug</label>
                <input
                  id="storeSlug"
                  type="text"
                  required
                  minLength={2}
                  maxLength={255}
                  pattern="[a-z0-9-]+"
                  title="Lowercase letters, numbers, and hyphens only"
                  value={storeSlug}
                  onChange={(e) => setStoreSlug(e.target.value)}
                  className="border border-gray-300 rounded-md px-3 py-2 font-mono focus:outline-none focus:ring-2 focus:ring-black"
                />
              </div>

              <div className="flex flex-col gap-1">
                <label htmlFor="storeDescription" className="text-sm font-medium text-gray-700">Description (optional)</label>
                <textarea
                  id="storeDescription"
                  rows={2}
                  value={storeDescription}
                  onChange={(e) => setStoreDescription(e.target.value)}
                  className="border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-black"
                />
              </div>

              <div className="flex flex-col gap-1">
                <label htmlFor="storePhone" className="text-sm font-medium text-gray-700">Contact phone (optional)</label>
                <input
                  id="storePhone"
                  type="tel"
                  value={storePhone}
                  onChange={(e) => setStorePhone(e.target.value)}
                  className="border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-black"
                />
              </div>
            </div>
          )}

          {error && <p className="text-sm text-red-600">{error}</p>}

          <button
            type="submit"
            disabled={loading}
            className="bg-black text-white rounded-md py-2 font-medium disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {loading && <Spinner className="text-white" />}
            {loading ? "Creating account..." : "Create account"}
          </button>
        </form>

        <p className="text-sm text-gray-600 text-center mt-6">
          Already have an account?{" "}
          <Link href="/login" className="text-black font-medium underline">Log in</Link>
        </p>
      </div>
    </main>
  );
}