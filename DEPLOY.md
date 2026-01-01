# Production Deployment Guide

## Quick Deploy

1. **Setup Environment**
   ```bash
   cp .env.production .env
   # Edit .env with your credentials
   ```

2. **Deploy with Docker**
   ```bash
   docker-compose up -d --build
   ```

3. **Access Application**
   - Frontend: http://localhost
   - Backend API: http://localhost:8000

## Environment Variables

Required in `.env`:
- `DATABASE_URL` - PostgreSQL connection string
- `GROQ_API_KEY` - Groq API key
- `CLOUDINARY_CLOUD_NAME` - Cloudinary cloud name
- `CLOUDINARY_API_KEY` - Cloudinary API key
- `CLOUDINARY_API_SECRET` - Cloudinary API secret
- `SECRET_KEY` - Application secret key

## Production Checklist

- [ ] Configure production DATABASE_URL
- [ ] Set up SSL/HTTPS (add reverse proxy)
- [ ] Configure firewall rules
- [ ] Set up monitoring/logging
- [ ] Configure backup strategy

## Manual Build

### Backend
```bash
cd backend
docker build -t pdfreader-backend .
docker run -p 8000:8000 --env-file .env pdfreader-backend
```

### Frontend
```bash
cd frontend/frontapp
docker build -t pdfreader-frontend .
docker run -p 80:80 pdfreader-frontend
```