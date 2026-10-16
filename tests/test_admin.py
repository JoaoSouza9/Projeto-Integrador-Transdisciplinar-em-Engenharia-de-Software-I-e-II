from decimal import Decimal

from app.extensions import db
from app.models import Pedido, Produto
from tests.conftest import login


def test_area_admin_bloqueada_para_visitante_e_cliente(client, cliente_user):
    assert client.get("/admin/pedidos").status_code == 302      # sem login
    login(client)
    assert client.get("/admin/pedidos").status_code == 403      # RN11
    assert client.get("/admin/produtos").status_code == 403


def test_admin_atualiza_status_ate_entregar(client, admin_user, cliente_user, produto, endereco):
    pedido = Pedido.criar(cliente_user, endereco, [(produto, 1)], Decimal("0"))
    db.session.commit()
    login(client, "admin@teste.com")
    for novo in ("CONFIRMADO", "EM_PREPARO", "SAIU_PARA_ENTREGA", "ENTREGUE"):
        client.post(f"/admin/pedidos/{pedido.id}/status", data={"status": novo})
    db.session.refresh(pedido)
    assert pedido.status == "ENTREGUE"


def test_admin_nao_pode_pular_status(client, admin_user, cliente_user, produto, endereco):
    pedido = Pedido.criar(cliente_user, endereco, [(produto, 1)], Decimal("0"))
    db.session.commit()
    login(client, "admin@teste.com")
    r = client.post(f"/admin/pedidos/{pedido.id}/status", data={"status": "ENTREGUE"}, follow_redirects=True)
    assert "não permitida" in r.get_data(as_text=True)
    db.session.refresh(pedido)
    assert pedido.status == "AGUARDANDO_PAGAMENTO"


def test_admin_crud_produto(client, admin_user, produto):
    login(client, "admin@teste.com")
    dados = {"nome": "Novo", "descricao": "d", "categoria_id": produto.categoria_id, "preco": "9,90",
             "estoque": "5", "ativo": "on"}
    assert client.post("/admin/produtos/novo", data=dados).status_code == 302
    novo = Produto.query.filter_by(nome="Novo").one()
    assert novo.preco == Decimal("9.90")
    client.post(f"/admin/produtos/{novo.id}/editar", data=dict(dados, preco="11.50"))
    db.session.refresh(novo)
    assert novo.preco == Decimal("11.50")
    client.post(f"/admin/produtos/{novo.id}/excluir")
    assert Produto.query.filter_by(nome="Novo").first() is None


def test_admin_produto_invalido(client, admin_user, produto):
    login(client, "admin@teste.com")
    r = client.post("/admin/produtos/novo", data={"nome": "", "preco": "-1", "estoque": "x", "categoria_id": 999})
    html = r.get_data(as_text=True)
    assert r.status_code == 400 and "maior que zero" in html and "categoria" in html.lower()


def test_produto_com_pedido_e_apenas_desativado(client, admin_user, cliente_user, produto, endereco):
    Pedido.criar(cliente_user, endereco, [(produto, 1)], Decimal("0"))
    db.session.commit()
    login(client, "admin@teste.com")
    client.post(f"/admin/produtos/{produto.id}/excluir")
    db.session.refresh(produto)
    assert produto.ativo is False                                 # RN12
