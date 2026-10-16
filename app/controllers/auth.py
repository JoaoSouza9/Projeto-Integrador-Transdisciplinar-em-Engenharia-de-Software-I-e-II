from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from ..extensions import db
from ..models import Usuario
from ..utils import EMAIL_RE, so_digitos, url_segura

bp = Blueprint("auth", __name__)


@bp.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        email = request.form.get("email", "").strip().lower()
        telefone = so_digitos(request.form.get("telefone"))
        senha, confirmar = request.form.get("senha", ""), request.form.get("confirmar", "")
        erros = []
        if len(nome) < 3:
            erros.append("Informe seu nome completo.")
        if not EMAIL_RE.match(email):
            erros.append("Informe um e-mail válido.")
        elif Usuario.query.filter_by(email=email).first():  # RN01
            erros.append("Este e-mail já está cadastrado.")
        if len(senha) < 8:  # RN01
            erros.append("A senha deve ter no mínimo 8 caracteres.")
        if senha != confirmar:
            erros.append("A confirmação de senha não confere.")
        if telefone and len(telefone) not in (10, 11):
            erros.append("Telefone deve ter DDD + 8 ou 9 dígitos.")
        if erros:
            for e in erros:
                flash(e, "erro")
            return render_template("cadastro.html", form=request.form), 400
        u = Usuario(nome=nome, email=email, telefone=telefone or None)
        u.definir_senha(senha)
        db.session.add(u)
        db.session.commit()
        session.clear()
        session["uid"] = u.id
        flash("Cadastro realizado! Bem-vindo(a).", "sucesso")
        return redirect(url_for("catalogo.vitrine"))
    return render_template("cadastro.html", form={})


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        u = Usuario.query.filter_by(email=email).first()
        if u and u.verificar_senha(request.form.get("senha", "")):
            destino = url_segura(request.args.get("next"))
            session.clear()
            session["uid"] = u.id
            flash(f"Olá, {u.nome.split()[0]}!", "sucesso")
            return redirect(destino or url_for("catalogo.vitrine"))
        flash("E-mail ou senha incorretos.", "erro")
        return render_template("login.html", email=email), 401
    return render_template("login.html", email="")


@bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("Você saiu da sua conta.", "info")
    return redirect(url_for("catalogo.vitrine"))
