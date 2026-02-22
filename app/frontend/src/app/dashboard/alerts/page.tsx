"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { useAuth } from "@/contexts/AuthContext";
import { fetchAlerts, deleteAlert, checkAlertNow } from "@/lib/api";
import type { AlertData } from "@/lib/types";
import AlertCard from "@/components/AlertCard";

export default function AlertsPage() {
  const { token } = useAuth();
  const [alerts, setAlerts] = useState<AlertData[]>([]);
  const [loading, setLoading] = useState(true);
  const [checkingAlertId, setCheckingAlertId] = useState<number | null>(null);

  const loadAlerts = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    const data = await fetchAlerts(token);
    setAlerts(data);
    setLoading(false);
  }, [token]);

  useEffect(() => {
    loadAlerts();
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
    setTimeout(loadAlerts, 10000);
    setTimeout(() => setCheckingAlertId(null), 2000);
  }

  return (
    <div className="dashboard-page">
      <div className="section-header">
        <div className="dashboard-alerts-header">
          <div>
            <h2 className="section-title">Alertl&#601;rim / My Alerts</h2>
            <p className="section-subtitle">Butun qiym&#601;t alertl&#601;riniz / All your price alerts</p>
          </div>
          <Link href="/dashboard/alerts/create" className="btn btn-primary dashboard-action-btn">
            Yeni Alert / New Alert
          </Link>
        </div>
      </div>

      {loading && <div className="my-alerts-loading">Yukl&#601;nir... / Loading...</div>}

      {!loading && alerts.length === 0 && (
        <div className="dashboard-empty">
          H&#601;l&#601; alert yoxdur.{" "}
          <Link href="/dashboard/alerts/create" className="my-alert-link">
            Yeni alert yaradin / Create your first alert
          </Link>
        </div>
      )}

      {!loading && (
        <div className="my-alerts-list">
          {alerts.map((alert) => (
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
    </div>
  );
}
