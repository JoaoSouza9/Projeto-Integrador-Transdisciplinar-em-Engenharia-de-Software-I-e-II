"""Popula o banco com categorias, cupcakes de exemplo e um administrador.

Uso:  python seed.py
Variáveis opcionais: ADMIN_EMAIL, ADMIN_SENHA (troque a senha padrão em produção!).
"""
import os
from decimal import Decimal

from app import create_app
from app.extensions import db
from app.models import Categoria, Produto, Usuario

CATALOGO = {
    "Clássicos": [("Baunilha com Buttercream", "Massa fofinha de baunilha e cobertura cremosa.", "7.50", 30),
                  ("Chocolate Intenso", "Massa de chocolate com ganache.", "8.00", 30)],
    "Recheados": [("Red Velvet", "Massa aveludada com recheio de cream cheese.", "9.50", 25),
                  ("Brigadeiro Gourmet", "Recheio de brigadeiro belga e granulado.", "9.00", 25)],
    "Veganos": [("Cenoura Vegano", "Sem ingredientes de origem animal, cobertura de chocolate.", "8.50", 20),
                ("Limão Siciliano Vegano", "Cítrico e leve.", "8.50", 20)],
    "Premium": [("Pistache Premium", "Pasta de pistache e farofa crocante.", "12.00", 15),
                ("Frutas Vermelhas", "Geleia artesanal e chantilly.", "11.00", 15)],
}


def popular():
    for nome_cat, produtos in CATALOGO.items():
        cat = Categoria.query.filter_by(nome=nome_cat).first() or Categoria(nome=nome_cat)
        db.session.add(cat)
        db.session.flush()
        for nome, desc, preco, estoque in produtos:
            if not Produto.query.filter_by(nome=nome).first():
                db.session.add(Produto(categoria_id=cat.id, nome=nome, descricao=desc, preco=Decimal(preco), estoque=estoque))
    email = os.environ.get("ADMIN_EMAIL", "admin@cupcakes.local")
    if not Usuario.query.filter_by(email=email).first():
        admin = Usuario(nome="Administrador", email=email, perfil="ADMIN")
        admin.definir_senha(os.environ.get("ADMIN_SENHA", "admin12345"))
        db.session.add(admin)
    db.session.commit()


if __name__ == "__main__":
    with create_app().app_context():
        popular()
        print("Banco populado. Admin:", os.environ.get("ADMIN_EMAIL", "admin@cupcakes.local"))
