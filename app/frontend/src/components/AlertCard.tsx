"use client";

import type { AlertData } from "@/lib/types";
import { stores } from "@/lib/constants";

interface AlertCardProps {
  alert: AlertData;
  onDelete: (id: number) => void;
  onCheckNow: (id: number) => void;
  checkingAlertId: number | null;
}

export default function AlertCard({ alert, onDelete, onCheckNow, checkingAlertId }: AlertCardProps) {
  const storeName =
    stores.find((s) => s.slug === alert.lowest_price_store)?.name ||
    alert.lowest_price_store;

  return (
    <div className={`my-alert-card ${alert.is_triggered ? "my-alert-triggered" : ""}`}>
      <div className="my-alert-header">
        <div className="my-alert-query">{alert.search_query}</div>
        <div className="my-alert-actions">
          <button
            className="my-alert-check"
            onClick={() => onCheckNow(alert.id)}
            disabled={checkingAlertId === alert.id}
            title="Indi yoxla / Check now"
          >
            {checkingAlertId === alert.id ? "\u23F3" : "\u{1F504}"}
          </button>
          <button
            className="my-alert-delete"
            onClick={() => onDelete(alert.id)}
            title="Sil / Delete"
          >
            &#10005;
          </button>
        </div>
      </div>

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
          <span className="my-alert-label">Hedef / Target:</span>
          <span className="my-alert-value">{alert.target_price} AZN</span>
        </div>
        {alert.lowest_price_found !== null && (
          <div className="my-alert-row">
            <span className="my-alert-label">En asagi / Lowest:</span>
            <span
              className={`my-alert-value ${
                alert.lowest_price_found <= alert.target_price
                  ? "my-alert-price-hit"
                  : "my-alert-price-above"
              }`}
            >
              {alert.lowest_price_found} AZN
            </span>
          </div>
        )}
        {storeName && alert.lowest_price_found !== null && (
          <div className="my-alert-row">
            <span className="my-alert-label">Magaza / Store:</span>
            <span className="my-alert-value">
              {alert.lowest_price_url ? (
                <a
                  href={alert.lowest_price_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="my-alert-link"
                >
                  {storeName}
                </a>
              ) : (
                storeName
              )}
            </span>
          </div>
        )}
        {alert.last_checked_at && (
          <div className="my-alert-row">
            <span className="my-alert-label">Yoxlanilir / Checked:</span>
            <span className="my-alert-value my-alert-time">
              {new Date(alert.last_checked_at).toLocaleString("az-AZ")}
            </span>
          </div>
        )}
        {!alert.last_checked_at && (
          <div className="my-alert-checking">
            Qiymetler yoxlanilir... / Checking prices...
          </div>
        )}
      </div>
      {alert.is_triggered && (
        <div className="my-alert-triggered-badge">Tapildi! / Price hit!</div>
      )}
    </div>
  );
}
