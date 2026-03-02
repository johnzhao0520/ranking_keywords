from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.models import User, Project, Keyword, ProjectMember, RankResult
from app.schemas.schemas import (
    ProjectCreate, ProjectUpdate, ProjectResponse, ProjectMemberAdd,
    KeywordCreate, KeywordUpdate, KeywordResponse, KeywordWithResults,
    RankResultResponse
)

router = APIRouter(prefix="/projects", tags=["Projects"])


# ============ Projects ============
@router.get("", response_model=List[ProjectResponse])
def get_projects(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    projects = db.query(Project).filter(
        (Project.user_id == current_user.id) | 
        (Project.members.any(ProjectMember.user_id == current_user.id))
    ).all()
    
    result = []
    for p in projects:
        keywords_count = db.query(Keyword).filter(Keyword.project_id == p.id).count()
        result.append(ProjectResponse(
            id=p.id,
            user_id=p.user_id,
            name=p.name,
            description=p.description,
            root_domain=p.root_domain,
            subdomain=p.subdomain,
            notification_channels=p.notification_channels or [],
            created_at=p.created_at,
            keywords_count=keywords_count
        ))
    
    return result


@router.post("", response_model=ProjectResponse)
def create_project(
    project: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_project = Project(
        user_id=current_user.id,
        name=project.name,
        description=project.description,
        root_domain=project.root_domain,
        subdomain=project.subdomain,
        notification_channels=project.notification_channels or []
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    
    return ProjectResponse(
        id=db_project.id,
        user_id=db_project.user_id,
        name=db_project.name,
        description=db_project.description,
        root_domain=db_project.root_domain,
        subdomain=db_project.subdomain,
        notification_channels=db_project.notification_channels or [],
        created_at=db_project.created_at,
        keywords_count=0
    )


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check access
    if project.user_id != current_user.id:
        member = db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == current_user.id
        ).first()
        if not member:
            raise HTTPException(status_code=403, detail="Access denied")
    
    keywords_count = db.query(Keyword).filter(Keyword.project_id == project.id).count()
    
    return ProjectResponse(
        id=project.id,
        user_id=project.user_id,
        name=project.name,
        description=project.description,
        root_domain=project.root_domain,
        subdomain=project.subdomain,
        notification_channels=project.notification_channels or [],
        created_at=project.created_at,
        keywords_count=keywords_count
    )


@router.patch("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int,
    project_update: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project_update.name is not None:
        project.name = project_update.name
    if project_update.description is not None:
        project.description = project_update.description
    if project_update.root_domain is not None:
        project.root_domain = project_update.root_domain
    if project_update.subdomain is not None:
        project.subdomain = project_update.subdomain
    if project_update.notification_channels is not None:
        project.notification_channels = project_update.notification_channels
    
    db.commit()
    db.refresh(project)
    
    keywords_count = db.query(Keyword).filter(Keyword.project_id == project.id).count()
    
    return ProjectResponse(
        id=project.id,
        user_id=project.user_id,
        name=project.name,
        description=project.description,
        root_domain=project.root_domain,
        subdomain=project.subdomain,
        notification_channels=project.notification_channels or [],
        created_at=project.created_at,
        keywords_count=keywords_count
    )


@router.delete("/{project_id}")
def delete_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    db.delete(project)
    db.commit()
    
    return {"message": "Project deleted"}


# ============ Keywords ============
@router.get("/{project_id}/keywords", response_model=List[KeywordWithResults])
def get_keywords(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check access
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project.user_id != current_user.id:
        member = db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == current_user.id
        ).first()
        if not member:
            raise HTTPException(status_code=403, detail="Access denied")
    
    keywords = db.query(Keyword).filter(Keyword.project_id == project_id).all()
    
    result = []
    for k in keywords:
        try:
            latest_result = db.query(RankResult).filter(
                RankResult.keyword_id == k.id
            ).order_by(RankResult.checked_at.desc()).first()
        except:
            latest_result = None
        
        try:
            results_count = db.query(RankResult).filter(
                RankResult.keyword_id == k.id
            ).count()
        except:
            results_count = 0
        
        rank = None
        url = None
        if latest_result:
            try:
                rank = latest_result.rank
                url = latest_result.url
            except:
                pass
        
        result.append(KeywordWithResults(
            id=k.id,
            project_id=k.project_id,
            keyword=k.keyword,
            country_code=k.country_code,
            language=k.language,
            tracking_interval_hours=k.tracking_interval_hours,
            is_active=k.is_active,
            created_at=k.created_at,
            results_count=results_count,
            latest_rank=rank,
            latest_url=url
        ))
    
    return result


@router.post("/{project_id}/keywords", response_model=KeywordResponse)
def create_keyword(
    project_id: int,
    keyword: KeywordCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check access - owner or member can add keywords
    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Check if user is owner or member
    if project.user_id != current_user.id:
        member = db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == current_user.id
        ).first()
        if not member:
            raise HTTPException(status_code=403, detail="Access denied")
    
    db_keyword = Keyword(
        project_id=project_id,
        keyword=keyword.keyword,
        country_code=keyword.country_code,
        language=keyword.language,
        tracking_interval_hours=keyword.tracking_interval_hours
    )
    db.add(db_keyword)
    db.commit()
    db.refresh(db_keyword)
    
    return KeywordResponse(
        id=db_keyword.id,
        project_id=db_keyword.project_id,
        keyword=db_keyword.keyword,
        country_code=db_keyword.country_code,
        language=db_keyword.language,
        tracking_interval_hours=db_keyword.tracking_interval_hours,
        is_active=db_keyword.is_active,
        created_at=db_keyword.created_at,
        results_count=0
    )


@router.patch("/keywords/{keyword_id}", response_model=KeywordResponse)
def update_keyword(
    keyword_id: int,
    keyword_update: KeywordUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    keyword = db.query(Keyword).join(Project).filter(
        Keyword.id == keyword_id,
        Project.user_id == current_user.id
    ).first()
    
    if not keyword:
        raise HTTPException(status_code=404, detail="Keyword not found")
    
    if keyword_update.keyword is not None:
        keyword.keyword = keyword_update.keyword
    if keyword_update.country_code is not None:
        keyword.country_code = keyword_update.country_code
    if keyword_update.language is not None:
        keyword.language = keyword_update.language
    if keyword_update.tracking_interval_hours is not None:
        keyword.tracking_interval_hours = keyword_update.tracking_interval_hours
    if keyword_update.is_active is not None:
        keyword.is_active = keyword_update.is_active
    
    db.commit()
    db.refresh(keyword)
    
    results_count = db.query(RankResult).filter(
        RankResult.keyword_id == keyword.id
    ).count()
    
    return KeywordResponse(
        id=keyword.id,
        project_id=keyword.project_id,
        keyword=keyword.keyword,
        country_code=keyword.country_code,
        language=keyword.language,
        tracking_interval_hours=keyword.tracking_interval_hours,
        is_active=keyword.is_active,
        created_at=keyword.created_at,
        results_count=results_count
    )


@router.delete("/keywords/{keyword_id}")
def delete_keyword(
    keyword_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check ownership or membership
    keyword = db.query(Keyword).join(Project).filter(
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

    db.delete(keyword)
    db.commit()

    return {"message": "Keyword deleted"}


# ============ Results ============
@router.get("/keywords/{keyword_id}/results", response_model=List[RankResultResponse])
def get_keyword_results(
    keyword_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    keyword = db.query(Keyword).join(Project).filter(
        Keyword.id == keyword_id,
        Project.user_id == current_user.id
    ).first()
    
    if not keyword:
        raise HTTPException(status_code=404, detail="Keyword not found")
    
    results = db.query(RankResult).filter(
        RankResult.keyword_id == keyword_id
    ).order_by(RankResult.checked_at.desc()).limit(100).all()
    
    return results


# ============ Share Project ============
@router.post("/{project_id}/share")
def share_project(
    project_id: int,
    request: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    email = request.get("email")
    role = request.get("role", "editor")
    """Share project with another user by email"""
    # Check ownership
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Find user by email
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot share with yourself")
    
    # Check if already shared
    existing = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == user.id
    ).first()
    
    if existing:
        existing.role = role
    else:
        member = ProjectMember(
            project_id=project_id,
            user_id=user.id,
            role=role
        )
        db.add(member)
    
    db.commit()
    return {"message": f"Project shared with {email}"}


@router.get("/{project_id}/members")
def get_project_members(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get project members"""
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check access
    if project.user_id != current_user.id:
        member = db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == current_user.id
        ).first()
        if not member:
            raise HTTPException(status_code=403, detail="Access denied")
    
    members = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id
    ).all()
    
    result = []
    for m in members:
        user = db.query(User).filter(User.id == m.user_id).first()
        if user:
            result.append({
                "user_id": user.id,
                "email": user.email,
                "username": user.username,
                "role": m.role
            })
    
    return result


@router.delete("/{project_id}/members/{user_id}")
def remove_project_member(
    project_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove a member from project"""
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    member = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == user_id
    ).first()
    
    if member:
        db.delete(member)
        db.commit()
    
    return {"message": "Member removed"}
