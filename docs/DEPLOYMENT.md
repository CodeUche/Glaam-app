# GlamConnect Deployment Guide

## Prerequisites

- Docker and Docker Compose installed
- Domain name configured (e.g., glamconnect.com)
- SSL certificate (Let's Encrypt recommended)
- Cloudinary account for image storage
- SMTP email service (e.g., Gmail, SendGrid, Mailgun)

---

## Step 1: Server Setup

### Minimum Requirements
- **CPU:** 2 vCPUs
- **RAM:** 4 GB
- **Storage:** 20 GB SSD
- **OS:** Ubuntu 22.04 LTS

### Install Docker
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add user to docker group
sudo usermod -aG docker $USER
```

---

## Step 2: Clone and Configure

```bash
# Clone repository
git clone https://github.com/yourusername/glamconnect.git
cd glamconnect

# Create production environment file
cp backend/.env.example backend/.env
```

### Edit backend/.env
```bash
# Generate a secure secret key
python3 -c "import secrets; print(secrets.token_urlsafe(50))"

# Update .env with production values:
SECRET_KEY=<generated-key>
DEBUG=False
ALLOWED_HOSTS=api.glamconnect.com,glamconnect.com

# Database (match docker-compose.prod.yml)
DATABASE_URL=postgresql://glamconnect_user:STRONG_PASSWORD_HERE@db:5432/glamconnect

# Redis
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/1

# Email (example with SendGrid)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=your-sendgrid-api-key

# Cloudinary
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret

# Security
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

### Create .env for Docker Compose
```bash
# Create root .env for docker-compose.prod.yml
cat > .env << EOF
POSTGRES_DB=glamconnect
POSTGRES_USER=glamconnect_user
POSTGRES_PASSWORD=STRONG_PASSWORD_HERE
EOF
```

---

## Step 3: SSL Certificate Setup

### Option A: Let's Encrypt (Recommended)
```bash
# Install certbot
sudo apt install certbot -y

# Get certificate
sudo certbot certonly --standalone -d api.glamconnect.com

# Copy certificates
mkdir -p docker/nginx/ssl
sudo cp /etc/letsencrypt/live/api.glamconnect.com/fullchain.pem docker/nginx/ssl/
sudo cp /etc/letsencrypt/live/api.glamconnect.com/privkey.pem docker/nginx/ssl/
```

### Auto-Renewal
```bash
# Add to crontab
sudo crontab -e
# Add this line:
0 0 1 * * certbot renew --quiet && docker-compose -f docker-compose.prod.yml restart nginx
```

---

## Step 4: Build and Deploy

```bash
# Build Docker images
docker-compose -f docker-compose.prod.yml build

# Start services
docker-compose -f docker-compose.prod.yml up -d

# Wait for database to be ready, then run migrations
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate

# Collect static files
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput

# Create superuser
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

---

## Step 5: Verify Deployment

```bash
# Check all services are running
docker-compose -f docker-compose.prod.yml ps

# Check logs
docker-compose -f docker-compose.prod.yml logs web
docker-compose -f docker-compose.prod.yml logs celery_worker

# Test API
curl https://api.glamconnect.com/api/v1/auth/login/
```

Expected: All containers running, API responds with 405 (method not allowed) or 200.

---

## Step 6: Frontend Deployment

### Next.js (Vercel — Recommended)
```bash
cd frontend/web

# Install Vercel CLI
npm i -g vercel

# Deploy
vercel --prod
```

Set environment variables in Vercel dashboard:
- `NEXT_PUBLIC_API_URL=https://api.glamconnect.com`
- `NEXT_PUBLIC_WS_URL=wss://api.glamconnect.com`

### Next.js (Self-hosted with Docker)
```bash
cd frontend/web
docker build -t glamconnect-web .
docker run -d -p 3000:3000 --name glamconnect-web glamconnect-web
```

### React Native
```bash
cd frontend/mobile

# Android
npx react-native run-android --variant=release

# iOS
npx react-native run-ios --configuration Release

# Or build APK/IPA
cd android && ./gradlew assembleRelease
```

---

## Database Backup & Restore

### Backup
```bash
# Create backup
docker-compose -f docker-compose.prod.yml exec db pg_dump -U glamconnect_user glamconnect > backup_$(date +%Y%m%d_%H%M%S).sql

# Automated daily backup (add to crontab)
0 2 * * * cd /path/to/glamconnect && docker-compose -f docker-compose.prod.yml exec -T db pg_dump -U glamconnect_user glamconnect | gzip > /backups/glamconnect_$(date +\%Y\%m\%d).sql.gz
```

### Restore
```bash
cat backup.sql | docker-compose -f docker-compose.prod.yml exec -T db psql -U glamconnect_user glamconnect
```

---

## Monitoring & Maintenance

### View Logs
```bash
# All services
docker-compose -f docker-compose.prod.yml logs -f

# Specific service
docker-compose -f docker-compose.prod.yml logs -f web
docker-compose -f docker-compose.prod.yml logs -f celery_worker
```

### Restart Services
```bash
# Restart all
docker-compose -f docker-compose.prod.yml restart

# Restart specific service
docker-compose -f docker-compose.prod.yml restart web
```

### Update Deployment
```bash
git pull origin main
docker-compose -f docker-compose.prod.yml build web
docker-compose -f docker-compose.prod.yml up -d web
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate
```

### Health Check
```bash
# Check service health
curl -s https://api.glamconnect.com/health/ | head -1

# Check database
docker-compose -f docker-compose.prod.yml exec db pg_isready -U glamconnect_user

# Check Redis
docker-compose -f docker-compose.prod.yml exec redis redis-cli ping
```

---

## Security Checklist for Production

- [ ] `DEBUG=False` in production
- [ ] Strong `SECRET_KEY` generated
- [ ] `ALLOWED_HOSTS` configured
- [ ] SSL/HTTPS enabled
- [ ] Database password is strong and unique
- [ ] CORS origins restricted to your domains
- [ ] Rate limiting enabled
- [ ] Firewall configured (only ports 80, 443 open)
- [ ] Regular database backups scheduled
- [ ] Log rotation configured
- [ ] SSH key-based authentication (disable password auth)
- [ ] Docker images are pinned to specific versions

---

## Platform-Specific Deployment

### AWS (EC2 + RDS)
1. Launch EC2 instance (t3.medium or larger)
2. Create RDS PostgreSQL instance
3. Create ElastiCache Redis instance
4. Update `DATABASE_URL` and `REDIS_URL` in `.env`
5. Use ALB for load balancing and SSL termination
6. Use S3 for media storage (alternative to Cloudinary)

### Render
1. Create Web Service (Docker)
2. Create PostgreSQL database
3. Create Redis instance
4. Set environment variables in Render dashboard
5. Deploy from GitHub

### Railway
1. Create new project
2. Add PostgreSQL and Redis services
3. Connect GitHub repository
4. Set environment variables
5. Deploy
