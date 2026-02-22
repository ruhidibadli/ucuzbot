"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
import { createAlert } from "@/lib/api";
import { stores, API_BASE, urlBase64ToUint8Array } from "@/lib/constants";
import StoreChips from "@/components/StoreChips";

export default function CreateAlertPage() {
  const { token } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();

  const [searchQuery, setSearchQuery] = useState("");
  const [targetPrice, setTargetPrice] = useState("");
  const [selectedStores, setSelectedStores] = useState<string[]>(
    stores.map((s) => s.slug)
  );
  const [status, setStatus] = useState<{
    type: "success" | "error" | "info";
    message: string;
  } | null>(null);
  const [loading, setLoading] = useState(false);

  // Push state
  const [pushSupported, setPushSupported] = useState(false);
  const [pushSubscribed, setPushSubscribed] = useState(false);
  const [pushEndpoint, setPushEndpoint] = useState<string | null>(null);
  const [pushLoading, setPushLoading] = useState(false);
  const [pushError, setPushError] = useState<string | null>(null);

  // Pre-fill from query param
  useEffect(() => {
    const q = searchParams.get("q");
    if (q) setSearchQuery(q);
  }, [searchParams]);

  // Check existing push subscription
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
      setPushError(err instanceof Error ? err.message : "Subscription failed");
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

  const canCreate = !!token || (pushSubscribed && !!pushEndpoint);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!searchQuery.trim() || !targetPrice || selectedStores.length === 0) {
      setStatus({
        type: "error",
        message:
          "Butun sah&#601;l&#601;ri doldurun v&#601; &#601;n azi bir magaza secin. / Please fill all fields and select at least one store.",
      });
      return;
    }

    if (!canCreate) {
      setStatus({
        type: "info",
        message:
          "Daxil olun v&#601; ya bildirisl&#601;ri aktivl&#601;sdirin. / Please login or enable notifications first.",
      });
      return;
    }

    setLoading(true);
    setStatus(null);
    try {
      await createAlert(
        token,
        searchQuery.trim(),
        parseFloat(targetPrice),
        selectedStores,
        !token ? pushEndpoint : null
      );
      setStatus({
        type: "success",
        message:
          "Alert yaradildi! Yonl&#601;ndirilirsiniz... / Alert created! Redirecting...",
      });
      setTimeout(() => router.push("/dashboard/alerts"), 1500);
    } catch (err: unknown) {
      setStatus({
        type: "error",
        message: err instanceof Error ? err.message : "Failed to create alert",
      });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="dashboard-page">
      <div className="section-header">
        <h2 className="section-title">Alert Yarat / Create Alert</h2>
        <p className="section-subtitle">Qiym&#601;t dusdukd&#601; bildirs al / Get notified when prices drop</p>
      </div>

      <div className="form-wrapper">
        {/* Push Notification Banner -- only show if not authenticated */}
        {!token && pushSupported && (
          <div className={`push-banner ${pushSubscribed ? "push-banner-active" : ""}`}>
            <div className="push-banner-icon">{pushSubscribed ? "\u2705" : "\u{1F514}"}</div>
            {!pushSubscribed ? (
              <>
                <div className="push-banner-text">
                  <strong>Bildirislerri aktivlesdirin</strong>
                  <br />
                  Alert yaratmaq ucun bildirislere icaze lazimdir ve ya daxil olun.
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
                  {pushLoading ? "Gozleyin..." : "Bildirisleri aktivlesdir"}
                </button>
              </>
            ) : (
              <>
                <div className="push-active-text">
                  Bildirislr aktivdir / Notifications enabled
                </div>
                <button
                  onClick={handleUnsubscribe}
                  disabled={pushLoading}
                  className="btn btn-ghost"
                >
                  Sondur / Disable
                </button>
              </>
            )}
            {pushError && <div className="push-error">{pushError}</div>}
          </div>
        )}

        {token && (
          <div className="push-banner push-banner-active">
            <div className="push-banner-icon">{"\u2705"}</div>
            <div className="push-active-text">
              Daxil olmusunuz — alert yarada bilersiniz / Logged in — you can create alerts
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label" htmlFor="product-name">
              M&#601;hsul adi / Product name
            </label>
            <input
              id="product-name"
              type="text"
              className="form-input"
              placeholder="m&#601;s. iPhone 15 Pro Max"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              maxLength={500}
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="target-price">
              H&#601;d&#601;f qiym&#601;t / Target price
            </label>
            <div className="form-input-suffix">
              <input
                id="target-price"
                type="number"
                className="form-input"
                placeholder="m&#601;s. 1500"
                value={targetPrice}
                onChange={(e) => setTargetPrice(e.target.value)}
                min="0.01"
                step="0.01"
              />
              <span className="suffix">AZN</span>
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Magazalar / Stores</label>
            <StoreChips
              selectedStores={selectedStores}
              onToggle={toggleStore}
              onToggleAll={toggleAllStores}
            />
          </div>

          <button
            type="submit"
            disabled={loading || !canCreate}
            className="btn btn-primary"
          >
            {loading ? "Yaradilir..." : "Alert Yarat / Create Alert"}
          </button>
        </form>

        {status && (
          <div className={`alert-msg alert-msg-${status.type}`}>
            {status.message}
          </div>
        )}
      </div>
    </div>
  );
}
