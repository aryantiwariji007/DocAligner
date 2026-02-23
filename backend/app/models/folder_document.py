from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
import uuid
from .base import IDMixin, TimestampMixin

class FolderBase(SQLModel):
    name: str = Field(index=True)
    parent_id: Optional[uuid.UUID] = Field(default=None, foreign_key="folder.id", index=True)

class Folder(FolderBase, IDMixin, TimestampMixin, table=True):
    __tablename__ = "folder"
    parent: Optional["Folder"] = Relationship(back_populates="children", sa_relationship_kwargs={"remote_side": "Folder.id"})
    children: List["Folder"] = Relationship(back_populates="parent")
    documents: List["Document"] = Relationship(
        back_populates="folder",
        sa_relationship_kwargs={"lazy": "selectin", "cascade": "all, delete-orphan"}
    )
    
    # We will use this for standard inheritance
    # standard_assignment: Optional["StandardAssignment"] = Relationship(
    #     sa_relationship_kwargs={
    #         "primaryjoin": "and_(Folder.id==foreign(StandardAssignment.target_id), StandardAssignment.target_type=='FOLDER')",
    #         "overlaps": "folder,standard_assignment"
    #     }
    # )

class DocumentBase(SQLModel):
    filename: str = Field(index=True)
    minio_version_id: Optional[str] = None
    hash: str = Field(index=True)
    folder_id: Optional[uuid.UUID] = Field(default=None, foreign_key="folder.id", index=True)

class Document(DocumentBase, IDMixin, TimestampMixin, table=True):
    __tablename__ = "document"
    folder: Optional[Folder] = Relationship(back_populates="documents")
    validation_results: List["ValidationResult"] = Relationship(
        back_populates="document",
        sa_relationship_kwargs={"lazy": "selectin", "cascade": "all, delete-orphan"}
    )
    
    # Standard assignment
    # standard_assignment: Optional["StandardAssignment"] = Relationship(
    #     sa_relationship_kwargs={
    #         "primaryjoin": "and_(Document.id==foreign(StandardAssignment.target_id), StandardAssignment.target_type=='DOCUMENT')",
    #         "overlaps": "document,standard_assignment"
    #     }
    # )
