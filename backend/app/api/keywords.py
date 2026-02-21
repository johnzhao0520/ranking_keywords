from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.models import User, Keyword, RankResult, Project
from app.schemas.schemas import KeywordHistoryResponse, RankResultResponse

router = APIRouter(prefix="/keywords", tags=["Keywords"])


@router.get("/{keyword_id}/history", response_model=KeywordHistoryResponse)
def get_keyword_history(
    keyword_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get keyword ranking history with SERP results"""
    
    # Check ownership
    keyword = db.query(Keyword).join(Project).filter(
        Keyword.id == keyword_id,
        Project.user_id == current_user.id
    ).first()
    
    if not keyword:
        raise HTTPException(status_code=404, detail="Keyword not found")
    
    # Get history (last 30 records)
    results = db.query(RankResult).filter(
        RankResult.keyword_id == keyword_id
    ).order_by(RankResult.checked_at.desc()).limit(30).all()
    
    return KeywordHistoryResponse(
        keyword_id=keyword_id,
        keyword=keyword.keyword,
        history=results
    )
