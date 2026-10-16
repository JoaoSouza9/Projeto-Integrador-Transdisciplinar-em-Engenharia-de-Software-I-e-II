from decimal import Decimal

import pytest

from app.extensions import db
from app.models import EstoqueInsuficiente, Pedido


def test_senha_e_armazenada_com_hash(cliente_user):
    assert cliente_user.senha_hash != "senha1234"
    assert cliente_user.verificar_senha("senha1234")
    assert not cliente_user.verificar_senha("outra")


def test_criar_pedido_reserva_estoque_e_calcula_total(cliente_user, endereco, produto):
    pedido = Pedido.criar(cliente_user, endereco, [(produto, 3)], Decimal("10.00"))
    db.session.commit()
    assert produto.estoque == 7
    assert pedido.subtotal == Decimal("30.00")
    assert pedido.total == Decimal("40.00")
    assert pedido.status == "AGUARDANDO_PAGAMENTO"


def test_estoque_insuficiente_levanta_excecao(cliente_user, endereco, produto):
    with pytest.raises(EstoqueInsuficiente):
        Pedido.criar(cliente_user, endereco, [(produto, 11)], Decimal("10.00"))


def test_transicoes_validas_e_invalidas(cliente_user, endereco, produto):
    pedido = Pedido.criar(cliente_user, endereco, [(produto, 1)], Decimal("0"))
    assert not pedido.avancar_status("ENTREGUE")          # pula etapas
    assert pedido.avancar_status("CONFIRMADO")
    assert pedido.avancar_status("EM_PREPARO")
    assert not pedido.pode_cancelar()                      # RN10
    assert pedido.avancar_status("SAIU_PARA_ENTREGA")
    assert pedido.avancar_status("ENTREGUE")
    assert pedido.entrega.entregue_em is not None
    assert not pedido.avancar_status("CANCELADO")


def test_cancelar_devolve_estoque(cliente_user, endereco, produto):
    pedido = Pedido.criar(cliente_user, endereco, [(produto, 4)], Decimal("0"))
    assert produto.estoque == 6
    assert pedido.avancar_status("CANCELADO")
    assert produto.estoque == 10
