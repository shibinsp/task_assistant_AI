"""
TaskPulse - AI Assistant - AI Unblock Schemas
Pydantic schemas for RAG-powered AI assistance
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

from app.models.knowledge_base import DocumentSource, DocumentStatus, DocumentType


# ==================== Document Schemas ====================

class DocumentBase(BaseModel):
    """Base document schema."""
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    source: DocumentSource = DocumentSource.MANUAL_UPLOAD
    source_url: Optional[str] = Field(None, max_length=2000)
    doc_type: DocumentType = DocumentType.DOCUMENTATION
    language: str = "en"
    is_public: bool = True
    team_ids: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    categories: List[str] = Field(default_factory=list)


class DocumentCreate(DocumentBase):
    """Schema for creating a document."""
    content: str = Field(..., min_length=1)


class DocumentUpdate(BaseModel):
    """Schema for updating a document."""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = None
    doc_type: Optional[DocumentType] = None
    language: Optional[str] = None
    is_public: Optional[bool] = None
    team_ids: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    categories: Optional[List[str]] = None
    content: Optional[str] = None


class DocumentResponse(BaseModel):
    """Document response schema."""
    id: str
    org_id: str
    title: str
    description: Optional[str]
    source: DocumentSource
    source_url: Optional[str]
    doc_type: DocumentType
    status: DocumentStatus
    file_name: Optional[str]
    file_type: Optional[str]
    language: str
    is_public: bool
    tags: List[str]
    categories: List[str]
    view_count: int
    helpful_count: int
    not_helpful_count: int
    processed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """Paginated document list."""
    documents: List[DocumentResponse]
    total: int
    page: int
    page_size: int


# ==================== Unblock Request/Response ====================

class UnblockRequest(BaseModel):
    """Request for AI unblock assistance."""
    query: str = Field(..., min_length=1, max_length=5000)
    task_id: Optional[str] = None
    checkin_id: Optional[str] = None
    blocker_type: Optional[str] = None
    context: Optional[str] = Field(None, max_length=10000)
    skill_level: Optional[str] = Field("intermediate", pattern="^(junior|intermediate|senior)$")


class UnblockSource(BaseModel):
    """Source document used in response."""
    document_id: str
    title: str
    relevance_score: float
    snippet: str


class UnblockResponse(BaseModel):
    """Response from AI unblock engine."""
    session_id: str
    suggestion: str
    confidence: float
    sources: List[UnblockSource]
    code_snippets: List[str] = Field(default_factory=list)
    related_docs: List[str] = Field(default_factory=list)
    escalation_recommended: bool = False
    recommended_contacts: List[str] = Field(default_factory=list)
    detail_level: str  # junior, intermediate, senior


class UnblockFeedback(BaseModel):
    """Feedback on unblock response."""
    was_helpful: bool
    feedback_text: Optional[str] = Field(None, max_length=1000)


class UnblockFeedbackResponse(BaseModel):
    """Confirmation of feedback submission."""
    session_id: str
    feedback_recorded: bool = True
    thank_you_message: str = "Thank you for your feedback!"


# ==================== Knowledge Base Status ====================

class KnowledgeBaseStatus(BaseModel):
    """Knowledge base status."""
    total_documents: int
    indexed_documents: int
    pending_documents: int
    failed_documents: int
    total_chunks: int
    last_sync: Optional[datetime]
    sources: dict  # Count by source


class SyncRequest(BaseModel):
    """Request to sync documents from external source."""
    source: DocumentSource
    source_url: Optional[str] = None
    credentials_key: Optional[str] = None  # Reference to stored credentials


class SyncResponse(BaseModel):
    """Response from sync operation."""
    source: DocumentSource
    documents_found: int
    documents_synced: int
    documents_updated: int
    errors: List[str] = Field(default_factory=list)
    sync_id: str


# ==================== Upload Schema ====================

class UploadResponse(BaseModel):
    """Response from document upload."""
    document_id: str
    title: str
    status: DocumentStatus
    message: str


# ==================== Session History ====================

class UnblockSessionResponse(BaseModel):
    """Unblock session details."""
    id: str
    user_id: Optional[str]
    task_id: Optional[str]
    query: str
    response: Optional[str]
    confidence: Optional[float]
    sources: List[str]
    was_helpful: Optional[bool]
    feedback_text: Optional[str]
    escalated: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UnblockHistoryResponse(BaseModel):
    """User's unblock history."""
    sessions: List[UnblockSessionResponse]
    total: int
    page: int
    page_size: int
