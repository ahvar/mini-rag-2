import os
from pathlib import Path

from dotenv import load_dotenv

basedir = Path(__file__).resolve().parent
DATA_DIR = basedir / "data"
envfile = basedir / ".env"
load_dotenv(str(envfile))


class Config:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
    PINECONE_INDEX = os.getenv("PINECONE_INDEX")
    PINECONE_NAMESPACE = os.getenv("PINECONE_NAMESPACE")
    OPENAI_FINETUNED_MODEL = os.getenv("OPENAI_FINETUNED_MODEL")
    BASE_MODEL = os.getenv("BASE_MODEL", "gpt-4o-mini-2024-07-18")
    DEFAULT_JSONL_PATH = os.getenv(
        "DEFAULT_JSONL_PATH", str(DATA_DIR / "linkedin_training.jsonl")
    )
    USER_AGENT = os.getenv("USER_AGENT")
    RAG_INITIAL_FETCH = int(os.getenv("RAG_INITIAL_FETCH", "10"))
    RAG_TOP_K = int(os.getenv("RAG_TOP_K", "3"))
