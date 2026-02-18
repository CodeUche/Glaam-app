# GlamConnect Security Checklist

## Authentication & Authorization
- [x] JWT with short-lived access tokens (15 min)
- [x] Refresh token rotation
- [x] Token blacklisting on logout
- [x] Password hashing with Argon2 (primary) + bcrypt fallback
- [x] Password strength validation (min 8 chars, complexity rules)
- [x] Role-based access control (Client, Artist, Admin)
- [x] Object-level permissions on every view
- [x] Admin role cannot be self-assigned during registration
- [x] Soft delete prevents reuse of deactivated accounts

## Input Validation
- [x] Django REST Framework serializer validation on all inputs
- [x] File type validation for image uploads (JPEG, PNG, WebP only)
- [x] File size limits (5MB max)
- [x] Email format validation
- [x] Phone number format validation
- [x] Rating range enforcement (1-5)
- [x] Booking date validation (future dates only)
- [x] Price validation (non-negative)
- [x] Duration validation (15-480 minutes)

## SQL Injection Protection
- [x] Django ORM parameterized queries (no raw SQL)
- [x] Input sanitization via serializers
- [x] No string interpolation in queries

## XSS Protection
- [x] Django's auto-escaping in templates
- [x] Content-Type-Options: nosniff header
- [x] X-XSS-Protection header
- [x] JSON-only API responses (no HTML rendering)

## CSRF Protection
- [x] Django CSRF middleware enabled
- [x] SameSite cookie attribute
- [x] CSRF tokens for session-based requests

## Rate Limiting
- [x] Nginx-level rate limiting (10 req/s general, 5 req/min auth)
- [x] DRF throttling (100/hour anon, 1000/hour authenticated)
- [x] Stricter limits on auth endpoints (5/minute)
- [x] Upload endpoint limiting (10/minute)

## Secure Headers
- [x] Strict-Transport-Security (HSTS)
- [x] X-Frame-Options: DENY
- [x] X-Content-Type-Options: nosniff
- [x] Referrer-Policy: strict-origin-when-cross-origin
- [x] Permissions-Policy configured

## File Upload Security
- [x] Content-type validation
- [x] File size limits enforced
- [x] Images processed through Cloudinary (stripped of metadata)
- [x] No executable file uploads
- [x] Separate media storage from application code

## Infrastructure Security
- [x] HTTPS enforced in production
- [x] Database credentials in environment variables
- [x] Secret key in environment variables
- [x] Non-root Docker user in production
- [x] Health check endpoints
- [x] Logging and audit trail

## Audit & Monitoring
- [x] AuditLog model for tracking user actions
- [x] Request logging via Django middleware
- [x] Failed login attempt tracking
- [x] Rotating log files (10MB, 10 backups)

## Data Protection
- [x] Soft delete retains data for compliance
- [x] Passwords never returned in API responses
- [x] Sensitive fields marked as write_only in serializers
- [x] Password reset prevents email enumeration (always returns success)
- [x] Token expiration on password change
