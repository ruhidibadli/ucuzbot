"use client";

import { useState } from "react";
import Link from "next/link";
import { searchProducts } from "@/lib/api";
import type { SearchResult } from "@/lib/types";

function notifySearchResults(query: string, count: number) {
  if (typeof window === "undefined" || count === 0) return;
  if ("Notification" in window && Notification.permission === "granted") {
    new Notification("UcuzBot — Neticeler tapildi!", {
      body: `"${query}" ucun ${count} neice / ${count} results for "${query}"`,
      icon: "/icon-192.png",
      tag: "ucuzbot-search",
    });
  }
}

export default function DashboardSearchPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState(false);

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!query.trim()) return;

    // Request permission on user gesture (browsers block it outside of clicks)
    if ("Notification" in window && Notification.permission === "default") {
      await Notification.requestPermission();
    }

    setLoading(true);
    setError(null);
    setHasSearched(true);
    try {
      const data = await searchProducts(query.trim());
      setResults(data);
      notifySearchResults(query.trim(), data.length);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Search failed");
      setResults([]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="dashboard-page">
      <div className="section-header">
        <h2 className="section-title">M&#601;hsul Axtarisi / Product Search</h2>
        <p className="section-subtitle">Qiym&#601;tl&#601;ri muqayis&#601; edin / Compare prices across all stores</p>
      </div>

      <div className="search-wrapper">
        <form onSubmit={handleSearch} className="search-form">
          <input
            type="text"
            className="form-input search-input"
            placeholder="m&#601;s. iPhone 15, Samsung Galaxy, AirPods..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            maxLength={500}
          />
          <button type="submit" disabled={loading} className="btn btn-primary btn-search">
            {loading ? "Axtarilir..." : "Axtar / Search"}
          </button>
        </form>

        {error && <div className="alert-msg alert-msg-error">{error}</div>}

        {results.length > 0 && (
          <div className="search-results">
            {results.map((r, i) => (
              <div key={`${r.store_slug}-${r.product_url}-${i}`} className="search-result-card-dashboard">
                <a
                  href={r.product_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="search-result-card"
                >
                  {r.image_url && (
                    <div className="search-result-img">
                      <img src={r.image_url} alt={r.product_name} loading="lazy" />
                    </div>
                  )}
                  <div className="search-result-info">
                    <div className="search-result-name">{r.product_name}</div>
                    <div className="search-result-store">{r.store_name}</div>
                  </div>
                  <div className="search-result-price">{r.price} AZN</div>
                </a>
                <Link
                  href={`/dashboard/alerts/create?q=${encodeURIComponent(r.product_name)}`}
                  className="search-result-alert-link"
                >
                  Alert yarat
                </Link>
              </div>
            ))}
          </div>
        )}

        {hasSearched && !loading && results.length === 0 && !error && (
          <div className="search-no-results">
            N&#601;tic&#601; tapilmadi / No results found
          </div>
        )}
      </div>
    </div>
  );
}
