"""
Stub test for the vector retry single-entry service.

Usage:
    PYTHONPATH=backend python3 scripts/test_vector_retry_stub.py
"""

from __future__ import annotations

import asyncio

from app.services.vector_retry_service import VectorRetryService


class StubLLM:
    async def get_embedding(self, text: str, *, user_id: int | None = None, model: str | None = None):
        return [0.1, 0.2, 0.3]


class StubVectorStore:
    def __init__(self):
        self.chunks = []

    async def delete_by_chapters(self, project_id: str, chapters):
        return

    async def upsert_chunks(self, records):
        self.chunks.extend(records)

    async def upsert_summaries(self, records):
        self.chunks.extend(records)


async def main():
    service = VectorRetryService(llm_service=StubLLM(), vector_store=StubVectorStore())  # type: ignore[arg-type]
    status = await service.retry(
        project_id="p1",
        chapter_number=1,
        title="第1章",
        content="这里是正文，用于切分和向量化。",
        user_id=1,
    )
    assert status["status"] == "updated", f"retry status unexpected: {status}"
    print("✅ test_vector_retry_stub passed")


def test_vector_retry_stub():
    asyncio.run(main())


if __name__ == "__main__":
    asyncio.run(main())
