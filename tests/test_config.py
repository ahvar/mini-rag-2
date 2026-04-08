from config import Config


class TestConfig(Config):
    TESTING = True
    OPENAI_API_KEY = "openai-api-key"
    PINECONE_API_KEY = "pinecone-api-key"
    PINECONE_INDEX = "rag-tutorial"
    PINECONE_NAMESPACE = "pinecone-namespace"
    OPENAI_FINETUNED_MODEL = "openai-finetuned-model"
    USER_AGENT = "user-agent"
    RAG_TOP_K = 3
