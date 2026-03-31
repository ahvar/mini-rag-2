from __future__ import annotations

from flask import jsonify
from langchain_openai import OpenAIEmbeddings

from app.api import bp
from app.main.pinecone_client import PineconeClient
from config import Config

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 512


@bp.route("/api/test-rag/<query>", methods=["PUT"])
def test_rag(query: str):
    embeddings_client = OpenAIEmbeddings(
        model=EMBEDDING_MODEL,
        dimensions=EMBEDDING_DIMENSIONS,
        api_key=Config.OPENAI_API_KEY,
    )
    query_embedding = embeddings_client.embed_query(query)

    pinecone_client = PineconeClient(
        api_key=Config.PINECONE_API_KEY,
        index_name=Config.PINECONE_INDEX,
        namespace=Config.PINECONE_NAMESPACE,
    )

    query_response = pinecone_client.query_vectors(
        vector=query_embedding,
        top_k=Config.RAG_TOP_K,
        include_metadata=True,
    )
    matches = getattr(query_response, "matches", None)
    if matches is None and isinstance(query_response, dict):
        matches = query_response.get("matches", [])

    result = [
        {
            "id": match.get("id") if isinstance(match, dict) else getattr(match, "id", None),
            "score": match.get("score") if isinstance(match, dict) else getattr(match, "score", None),
            "metadata": match.get("metadata") if isinstance(match, dict) else getattr(match, "metadata", {}),
        }
        for match in (matches or [])
    ]
    return jsonify(result)
