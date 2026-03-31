import os
from pathlib import Path

from dotenv import load_dotenv

basedir = Path(__file__).resolve().parent
envfile = basedir / ".env"
load_dotenv(str(envfile))


class Config:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
    PINECONE_INDEX = os.getenv("PINECONE_INDEX")
    PINECONE_NAMESPACE = os.getenv("PINECONE_NAMESPACE")
    OPENAI_FINETUNED_MODEL = os.getenv("OPENAI_FINETUNED_MODEL")
    USER_AGENT = os.getenv("USER_AGENT")
    RAG_TOP_K = int(os.getenv("RAG_TOP_K", "3"))
