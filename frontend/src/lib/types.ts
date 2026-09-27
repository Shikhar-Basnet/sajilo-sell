export interface UserOut {
  id: string;
  email: string;
  is_active: boolean;
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
  created_at: string;
}