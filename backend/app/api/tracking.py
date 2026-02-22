from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.models import User, Keyword, RankResult, Subscription, CreditTransaction, SubscriptionStatus
from app.services.tracker import google_tracker
from app.schemas.schemas import RankResultResponse

router = APIRouter(prefix="/tracking", tags=["Tracking"])


@router.post("/keywords/{keyword_id}/track", response_model=RankResultResponse)
async def track_keyword(
    keyword_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Manually trigger tracking for a keyword"""
    
    # Get keyword and check ownership
    keyword = db.query(Keyword).join(Keyword.project).filter(
        Keyword.id == keyword_id,
        Keyword.project.has(user_id=current_user.id)
    ).first()
    
    if not keyword:
        raise HTTPException(status_code=404, detail="Keyword not found")
    
    if not keyword.is_active:
        raise HTTPException(status_code=400, detail="Keyword is inactive")
    
    # Get project target URL
    project = keyword.project
    target_domain = project.subdomain or project.root_domain
    
    # Check credits
    subscription = db.query(Subscription).filter(
        Subscription.user_id == current_user.id,
        Subscription.status == SubscriptionStatus.ACTIVE.value
    ).first()
    
    if not subscription or subscription.credits <= 0:
        raise HTTPException(status_code=402, detail="Insufficient credits")
    
    # Track keyword
    result = await google_tracker.track_keyword(
        keyword=keyword.keyword,
        country=keyword.country_code,
        language=keyword.language
    )
    
    if not result:
        raise HTTPException(status_code=500, detail="Failed to track keyword")
    
    # Find rank for target domain
    rank = None
    url = None
    title = None
    snippet = None
    
    results = result.get("results", [])
    for idx, r in enumerate(results, 1):
        if target_domain and target_domain in r.get("domain", ""):
            rank = idx
            url = r.get("link")
            title = r.get("title")
            snippet = r.get("snippet")
            break
    
    # If no match, record first result
    if not rank and results:
        rank = 1
        url = results[0].get("link")
        title = results[0].get("title")
        snippet = results[0].get("snippet")
    
    # Calculate and deduct credits
    credits_used = google_tracker.calculate_credits(rank) if rank else 1
    
    # Deduct credits
    subscription.credits -= credits_used
    
    # Record transaction
    transaction = CreditTransaction(
        user_id=current_user.id,
        amount=-credits_used,
        transaction_type="consume",
        description=f"Tracked keyword: {keyword.keyword}"
    )
    db.add(transaction)
    
    # Save result
    rank_result = RankResult(
        keyword_id=keyword_id,
        rank=rank,
        url=url,
        title=title,
        snippet=snippet,
        credits_used=credits_used
    )
    db.add(rank_result)
    
    db.commit()
    db.refresh(rank_result)
    
    return rank_result
