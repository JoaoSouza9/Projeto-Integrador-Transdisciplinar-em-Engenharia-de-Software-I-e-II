from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from ..extensions import db
from ..models import Produto
from ..services import carrinho as svc
from ..services.frete import calcular_frete

bp = Blueprint("carrinho", __name__, url_prefix="/carrinho")


def _produto_ou_404(pid):
    p = db.session.get(Produto, pid)
    if not p or not p.ativo:
        abort(404)
    return p


def _qtd_valida(produto, qtd):
    """RN03: 1 até min(estoque, limite por item)."""
    limite = min(produto.estoque, svc.MAX_QTD_ITEM)
    return 1 <= qtd <= limite, limite


@bp.route("/")
def ver():
    lista = svc.itens()
    sub = svc.subtotal(lista)
    frete = calcular_frete(sub)
    return render_template("carrinho.html", itens=lista, subtotal=sub, frete=frete, total=sub + frete)


@bp.route("/adicionar/<int:produto_id>", methods=["POST"])
def adicionar(produto_id):
    produto = _produto_ou_404(produto_id)
    qtd = request.form.get("quantidade", 1, type=int)
    cart = svc.obter()
    nova = cart.get(str(produto_id), 0) + qtd
    ok, limite = _qtd_valida(produto, nova)
    if not ok:
        flash(f"Quantidade indisponível. Máximo para {produto.nome}: {limite}.", "erro")
        return redirect(request.referrer or url_for("catalogo.vitrine"))
    cart[str(produto_id)] = nova
    svc.salvar(cart)
    flash(f"{produto.nome} adicionado ao carrinho.", "sucesso")
    return redirect(url_for("carrinho.ver"))


@bp.route("/atualizar/<int:produto_id>", methods=["POST"])
def atualizar(produto_id):
    produto = _produto_ou_404(produto_id)
    qtd = request.form.get("quantidade", type=int)
    cart = svc.obter()
    if str(produto_id) in cart and qtd is not None:
        ok, limite = _qtd_valida(produto, qtd)
        if ok:
            cart[str(produto_id)] = qtd
            svc.salvar(cart)
        else:
            flash(f"Quantidade inválida. Escolha de 1 a {limite}.", "erro")
    return redirect(url_for("carrinho.ver"))


@bp.route("/remover/<int:produto_id>", methods=["POST"])
def remover(produto_id):
    cart = svc.obter()
    if cart.pop(str(produto_id), None) is not None:
        svc.salvar(cart)
        flash("Item removido do carrinho.", "info")
    return redirect(url_for("carrinho.ver"))
