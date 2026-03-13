"""
TaskPulse - AI Assistant - Storage Service
File upload/download via Supabase Storage
"""

import asyncio
import logging
from typing import Optional, Tuple

from app.config import settings
from app.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)

BUCKET = settings.SUPABASE_STORAGE_BUCKET  # "documents"


class StorageService:
    """Service for file operations via Supabase Storage."""

    def __init__(self):
        self.client = get_supabase_client()

    async def upload_file(
        self,
        org_id: str,
        doc_id: str,
        filename: str,
        content: bytes,
        content_type: str = "application/octet-stream",
    ) -> Tuple[str, str]:
        """
        Upload a file to Supabase Storage.

        Files are stored under ``{org_id}/{doc_id}/{filename}`` so each
        document gets its own namespace and org data is isolated.

        Args:
            org_id: Organization ID (path prefix for isolation)
            doc_id: Document ID (sub-folder)
            filename: Original file name
            content: Raw file bytes
            content_type: MIME type

        Returns:
            Tuple of (storage_path, public_url)
        """
        storage_path = f"{org_id}/{doc_id}/{filename}"

        try:
            await asyncio.to_thread(
                self.client.storage.from_(BUCKET).upload,
                path=storage_path,
                file=content,
                file_options={"content-type": content_type},
            )
        except Exception as exc:
            logger.error("Supabase storage upload failed for %s: %s", storage_path, exc)
            raise

        # Build the public URL (works for public buckets; for private ones
        # callers should use get_signed_url instead).
        public_url = (
            f"{settings.SUPABASE_URL}/storage/v1/object/public/{BUCKET}/{storage_path}"
        )

        logger.info("Uploaded %s (%d bytes) to Supabase Storage", storage_path, len(content))
        return storage_path, public_url

    async def delete_file(self, storage_path: str) -> None:
        """
        Delete a file from Supabase Storage.

        Args:
            storage_path: The path returned by upload_file
        """
        try:
            await asyncio.to_thread(
                self.client.storage.from_(BUCKET).remove,
                [storage_path],
            )
            logger.info("Deleted %s from Supabase Storage", storage_path)
        except Exception as exc:
            logger.warning("Failed to delete %s from storage: %s", storage_path, exc)

    async def get_signed_url(
        self,
        storage_path: str,
        expires_in: int = 3600,
    ) -> str:
        """
        Generate a signed (time-limited) URL for a private file.

        Args:
            storage_path: The path returned by upload_file
            expires_in: Seconds until the URL expires (default 1 hour)

        Returns:
            Signed URL string
        """
        try:
            result = await asyncio.to_thread(
                self.client.storage.from_(BUCKET).create_signed_url,
                storage_path,
                expires_in,
            )
            return result["signedURL"]
        except Exception as exc:
            logger.error("Failed to create signed URL for %s: %s", storage_path, exc)
            raise
