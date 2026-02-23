"""
Decision Flow API — Compatibility-gated standard application.
"""
from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.database import get_session
from backend.app.api import deps
from backend.app.models import Document, TargetType
from backend.app.services.storage import minio_client
from backend.app.services.inheritance_service import inheritance_service
from backend.app.services.decision_flow_service import decision_flow_service
from backend.app.services.audit_service import audit_service
import uuid

router = APIRouter()


@router.post("/{document_id}/analyze")
async def analyze_compatibility(
    *,
    db: AsyncSession = Depends(get_session),
    document_id: uuid.UUID,
    current_user: dict = Depends(deps.get_current_active_user),
) -> Any:
    """
    Run compatibility analysis only (no transformation).
    Returns score, per-dimension breakdown, and risk classification.
    """
    # 1. Fetch document + standard
    document = await db.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    effective_std = await inheritance_service.get_effective_standard_version(
        db, document_id, TargetType.DOCUMENT
    )
    if not effective_std:
        raise HTTPException(status_code=400, detail="No standard assigned to this document.")

    # 2. Get file
    storage_path = document.minio_version_id or f"{document.id}/{document.filename}"
    file_content = minio_client.get_file(storage_path)

    # 3. Analyze
    result = await decision_flow_service.analyze(
        file_content, document.filename, effective_std.rules_json
    )
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])

    # Remove raw text from response
    result.pop("text", None)
    return result


@router.post("/{document_id}/apply")
async def apply_with_decision_flow(
    *,
    db: AsyncSession = Depends(get_session),
    document_id: uuid.UUID,
    competence_level: str = "general",
    current_user: dict = Depends(deps.get_current_active_user),
) -> Any:
    """
    Full decision flow pipeline: analyze → select rules → transform (gated).
    Transformation only happens if compatibility score permits.
    """
    # 1. Fetch document + standard
    document = await db.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    effective_std = await inheritance_service.get_effective_standard_version(
        db, document_id, TargetType.DOCUMENT
    )
    if not effective_std:
        raise HTTPException(status_code=400, detail="No standard assigned to this document.")

    # 2. Get file
    storage_path = document.minio_version_id or f"{document.id}/{document.filename}"
    file_content = minio_client.get_file(storage_path)

    # 3. Run full pipeline
    result = await decision_flow_service.apply(
        file_content, document.filename, effective_std.rules_json, competence_level=competence_level
    )
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])

    # 4. Save transformed content if available
    if result.get("transformed_content"):
        from backend.app.models import ValidationResult
        from sqlmodel import select

        fixed_object_name = f"fixed/{document_id}/{document.filename}.fixed.txt"
        try:
            minio_client.upload_file(
                result["transformed_content"].encode("utf-8"),
                fixed_object_name,
                "text/plain"
            )
        except Exception as e:
            print(f"Warning: could not save fixed content: {e}")

        # Update latest validation result
        stmt = (
            select(ValidationResult)
            .where(ValidationResult.document_id == document_id)
            .order_by(ValidationResult.created_at.desc())
            .limit(1)
        )
        res = await db.execute(stmt)
        v = res.scalar_one_or_none()
        if v:
            existing = v.report_json or {}
            existing["fixed_content"] = result["transformed_content"]
            existing["fixed_path"] = fixed_object_name
            existing["decision_flow"] = {
                "action": result["action"],
                "score": result["score"],
                "risk": result["risk"],
                "rule_selection": result["rule_selection"],
                "warnings": result["warnings"],
            }
            v.report_json = existing
            db.add(v)
            await db.commit()

    # 5. Audit
    await audit_service.log_action(
        db,
        actor_id=current_user.get("sub", "unknown"),
        action=f"DECISION_FLOW_{result['action'].upper()}",
        target_id=document_id,
        details={
            "score": result["score"],
            "risk": result["risk"],
            "action": result["action"]
        }
    )
    await db.commit()

    return result
