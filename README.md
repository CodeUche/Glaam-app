# GlamConnect - Makeup Artist Marketplace

A production-ready platform connecting makeup artists with clients, built with Django, React Native, and Next.js.

## Features

- **For Clients:**
  - Browse and search makeup artists
  - View portfolios and reviews
  - Book appointments in real-time
  - Manage favorites
  - Leave ratings and reviews

- **For Makeup Artists:**
  - Professional profile management
  - Portfolio showcase
  - Service and pricing management
  - Booking management system
  - Availability calendar
  - Earnings dashboard

- **For Admins:**
  - User management
  - Content moderation
  - Platform analytics
  - Dispute resolution

## Tech Stack

### Backend
- Python 3.11+
- Django 5.0+
- Django REST Framework
- PostgreSQL 15
- Redis 7
- Celery
- Django Channels (WebSocket)

### Frontend
- **Web:** Next.js 14, TypeScript, TailwindCSS
- **Mobile:** React Native, TypeScript

### Infrastructure
- Docker & Docker Compose
- Nginx
- Gunicorn
- Cloudinary (Image storage)

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Node.js 18+ (for frontend development)
- Python 3.11+ (for local backend development)

### Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/glamconnect.git
   cd glamconnect
   ```

2. **Set up environment variables**
   ```bash
   cp backend/.env.example backend/.env
   cp frontend/web/.env.example frontend/web/.env.local
   ```

   Edit the `.env` files with your configuration.

3. **Start services with Docker**
   ```bash
   docker-compose up -d
   ```

4. **Run migrations**
   ```bash
   docker-compose exec web python manage.py migrate
   ```

5. **Create superuser**
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

6. **Access the application**
   - API: http://localhost:8000
   - Admin: http://localhost:8000/admin
   - Web App: http://localhost:3000
   - API Docs: http://localhost:8000/api/docs

### Local Development (without Docker)

#### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

#### Frontend (Web)
```bash
cd frontend/web
npm install
npm run dev
```

#### Frontend (Mobile)
```bash
cd frontend/mobile
npm install
npm run android  # or npm run ios
```

## Project Structure

```
glamconnect/
├── backend/                  # Django backend
│   ├── config/              # Django settings
│   ├── apps/                # Django apps
│   │   ├── users/          # Authentication & user management
│   │   ├── profiles/       # Client & artist profiles
│   │   ├── bookings/       # Booking system
│   │   ├── reviews/        # Reviews & ratings
│   │   ├── services/       # Service management
│   │   ├── notifications/  # Notification system
│   │   └── payments/       # Payment integration
│   ├── static/             # Static files
│   └── media/              # User uploads
├── frontend/
│   ├── web/                # Next.js web application
│   └── mobile/             # React Native mobile app
├── docker/                 # Docker configurations
├── docs/                   # Documentation
└── scripts/                # Utility scripts
```

## API Documentation

See [API_DOCUMENTATION.md](docs/API_DOCUMENTATION.md) for complete API reference.

### Key Endpoints

- `POST /api/v1/auth/register/` - User registration
- `POST /api/v1/auth/login/` - User login
- `GET /api/v1/artists/` - List artists
- `POST /api/v1/bookings/` - Create booking
- `POST /api/v1/reviews/` - Create review

## Testing

### Backend Tests
```bash
cd backend
python manage.py test
```

### Frontend Tests
```bash
cd frontend/web
npm run test
```

## Deployment

See [DEPLOYMENT.md](docs/DEPLOYMENT.md) for production deployment instructions.

### Quick Deploy with Docker

```bash
docker-compose -f docker-compose.prod.yml up -d
```

## Security

- JWT authentication with refresh tokens
- Role-based access control
- Rate limiting on all endpoints
- Input validation and sanitization
- SQL injection protection
- XSS protection
- CSRF protection
- Secure file upload validation

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For issues and questions:
- Create an issue on GitHub
- Email: support@glamconnect.com
- Documentation: https://docs.glamconnect.com

## Roadmap

See [ROADMAP.md](docs/ROADMAP.md) for future features and improvements.
