"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import Link from "next/link";
import { useAuth } from "@/contexts/AuthContext";
import { fetchAlerts, deleteAlert, checkAlertNow } from "@/lib/api";
import type { AlertData } from "@/lib/types";
import AlertCard from "@/components/AlertCard";

const POLL_INTERVAL = 30_000;

export default function DashboardPage() {
  const { token } = useAuth();
  const [alerts, setAlerts] = useState<AlertData[]>([]);
  const [loading, setLoading] = useState(true);
  const [checkingAlertId, setCheckingAlertId] = useState<number | null>(null);
  const checkPollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const loadAlerts = useCallback(async (showLoading = false) => {
    if (!token) return;
    if (showLoading) setLoading(true);
    try {
      const data = await fetchAlerts(token);
      setAlerts(data);
    } catch {
      // Network error during polling — ignore silently
    }
    if (showLoading) setLoading(false);
  }, [token]);

  // Initial load
  useEffect(() => {
    loadAlerts(true);
  }, [loadAlerts]);

  // Auto-poll every 30 seconds
  useEffect(() => {
    const interval = setInterval(() => loadAlerts(), POLL_INTERVAL);
    return () => clearInterval(interval);
  }, [loadAlerts]);

  async function handleDelete(id: number) {
    const ok = await deleteAlert(token, id);
    if (ok) {
      setAlerts((prev) => prev.filter((a) => a.id !== id));
    }
  }

  async function handleCheckNow(id: number) {
    setCheckingAlertId(id);
    await checkAlertNow(token, id);

    if (checkPollRef.current) clearInterval(checkPollRef.current);
    checkPollRef.current = setInterval(() => loadAlerts(), 5_000);
    setTimeout(() => {
      if (checkPollRef.current) clearInterval(checkPollRef.current);
      checkPollRef.current = null;
      setCheckingAlertId(null);
    }, 60_000);
  }

  const total = alerts.length;
  const active = alerts.filter((a) => a.is_active && !a.is_triggered).length;
  const triggered = alerts.filter((a) => a.is_triggered).length;
  const recent = alerts.slice(0, 3);

  return (
    <div className="dashboard-page">
      <div className="section-header">
        <h2 className="section-title">Icmal / Overview</h2>
        <p className="section-subtitle">Alertl&#601;rinizin xulas&#601;si / Your alerts at a glance</p>
      </div>

      {/* Stats */}
      <div className="dashboard-stats">
        <div className="dashboard-stat-card">
          <div className="dashboard-stat-number">{total}</div>
          <div className="dashboard-stat-label">Cemi / Total</div>
        </div>
        <div className="dashboard-stat-card">
          <div className="dashboard-stat-number">{active}</div>
          <div className="dashboard-stat-label">Aktiv / Active</div>
        </div>
        <div className="dashboard-stat-card">
          <div className="dashboard-stat-number">{triggered}</div>
          <div className="dashboard-stat-label">Tapildi / Triggered</div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="dashboard-actions">
        <Link href="/dashboard/alerts/create" className="btn btn-primary dashboard-action-btn">
          Alert Yarat / Create Alert
        </Link>
        <Link href="/dashboard/search" className="btn btn-ghost dashboard-action-btn">
          Mehsul Axtar / Search Products
        </Link>
      </div>

      {/* Recent Alerts */}
      <div className="dashboard-recent">
        <h3 className="dashboard-recent-title">Son alertl&#601;r / Recent Alerts</h3>
        {loading && <div className="my-alerts-loading">Yukl&#601;nir... / Loading...</div>}
        {!loading && recent.length === 0 && (
          <div className="dashboard-empty">
            H&#601;l&#601; alert yoxdur.{" "}
            <Link href="/dashboard/alerts/create" className="my-alert-link">
              Yeni alert yaradın / Create your first alert
            </Link>
          </div>
        )}
        {!loading && (
          <div className="my-alerts-list">
            {recent.map((alert) => (
              <AlertCard
                key={alert.id}
                alert={alert}
                onDelete={handleDelete}
                onCheckNow={handleCheckNow}
                checkingAlertId={checkingAlertId}
              />
            ))}
          </div>
        )}
        {!loading && alerts.length > 3 && (
          <div style={{ textAlign: "center", marginTop: "1rem" }}>
            <Link href="/dashboard/alerts" className="my-alert-link">
              Butun alertl&#601;r&#601; bax / View all alerts ({alerts.length})
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}
