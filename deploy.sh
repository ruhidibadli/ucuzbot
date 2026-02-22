#!/bin/bash
set -e

# ============================================================
# UcuzBot — One-Command VPS Deployment Script
# Usage: ./deploy.sh [--with-telegram] [--setup] [--ssl DOMAIN]
# ============================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod.yml"
PROFILE=""
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

log()   { echo -e "${GREEN}[DEPLOY]${NC} $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# ----------------------------------------------------------
# Parse arguments
# ----------------------------------------------------------
SETUP=false
SSL_DOMAIN=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --with-telegram)
            PROFILE="--profile telegram"
            shift
            ;;
        --setup)
            SETUP=true
            shift
            ;;
        --ssl)
            SSL_DOMAIN="$2"
            shift 2
            ;;
        *)
            echo "Usage: $0 [--with-telegram] [--setup] [--ssl DOMAIN]"
            echo ""
            echo "  --setup           First-time server setup (install Docker, configure firewall)"
            echo "  --with-telegram   Also start the Telegram bot service"
            echo "  --ssl DOMAIN      Obtain SSL certificate for DOMAIN (e.g., ucuzbot.az)"
            exit 1
            ;;
    esac
done

cd "$PROJECT_DIR"

# ----------------------------------------------------------
# First-time setup (Docker, firewall, directories)
# ----------------------------------------------------------
if [ "$SETUP" = true ]; then
    log "Running first-time server setup..."

    # Install Docker if not present
    if ! command -v docker &> /dev/null; then
        log "Installing Docker..."
        sudo apt update
        sudo apt install -y ca-certificates curl gnupg lsb-release

        sudo install -m 0755 -d /etc/apt/keyrings
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
        sudo chmod a+r /etc/apt/keyrings/docker.gpg

        echo \
          "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
          $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
          sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

        sudo apt update
        sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
        sudo usermod -aG docker "$USER"
        log "Docker installed. You may need to log out and back in for group changes."
    else
        log "Docker already installed: $(docker --version)"
    fi

    # Configure firewall
    log "Configuring firewall..."
    sudo ufw allow OpenSSH
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    echo "y" | sudo ufw enable || true
    log "Firewall configured."

    # Create certbot directories
    mkdir -p certbot/conf certbot/www

    log "Server setup complete."
fi

# ----------------------------------------------------------
# Pre-flight checks
# ----------------------------------------------------------
log "Running pre-flight checks..."

# Check Docker is available
if ! command -v docker &> /dev/null; then
    error "Docker is not installed. Run: ./deploy.sh --setup"
fi

if ! docker compose version &> /dev/null; then
    error "Docker Compose plugin is not installed."
fi

# Check .env exists
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        warn ".env file not found. Creating from .env.example..."
        cp .env.example .env
        warn "IMPORTANT: Edit .env with production values before continuing!"
        warn "  nano .env"
        warn ""
        warn "At minimum, change:"
        warn "  - POSTGRES_PASSWORD"
        warn "  - JWT_SECRET_KEY"
        warn "  - VAPID_PUBLIC_KEY / VAPID_PRIVATE_KEY"
        exit 1
    else
        error ".env file not found and no .env.example available."
    fi
fi

# Validate critical env vars
source .env 2>/dev/null || true

if [ "$POSTGRES_PASSWORD" = "changeme_in_production" ] || [ -z "$POSTGRES_PASSWORD" ]; then
    warn "POSTGRES_PASSWORD is still the default! Change it in .env"
fi

if [ "$JWT_SECRET_KEY" = "change-me-in-production" ] || [ -z "$JWT_SECRET_KEY" ]; then
    warn "JWT_SECRET_KEY is still the default! Change it in .env"
fi

if [ -z "$VAPID_PUBLIC_KEY" ] || [ -z "$VAPID_PRIVATE_KEY" ]; then
    warn "VAPID keys are empty. Web push notifications will not work."
    warn "Generate keys: pip3 install py-vapid && vapid --gen"
fi

# Check docker-compose.prod.yml exists
if [ ! -f docker-compose.prod.yml ]; then
    error "docker-compose.prod.yml not found."
fi

log "Pre-flight checks passed."

# ----------------------------------------------------------
# SSL certificate (if requested)
# ----------------------------------------------------------
if [ -n "$SSL_DOMAIN" ]; then
    log "Obtaining SSL certificate for $SSL_DOMAIN..."

    mkdir -p certbot/conf certbot/www

    # Start nginx temporarily for ACME challenge
    docker compose $COMPOSE_FILES up -d nginx

    sleep 3

    docker compose $COMPOSE_FILES run --rm certbot \
        certonly --webroot --webroot-path=/var/www/certbot \
        -d "$SSL_DOMAIN" -d "www.$SSL_DOMAIN" \
        --email "admin@$SSL_DOMAIN" --agree-tos --no-eff-email

    docker compose $COMPOSE_FILES stop nginx

    log "SSL certificate obtained for $SSL_DOMAIN"

    # Set up auto-renewal cron
    CRON_CMD="0 3 * * * cd $PROJECT_DIR && docker compose $COMPOSE_FILES run --rm certbot renew && docker compose $COMPOSE_FILES restart nginx"
    (crontab -l 2>/dev/null | grep -v "certbot renew"; echo "$CRON_CMD") | crontab -
    log "SSL auto-renewal cron job added."
fi

# ----------------------------------------------------------
# Build and deploy
# ----------------------------------------------------------
log "Pulling latest base images..."
docker compose $COMPOSE_FILES pull postgres redis nginx 2>/dev/null || true

log "Building application images..."
docker compose $COMPOSE_FILES $PROFILE build

log "Stopping existing containers..."
docker compose $COMPOSE_FILES $PROFILE down --remove-orphans 2>/dev/null || true

log "Starting all services..."
docker compose $COMPOSE_FILES $PROFILE up -d

# ----------------------------------------------------------
# Health checks
# ----------------------------------------------------------
log "Waiting for services to start..."
sleep 10

log "Running health checks..."

# Check each service
SERVICES="postgres redis backend celery_worker celery_beat frontend nginx"
ALL_OK=true

for svc in $SERVICES; do
    STATUS=$(docker compose $COMPOSE_FILES ps --format '{{.Status}}' "$svc" 2>/dev/null || echo "not found")
    if echo "$STATUS" | grep -qi "up"; then
        log "  $svc: running"
    else
        warn "  $svc: $STATUS"
        ALL_OK=false
    fi
done

# Check API health
sleep 5
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/health 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ]; then
    log "  API health check: OK (200)"
else
    warn "  API health check: HTTP $HTTP_CODE (may still be starting)"
fi

# ----------------------------------------------------------
# Done
# ----------------------------------------------------------
echo ""
if [ "$ALL_OK" = true ]; then
    log "========================================"
    log "  Deployment successful!"
    log "========================================"
else
    warn "========================================"
    warn "  Deployment completed with warnings."
    warn "  Check logs: docker compose $COMPOSE_FILES logs -f"
    warn "========================================"
fi

echo ""
log "Useful commands:"
log "  View logs:     docker compose $COMPOSE_FILES logs -f"
log "  Stop:          docker compose $COMPOSE_FILES down"
log "  Restart:       docker compose $COMPOSE_FILES restart"
log "  DB backup:     docker compose $COMPOSE_FILES exec postgres pg_dump -U app az_price_alert > backup.sql"
log "  DB shell:      docker compose $COMPOSE_FILES exec postgres psql -U app az_price_alert"
echo ""
