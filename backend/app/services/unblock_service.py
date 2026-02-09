"""
TaskPulse - AI Assistant - Unblock Service
RAG-powered AI assistance for unblocking tasks
"""

from typing import Optional, List, Tuple
from datetime import datetime
import hashlib
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.knowledge_base import (
    Document, DocumentChunk, UnblockSession,
    DocumentSource, DocumentStatus, DocumentType
)
from app.models.task import Task
from app.models.user import User
from app.schemas.ai_unblock import (
    DocumentCreate, DocumentUpdate, UnblockRequest, UnblockFeedback
)
from app.utils.helpers import generate_uuid
from app.core.exceptions import NotFoundException
from app.services.ai_service import get_ai_service


class UnblockService:
    """Service for RAG-powered AI assistance."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai_service = get_ai_service()

    # ==================== Document Management ====================

    async def create_document(
        self,
        org_id: str,
        doc_data: DocumentCreate
    ) -> Document:
        """Create and process a new document."""
        content_hash = hashlib.sha256(doc_data.content.encode()).hexdigest()

        doc = Document(
            id=generate_uuid(),
            org_id=org_id,
            title=doc_data.title,
            description=doc_data.description,
            source=doc_data.source,
            source_url=doc_data.source_url,
            doc_type=doc_data.doc_type,
            content=doc_data.content,
            content_hash=content_hash,
            language=doc_data.language,
            is_public=doc_data.is_public,
            status=DocumentStatus.PENDING
        )

        doc.tags = doc_data.tags
        doc.categories = doc_data.categories
        doc.team_ids = doc_data.team_ids

        self.db.add(doc)
        await self.db.flush()

        # Process document (chunk and embed)
        await self._process_document(doc)

        await self.db.refresh(doc)
        return doc

    async def _process_document(self, doc: Document) -> None:
        """Process document: chunk and create embeddings."""
        try:
            doc.status = DocumentStatus.PROCESSING
            await self.db.flush()

            # Simple chunking strategy (by paragraphs, max 1000 chars)
            chunks = self._chunk_content(doc.content)

            for i, chunk_content in enumerate(chunks):
                chunk = DocumentChunk(
                    id=generate_uuid(),
                    document_id=doc.id,
                    content=chunk_content,
                    chunk_index=i,
                    token_count=len(chunk_content.split())
                )

                # In production, generate actual embeddings here
                # For mock, we'll use a simple hash-based "embedding"
                chunk.embedding = self._mock_embedding(chunk_content)
                chunk.embedding_model = "mock-embeddings-v1"

                self.db.add(chunk)

            doc.status = DocumentStatus.INDEXED
            doc.processed_at = datetime.utcnow()

        except Exception as e:
            doc.status = DocumentStatus.FAILED
            doc.error_message = str(e)

        await self.db.flush()

    def _chunk_content(
        self,
        content: str,
        max_chunk_size: int = 1000,
        overlap: int = 100
    ) -> List[str]:
        """Split content into overlapping chunks."""
        chunks = []
        paragraphs = content.split('\n\n')

        current_chunk = ""
        for para in paragraphs:
            if len(current_chunk) + len(para) < max_chunk_size:
                current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = para + "\n\n"

        if current_chunk:
            chunks.append(current_chunk.strip())

        # If no natural breaks, split by size
        if not chunks:
            for i in range(0, len(content), max_chunk_size - overlap):
                chunks.append(content[i:i + max_chunk_size])

        return chunks

    def _mock_embedding(self, text: str) -> List[float]:
        """Generate mock embedding (for development without actual embeddings)."""
        # Create a simple hash-based "embedding" of 384 dimensions
        import hashlib
        hash_obj = hashlib.sha384(text.encode())
        hash_bytes = hash_obj.digest()

        # Convert to floats between -1 and 1
        embedding = []
        for byte in hash_bytes:
            embedding.append((byte / 127.5) - 1)

        return embedding

    async def get_document(
        self,
        doc_id: str,
        org_id: str
    ) -> Optional[Document]:
        """Get a document by ID."""
        result = await self.db.execute(
            select(Document).where(
                and_(Document.id == doc_id, Document.org_id == org_id)
            )
        )
        return result.scalar_one_or_none()

    async def get_documents(
        self,
        org_id: str,
        source: Optional[DocumentSource] = None,
        doc_type: Optional[DocumentType] = None,
        status: Optional[DocumentStatus] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[Document], int]:
        """Get documents with filters."""
        query = select(Document).where(Document.org_id == org_id)

        if source:
            query = query.where(Document.source == source)
        if doc_type:
            query = query.where(Document.doc_type == doc_type)
        if status:
            query = query.where(Document.status == status)
        if search:
            query = query.where(
                or_(
                    Document.title.ilike(f"%{search}%"),
                    Document.description.ilike(f"%{search}%")
                )
            )

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        query = query.offset(skip).limit(limit)
        query = query.order_by(Document.created_at.desc())

        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def update_document(
        self,
        doc_id: str,
        org_id: str,
        doc_data: DocumentUpdate
    ) -> Document:
        """Update a document."""
        doc = await self.get_document(doc_id, org_id)
        if not doc:
            raise NotFoundException("Document", doc_id)

        update_dict = doc_data.model_dump(exclude_unset=True)

        for field, value in update_dict.items():
            if field in ('tags', 'categories', 'team_ids'):
                setattr(doc, field, value)
            elif field == 'content' and value:
                # Content changed, re-process
                doc.content = value
                doc.content_hash = hashlib.sha256(value.encode()).hexdigest()
                # Delete existing chunks
                await self.db.execute(
                    DocumentChunk.__table__.delete().where(
                        DocumentChunk.document_id == doc_id
                    )
                )
                await self._process_document(doc)
            else:
                setattr(doc, field, value)

        await self.db.flush()
        await self.db.refresh(doc)
        return doc

    async def delete_document(
        self,
        doc_id: str,
        org_id: str
    ) -> bool:
        """Delete a document."""
        doc = await self.get_document(doc_id, org_id)
        if not doc:
            raise NotFoundException("Document", doc_id)

        await self.db.delete(doc)
        await self.db.flush()
        return True

    # ==================== RAG Search ====================

    async def search_documents(
        self,
        query: str,
        org_id: str,
        team_ids: Optional[List[str]] = None,
        limit: int = 5
    ) -> List[Tuple[DocumentChunk, float]]:
        """Search documents using similarity (mock implementation)."""
        # Get query embedding
        query_embedding = self._mock_embedding(query)

        # Get all indexed chunks for the org
        chunk_query = select(DocumentChunk).join(Document).where(
            and_(
                Document.org_id == org_id,
                Document.status == DocumentStatus.INDEXED
            )
        )

        if team_ids:
            # Filter by team access (simplified)
            chunk_query = chunk_query.where(
                or_(
                    Document.is_public == True,
                    # Would need proper JSON containment check in production
                )
            )

        result = await self.db.execute(
            chunk_query.options(selectinload(DocumentChunk.document))
        )
        chunks = result.scalars().all()

        # Calculate similarity scores (cosine similarity mock)
        scored_chunks = []
        for chunk in chunks:
            if chunk.embedding:
                score = self._cosine_similarity(query_embedding, chunk.embedding)
                scored_chunks.append((chunk, score))

        # Sort by score and return top results
        scored_chunks.sort(key=lambda x: x[1], reverse=True)
        return scored_chunks[:limit]

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        if len(a) != len(b):
            return 0.0

        dot_product = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot_product / (norm_a * norm_b)

    # ==================== Unblock Engine ====================

    async def get_unblock_suggestion(
        self,
        org_id: str,
        user_id: str,
        request: UnblockRequest
    ) -> dict:
        """Get AI-powered suggestion to unblock a task."""
        # Create session
        session = UnblockSession(
            id=generate_uuid(),
            org_id=org_id,
            user_id=user_id,
            task_id=request.task_id,
            checkin_id=request.checkin_id,
            query=request.query,
            blocker_type=request.blocker_type,
            user_skill_level=request.skill_level or "intermediate"
        )
        self.db.add(session)

        # Get user info for skill level
        user = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = user.scalar_one_or_none()
        team_ids = [user.team_id] if user and user.team_id else None

        # Search relevant documents
        relevant_chunks = await self.search_documents(
            request.query, org_id, team_ids, limit=5
        )

        # Build context from chunks
        context_parts = []
        source_docs = []
        for chunk, score in relevant_chunks:
            if score > 0.3:  # Relevance threshold
                context_parts.append(f"[Source: {chunk.document.title}]\n{chunk.content}")
                source_docs.append({
                    "document_id": chunk.document.id,
                    "title": chunk.document.title,
                    "relevance_score": round(score, 3),
                    "snippet": chunk.content[:200] + "..."
                })

        # Get AI suggestion
        ai_response = await self.ai_service.get_unblock_suggestion(
            task_title=request.task_id or "Unknown task",
            task_description=request.context or "",
            blocker_type=request.blocker_type or "unknown",
            blocker_description=request.query,
            user_skill_level=request.skill_level or "intermediate",
            context=context_parts
        )

        # Update session
        session.response = ai_response.get("suggestion", "")
        session.confidence = ai_response.get("confidence", 0.5)
        session.sources = [s["document_id"] for s in source_docs]
        session.escalation_recommended = ai_response.get("escalation_recommended", False)

        await self.db.flush()
        await self.db.refresh(session)

        # Determine detail level
        detail_level = ai_response.get("detail_level", request.skill_level)

        return {
            "session_id": session.id,
            "suggestion": session.response,
            "confidence": session.confidence,
            "sources": source_docs,
            "code_snippets": [],  # Would extract from response in production
            "related_docs": [s["document_id"] for s in source_docs],
            "escalation_recommended": session.escalation_recommended,
            "recommended_contacts": [],  # Would find teammates with relevant skills
            "detail_level": detail_level
        }

    async def submit_feedback(
        self,
        session_id: str,
        org_id: str,
        user_id: str,
        feedback: UnblockFeedback
    ) -> UnblockSession:
        """Submit feedback on an unblock session."""
        result = await self.db.execute(
            select(UnblockSession).where(
                and_(
                    UnblockSession.id == session_id,
                    UnblockSession.org_id == org_id
                )
            )
        )
        session = result.scalar_one_or_none()

        if not session:
            raise NotFoundException("UnblockSession", session_id)

        session.was_helpful = feedback.was_helpful
        session.feedback_text = feedback.feedback_text
        session.feedback_at = datetime.utcnow()

        # Update document helpfulness counts
        if session.sources:
            for doc_id in session.sources:
                doc = await self.get_document(doc_id, org_id)
                if doc:
                    if feedback.was_helpful:
                        doc.helpful_count += 1
                    else:
                        doc.not_helpful_count += 1

        await self.db.flush()
        await self.db.refresh(session)

        return session

    async def get_session_history(
        self,
        org_id: str,
        user_id: Optional[str] = None,
        task_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[UnblockSession], int]:
        """Get unblock session history."""
        query = select(UnblockSession).where(UnblockSession.org_id == org_id)

        if user_id:
            query = query.where(UnblockSession.user_id == user_id)
        if task_id:
            query = query.where(UnblockSession.task_id == task_id)

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        query = query.offset(skip).limit(limit)
        query = query.order_by(UnblockSession.created_at.desc())

        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    # ==================== Knowledge Base Status ====================

    async def get_knowledge_base_status(self, org_id: str) -> dict:
        """Get knowledge base statistics."""
        # Total documents
        total = (await self.db.execute(
            select(func.count()).select_from(Document).where(Document.org_id == org_id)
        )).scalar() or 0

        # By status
        status_counts = {}
        for status in DocumentStatus:
            count = (await self.db.execute(
                select(func.count()).select_from(Document).where(
                    and_(Document.org_id == org_id, Document.status == status)
                )
            )).scalar() or 0
            status_counts[status.value] = count

        # Total chunks
        total_chunks = (await self.db.execute(
            select(func.count()).select_from(DocumentChunk).join(Document).where(
                Document.org_id == org_id
            )
        )).scalar() or 0

        # By source
        source_counts = {}
        for source in DocumentSource:
            count = (await self.db.execute(
                select(func.count()).select_from(Document).where(
                    and_(Document.org_id == org_id, Document.source == source)
                )
            )).scalar() or 0
            if count > 0:
                source_counts[source.value] = count

        # Last sync
        last_sync = (await self.db.execute(
            select(func.max(Document.last_synced_at)).where(
                and_(Document.org_id == org_id, Document.last_synced_at != None)
            )
        )).scalar()

        return {
            "total_documents": total,
            "indexed_documents": status_counts.get("indexed", 0),
            "pending_documents": status_counts.get("pending", 0),
            "failed_documents": status_counts.get("failed", 0),
            "total_chunks": total_chunks,
            "last_sync": last_sync,
            "sources": source_counts
        }
