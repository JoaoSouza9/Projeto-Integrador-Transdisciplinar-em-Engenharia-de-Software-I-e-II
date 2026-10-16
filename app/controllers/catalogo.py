from flask import Blueprint, abort, render_template, request

from ..extensions import db
from ..models import Categoria, Produto

bp = Blueprint("catalogo", __name__)


@bp.route("/")
def vitrine():
    q = request.args.get("q", "").strip()
    categoria_id = request.args.get("categoria", type=int)
    consulta = Produto.query.filter(Produto.ativo.is_(True), Produto.estoque > 0)  # RN02
    if q:
        consulta = consulta.filter(Produto.nome.ilike(f"%{q}%"))
    if categoria_id:
        consulta = consulta.filter(Produto.categoria_id == categoria_id)
    produtos = consulta.order_by(Produto.nome).all()
    categorias = Categoria.query.order_by(Categoria.nome).all()
    return render_template("index.html", produtos=produtos, categorias=categorias, q=q, categoria_id=categoria_id)


@bp.route("/produto/<int:produto_id>")
def detalhe(produto_id):
    produto = db.session.get(Produto, produto_id)
    if not produto or not produto.ativo:
        abort(404)
    return render_template("produto.html", produto=produto)
