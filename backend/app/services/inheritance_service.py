from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from backend.app.models import StandardAssignment, TargetType, Folder, Document, StandardVersion
import uuid
from typing import Optional

class InheritanceService:
    async def get_effective_standard_version(
        self, db: AsyncSession, target_id: uuid.UUID, target_type: TargetType
    ) -> Optional[StandardVersion]:
        """
        Resolves the effective standard version for a given folder or document.
        Logic:
        1. Check direct assignment.
        2. If Document, check parent folder recursively.
        3. If Folder, check parent folder recursively.
        """
        # 1. Direct Assignment check
        stmt = select(StandardAssignment).where(
            StandardAssignment.target_id == target_id,
            StandardAssignment.target_type == target_type
        )
        result = await db.execute(stmt)
        assignment = result.scalars().first()
        
        if assignment:
            # Fetch the version
            # Assuming eager loading or we fetch it
            return await db.get(StandardVersion, assignment.standard_version_id)
            
        # 2. Ancestor Traversal
        current_folder_id = None
        
        if target_type == TargetType.DOCUMENT:
            # Get document to find parent folder
            doc = await db.get(Document, target_id)
            if doc and doc.folder_id:
                current_folder_id = doc.folder_id
        elif target_type == TargetType.FOLDER:
            # Get folder to find parent
            folder = await db.get(Folder, target_id)
            if folder:
                current_folder_id = folder.parent_id
                
        while current_folder_id:
            # Check assignment on this folder
            stmt = select(StandardAssignment).where(
                StandardAssignment.target_id == current_folder_id,
                StandardAssignment.target_type == TargetType.FOLDER
            )
            result = await db.execute(stmt)
            assignment = result.scalars().first()
            
            if assignment:
                return await db.get(StandardVersion, assignment.standard_version_id)
            
            # Move up
            folder = await db.get(Folder, current_folder_id)
            if not folder:
                break
            current_folder_id = folder.parent_id
            
        return None

inheritance_service = InheritanceService()
