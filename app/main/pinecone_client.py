from __future__ import annotations

import asyncio
from typing import Any, Sequence

from pinecone import Pinecone


class PineconeClient:
    """Small adapter around Pinecone index operations."""

    def __init__(self, api_key: str, index_name: str, namespace: str | None = None) -> None:
        self.index_name = index_name
        self.namespace = namespace
        self.index = Pinecone(api_key=api_key).Index(index_name)

    async def upsert_vectors(self, vectors: Sequence[dict[str, Any]]) -> Any:
        return await asyncio.to_thread(
            self.index.upsert,
            vectors=list(vectors),
            namespace=self.namespace,
        )

    def query_vectors(
        self,
        vector: Sequence[float],
        top_k: int = 3,
        include_metadata: bool = True,
    ) -> Any:
        return self.index.query(
            vector=list(vector),
            top_k=top_k,
            include_metadata=include_metadata,
            namespace=self.namespace,
        )

    async def query_vectors_async(
        self,
        vector: Sequence[float],
        top_k: int = 3,
        include_metadata: bool = True,
    ) -> Any:
        return await asyncio.to_thread(
            self.query_vectors,
            vector,
            top_k,
            include_metadata,
        )

    async def fetch_vectors(self, ids: Sequence[str]) -> Any:
        return await asyncio.to_thread(
            self.index.fetch,
            ids=list(ids),
            namespace=self.namespace,
        )
