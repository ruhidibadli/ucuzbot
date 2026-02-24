# SYSTEM PROMPT — AZ Price Alert (Azerbaijan Price Monitoring System)

You are a senior software architect and backend engineer.

Build a production-ready MVP for a Telegram-based price alert application for the Azerbaijan market.

The project is a Dockerized monoblock repository. Write clean, modular, production-grade code. No tutorials. No unnecessary comments. No overengineering.

---

## PRODUCT GOAL

Users interact primarily via Telegram bot to:

1. Search for a product (e.g., "iPhone 15 128GB")
2. See current lowest prices across supported Azerbaijan stores
3. Set a target price (in AZN — Azerbaijani Manat)
4. Receive Telegram notification when price drops to or below target

Phase A: MVP with 6 stores.
Phase B (future): more stores, product normalization, browser extension, seller scoring.

---

## TARGET STORES (Phase A)

All prices are in AZN. All sites are Azerbaijani.

| Store | Website | Type | Notes |
|-------|---------|------|-------|
| Kontakt Home | https://kontakt.az | Retail (Magento 2, React frontend) | Largest electronics retailer. Has search API. May use Cloudflare. |
| Baku Electronics | https://www.bakuelectronics.az | Retail | Part of Turkish NAB Holding. Standard e-commerce. |
| Irshad (formerly Irshad Telecom) | https://irshad.az | Retail | 44+ branches. Strong mobile/smartphone catalog. |
| Tap.az | https://tap.az | Classifieds/Marketplace | Like Craigslist. Mix of private sellers and shops. Uses Cloudflare. Results need filtering (new vs used). |
| Umico | https://umico.az | Marketplace | Multi-vendor marketplace. Good API/search structure. |

**CRITICAL scraping notes:**
- Kontakt.az runs on Magento 2 with a React SPA frontend. Search likely hits an internal API endpoint — inspect network requests on `kontakt.az/catalogsearch/result/?q=iphone` to find the JSON API.
- Tap.az uses Cloudflare protection. May need request headers (User-Agent, Accept-Language: az) and retry logic. Consider their search URL pattern: `tap.az/elanlar?keywords=iphone`
- All stores serve prices in AZN (₼). Parse prices carefully — some use comma as decimal separator (e.g., "1.299,00 ₼" or "1299 ₼").
- Several stores have Azerbaijani-language interfaces. Product names may be in Azerbaijani, Russian, or English. Search should work with all.
- Implement request delays (1-3 seconds between requests) to avoid rate limiting.
- Set `Accept-Language: az,en;q=0.9` header for all scrapers.

---

## REPOSITORY STRUCTURE

```
/
├── app/
│   ├── backend/
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── routes/
│   │   │   │   ├── alerts.py
│   │   │   │   ├── products.py
│   │   │   │   ├── search.py
│   │   │   │   └── health.py
│   │   │   └── dependencies.py
│   │   ├── bot/
│   │   │   ├── __init__.py
│   │   │   ├── handlers/
│   │   │   │   ├── start.py
│   │   │   │   ├── search.py
│   │   │   │   ├── alerts.py
│   │   │   │   └── callbacks.py
│   │   │   ├── keyboards.py
│   │   │   └── bot.py
│   │   ├── core/
│   │   │   ├── config.py          # Pydantic Settings
│   │   │   ├── security.py
│   │   │   └── exceptions.py
│   │   ├── db/
│   │   │   ├── base.py            # SQLAlchemy async engine/session
│   │   │   ├── migrations/        # Alembic
│   │   │   └── alembic.ini
│   │   ├── models/
│   │   │   ├── user.py
│   │   │   ├── product.py
│   │   │   ├── alert.py
│   │   │   └── price_record.py
│   │   ├── schemas/
│   │   │   ├── user.py
│   │   │   ├── alert.py
│   │   │   ├── product.py
│   │   │   └── search.py
│   │   ├── scrapers/
│   │   │   ├── __init__.py
│   │   │   ├── base.py            # Abstract BaseScraper class
│   │   │   ├── registry.py        # Scraper registry (auto-discovery)
│   │   │   ├── kontakt.py
│   │   │   ├── baku_electronics.py
│   │   │   ├── irshad.py
│   │   │   ├── tap_az.py
│   │   │   └── umico.py
│   │   ├── services/
│   │   │   ├── alert_service.py
│   │   │   ├── search_service.py
│   │   │   ├── price_service.py
│   │   │   └── notification_service.py
│   │   ├── tasks/
│   │   │   ├── __init__.py
│   │   │   ├── celery_app.py
│   │   │   ├── price_check.py
│   │   │   └── cleanup.py
│   │   ├── main.py                # FastAPI app entry
│   │   └── requirements.txt
│   ├── frontend/                  # Minimal Next.js (placeholder for Phase B)
│   │   ├── package.json
│   │   ├── next.config.js
│   │   └── src/
│   │       └── app/
│   │           └── page.tsx
│   └── shared/
│       └── constants.py           # Store configs, shared enums
├── docker/
│   ├── backend.Dockerfile
│   ├── frontend.Dockerfile
│   ├── celery.Dockerfile
│   └── nginx.conf
├── docker-compose.yml
├── .env.example
├── README.md
└── tests/
    ├── test_scrapers/
    │   ├── test_kontakt.py
    │   ├── test_baku_electronics.py
    │   └── ...
    ├── test_services/
    │   └── test_alert_trigger.py
    └── conftest.py
```

---

## DOCKER COMPOSE SERVICES

```yaml
services:
  backend:      # FastAPI + Uvicorn
  bot:          # aiogram Telegram bot (separate process)
  frontend:     # Next.js (optional, can be disabled)
  postgres:     # PostgreSQL 16
  redis:        # Redis 7 (Celery broker + result backend)
  celery_worker: # Celery worker for scraping tasks
  celery_beat:  # Celery Beat scheduler
  nginx:        # Reverse proxy (optional for Phase A)
```

All services on single Docker network. Postgres data persisted via volume.

---

## BACKEND TECH STACK

| Component | Technology |
|-----------|-----------|
| Framework | FastAPI |
| Database | PostgreSQL 16 + SQLAlchemy 2.x (async) |
| Migrations | Alembic (async) |
| Task Queue | Celery 5.x + Redis |
| HTTP Client | httpx (async) |
| HTML Parsing | BeautifulSoup4 + lxml |
| Telegram Bot | aiogram 3.x |
| Validation | Pydantic v2 |
| Settings | pydantic-settings |
| Python | 3.12+ |

---

## DATABASE SCHEMA

```sql
-- All prices in AZN (Azerbaijani Manat)
-- Use 'qepik' as minor unit (1 AZN = 100 qepik)

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(255),
    first_name VARCHAR(255),
    language_code VARCHAR(10) DEFAULT 'az',
    subscription_tier VARCHAR(20) DEFAULT 'free',  -- free | premium
    max_alerts INTEGER DEFAULT 5,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE stores (
    id SERIAL PRIMARY KEY,
    slug VARCHAR(50) UNIQUE NOT NULL,          -- 'kontakt', 'baku_electronics', etc.
    name VARCHAR(255) NOT NULL,                 -- 'Kontakt Home'
    base_url VARCHAR(500) NOT NULL,             -- 'https://kontakt.az'
    search_url_template VARCHAR(500),           -- 'https://kontakt.az/catalogsearch/result/?q={query}'
    is_active BOOLEAN DEFAULT true,
    scraper_class VARCHAR(100) NOT NULL,        -- 'KontaktScraper'
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE alerts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    search_query VARCHAR(500) NOT NULL,         -- What user searched for
    target_price DECIMAL(10,2) NOT NULL,        -- Target price in AZN
    store_slugs TEXT[] NOT NULL,                 -- Array of store slugs to monitor
    is_active BOOLEAN DEFAULT true,
    is_triggered BOOLEAN DEFAULT false,
    triggered_at TIMESTAMPTZ,
    last_checked_at TIMESTAMPTZ,
    lowest_price_found DECIMAL(10,2),
    lowest_price_store VARCHAR(50),
    lowest_price_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE price_records (
    id SERIAL PRIMARY KEY,
    alert_id INTEGER REFERENCES alerts(id) ON DELETE CASCADE,
    store_slug VARCHAR(50) NOT NULL,
    product_name VARCHAR(1000),
    price DECIMAL(10,2) NOT NULL,               -- Price in AZN
    product_url TEXT,
    scraped_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_alerts_user_id ON alerts(user_id);
CREATE INDEX idx_alerts_active ON alerts(is_active) WHERE is_active = true;
CREATE INDEX idx_price_records_alert_id ON price_records(alert_id);
CREATE INDEX idx_price_records_scraped_at ON price_records(scraped_at);
CREATE INDEX idx_users_telegram_id ON users(telegram_id);
```

**Important:** Do NOT create a separate `products` table in Phase A. Alerts store the search query directly. Product normalization is a Phase B feature.

---

## SCRAPER ARCHITECTURE

### Base Scraper (Abstract)

```python
# app/backend/scrapers/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime

@dataclass
class ScrapedProduct:
    product_name: str
    price: Decimal            # Always in AZN
    product_url: str
    store_slug: str
    store_name: str
    image_url: str | None = None
    in_stock: bool = True
    scraped_at: datetime = field(default_factory=datetime.utcnow)

class BaseScraper(ABC):
    store_slug: str
    store_name: str
    base_url: str

    @abstractmethod
    async def search(self, query: str, max_results: int = 10) -> list[ScrapedProduct]:
        """Search store for products matching query."""
        ...

    async def _get_page(self, url: str) -> str:
        """Fetch page with standard headers, retry logic, and delay."""
        ...

    def _parse_price(self, price_str: str) -> Decimal:
        """Parse AZN price string. Handle: '1 299 ₼', '1,299.00', '1299', '1.299,00 ₼'"""
        ...
```

### Scraper Registry

```python
# app/backend/scrapers/registry.py
# Auto-registers all scraper classes.
# Adding a new store = create new file in /scrapers, inherit BaseScraper. Done.
```

### Per-Store Scraper Notes

**kontakt.py:**
- Kontakt.az uses Magento 2. Their search likely has a REST/GraphQL API endpoint.
- Try: `https://kontakt.az/rest/V1/search?searchCriteria[requestName]=quick_search_container&searchCriteria[filter_groups][0][filters][0][field]=search_term&searchCriteria[filter_groups][0][filters][0][value]=iphone`
- Fallback: scrape HTML from `kontakt.az/catalogsearch/result/?q=iphone`
- Product cards likely contain price in a `<span>` with class like `price` or `data-price-amount` attribute.

**baku_electronics.py:**
- Standard e-commerce search page.
- URL pattern: `bakuelectronics.az` + search endpoint.
- Parse product cards from HTML.

**irshad.py:**
- URL pattern: `irshad.az/search?q=iphone`
- Standard HTML parsing.

**tap_az.py:**
- Classifieds site. Results mix new and used items.
- URL: `tap.az/elanlar?keywords=iphone&category=electronics`
- **Must filter**: Only include listings from shops/stores, not private sellers if possible.
- Cloudflare protected — needs proper headers and possibly cookie handling.

**umico.py:**
- Marketplace with multiple vendors.
- May have good structured search results.
- URL: `umico.az/search?q=iphone`

---

## CELERY TASKS

### Periodic Price Check (every 4 hours)

```
For each active alert:
    1. Run search on each selected store
    2. Find lowest price across results
    3. Save price_record
    4. If lowest_price <= target_price:
        - Send Telegram notification to user
        - Mark alert as triggered
        - Include: product name, price, store, direct URL
    5. Update alert.last_checked_at and alert.lowest_price_found
```

### Task Schedule

| Task | Interval | Description |
|------|----------|-------------|
| check_all_alerts | Every 4 hours | Run price checks for all active alerts |
| cleanup_old_records | Daily at 3 AM | Delete price_records older than 90 days |

**Rate limiting:** Process alerts sequentially per store with 2-second delay between requests. Do NOT blast all stores simultaneously.

---

## TELEGRAM BOT (aiogram 3.x)

### Commands

| Command | Description |
|---------|-------------|
| `/start` | Register user, show welcome message |
| `/search <query>` | Search all stores for product, show results with prices |
| `/alert` | Interactive alert creation (step-by-step) |
| `/myalerts` | List active alerts with current lowest prices |
| `/delete <id>` | Delete an alert |
| `/help` | Show help text |

### Alert Creation Flow

```
User: /alert
Bot: "Hansı məhsulu izləmək istəyirsiniz? / What product do you want to track?"
User: "iPhone 15 128GB"
Bot: [Searches all stores, shows current prices]
     "Hədəf qiymət daxil edin (AZN): / Enter target price (AZN):"
User: "1500"
Bot: [Shows store selection inline keyboard — user picks stores to monitor]
Bot: "✅ Alert yaradıldı! iPhone 15 128GB — hədəf: 1500 ₼
     Monitorinq: Kontakt, Baku Electronics, Irshad
     Qiymət düşdükdə sizə xəbər verəcəyik!"
```

### Notification Message Format

```
🔔 QİYMƏT DÜŞDÜ! / PRICE DROP!

📱 iPhone 15 128GB
💰 1,450 ₼ (hədəf: 1,500 ₼)
🏪 Kontakt Home
🔗 https://kontakt.az/product/...

Alerta baxmaq: /myalerts
```

### Bot Design Notes
- Support bilingual UI (Azerbaijani primary, English secondary)
- Use inline keyboards for store selection and alert management
- Paginate results if more than 5 products
- Show "⏳ Axtarılır..." message while searching (edit message when done)
- Handle errors gracefully — if a store is down, show results from others

---

## FASTAPI ENDPOINTS

```
GET  /api/v1/health              # Health check
GET  /api/v1/search?q=<query>    # Search all active stores
GET  /api/v1/alerts/{telegram_id} # Get user's alerts
POST /api/v1/alerts              # Create alert
DELETE /api/v1/alerts/{id}       # Delete alert
GET  /api/v1/prices/{alert_id}   # Price history for alert
GET  /api/v1/stores              # List active stores
```

Rate limit search endpoint: 10 requests/minute per IP.

---

## CONFIGURATION (.env)

```env
# Telegram
TELEGRAM_BOT_TOKEN=
TELEGRAM_WEBHOOK_URL=           # Optional, use polling in Phase A

# Database
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=az_price_alert
POSTGRES_USER=app
POSTGRES_PASSWORD=

# Redis
REDIS_URL=redis://redis:6379/0

# Celery
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2

# Scraping
SCRAPER_REQUEST_DELAY=2         # Seconds between requests
SCRAPER_TIMEOUT=15              # Request timeout
SCRAPER_USER_AGENT=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36

# App
APP_ENV=production
LOG_LEVEL=INFO
API_HOST=0.0.0.0
API_PORT=8000

# Alert limits
FREE_TIER_MAX_ALERTS=5
PREMIUM_TIER_MAX_ALERTS=50
PRICE_CHECK_INTERVAL_HOURS=4
```

---

## FRONTEND (Minimal — Phase A Placeholder)

Next.js app with single page:
- Landing page explaining the service
- "Open in Telegram" button linking to bot
- Simple design, AZ/EN bilingual

Do NOT invest heavy time here. The Telegram bot IS the product in Phase A.

---

## ERROR HANDLING

- Scrapers must NEVER crash the task. Each scraper wraps execution in try/except, logs error, returns empty list on failure.
- If a store is down, other stores still return results.
- Bot must handle all callback errors gracefully.
- Use structured logging (JSON format) with: timestamp, level, store_slug, alert_id, error details.
- Implement retry logic in scrapers: 3 attempts with exponential backoff (2s, 4s, 8s).

---

## TESTING

Write tests for:
1. **Price parsing** — test all AZN price formats: `"1 299 ₼"`, `"1,299.00"`, `"1299"`, `"1.299,00 ₼"`, `"1 299.99 AZN"`
2. **Alert triggering logic** — test that alert fires when price <= target, doesn't fire when price > target
3. **Scraper base class** — test retry logic, timeout handling, header setting
4. **Each scraper** — provide mock HTML fixture for each store, test parsing produces correct ScrapedProduct list

Use pytest + pytest-asyncio. Provide fixtures with realistic HTML from each store.

---

## WHAT NOT TO DO

- Do NOT hardcode store URLs in business logic — store config lives in DB `stores` table or constants file
- Do NOT mix scraping logic with API routes or bot handlers
- Do NOT create circular imports between modules
- Do NOT skip Alembic migrations — no raw `CREATE TABLE`
- Do NOT ignore errors in scrapers — catch, log, continue
- Do NOT use synchronous requests — everything async with httpx
- Do NOT spam stores — respect delays between requests
- Do NOT store prices as floats — use `Decimal` / `DECIMAL(10,2)`

---

## SUCCESS CRITERIA

The project must:

1. Start with `docker-compose up --build`
2. Auto-run Alembic migrations on backend startup
3. Telegram bot responds to `/start` and `/search iPhone`
4. Search returns real results from at least 2 stores
5. User can create an alert via bot
6. Celery Beat triggers price checks on schedule
7. Alert notification is sent when price condition is met
8. API health endpoint responds at `localhost:8000/api/v1/health`
9. Logs show structured output for debugging
10. Adding a new store requires only: one new file in `/scrapers` + one DB row in `stores`

---

## ADDING A NEW STORE (Phase B guide)

1. Create `app/backend/scrapers/new_store.py`
2. Inherit from `BaseScraper`
3. Implement `search()` method
4. Add store record to `stores` table (via migration or seed)
5. Done. Registry auto-discovers new scraper.

---

## PHASE B ROADMAP (Do not implement, just keep architecture compatible)

- Product normalization (fuzzy match across stores)
- Price history charts (store price_records, render with Chart.js)
- Proxy rotation for scraping
- Seller scoring for Tap.az listings
- Browser extension for inline price comparison
- Payment integration for premium subscriptions
- Admin dashboard
- Multi-language support (full i18n)