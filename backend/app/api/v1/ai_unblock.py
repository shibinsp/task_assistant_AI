"""
TaskPulse - AI Assistant - AI Unblock API
RAG-powered AI assistance endpoints
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, Query, status, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User, UserRole
from app.models.knowledge_base import DocumentSource, DocumentStatus, DocumentType
from app.schemas.ai_unblock import (
    DocumentCreate, DocumentUpdate, DocumentResponse, DocumentListResponse,
    UnblockRequest, UnblockResponse, UnblockFeedback, UnblockFeedbackResponse,
    KnowledgeBaseStatus, UploadResponse,
    UnblockSessionResponse, UnblockHistoryResponse
)
from app.services.unblock_service import UnblockService
from app.api.v1.dependencies import (
    get_current_active_user, require_roles, get_pagination, PaginationParams
)
from app.core.permissions import Permission, has_permission
from app.core.exceptions import NotFoundException, ForbiddenException

router = APIRouter()


def get_unblock_service(db: AsyncSession = Depends(get_db)) -> UnblockService:
    """Dependency to get unblock service."""
    return UnblockService(db)


# ==================== AI Unblock Endpoints ====================

@router.post(
    "/unblock",
    response_model=UnblockResponse,
    summary="Get AI unblock suggestion",
    description="Get AI-powered help to unblock a task"
)
async def get_unblock_suggestion(
    request: UnblockRequest,
    current_user: User = Depends(get_current_active_user),
    service: UnblockService = Depends(get_unblock_service)
):
    """Get AI-powered suggestion to unblock."""
    if not has_permission(current_user.role, Permission.AI_USE_ASSISTANT):
        raise ForbiddenException("Not authorized to use AI assistant")

    result = await service.get_unblock_suggestion(
        org_id=current_user.org_id,
        user_id=current_user.id,
        request=request
    )

    return UnblockResponse(**result)


@router.post(
    "/unblock/{session_id}/feedback",
    response_model=UnblockFeedbackResponse,
    summary="Submit feedback",
    description="Submit feedback on AI suggestion"
)
async def submit_feedback(
    session_id: str,
    feedback: UnblockFeedback,
    current_user: User = Depends(get_current_active_user),
    service: UnblockService = Depends(get_unblock_service)
):
    """Submit feedback on an AI suggestion."""
    await service.submit_feedback(
        session_id, current_user.org_id, current_user.id, feedback
    )

    return UnblockFeedbackResponse(session_id=session_id)


@router.get(
    "/unblock/history",
    response_model=UnblockHistoryResponse,
    summary="Get unblock history",
    description="Get history of AI unblock sessions"
)
async def get_unblock_history(
    pagination: PaginationParams = Depends(get_pagination),
    task_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    service: UnblockService = Depends(get_unblock_service)
):
    """Get user's unblock history."""
    sessions, total = await service.get_session_history(
        org_id=current_user.org_id,
        user_id=current_user.id,
        task_id=task_id,
        skip=pagination.skip,
        limit=pagination.limit
    )

    return UnblockHistoryResponse(
        sessions=[
            UnblockSessionResponse(
                id=s.id,
                user_id=s.user_id,
                task_id=s.task_id,
                query=s.query,
                response=s.response,
                confidence=s.confidence,
                sources=s.sources,
                was_helpful=s.was_helpful,
                feedback_text=s.feedback_text,
                escalated=s.escalated,
                created_at=s.created_at
            ) for s in sessions
        ],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size
    )


# ==================== Knowledge Base Status ====================

@router.get(
    "/knowledge-base/status",
    response_model=KnowledgeBaseStatus,
    summary="Get knowledge base status",
    description="Get statistics about the knowledge base"
)
async def get_knowledge_base_status(
    current_user: User = Depends(get_current_active_user),
    service: UnblockService = Depends(get_unblock_service)
):
    """Get knowledge base status."""
    status_data = await service.get_knowledge_base_status(current_user.org_id)
    return KnowledgeBaseStatus(**status_data)


# ==================== Document Management ====================

@router.get(
    "/knowledge-base/documents",
    response_model=DocumentListResponse,
    summary="List documents",
    description="List knowledge base documents"
)
async def list_documents(
    pagination: PaginationParams = Depends(get_pagination),
    source: Optional[DocumentSource] = Query(None),
    doc_type: Optional[DocumentType] = Query(None),
    status_filter: Optional[DocumentStatus] = Query(None, alias="status"),
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    service: UnblockService = Depends(get_unblock_service)
):
    """List documents in knowledge base."""
    docs, total = await service.get_documents(
        org_id=current_user.org_id,
        source=source,
        doc_type=doc_type,
        status=status_filter,
        search=search,
        skip=pagination.skip,
        limit=pagination.limit
    )

    return DocumentListResponse(
        documents=[
            DocumentResponse(
                id=d.id,
                org_id=d.org_id,
                title=d.title,
                description=d.description,
                source=d.source,
                source_url=d.source_url,
                doc_type=d.doc_type,
                status=d.status,
                file_name=d.file_name,
                file_type=d.file_type,
                language=d.language,
                is_public=d.is_public,
                tags=d.tags,
                categories=d.categories,
                view_count=d.view_count,
                helpful_count=d.helpful_count,
                not_helpful_count=d.not_helpful_count,
                processed_at=d.processed_at,
                created_at=d.created_at,
                updated_at=d.updated_at
            ) for d in docs
        ],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size
    )


@router.post(
    "/knowledge-base/documents",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create document",
    description="Add a document to the knowledge base"
)
async def create_document(
    doc_data: DocumentCreate,
    current_user: User = Depends(require_roles(
        UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.MANAGER
    )),
    service: UnblockService = Depends(get_unblock_service)
):
    """Create a new document."""
    if not has_permission(current_user.role, Permission.AI_MANAGE_KNOWLEDGE_BASE):
        raise ForbiddenException("Not authorized to manage knowledge base")

    doc = await service.create_document(current_user.org_id, doc_data)

    return DocumentResponse(
        id=doc.id,
        org_id=doc.org_id,
        title=doc.title,
        description=doc.description,
        source=doc.source,
        source_url=doc.source_url,
        doc_type=doc.doc_type,
        status=doc.status,
        file_name=doc.file_name,
        file_type=doc.file_type,
        language=doc.language,
        is_public=doc.is_public,
        tags=doc.tags,
        categories=doc.categories,
        view_count=doc.view_count,
        helpful_count=doc.helpful_count,
        not_helpful_count=doc.not_helpful_count,
        processed_at=doc.processed_at,
        created_at=doc.created_at,
        updated_at=doc.updated_at
    )


@router.post(
    "/knowledge-base/upload",
    response_model=UploadResponse,
    summary="Upload document",
    description="Upload a file to the knowledge base"
)
async def upload_document(
    file: UploadFile = File(...),
    doc_type: DocumentType = Query(DocumentType.DOCUMENTATION),
    is_public: bool = Query(True),
    current_user: User = Depends(require_roles(
        UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.MANAGER
    )),
    service: UnblockService = Depends(get_unblock_service)
):
    """Upload a file to knowledge base."""
    from app.config import settings as app_settings
    import os

    if not has_permission(current_user.role, Permission.AI_MANAGE_KNOWLEDGE_BASE):
        raise ForbiddenException("Not authorized to upload documents")

    # SEC-007: Validate file extension against allowlist
    filename = file.filename or ""
    file_ext = os.path.splitext(filename)[1].lower()
    if file_ext not in app_settings.ALLOWED_UPLOAD_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"File type '{file_ext}' is not allowed. "
                f"Supported extensions: {', '.join(app_settings.ALLOWED_UPLOAD_EXTENSIONS)}"
            )
        )

    # SEC-007: Read file content with size enforcement
    content = await file.read()

    if len(content) > app_settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size is {app_settings.MAX_UPLOAD_SIZE_MB}MB."
        )

    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty."
        )

    # Decode based on file type
    try:
        text_content = content.decode('utf-8')
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a text file (txt, md, etc.)"
        )

    # Create document
    doc_data = DocumentCreate(
        title=file.filename or "Uploaded Document",
        content=text_content,
        source=DocumentSource.MANUAL_UPLOAD,
        doc_type=doc_type,
        is_public=is_public
    )

    doc = await service.create_document(current_user.org_id, doc_data)
    doc.file_name = file.filename
    doc.file_type = file.content_type
    doc.file_size = len(content)

    await service.db.flush()

    return UploadResponse(
        document_id=doc.id,
        title=doc.title,
        status=doc.status,
        message="Document uploaded and queued for processing"
    )


@router.get(
    "/knowledge-base/documents/{doc_id}",
    response_model=DocumentResponse,
    summary="Get document",
    description="Get a specific document"
)
async def get_document(
    doc_id: str,
    current_user: User = Depends(get_current_active_user),
    service: UnblockService = Depends(get_unblock_service)
):
    """Get a document by ID."""
    doc = await service.get_document(doc_id, current_user.org_id)
    if not doc:
        raise NotFoundException("Document", doc_id)

    # Increment view count
    doc.view_count += 1
    await service.db.flush()

    return DocumentResponse(
        id=doc.id,
        org_id=doc.org_id,
        title=doc.title,
        description=doc.description,
        source=doc.source,
        source_url=doc.source_url,
        doc_type=doc.doc_type,
        status=doc.status,
        file_name=doc.file_name,
        file_type=doc.file_type,
        language=doc.language,
        is_public=doc.is_public,
        tags=doc.tags,
        categories=doc.categories,
        view_count=doc.view_count,
        helpful_count=doc.helpful_count,
        not_helpful_count=doc.not_helpful_count,
        processed_at=doc.processed_at,
        created_at=doc.created_at,
        updated_at=doc.updated_at
    )


@router.patch(
    "/knowledge-base/documents/{doc_id}",
    response_model=DocumentResponse,
    summary="Update document",
    description="Update a document"
)
async def update_document(
    doc_id: str,
    doc_data: DocumentUpdate,
    current_user: User = Depends(require_roles(
        UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.MANAGER
    )),
    service: UnblockService = Depends(get_unblock_service)
):
    """Update a document."""
    if not has_permission(current_user.role, Permission.AI_MANAGE_KNOWLEDGE_BASE):
        raise ForbiddenException("Not authorized to update documents")

    doc = await service.update_document(doc_id, current_user.org_id, doc_data)

    return DocumentResponse(
        id=doc.id,
        org_id=doc.org_id,
        title=doc.title,
        description=doc.description,
        source=doc.source,
        source_url=doc.source_url,
        doc_type=doc.doc_type,
        status=doc.status,
        file_name=doc.file_name,
        file_type=doc.file_type,
        language=doc.language,
        is_public=doc.is_public,
        tags=doc.tags,
        categories=doc.categories,
        view_count=doc.view_count,
        helpful_count=doc.helpful_count,
        not_helpful_count=doc.not_helpful_count,
        processed_at=doc.processed_at,
        created_at=doc.created_at,
        updated_at=doc.updated_at
    )


@router.delete(
    "/knowledge-base/documents/{doc_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete document",
    description="Delete a document from knowledge base"
)
async def delete_document(
    doc_id: str,
    current_user: User = Depends(require_roles(
        UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN
    )),
    service: UnblockService = Depends(get_unblock_service)
):
    """Delete a document."""
    if not has_permission(current_user.role, Permission.AI_MANAGE_KNOWLEDGE_BASE):
        raise ForbiddenException("Not authorized to delete documents")

    await service.delete_document(doc_id, current_user.org_id)
