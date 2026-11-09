"""Rutas de la interfaz web: páginas HTML y panel técnico de pruebas.

Las páginas solo sirven HTML; los datos los piden al API desde el navegador
con el JWT de la sesión. La protección real está en la API (401/403): ocultar
un menú en la interfaz no es un control de seguridad.
"""

from flask import Blueprint, redirect, render_template, url_for

bp = Blueprint("home", __name__)


@bp.route("/")
def index():
    """La raíz lleva al inicio de sesión (o al catálogo si ya hay sesión)."""
    return redirect(url_for("home.login"))


@bp.route("/login")
def login():
    """Página de inicio de sesión."""
    return render_template("login.html")


@bp.route("/registro")
def register():
    """Página de registro de usuarios (rol client)."""
    return render_template("register.html")


@bp.route("/catalogo")
def catalog():
    """Catálogo de productos con compra directa."""
    return render_template("catalog.html")


@bp.route("/ordenes")
def orders():
    """Órdenes del usuario (el admin puede ver todas)."""
    return render_template("orders.html")


@bp.route("/admin/productos")
def admin_products():
    """Administración del catálogo (solo admin)."""
    return render_template("admin_products.html")


@bp.route("/dev")
def dev_panel():
    """Panel técnico para probar la API (401/403, token manipulado...)."""
    return render_template("dev.html")
