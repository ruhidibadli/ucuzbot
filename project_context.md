# UcuzBot — Project Context

> Paste this file at the start of any new AI chat session to give the agent full context without browsing files.

## What Is This?

UcuzBot is a **price tracking system for Azerbaijan e-commerce stores**. Users create price alerts (e.g. "iPhone 15 under 1500 AZN") and get notified via **browser push notifications** when prices drop. The system scrapes 6 Azerbaijani stores on a schedule using Celery.

**Current status:** Telegram bot is fully functional with button-driven UX (no commands required). Browser push notifications also active. **Web authentication (email/password)** allows cross-device alert sync.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend API | FastAPI 0.115.6, Python 3.12 |
| Database | PostgreSQL 16 (async via SQLAlchemy 2.0 + asyncpg) |
| Migrations | Alembic |
| Task Queue | Celery 5.4 + Redis 7 (broker + backend) |
| Scrapers | httpx + BeautifulSoup4 + lxml |
| Push Notifications | pywebpush 2.0 (Web Push API + VAPID) |
| Auth | bcrypt 4.2.1 (password hashing) + PyJWT 2.10.1 (JWT tokens) |
| Frontend | Next.js 14 + React 18 + TypeScript |
| Infra | Docker Compose, Nginx reverse proxy |
| Logging | structlog 24.4 (JSON in prod, console in dev) |

## Directory Structure

```
D:\ucuzbot/
├── app/
│   ├── backend/
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   │   ├── alerts.py          # Alert CRUD (supports telegram_id, push_endpoint, JWT auth)
│   │   │   │   ├── auth.py            # POST register, POST login, GET me
│   │   │   │   ├── health.py          # GET /api/v1/health
│   │   │   │   ├── products.py        # Price history, store list
│   │   │   │   ├── push.py            # Push subscribe/unsubscribe/vapid-key
│   │   │   │   └── search.py          # Multi-store product search
│   │   │   └── dependencies.py        # DB session, rate limiting, get_current_user, get_optional_user
│   │   ├── bot/                        # Telegram bot (button-driven UX)
│   │   │   ├── handlers/
│   │   │   │   ├── start.py           # /start, /help, reply keyboard button handlers
│   │   │   │   ├── search.py          # /search, SearchFlow FSM, _execute_search()
│   │   │   │   ├── alerts.py          # /alert, /myalerts, /delete, AlertCreation FSM
│   │   │   │   ├── callbacks.py       # Inline button callbacks (menu, store, alert actions)
│   │   │   │   └── fallback.py        # Catch-all: plain text → auto search (registered last)
│   │   │   ├── keyboards.py           # Reply + inline keyboards (15 keyboard functions)
│   │   │   └── bot.py
│   │   ├── core/
│   │   │   ├── auth.py                # hash_password, verify_password, create_jwt, decode_jwt
│   │   │   ├── config.py              # Pydantic Settings (all env vars incl. JWT_SECRET_KEY)
│   │   │   ├── exceptions.py          # Custom exceptions
│   │   │   ├── logging.py             # structlog setup
│   │   │   └── security.py            # In-memory rate limiter
│   │   ├── db/
│   │   │   ├── base.py                # SQLAlchemy async engine + session factory
│   │   │   ├── alembic.ini
│   │   │   └── migrations/versions/
│   │   │       ├── 001_initial.py     # users, stores, alerts, price_records
│   │   │       ├── 002_push_subscriptions.py  # push_subscriptions table + alerts changes
│   │   │       └── 003_web_auth.py    # email, password_hash columns + telegram_id nullable
│   │   ├── models/
│   │   │   ├── __init__.py            # Exports: User, Store, Alert, PriceRecord, PushSubscription
│   │   │   ├── user.py               # telegram_id nullable, email, password_hash
│   │   │   ├── store.py
│   │   │   ├── alert.py               # user_id nullable, has push_subscription_id FK
│   │   │   ├── price_record.py
│   │   │   └── push_subscription.py   # endpoint, p256dh, auth keys
│   │   ├── schemas/
│   │   │   ├── alert.py               # AlertCreate (telegram_id OR push_endpoint), AlertResponse
│   │   │   ├── auth.py                # RegisterRequest, LoginRequest, AuthResponse, UserProfile
│   │   │   ├── push.py                # PushSubscribeRequest, VapidKeyResponse, etc.
│   │   │   ├── product.py
│   │   │   └── search.py
│   │   ├── scrapers/
│   │   │   ├── base.py                # BaseScraper ABC + ScrapedProduct dataclass
│   │   │   ├── registry.py            # Auto-discovery scraper registry
│   │   │   ├── kontakt.py             # Kontakt Home (Magento 2 API + HTML fallback)
│   │   │   ├── baku_electronics.py
│   │   │   ├── irshad.py
│   │   │   ├── maxi.py
│   │   │   ├── tap_az.py
│   │   │   └── umico.py
│   │   ├── services/
│   │   │   ├── alert_service.py       # create_alert, create_alert_for_push, get_all_active_alerts
│   │   │   ├── search_service.py      # Parallel multi-store search via asyncio.gather + relevance filtering
│   │   │   ├── relevance.py           # Search relevance scoring — filters out accessories/peripherals
│   │   │   ├── price_service.py       # Record prices, check triggers, cleanup
│   │   │   └── notification_service.py # send_push_alert, send_price_alert (Telegram + push)
│   │   ├── tasks/
│   │   │   ├── celery_app.py          # Celery config + beat schedule
│   │   │   ├── price_check.py         # check_all_alerts (runs every 4h), check_single_alert
│   │   │   └── cleanup.py             # Delete price_records older than 90 days (daily 3AM)
│   │   ├── main.py                    # FastAPI app, startup migrations + store seeding
│   │   └── requirements.txt
│   ├── frontend/
│   │   ├── src/app/
│   │   │   ├── layout.tsx             # Root layout, registers service worker, links manifest
│   │   │   ├── page.tsx               # Landing page + auth modal + product search + alert form
│   │   │   └── globals.css            # Full CSS (dark theme, auth modal, search, instructions)
│   │   ├── public/
│   │   │   ├── sw.js                  # Service worker (push event → showNotification)
│   │   │   └── manifest.json          # PWA manifest
│   │   ├── package.json
│   │   ├── next.config.js             # output: 'standalone'
│   │   └── tsconfig.json
│   └── shared/
│       └── constants.py               # StoreSlug enum, STORE_CONFIGS dict, DEFAULT_HEADERS
├── docker/
│   ├── backend.Dockerfile             # python:3.12-slim
│   ├── celery.Dockerfile              # Same base, no CMD (set by compose)
│   ├── frontend.Dockerfile            # node:20-alpine, npm run build
│   └── nginx.conf                     # Reverse proxy: /api/ → backend:8000, / → frontend:3000
├── tests/
├── docker-compose.yml                 # 7 services (bot disabled): backend, celery_worker, celery_beat, postgres, redis, frontend, nginx
├── .env.example
└── project_context.md                 # ← This file
```

## Database Schema (5 tables)

```
users
  id SERIAL PK
  telegram_id BIGINT UNIQUE (indexed, NULLABLE — web-only users have no telegram_id)
  email VARCHAR(255) UNIQUE (indexed, NULLABLE — Telegram-only users have no email)
  password_hash TEXT (NULLABLE — Telegram users don't have passwords)
  username VARCHAR(255)
  first_name VARCHAR(255)
  language_code VARCHAR(10) DEFAULT 'az'
  subscription_tier VARCHAR(20) DEFAULT 'free'
  max_alerts INTEGER DEFAULT 5
  is_active BOOLEAN DEFAULT true
  created_at TIMESTAMPTZ
  updated_at TIMESTAMPTZ

stores
  id SERIAL PK
  slug VARCHAR(50) UNIQUE NOT NULL        -- 'kontakt', 'baku_electronics', etc.
  name VARCHAR(255) NOT NULL              -- 'Kontakt Home', etc.
  base_url VARCHAR(500) NOT NULL
  search_url_template VARCHAR(500)
  is_active BOOLEAN DEFAULT true
  scraper_class VARCHAR(100) NOT NULL     -- 'KontaktScraper', etc.
  created_at TIMESTAMPTZ

alerts
  id SERIAL PK
  user_id INTEGER FK→users(id) CASCADE    -- NULLABLE (push-only alerts have no user)
  push_subscription_id INTEGER FK→push_subscriptions(id) SET NULL  -- NULLABLE
  search_query VARCHAR(500) NOT NULL
  target_price NUMERIC(10,2) NOT NULL     -- AZN
  store_slugs TEXT[] NOT NULL             -- ['kontakt', 'irshad']
  is_active BOOLEAN DEFAULT true
  is_triggered BOOLEAN DEFAULT false
  triggered_at TIMESTAMPTZ
  last_checked_at TIMESTAMPTZ
  lowest_price_found NUMERIC(10,2)
  lowest_price_store VARCHAR(50)
  lowest_price_url TEXT
  created_at TIMESTAMPTZ
  updated_at TIMESTAMPTZ
  INDEXES: idx_alerts_user_id, idx_alerts_active (partial WHERE is_active=true)

price_records
  id SERIAL PK
  alert_id INTEGER FK→alerts(id) CASCADE
  store_slug VARCHAR(50) NOT NULL
  product_name VARCHAR(1000)
  price NUMERIC(10,2) NOT NULL
  product_url TEXT
  scraped_at TIMESTAMPTZ
  INDEXES: idx_price_records_alert_id, idx_price_records_scraped_at

push_subscriptions
  id SERIAL PK
  user_id INTEGER FK→users(id) CASCADE    -- NULLABLE (anonymous subscribers OK)
  endpoint TEXT UNIQUE NOT NULL            -- Browser push endpoint URL
  p256dh TEXT NOT NULL                    -- Public key from browser
  auth TEXT NOT NULL                      -- Auth secret from browser
  is_active BOOLEAN DEFAULT true
  created_at TIMESTAMPTZ
  INDEXES: idx_push_subs_user_id, idx_push_subs_active (partial WHERE is_active=true)
```

## API Endpoints

```
GET  /api/v1/health                → {"status": "ok"}
GET  /api/v1/search?q=<query>     → SearchResponse (rate limited: 10/min per IP)

# Auth
POST /api/v1/auth/register         → AuthResponse (201) — {email, password, first_name?}
POST /api/v1/auth/login            → AuthResponse — {email, password}
GET  /api/v1/auth/me               → UserProfile (requires Bearer token)

# Alerts
GET  /api/v1/alerts/me             → list[AlertResponse] (requires Bearer token)
GET  /api/v1/alerts/{telegram_id}  → list[AlertResponse]
POST /api/v1/alerts                → AlertResponse (201) — supports JWT, telegram_id, or push_endpoint
POST /api/v1/alerts/by-push        → list[AlertResponse] — {endpoint}
POST /api/v1/alerts/{alert_id}/check → {"status": "checking"} — trigger manual price check
DELETE /api/v1/alerts/{alert_id}?telegram_id=<id> → {"status": "deleted"} — supports JWT auth

# Products
GET  /api/v1/prices/{alert_id}    → PriceHistoryResponse (last 100 records)
GET  /api/v1/stores               → list[{slug, name, base_url}]

# Push
GET  /api/v1/push/vapid-key       → {"public_key": "..."}
POST /api/v1/push/subscribe       → PushSubscriptionResponse (201) — {endpoint, keys, user_id?}
POST /api/v1/push/unsubscribe     → {"status": "unsubscribed"} — {endpoint}
```

## Key Flows

### 1. User Registers & Creates Alert via Web (Authenticated)
1. User visits `localhost:3000` (or `ucuzbot.az`)
2. Clicks "Login" → registers with email/password
3. Frontend stores JWT in localStorage, validates via `GET /api/v1/auth/me`
4. User fills alert form (product name, target price, stores)
5. Frontend calls `POST /api/v1/alerts` with `Authorization: Bearer <token>` — no push needed
6. Alerts fetched via `GET /api/v1/alerts/me`

### 2. User Creates Alert via Browser (Push-only, No Account)
1. User visits `localhost:3000` (or `ucuzbot.az`)
2. Clicks "Enable Notifications" → browser permission prompt
3. Frontend calls `GET /api/v1/push/vapid-key` → gets VAPID public key
4. Frontend calls `pushManager.subscribe()` → gets PushSubscription object
5. Frontend calls `POST /api/v1/push/subscribe` with endpoint + keys → stored in DB
6. User fills alert form (product name, target price, stores)
7. Frontend calls `POST /api/v1/alerts` with `push_endpoint` → alert created

### 3. Price Check Cycle (Celery Beat — every 4 hours)
1. `check_all_alerts` task fetches all active, non-triggered alerts
2. For each alert: scrape selected stores in parallel via `search_stores_for_alert()`
3. Record prices in `price_records` table, update alert's `lowest_price_*` fields
4. If `lowest_price <= target_price`: mark triggered + send push notification via `pywebpush`
5. Push notification payload: `{title, body, url, icon}` → service worker shows native notification

### 4. Scraper Architecture
- All scrapers extend `BaseScraper` ABC and implement `search(query, max_results) → list[ScrapedProduct]`
- `ScraperRegistry` auto-discovers scraper modules via `pkgutil`
- Scrapers use `@scraper_registry.register` decorator
- Built-in retry (3x exponential backoff) and rate limiting between requests
- `ScrapedProduct` dataclass: `{product_name, price (Decimal), product_url, store_slug, store_name, image_url?, in_stock}`

### 5. Search Relevance Filtering (`services/relevance.py`)
After scraping, results pass through a relevance filter before being returned:
- **Query-word match ratio** — what fraction of query words appear in the product name
- **Accessory penalty** — if product contains accessory words (case, cover, protector, cable, etc.) but the query does NOT, score is multiplied by 0.1
- **"For" penalty** — if product says "for" (indicating it's FOR the product, not the product itself), score is multiplied by 0.2
- Products scoring below 0.25 are filtered out
- Both user-facing search and alert price checking benefit (both use `search_all_stores()`)
- Prevents alerts from triggering on irrelevant accessories (e.g., a $9.99 case for a phone alert)

### 6. Telegram Bot UX (Button-Driven, No Commands Required)
- **Fallback handler**: Any plain text with no active FSM state is auto-searched as a product query
- **SearchFlow FSM**: "Search" button enters `waiting_for_query` state, next text triggers search
- **Cancel buttons**: All `/cancel` text replaced with inline cancel buttons (`action:cancel` callback)
- **Contextual follow-ups**: Every response includes next-action buttons (create alert, search again, menu)
- **Welcome flow**: `/start` shows personalized greeting + guided onboarding with action buttons
- **Keyboards**: 15 keyboard functions in `keyboards.py` — main menu, cancel, no-results, no-alerts, after-delete, after-search, price-drop, etc.

## Supported Stores (6)

| Slug | Name | Scraper |
|------|------|---------|
| `kontakt` | Kontakt Home | KontaktScraper (Magento API + HTML) |
| `baku_electronics` | Baku Electronics | BakuElectronicsScraper |
| `irshad` | Irshad | IrshadScraper |
| `maxi` | Maxi.az | MaxiScraper |
| `tap_az` | Tap.az | TapAzScraper |
| `umico` | Umico | UmicoScraper |

## Environment Variables (.env)

```
# Database
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=az_price_alert
POSTGRES_USER=app
POSTGRES_PASSWORD=changeme_in_production

# Redis
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2

# Scraping
SCRAPER_REQUEST_DELAY=2
SCRAPER_TIMEOUT=15

# App
APP_ENV=production
LOG_LEVEL=INFO
API_HOST=0.0.0.0
API_PORT=8000

# Alert limits
FREE_TIER_MAX_ALERTS=5
PRICE_CHECK_INTERVAL_HOURS=4

# JWT Auth
JWT_SECRET_KEY=change-me-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=72

# Web Push (VAPID) — generate keys with: vapid --gen
VAPID_PUBLIC_KEY=<base64url-encoded>
VAPID_PRIVATE_KEY=<base64url-encoded>
VAPID_CLAIMS_EMAIL=mailto:admin@ucuzbot.az

# Telegram (DISABLED — commented out in code)
TELEGRAM_BOT_TOKEN=
TELEGRAM_WEBHOOK_URL=
```

## Docker Services

```
docker compose up --build
```

| Service | Port | Description |
|---------|------|-------------|
| `backend` | 8000 | FastAPI API server |
| `celery_worker` | — | Processes price check + cleanup tasks |
| `celery_beat` | — | Schedules tasks (every 4h + daily 3AM) |
| `postgres` | 5432 | PostgreSQL 16 |
| `redis` | 6379 | Redis 7 (Celery broker + backend) |
| `frontend` | 3000 | Next.js SSR |
| `nginx` | 80 | Reverse proxy |
| `bot` | — | Telegram bot (button-driven UX, may need uncommenting in docker-compose) |

## Telegram Bot

The Telegram bot (`app/backend/bot/`) is fully implemented with a button-driven UX:
- **No commands required** — users interact entirely via buttons and typing product names
- **Smart fallback** — any plain text is treated as a product search (when no FSM is active)
- **FSM flows** — `SearchFlow` (search) and `AlertCreation` (alert creation with query → price → store selection)
- **Inline cancel buttons** — replaces all `/cancel` text references
- **Contextual keyboards** — every response includes relevant next-action buttons
- **Price drop notifications** — sent with inline "View my alerts" button

Docker status: `bot` service in `docker-compose.yml` may be commented out — uncomment to enable.

## Patterns & Conventions

- **Async everywhere**: All DB access, HTTP calls, and service functions are async
- **SQLAlchemy 2.0 style**: `Mapped[type]`, `mapped_column()`, `select()` queries
- **Soft deletes**: Alerts use `is_active = False` instead of hard delete
- **Structured logging**: `structlog` with `get_logger(__name__)`, key=value style
- **Error handling**: Custom exceptions in `core/exceptions.py`, caught in route handlers
- **Pydantic v2**: `model_config = {"from_attributes": True}` for ORM serialization
- **Prices**: Always `Decimal(10,2)` in AZN
- **Language**: Bilingual UI — Azerbaijani primary, English secondary
- **Celery tasks**: Wrap async functions with `asyncio.run()` since Celery is sync
- **DB sessions**: `async_session_factory()` for tasks, `Depends(get_db)` for routes
- **Search relevance**: All search results filtered through `relevance.filter_relevant()` before display/alerting
- **Bot UX**: Button-driven, no slash commands shown to users; FSM states for multi-step flows
- **Callback data**: Prefixed namespaces (`menu:`, `alert:`, `store:`, `search:alert:`, `action:`); query truncated to 40 chars to stay under 64-byte limit
- **Auth**: JWT Bearer tokens via `Authorization` header; bcrypt for password hashing; 72-hour token expiry

## Known Issues / TODOs

1. Need PWA icons (`public/icon-192.png`, `public/icon-512.png`) — referenced in manifest but not created
2. `pydantic==2.10.4` is pinned — if re-enabling `aiogram`, must downgrade to `2.9.x` (aiogram requires `<2.10`)
3. Relevance filter uses a static accessory word list — may need expansion as new product categories are added
4. Docker `bot` service may still be commented out in `docker-compose.yml` — uncomment to enable Telegram bot
5. No email verification for MVP — users can log in immediately after registration
6. `JWT_SECRET_KEY` must be changed from default in production
