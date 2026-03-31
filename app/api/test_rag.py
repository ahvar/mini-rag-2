from app.api import bp
from flask import request, url_for, abort


@bp.route("/api/test-rag/<query>", methods=["PUT"])
def test_rag(query):
    pass
