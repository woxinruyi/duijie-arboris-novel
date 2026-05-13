"""
Contract test: finalize vector update uses a canonical interface and reports status.

This uses a stub vector store and stub llm service to avoid network/db.

Usage:
    PYTHONPATH=backend python3 scripts/contract_finalize_vector_stub.py
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

from app.services.finalize_service import FinalizeService


class StubLLMService:
    async def get_embedding(self, text: str, *, user_id: Optional[int] = None, model: Optional[str] = None) -> List[float]:
        return [0.1, 0.2, 0.3]  # deterministic stub


class StubVectorStore:
    def __init__(self):
        self.add_calls: List[Dict[str, Any]] = []

    async def upsert_chunks(self, records: List[Dict[str, Any]]):
        self.add_calls.extend(records)

    async def upsert_summaries(self, records: List[Dict[str, Any]]):
        self.add_calls.extend(records)

    async def delete_by_chapters(self, project_id: str, chapters: List[int]):
        # noop for stub
        return


async def main():
    llm = StubLLMService()
    vector = StubVectorStore()
    svc = FinalizeService(db=None, llm_service=llm, vector_store_service=vector)  # type: ignore[arg-type]

    status = await svc._update_vector_store(  # pylint: disable=protected-access
        project_id="proj",
        chapter_number=1,
        chapter_text="stub content",
        user_id=1,
    )

    assert status["status"] == "updated", f"vector status unexpected: {status}"
    assert vector.add_calls, "vector store should receive records"
    print("✅ contract_finalize_vector_stub passed")


if __name__ == "__main__":
    asyncio.run(main())
