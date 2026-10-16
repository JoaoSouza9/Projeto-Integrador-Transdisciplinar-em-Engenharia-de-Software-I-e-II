from app.extensions import db
from app.models import Pedido
from tests.conftest import login

CARTAO_OK = {"forma": "CARTAO", "numero": "4111111111111111", "nome": "Maria", "cvv": "123"}


def add(client, produto, qtd=1):
    return client.post(f"/carrinho/adicionar/{produto.id}", data={"quantidade": qtd}, follow_redirects=True)


def test_carrinho_adicionar_atualizar_remover(client, produto):
    assert "adicionado" in add(client, produto, 2).get_data(as_text=True)
    assert "R$ 20,00" in client.get("/carrinho/").get_data(as_text=True)
    client.post(f"/carrinho/atualizar/{produto.id}", data={"quantidade": 3})
    assert "R$ 30,00" in client.get("/carrinho/").get_data(as_text=True)
    assert "Item removido" in client.post(f"/carrinho/remover/{produto.id}", follow_redirects=True).get_data(as_text=True)
    assert "vazio" in client.get("/carrinho/").get_data(as_text=True)


def test_carrinho_nao_aceita_quantidade_acima_do_estoque(client, produto):
    assert "indisponível" in add(client, produto, 11).get_data(as_text=True)
    assert "vazio" in client.get("/carrinho/").get_data(as_text=True)


def test_checkout_exige_login(client, produto):
    add(client, produto)
    r = client.get("/checkout")
    assert r.status_code == 302 and "/login" in r.headers["Location"]


def test_checkout_com_carrinho_vazio_redireciona(client, cliente_user):
    login(client)
    assert client.get("/checkout").status_code == 302


def test_fluxo_completo_pix(client, cliente_user, produto):
    login(client)
    add(client, produto, 2)
    r = client.post("/checkout", data={"endereco_id": "novo", "cep": "70000-000", "rua": "Rua A", "numero": "1",
                                       "bairro": "Centro", "cidade": "Brasília", "uf": "DF"})
    assert r.status_code == 302
    pedido = Pedido.query.one()
    assert str(pedido.total) == "30.00" and pedido.frete == 10 and produto.estoque == 8
    r = client.post(f"/pedidos/{pedido.id}/pagar", data={"forma": "PIX"}, follow_redirects=True)
    assert "PIX confirmado" in r.get_data(as_text=True)
    db.session.refresh(pedido)
    assert pedido.status == "CONFIRMADO" and pedido.pagamento.status == "APROVADO"


def test_frete_gratis_acima_de_120(client, cliente_user, produto):
    produto.estoque, produto.preco = 20, 15
    db.session.commit()
    login(client)
    add(client, produto, 10)
    client.post("/checkout", data={"endereco_id": "novo", "cep": "70000000", "rua": "R", "numero": "1",
                                   "bairro": "B", "cidade": "C", "uf": "DF"})
    assert Pedido.query.one().frete == 0


def test_checkout_endereco_invalido(client, cliente_user, produto):
    login(client)
    add(client, produto)
    r = client.post("/checkout", data={"endereco_id": "novo", "cep": "123", "rua": "", "uf": "ZZ"})
    html = r.get_data(as_text=True)
    assert r.status_code == 400 and "CEP deve ter 8 dígitos" in html and "UF válida" in html
    assert Pedido.query.count() == 0


def test_cartao_recusado_mantem_aguardando_e_permite_nova_tentativa(client, cliente_user, produto, endereco):
    login(client)
    add(client, produto)
    client.post("/checkout", data={"endereco_id": str(endereco.id)})
    pedido = Pedido.query.one()
    r = client.post(f"/pedidos/{pedido.id}/pagar", data=dict(CARTAO_OK, numero="4000000000000002"))
    assert r.status_code == 402 and "recusado" in r.get_data(as_text=True)
    db.session.refresh(pedido)
    assert pedido.status == "AGUARDANDO_PAGAMENTO"
    r = client.post(f"/pedidos/{pedido.id}/pagar", data=CARTAO_OK, follow_redirects=True)
    db.session.refresh(pedido)
    assert pedido.status == "CONFIRMADO" and pedido.pagamento.status == "APROVADO"


def test_dados_de_cartao_invalidos(client, cliente_user, produto, endereco):
    login(client)
    add(client, produto)
    client.post("/checkout", data={"endereco_id": str(endereco.id)})
    pedido = Pedido.query.one()
    r = client.post(f"/pedidos/{pedido.id}/pagar", data=dict(CARTAO_OK, numero="1234"))
    assert r.status_code == 400 and "inválidos" in r.get_data(as_text=True)


def test_cliente_cancela_pedido_e_estoque_volta(client, cliente_user, produto, endereco):
    login(client)
    add(client, produto, 3)
    client.post("/checkout", data={"endereco_id": str(endereco.id)})
    pedido = Pedido.query.one()
    assert produto.estoque == 7
    client.post(f"/pedidos/{pedido.id}/cancelar")
    db.session.refresh(pedido)
    assert pedido.status == "CANCELADO" and produto.estoque == 10


def test_cliente_nao_ve_pedido_de_outro(client, cliente_user, produto, endereco):
    from tests.conftest import criar_usuario
    login(client)
    add(client, produto)
    client.post("/checkout", data={"endereco_id": str(endereco.id)})
    pedido = Pedido.query.one()
    client.post("/logout")
    criar_usuario(email="outro@teste.com")
    login(client, "outro@teste.com")
    assert client.get(f"/pedidos/{pedido.id}").status_code == 404
    assert client.post(f"/pedidos/{pedido.id}/cancelar").status_code == 404
