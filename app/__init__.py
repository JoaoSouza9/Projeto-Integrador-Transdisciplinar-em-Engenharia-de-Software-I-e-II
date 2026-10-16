from flask import Flask, render_template

from .config import Config
from .extensions import db
from .utils import registrar_utils


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    db.init_app(app)
    registrar_utils(app)

    from .controllers import admin, auth, carrinho, catalogo, pedidos

    for modulo in (auth, catalogo, carrinho, pedidos, admin):
        app.register_blueprint(modulo.bp)

    def erro(codigo, titulo, mensagem):
        def handler(_e):
            return render_template("erro.html", codigo=codigo, titulo=titulo, mensagem=mensagem), codigo
        return handler

    app.register_error_handler(400, erro(400, "Requisição inválida", "Sua sessão expirou ou o formulário é inválido. Volte e tente novamente."))
    app.register_error_handler(403, erro(403, "Acesso negado", "Você não tem permissão para acessar esta página."))
    app.register_error_handler(404, erro(404, "Página não encontrada", "Não encontramos o que você procura."))
    app.register_error_handler(500, erro(500, "Erro inesperado", "Algo deu errado do nosso lado. Tente novamente em instantes."))

    with app.app_context():
        db.create_all()
    return app
