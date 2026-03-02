from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


# ============ User Schemas ============
class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(UserBase):
    id: int
    role: str
    is_active: bool
    is_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserWithCredits(UserResponse):
    credits: int = 0


# ============ Auth Schemas ============
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    user_id: Optional[int] = None


# ============ Plan Schemas ============
class PlanBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    credits: int
    duration_days: int


class PlanResponse(PlanBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ============ Subscription Schemas ============
class SubscriptionCreate(BaseModel):
    plan_id: int


class SubscriptionResponse(BaseModel):
    id: int
    plan_id: int
    credits: int
    start_date: datetime
    end_date: Optional[datetime]
    status: str

    class Config:
        from_attributes = True


# ============ Credit Transaction Schemas ============
class CreditTransactionResponse(BaseModel):
    id: int
    amount: int
    transaction_type: str
    description: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class CreditPurchase(BaseModel):
    plan_id: int


# ============ Project Schemas ============
class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    root_domain: str = Field(..., description="根域名，如 example.com")
    subdomain: Optional[str] = Field(None, description="二级域名，如 www.example.com")


class ProjectCreate(ProjectBase):
    notification_channels: Optional[List[str]] = []


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    root_domain: Optional[str] = None
    subdomain: Optional[str] = None
    notification_channels: Optional[List[str]] = None


class ProjectResponse(ProjectBase):
    id: int
    user_id: int
    notification_channels: List[str]
    created_at: datetime
    keywords_count: int = 0

    class Config:
        from_attributes = True


class ProjectMemberAdd(BaseModel):
    user_id: int
    role: str = "member"


# ============ Keyword Schemas ============
class KeywordBase(BaseModel):
    keyword: str = Field(..., min_length=1, max_length=500)
    country_code: str = "com"
    language: str = "en"
    tracking_interval_hours: int = Field(default=24, ge=-1, le=720)  # -1=每分钟, 最大30天


class KeywordCreate(KeywordBase):
    pass


class KeywordUpdate(BaseModel):
    keyword: Optional[str] = None
    country_code: Optional[str] = None
    language: Optional[str] = None
    tracking_interval_hours: Optional[int] = None
    is_active: Optional[bool] = None


class KeywordResponse(KeywordBase):
    id: int
    project_id: int
    is_active: bool
    created_at: datetime
    results_count: int = 0

    class Config:
        from_attributes = True


class KeywordWithResults(KeywordResponse):
    latest_rank: Optional[int] = None
    latest_url: Optional[str] = None


# ============ Rank Result Schemas ============
class RankResultResponse(BaseModel):
    id: int
    keyword_id: int
    rank: Optional[int]
    url: Optional[str]
    title: Optional[str]
    snippet: Optional[str]
    serp_results: Optional[str]  # JSON string of top 10 results
    credits_used: int
    checked_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class KeywordHistoryResponse(BaseModel):
    keyword_id: int
    keyword: str
    history: List[RankResultResponse]


class ManualTrackRequest(BaseModel):
    keyword_id: int


# ============ Dashboard Schemas ============
class DashboardStats(BaseModel):
    total_projects: int
    total_keywords: int
    active_keywords: int
    credits_remaining: int
    credits_used_this_month: int
