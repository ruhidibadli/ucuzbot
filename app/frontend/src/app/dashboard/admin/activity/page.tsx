"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { useAuth } from "@/contexts/AuthContext";
import { fetchAdminBotActivity } from "@/lib/api";
import type { AdminBotActivityItem } from "@/lib/types";

const ACTION_LABELS: Record<string, string> = {
  search: "Search",
  alert_create: "Alert Created",
  alert_delete: "Alert Deleted",
  alert_triggered: "Alert Triggered",
};

const ACTION_FILTERS = [
  { value: "all", label: "All Actions" },
  { value: "search", label: "Search" },
  { value: "alert_create", label: "Alert Created" },
  { value: "alert_delete", label: "Alert Deleted" },
  { value: "alert_triggered", label: "Alert Triggered" },
];

function formatDate(dateStr: string): string {
  const d = new Date(dateStr);
  return d.toLocaleDateString("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function AdminActivityPage() {
  const { token } = useAuth();
  const [activities, setActivities] = useState<AdminBotActivityItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [actionFilter, setActionFilter] = useState("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const pageSize = 20;

  const loadData = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    setError("");
    try {
      const res = await fetchAdminBotActivity(token, page, pageSize, actionFilter);
      setActivities(res.activities);
      setTotal(res.total);
    } catch {
      setError("Failed to load activity log");
    } finally {
      setLoading(false);
    }
  }, [token, page, pageSize, actionFilter]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const totalPages = Math.ceil(total / pageSize);

  return (
    <div className="dashboard-page">
      <div style={{ marginBottom: "1.5rem" }}>
        <Link href="/dashboard/admin" style={{ color: "var(--text-muted)", fontSize: "0.85rem", textDecoration: "none" }}>
          &larr; Back to Admin
        </Link>
      </div>

      <h1 className="section-title" style={{ marginBottom: "0.5rem" }}>
        Bot Activity Log
      </h1>
      <p className="section-subtitle" style={{ marginBottom: "1.5rem" }}>
        User actions in the Telegram bot
      </p>

      <div className="admin-filters">
        <div className="admin-filters__group">
          <label className="admin-filters__label">Action</label>
          <select
            className="form-input"
            value={actionFilter}
            onChange={(e) => { setActionFilter(e.target.value); setPage(1); }}
          >
            {ACTION_FILTERS.map((f) => (
              <option key={f.value} value={f.value}>{f.label}</option>
            ))}
          </select>
        </div>
      </div>

      {error && <p className="alert-msg alert-msg-error">{error}</p>}

      {loading ? (
        <div className="dashboard-loading" style={{ minHeight: "200px" }}>
          <div className="dashboard-spinner" />
        </div>
      ) : activities.length === 0 ? (
        <div className="dashboard-empty">No activity found</div>
      ) : (
        <>
          <div className="admin-table-container">
            <table className="admin-table">
              <thead>
                <tr>
                  <th>Time</th>
                  <th>User</th>
                  <th>Action</th>
                  <th>Detail</th>
                </tr>
              </thead>
              <tbody>
                {activities.map((item) => (
                  <tr key={item.id}>
                    <td>{formatDate(item.created_at)}</td>
                    <td>
                      {item.user_first_name || item.user_email || (item.telegram_id ? `TG:${item.telegram_id}` : "—")}
                    </td>
                    <td>
                      <span className={`admin-activity-badge admin-activity-badge--${item.action}`}>
                        {ACTION_LABELS[item.action] || item.action}
                      </span>
                    </td>
                    <td className="admin-table__query">{item.detail || "—"}</td>
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
                Previous
              </button>
              <span className="admin-pagination__info">
                Page {page} of {totalPages} ({total} total)
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
