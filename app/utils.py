import functools
import re
import secrets
from decimal import Decimal, InvalidOperation

from flask import abort, current_app, flash, g, redirect, request, session, url_for

from .extensions import db

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def moeda(valor):
    valor = Decimal(valor or 0)
    texto = f"{valor:,.2f}"
    return "R$ " + texto.replace(",", "X").replace(".", ",").replace("X", ".")


def rotulo_status(status):
    return (status or "").replace("_", " ").capitalize()


def so_digitos(texto):
    return re.sub(r"\D", "", texto or "")


def parse_decimal(texto):
    t = (texto or "").strip()
    if "," in t:  # formato brasileiro: 1.234,50
        t = t.replace(".", "").replace(",", ".")
    try:
        d = Decimal(t)
    except InvalidOperation:
        return None
    return d if d.is_finite() else None


def url_segura(destino):
    """Evita open redirect: só aceita caminhos relativos internos."""
    if destino and destino.startswith("/") and not destino.startswith("//"):
        return destino
    return None


def login_required(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        if g.usuario is None:
            flash("Faça login para continuar.", "aviso")
            return redirect(url_for("auth.login", next=request.path))
        return f(*args, **kwargs)
    return wrapper


def admin_required(f):
    @functools.wraps(f)
    @login_required
    def wrapper(*args, **kwargs):
        if not g.usuario.eh_admin():  # RN11
            abort(403)
        return f(*args, **kwargs)
    return wrapper


def registrar_utils(app):
    @app.before_request
    def carregar_usuario_e_csrf():
        from .models import Usuario

        uid = session.get("uid")
        g.usuario = db.session.get(Usuario, uid) if uid else None
        if request.method == "POST" and current_app.config["CSRF_ATIVO"]:
            esperado, enviado = session.get("csrf"), request.form.get("csrf_token", "")
            if not esperado or not secrets.compare_digest(esperado, enviado):
                abort(400)

    @app.context_processor
    def contexto():
        def csrf_token():
            if "csrf" not in session:
                session["csrf"] = secrets.token_hex(16)
            return session["csrf"]

        return {"csrf_token": csrf_token, "usuario": g.get("usuario"),
                "qtd_carrinho": sum(session.get("carrinho", {}).values())}

    app.add_template_filter(moeda, "moeda")
    app.add_template_filter(rotulo_status, "status")
