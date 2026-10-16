from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from ..extensions import db
from ..models import STATUS_PEDIDO, TRANSICOES, Categoria, ItemPedido, Pedido, Produto
from ..utils import admin_required, parse_decimal

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.route("/pedidos")
@admin_required
def pedidos():
    status = request.args.get("status", "")
    consulta = Pedido.query
    if status in STATUS_PEDIDO:
        consulta = consulta.filter_by(status=status)
    lista = consulta.order_by(Pedido.criado_em.desc()).all()
    return render_template("admin/pedidos.html", pedidos=lista, status_atual=status,
                           todos_status=STATUS_PEDIDO, transicoes=TRANSICOES)


@bp.route("/pedidos/<int:pedido_id>/status", methods=["POST"])
@admin_required
def atualizar_status(pedido_id):
    pedido = db.session.get(Pedido, pedido_id) or abort(404)
    novo = request.form.get("status", "")
    if pedido.avancar_status(novo):  # RN09
        db.session.commit()
        flash(f"Pedido #{pedido.id} atualizado para {novo.replace('_', ' ').lower()}.", "sucesso")
    else:
        flash("Transição de status não permitida.", "erro")
    return redirect(url_for("admin.pedidos"))


@bp.route("/produtos")
@admin_required
def produtos():
    return render_template("admin/produtos.html", produtos=Produto.query.order_by(Produto.nome).all())


def _validar_produto(form):
    erros, dados = [], {}
    dados["nome"] = form.get("nome", "").strip()
    dados["descricao"] = form.get("descricao", "").strip()[:300] or None
    dados["imagem_url"] = form.get("imagem_url", "").strip() or None
    preco = parse_decimal(form.get("preco"))
    estoque = form.get("estoque", type=int)
    categoria = db.session.get(Categoria, form.get("categoria_id", type=int) or 0)
    if len(dados["nome"]) < 2:
        erros.append("Informe o nome do produto.")
    if preco is None or preco <= 0:
        erros.append("Preço deve ser maior que zero.")
    if estoque is None or estoque < 0:
        erros.append("Estoque deve ser zero ou mais.")
    if categoria is None:
        erros.append("Selecione uma categoria.")
    dados.update(preco=preco, estoque=estoque, categoria_id=categoria.id if categoria else None,
                 ativo=form.get("ativo") == "on")
    return dados, erros


def _form_produto(produto=None):
    categorias = Categoria.query.order_by(Categoria.nome).all()
    if request.method == "POST":
        dados, erros = _validar_produto(request.form)
        if erros:
            for e in erros:
                flash(e, "erro")
            return render_template("admin/produto_form.html", produto=produto, categorias=categorias, form=request.form), 400
        if produto is None:
            produto = Produto()
            db.session.add(produto)
        for k, v in dados.items():
            setattr(produto, k, v)
        db.session.commit()
        flash("Produto salvo.", "sucesso")
        return redirect(url_for("admin.produtos"))
    return render_template("admin/produto_form.html", produto=produto, categorias=categorias, form={})


@bp.route("/produtos/novo", methods=["GET", "POST"])
@admin_required
def novo_produto():
    return _form_produto()


@bp.route("/produtos/<int:produto_id>/editar", methods=["GET", "POST"])
@admin_required
def editar_produto(produto_id):
    return _form_produto(db.session.get(Produto, produto_id) or abort(404))


@bp.route("/produtos/<int:produto_id>/excluir", methods=["POST"])
@admin_required
def excluir_produto(produto_id):
    produto = db.session.get(Produto, produto_id) or abort(404)
    if ItemPedido.query.filter_by(produto_id=produto.id).first():  # RN12
        produto.ativo = False
        flash("Produto possui pedidos e foi apenas desativado.", "info")
    else:
        db.session.delete(produto)
        flash("Produto excluído.", "info")
    db.session.commit()
    return redirect(url_for("admin.produtos"))
