from app.main import bp
from flask import render_template, flash, redirect, url_for, request, current_app


@bp.route("/", methods=["GET", "POST"])
@bp.route("/index", methods=["GET", "POST"])
def index():
    return "Hello, World!"
