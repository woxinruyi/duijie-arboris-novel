"""
Vector retry service: single entrypoint to compensate failed vector writes.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from .chapter_ingest_service import ChapterIngestionService
from .llm_service import LLMService
from .vector_store_service import VectorStoreService

logger = logging.getLogger(__name__)


class VectorRetryService:
    """Retry vector ingestion for a chapter version. Keeps logic in one place for API and jobs."""

    def __init__(self, *, llm_service: LLMService, vector_store: Optional[VectorStoreService] = None) -> None:
        self.llm_service = llm_service
        self.vector_store = vector_store or VectorStoreService()

    async def retry(
        self,
        *,
        project_id: str,
        chapter_number: int,
        title: str,
        content: str,
        user_id: int,
    ) -> Dict[str, Any]:
        if not content or not content.strip():
            return {"status": "failed", "error": "empty_content"}
        try:
            ingest_service = ChapterIngestionService(llm_service=self.llm_service, vector_store=self.vector_store)
            await ingest_service.ingest_chapter(
                project_id=project_id,
                chapter_number=chapter_number,
                title=title,
                content=content,
                summary=None,
                user_id=user_id,
            )
            return {"status": "updated"}
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.error("向量重试失败: %s", exc)
            return {"status": "failed", "error": str(exc)}
