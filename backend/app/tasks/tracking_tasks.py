"""
Celery Tasks for scheduled keyword tracking
"""
from celery import Celery
from celery.schedules import crontab
from app.core.config import settings
from app.core.database import SessionLocal
from app.models.models import Keyword, RankResult, Subscription, CreditTransaction, SubscriptionStatus
from app.services.tracker import google_tracker
from datetime import datetime, timedelta, timezone
import asyncio

# Initialize Celery
celery_app = Celery(
    "keyword_tracker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

celery_app.conf.update(
    timezone='UTC',
    enable_utc=True,
)

# Tracking intervals in hours
TRACKING_INTERVALS = {
    1: "每天1次",
    2: "2天1次",
    3: "3天1次",
    7: "7天1次",
}


@celery_app.task(name="track_keyword")
def track_keyword_task(keyword_id: int):
    """Track a single keyword"""
    db = SessionLocal()
    try:
        keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()
        if not keyword or not keyword.is_active:
            return {"status": "skipped", "reason": "inactive"}
        
        # Check user credits
        subscription = db.query(Subscription).filter(
            Subscription.user_id == keyword.project.user_id,
            Subscription.status == SubscriptionStatus.ACTIVE.value
        ).first()
        
        if not subscription or subscription.credits <= 0:
            return {"status": "skipped", "reason": "no_credits"}
        
        # Track keyword
        result = asyncio.run(google_tracker.track_keyword(
            keyword=keyword.keyword,
            country=keyword.country_code,
            language=keyword.language
        ))
        
        if not result:
            return {"status": "failed", "reason": "tracking_error"}
        
        # Calculate credits
        results = result.get("results", [])
        rank = None
        if results:
            # Find first result (position 1)
            rank = results[0].get("position", 1)
        
        credits_used = google_tracker.calculate_credits(rank) if rank else 1
        
        # Deduct credits
        subscription.credits -= credits_used
        
        # Save result
        first_result = results[0] if results else {}
        rank_result = RankResult(
            keyword_id=keyword_id,
            rank=rank,
            url=first_result.get("link"),
            title=first_result.get("title"),
            snippet=first_result.get("snippet"),
            credits_used=credits_used
        )
        db.add(rank_result)
        
        # Record transaction
        transaction = CreditTransaction(
            user_id=keyword.project.user_id,
            amount=-credits_used,
            transaction_type="consume",
            description=f"Auto-track: {keyword.keyword}"
        )
        db.add(transaction)
        db.commit()
        
        return {"status": "success", "rank": rank, "credits_used": credits_used}
        
    except Exception as e:
        db.rollback()
        return {"status": "error", "error": str(e)}
    finally:
        db.close()


@celery_app.task(name="process_all_keywords")
def process_all_keywords_task():
    """Process all due keywords based on their tracking interval"""
    
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        
        # Get all active keywords
        keywords = db.query(Keyword).filter(
            Keyword.is_active == True
        ).all()
        
        due_keywords = []
        
        for kw in keywords:
            interval = kw.tracking_interval_hours or 24  # Default to 24 hours
            
            if kw.results:
                # Get last result
                last_result = kw.results[0]
                if last_result.checked_at:
                    next_check = last_result.checked_at + timedelta(hours=interval)
                    if now >= next_check:
                        due_keywords.append(kw.id)
            else:
                # Never tracked, track now
                due_keywords.append(kw.id)
        
        # Dispatch tasks
        for keyword_id in due_keywords:
            track_keyword_task.delay(keyword_id)
        
        return {"status": "success", "due_count": len(due_keywords)}
        
    finally:
        db.close()


@celery_app.task(name="cleanup_old_results")
def cleanup_old_results_task():
    """Clean up old rank results (default: keep 365 days, configurable)"""
    
    db = SessionLocal()
    try:
        # Get retention days from settings (default 365)
        retention_days = getattr(settings, 'DATA_RETENTION_DAYS', 365)
        
        if retention_days <= 0:
            # 0 means keep forever
            return {"status": "skipped", "reason": "retention disabled"}
        
        cutoff = datetime.utcnow() - timedelta(days=retention_days)
        
        old_results = db.query(RankResult).filter(
            RankResult.checked_at < cutoff
        ).delete()
        
        db.commit()
        
        return {"status": "success", "deleted": old_results, "retention_days": retention_days}
    finally:
        db.close()


# Celery Beat Schedule
# Run every hour to check for due keywords
celery_app.conf.beat_schedule = {
    'process-keywords-hourly': {
        'task': 'process_all_keywords',
        'schedule': crontab(minute=0),  # Every hour at :00
    },
    
    # Daily cleanup at 3 AM UTC
    'cleanup-old-results': {
        'task': 'cleanup_old_results',
        'schedule': crontab(hour=3, minute=0),
    },
}


# User settings for tracking intervals:
"""
In the Keyword model or Project settings, users can set:
- tracking_interval_hours: 1, 2, 3, or 7

Cost calculation examples:
- 100 keywords, daily (24h): 100 calls/day = 3,000/month
- 100 keywords, 2-day: 50 calls/day = 1,500/month  
- 100 keywords, 7-day: ~14 calls/day = 420/month

With Serper at ~$0.50/1000 calls:
- Daily: $1.50/month
- 2-day: $0.75/month
- 7-day: $0.21/month
"""
