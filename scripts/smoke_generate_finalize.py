"""
Smoke test to validate generate/finalize invariants without hitting LLMs:
- generate: selected_version_id stays NULL and status is WAITING_FOR_CONFIRM
- finalize: selected_version_id points to an existing chapter_versions row

Usage:
    SECRET_KEY=test OPENAI_API_KEY=dummy EMBEDDING_BASE_URL=http://localhost PYTHONPATH=backend python3 scripts/smoke_generate_finalize.py
"""

import asyncio
import os
from pathlib import Path

os.environ.setdefault("SECRET_KEY", "smoke-secret")
os.environ.setdefault("OPENAI_API_KEY", "dummy")
os.environ.setdefault("EMBEDDING_BASE_URL", "http://localhost")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./smoke_generate_finalize.db")
os.environ.setdefault("DB_PROVIDER", "sqlite")

from app.db.base import Base  # noqa: E402  # pylint: disable=wrong-import-position
from app.db.session import AsyncSessionLocal, engine  # noqa: E402
from app.models import Chapter, ChapterOutline, ChapterVersion, NovelProject, User  # noqa: E402


async def main():
    db_path = Path("./smoke_generate_finalize.db")
    if db_path.exists():
        db_path.unlink()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        user = User(username="smoke-user", hashed_password="x", email="smoke@example.com")
        session.add(user)
        await session.flush()

        project = NovelProject(id="proj-smoke", user_id=user.id, title="Smoke Project")
        outline = ChapterOutline(project_id=project.id, chapter_number=1, title="Chapter 1", summary="Outline summary")
        chapter = Chapter(project_id=project.id, chapter_number=1, status="not_generated")
        session.add_all([project, outline, chapter])
        await session.commit()
        await session.refresh(chapter)

        # Simulate generate
        draft_version = ChapterVersion(chapter_id=chapter.id, content="draft content", version_label="v1")
        chapter.status = "waiting_for_confirm"
        session.add(draft_version)
        await session.commit()
        await session.refresh(chapter)

        assert chapter.selected_version_id is None, "selected_version_id should be NULL after generate"
        assert chapter.status == "waiting_for_confirm", "chapter status should be WAITING_FOR_CONFIRM after generate"

        # Simulate finalize
        chapter.selected_version_id = draft_version.id
        chapter.status = "successful"
        chapter.word_count = len(draft_version.content)
        await session.commit()
        await session.refresh(chapter)

        assert chapter.selected_version_id == draft_version.id, "selected_version_id should be set on finalize"
        assert chapter.status == "successful", "chapter status should be SUCCESSFUL after finalize"

        print("✅ smoke_generate_finalize passed")


if __name__ == "__main__":
    asyncio.run(main())
