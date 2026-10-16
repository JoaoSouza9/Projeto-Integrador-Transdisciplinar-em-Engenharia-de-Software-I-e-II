from app.models import Usuario
from tests.conftest import login


def cadastro(client, **sobrescrever):
    dados = {"nome": "Ana Souza", "email": "ana@teste.com", "senha": "senha1234", "confirmar": "senha1234"}
    dados.update(sobrescrever)
    return client.post("/cadastro", data=dados, follow_redirects=True)


def test_cadastro_com_sucesso(client):
    r = cadastro(client)
    assert r.status_code == 200 and "Cadastro realizado" in r.get_data(as_text=True)
    assert Usuario.query.filter_by(email="ana@teste.com").one()


def test_cadastro_email_duplicado(client):
    cadastro(client)
    r = cadastro(client)
    assert r.status_code == 400 and "já está cadastrado" in r.get_data(as_text=True)


def test_cadastro_senha_curta_e_email_invalido(client):
    r = cadastro(client, senha="123", confirmar="123", email="xx")
    html = r.get_data(as_text=True)
    assert r.status_code == 400 and "mínimo 8" in html and "e-mail válido" in html


def test_login_e_logout(client, cliente_user):
    assert "Olá, Maria" in login(client).get_data(as_text=True)
    r = client.post("/logout", follow_redirects=True)
    assert "Você saiu" in r.get_data(as_text=True)


def test_login_invalido(client, cliente_user):
    r = client.post("/login", data={"email": "cli@teste.com", "senha": "errada"})
    assert r.status_code == 401 and "incorretos" in r.get_data(as_text=True)


def test_login_nao_redireciona_para_site_externo(client, cliente_user):
    r = client.post("/login?next=//evil.com", data={"email": "cli@teste.com", "senha": "senha1234"})
    assert r.headers["Location"] == "/"


def test_vitrine_lista_busca_e_oculta_esgotados(client, produto):
    assert "Baunilha" in client.get("/").get_data(as_text=True)
    assert "Baunilha" not in client.get("/?q=zzz").get_data(as_text=True)
    produto.estoque = 0
    from app.extensions import db
    db.session.commit()
    assert "Baunilha" not in client.get("/").get_data(as_text=True)       # RN02
    assert "esgotado" in client.get(f"/produto/{produto.id}").get_data(as_text=True)


def test_produto_inexistente_404(client):
    assert client.get("/produto/999").status_code == 404
