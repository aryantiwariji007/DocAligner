from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime
import uuid
from enum import Enum

class TargetType(str, Enum):
    FOLDER = "FOLDER"
    DOCUMENT = "DOCUMENT"

class StandardBase(BaseModel):
    name: str
    description: Optional[str] = None

class StandardCreate(StandardBase):
    pass

class StandardAssignmentBase(BaseModel):
    target_id: uuid.UUID
    target_type: TargetType
    standard_version_id: uuid.UUID

class StandardAssignment(StandardAssignmentBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class StandardVersionBase(BaseModel):
    standard_id: uuid.UUID
    version_number: int
    rules_json: Optional[Dict] = {}
    is_active: bool

class StandardVersion(StandardVersionBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class Standard(StandardBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    versions: Optional[List[StandardVersion]] = None

    class Config:
        from_attributes = True

# Resolve forward references
Standard.model_rebuild()
