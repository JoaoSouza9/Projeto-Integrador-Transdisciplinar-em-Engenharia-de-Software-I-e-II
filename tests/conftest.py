from decimal import Decimal

import pytest

from app import create_app
from app.config import TestConfig
from app.extensions import db
from app.models import Categoria, Endereco, Produto, Usuario


@pytest.fixture()
def app():
    app = create_app(TestConfig)
    with app.app_context():
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def produto(app):
    cat = Categoria(nome="Clássicos")
    db.session.add(cat)
    db.session.flush()
    p = Produto(categoria_id=cat.id, nome="Baunilha", descricao="Teste", preco=Decimal("10.00"), estoque=10)
    db.session.add(p)
    db.session.commit()
    return p


def criar_usuario(email="cli@teste.com", senha="senha1234", perfil="CLIENTE", nome="Maria Teste"):
    u = Usuario(nome=nome, email=email, perfil=perfil)
    u.definir_senha(senha)
    db.session.add(u)
    db.session.commit()
    return u


@pytest.fixture()
def cliente_user(app):
    return criar_usuario()


@pytest.fixture()
def admin_user(app):
    return criar_usuario(email="admin@teste.com", perfil="ADMIN", nome="Admin")


@pytest.fixture()
def endereco(cliente_user):
    e = Endereco(usuario_id=cliente_user.id, rua="Rua A", numero="10", bairro="Centro",
                 cidade="Brasília", uf="DF", cep="70000000")
    db.session.add(e)
    db.session.commit()
    return e


def login(client, email="cli@teste.com", senha="senha1234"):
    return client.post("/login", data={"email": email, "senha": senha}, follow_redirects=True)
