from app import create_app
from app.main import routes
from app.api import test_rag

app = create_app()


@app.shell_context_processor
def make_shell_context():
    return {}
