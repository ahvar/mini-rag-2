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
    OPENAI_FINETUNED_MODEL = os.getenv("OPENAI_FINETUNED_MODEL")
    USER_AGENT = os.getenv("USER_AGENT")
