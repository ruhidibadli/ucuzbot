# UcuzBot - Azerbaijan Price Tracker

Azərbaycan mağazalarında qiymətləri izləyin və ən ucuz qiyməti tapın.

Track prices across Azerbaijan stores and get notified when prices drop.

## Supported Stores

| Store | Website |
|-------|---------|
| Kontakt Home | kontakt.az |
| Baku Electronics | bakuelectronics.az |
| Irshad | irshad.az |
| Maxi.az | maxi.az |
| Tap.az | tap.az |
| Umico | umico.az |

## Quick Start

1. Copy `.env.example` to `.env` and fill in your values:
```bash
cp .env.example .env
```

2. Set your Telegram bot token in `.env`:
```
TELEGRAM_BOT_TOKEN=your_bot_token_here
```

3. Start all services:
```bash
docker-compose up --build
```

4. The system will:
   - Start PostgreSQL and Redis
   - Run database migrations automatically
   - Start the FastAPI backend at `http://localhost:8000`
   - Start the Telegram bot
   - Start Celery worker and beat scheduler
   - Start the frontend at `http://localhost:3000`

## Architecture

```
Telegram Bot (aiogram 3.x)
     |
FastAPI Backend ──── PostgreSQL 16
     |                    |
Scrapers (6 stores)  Alembic migrations
     |
Celery Worker ──── Redis 7
     |
Celery Beat (scheduler)
```

## Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Register and show welcome |
| `/search <query>` | Search products across stores |
| `/alert` | Create a price alert |
| `/myalerts` | View active alerts |
| `/delete <id>` | Delete an alert |
| `/help` | Show help |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/health` | Health check |
| GET | `/api/v1/search?q=<query>` | Search products |
| GET | `/api/v1/alerts/{telegram_id}` | List user alerts |
| POST | `/api/v1/alerts` | Create alert |
| DELETE | `/api/v1/alerts/{id}` | Delete alert |
| GET | `/api/v1/prices/{alert_id}` | Price history |
| GET | `/api/v1/stores` | List stores |

## Adding a New Store

1. Create `app/backend/scrapers/new_store.py`
2. Inherit from `BaseScraper`
3. Implement `search()` method
4. Add store config to `app/shared/constants.py`
5. Add store record to DB (via migration or seed)

## Tech Stack

- **Backend:** FastAPI, SQLAlchemy 2.x (async), Alembic
- **Bot:** aiogram 3.x
- **Task Queue:** Celery 5.x + Redis
- **Database:** PostgreSQL 16
- **Scraping:** httpx + BeautifulSoup4
- **Frontend:** Next.js (minimal)

## Development

Run tests:
```bash
pip install pytest pytest-asyncio
pytest
```

## License

Private project.

---

**ucuzbot.az**
