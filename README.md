# UcuzaTap - Azerbaijan Price Tracker

Azərbaycan mağazalarında qiymətləri izləyin və ən ucuz qiyməti tapın.

Track prices across Azerbaijan stores and get notified when prices drop.

## Features

- **Price Alerts** — set a target price (e.g. "iPhone 15 under 1500 AZN") and get notified when it drops
- **5 Store Scrapers** — Kontakt, Baku Electronics, Irshad, Tap.az, Birmarket
- **Web App** — search products, create alerts, and manage them from the browser
- **Web Authentication** — email/password registration with JWT for cross-device alert sync
- **Browser Push Notifications** — get notified via Web Push API (VAPID) without an account
- **Telegram Bot** — fully button-driven UX, no commands required
- **Smart Relevance Filtering** — filters out accessories and irrelevant results from search and alerts
- **Scheduled Price Checks** — Celery Beat checks all active alerts every 4 hours

## Supported Stores

| Store | Website |
|-------|---------|
| Kontakt Home | kontakt.az |
| Baku Electronics | bakuelectronics.az |
| Irshad | irshad.az |
| Tap.az | tap.az |
| Birmarket | birmarket.az |

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend API | FastAPI 0.115.6, Python 3.12 |
| Database | PostgreSQL 16 (async via SQLAlchemy 2.0 + asyncpg) |
| Migrations | Alembic |
| Task Queue | Celery 5.4 + Redis 7 (broker + backend) |
| Scrapers | httpx + BeautifulSoup4 + lxml |
| Push Notifications | pywebpush 2.0 (Web Push API + VAPID) |
| Auth | bcrypt (password hashing) + PyJWT (JWT tokens) |
| Frontend | Next.js 14 + React 18 + TypeScript |
| Infra | Docker Compose, Nginx reverse proxy |
| Logging | structlog (JSON in prod, console in dev) |

## Quick Start

1. Copy `.env.example` to `.env` and fill in your values:
```bash
cp .env.example .env
```

2. Generate VAPID keys for push notifications:
```bash
pip install py-vapid
vapid --gen
```

3. Update `.env` with the generated VAPID keys and set a secure `JWT_SECRET_KEY`.

4. Start all services:
```bash
docker compose up --build
```

5. The system will:
   - Start PostgreSQL and Redis
   - Run database migrations automatically
   - Seed store records into the database
   - Start the FastAPI backend at `http://localhost:8000`
   - Start Celery worker and beat scheduler
   - Start the Next.js frontend at `http://localhost:3000`
   - Start Nginx reverse proxy at `http://localhost:80`

## Architecture

```
Browser (Next.js PWA)
     |
Nginx (:80) ─── reverse proxy
     |                |
     |          Frontend (:3000)
     |
FastAPI Backend (:8000) ──── PostgreSQL 16
     |                            |
     ├── Auth (JWT + bcrypt)  Alembic migrations
     ├── Push (VAPID/pywebpush)
     └── Scrapers (6 stores)
              |
         Celery Worker ──── Redis 7
              |
         Celery Beat (every 4h + daily cleanup)
              |
         Telegram Bot (button-driven UX)
```

## Docker Services

| Service | Port | Description |
|---------|------|-------------|
| `backend` | 8000 | FastAPI API server |
| `celery_worker` | — | Processes price check + cleanup tasks |
| `celery_beat` | — | Schedules tasks (every 4h + daily 3AM) |
| `postgres` | 5432 | PostgreSQL 16 |
| `redis` | 6379 | Redis 7 (Celery broker + backend) |
| `frontend` | 3000 | Next.js SSR |
| `nginx` | 80 | Reverse proxy |
| `bot` | — | Telegram bot (may need uncommenting in docker-compose.yml) |

## API Endpoints

### Health
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/health` | Health check |

### Auth
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register with email/password |
| POST | `/api/v1/auth/login` | Login, returns JWT |
| GET | `/api/v1/auth/me` | Get current user profile (requires Bearer token) |

### Search
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/search?q=<query>` | Search products across all stores (rate limited: 10/min) |

### Alerts
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/alerts/me` | List alerts for authenticated user (requires Bearer token) |
| GET | `/api/v1/alerts/{telegram_id}` | List alerts by Telegram ID |
| POST | `/api/v1/alerts` | Create alert (supports JWT, telegram_id, or push_endpoint) |
| POST | `/api/v1/alerts/by-push` | List alerts by push endpoint |
| POST | `/api/v1/alerts/{alert_id}/check` | Trigger manual price check |
| DELETE | `/api/v1/alerts/{alert_id}` | Delete alert (supports JWT auth or telegram_id query param) |

### Products
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/prices/{alert_id}` | Price history (last 100 records) |
| GET | `/api/v1/stores` | List all stores |

### Push Notifications
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/push/vapid-key` | Get VAPID public key |
| POST | `/api/v1/push/subscribe` | Subscribe to push notifications |
| POST | `/api/v1/push/unsubscribe` | Unsubscribe from push notifications |

## Telegram Bot

The Telegram bot (`app/backend/bot/`) is fully implemented with a button-driven UX:

- **No commands required** — users interact entirely via buttons and typing product names
- **Smart fallback** — any plain text is treated as a product search (when no FSM is active)
- **FSM flows** — `SearchFlow` (search) and `AlertCreation` (alert creation with query → price → store selection)
- **Inline cancel buttons** — replaces all `/cancel` text references
- **Contextual keyboards** — every response includes relevant next-action buttons
- **Price drop notifications** — sent with inline "View my alerts" button

To enable: uncomment the `bot` service in `docker-compose.yml` and set `TELEGRAM_BOT_TOKEN` in `.env`.

## Adding a New Store

1. Create `app/backend/scrapers/new_store.py`
2. Inherit from `BaseScraper` and use `@scraper_registry.register` decorator
3. Implement `search(query, max_results) → list[ScrapedProduct]`
4. Add store config to `app/shared/constants.py`
5. Add store record to DB (via migration or seed)

## Development

Run tests:
```bash
pip install pytest pytest-asyncio
pytest
```

## Environment Variables

See `.env.example` for all required variables. Key ones to configure:

| Variable | Description |
|----------|-------------|
| `POSTGRES_PASSWORD` | Database password |
| `JWT_SECRET_KEY` | Secret for JWT token signing (change in production) |
| `VAPID_PUBLIC_KEY` | Web Push VAPID public key |
| `VAPID_PRIVATE_KEY` | Web Push VAPID private key |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token (optional, for bot service) |

## License

Private project.

---

**ucuzbot.az**
