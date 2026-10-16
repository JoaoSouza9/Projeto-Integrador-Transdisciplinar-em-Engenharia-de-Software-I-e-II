from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for

from ..extensions import db
from ..models import Endereco, EstoqueInsuficiente, Pagamento, Pedido
from ..services import carrinho as svc
from ..services.frete import calcular_frete
from ..services.pagamento import FORMAS, DadosPagamentoInvalidos, processar
from ..utils import login_required, so_digitos

bp = Blueprint("pedidos", __name__)

UFS = "AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO".split()


def _pedido_do_usuario(pedido_id):
    p = db.session.get(Pedido, pedido_id)
    if not p or p.usuario_id != g.usuario.id:
        abort(404)
    return p


def _endereco_do_form(form):
    """Valida os campos de novo endereço (RN05). Retorna (Endereco|None, erros)."""
    campos = {k: form.get(k, "").strip() for k in ("rua", "numero", "complemento", "bairro", "cidade", "uf")}
    cep = so_digitos(form.get("cep"))
    erros = []
    for k, rotulo in (("rua", "Rua"), ("numero", "Número"), ("bairro", "Bairro"), ("cidade", "Cidade")):
        if not campos[k]:
            erros.append(f"{rotulo} é obrigatório.")
    if len(cep) != 8:
        erros.append("CEP deve ter 8 dígitos.")
    if campos["uf"].upper() not in UFS:
        erros.append("Selecione uma UF válida.")
    if erros:
        return None, erros
    campos["uf"] = campos["uf"].upper()
    return Endereco(usuario=g.usuario, cep=cep, **campos), []


@bp.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    lista = svc.itens()
    if not lista:
        flash("Seu carrinho está vazio.", "aviso")
        return redirect(url_for("catalogo.vitrine"))
    sub = svc.subtotal(lista)
    frete = calcular_frete(sub)
    contexto = dict(itens=lista, subtotal=sub, frete=frete, total=sub + frete, ufs=UFS, form=request.form)

    if request.method == "POST":
        endereco_id = request.form.get("endereco_id", "")
        if endereco_id and endereco_id != "novo":
            endereco = db.session.get(Endereco, int(endereco_id)) if endereco_id.isdigit() else None
            if not endereco or endereco.usuario_id != g.usuario.id:
                flash("Endereço inválido.", "erro")
                return render_template("checkout.html", **contexto), 400
        else:
            endereco, erros = _endereco_do_form(request.form)
            if erros:
                for e in erros:
                    flash(e, "erro")
                return render_template("checkout.html", **contexto), 400
            db.session.add(endereco)
        try:
            pedido = Pedido.criar(g.usuario, endereco, [(i["produto"], i["quantidade"]) for i in lista],
                                  frete, request.form.get("observacao", "").strip()[:200] or None)
            db.session.commit()
        except EstoqueInsuficiente as e:
            db.session.rollback()
            flash(f"{e.produto.nome} não tem mais estoque suficiente. Ajuste o carrinho.", "erro")
            return redirect(url_for("carrinho.ver"))
        svc.limpar()
        flash("Pedido criado! Escolha a forma de pagamento.", "sucesso")
        return redirect(url_for("pedidos.pagar", pedido_id=pedido.id))
    return render_template("checkout.html", **contexto)


@bp.route("/pedidos/<int:pedido_id>/pagar", methods=["GET", "POST"])
@login_required
def pagar(pedido_id):
    pedido = _pedido_do_usuario(pedido_id)
    if pedido.status != "AGUARDANDO_PAGAMENTO":
        flash("Este pedido não está aguardando pagamento.", "aviso")
        return redirect(url_for("pedidos.detalhe", pedido_id=pedido.id))
    if request.method == "POST":
        forma = request.form.get("forma", "")
        try:
            status, msg = processar(forma, pedido.total, request.form)
        except DadosPagamentoInvalidos as e:
            flash(str(e), "erro")
            return render_template("pagamento.html", pedido=pedido, formas=FORMAS), 400
        if pedido.pagamento is None:
            pedido.pagamento = Pagamento(forma=forma, status=status, valor=pedido.total)
        else:
            pedido.pagamento.forma, pedido.pagamento.status = forma, status
        if status in ("APROVADO", "PENDENTE"):
            pedido.avancar_status("CONFIRMADO")
            db.session.commit()
            flash(msg, "sucesso")
            return redirect(url_for("pedidos.detalhe", pedido_id=pedido.id))
        db.session.commit()
        flash(msg, "erro")
        return render_template("pagamento.html", pedido=pedido, formas=FORMAS), 402
    return render_template("pagamento.html", pedido=pedido, formas=FORMAS)


@bp.route("/pedidos")
@login_required
def meus_pedidos():
    pedidos = Pedido.query.filter_by(usuario_id=g.usuario.id).order_by(Pedido.criado_em.desc()).all()
    return render_template("pedidos.html", pedidos=pedidos)


@bp.route("/pedidos/<int:pedido_id>")
@login_required
def detalhe(pedido_id):
    return render_template("pedido_detalhe.html", pedido=_pedido_do_usuario(pedido_id), formas=FORMAS)


@bp.route("/pedidos/<int:pedido_id>/cancelar", methods=["POST"])
@login_required
def cancelar(pedido_id):
    pedido = _pedido_do_usuario(pedido_id)
    if pedido.pode_cancelar() and pedido.avancar_status("CANCELADO"):  # RN10
        db.session.commit()
        flash("Pedido cancelado.", "info")
    else:
        flash("Este pedido não pode mais ser cancelado.", "erro")
    return redirect(url_for("pedidos.detalhe", pedido_id=pedido.id))
