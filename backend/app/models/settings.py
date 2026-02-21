"""
Project Settings Model

User-configurable settings for data retention
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from enum import Enum


class DataRetention(str, Enum):
    KEEP_FOREVER = "keep_forever"
    RETAIN_90_DAYS = "90_days"
    RETAIN_180_DAYS = "180_days"
    RETAIN_365_DAYS = "365_days"
    RETAIN_2_YEARS = "2_years"


class ProjectSettings(Base):
    __tablename__ = "project_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), unique=True, nullable=False)
    
    # Data retention settings
    data_retention = Column(
        String(20), 
        default=DataRetention.RETAIN_365_DAYS.value
    )
    
    # Tracking preferences
    default_tracking_interval = Column(Integer, default=24)  # hours: 24, 48, 72, 168
    
    # Notification settings
    notify_on_rank_change = Column(Boolean, default=True)
    rank_change_threshold = Column(Integer, default=5)  # Notify if rank changes by more than X positions
    
    # Report settings
    daily_report = Column(Boolean, default=False)
    weekly_report = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    project = relationship("Project", backref="settings")


# Tracking interval options for UI
TRACKING_INTERVAL_OPTIONS = [
    {"value": 24, "label": "每天1次", "description": "每天 UTC 0:00 执行", "cost_per_100_keywords": "$1.50/月"},
    {"value": 48, "label": "2天1次", "description": "每2天执行一次", "cost_per_100_keywords": "$0.75/月"},
    {"value": 72, "label": "3天1次", "description": "每3天执行一次", "cost_per_100_keywords": "$0.50/月"},
    {"value": 168, "label": "7天1次", "description": "每周执行一次", "cost_per_100_keywords": "$0.21/月"},
]

# Data retention options for UI
DATA_RETENTION_OPTIONS = [
    {"value": DataRetention.KEEP_FOREVER.value, "label": "永久保留", "description": "不自动删除任何数据"},
    {"value": DataRetention.RETAIN_365_DAYS.value, "label": "保留1年", "description": "365天后自动删除"},
    {"value": DataRetention.RETAIN_2_YEARS.value, "label": "保留2年", "description": "730天后自动删除"},
]


# Usage in API:
"""
# Get project settings
settings = db.query(ProjectSettings).filter(
    ProjectSettings.project_id == project_id
).first()

if not settings:
    # Create default settings
    settings = ProjectSettings(project_id=project_id)
    db.add(settings)
    db.commit()

# Use settings for cleanup
if settings.data_retention == DataRetention.KEEP_FOREVER.value:
    # Never delete
    pass
elif settings.data_retention == DataRetention.RETAIN_365_DAYS.value:
    # Delete data older than 365 days
    cutoff = datetime.utcnow() - timedelta(days=365)
"""
