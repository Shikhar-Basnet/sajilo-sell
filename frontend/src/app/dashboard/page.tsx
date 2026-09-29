"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch, ApiError, clearTokens, isAuthenticated } from "@/lib/api";
import type { ProductOut, StoreOut, UserOut } from "@/lib/types";
import { Spinner } from "@/components/Spinner";

type MeState =
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "ready"; user: UserOut };

export default function DashboardPage() {
  const router = useRouter();
  const [me, setMe] = useState<MeState>({ status: "loading" });

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace("/login");
      return;
    }
    loadMe();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function loadMe() {
    setMe({ status: "loading" });
    try {
      const user = await apiFetch<UserOut>("/v1/auth/me");
      setMe({ status: "ready", user });
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        router.replace("/login");
      } else {
        setMe({ status: "error", message: err instanceof ApiError ? err.message : "Failed to load your account." });
      }
    }
  }

  function handleLogout() {
    clearTokens();
    router.push("/login");
  }

  return (
    <main className="min-h-screen flex flex-col items-center p-8 font-sans">
      <div className="w-full max-w-2xl">
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-2xl font-bold">Dashboard</h1>
          <button onClick={handleLogout} className="text-sm text-gray-600 underline hover:text-black">
            Log out
          </button>
        </div>

        {me.status === "loading" && <p className="text-gray-600">Loading...</p>}

        {me.status === "error" && (
          <div className="flex flex-col gap-3">
            <p className="text-red-600">{me.message}</p>
            <button onClick={loadMe} className="self-start bg-black text-white rounded-md px-4 py-2 text-sm font-medium">
              Retry
            </button>
          </div>
        )}

        {me.status === "ready" && me.user.role === "seller" && <SellerDashboard />}
        {me.status === "ready" && me.user.role === "admin" && <AdminDashboard />}
        {me.status === "ready" && me.user.role === "customer" && <CustomerDashboard user={me.user} />}
      </div>
    </main>
  );
}

function CustomerDashboard({ user }: { user: UserOut }) {
  return (
    <div className="border border-gray-200 rounded-lg p-6 text-center">
      <p className="text-gray-600 mb-4">Welcome, {user.email}.</p>
      <a href="/browse" className="inline-block bg-black text-white rounded-md px-4 py-2 text-sm font-medium">
        Browse stores
      </a>
    </div>
  );
}

/* ---------- Seller ---------- */

type SellerViewState =
  | { status: "loading" }
  | { status: "no-store" }
  | { status: "has-store"; store: StoreOut }
  | { status: "error"; message: string };

function SellerDashboard() {
  const [view, setView] = useState<SellerViewState>({ status: "loading" });

  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const [products, setProducts] = useState<ProductOut[] | null>(null);
  const [productsError, setProductsError] = useState<string | null>(null);
  const [productActionId, setProductActionId] = useState<string | null>(null);

  const [editingId, setEditingId] = useState<string | null>(null);
  const [pName, setPName] = useState("");
  const [pDescription, setPDescription] = useState("");
  const [pPrice, setPPrice] = useState("");
  const [pFormError, setPFormError] = useState<string | null>(null);
  const [pSubmitting, setPSubmitting] = useState(false);

  // Edit-store / resubmit-after-rejection form
  const [editingStore, setEditingStore] = useState(false);
  const [sName, setSName] = useState("");
  const [sDescription, setSDescription] = useState("");
  const [sPhone, setSPhone] = useState("");
  const [sOwnerFullName, setSOwnerFullName] = useState("");
  const [sLegalBusinessName, setSLegalBusinessName] = useState("");
  const [sPanNumber, setSPanNumber] = useState("");
  const [sFormError, setSFormError] = useState<string | null>(null);
  const [sSubmitting, setSSubmitting] = useState(false);

  useEffect(() => {
    loadStore();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (view.status === "has-store") loadProducts();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [view.status]);

  async function loadStore() {
    setView({ status: "loading" });
    try {
      const store = await apiFetch<StoreOut>("/v1/stores/me");
      setView({ status: "has-store", store });
    } catch (err) {
      if (err instanceof ApiError && err.status === 404) {
        setView({ status: "no-store" });
      } else {
        setView({ status: "error", message: err instanceof ApiError ? err.message : "Failed to load your store." });
      }
    }
  }

  async function loadProducts() {
    try {
      const items = await apiFetch<ProductOut[]>("/v1/products/me");
      setProducts(items);
      setProductsError(null);
    } catch (err) {
      setProductsError(err instanceof ApiError ? err.message : "Failed to load products.");
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

  function resetProductForm() {
    setEditingId(null);
    setPName("");
    setPDescription("");
    setPPrice("");
    setPFormError(null);
  }

  function startEdit(product: ProductOut) {
    setEditingId(product.id);
    setPName(product.name);
    setPDescription(product.description ?? "");
    setPPrice((product.price_cents / 100).toFixed(2));
    setPFormError(null);
  }

  async function handleSubmitProduct(e: React.FormEvent) {
    e.preventDefault();
    setPFormError(null);
    const priceNumber = Number(pPrice);
    if (Number.isNaN(priceNumber) || priceNumber < 0) {
      setPFormError("Enter a valid price.");
      return;
    }
    const price_cents = Math.round(priceNumber * 100);

    setPSubmitting(true);
    try {
      if (editingId) {
        const updated = await apiFetch<ProductOut>(`/v1/products/${editingId}`, {
          method: "PATCH",
          body: JSON.stringify({ name: pName, description: pDescription || null, price_cents }),
        });
        setProducts((prev) => prev?.map((p) => (p.id === updated.id ? updated : p)) ?? [updated]);
      } else {
        const created = await apiFetch<ProductOut>("/v1/products", {
          method: "POST",
          body: JSON.stringify({ name: pName, description: pDescription || null, price_cents, is_active: true }),
        });
        setProducts((prev) => (prev ? [created, ...prev] : [created]));
      }
      resetProductForm();
    } catch (err) {
      setPFormError(err instanceof ApiError ? err.message : "Failed to save product.");
    } finally {
      setPSubmitting(false);
    }
  }

  async function handleToggleActive(product: ProductOut) {
    setProductActionId(product.id);
    try {
      const updated = await apiFetch<ProductOut>(`/v1/products/${product.id}`, {
        method: "PATCH",
        body: JSON.stringify({ is_active: !product.is_active }),
      });
      setProducts((prev) => prev?.map((p) => (p.id === updated.id ? updated : p)) ?? null);
    } catch (err) {
      setProductsError(err instanceof ApiError ? err.message : "Failed to update product.");
    } finally {
      setProductActionId(null);
    }
  }

  async function handleDeleteProduct(id: string) {
    if (!confirm("Delete this product? This can't be undone.")) return;
    setProductActionId(id);
    try {
      await apiFetch(`/v1/products/${id}`, { method: "DELETE" });
      setProducts((prev) => prev?.filter((p) => p.id !== id) ?? null);
    } catch (err) {
      setProductsError(err instanceof ApiError ? err.message : "Failed to delete product.");
    } finally {
      setProductActionId(null);
    }
  }

  function startEditStore(store: StoreOut) {
    setSName(store.name);
    setSDescription(store.description ?? "");
    setSPhone(store.contact_phone ?? "");
    setSOwnerFullName(store.owner_full_name ?? "");
    setSLegalBusinessName(store.legal_business_name ?? "");
    setSPanNumber(store.pan_number ?? "");
    setSFormError(null);
    setEditingStore(true);
  }

  async function handleSubmitStoreEdit(e: React.FormEvent) {
    e.preventDefault();
    setSFormError(null);
    setSSubmitting(true);
    try {
      const updated = await apiFetch<StoreOut>("/v1/stores/me", {
        method: "PATCH",
        body: JSON.stringify({
          name: sName,
          description: sDescription || null,
          contact_phone: sPhone || null,
          owner_full_name: sOwnerFullName,
          legal_business_name: sLegalBusinessName,
          pan_number: sPanNumber,
        }),
      });
      setView({ status: "has-store", store: updated });
      setEditingStore(false);
    } catch (err) {
      setSFormError(err instanceof ApiError ? err.message : "Failed to update store.");
    } finally {
      setSSubmitting(false);
    }
  }

  if (view.status === "loading") return <p className="text-gray-600">Loading...</p>;

  if (view.status === "error") {
    return (
      <div className="flex flex-col gap-3">
        <p className="text-red-600">{view.message}</p>
        <button onClick={loadStore} className="self-start bg-black text-white rounded-md px-4 py-2 text-sm font-medium">
          Retry
        </button>
      </div>
    );
  }

  if (view.status === "no-store") {
    return (
      <div>
        <p className="text-gray-600 mb-4">You don&apos;t have a store yet. Create one to get started.</p>
        <form onSubmit={handleCreateStore} className="flex flex-col gap-4">
          <div className="flex flex-col gap-1">
            <label htmlFor="name" className="text-sm font-medium text-gray-700">Store name</label>
            <input
              id="name" type="text" required minLength={2} maxLength={255} value={name}
              onChange={(e) => setName(e.target.value)}
              className="border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-black"
            />
          </div>
          <div className="flex flex-col gap-1">
            <label htmlFor="slug" className="text-sm font-medium text-gray-700">Slug</label>
            <input
              id="slug" type="text" required minLength={2} maxLength={255} pattern="[a-z0-9-]+"
              title="Lowercase letters, numbers, and hyphens only" value={slug}
              onChange={(e) => setSlug(e.target.value)}
              className="border border-gray-300 rounded-md px-3 py-2 font-mono focus:outline-none focus:ring-2 focus:ring-black"
            />
          </div>
          {formError && <p className="text-sm text-red-600">{formError}</p>}
          <button
            type="submit" disabled={submitting}
            className="bg-black text-white rounded-md py-2 font-medium disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {submitting && <Spinner className="text-white" />}
            {submitting ? "Creating..." : "Create store"}
          </button>
        </form>
      </div>
    );
  }

  const { store } = view;
  const statusBanner = {
    pending: { text: "Pending admin approval — your storefront isn't public yet.", cls: "bg-yellow-50 text-yellow-800 border-yellow-200" },
    approved: { text: "Approved — your storefront is live.", cls: "bg-green-50 text-green-800 border-green-200" },
    rejected: { text: "Your store application was rejected.", cls: "bg-red-50 text-red-800 border-red-200" },
  }[store.status];

  return (
    <>
      <div className={`border rounded-md px-4 py-2 text-sm mb-2 ${statusBanner.cls}`}>{statusBanner.text}</div>

      {store.status === "rejected" && store.rejection_reason && (
        <div className="border border-red-200 bg-red-50 rounded-md px-4 py-3 text-sm text-red-800 mb-4">
          <p className="font-medium mb-1">Reason from admin:</p>
          <p>{store.rejection_reason}</p>
        </div>
      )}

      <div className="border border-gray-200 rounded-lg p-6 mb-8">
        {!editingStore ? (
          <>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">{store.name}</h2>
              {store.status !== "approved" && (
                <button onClick={() => startEditStore(store)} className="text-sm underline">
                  {store.status === "rejected" ? "Edit & resubmit" : "Edit details"}
                </button>
              )}
            </div>
            <dl className="flex flex-col gap-2 text-sm">
              <div className="flex justify-between"><dt className="text-gray-500">Slug</dt><dd className="font-mono">{store.slug}</dd></div>
              <div className="flex justify-between"><dt className="text-gray-500">Status</dt><dd className="capitalize">{store.status}</dd></div>
              <div className="flex justify-between"><dt className="text-gray-500">Owner name</dt><dd>{store.owner_full_name || "—"}</dd></div>
              <div className="flex justify-between"><dt className="text-gray-500">Company name</dt><dd>{store.legal_business_name || "—"}</dd></div>
              <div className="flex justify-between"><dt className="text-gray-500">PAN</dt><dd className="font-mono">{store.pan_number || "—"}</dd></div>
              <div className="flex justify-between"><dt className="text-gray-500">Created</dt><dd>{new Date(store.created_at).toLocaleDateString()}</dd></div>
            </dl>
            {store.status === "approved" && (
              <a href={`/store/${store.slug}`} target="_blank" rel="noopener noreferrer" className="inline-block mt-4 text-sm text-black underline">
                View your storefront →
              </a>
            )}
          </>
        ) : (
          <form onSubmit={handleSubmitStoreEdit} className="flex flex-col gap-3">
            <h2 className="text-lg font-semibold mb-1">
              {store.status === "rejected" ? "Edit & resubmit for approval" : "Edit store details"}
            </h2>
            <div className="flex flex-col gap-1">
              <label className="text-sm font-medium text-gray-700">Store name</label>
              <input
                type="text" required minLength={2} maxLength={255} value={sName}
                onChange={(e) => setSName(e.target.value)}
                className="border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-black"
              />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-sm font-medium text-gray-700">Description</label>
              <textarea
                rows={2} value={sDescription}
                onChange={(e) => setSDescription(e.target.value)}
                className="border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-black"
              />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-sm font-medium text-gray-700">Contact phone</label>
              <input
                type="tel" value={sPhone}
                onChange={(e) => setSPhone(e.target.value)}
                className="border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-black"
              />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-sm font-medium text-gray-700">Owner&apos;s full name</label>
              <input
                type="text" required minLength={2} maxLength={255} value={sOwnerFullName}
                onChange={(e) => setSOwnerFullName(e.target.value)}
                className="border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-black"
              />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-sm font-medium text-gray-700">Registered company name</label>
              <input
                type="text" required minLength={2} maxLength={255} value={sLegalBusinessName}
                onChange={(e) => setSLegalBusinessName(e.target.value)}
                className="border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-black"
              />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-sm font-medium text-gray-700">Business PAN number</label>
              <input
                type="text" required minLength={5} maxLength={50} value={sPanNumber}
                onChange={(e) => setSPanNumber(e.target.value)}
                className="border border-gray-300 rounded-md px-3 py-2 font-mono focus:outline-none focus:ring-2 focus:ring-black"
              />
            </div>

            {sFormError && <p className="text-sm text-red-600">{sFormError}</p>}

            <div className="flex gap-2">
              <button
                type="submit" disabled={sSubmitting}
                className="bg-black text-white rounded-md px-4 py-2 text-sm font-medium disabled:opacity-50 flex items-center gap-2"
              >
                {sSubmitting && <Spinner className="text-white" />}
                {sSubmitting ? "Saving..." : store.status === "rejected" ? "Resubmit for approval" : "Save changes"}
              </button>
              <button type="button" onClick={() => setEditingStore(false)} className="text-sm text-gray-600 underline">
                Cancel
              </button>
            </div>
          </form>
        )}
      </div>

      <div className="border border-gray-200 rounded-lg p-6">
        <h2 className="text-lg font-semibold mb-4">{editingId ? "Edit product" : "Add a product"}</h2>
        <form onSubmit={handleSubmitProduct} className="flex flex-col gap-3 mb-6">
          <input
            type="text" placeholder="Product name" required value={pName}
            onChange={(e) => setPName(e.target.value)}
            className="border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-black"
          />
          <textarea
            placeholder="Description (optional)" value={pDescription} rows={2}
            onChange={(e) => setPDescription(e.target.value)}
            className="border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-black"
          />
          <input
            type="number" step="0.01" min="0" placeholder="Price (e.g. 499.00)" required value={pPrice}
            onChange={(e) => setPPrice(e.target.value)}
            className="border border-gray-300 rounded-md px-3 py-2 font-mono focus:outline-none focus:ring-2 focus:ring-black"
          />
          {pFormError && <p className="text-sm text-red-600">{pFormError}</p>}
          <div className="flex gap-2">
            <button
              type="submit" disabled={pSubmitting}
              className="bg-black text-white rounded-md px-4 py-2 text-sm font-medium disabled:opacity-50 flex items-center gap-2"
            >
              {pSubmitting && <Spinner className="text-white" />}
              {pSubmitting ? "Saving..." : editingId ? "Save changes" : "Add product"}
            </button>
            {editingId && <button type="button" onClick={resetProductForm} className="text-sm text-gray-600 underline">Cancel</button>}
          </div>
        </form>

        <h3 className="text-sm font-semibold text-gray-500 mb-2">Your products</h3>
        {productsError && <p className="text-sm text-red-600 mb-2">{productsError}</p>}
        {products === null && !productsError && <p className="text-sm text-gray-500">Loading products...</p>}
        {products !== null && products.length === 0 && <p className="text-sm text-gray-500">No products yet.</p>}

        <ul className="flex flex-col gap-2">
          {products?.map((product) => {
            const isBusy = productActionId === product.id;
            return (
              <li key={product.id} className="flex items-center justify-between border border-gray-200 rounded-md px-3 py-2">
                <div>
                  <p className={`font-medium ${!product.is_active ? "text-gray-400 line-through" : ""}`}>{product.name}</p>
                  <p className="text-xs text-gray-500 font-mono">Rs. {(product.price_cents / 100).toFixed(2)}</p>
                </div>
                <div className="flex items-center gap-3 text-xs">
                  {isBusy && <Spinner className="h-3 w-3 text-gray-500" />}
                  <button onClick={() => startEdit(product)} disabled={isBusy} className="underline disabled:opacity-40">Edit</button>
                  <button onClick={() => handleToggleActive(product)} disabled={isBusy} className="underline disabled:opacity-40">
                    {product.is_active ? "Hide" : "Unhide"}
                  </button>
                  <button onClick={() => handleDeleteProduct(product.id)} disabled={isBusy} className="underline text-red-600 disabled:opacity-40">
                    Delete
                  </button>
                </div>
              </li>
            );
          })}
        </ul>
      </div>
    </>
  );
}

/* ---------- Admin ---------- */

function AdminDashboard() {
  const [pendingStores, setPendingStores] = useState<StoreOut[] | null>(null);
  const [users, setUsers] = useState<UserOut[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [storeActionId, setStoreActionId] = useState<string | null>(null);
  const [userActionId, setUserActionId] = useState<string | null>(null);

  useEffect(() => {
    loadPending();
    loadUsers();
  }, []);

  async function loadPending() {
    try {
      const stores = await apiFetch<StoreOut[]>("/v1/admin/stores?status=pending");
      setPendingStores(stores);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load pending stores.");
    }
  }

  async function loadUsers() {
    try {
      const list = await apiFetch<UserOut[]>("/v1/admin/users");
      setUsers(list);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load users.");
    }
  }

  async function handleApprove(storeId: string) {
    setStoreActionId(storeId);
    try {
      await apiFetch(`/v1/admin/stores/${storeId}/approve`, { method: "POST" });
      setPendingStores((prev) => prev?.filter((s) => s.id !== storeId) ?? null);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to approve store.");
    } finally {
      setStoreActionId(null);
    }
  }

  async function handleReject(storeId: string) {
    const reason = prompt("Reason for rejection (shown to the seller):") ?? undefined;
    setStoreActionId(storeId);
    try {
      await apiFetch(`/v1/admin/stores/${storeId}/reject`, {
        method: "POST",
        body: JSON.stringify({ reason: reason || null }),
      });
      setPendingStores((prev) => prev?.filter((s) => s.id !== storeId) ?? null);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to reject store.");
    } finally {
      setStoreActionId(null);
    }
  }

  async function handleToggleUserActive(user: UserOut) {
    setUserActionId(user.id);
    try {
      const updated = await apiFetch<UserOut>(`/v1/admin/users/${user.id}/set-active`, {
        method: "POST",
        body: JSON.stringify({ is_active: !user.is_active }),
      });
      setUsers((prev) => prev?.map((u) => (u.id === updated.id ? updated : u)) ?? null);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to update user.");
    } finally {
      setUserActionId(null);
    }
  }

  return (
    <div className="flex flex-col gap-8">
      {error && <p className="text-sm text-red-600">{error}</p>}

      <div className="border border-gray-200 rounded-lg p-6">
        <h2 className="text-lg font-semibold mb-4">Pending seller applications</h2>
        {pendingStores === null && <p className="text-sm text-gray-500">Loading...</p>}
        {pendingStores !== null && pendingStores.length === 0 && (
          <p className="text-sm text-gray-500">Nothing pending review.</p>
        )}
        <ul className="flex flex-col gap-2">
          {pendingStores?.map((store) => {
            const isBusy = storeActionId === store.id;
            return (
              <li key={store.id} className="border border-gray-200 rounded-md px-3 py-3">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">{store.name}</p>
                    <p className="text-xs text-gray-500 font-mono">/{store.slug}</p>
                  </div>
                  <div className="flex items-center gap-3 text-xs">
                    {isBusy && <Spinner className="h-3 w-3 text-gray-500" />}
                    <button
                      onClick={() => handleApprove(store.id)} disabled={isBusy}
                      className="bg-black text-white rounded px-3 py-1 disabled:opacity-50"
                    >
                      Approve
                    </button>
                    <button
                      onClick={() => handleReject(store.id)} disabled={isBusy}
                      className="border border-gray-300 rounded px-3 py-1 disabled:opacity-50"
                    >
                      Reject
                    </button>
                  </div>
                </div>
                <dl className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs text-gray-600 mt-3">
                  <div><dt className="inline text-gray-400">Owner: </dt><dd className="inline">{store.owner_full_name || "—"}</dd></div>
                  <div><dt className="inline text-gray-400">Company: </dt><dd className="inline">{store.legal_business_name || "—"}</dd></div>
                  <div><dt className="inline text-gray-400">PAN: </dt><dd className="inline font-mono">{store.pan_number || "—"}</dd></div>
                  <div><dt className="inline text-gray-400">Phone: </dt><dd className="inline">{store.contact_phone || "—"}</dd></div>
                </dl>
                {store.description && <p className="text-sm text-gray-600 mt-2">{store.description}</p>}
              </li>
            );
          })}
        </ul>
      </div>

      <div className="border border-gray-200 rounded-lg p-6">
        <h2 className="text-lg font-semibold mb-4">Users</h2>
        {users === null && <p className="text-sm text-gray-500">Loading...</p>}
        <ul className="flex flex-col gap-2">
          {users?.map((user) => {
            const isBusy = userActionId === user.id;
            return (
              <li key={user.id} className="flex items-center justify-between border border-gray-200 rounded-md px-3 py-2">
                <div>
                  <p className={`text-sm ${!user.is_active ? "text-gray-400" : ""}`}>{user.email}</p>
                  <p className="text-xs text-gray-500 capitalize">{user.role}{!user.is_active ? " · deactivated" : ""}</p>
                </div>
                {user.role !== "admin" && (
                  <div className="flex items-center gap-2">
                    {isBusy && <Spinner className="h-3 w-3 text-gray-500" />}
                    <button onClick={() => handleToggleUserActive(user)} disabled={isBusy} className="text-xs underline disabled:opacity-50">
                      {user.is_active ? "Deactivate" : "Reactivate"}
                    </button>
                  </div>
                )}
              </li>
            );
          })}
        </ul>
      </div>
    </div>
  );
}