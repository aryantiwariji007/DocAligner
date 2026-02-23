from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Literal, Union
from enum import Enum

# --- Enums ---
class StandardStatus(str, Enum):
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    DRAFT = "draft"

class ScopeLevel(str, Enum):
    FILE = "file"
    FOLDER = "folder"
    ORGANIZATION = "organization"

class HeadingStyle(str, Enum):
    NUMBERED = "numbered"
    ROMAN = "roman"
    PLAIN = "plain"

class ModalVerb(str, Enum):
    MUST = "must"
    SHOULD = "should"
    COULD = "could"

# --- Nested Models ---

class Scope(BaseModel):
    level: ScopeLevel
    applies_to: Optional[str] = Field(None, description="Folder ID or file ID")

class StandardStructure(BaseModel):
    mandatory_sections: List[str] = Field(default_factory=list)
    section_order_enforced: bool = False

class FontRules(BaseModel):
    body: Optional[str] = None
    heading: Optional[str] = None

class FormattingRules(BaseModel):
    heading_style: Optional[HeadingStyle] = None
    font_rules: Optional[FontRules] = None

class LanguageRules(BaseModel):
    controlled_vocabulary: bool = False
    modal_verbs: List[ModalVerb] = Field(default_factory=list)

class MetadataRules(BaseModel):
    versioning_required: bool = False
    approval_block_required: bool = False

class StandardRules(BaseModel):
    structure: Optional[StandardStructure] = None
    formatting: Optional[FormattingRules] = None
    language: Optional[LanguageRules] = None
    metadata: Optional[MetadataRules] = None

# --- Main Model ---

class DocumentStandard(BaseModel):
    """
    Strict JSON Schema for Document Standards.
    Ensures LLM output is deterministic and valid.
    """
    standard_id: str = Field(..., description="Unique identifier for the standard")
    version: str = Field(..., pattern=r"^[0-9]+\.[0-9]+(\.[0-9]+)?$")
    status: StandardStatus = StandardStatus.DRAFT
    scope: Scope
    rules: StandardRules
