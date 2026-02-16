"""
TaskPulse - AI Assistant - Knowledge Base Model
Document storage for RAG-powered AI assistance
"""

from sqlalchemy import Column, String, Enum, Text, Boolean, ForeignKey, Integer, Float, DateTime
from sqlalchemy.orm import relationship
import enum
from datetime import datetime
from typing import Optional

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
        String(36),
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
    language = Column(String(50), default="en")

    # Access control
    is_public = Column(Boolean, default=False)  # Visible to all org members
    team_ids_json = Column(Text, default="[]")  # Restricted to these teams

    # Categorization
    tags_json = Column(Text, default="[]")
    categories_json = Column(Text, default="[]")

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

    @property
    def tags(self) -> list:
        import json
        try:
            return json.loads(self.tags_json or "[]")
        except:
            return []

    @tags.setter
    def tags(self, value: list):
        import json
        self.tags_json = json.dumps(value)

    @property
    def categories(self) -> list:
        import json
        try:
            return json.loads(self.categories_json or "[]")
        except:
            return []

    @categories.setter
    def categories(self, value: list):
        import json
        self.categories_json = json.dumps(value)

    @property
    def team_ids(self) -> list:
        import json
        try:
            return json.loads(self.team_ids_json or "[]")
        except:
            return []

    @team_ids.setter
    def team_ids(self, value: list):
        import json
        self.team_ids_json = json.dumps(value)


class DocumentChunk(Base):
    """
    Chunked document for embedding and retrieval.
    Documents are split into smaller chunks for better RAG performance.
    """

    __tablename__ = "document_chunks"

    document_id = Column(
        String(36),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Chunk content
    content = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)  # Order within document
    start_char = Column(Integer, nullable=True)  # Start position in original
    end_char = Column(Integer, nullable=True)  # End position in original

    # Embedding (stored as JSON string for SQLite compatibility)
    # In production, use pgvector or similar
    embedding_json = Column(Text, nullable=True)
    embedding_model = Column(String(100), nullable=True)

    # Metadata
    token_count = Column(Integer, nullable=True)
    metadata_json = Column(Text, default="{}")

    # Relationships
    document = relationship("Document", back_populates="chunks")

    def __repr__(self) -> str:
        return f"<DocumentChunk(doc={self.document_id}, index={self.chunk_index})>"

    @property
    def embedding(self) -> Optional[list]:
        import json
        try:
            return json.loads(self.embedding_json) if self.embedding_json else None
        except:
            return None

    @embedding.setter
    def embedding(self, value: list):
        import json
        self.embedding_json = json.dumps(value) if value else None

    @property
    def chunk_metadata(self) -> dict:
        import json
        try:
            return json.loads(self.metadata_json or "{}")
        except:
            return {}

    @chunk_metadata.setter
    def chunk_metadata(self, value: dict):
        import json
        self.metadata_json = json.dumps(value)


class UnblockSession(Base):
    """
    AI unblock session tracking.
    Tracks interactions with the AI unblock engine.
    """

    __tablename__ = "unblock_sessions"

    org_id = Column(
        String(36),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    task_id = Column(
        String(36),
        ForeignKey("tasks.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    checkin_id = Column(
        String(36),
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
    sources_json = Column(Text, default="[]")  # Document IDs used

    # Escalation
    escalation_recommended = Column(Boolean, default=False)
    escalated = Column(Boolean, default=False)
    escalated_to = Column(String(36), ForeignKey("users.id"), nullable=True)

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

    @property
    def sources(self) -> list:
        import json
        try:
            return json.loads(self.sources_json or "[]")
        except:
            return []

    @sources.setter
    def sources(self, value: list):
        import json
        self.sources_json = json.dumps(value)
