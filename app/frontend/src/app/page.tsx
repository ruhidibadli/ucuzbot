"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/contexts/AuthContext";
import { stores } from "@/lib/constants";
import { searchProducts } from "@/lib/api";
import type { SearchResult } from "@/lib/types";
import AuthModal from "@/components/AuthModal";

function notifySearchResults(query: string, count: number) {
  if (typeof window === "undefined" || count === 0) return;
  if ("Notification" in window && Notification.permission === "granted") {
    new Notification("UcuzaTap — Neticeler tapildi!", {
      body: `"${query}" ucun ${count} neice / ${count} results for "${query}"`,
      icon: "/icon-192.png",
      tag: "ucuzbot-search",
    });
  }
}

export default function Home() {
  const { user, token, isLoading } = useAuth();
  const router = useRouter();
  const [showAuthModal, setShowAuthModal] = useState(false);

  // Search state
  const [productSearch, setProductSearch] = useState("");
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState(false);

  async function handleProductSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!productSearch.trim()) return;

    // Request permission on user gesture (browsers block it outside of clicks)
    if ("Notification" in window && Notification.permission === "default") {
      await Notification.requestPermission();
    }

    setSearchLoading(true);
    setSearchError(null);
    setHasSearched(true);
    try {
      const data = await searchProducts(productSearch.trim());
      setSearchResults(data);
      notifySearchResults(productSearch.trim(), data.length);
    } catch (err: unknown) {
      setSearchError(err instanceof Error ? err.message : "Search failed");
      setSearchResults([]);
    } finally {
      setSearchLoading(false);
    }
  }

  function handleAuthSuccess() {
    setShowAuthModal(false);
    router.push("/dashboard");
  }

  return (
    <div>
      {/* Background Glows */}
      <div className="bg-glow bg-glow-1" />
      <div className="bg-glow bg-glow-2" />

      {/* Navbar */}
      <nav className="navbar">
        <div className="navbar-left">
          <span className="navbar-logo">UcuzaTap</span>
          <span className="navbar-tag">Beta</span>
        </div>
        <div className="navbar-right">
          <a
            href="https://t.me/UcuzaTap_bot"
            target="_blank"
            rel="noopener noreferrer"
            className="navbar-telegram"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
              <path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.479.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z"/>
            </svg>
            Telegram Bot
          </a>
          {!isLoading && token ? (
            <Link href="/dashboard" className="btn btn-auth">
              Dashboard
            </Link>
          ) : (
            <button
              onClick={() => setShowAuthModal(true)}
              className="btn btn-auth"
            >
              Daxil ol / Login
            </button>
          )}
        </div>
      </nav>

      {/* Auth Modal */}
      <AuthModal
        isOpen={showAuthModal}
        onClose={() => setShowAuthModal(false)}
        onSuccess={handleAuthSuccess}
      />

      {/* Hero */}
      <section className="hero">
        <div className="animate-fade-in-up delay-1">
          <span className="hero-badge">
            <span>&#9889;</span>
            Az&#601;rbaycanın qiym&#601;t izl&#601;yicisi
          </span>
        </div>

        <h1 className="hero-title animate-fade-in-up delay-2">
          <span className="hero-title-gradient">
            &#399;n ucuz qiym&#601;ti tapın,
          </span>
          <br />
          pul q&#601;na&#601;t edin
        </h1>

        <p className="hero-description animate-fade-in-up delay-3">
          UcuzaTap Az&#601;rbaycanın 5 b&#246;y&#252;k ma&#287;azasında qiym&#601;tl&#601;ri avtomatik izl&#601;yir.
          İst&#601;diyiniz m&#601;hsulun qiym&#601;tini t&#601;yin edin — qiym&#601;t d&#252;&#351;&#601;n kimi siz&#601; bildiri&#351; g&#246;nd&#601;r&#601;k.
        </p>
        <p className="hero-description-en animate-fade-in-up delay-3">
          UcuzaTap automatically tracks prices across 5 major Azerbaijan stores.
          Set your target price for any product — we&apos;ll notify you the moment it drops.
        </p>

        <div className="hero-stats animate-fade-in-up delay-4">
          <div className="hero-stat">
            <div className="hero-stat-number">5</div>
            <div className="hero-stat-label">Ma&#287;aza / Stores</div>
          </div>
          <div className="hero-stat">
            <div className="hero-stat-number">24/7</div>
            <div className="hero-stat-label">Monitorinq / Monitoring</div>
          </div>
          <div className="hero-stat">
            <div className="hero-stat-number">&#8380;</div>
            <div className="hero-stat-label">AZN il&#601; / Prices in AZN</div>
          </div>
        </div>
      </section>

      <div className="section-divider" />

      {/* How It Works */}
      <section className="section">
        <div className="section-header animate-fade-in-up delay-1">
          <div className="section-label">Nec&#601; i&#351;l&#601;yir / How it works</div>
          <h2 className="section-title">3 sad&#601; addım il&#601; ba&#351;layın</h2>
          <p className="section-subtitle">Get started in 3 simple steps</p>
        </div>

        <div className="steps-grid">
          <div className="step-card animate-fade-in-up delay-2">
            <span className="step-number">1</span>
            <span className="step-icon">&#128270;</span>
            <div className="step-title">Bildiri&#351;l&#601;ri aktivl&#601;&#351;dirin</div>
            <div className="step-desc">
              Brauzerd&#601; bildiri&#351;l&#601;r&#601; icaz&#601; verin ki, qiym&#601;t d&#252;&#351;&#601;nd&#601; anında x&#601;b&#601;r alasınız.
            </div>
            <div className="step-desc-en">Enable browser notifications to get instant price drop alerts.</div>
          </div>
          <div className="step-card animate-fade-in-up delay-3">
            <span className="step-number">2</span>
            <span className="step-icon">&#127919;</span>
            <div className="step-title">H&#601;d&#601;f qiym&#601;t t&#601;yin edin</div>
            <div className="step-desc">
              Axtardı&#287;ınız m&#601;hsulu yazın, h&#601;d&#601;f qiym&#601;ti daxil edin v&#601; ma&#287;azaları se&#231;in.
            </div>
            <div className="step-desc-en">Enter the product, set your target price, and pick stores.</div>
          </div>
          <div className="step-card animate-fade-in-up delay-4">
            <span className="step-number">3</span>
            <span className="step-icon">&#128276;</span>
            <div className="step-title">Bildiri&#351; alın</div>
            <div className="step-desc">
              Qiym&#601;t h&#601;d&#601;finiz&#601; &#231;atanda v&#601; ya a&#351;a&#287;ı d&#252;&#351;&#601;nd&#601; d&#601;rhal bildiri&#351; alacaqsınız.
            </div>
            <div className="step-desc-en">Get notified instantly when the price hits your target.</div>
          </div>
        </div>
      </section>

      <div className="section-divider" />

      {/* Instructions */}
      <section className="section">
        <div className="section-header animate-fade-in-up delay-1">
          <div className="section-label">T&#601;limatlar / Instructions</div>
          <h2 className="section-title">İstifad&#601; qaydası</h2>
          <p className="section-subtitle">How to use UcuzaTap</p>
        </div>

        <div className="instructions-grid">
          <div className="instruction-card animate-fade-in-up delay-2">
            <div className="instruction-icon">&#128270;</div>
            <div className="instruction-title">M&#601;hsul Axtarı&#351;ı / Product Search</div>
            <div className="instruction-text">
              A&#351;a&#287;ıdakı axtarı&#351; b&#246;lm&#601;sind&#601; m&#601;hsul adınızı yazın. B&#252;t&#252;n ma&#287;azalarda canlı qiym&#601;tl&#601;ri g&#246;r&#601;c&#601;ksiniz.
            </div>
            <div className="instruction-text-en">
              Type your product name in the search section below. You will see live prices from all stores.
            </div>
          </div>
          <div className="instruction-card animate-fade-in-up delay-3">
            <div className="instruction-icon">&#128276;</div>
            <div className="instruction-title">Qiym&#601;t Alertl&#601;ri / Price Alerts</div>
            <div className="instruction-text">
              H&#601;d&#601;f qiym&#601;t t&#601;yin edin. Sistem h&#601;r 4 saatdan bir qiym&#601;tl&#601;ri yoxlayır v&#601; qiym&#601;t d&#252;&#351;&#601;nd&#601; siz&#601; x&#601;b&#601;r verir.
            </div>
            <div className="instruction-text-en">
              Set a target price. The system checks prices every 4 hours and notifies you when the price drops.
            </div>
          </div>
          <div className="instruction-card animate-fade-in-up delay-4">
            <div className="instruction-icon">&#128100;</div>
            <div className="instruction-title">Hesab / Account</div>
            <div className="instruction-text">
              Qeydiyyatdan ke&#231;in ki, alertl&#601;riniz b&#252;t&#252;n cihazlarda sinxron olsun. Qeydiyyatsız da bildiri&#351; il&#601; i&#351;l&#601;y&#601; bil&#601;rsiniz.
            </div>
            <div className="instruction-text-en">
              Register to sync alerts across devices. You can also use push notifications without an account.
            </div>
          </div>
          <div className="instruction-card animate-fade-in-up delay-5">
            <div className="instruction-icon">&#128640;</div>
            <div className="instruction-title">Telegram Bot</div>
            <div className="instruction-text">
              <a href="https://t.me/UcuzaTap_bot" target="_blank" rel="noopener noreferrer" className="instruction-link">
                @UcuzaTap_bot
              </a>
              {" "}il&#601; Telegram-dan da istifad&#601; ed&#601; bil&#601;rsiniz. Mesaj yazın — avtomatik axtarı&#351; ed&#601;c&#601;k.
            </div>
            <div className="instruction-text-en">
              You can also use{" "}
              <a href="https://t.me/UcuzaTap_bot" target="_blank" rel="noopener noreferrer" className="instruction-link">
                @UcuzaTap_bot
              </a>
              {" "}on Telegram. Just type a product name — it searches automatically.
            </div>
          </div>
        </div>
      </section>

      <div className="section-divider" />

      {/* Stores */}
      <section className="section">
        <div className="section-header animate-fade-in-up delay-1">
          <div className="section-label">Ma&#287;azalar / Stores</div>
          <h2 className="section-title">D&#601;st&#601;kl&#601;n&#601;n ma&#287;azalar</h2>
          <p className="section-subtitle">We track prices from these stores</p>
        </div>

        <div className="stores-grid">
          {stores.map((store, i) => (
            <div
              key={store.slug}
              className={`store-card animate-fade-in-up delay-${Math.min(i + 2, 5)}`}
            >
              <div className="store-icon">{store.icon}</div>
              <div>
                <div className="store-name">{store.name}</div>
                <div className="store-type">{store.type}</div>
              </div>
            </div>
          ))}
        </div>
      </section>

      <div className="section-divider" />

      {/* Product Search */}
      <section className="section" id="search">
        <div className="section-header animate-fade-in-up delay-1">
          <div className="section-label">M&#601;hsul Axtarı&#351;ı / Product Search</div>
          <h2 className="section-title">Qiym&#601;tl&#601;ri m&#252;qayis&#601; edin</h2>
          <p className="section-subtitle">Compare prices across all stores</p>
        </div>

        <div className="search-wrapper animate-fade-in-up delay-2">
          <form onSubmit={handleProductSearch} className="search-form">
            <input
              type="text"
              className="form-input search-input"
              placeholder="m&#601;s. iPhone 15, Samsung Galaxy, AirPods..."
              value={productSearch}
              onChange={(e) => setProductSearch(e.target.value)}
              maxLength={500}
            />
            <button type="submit" disabled={searchLoading} className="btn btn-primary btn-search">
              {searchLoading ? "Axtarılır..." : "Axtar / Search"}
            </button>
          </form>

          {searchError && (
            <div className="alert-msg alert-msg-error">{searchError}</div>
          )}

          {searchResults.length > 0 && (
            <div className="search-results">
              {searchResults.map((r, i) => (
                <a
                  key={`${r.store_slug}-${r.product_url}-${i}`}
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
              ))}
            </div>
          )}

          {hasSearched && !searchLoading && searchResults.length === 0 && !searchError && (
            <div className="search-no-results">
              N&#601;tic&#601; tapılmadı / No results found
            </div>
          )}
        </div>
      </section>

      <div className="section-divider" />

      {/* Footer */}
      <footer className="footer">
        <div className="footer-logo">UcuzaTap</div>
        <div className="footer-text">
          Az&#601;rbaycanda &#601;n yaxşı qiym&#601;tl&#601;ri izl&#601;yin
          &bull; Track the best prices in Azerbaijan
        </div>
        <div className="footer-links">
          <a href="#search" className="footer-link">Axtarı&#351; / Search</a>
          {token ? (
            <Link href="/dashboard/alerts/create" className="footer-link">Alert Yarat / Create Alert</Link>
          ) : (
            <button onClick={() => setShowAuthModal(true)} className="footer-link" style={{ background: "none", border: "none", cursor: "pointer", fontFamily: "var(--font-main)" }}>
              Alert Yarat / Create Alert
            </button>
          )}
          <a
            href="https://t.me/UcuzaTap_bot"
            target="_blank"
            rel="noopener noreferrer"
            className="footer-link"
          >
            Telegram Bot
          </a>
        </div>
        <div className="footer-text" style={{ marginTop: "0.5rem" }}>
          &copy; {new Date().getFullYear()} ucuzatap.az
        </div>
      </footer>
    </div>
  );
}
