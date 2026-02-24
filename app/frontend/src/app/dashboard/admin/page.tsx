"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/contexts/AuthContext";
import { fetchAdminStats } from "@/lib/api";
import type { AdminStats } from "@/lib/types";

export default function AdminOverviewPage() {
  const { token } = useAuth();
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!token) return;
    fetchAdminStats(token)
      .then(setStats)
      .catch(() => setError("Failed to load stats"));
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

      <div style={{ marginTop: "2rem", display: "flex", gap: "1rem" }}>
        <Link href="/dashboard/admin/users" className="btn btn-primary" style={{ width: "auto" }}>
          View All Users
        </Link>
        <Link href="/dashboard/admin/alerts" className="btn btn-ghost">
          View All Alerts
        </Link>
      </div>
    </div>
  );
}
