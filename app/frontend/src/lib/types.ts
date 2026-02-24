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
  is_admin: boolean;
  created_at: string;
}

export interface AdminStats {
  total_users: number;
  total_alerts: number;
  active_alerts: number;
  triggered_alerts: number;
  inactive_alerts: number;
  alerts_by_store: Record<string, number>;
  recent_triggered_count_24h: number;
  recent_triggered_count_7d: number;
}

export interface AdminUserListItem {
  id: number;
  email: string | null;
  telegram_id: number | null;
  first_name: string | null;
  subscription_tier: string;
  alert_count: number;
  active_alert_count: number;
  triggered_alert_count: number;
  is_active: boolean;
  created_at: string;
}

export interface AdminUserListResponse {
  users: AdminUserListItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface AdminAlertListItem {
  id: number;
  user_id: number | null;
  user_email: string | null;
  user_first_name: string | null;
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

export interface AdminAlertListResponse {
  alerts: AdminAlertListItem[];
  total: number;
  page: number;
  page_size: number;
}
