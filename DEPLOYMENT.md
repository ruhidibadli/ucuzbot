# UcuzBot VPS Deployment Guide

All deployment steps use `deploy.sh`. See [deploy.sh flags](#deploysh-reference) for details.

## Prerequisites

- A VPS running **Ubuntu 22.04+** (or Debian 12+)
- **Root or sudo** access
- A domain name (e.g., `ucuzbot.az`) pointed to your VPS IP via DNS A record
- Minimum **2 GB RAM**, 1 vCPU, 20 GB disk

## Quick Start (TL;DR)

```bash
ssh root@YOUR_VPS_IP

# 1. Upload project to /opt/ucuzbot (see Section 2)
# 2. Configure environment
cp .env.example .env && nano .env

# 3. First-time: setup server + deploy + SSL — all in one
chmod +x deploy.sh
./deploy.sh --setup
./deploy.sh --ssl ucuzbot.az
./deploy.sh
```

That's it. Everything else below is explanation.

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
scp -r D:\ucuzbot\* deploy@YOUR_VPS_IP:/opt/ucuzbot/
```

## 2. Configure Environment Variables

```bash
cd /opt/ucuzbot
cp .env.example .env
nano .env
```

### Generate secrets

```bash
# Strong database password
openssl rand -hex 16

# Strong JWT secret
openssl rand -hex 32

# VAPID keys for web push
pip3 install py-vapid && vapid --gen
```

### Fill in `.env`

```env
# Database — MUST change password
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=az_price_alert
POSTGRES_USER=app
POSTGRES_PASSWORD=<generated-password>

# Redis
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2

# Scraping
SCRAPER_REQUEST_DELAY=2
SCRAPER_TIMEOUT=15
SCRAPER_USER_AGENT=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36

# App
APP_ENV=production
LOG_LEVEL=INFO
API_HOST=0.0.0.0
API_PORT=8000

# Alert limits
FREE_TIER_MAX_ALERTS=5
PREMIUM_TIER_MAX_ALERTS=50
PRICE_CHECK_INTERVAL_HOURS=4

# JWT Auth — MUST change secret
JWT_SECRET_KEY=<generated-jwt-secret>
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=72

# Web Push (VAPID)
VAPID_PUBLIC_KEY=<your-vapid-public-key>
VAPID_PRIVATE_KEY=<your-vapid-private-key>
VAPID_CLAIMS_EMAIL=mailto:admin@ucuzbot.az

# Telegram (leave empty to disable bot)
TELEGRAM_BOT_TOKEN=
TELEGRAM_WEBHOOK_URL=
```

## 3. First-Time Server Setup

Installs Docker, configures firewall (UFW), creates certbot directories:

```bash
chmod +x deploy.sh
./deploy.sh --setup
```

> After this finishes, **log out and back in** so the docker group takes effect.

## 4. SSL/HTTPS Setup

### 4.1 Update nginx config for SSL

Before obtaining the certificate, replace `docker/nginx.conf` with the SSL version:

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

    # Redirect HTTP to HTTPS
    server {
        listen 80;
        server_name ucuzbot.az www.ucuzbot.az;

        location /.well-known/acme-challenge/ {
            root /var/www/certbot;
        }

        location / {
            return 301 https://$host$request_uri;
        }
    }

    # HTTPS server
    server {
        listen 443 ssl;
        server_name ucuzbot.az www.ucuzbot.az;

        ssl_certificate /etc/letsencrypt/live/ucuzbot.az/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/ucuzbot.az/privkey.pem;

        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;
        ssl_prefer_server_ciphers on;

        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

        location /api/ {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_read_timeout 60s;
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

### 4.2 Obtain certificate

```bash
./deploy.sh --ssl ucuzbot.az
```

This will:
- Start nginx temporarily for the ACME challenge
- Obtain the certificate via Let's Encrypt
- Set up a daily cron job for auto-renewal

## 5. Deploy

```bash
# Standard deploy
./deploy.sh

# With Telegram bot
./deploy.sh --with-telegram
```

The script automatically:
1. Validates `.env` (warns about default passwords)
2. Pulls base images (postgres, redis, nginx)
3. Builds application images (backend, frontend, celery)
4. Stops old containers
5. Starts all services
6. Runs health checks and reports status

## 6. Update Deployment (After Code Changes)

```bash
cd /opt/ucuzbot
git pull origin main
./deploy.sh
```

Database data is preserved across deploys (Docker volumes). Migrations run automatically on backend startup.

## 7. deploy.sh Reference

| Command | What it does |
|---------|-------------|
| `./deploy.sh` | Build and deploy all services |
| `./deploy.sh --with-telegram` | Deploy including the Telegram bot |
| `./deploy.sh --setup` | First-time: install Docker, configure firewall |
| `./deploy.sh --ssl ucuzbot.az` | Obtain SSL cert + set up auto-renewal cron |
| `./deploy.sh --setup --ssl ucuzbot.az --with-telegram` | All flags can be combined |

## 8. Maintenance

All maintenance commands use the same compose setup. For convenience, set an alias:

```bash
echo 'alias dc="docker compose -f docker-compose.yml -f docker-compose.prod.yml"' >> ~/.bashrc
source ~/.bashrc
```

Then use `dc` instead of the full command:

```bash
# View logs
dc logs -f                  # all services
dc logs -f backend          # specific service

# Restart a service
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

## 9. Monitoring & Troubleshooting

### Common issues

| Problem | Diagnosis | Fix |
|---------|-----------|-----|
| Backend won't start | `dc logs backend` | Check `.env` values, especially DB credentials |
| Migrations fail | `dc logs backend \| grep migration` | Check DB connection |
| Celery not running tasks | `dc logs celery_worker` | Check Redis connection, `dc restart celery_worker` |
| Frontend 502 | `dc logs frontend` | Ensure `npm run build` succeeded in image |
| Push notifications fail | Check VAPID keys in `.env` | Regenerate with `vapid --gen` |
| SSL cert expired | Check certbot cron (`crontab -l`) | `dc run --rm certbot renew && dc restart nginx` |

### Resource monitoring

```bash
docker stats    # Container CPU/memory usage
df -h           # Disk space
docker system df # Docker disk usage
```

## 10. Security Checklist

- [ ] Changed `POSTGRES_PASSWORD` from default
- [ ] Changed `JWT_SECRET_KEY` from default
- [ ] Generated fresh VAPID keys
- [ ] SSL/HTTPS enabled (`./deploy.sh --ssl`)
- [ ] Firewall enabled (`./deploy.sh --setup`)
- [ ] PostgreSQL and Redis only accessible via localhost (handled by `docker-compose.prod.yml`)
- [ ] `.env` file not committed to git
- [ ] Database backups scheduled
