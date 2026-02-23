from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models import AuditLog
import uuid
from typing import Dict, Any

class AuditService:
    async def log_action(
        self,
        db: AsyncSession,
        actor_id: str,
        action: str,
        target_id: uuid.UUID,
        details: Dict[str, Any] = None
    ):
        """
        Creates an audit log entry.
        """
        log_entry = AuditLog(
            actor_id=actor_id,
            action=action,
            target_id=target_id,
            details=details or {}
        )
        db.add(log_entry)
        # We assume the caller commits the transaction, strictly speaking.
        # But if we want audit to persist even if main action fails? 
        # Usually audit is part of the transaction or separate. 
        # For simplicity, we add to session. Caller commits.
        return log_entry

audit_service = AuditService()
