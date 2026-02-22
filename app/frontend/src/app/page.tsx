"use client";

import { useState, useEffect, useCallback } from "react";

const API_BASE = "/api/v1";

const stores = [
  { slug: "kontakt", name: "Kontakt Home", type: "Elektronika", icon: "\u{1F3EA}" },
  { slug: "baku_electronics", name: "Baku Electronics", type: "Elektronika", icon: "\u{1F4BB}" },
  { slug: "irshad", name: "Irshad", type: "Elektronika", icon: "\u{1F4F1}" },
  { slug: "maxi", name: "Maxi.az", type: "Marketplace", icon: "\u{1F6D2}" },
  { slug: "tap_az", name: "Tap.az", type: "Elanlar", icon: "\u{1F4CB}" },
  { slug: "umico", name: "Umico", type: "Marketplace", icon: "\u{1F381}" },
];

function urlBase64ToUint8Array(base64String: string): ArrayBuffer {
  const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/");
  const rawData = atob(base64);
  const outputArray = new Uint8Array(rawData.length);
  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray.buffer as ArrayBuffer;
}

interface AlertData {
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

interface SearchResult {
  product_name: string;
  price: number;
  product_url: string;
  store_slug: string;
  store_name: string;
  image_url: string | null;
  in_stock: boolean;
}

interface AuthUser {
  id: number;
  email: string | null;
  first_name: string | null;
  language_code: string;
  subscription_tier: string;
  max_alerts: number;
  created_at: string;
}

export default function Home() {
  // Auth state
  const [authUser, setAuthUser] = useState<AuthUser | null>(null);
  const [authToken, setAuthToken] = useState<string | null>(null);
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [authMode, setAuthMode] = useState<"login" | "register">("login");
  const [authEmail, setAuthEmail] = useState("");
  const [authPassword, setAuthPassword] = useState("");
  const [authFirstName, setAuthFirstName] = useState("");
  const [authError, setAuthError] = useState<string | null>(null);
  const [authLoading, setAuthLoading] = useState(false);

  // Push state
  const [pushSupported, setPushSupported] = useState(false);
  const [pushSubscribed, setPushSubscribed] = useState(false);
  const [pushEndpoint, setPushEndpoint] = useState<string | null>(null);
  const [pushLoading, setPushLoading] = useState(false);
  const [pushError, setPushError] = useState<string | null>(null);

  // Alert form state
  const [searchQuery, setSearchQuery] = useState("");
  const [targetPrice, setTargetPrice] = useState("");
  const [selectedStores, setSelectedStores] = useState<string[]>(
    stores.map((s) => s.slug)
  );
  const [alertStatus, setAlertStatus] = useState<{
    type: "success" | "error" | "info";
    message: string;
  } | null>(null);
  const [alertLoading, setAlertLoading] = useState(false);

  // My alerts state
  const [myAlerts, setMyAlerts] = useState<AlertData[]>([]);
  const [alertsLoading, setAlertsLoading] = useState(false);

  // Search state
  const [productSearch, setProductSearch] = useState("");
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState(false);

  // Check now loading state
  const [checkingAlertId, setCheckingAlertId] = useState<number | null>(null);

  // Auth helpers
  function getAuthHeaders(): Record<string, string> {
    const headers: Record<string, string> = { "Content-Type": "application/json" };
    if (authToken) {
      headers["Authorization"] = `Bearer ${authToken}`;
    }
    return headers;
  }

  const validateToken = useCallback(async (token: string) => {
    try {
      const res = await fetch(`${API_BASE}/auth/me`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const user = await res.json();
        setAuthUser(user);
        setAuthToken(token);
        return true;
      }
      localStorage.removeItem("ucuzbot_token");
      return false;
    } catch {
      return false;
    }
  }, []);

  // Load token on mount
  useEffect(() => {
    const token = localStorage.getItem("ucuzbot_token");
    if (token) {
      validateToken(token);
    }
  }, [validateToken]);

  async function handleAuth(e: React.FormEvent) {
    e.preventDefault();
    setAuthError(null);
    setAuthLoading(true);
    try {
      const endpoint = authMode === "register" ? "/auth/register" : "/auth/login";
      const body: Record<string, string> = { email: authEmail, password: authPassword };
      if (authMode === "register" && authFirstName.trim()) {
        body.first_name = authFirstName.trim();
      }
      const res = await fetch(`${API_BASE}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Authentication failed");
      }
      localStorage.setItem("ucuzbot_token", data.access_token);
      setAuthToken(data.access_token);
      setAuthUser(data.user);
      setShowAuthModal(false);
      setAuthEmail("");
      setAuthPassword("");
      setAuthFirstName("");
    } catch (err: unknown) {
      setAuthError(err instanceof Error ? err.message : "Authentication failed");
    } finally {
      setAuthLoading(false);
    }
  }

  function handleLogout() {
    localStorage.removeItem("ucuzbot_token");
    setAuthToken(null);
    setAuthUser(null);
    setMyAlerts([]);
  }

  // Fetch alerts for authenticated user
  const fetchMyAlertsAuth = useCallback(async (token: string) => {
    setAlertsLoading(true);
    try {
      const res = await fetch(`${API_BASE}/alerts/me`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        setMyAlerts(await res.json());
      }
    } catch {
      // ignore
    } finally {
      setAlertsLoading(false);
    }
  }, []);

  // Fetch alerts for push-subscribed user
  const fetchMyAlertsPush = useCallback(async (endpoint: string) => {
    setAlertsLoading(true);
    try {
      const res = await fetch(`${API_BASE}/alerts/by-push`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ endpoint }),
      });
      if (res.ok) {
        setMyAlerts(await res.json());
      }
    } catch {
      // ignore
    } finally {
      setAlertsLoading(false);
    }
  }, []);

  // Combined fetch alerts
  const fetchMyAlerts = useCallback(() => {
    if (authToken) {
      fetchMyAlertsAuth(authToken);
    } else if (pushEndpoint) {
      fetchMyAlertsPush(pushEndpoint);
    }
  }, [authToken, pushEndpoint, fetchMyAlertsAuth, fetchMyAlertsPush]);

  // Load alerts when auth or push changes
  useEffect(() => {
    fetchMyAlerts();
  }, [fetchMyAlerts]);

  // Push notification handlers
  const checkExistingSubscription = useCallback(async () => {
    try {
      const reg = await navigator.serviceWorker.ready;
      const sub = await reg.pushManager.getSubscription();
      if (sub) {
        setPushSubscribed(true);
        setPushEndpoint(sub.endpoint);
      }
    } catch {
      // ignore
    }
  }, []);

  useEffect(() => {
    if ("serviceWorker" in navigator && "PushManager" in window) {
      setPushSupported(true);
      checkExistingSubscription();
    }
  }, [checkExistingSubscription]);

  async function handleSubscribe() {
    setPushLoading(true);
    setPushError(null);
    try {
      const res = await fetch(`${API_BASE}/push/vapid-key`);
      if (!res.ok) throw new Error("Could not get VAPID key");
      const { public_key } = await res.json();

      const reg = await navigator.serviceWorker.ready;
      const sub = await reg.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(public_key),
      });

      const subJSON = sub.toJSON();
      const saveRes = await fetch(`${API_BASE}/push/subscribe`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          endpoint: subJSON.endpoint,
          keys: {
            p256dh: subJSON.keys?.p256dh,
            auth: subJSON.keys?.auth,
          },
        }),
      });
      if (!saveRes.ok) throw new Error("Failed to save subscription");

      setPushSubscribed(true);
      setPushEndpoint(subJSON.endpoint || null);
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Subscription failed";
      setPushError(message);
    } finally {
      setPushLoading(false);
    }
  }

  async function handleUnsubscribe() {
    setPushLoading(true);
    try {
      const reg = await navigator.serviceWorker.ready;
      const sub = await reg.pushManager.getSubscription();
      if (sub) {
        await fetch(`${API_BASE}/push/unsubscribe`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ endpoint: sub.endpoint }),
        });
        await sub.unsubscribe();
      }
      setPushSubscribed(false);
      setPushEndpoint(null);
    } catch {
      setPushError("Could not unsubscribe");
    } finally {
      setPushLoading(false);
    }
  }

  // Store selection
  function toggleStore(slug: string) {
    setSelectedStores((prev) =>
      prev.includes(slug) ? prev.filter((s) => s !== slug) : [...prev, slug]
    );
  }

  function toggleAllStores() {
    if (selectedStores.length === stores.length) {
      setSelectedStores([]);
    } else {
      setSelectedStores(stores.map((s) => s.slug));
    }
  }

  // Create alert
  async function handleCreateAlert(e: React.FormEvent) {
    e.preventDefault();
    if (!searchQuery.trim() || !targetPrice || selectedStores.length === 0) {
      setAlertStatus({
        type: "error",
        message: "Bütün sahələri doldurun və ən azı bir mağaza seçin. / Please fill all fields and select at least one store.",
      });
      return;
    }

    const isAuthenticated = !!authToken;
    const hasPush = pushSubscribed && pushEndpoint;

    if (!isAuthenticated && !hasPush) {
      setAlertStatus({
        type: "info",
        message: "Daxil olun və ya bildirişləri aktivləşdirin. / Please login or enable notifications first.",
      });
      return;
    }

    setAlertLoading(true);
    setAlertStatus(null);
    try {
      const body: Record<string, unknown> = {
        search_query: searchQuery.trim(),
        target_price: parseFloat(targetPrice),
        store_slugs: selectedStores,
      };
      if (!isAuthenticated && hasPush) {
        body.push_endpoint = pushEndpoint;
      }

      const res = await fetch(`${API_BASE}/alerts`, {
        method: "POST",
        headers: getAuthHeaders(),
        body: JSON.stringify(body),
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || "Failed to create alert");
      }
      setAlertStatus({
        type: "success",
        message: "Alert yaradıldı! Qiymətlər yoxlanılır... / Alert created! Checking prices now...",
      });
      setSearchQuery("");
      setTargetPrice("");
      // Refresh alerts immediately and again after price check completes
      fetchMyAlerts();
      setTimeout(fetchMyAlerts, 15000);
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Failed to create alert";
      setAlertStatus({ type: "error", message });
    } finally {
      setAlertLoading(false);
    }
  }

  // Delete alert
  async function handleDeleteAlert(alertId: number) {
    try {
      const res = await fetch(`${API_BASE}/alerts/${alertId}`, {
        method: "DELETE",
        headers: getAuthHeaders(),
      });
      if (res.ok) {
        setMyAlerts((prev) => prev.filter((a) => a.id !== alertId));
      }
    } catch {
      // ignore
    }
  }

  // Check now
  async function handleCheckNow(alertId: number) {
    setCheckingAlertId(alertId);
    try {
      await fetch(`${API_BASE}/alerts/${alertId}/check`, {
        method: "POST",
        headers: getAuthHeaders(),
      });
      setTimeout(fetchMyAlerts, 10000);
    } catch {
      // ignore
    } finally {
      setTimeout(() => setCheckingAlertId(null), 2000);
    }
  }

  // Product search
  async function handleProductSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!productSearch.trim()) return;
    setSearchLoading(true);
    setSearchError(null);
    setHasSearched(true);
    try {
      const res = await fetch(
        `${API_BASE}/search?q=${encodeURIComponent(productSearch.trim())}`
      );
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || "Search failed");
      }
      const data = await res.json();
      setSearchResults(data.results || []);
    } catch (err: unknown) {
      setSearchError(err instanceof Error ? err.message : "Search failed");
      setSearchResults([]);
    } finally {
      setSearchLoading(false);
    }
  }

  const canCreateAlert = !!authToken || (pushSubscribed && !!pushEndpoint);
  const showAlerts = myAlerts.length > 0 || (canCreateAlert && alertsLoading);

  return (
    <div>
      {/* Background Glows */}
      <div className="bg-glow bg-glow-1" />
      <div className="bg-glow bg-glow-2" />

      {/* Navbar */}
      <nav className="navbar">
        <div className="navbar-left">
          <span className="navbar-logo">UcuzBot</span>
          <span className="navbar-tag">Beta</span>
        </div>
        <div className="navbar-right">
          <a
            href="https://t.me/UcuzBot"
            target="_blank"
            rel="noopener noreferrer"
            className="navbar-telegram"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
              <path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.479.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z"/>
            </svg>
            Telegram Bot
          </a>
          {authUser ? (
            <div className="navbar-user">
              <span className="navbar-user-name">
                {authUser.first_name || authUser.email}
              </span>
              <button onClick={handleLogout} className="btn btn-ghost btn-sm">
                Çıxış / Logout
              </button>
            </div>
          ) : (
            <button
              onClick={() => { setShowAuthModal(true); setAuthError(null); }}
              className="btn btn-auth"
            >
              Daxil ol / Login
            </button>
          )}
        </div>
      </nav>

      {/* Auth Modal */}
      {showAuthModal && (
        <div className="auth-overlay" onClick={() => setShowAuthModal(false)}>
          <div className="auth-modal" onClick={(e) => e.stopPropagation()}>
            <button className="auth-close" onClick={() => setShowAuthModal(false)}>
              &#10005;
            </button>
            <h2 className="auth-title">
              {authMode === "login" ? "Daxil ol / Login" : "Qeydiyyat / Register"}
            </h2>
            <form onSubmit={handleAuth}>
              {authMode === "register" && (
                <div className="form-group">
                  <label className="form-label" htmlFor="auth-name">Ad / Name</label>
                  <input
                    id="auth-name"
                    type="text"
                    className="form-input"
                    placeholder="Adınız"
                    value={authFirstName}
                    onChange={(e) => setAuthFirstName(e.target.value)}
                  />
                </div>
              )}
              <div className="form-group">
                <label className="form-label" htmlFor="auth-email">Email</label>
                <input
                  id="auth-email"
                  type="email"
                  className="form-input"
                  placeholder="email@example.com"
                  value={authEmail}
                  onChange={(e) => setAuthEmail(e.target.value)}
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label" htmlFor="auth-password">Şifrə / Password</label>
                <input
                  id="auth-password"
                  type="password"
                  className="form-input"
                  placeholder="Minimum 6 simvol"
                  value={authPassword}
                  onChange={(e) => setAuthPassword(e.target.value)}
                  required
                  minLength={6}
                />
              </div>
              <button type="submit" disabled={authLoading} className="btn btn-primary">
                {authLoading
                  ? "Gözləyin..."
                  : authMode === "login"
                    ? "Daxil ol / Login"
                    : "Qeydiyyat / Register"}
              </button>
            </form>
            {authError && <div className="alert-msg alert-msg-error">{authError}</div>}
            <div className="auth-switch">
              {authMode === "login" ? (
                <>
                  Hesabınız yoxdur?{" "}
                  <button
                    type="button"
                    className="auth-switch-btn"
                    onClick={() => { setAuthMode("register"); setAuthError(null); }}
                  >
                    Qeydiyyatdan keçin / Register
                  </button>
                </>
              ) : (
                <>
                  Artıq hesabınız var?{" "}
                  <button
                    type="button"
                    className="auth-switch-btn"
                    onClick={() => { setAuthMode("login"); setAuthError(null); }}
                  >
                    Daxil olun / Login
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Hero */}
      <section className="hero">
        <div className="animate-fade-in-up delay-1">
          <span className="hero-badge">
            <span>&#9889;</span>
            Azərbaycanın qiymət izləyicisi
          </span>
        </div>

        <h1 className="hero-title animate-fade-in-up delay-2">
          <span className="hero-title-gradient">
            Ən ucuz qiyməti tapın,
          </span>
          <br />
          pul qənaət edin
        </h1>

        <p className="hero-description animate-fade-in-up delay-3">
          UcuzBot Azərbaycanın 6 böyük mağazasında qiymətləri avtomatik izləyir.
          İstədiyiniz məhsulun qiymətini təyin edin — qiymət düşən kimi sizə bildiriş göndərək.
        </p>
        <p className="hero-description-en animate-fade-in-up delay-3">
          UcuzBot automatically tracks prices across 6 major Azerbaijan stores.
          Set your target price for any product — we&apos;ll notify you the moment it drops.
        </p>

        <div className="hero-stats animate-fade-in-up delay-4">
          <div className="hero-stat">
            <div className="hero-stat-number">6</div>
            <div className="hero-stat-label">Mağaza / Stores</div>
          </div>
          <div className="hero-stat">
            <div className="hero-stat-number">24/7</div>
            <div className="hero-stat-label">Monitorinq / Monitoring</div>
          </div>
          <div className="hero-stat">
            <div className="hero-stat-number">&#8380;</div>
            <div className="hero-stat-label">AZN ilə / Prices in AZN</div>
          </div>
        </div>
      </section>

      <div className="section-divider" />

      {/* How It Works */}
      <section className="section">
        <div className="section-header animate-fade-in-up delay-1">
          <div className="section-label">Necə işləyir / How it works</div>
          <h2 className="section-title">3 sadə addım ilə başlayın</h2>
          <p className="section-subtitle">Get started in 3 simple steps</p>
        </div>

        <div className="steps-grid">
          <div className="step-card animate-fade-in-up delay-2">
            <span className="step-number">1</span>
            <span className="step-icon">&#128270;</span>
            <div className="step-title">Bildirişləri aktivləşdirin</div>
            <div className="step-desc">
              Brauzerdə bildirişlərə icazə verin ki, qiymət düşəndə anında xəbər alasınız.
            </div>
            <div className="step-desc-en">Enable browser notifications to get instant price drop alerts.</div>
          </div>
          <div className="step-card animate-fade-in-up delay-3">
            <span className="step-number">2</span>
            <span className="step-icon">&#127919;</span>
            <div className="step-title">Hədəf qiymət təyin edin</div>
            <div className="step-desc">
              Axtardığınız məhsulu yazın, hədəf qiyməti daxil edin və mağazaları seçin.
            </div>
            <div className="step-desc-en">Enter the product, set your target price, and pick stores.</div>
          </div>
          <div className="step-card animate-fade-in-up delay-4">
            <span className="step-number">3</span>
            <span className="step-icon">&#128276;</span>
            <div className="step-title">Bildiriş alın</div>
            <div className="step-desc">
              Qiymət hədəfinizə çatanda və ya aşağı düşəndə dərhal bildiriş alacaqsınız.
            </div>
            <div className="step-desc-en">Get notified instantly when the price hits your target.</div>
          </div>
        </div>
      </section>

      <div className="section-divider" />

      {/* Instructions */}
      <section className="section">
        <div className="section-header animate-fade-in-up delay-1">
          <div className="section-label">Təlimatlar / Instructions</div>
          <h2 className="section-title">İstifadə qaydası</h2>
          <p className="section-subtitle">How to use UcuzBot</p>
        </div>

        <div className="instructions-grid">
          <div className="instruction-card animate-fade-in-up delay-2">
            <div className="instruction-icon">&#128270;</div>
            <div className="instruction-title">Məhsul Axtarışı / Product Search</div>
            <div className="instruction-text">
              Aşağıdakı axtarış bölməsində məhsul adınızı yazın. Bütün mağazalarda canlı qiymətləri görəcəksiniz.
            </div>
            <div className="instruction-text-en">
              Type your product name in the search section below. You will see live prices from all stores.
            </div>
          </div>
          <div className="instruction-card animate-fade-in-up delay-3">
            <div className="instruction-icon">&#128276;</div>
            <div className="instruction-title">Qiymət Alertləri / Price Alerts</div>
            <div className="instruction-text">
              Hədəf qiymət təyin edin. Sistem hər 4 saatdan bir qiymətləri yoxlayır və qiymət düşəndə sizə xəbər verir.
            </div>
            <div className="instruction-text-en">
              Set a target price. The system checks prices every 4 hours and notifies you when the price drops.
            </div>
          </div>
          <div className="instruction-card animate-fade-in-up delay-4">
            <div className="instruction-icon">&#128100;</div>
            <div className="instruction-title">Hesab / Account</div>
            <div className="instruction-text">
              Qeydiyyatdan keçin ki, alertləriniz bütün cihazlarda sinxron olsun. Qeydiyyatsız da bildiriş ilə işləyə bilərsiniz.
            </div>
            <div className="instruction-text-en">
              Register to sync alerts across devices. You can also use push notifications without an account.
            </div>
          </div>
          <div className="instruction-card animate-fade-in-up delay-5">
            <div className="instruction-icon">&#128640;</div>
            <div className="instruction-title">Telegram Bot</div>
            <div className="instruction-text">
              <a href="https://t.me/UcuzBot" target="_blank" rel="noopener noreferrer" className="instruction-link">
                @UcuzBot
              </a>
              {" "}ilə Telegram-dan da istifadə edə bilərsiniz. Mesaj yazın — avtomatik axtarış edəcək.
            </div>
            <div className="instruction-text-en">
              You can also use{" "}
              <a href="https://t.me/UcuzBot" target="_blank" rel="noopener noreferrer" className="instruction-link">
                @UcuzBot
              </a>
              {" "}on Telegram. Just type a product name — it searches automatically.
            </div>
          </div>
        </div>
      </section>

      <div className="section-divider" />

      {/* Stores */}
      <section className="section">
        <div className="section-header animate-fade-in-up delay-1">
          <div className="section-label">Mağazalar / Stores</div>
          <h2 className="section-title">Dəstəklənən mağazalar</h2>
          <p className="section-subtitle">We track prices from these stores</p>
        </div>

        <div className="stores-grid">
          {stores.map((store, i) => (
            <div
              key={store.slug}
              className={`store-card animate-fade-in-up delay-${Math.min(i + 2, 5)}`}
            >
              <div className="store-icon">{store.icon}</div>
              <div>
                <div className="store-name">{store.name}</div>
                <div className="store-type">{store.type}</div>
              </div>
            </div>
          ))}
        </div>
      </section>

      <div className="section-divider" />

      {/* Product Search */}
      <section className="section" id="search">
        <div className="section-header animate-fade-in-up delay-1">
          <div className="section-label">Məhsul Axtarışı / Product Search</div>
          <h2 className="section-title">Qiymətləri müqayisə edin</h2>
          <p className="section-subtitle">Compare prices across all stores</p>
        </div>

        <div className="search-wrapper animate-fade-in-up delay-2">
          <form onSubmit={handleProductSearch} className="search-form">
            <input
              type="text"
              className="form-input search-input"
              placeholder="məs. iPhone 15, Samsung Galaxy, AirPods..."
              value={productSearch}
              onChange={(e) => setProductSearch(e.target.value)}
              maxLength={500}
            />
            <button type="submit" disabled={searchLoading} className="btn btn-primary btn-search">
              {searchLoading ? "Axtarılır..." : "Axtar / Search"}
            </button>
          </form>

          {searchError && (
            <div className="alert-msg alert-msg-error">{searchError}</div>
          )}

          {searchResults.length > 0 && (
            <div className="search-results">
              {searchResults.map((r, i) => (
                <a
                  key={`${r.store_slug}-${r.product_url}-${i}`}
                  href={r.product_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="search-result-card"
                >
                  {r.image_url && (
                    <div className="search-result-img">
                      <img src={r.image_url} alt={r.product_name} loading="lazy" />
                    </div>
                  )}
                  <div className="search-result-info">
                    <div className="search-result-name">{r.product_name}</div>
                    <div className="search-result-store">{r.store_name}</div>
                  </div>
                  <div className="search-result-price">{r.price} AZN</div>
                </a>
              ))}
            </div>
          )}

          {hasSearched && !searchLoading && searchResults.length === 0 && !searchError && (
            <div className="search-no-results">
              Nəticə tapılmadı / No results found
            </div>
          )}
        </div>
      </section>

      <div className="section-divider" />

      {/* Alert Form */}
      <section className="form-section" id="create-alert">
        <div className="section-header animate-fade-in-up delay-1">
          <div className="section-label">Qiymət Alerti / Price Alert</div>
          <h2 className="section-title">Alert yaradın</h2>
          <p className="section-subtitle">Create a price alert and save money</p>
        </div>

        <div className="form-wrapper animate-fade-in-up delay-2">
          {/* Push Notification Banner — only show if not authenticated */}
          {!authToken && pushSupported && (
            <div className={`push-banner ${pushSubscribed ? "push-banner-active" : ""}`}>
              <div className="push-banner-icon">{pushSubscribed ? "\u2705" : "\u{1F514}"}</div>
              {!pushSubscribed ? (
                <>
                  <div className="push-banner-text">
                    <strong>Bildirişləri aktivləşdirin</strong>
                    <br />
                    Alert yaratmaq üçün bildirişlərə icazə lazımdır və ya daxil olun.
                    <br />
                    <span style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
                      Enable notifications or login to create price alerts.
                    </span>
                  </div>
                  <button
                    onClick={handleSubscribe}
                    disabled={pushLoading}
                    className="btn btn-notify"
                  >
                    {pushLoading
                      ? "Gözləyin..."
                      : "Bildirişləri aktivləşdir"}
                  </button>
                </>
              ) : (
                <>
                  <div className="push-active-text">
                    Bildirişlər aktivdir / Notifications enabled
                  </div>
                  <button
                    onClick={handleUnsubscribe}
                    disabled={pushLoading}
                    className="btn btn-ghost"
                  >
                    Söndür / Disable
                  </button>
                </>
              )}
              {pushError && <div className="push-error">{pushError}</div>}
            </div>
          )}

          {authToken && (
            <div className="push-banner push-banner-active">
              <div className="push-banner-icon">{"\u2705"}</div>
              <div className="push-active-text">
                Daxil olmusunuz — alert yarada bilərsiniz / Logged in — you can create alerts
              </div>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleCreateAlert}>
            <div className="form-group">
              <label className="form-label" htmlFor="product-name">
                Məhsul adı / Product name
              </label>
              <input
                id="product-name"
                type="text"
                className="form-input"
                placeholder="məs. iPhone 15 Pro Max"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                maxLength={500}
              />
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="target-price">
                Hədəf qiymət / Target price
              </label>
              <div className="form-input-suffix">
                <input
                  id="target-price"
                  type="number"
                  className="form-input"
                  placeholder="məs. 1500"
                  value={targetPrice}
                  onChange={(e) => setTargetPrice(e.target.value)}
                  min="0.01"
                  step="0.01"
                />
                <span className="suffix">AZN</span>
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">
                Mağazalar / Stores
              </label>
              <div className="store-chips">
                {stores.map((store) => (
                  <div
                    key={store.slug}
                    className={`store-chip ${selectedStores.includes(store.slug) ? "active" : ""}`}
                    onClick={() => toggleStore(store.slug)}
                  >
                    <span className="store-chip-check">
                      {selectedStores.includes(store.slug) ? "\u2713" : ""}
                    </span>
                    {store.name}
                  </div>
                ))}
              </div>
              <button type="button" className="store-select-all" onClick={toggleAllStores}>
                {selectedStores.length === stores.length ? "Hamısını silin / Deselect all" : "Hamısını seçin / Select all"}
              </button>
            </div>

            <button
              type="submit"
              disabled={alertLoading || !canCreateAlert}
              className="btn btn-primary"
            >
              {alertLoading ? "Yaradılır..." : "Alert Yarat / Create Alert"}
            </button>
          </form>

          {alertStatus && (
            <div className={`alert-msg alert-msg-${alertStatus.type}`}>
              {alertStatus.message}
            </div>
          )}
        </div>
      </section>

      {/* My Alerts */}
      {showAlerts && (
        <>
          <div className="section-divider" />
          <section className="section">
            <div className="section-header">
              <div className="section-label">Alertlərim / My Alerts</div>
              <h2 className="section-title">Aktiv alertlər</h2>
              <p className="section-subtitle">Your price alerts and their current status</p>
            </div>

            <div className="my-alerts-list">
              {myAlerts.map((alert) => {
                const storeName = stores.find(
                  (s) => s.slug === alert.lowest_price_store
                )?.name || alert.lowest_price_store;
                return (
                  <div key={alert.id} className={`my-alert-card ${alert.is_triggered ? "my-alert-triggered" : ""}`}>
                    <div className="my-alert-header">
                      <div className="my-alert-query">{alert.search_query}</div>
                      <div className="my-alert-actions">
                        <button
                          className="my-alert-check"
                          onClick={() => handleCheckNow(alert.id)}
                          disabled={checkingAlertId === alert.id}
                          title="İndi yoxla / Check now"
                        >
                          {checkingAlertId === alert.id ? "\u23F3" : "\u{1F504}"}
                        </button>
                        <button
                          className="my-alert-delete"
                          onClick={() => handleDeleteAlert(alert.id)}
                          title="Sil / Delete"
                        >
                          &#10005;
                        </button>
                      </div>
                    </div>

                    {/* Store tags */}
                    <div className="my-alert-stores">
                      {alert.store_slugs.map((slug) => {
                        const s = stores.find((st) => st.slug === slug);
                        return (
                          <span key={slug} className="my-alert-store-tag">
                            {s?.name || slug}
                          </span>
                        );
                      })}
                    </div>

                    <div className="my-alert-details">
                      <div className="my-alert-row">
                        <span className="my-alert-label">Hədəf / Target:</span>
                        <span className="my-alert-value">{alert.target_price} AZN</span>
                      </div>
                      {alert.lowest_price_found !== null && (
                        <div className="my-alert-row">
                          <span className="my-alert-label">Ən aşağı / Lowest:</span>
                          <span className={`my-alert-value ${
                            alert.lowest_price_found <= alert.target_price
                              ? "my-alert-price-hit"
                              : "my-alert-price-above"
                          }`}>
                            {alert.lowest_price_found} AZN
                          </span>
                        </div>
                      )}
                      {storeName && alert.lowest_price_found !== null && (
                        <div className="my-alert-row">
                          <span className="my-alert-label">Mağaza / Store:</span>
                          <span className="my-alert-value">
                            {alert.lowest_price_url ? (
                              <a href={alert.lowest_price_url} target="_blank" rel="noopener noreferrer" className="my-alert-link">
                                {storeName}
                              </a>
                            ) : storeName}
                          </span>
                        </div>
                      )}
                      {alert.last_checked_at && (
                        <div className="my-alert-row">
                          <span className="my-alert-label">Yoxlanılıb / Checked:</span>
                          <span className="my-alert-value my-alert-time">
                            {new Date(alert.last_checked_at).toLocaleString("az-AZ")}
                          </span>
                        </div>
                      )}
                      {!alert.last_checked_at && (
                        <div className="my-alert-checking">Qiymətlər yoxlanılır... / Checking prices...</div>
                      )}
                    </div>
                    {alert.is_triggered && (
                      <div className="my-alert-triggered-badge">Tapıldı! / Price hit!</div>
                    )}
                  </div>
                );
              })}
            </div>

            {alertsLoading && <div className="my-alerts-loading">Yüklənir... / Loading...</div>}
          </section>
        </>
      )}

      {/* Footer */}
      <footer className="footer">
        <div className="footer-logo">UcuzBot</div>
        <div className="footer-text">
          Azərbaycanda ən yaxşı qiymətləri izləyin
          &bull; Track the best prices in Azerbaijan
        </div>
        <div className="footer-links">
          <a href="#search" className="footer-link">Axtarış / Search</a>
          <a href="#create-alert" className="footer-link">Alert Yarat / Create Alert</a>
          <a
            href="https://t.me/UcuzBot"
            target="_blank"
            rel="noopener noreferrer"
            className="footer-link"
          >
            Telegram Bot
          </a>
        </div>
        <div className="footer-text" style={{ marginTop: "0.5rem" }}>
          &copy; {new Date().getFullYear()} ucuzbot.az
        </div>
      </footer>
    </div>
  );
}
