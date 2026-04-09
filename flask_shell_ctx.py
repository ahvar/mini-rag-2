from app import create_app
from app.main import routes
from app.main.index_pipeline import IndexingPipeline
from app.main.pinecone_client import PineconeClient
from app.main.polite_scraper import Scraper
from app.main.text_chunker import TextChunker

from app.api import api_selectors

app = create_app()


@app.shell_context_processor
def make_shell_context():
    return {
        "IndexingPipeline": IndexingPipeline,
        "PineconeClient": PineconeClient,
        "Scraper": Scraper,
        "TextChunker": TextChunker,
    }
