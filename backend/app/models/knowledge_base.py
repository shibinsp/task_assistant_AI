"""
TaskPulse - AI Assistant - Knowledge Base Model
Document storage for RAG-powered AI assistance
"""

from sqlalchemy import Column, String, Enum, Text, Boolean, ForeignKey, Integer, Float, DateTime
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
import enum

from app.database import Base


class DocumentSource(str, enum.Enum):
    """Source of the document."""
    MANUAL_UPLOAD = "manual_upload"
    CONFLUENCE = "confluence"
    NOTION = "notion"
    GITHUB = "github"
    GITLAB = "gitlab"
    JIRA = "jira"
    SLACK = "slack"
    INTERNAL_WIKI = "internal_wiki"
    EXTERNAL_URL = "external_url"


class DocumentStatus(str, enum.Enum):
    """Document processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    INDEXED = "indexed"
    FAILED = "failed"
    ARCHIVED = "archived"


class DocumentType(str, enum.Enum):
    """Type of document."""
    DOCUMENTATION = "documentation"
    CODE_SNIPPET = "code_snippet"
    TUTORIAL = "tutorial"
    FAQ = "faq"
    RUNBOOK = "runbook"
    POLICY = "policy"
    MEETING_NOTES = "meeting_notes"
    ARCHITECTURE = "architecture"
    GUIDE = "guide"
    TROUBLESHOOTING = "troubleshooting"
    OTHER = "other"


class Document(Base):
    """
    Knowledge base document.
    Stores source documents that are chunked and embedded for RAG.
    """

    __tablename__ = "documents"

    org_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Document metadata
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    source = Column(Enum(DocumentSource), default=DocumentSource.MANUAL_UPLOAD)
    source_url = Column(String(2000), nullable=True)
    source_id = Column(String(255), nullable=True)  # External ID for sync

    # Content
    content = Column(Text, nullable=False)
    content_hash = Column(String(64), nullable=True)  # For change detection
    doc_type = Column(Enum(DocumentType), default=DocumentType.DOCUMENTATION)

    # Processing status
    status = Column(Enum(DocumentStatus), default=DocumentStatus.PENDING, index=True)
    error_message = Column(Text, nullable=True)
    processed_at = Column(DateTime, nullable=True)

    # Metadata
    file_name = Column(String(500), nullable=True)
    file_type = Column(String(50), nullable=True)  # pdf, md, txt, etc.
    file_size = Column(Integer, nullable=True)
    storage_path = Column(String(500), nullable=True)
    storage_url = Column(String(2000), nullable=True)
    language = Column(String(50), default="en")

    # Access control
    is_public = Column(Boolean, default=False)  # Visible to all org members
    team_ids = Column(JSONB, default=[])  # Restricted to these teams

    # Categorization
    tags = Column(JSONB, default=[])
    categories = Column(JSONB, default=[])

    # Stats
    view_count = Column(Integer, default=0)
    helpful_count = Column(Integer, default=0)
    not_helpful_count = Column(Integer, default=0)

    # Sync
    last_synced_at = Column(DateTime, nullable=True)
    sync_enabled = Column(Boolean, default=True)

    # Relationships
    organization = relationship("Organization", backref="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Document(id={self.id}, title={self.title[:30]}...)>"


class DocumentChunk(Base):
    """
    Chunked document for embedding and retrieval.
    Documents are split into smaller chunks for better RAG performance.
    """

    __tablename__ = "document_chunks"

    document_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Chunk content
    content = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)  # Order within document
    start_char = Column(Integer, nullable=True)  # Start position in original
    end_char = Column(Integer, nullable=True)  # End position in original

    # Embedding (pgvector native column)
    embedding = Column(Vector(1536), nullable=True)
    embedding_model = Column(String(100), nullable=True)

    # Metadata
    token_count = Column(Integer, nullable=True)
    chunk_metadata = Column(JSONB, default={})

    # Relationships
    document = relationship("Document", back_populates="chunks")

    def __repr__(self) -> str:
        return f"<DocumentChunk(doc={self.document_id}, index={self.chunk_index})>"


class UnblockSession(Base):
    """
    AI unblock session tracking.
    Tracks interactions with the AI unblock engine.
    """

    __tablename__ = "unblock_sessions"

    org_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    user_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    task_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("tasks.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    checkin_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("checkins.id", ondelete="SET NULL"),
        nullable=True
    )

    # Query
    query = Column(Text, nullable=False)
    blocker_type = Column(String(50), nullable=True)
    user_skill_level = Column(String(50), default="intermediate")

    # Response
    response = Column(Text, nullable=True)
    confidence = Column(Float, nullable=True)
    sources = Column(JSONB, default=[])  # Document IDs used

    # Escalation
    escalation_recommended = Column(Boolean, default=False)
    escalated = Column(Boolean, default=False)
    escalated_to = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Feedback
    was_helpful = Column(Boolean, nullable=True)
    feedback_text = Column(Text, nullable=True)
    feedback_at = Column(DateTime, nullable=True)

    # Relationships
    organization = relationship("Organization", backref="unblock_sessions")
    user = relationship("User", foreign_keys=[user_id], backref="unblock_sessions")
    task = relationship("Task", backref="unblock_sessions")
    checkin = relationship("CheckIn", backref="unblock_session")
    escalated_user = relationship("User", foreign_keys=[escalated_to])

    def __repr__(self) -> str:
        return f"<UnblockSession(id={self.id}, user={self.user_id})>"
