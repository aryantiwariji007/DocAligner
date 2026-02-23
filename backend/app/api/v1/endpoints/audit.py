from typing import Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from backend.app.models import AuditLog
from backend.app.database import get_session
from backend.app.api import deps
import uuid

router = APIRouter()

@router.get("/", response_model=List[AuditLog])
async def read_audit_logs(
    db: AsyncSession = Depends(get_session),
    skip: int = 0,
    limit: int = 100,
    target_id: uuid.UUID = None,
    current_user: dict = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve audit logs.
    """
    stmt = select(AuditLog)
    if target_id:
        stmt = stmt.where(AuditLog.target_id == target_id)
        
    stmt = stmt.order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    logs = result.scalars().all()
    return logs
