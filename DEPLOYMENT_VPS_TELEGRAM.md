# UcuzBot — VPS Deployment (Telegram Bot + IP Access, No Domain)

This guide deploys UcuzBot on a VPS **without a domain name**. The Telegram bot is the primary user interface. You (admin) access the web dashboard via the VPS IP address over HTTP.

## Architecture

```
Users ──► Telegram Bot ──► Backend API ──► PostgreSQL
                                  │
Admin ──► http://YOUR_IP ──► Nginx ──► Frontend (Next.js)
                               └──► /api/ ──► Backend (FastAPI)
                                  │
                          Celery Worker ──► Redis
                          Celery Beat (scheduler)
```

## Prerequisites

- A VPS running **Ubuntu 22.04+** (or Debian 12+)
- **Root or sudo** access
- Minimum **2 GB RAM**, 1 vCPU, 20 GB disk
- A **Telegram Bot Token** from [@BotFather](https://t.me/BotFather)

## Quick Start

```bash
ssh root@YOUR_VPS_IP

# 1. Upload project (see Section 1)
# 2. First-time server setup
cd /opt/ucuzbot
chmod +x deploy.sh
./deploy.sh --setup

# 3. Log out and back in (docker group)
exit
ssh root@YOUR_VPS_IP

# 4. Configure environment
cd /opt/ucuzbot
cp .env.example .env
nano .env    # See Section 3 for what to fill

# 5. Deploy with Telegram bot
./deploy.sh --with-telegram
```

Done. Bot is live at your Telegram bot link. Web is at `http://YOUR_VPS_IP`.

---

## 1. Upload the Project

### Option A: Git clone

```bash
cd /opt
sudo mkdir ucuzbot && sudo chown $USER:$USER ucuzbot
git clone YOUR_REPO_URL ucuzbot
cd ucuzbot
```

### Option B: SCP from local machine (Windows)

```bash
scp -r D:\ucuzbot\* root@YOUR_VPS_IP:/opt/ucuzbot/
```

## 2. First-Time Server Setup

```bash
cd /opt/ucuzbot
chmod +x deploy.sh
./deploy.sh --setup
```

This installs Docker, configures UFW firewall (opens ports 22, 80), and creates required directories.

> **Important:** Log out and back in after setup so the docker group takes effect.

## 3. Configure Environment Variables

```bash
cd /opt/ucuzbot
cp .env.example .env
nano .env
```

### Generate secrets

```bash
# Database password
openssl rand -hex 16

# JWT secret
openssl rand -hex 32
```

### Fill in `.env`

```env
# ===== TELEGRAM (REQUIRED) =====
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz    # From @BotFather
TELEGRAM_WEBHOOK_URL=                                        # Leave empty — bot uses polling

# ===== DATABASE =====
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=az_price_alert
POSTGRES_USER=app
POSTGRES_PASSWORD=<paste-generated-password>    # CHANGE THIS

# ===== REDIS =====
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2

# ===== SCRAPING =====
SCRAPER_REQUEST_DELAY=2
SCRAPER_TIMEOUT=15
SCRAPER_USER_AGENT=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36

# ===== APP =====
APP_ENV=production
LOG_LEVEL=INFO
API_HOST=0.0.0.0
API_PORT=8000

# ===== ALERT LIMITS =====
FREE_TIER_MAX_ALERTS=5
PREMIUM_TIER_MAX_ALERTS=50
PRICE_CHECK_INTERVAL_HOURS=4

# ===== JWT AUTH (for web dashboard) =====
JWT_SECRET_KEY=<paste-generated-jwt-secret>     # CHANGE THIS
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=72

# ===== WEB PUSH (OPTIONAL — skip if Telegram-only) =====
VAPID_PUBLIC_KEY=
VAPID_PRIVATE_KEY=
VAPID_CLAIMS_EMAIL=mailto:admin@ucuzbot.az
```

**Minimum required changes:**
1. `TELEGRAM_BOT_TOKEN` — your bot token from BotFather
2. `POSTGRES_PASSWORD` — generated password
3. `JWT_SECRET_KEY` — generated secret

VAPID keys are optional. Without them, browser push notifications won't work, but the Telegram bot and web dashboard work fine.

## 4. Update Nginx Config (IP-based, No Domain)

Replace the `server_name` directive to accept any hostname/IP:

```bash
nano docker/nginx.conf
```

Change `server_name ucuzbot.az www.ucuzbot.az;` to:

```nginx
server_name _;
```

Full file should look like:

```nginx
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server backend:8000;
    }

    upstream frontend {
        server frontend:3000;
    }

    server {
        listen 80;
        server_name _;

        location /api/ {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_read_timeout 120s;
            proxy_connect_timeout 10s;
            proxy_send_timeout 120s;
        }

        location / {
            proxy_pass http://frontend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
```

## 5. Deploy

```bash
cd /opt/ucuzbot
./deploy.sh --with-telegram
```

The `--with-telegram` flag is **required** — it enables the bot service.

The script will:
1. Validate `.env` (warns about default passwords)
2. Pull base images (postgres, redis, nginx)
3. Build application images (backend, frontend, celery, bot)
4. Start all services
5. Run health checks

### Verify deployment

```bash
# All services should show "Up"
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps

# Check bot logs
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f bot

# Check API health
curl http://localhost/api/v1/health
# Expected: {"status":"ok"}
```

Then open `http://YOUR_VPS_IP` in your browser — you should see the web dashboard.

Send `/start` to your Telegram bot — it should respond with the welcome message.

## 6. Set Up Telegram Bot with BotFather

Before deploying, configure your bot via [@BotFather](https://t.me/BotFather):

1. `/newbot` — create bot, get the token
2. `/setdescription` — set: `UcuzaTap - Azərbaycan mağazalarında qiymət izləmə botu`
3. `/setabouttext` — set: `Qiymət düşəndə bildiriş alın! 🔔`
4. `/setcommands` — set:
   ```
   start - Başla
   search - Məhsul axtar
   alert - Yeni bildiriş yarat
   myalerts - Bildirişlərimə bax
   help - Kömək
   ```

> Note: The bot is button-driven, so users don't need to type commands. But setting them helps with Telegram's command menu.

## 7. Update Deployment (After Code Changes)

```bash
cd /opt/ucuzbot
git pull origin main
./deploy.sh --with-telegram
```

Database data is preserved across deploys (Docker volumes). Migrations run automatically on backend startup.

## 8. Maintenance

Set up an alias for convenience:

```bash
echo 'alias dc="docker compose -f docker-compose.yml -f docker-compose.prod.yml"' >> ~/.bashrc
source ~/.bashrc
```

### Common commands

```bash
# View logs
dc logs -f                  # All services
dc logs -f bot              # Telegram bot only
dc logs -f backend          # API server
dc logs -f celery_worker    # Task worker

# Restart a service
dc restart bot
dc restart backend

# Service status
dc ps

# Database backup
dc exec postgres pg_dump -U app az_price_alert > backup_$(date +%Y%m%d_%H%M%S).sql

# Database restore
dc exec -T postgres psql -U app az_price_alert < backup.sql

# Database shell
dc exec postgres psql -U app az_price_alert

# Clear Redis cache
dc exec redis redis-cli FLUSHALL

# Stop everything
dc down

# Clean up unused Docker resources
docker system prune -f
```

### Automated database backups (recommended)

```bash
# Create backup directory
mkdir -p /opt/ucuzbot/backups

# Add daily backup cron (runs at 2 AM)
(crontab -l 2>/dev/null; echo "0 2 * * * cd /opt/ucuzbot && docker compose -f docker-compose.yml -f docker-compose.prod.yml exec -T postgres pg_dump -U app az_price_alert > backups/backup_\$(date +\%Y\%m\%d).sql && find backups/ -mtime +7 -delete") | crontab -
```

This keeps the last 7 days of backups.

## 9. Troubleshooting

| Problem | Diagnosis | Fix |
|---------|-----------|-----|
| Bot doesn't respond | `dc logs bot` | Check `TELEGRAM_BOT_TOKEN` in `.env` |
| Bot "conflict" error | Another instance running | Stop any other bot instances using the same token |
| Backend won't start | `dc logs backend` | Check DB credentials in `.env` |
| Celery not running tasks | `dc logs celery_worker` | Check Redis connection, `dc restart celery_worker` |
| Frontend 502 | `dc logs frontend` | Check if `npm run build` succeeded |
| Can't reach web via IP | `ufw status` | Ensure port 80 is open: `sudo ufw allow 80/tcp` |
| API health returns error | `curl http://localhost:8000/api/v1/health` | Check backend logs |

### Resource monitoring

```bash
docker stats              # Container CPU/memory usage
df -h                     # Disk space
docker system df          # Docker disk usage
```

## 10. Security Notes

Since there's no SSL (HTTP only), keep in mind:

- **Telegram bot traffic is secure** — Telegram handles encryption between users and your bot via their servers. The bot uses polling (not webhooks), so no inbound HTTP needed for Telegram.
- **Web dashboard over HTTP is unencrypted** — fine for admin access, but don't share the IP publicly for user registration. If you later want HTTPS, get a domain and follow the main `DEPLOYMENT.md`.
- PostgreSQL and Redis are only accessible from within Docker (localhost-bound in prod).

### Checklist

- [ ] Changed `POSTGRES_PASSWORD` from default
- [ ] Changed `JWT_SECRET_KEY` from default
- [ ] Set `TELEGRAM_BOT_TOKEN`
- [ ] Firewall enabled (`./deploy.sh --setup`)
- [ ] `.env` file not committed to git
- [ ] Database backups scheduled

## 11. Adding a Domain Later

If you later get a domain and want HTTPS:

1. Point your domain's DNS A record to your VPS IP
2. Update `docker/nginx.conf` — change `server_name _` to `server_name yourdomain.com`
3. Follow sections 4.1 and 4.2 in the main `DEPLOYMENT.md` for SSL setup
4. Run `./deploy.sh --ssl yourdomain.com --with-telegram`
