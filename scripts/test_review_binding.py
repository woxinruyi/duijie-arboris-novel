"""
Tests for version–content–review binding and stale propagation.

Usage:
    PYTHONPATH=backend python3 scripts/test_review_binding.py
"""

import asyncio
import os
from pathlib import Path

os.environ.setdefault("SECRET_KEY", "test")
os.environ.setdefault("OPENAI_API_KEY", "dummy")
os.environ.setdefault("EMBEDDING_BASE_URL", "http://localhost")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./smoke_generate_finalize.db")
os.environ.setdefault("DB_PROVIDER", "sqlite")

from sqlalchemy import select, create_engine  # noqa: E402
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.models import (  # noqa: E402
    Chapter,
    ChapterOutline,
    ChapterSnapshot,
    ChapterVersion,
    ChapterVersionReview,
    NovelProject,
    User,
)
from app.schemas.novel import ChapterGenerationStatus  # noqa: E402
from app.services.finalize_service import FinalizeService  # noqa: E402
from app.services.novel_service import NovelService  # noqa: E402

ASYNC_DB_URL = "sqlite+aiosqlite:///./smoke_generate_finalize.db"
SYNC_DB_URL = "sqlite:///./smoke_generate_finalize.db"
async_engine = create_async_engine(ASYNC_DB_URL)
AsyncSessionLocal = async_sessionmaker(bind=async_engine, expire_on_commit=False)


class StubLLMService:
    async def generate(self, *args, **kwargs):
        return "stubbed"

    async def get_embedding(self, text: str, *, user_id=None, model=None):
        return [0.1, 0.2, 0.3]


async def main():
    db_path = Path("./smoke_generate_finalize.db")
    if db_path.exists():
        db_path.unlink()
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        user = User(username="review-user", hashed_password="x", email="review@example.com")
        session.add(user)
        await session.flush()

        project = NovelProject(id="proj-review", user_id=user.id, title="Review Binding Project")
        outline = ChapterOutline(project_id=project.id, chapter_number=1, title="Chapter 1", summary="Outline summary")
        chapter = Chapter(project_id=project.id, chapter_number=1, status="not_generated")
        session.add_all([project, outline, chapter])
        await session.commit()
        await session.refresh(chapter)

        service = NovelService(session)

        # Create first version + review
        v1_models = await service.replace_chapter_versions(
            chapter,
            ["first draft"],
            metadata=[{"lineage": {"label": "v1"}, "validation": {"ok": True, "action": "accept"}}],
        )
        v1 = v1_models[0]
        reviews_v1 = (
            await session.execute(
                select(ChapterVersionReview).where(ChapterVersionReview.chapter_version_id == v1.id)
            )
        ).scalars().all()
        assert reviews_v1, "v1 should have a review"
        assert reviews_v1[0].content_hash == v1.content_hash
        assert reviews_v1[0].is_stale is False

        # Retry produces new version and stales old review
        v2_models = await service.replace_chapter_versions(
            chapter,
            ["second draft with changes"],
            metadata=[{"lineage": {"label": "v2", "parent_label": "v1"}, "validation": {"ok": True, "action": "accept"}}],
        )
        v2 = v2_models[0]
        assert v1.content_hash != v2.content_hash, "hash must change when text changes"

        refreshed_v1_reviews = (
            await session.execute(
                select(ChapterVersionReview).where(ChapterVersionReview.chapter_version_id == v1.id)
            )
        ).scalars().all()
        assert all(r.is_stale for r in refreshed_v1_reviews), "old reviews must be stale"

        refreshed_v2_reviews = (
            await session.execute(
                select(ChapterVersionReview).where(ChapterVersionReview.chapter_version_id == v2.id)
            )
        ).scalars().all()
        assert refreshed_v2_reviews and refreshed_v2_reviews[0].content_hash == v2.content_hash
        assert refreshed_v2_reviews[0].is_stale is False

        project_id = project.id
        v2_id = v2.id
        v2_content = v2.content
        v2_hash = v2.content_hash

    # Finalize selects v2 and records snapshot with hash using sync engine to avoid greenlet issues
    sync_engine = create_engine(SYNC_DB_URL)
    SyncSession = sessionmaker(bind=sync_engine)
    with SyncSession() as sync_session:
        chapter_row = sync_session.query(Chapter).filter(
            Chapter.project_id == project_id, Chapter.chapter_number == 1
        ).first()
        chapter_row.selected_version_id = v2_id
        chapter_row.status = ChapterGenerationStatus.WAITING_FOR_CONFIRM.value
        sync_session.commit()

        finalize_service = FinalizeService(sync_session, StubLLMService(), vector_store_service=None)
        # Stub out heavy LLM/memory updates to keep the test deterministic and avoid extra DB writes.
        async def _noop(*args, **kwargs):
            return None

        finalize_service._update_global_summary = _noop  # type: ignore[attr-defined]
        finalize_service._update_character_state = _noop  # type: ignore[attr-defined]
        finalize_service._save_character_state = _noop  # type: ignore[attr-defined]
        finalize_service._update_plot_arcs = _noop  # type: ignore[attr-defined]
        finalize_service._generate_chapter_summary = _noop  # type: ignore[attr-defined]
        await finalize_service.finalize_chapter(  # type: ignore[call-arg]
            project_id=project_id,
            chapter_number=1,
            chapter_text=v2_content,
            user_id=1,
            skip_vector_update=True,
            chapter_version_id=v2_id,
        )

        snapshot = (
            sync_session.query(ChapterSnapshot)
            .filter(
                ChapterSnapshot.project_id == project_id,
                ChapterSnapshot.chapter_number == 1,
            )
            .first()
        )
        assert snapshot is not None, "snapshot must be created"
        assert snapshot.version_id == v2_id, "snapshot should bind version_id"
        assert snapshot.content_hash == v2_hash, "snapshot should store content_hash"

        print("✅ review binding and stale propagation passed")

    await async_engine.dispose()


def test_review_binding():
    asyncio.run(main())


if __name__ == "__main__":
    asyncio.run(main())
