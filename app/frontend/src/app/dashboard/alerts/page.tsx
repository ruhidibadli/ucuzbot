"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import Link from "next/link";
import { useAuth } from "@/contexts/AuthContext";
import { fetchAlerts, deleteAlert, checkAlertNow } from "@/lib/api";
import type { AlertData } from "@/lib/types";
import AlertCard from "@/components/AlertCard";

const POLL_INTERVAL = 30_000; // 30 seconds
const CHECK_POLL_INTERVAL = 5_000; // 5 seconds after "Check Now"
const CHECK_POLL_DURATION = 60_000; // poll for 60 seconds after "Check Now"

function showTriggeredNotification(alert: AlertData) {
  if (typeof window === "undefined") return;
  if ("Notification" in window && Notification.permission === "granted") {
    new Notification("UcuzaTap — Qiymet dusdu! / Price drop!", {
      body: `${alert.search_query}\n${alert.lowest_price_found} AZN`,
      icon: "/icon-192.png",
      tag: `ucuzbot-triggered-${alert.id}`,
    });
  }
}

export default function AlertsPage() {
  const { token } = useAuth();
  const [alerts, setAlerts] = useState<AlertData[]>([]);
  const [loading, setLoading] = useState(true);
  const [checkingAlertId, setCheckingAlertId] = useState<number | null>(null);
  const triggeredIdsRef = useRef<Set<number>>(new Set());
  const isFirstLoadRef = useRef(true);
  const checkPollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const loadAlerts = useCallback(async (showLoading = false) => {
    if (!token) return;
    if (showLoading) setLoading(true);
    try {
      const data = await fetchAlerts(token);

      if (isFirstLoadRef.current) {
        // First load: record existing triggered IDs without notifying
        for (const alert of data) {
          if (alert.is_triggered) {
            triggeredIdsRef.current.add(alert.id);
          }
        }
        isFirstLoadRef.current = false;
      } else {
        // Subsequent loads: detect newly triggered alerts and notify
        for (const alert of data) {
          if (alert.is_triggered && !triggeredIdsRef.current.has(alert.id)) {
            triggeredIdsRef.current.add(alert.id);
            showTriggeredNotification(alert);
          }
        }
      }

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
    // Request permission on user gesture
    if ("Notification" in window && Notification.permission === "default") {
      await Notification.requestPermission();
    }

    setCheckingAlertId(id);
    await checkAlertNow(token, id);

    // Clear any previous check polling
    if (checkPollRef.current) clearInterval(checkPollRef.current);

    // Poll frequently to catch the check result
    checkPollRef.current = setInterval(() => loadAlerts(), CHECK_POLL_INTERVAL);
    setTimeout(() => {
      if (checkPollRef.current) clearInterval(checkPollRef.current);
      checkPollRef.current = null;
      setCheckingAlertId(null);
    }, CHECK_POLL_DURATION);
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
