from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.models import User, Plan, Subscription, CreditTransaction, SubscriptionStatus
from app.schemas.schemas import (
    PlanResponse, SubscriptionCreate, SubscriptionResponse,
    CreditTransactionResponse, CreditPurchase, DashboardStats
)

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/credits", response_model=dict)
def get_credits(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    subscription = db.query(Subscription).filter(
        Subscription.user_id == current_user.id,
        Subscription.status == SubscriptionStatus.ACTIVE.value
    ).first()
    
    return {
        "credits": subscription.credits if subscription else 0
    }


@router.post("/credits/purchase", response_model=CreditTransactionResponse)
def purchase_credits(
    purchase: CreditPurchase,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Get plan
    plan = db.query(Plan).filter(
        Plan.id == purchase.plan_id,
        Plan.is_active == True
    ).first()
    
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan not found"
        )
    
    # Get or create subscription
    subscription = db.query(Subscription).filter(
        Subscription.user_id == current_user.id,
        Subscription.status == SubscriptionStatus.ACTIVE.value
    ).first()
    
    if not subscription:
        subscription = Subscription(
            user_id=current_user.id,
            plan_id=plan.id,
            credits=0,
            status=SubscriptionStatus.ACTIVE.value
        )
        db.add(subscription)
    
    # Add credits
    subscription.credits += plan.credits
    
    # Record transaction
    transaction = CreditTransaction(
        user_id=current_user.id,
        amount=plan.credits,
        transaction_type="purchase",
        description=f"Purchased {plan.name} plan"
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    
    return transaction


@router.get("/credits/transactions", response_model=list[CreditTransactionResponse])
def get_transactions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    transactions = db.query(CreditTransaction).filter(
        CreditTransaction.user_id == current_user.id
    ).order_by(CreditTransaction.created_at.desc()).limit(50).all()
    
    return transactions


@router.get("/dashboard", response_model=DashboardStats)
def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from app.models.models import Project, Keyword
    
    # Get user's projects
    projects = db.query(Project).filter(Project.user_id == current_user.id).all()
    project_ids = [p.id for p in projects]
    
    # Get keywords count
    keywords_count = db.query(Keyword).filter(
        Keyword.project_id.in_(project_ids)
    ).count() if project_ids else 0
    
    active_keywords = db.query(Keyword).filter(
        Keyword.project_id.in_(project_ids),
        Keyword.is_active == True
    ).count() if project_ids else 0
    
    # Get credits
    subscription = db.query(Subscription).filter(
        Subscription.user_id == current_user.id,
        Subscription.status == SubscriptionStatus.ACTIVE.value
    ).first()
    
    credits = subscription.credits if subscription else 0
    
    # Get credits used this month
    from datetime import datetime
    from calendar import monthrange
    from sqlalchemy import func
    
    today = datetime.now()
    _, last_day = monthrange(today.year, today.month)
    month_start = datetime(today.year, today.month, 1)
    month_end = datetime(today.year, today.month, last_day, 23, 59, 59)
    
    credits_used = db.query(func.sum(CreditTransaction.amount)).filter(
        CreditTransaction.user_id == current_user.id,
        CreditTransaction.transaction_type == "consume",
        CreditTransaction.created_at >= month_start,
        CreditTransaction.created_at <= month_end
    ).scalar() or 0
    
    return DashboardStats(
        total_projects=len(projects),
        total_keywords=keywords_count,
        active_keywords=active_keywords,
        credits_remaining=credits,
        credits_used_this_month=abs(credits_used)
    )


# ============ Admin: User Management ============
@router.post("/admin/add-credits")
def admin_add_credits(
    user_email: str,
    amount: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """管理员给用户添加积分"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")
    
    # 查找目标用户
    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 查找或创建订阅
    subscription = db.query(Subscription).filter(
        Subscription.user_id == user.id,
        Subscription.status == SubscriptionStatus.ACTIVE.value
    ).first()
    
    if subscription:
        subscription.credits += amount
    else:
        subscription = Subscription(
            user_id=user.id,
            plan_id=1,
            credits=amount,
            status=SubscriptionStatus.ACTIVE.value
        )
        db.add(subscription)
    
    # 记录交易
    transaction = CreditTransaction(
        user_id=user.id,
        amount=amount,
        transaction_type="purchase",
        description=f"Admin added credits: {current_user.email}"
    )
    db.add(transaction)
    db.commit()
    
    return {"message": f"Added {amount} credits to {user_email}", "new_balance": subscription.credits}


@router.get("/admin/users")
def admin_list_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """管理员查看所有用户"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")
    
    users = db.query(User).all()
    result = []
    for u in users:
        sub = db.query(Subscription).filter(
            Subscription.user_id == u.id,
            Subscription.status == SubscriptionStatus.ACTIVE.value
        ).first()
        result.append({
            "id": u.id,
            "email": u.email,
            "username": u.username,
            "credits": sub.credits if sub else 0,
            "role": u.role
        })
    return result
