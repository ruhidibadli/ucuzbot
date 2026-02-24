import { API_BASE } from "./constants";
import type {
  AdminAlertListResponse,
  AdminStats,
  AdminUserListResponse,
  AlertData,
  AuthUser,
  SearchResult,
} from "./types";

export function getAuthHeaders(token: string | null): Record<string, string> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  return headers;
}

export async function validateToken(token: string): Promise<AuthUser | null> {
  try {
    const res = await fetch(`${API_BASE}/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (res.ok) {
      return await res.json();
    }
    return null;
  } catch {
    return null;
  }
}

export async function loginApi(
  email: string,
  password: string
): Promise<{ access_token: string; user: AuthUser }> {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || "Authentication failed");
  }
  return data;
}

export async function registerApi(
  email: string,
  password: string,
  firstName?: string
): Promise<{ access_token: string; user: AuthUser }> {
  const body: Record<string, string> = { email, password };
  if (firstName?.trim()) {
    body.first_name = firstName.trim();
  }
  const res = await fetch(`${API_BASE}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || "Registration failed");
  }
  return data;
}

export async function fetchAlerts(token: string): Promise<AlertData[]> {
  const res = await fetch(`${API_BASE}/alerts/me`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (res.ok) {
    return await res.json();
  }
  return [];
}

export async function fetchAlertsByPush(endpoint: string): Promise<AlertData[]> {
  const res = await fetch(`${API_BASE}/alerts/by-push`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ endpoint }),
  });
  if (res.ok) {
    return await res.json();
  }
  return [];
}

export async function createAlert(
  token: string | null,
  searchQuery: string,
  targetPrice: number,
  storeSlugs: string[],
  pushEndpoint?: string | null
): Promise<void> {
  const body: Record<string, unknown> = {
    search_query: searchQuery,
    target_price: targetPrice,
    store_slugs: storeSlugs,
  };
  if (!token && pushEndpoint) {
    body.push_endpoint = pushEndpoint;
  }
  const res = await fetch(`${API_BASE}/alerts`, {
    method: "POST",
    headers: getAuthHeaders(token),
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const data = await res.json();
    throw new Error(data.detail || "Failed to create alert");
  }
}

export async function deleteAlert(token: string | null, alertId: number): Promise<boolean> {
  const res = await fetch(`${API_BASE}/alerts/${alertId}`, {
    method: "DELETE",
    headers: getAuthHeaders(token),
  });
  return res.ok;
}

export async function checkAlertNow(token: string | null, alertId: number): Promise<void> {
  await fetch(`${API_BASE}/alerts/${alertId}/check`, {
    method: "POST",
    headers: getAuthHeaders(token),
  });
}

export async function fetchAdminStats(token: string): Promise<AdminStats> {
  const res = await fetch(`${API_BASE}/admin/stats`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("Failed to fetch admin stats");
  return res.json();
}

export async function fetchAdminUsers(
  token: string,
  page = 1,
  pageSize = 20,
  search = ""
): Promise<AdminUserListResponse> {
  const params = new URLSearchParams({
    page: String(page),
    page_size: String(pageSize),
  });
  if (search.trim()) params.set("search", search.trim());
  const res = await fetch(`${API_BASE}/admin/users?${params}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("Failed to fetch admin users");
  return res.json();
}

export async function fetchAdminAlerts(
  token: string,
  page = 1,
  pageSize = 20,
  statusFilter = "all",
  storeSlug = ""
): Promise<AdminAlertListResponse> {
  const params = new URLSearchParams({
    page: String(page),
    page_size: String(pageSize),
    status_filter: statusFilter,
  });
  if (storeSlug.trim()) params.set("store_slug", storeSlug.trim());
  const res = await fetch(`${API_BASE}/admin/alerts?${params}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("Failed to fetch admin alerts");
  return res.json();
}

export async function searchProducts(query: string): Promise<SearchResult[]> {
  const res = await fetch(
    `${API_BASE}/search?q=${encodeURIComponent(query)}`
  );
  if (!res.ok) {
    const data = await res.json();
    throw new Error(data.detail || "Search failed");
  }
  const data = await res.json();
  return data.results || [];
}
