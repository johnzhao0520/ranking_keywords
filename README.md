# KeywordTracker Pro

Professional Google keyword ranking tracking tool for SEO agencies and clients.

## Features

- 🔍 **Keyword Tracking** - Track keyword rankings across multiple Google domains
- 🌍 **Country Targeting** - Target any Google country (.com, .co.uk, .de, etc.)
- ⏱️ **Flexible Intervals** - Set tracking frequency (1h, 6h, 12h, 24h)
- 💰 **Credit System** - Pay only for what you use
- 📊 **Trend Analysis** - Visualize ranking changes over time
- 👥 **Team Collaboration** - Invite team members to projects

## Pricing

| Plan | Credits | Price | Best For |
|------|---------|--------|----------|
| Starter | 1,000 | ¥99/mo | 5-10 keywords |
| Pro | 5,000 | ¥399/mo | 20-50 keywords |
| Enterprise | 15,000 | ¥999/mo | Unlimited |

## Quick Start

1. Sign up for an account
2. Create a project
3. Add keywords to track
4. Watch your rankings

## Tech Stack

- **Backend**: FastAPI (Python)
- **Database**: PostgreSQL
- **Task Queue**: Celery + Redis
- **Frontend**: Next.js
- **Deployment**: Railway

## API

The API is available at `/api`. See the documentation for endpoints.

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload
```

## License

MIT
