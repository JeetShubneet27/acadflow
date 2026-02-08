from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.models.draft_lock import DraftLock
from app.models.enums import DraftLockStatus, InviteStatus
from app.models.project_invite import ProjectInvite
from app.models.user import User


router = APIRouter(tags=["maintenance"])


@router.post("/maintenance/cleanup")
def run_cleanup(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(["faculty"])),
) -> dict:
    now = datetime.utcnow()
    invite_count = (
        db.query(ProjectInvite)
        .filter(ProjectInvite.status == InviteStatus.pending, ProjectInvite.expires_at < now)
        .update({ProjectInvite.status: InviteStatus.expired}, synchronize_session=False)
    )
    lock_count = (
        db.query(DraftLock)
        .filter(DraftLock.status == DraftLockStatus.active, DraftLock.expires_at < now)
        .update({DraftLock.status: DraftLockStatus.expired}, synchronize_session=False)
    )
    db.commit()
    return {"expired_invites": invite_count, "expired_locks": lock_count}
