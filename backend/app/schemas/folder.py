from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid

# Shared properties
class FolderBase(BaseModel):
    name: str
    parent_id: Optional[uuid.UUID] = None

# Properties to receive on creation
class FolderCreate(FolderBase):
    pass

# Properties to receive on update
class FolderUpdate(FolderBase):
    pass

# Properties shared by models stored in DB
class FolderInDBBase(FolderBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Properties to return to client
class Folder(FolderInDBBase):
    pass

# Properties stored in DB
class FolderInDB(FolderInDBBase):
    pass
