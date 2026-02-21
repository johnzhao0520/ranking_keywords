# Local Development Environment Setup

## Quick Start

```bash
# 1. Navigate to backend
cd backend

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create .env file
cp .env.example .env

# 5. Start services with Docker
docker-compose up -d postgres redis

# 6. Run migrations
alembic upgrade head

# 7. Start the server
uvicorn app.main:app --reload
```

## Environment Variables (.env)

```bash
# Required
SECRET_KEY=your-secret-key-here-change-in-production
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/keyword_tracker
REDIS_URL=redis://localhost:6379/0

# For local development, you can use SQLite
# DATABASE_URL=sqlite:///./dev.db

# Optional
SERPER_API_KEY=your-serper-api-key
STRIPE_API_KEY=sk_test_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx
```

## Testing the API

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test registration
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","username":"testuser","password":"testpass123"}'

# Test login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=testpass123"
```

## Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_auth.py -v

# Run with coverage
pytest --cov=app --cov-report=html
```

## Common Issues

### Database Connection Error
```bash
# Make sure PostgreSQL is running
docker-compose up -d postgres

# Check connection
psql -h localhost -U postgres -d keyword_tracker
```

### Port Already in Use
```bash
# Find and kill process on port 8000
lsof -i :8000
kill -9 <PID>
```

### Import Errors
```bash
# Make sure you're in the virtual environment
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```
