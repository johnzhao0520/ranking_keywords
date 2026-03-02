from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import logging
import os

from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.models import User, Keyword, RankResult, Subscription, CreditTransaction, SubscriptionStatus, ProjectMember
from app.services.tracker import google_tracker
from app.schemas.schemas import RankResultResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tracking", tags=["Tracking"])


@router.post("/process")
async def process_due_keywords():
    """定时任务：处理所有到期的关键词（供 Railway Cron 调用）"""
    from app.services.scheduler import process_due_keywords as run_scheduler

    try:
        result = await run_scheduler()
        return {"status": "success", "result": result}
    except Exception as e:
        logger.error(f"定时任务执行失败: {e}")
        return {"status": "error", "error": str(e)}


@router.post("/test-process")
async def test_process_keywords():
    """测试用：每分钟追踪所有活跃关键词（不计入积分）"""
    from app.services.scheduler import test_track_all_keywords as run_test

    if os.getenv("ENABLE_TEST_TRACKING_API", "false").lower() != "true":
        raise HTTPException(status_code=404, detail="Not found")

    try:
        result = await run_test()
        return {"status": "success", "result": result}
    except Exception as e:
        logger.error(f"测试追踪执行失败: {e}")
        return {"status": "error", "error": str(e)}


@router.post("/keywords/{keyword_id}/track", response_model=RankResultResponse)
async def track_keyword(
    keyword_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Manually trigger tracking for a keyword"""

    # Get keyword and check ownership or membership
    keyword = db.query(Keyword).join(Keyword.project).filter(
        Keyword.id == keyword_id
    ).first()

    if not keyword:
        raise HTTPException(status_code=404, detail="Keyword not found")

    # Check if user is owner or member
    project = keyword.project
    if project.user_id != current_user.id:
        member = db.query(ProjectMember).filter(
            ProjectMember.project_id == project.id,
            ProjectMember.user_id == current_user.id
        ).first()
        if not member:
            raise HTTPException(status_code=403, detail="Access denied")
    
    if not keyword.is_active:
        raise HTTPException(status_code=400, detail="Keyword is inactive")
    
    # Get project target URL
    project = keyword.project
    target_domain = project.subdomain or project.root_domain

    # Check credits - 积分从项目所有者账户扣除
    subscription = db.query(Subscription).filter(
        Subscription.user_id == project.user_id,
        Subscription.status == SubscriptionStatus.ACTIVE.value
    ).first()

    if not subscription or subscription.credits <= 0:
        raise HTTPException(status_code=402, detail="项目所有者积分不足")
    
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
    
    # 保存完整 SERP 结果（Top 10）
    import json
    serp_top10 = results[:10] if results else []
    serp_results_json = json.dumps(serp_top10)
    
    for idx, r in enumerate(results, 1):
        if target_domain and target_domain in r.get("domain", ""):
            rank = idx
            url = r.get("link")
            title = r.get("title")
            snippet = r.get("snippet")
            break
    
    # If no match, keyword is not in top 100
    if not rank:
        # 只记录追踪，但不记录具体排名
        pass
    
    # Calculate and deduct credits (always 1 credit per tracking)
    credits_used = 1
    
    # Deduct credits
    subscription.credits -= credits_used
    
    # Record transaction - 积分从项目所有者账户扣除
    transaction = CreditTransaction(
        user_id=project.user_id,
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
        serp_results=serp_results_json,
        credits_used=credits_used
    )
    db.add(rank_result)
    
    db.commit()
    db.refresh(rank_result)
    
    return rank_result
