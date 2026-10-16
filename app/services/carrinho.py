"""Carrinho guardado na sessão do navegador (não persistido no banco)."""
from decimal import Decimal

from flask import session

from ..extensions import db
from ..models import Produto

MAX_QTD_ITEM = 20  # RN03


def obter():
    return session.setdefault("carrinho", {})


def salvar(carrinho):
    session["carrinho"] = carrinho
    session.modified = True


def limpar():
    session.pop("carrinho", None)


def itens():
    """Lista de dicts {produto, quantidade, subtotal}; descarta itens que ficaram indisponíveis."""
    resultado, limpo = [], {}
    for pid, qtd in obter().items():
        produto = db.session.get(Produto, int(pid))
        if produto and produto.disponivel(1):
            qtd = min(qtd, produto.estoque, MAX_QTD_ITEM)
            limpo[pid] = qtd
            resultado.append({"produto": produto, "quantidade": qtd, "subtotal": Decimal(produto.preco) * qtd})
    if limpo != obter():
        salvar(limpo)
    return resultado


def subtotal(lista):
    return sum((i["subtotal"] for i in lista), Decimal("0.00"))
