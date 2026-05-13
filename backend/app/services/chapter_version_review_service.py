"""Service helpers for chapter version review binding and stale handling."""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Sequence

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import ChapterVersion, ChapterVersionReview

logger = logging.getLogger(__name__)


class ChapterVersionReviewService:
    """Ensure reviews are tied to content_hash and stale when text changes."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def mark_stale_for_other_versions(
        self,
        *,
        chapter_id: int,
        new_hash: str,
        exclude_version_id: int,
    ) -> None:
        """Mark reviews for sibling versions (different hash) as stale."""
        sibling_ids = select(ChapterVersion.id).where(
            ChapterVersion.chapter_id == chapter_id,
            ChapterVersion.id != exclude_version_id,
            ChapterVersion.content_hash != new_hash,
        )
        stmt = (
            update(ChapterVersionReview)
            .where(
                ChapterVersionReview.is_stale.is_(False),
                ChapterVersionReview.chapter_version_id.in_(sibling_ids),
            )
            .values(is_stale=True)
        )
        result = await self.session.execute(stmt)
        if result.rowcount:
            logger.info("Marked %s reviews as stale for chapter_id=%s", result.rowcount, chapter_id)

    async def create_review(
        self,
        *,
        version_id: int,
        content_hash: str,
        review_type: str,
        payload: Optional[Dict[str, Any]],
    ) -> ChapterVersionReview:
        review = ChapterVersionReview(
            chapter_version_id=version_id,
            content_hash=content_hash,
            is_stale=False,
            review_type=review_type,
            payload_json=payload or {},
        )
        self.session.add(review)
        await self.session.flush()
        return review

    async def bulk_create_reviews(
        self,
        *,
        version_id: int,
        content_hash: str,
        reviews: Sequence[Dict[str, Any]],
    ) -> None:
        """Create multiple reviews for a version."""
        for item in reviews:
            await self.create_review(
                version_id=version_id,
                content_hash=content_hash,
                review_type=item.get("review_type") or "validator",
                payload=item.get("payload"),
            )
