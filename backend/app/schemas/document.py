from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid

class DocumentBase(BaseModel):
    filename: str
    folder_id: Optional[uuid.UUID] = None

class DocumentCreate(DocumentBase):
    pass

class Document(DocumentBase):
    id: uuid.UUID
    minio_version_id: Optional[str] = None
    hash: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
