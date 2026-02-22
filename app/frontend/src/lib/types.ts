export interface AlertData {
  id: number;
  search_query: string;
  target_price: number;
  store_slugs: string[];
  is_active: boolean;
  is_triggered: boolean;
  triggered_at: string | null;
  last_checked_at: string | null;
  lowest_price_found: number | null;
  lowest_price_store: string | null;
  lowest_price_url: string | null;
  created_at: string;
}

export interface SearchResult {
  product_name: string;
  price: number;
  product_url: string;
  store_slug: string;
  store_name: string;
  image_url: string | null;
  in_stock: boolean;
}

export interface AuthUser {
  id: number;
  email: string | null;
  first_name: string | null;
  language_code: string;
  subscription_tier: string;
  max_alerts: number;
  created_at: string;
}
