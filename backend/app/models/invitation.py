"""
Customer Invitation System

Only invited customers can register and use the system
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import secrets
import string


class InvitationCode(Base):
    __tablename__ = "invitation_codes"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    used_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    used_at = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime(timezone=True))
    max_uses = Column(Integer, default=1)  # 1 = single use
    uses_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    user = relationship("User", foreign_keys=[used_by])


def generate_code(length: int = 12) -> str:
    """Generate a random invitation code"""
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def create_invitation(db, user_id: int, max_uses: int = 1, days_until_expiry: int = 30) -> InvitationCode:
    """Create a new invitation code"""
    from datetime import datetime, timedelta
    
    code = generate_code()
    expires_at = datetime.utcnow() + timedelta(days=days_until_expiry)
    
    invitation = InvitationCode(
        code=code,
        created_by=user_id,
        max_uses=max_uses,
        expires_at=expires_at
    )
    
    db.add(invitation)
    db.commit()
    db.refresh(invitation)
    
    return invitation


def validate_code(db, code: str) -> tuple[bool, str]:
    """Validate an invitation code"""
    
    invitation = db.query(InvitationCode).filter(
        InvitationCode.code == code,
        InvitationCode.is_active == True
    ).first()
    
    if not invitation:
        return False, "邀请码无效"
    
    if invitation.expires_at and invitation.expires_at.isoformat() < datetime.utcnow().isoformat():
        return False, "邀请码已过期"
    
    if invitation.uses_count >= invitation.max_uses:
        return False, "邀请码已达到使用上限"
    
    return True, "valid"


def use_code(db, code: str, user_id: int) -> bool:
    """Mark an invitation code as used"""
    from datetime import datetime
    
    invitation = db.query(InvitationCode).filter(
        InvitationCode.code == code,
        InvitationCode.is_active == True
    ).first()
    
    if not invitation:
        return False
    
    invitation.used_by = user_id
    invitation.used_at = datetime.utcnow()
    invitation.uses_count += 1
    
    if invitation.uses_count >= invitation.max_uses:
        invitation.is_active = False
    
    db.commit()
    return True


# API Usage:
"""
@router.post("/admin/invitation-codes", response_model=InvitationCodeResponse)
def create_invitation_code(
    max_uses: int = 1,
    days_until_expiry: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check if admin
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    
    invitation = create_invitation(db, current_user.id, max_uses, days_until_expiry)
    return invitation


@router.post("/auth/register", response_model=UserResponse)
def register_with_invitation(
    user: UserCreate,
    invitation_code: str,
    db: Session = Depends(get_db)
):
    # Validate invitation code
    is_valid, message = validate_code(db, invitation_code)
    if not is_valid:
        raise HTTPException(status_code=400, detail=message)
    
    # ... create user (from existing code)
    
    # Mark code as used
    use_code(db, invitation_code, user.id)
    
    return user
"""
