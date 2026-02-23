from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from backend.app import schemas
from backend.app.models import Document, StandardVersion, ValidationResult, ValidationStatus
from backend.app.database import get_session
from backend.app.api import deps
from backend.app.services.validation_service import validation_service
from backend.app.services.storage import minio_client
import uuid

router = APIRouter()

@router.post("/{document_id}/validate", response_model=schemas.validation_audit.ValidationResult) # Need schema
async def validate_document_endpoint(
    *,
    db: AsyncSession = Depends(get_session),
    document_id: uuid.UUID,
    standard_version_id: uuid.UUID = Body(..., embed=True), # Explicitly pass version for now
    current_user: dict = Depends(deps.get_current_active_user),
) -> Any:
    """
    Validate a document against a standard version.
    """
    # 1. Fetch Entitites
    document = await db.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
        
    start_ver = await db.get(StandardVersion, standard_version_id)
    if not start_ver:
        raise HTTPException(status_code=404, detail="Standard version not found")
        
    # 2. Get File
    storage_path = document.minio_version_id or f"{document.id}/{document.filename}"
    file_content = minio_client.get_file(storage_path)
    
    # 3. Validate
    report = validation_service.validate_document(file_content, start_ver)
    
    # 4. Save Result
    status = ValidationStatus.PASS if report["compliant"] else ValidationStatus.FAIL
    if report["compliant"] and report["warnings"]:
        status = ValidationStatus.WARN
        
    validation_result = ValidationResult(
        document_id=document_id,
        standard_version_id=standard_version_id,
        status=status,
        report_json=report
    )
    db.add(validation_result)
    await db.commit()
    await db.refresh(validation_result)
    
    return validation_result
