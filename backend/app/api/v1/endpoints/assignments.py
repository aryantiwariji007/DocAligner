from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from backend.app import schemas
from backend.app.models import StandardAssignment, TargetType, StandardVersion
from backend.app.database import get_session
from backend.app.api import deps
from backend.app.services.inheritance_service import inheritance_service
from backend.app.services.audit_service import audit_service
from backend.app.tasks import revalidate_folder_task, validate_document_task
import uuid

router = APIRouter()

@router.post("/", response_model=Any) # Returning a status dict, so Any is appropriate
async def assign_standard(
    *,
    db: AsyncSession = Depends(get_session),
    target_id: uuid.UUID = Body(...),
    target_type: TargetType = Body(...),
    standard_version_id: uuid.UUID = Body(...),
    current_user: dict = Depends(deps.get_current_active_user),
) -> Any:
    """
    Assign a standard version to a folder or document.
    """
    # Check if assignment exists
    stmt = select(StandardAssignment).where(
        StandardAssignment.target_id == target_id,
        StandardAssignment.target_type == target_type
    )
    result = await db.execute(stmt)
    existing = result.scalars().first()
    
    if existing:
        existing.standard_version_id = standard_version_id
        db.add(existing)
    else:
        new_assignment = StandardAssignment(
            target_id=target_id,
            target_type=target_type,
            standard_version_id=standard_version_id
        )
        db.add(new_assignment)
    
    # Audit
    await audit_service.log_action(
        db,
        actor_id=current_user.get("sub", "unknown"),
        action=f"ASSIGN_{target_type.value}",
        target_id=target_id,
        details={"standard_version_id": str(standard_version_id)}
    )

    await db.commit()
    
    # Trigger re-validation
    if target_type == TargetType.FOLDER:
        revalidate_folder_task.delay(str(target_id), str(standard_version_id))
    elif target_type == TargetType.DOCUMENT:
        validate_document_task.delay(str(target_id), str(standard_version_id))
        
    return {"status": "assigned, validation triggered"}

@router.get("/effective/{target_type}/{target_id}", response_model=schemas.standard.StandardVersion)
async def get_effective_standard(
    *,
    db: AsyncSession = Depends(get_session),
    target_type: TargetType,
    target_id: uuid.UUID,
    current_user: dict = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get effective standard for a target.
    """
    version = await inheritance_service.get_effective_standard_version(db, target_id, target_type)
    if not version:
        raise HTTPException(status_code=404, detail="No effective standard found")
    return version
