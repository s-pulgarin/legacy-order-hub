"""Ruta del panel web."""

from flask import Blueprint, render_template

bp = Blueprint("home", __name__)


@bp.route("/")
def index():
    """Muestra el panel HTML de OrderHub."""
    return render_template("index.html")
