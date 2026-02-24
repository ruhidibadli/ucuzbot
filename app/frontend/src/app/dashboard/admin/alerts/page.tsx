"use client";

import { useEffect, useState, useCallback } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { fetchAdminAlerts } from "@/lib/api";
import { stores } from "@/lib/constants";
import type { AdminAlertListItem } from "@/lib/types";

const STATUS_OPTIONS = [
  { value: "all", label: "All" },
  { value: "active", label: "Active" },
  { value: "triggered", label: "Triggered" },
  { value: "inactive", label: "Inactive" },
];

export default function AdminAlertsPage() {
  const { token } = useAuth();
  const [alerts, setAlerts] = useState<AdminAlertListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState("all");
  const [storeSlug, setStoreSlug] = useState("");
  const [loading, setLoading] = useState(true);
  const pageSize = 20;

  const load = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    try {
      const data = await fetchAdminAlerts(token, page, pageSize, statusFilter, storeSlug);
      setAlerts(data.alerts);
      setTotal(data.total);
    } catch {
      /* ignore */
    } finally {
      setLoading(false);
    }
  }, [token, page, statusFilter, storeSlug]);

  useEffect(() => {
    load();
  }, [load]);

  const totalPages = Math.ceil(total / pageSize);

  const getStatusBadge = (alert: AdminAlertListItem) => {
    if (alert.is_triggered) return <span className="admin-badge admin-badge--warning">Triggered</span>;
    if (alert.is_active) return <span className="admin-badge admin-badge--success">Active</span>;
    return <span className="admin-badge admin-badge--inactive">Inactive</span>;
  };

  return (
    <div className="dashboard-page">
      <h1 className="section-title" style={{ marginBottom: "1.5rem" }}>
        Alerts ({total})
      </h1>

      <div className="admin-filters">
        <div className="admin-filters__group">
          <label className="admin-filters__label">Status</label>
          <select
            className="form-input"
            value={statusFilter}
            onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
          >
            {STATUS_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        </div>
        <div className="admin-filters__group">
          <label className="admin-filters__label">Store</label>
          <select
            className="form-input"
            value={storeSlug}
            onChange={(e) => { setStoreSlug(e.target.value); setPage(1); }}
          >
            <option value="">All Stores</option>
            {stores.map((s) => (
              <option key={s.slug} value={s.slug}>{s.name}</option>
            ))}
          </select>
        </div>
      </div>

      {loading ? (
        <div className="dashboard-loading" style={{ minHeight: "200px" }}>
          <div className="dashboard-spinner" />
        </div>
      ) : alerts.length === 0 ? (
        <div className="dashboard-empty">No alerts found.</div>
      ) : (
        <>
          <div className="admin-table-container">
            <table className="admin-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>User</th>
                  <th>Query</th>
                  <th>Target</th>
                  <th>Stores</th>
                  <th>Status</th>
                  <th>Lowest</th>
                  <th>Last Checked</th>
                  <th>Created</th>
                </tr>
              </thead>
              <tbody>
                {alerts.map((a) => (
                  <tr key={a.id}>
                    <td>{a.id}</td>
                    <td>{a.user_email || a.user_first_name || `#${a.user_id ?? "—"}`}</td>
                    <td className="admin-table__query">{a.search_query}</td>
                    <td>{Number(a.target_price).toFixed(2)} AZN</td>
                    <td>
                      <div className="admin-store-tags admin-store-tags--compact">
                        {a.store_slugs.map((s) => (
                          <span key={s} className="admin-store-tag admin-store-tag--sm">{s}</span>
                        ))}
                      </div>
                    </td>
                    <td>{getStatusBadge(a)}</td>
                    <td>
                      {a.lowest_price_found != null ? (
                        a.lowest_price_url ? (
                          <a
                            href={a.lowest_price_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="my-alert-link"
                          >
                            {Number(a.lowest_price_found).toFixed(2)} AZN
                          </a>
                        ) : (
                          `${Number(a.lowest_price_found).toFixed(2)} AZN`
                        )
                      ) : (
                        "—"
                      )}
                    </td>
                    <td>
                      {a.last_checked_at
                        ? new Date(a.last_checked_at).toLocaleString()
                        : "—"}
                    </td>
                    <td>{new Date(a.created_at).toLocaleDateString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {totalPages > 1 && (
            <div className="admin-pagination">
              <button
                className="btn btn-ghost btn-sm"
                disabled={page <= 1}
                onClick={() => setPage((p) => p - 1)}
              >
                Prev
              </button>
              <span className="admin-pagination__info">
                Page {page} of {totalPages}
              </span>
              <button
                className="btn btn-ghost btn-sm"
                disabled={page >= totalPages}
                onClick={() => setPage((p) => p + 1)}
              >
                Next
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
