import hashlib
from dataclasses import dataclass
from typing import Any, Sequence
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

DEFAULT_CHUNK_SIZE = 100
DEFAULT_CHUNK_OVERLAP = 20


@dataclass(slots=True)
class IndexedChunk:
    """A normalized text chunk ready for embedding and indexing."""

    id: str
    content: str
    metadata: dict[str, Any]


class TextChunker:
    """Split documents into small, semantically coherent chunks."""

    def __init__(
        self,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    ) -> None:
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            is_separator_regex=False,
        )

    def chunk_documents(self, documents: Sequence[Document]) -> list[IndexedChunk]:
        split_documents = self.splitter.split_documents(list(documents))
        total_chunks = len(split_documents)
        chunks: list[IndexedChunk] = []

        for chunk_index, document in enumerate(split_documents):
            source_url = str(
                document.metadata.get("source")
                or document.metadata.get("url")
                or "unknown-source"
            )
            chunk_id = self._build_chunk_id(
                source_url=source_url, chunk_index=chunk_index
            )
            metadata = {
                **document.metadata,
                "url": source_url,
                "chunkIndex": chunk_index,
                "totalChunks": total_chunks,
            }
            chunks.append(
                IndexedChunk(
                    id=chunk_id,
                    content=document.page_content,
                    metadata=metadata,
                )
            )

        return chunks

    @staticmethod
    def _build_chunk_id(source_url: str, chunk_index: int) -> str:
        source_hash = hashlib.sha256(source_url.encode("utf-8")).hexdigest()[:16]
        return f"{source_hash}-chunk-{chunk_index}"
