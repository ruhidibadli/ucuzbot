"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/contexts/AuthContext";
import { fetchAdminStats, fetchAdminBotActivity } from "@/lib/api";
import type { AdminStats, AdminBotActivityItem } from "@/lib/types";

const ACTION_LABELS: Record<string, string> = {
  search: "Search",
  alert_create: "Alert Created",
  alert_delete: "Alert Deleted",
  alert_triggered: "Alert Triggered",
};

function formatTimeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

export default function AdminOverviewPage() {
  const { token } = useAuth();
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [recentActivity, setRecentActivity] = useState<AdminBotActivityItem[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!token) return;
    fetchAdminStats(token)
      .then(setStats)
      .catch(() => setError("Failed to load stats"));
    fetchAdminBotActivity(token, 1, 20)
      .then((res) => setRecentActivity(res.activities))
      .catch(() => {});
  }, [token]);

  if (error) {
    return (
      <div className="dashboard-page">
        <p className="alert-msg alert-msg-error">{error}</p>
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="dashboard-page">
        <div className="dashboard-loading">
          <div className="dashboard-spinner" />
          <p>Loading admin stats...</p>
        </div>
      </div>
    );
  }

  const statCards = [
    { label: "Total Users", value: stats.total_users, variant: "info" },
    { label: "Total Alerts", value: stats.total_alerts, variant: "info" },
    { label: "Active Alerts", value: stats.active_alerts, variant: "success" },
    { label: "Triggered Alerts", value: stats.triggered_alerts, variant: "warning" },
    { label: "Inactive Alerts", value: stats.inactive_alerts, variant: "" },
    { label: "Triggered (24h)", value: stats.recent_triggered_count_24h, variant: "warning" },
    { label: "Triggered (7d)", value: stats.recent_triggered_count_7d, variant: "warning" },
  ];

  return (
    <div className="dashboard-page">
      <h1 className="section-title" style={{ marginBottom: "0.5rem" }}>
        Admin Panel
      </h1>
      <p className="section-subtitle" style={{ marginBottom: "2rem" }}>
        System overview and management
      </p>

      <div className="admin-stats-grid">
        {statCards.map((card) => (
          <div key={card.label} className={`admin-stat-card ${card.variant ? `admin-stat-card--${card.variant}` : ""}`}>
            <div className="admin-stat-card__number">{card.value}</div>
            <div className="admin-stat-card__label">{card.label}</div>
          </div>
        ))}
      </div>

      {Object.keys(stats.alerts_by_store).length > 0 && (
        <div style={{ marginTop: "2rem" }}>
          <h2 className="dashboard-recent-title">Alerts by Store</h2>
          <div className="admin-store-tags">
            {Object.entries(stats.alerts_by_store)
              .sort(([, a], [, b]) => b - a)
              .map(([store, count]) => (
                <span key={store} className="admin-store-tag">
                  {store}: {count}
                </span>
              ))}
          </div>
        </div>
      )}

      {recentActivity.length > 0 && (
        <div style={{ marginTop: "2rem" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
            <h2 className="dashboard-recent-title" style={{ marginBottom: 0 }}>Recent Bot Activity</h2>
            <Link href="/dashboard/admin/activity" className="btn btn-ghost btn-sm">
              View All
            </Link>
          </div>
          <div className="admin-activity-feed">
            {recentActivity.map((item) => (
              <div key={item.id} className="admin-activity-item">
                <span className="admin-activity-time">{formatTimeAgo(item.created_at)}</span>
                <span className="admin-activity-user">
                  {item.user_first_name || item.user_email || (item.telegram_id ? `TG:${item.telegram_id}` : "Unknown")}
                </span>
                <span className={`admin-activity-badge admin-activity-badge--${item.action}`}>
                  {ACTION_LABELS[item.action] || item.action}
                </span>
                {item.detail && <span className="admin-activity-detail">{item.detail}</span>}
              </div>
            ))}
          </div>
        </div>
      )}

      <div style={{ marginTop: "2rem", display: "flex", gap: "1rem", flexWrap: "wrap" }}>
        <Link href="/dashboard/admin/users" className="btn btn-primary" style={{ width: "auto" }}>
          View All Users
        </Link>
        <Link href="/dashboard/admin/alerts" className="btn btn-ghost">
          View All Alerts
        </Link>
        <Link href="/dashboard/admin/activity" className="btn btn-ghost">
          Bot Activity Log
        </Link>
      </div>
    </div>
  );
}
