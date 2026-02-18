#!/bin/bash
# GlamConnect Development Setup Script

set -e

echo "========================================="
echo "  GlamConnect Development Setup"
echo "========================================="
echo ""

# Check prerequisites
command -v docker >/dev/null 2>&1 || { echo "Docker is required but not installed. Aborting."; exit 1; }
command -v docker-compose >/dev/null 2>&1 || command -v docker compose >/dev/null 2>&1 || { echo "Docker Compose is required but not installed. Aborting."; exit 1; }

# Navigate to project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

echo "[1/6] Setting up environment files..."
if [ ! -f backend/.env ]; then
    cp backend/.env.example backend/.env
    # Generate a random secret key
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(50))" 2>/dev/null || echo "dev-secret-key-$(date +%s)")
    sed -i "s/your-secret-key-here-change-in-production/$SECRET_KEY/" backend/.env 2>/dev/null || true
    echo "  Created backend/.env"
else
    echo "  backend/.env already exists, skipping"
fi

echo ""
echo "[2/6] Starting Docker services..."
docker-compose up -d db redis
echo "  Waiting for PostgreSQL to be ready..."
sleep 5

echo ""
echo "[3/6] Building and starting web service..."
docker-compose up -d --build web

echo ""
echo "[4/6] Running database migrations..."
docker-compose exec web python manage.py migrate

echo ""
echo "[5/6] Collecting static files..."
docker-compose exec web python manage.py collectstatic --noinput

echo ""
echo "[6/6] Starting all services..."
docker-compose up -d

echo ""
echo "========================================="
echo "  Setup Complete!"
echo "========================================="
echo ""
echo "  API:    http://localhost:8000"
echo "  Admin:  http://localhost:8000/admin"
echo "  Nginx:  http://localhost:80"
echo ""
echo "  To create a superuser:"
echo "    docker-compose exec web python manage.py createsuperuser"
echo ""
echo "  To view logs:"
echo "    docker-compose logs -f web"
echo ""
echo "  To stop services:"
echo "    docker-compose down"
echo ""
