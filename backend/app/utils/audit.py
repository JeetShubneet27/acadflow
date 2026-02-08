from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.audit_event import AuditEvent


def log_event(
    db: Session,
    project_id: Optional[int],
    actor_id: Optional[int],
    event_type: str,
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    metadata: Optional[dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> AuditEvent:
    event = AuditEvent(
        project_id=project_id,
        actor_id=actor_id,
        event_type=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
        metadata=metadata,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(event)
    return event
