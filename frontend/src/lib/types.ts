export interface UserOut {
  id: string;
  email: string;
  is_active: boolean;
  role: "admin" | "seller" | "customer";
  created_at: string;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface StoreOut {
  id: string;
  owner_id: string;
  name: string;
  slug: string;
  description: string | null;
  contact_phone: string | null;
  legal_business_name: string | null;
  owner_full_name: string | null;
  pan_number: string | null;
  status: "pending" | "approved" | "rejected";
  rejection_reason: string | null;
  created_at: string;
}

export interface StorePublicOut {
  name: string;
  slug: string;
  description: string | null;
  contact_phone: string | null;
  created_at: string;
}

export interface ProductOut {
  id: string;
  store_id: string;
  name: string;
  description: string | null;
  price_cents: number;
  is_active: boolean;
  created_at: string;
}

export interface ProductPublicOut {
  id: string;
  name: string;
  description: string | null;
  price_cents: number;
}

export interface SellerDashboardOut {
  store: StoreOut | null;
  products: ProductOut[];
}