"use client";

import { useEffect, useState, useCallback } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { fetchAdminUsers } from "@/lib/api";
import type { AdminUserListItem } from "@/lib/types";

export default function AdminUsersPage() {
  const { token } = useAuth();
  const [users, setUsers] = useState<AdminUserListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [loading, setLoading] = useState(true);
  const pageSize = 20;

  const load = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    try {
      const data = await fetchAdminUsers(token, page, pageSize, search);
      setUsers(data.users);
      setTotal(data.total);
    } catch {
      /* ignore */
    } finally {
      setLoading(false);
    }
  }, [token, page, search]);

  useEffect(() => {
    load();
  }, [load]);

  const totalPages = Math.ceil(total / pageSize);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    setSearch(searchInput);
  };

  return (
    <div className="dashboard-page">
      <h1 className="section-title" style={{ marginBottom: "1.5rem" }}>
        Users ({total})
      </h1>

      <form onSubmit={handleSearch} className="admin-search-bar">
        <input
          type="text"
          className="form-input"
          placeholder="Search by email or name..."
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
        />
        <button type="submit" className="btn btn-primary" style={{ width: "auto" }}>
          Search
        </button>
      </form>

      {loading ? (
        <div className="dashboard-loading" style={{ minHeight: "200px" }}>
          <div className="dashboard-spinner" />
        </div>
      ) : users.length === 0 ? (
        <div className="dashboard-empty">No users found.</div>
      ) : (
        <>
          <div className="admin-table-container">
            <table className="admin-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Email</th>
                  <th>Name</th>
                  <th>Telegram</th>
                  <th>Tier</th>
                  <th>Alerts</th>
                  <th>Active</th>
                  <th>Triggered</th>
                  <th>Status</th>
                  <th>Joined</th>
                </tr>
              </thead>
              <tbody>
                {users.map((u) => (
                  <tr key={u.id}>
                    <td>{u.id}</td>
                    <td>{u.email || "—"}</td>
                    <td>{u.first_name || "—"}</td>
                    <td>{u.telegram_id || "—"}</td>
                    <td>
                      <span className={`admin-badge ${u.subscription_tier === "premium" ? "admin-badge--warning" : "admin-badge--inactive"}`}>
                        {u.subscription_tier}
                      </span>
                    </td>
                    <td>{u.alert_count}</td>
                    <td>{u.active_alert_count}</td>
                    <td>{u.triggered_alert_count}</td>
                    <td>
                      <span className={`admin-badge ${u.is_active ? "admin-badge--success" : "admin-badge--inactive"}`}>
                        {u.is_active ? "Active" : "Inactive"}
                      </span>
                    </td>
                    <td>{new Date(u.created_at).toLocaleDateString()}</td>
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
