"""Camada Model (MVC): entidades persistentes e regras de domínio."""
from datetime import datetime, timezone
from decimal import Decimal

from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db

def agora():
    """Data/hora UTC sem fuso (naive), compatível com as colunas DateTime."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


STATUS_PEDIDO = (
    "AGUARDANDO_PAGAMENTO",
    "CONFIRMADO",
    "EM_PREPARO",
    "SAIU_PARA_ENTREGA",
    "ENTREGUE",
    "CANCELADO",
)

# RN09 - transições de status permitidas
TRANSICOES = {
    "AGUARDANDO_PAGAMENTO": {"CONFIRMADO", "CANCELADO"},
    "CONFIRMADO": {"EM_PREPARO", "CANCELADO"},
    "EM_PREPARO": {"SAIU_PARA_ENTREGA"},
    "SAIU_PARA_ENTREGA": {"ENTREGUE"},
    "ENTREGUE": set(),
    "CANCELADO": set(),
}

# RN10 - o cliente só cancela nestes status
STATUS_CANCELAVEIS = ("AGUARDANDO_PAGAMENTO", "CONFIRMADO")


class EstoqueInsuficiente(Exception):
    def __init__(self, produto):
        super().__init__(f"Estoque insuficiente para {produto.nome}.")
        self.produto = produto


class Usuario(db.Model):
    __tablename__ = "usuarios"
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True, index=True)
    senha_hash = db.Column(db.String(255), nullable=False)
    telefone = db.Column(db.String(15))
    perfil = db.Column(db.String(10), nullable=False, default="CLIENTE")
    criado_em = db.Column(db.DateTime, nullable=False, default=agora)

    enderecos = db.relationship("Endereco", back_populates="usuario", cascade="all, delete-orphan")
    pedidos = db.relationship("Pedido", back_populates="usuario")

    def definir_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def verificar_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)

    def eh_admin(self):
        return self.perfil == "ADMIN"


class Endereco(db.Model):
    __tablename__ = "enderecos"
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    rua = db.Column(db.String(120), nullable=False)
    numero = db.Column(db.String(10), nullable=False)
    complemento = db.Column(db.String(60))
    bairro = db.Column(db.String(60), nullable=False)
    cidade = db.Column(db.String(60), nullable=False)
    uf = db.Column(db.String(2), nullable=False)
    cep = db.Column(db.String(8), nullable=False)

    usuario = db.relationship("Usuario", back_populates="enderecos")

    def resumo(self):
        comp = f" - {self.complemento}" if self.complemento else ""
        return f"{self.rua}, {self.numero}{comp}, {self.bairro}, {self.cidade}/{self.uf} - CEP {self.cep[:5]}-{self.cep[5:]}"


class Categoria(db.Model):
    __tablename__ = "categorias"
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False, unique=True)

    produtos = db.relationship("Produto", back_populates="categoria")


class Produto(db.Model):
    __tablename__ = "produtos"
    id = db.Column(db.Integer, primary_key=True)
    categoria_id = db.Column(db.Integer, db.ForeignKey("categorias.id"), nullable=False)
    nome = db.Column(db.String(80), nullable=False)
    descricao = db.Column(db.String(300))
    preco = db.Column(db.Numeric(10, 2), nullable=False)
    estoque = db.Column(db.Integer, nullable=False, default=0)
    imagem_url = db.Column(db.String(255))
    ativo = db.Column(db.Boolean, nullable=False, default=True)

    categoria = db.relationship("Categoria", back_populates="produtos")

    def disponivel(self, qtd=1):
        return bool(self.ativo) and self.estoque >= qtd


class Pedido(db.Model):
    __tablename__ = "pedidos"
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    endereco_id = db.Column(db.Integer, db.ForeignKey("enderecos.id"), nullable=False)
    status = db.Column(db.String(25), nullable=False, default="AGUARDANDO_PAGAMENTO")
    subtotal = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    frete = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    total = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    observacao = db.Column(db.String(200))
    criado_em = db.Column(db.DateTime, nullable=False, default=agora)

    usuario = db.relationship("Usuario", back_populates="pedidos")
    endereco = db.relationship("Endereco")
    itens = db.relationship("ItemPedido", back_populates="pedido", cascade="all, delete-orphan")
    pagamento = db.relationship("Pagamento", back_populates="pedido", uselist=False, cascade="all, delete-orphan")
    entrega = db.relationship("Entrega", back_populates="pedido", uselist=False, cascade="all, delete-orphan")

    @classmethod
    def criar(cls, usuario, endereco, itens, frete, observacao=None):
        """Cria o pedido reservando o estoque (RN06). `itens` = [(Produto, quantidade)]."""
        with db.session.no_autoflush:
            pedido = cls(usuario=usuario, endereco=endereco, frete=Decimal(frete),
                         observacao=observacao, status="AGUARDANDO_PAGAMENTO")
            for produto, qtd in itens:
                if not produto.disponivel(qtd):
                    raise EstoqueInsuficiente(produto)
                produto.estoque -= qtd
                pedido.itens.append(ItemPedido(produto=produto, quantidade=qtd, preco_unitario=produto.preco))
        pedido.calcular_totais()
        db.session.add(pedido)
        return pedido

    def calcular_totais(self):
        self.subtotal = sum((i.subtotal() for i in self.itens), Decimal("0.00"))
        self.total = self.subtotal + Decimal(self.frete or 0)

    def pode_cancelar(self):
        return self.status in STATUS_CANCELAVEIS

    def avancar_status(self, novo):
        """Aplica a transição se permitida (RN09). Não faz commit."""
        if novo not in TRANSICOES.get(self.status, set()):
            return False
        self.status = novo
        if novo == "CANCELADO":
            for item in self.itens:  # devolve o estoque reservado (RN06)
                item.produto.estoque += item.quantidade
        if novo == "ENTREGUE":
            if self.entrega is None:
                self.entrega = Entrega()
            self.entrega.entregue_em = agora()
            if self.pagamento and self.pagamento.forma == "DINHEIRO":
                self.pagamento.status = "APROVADO"
        return True


class ItemPedido(db.Model):
    __tablename__ = "itens_pedido"
    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey("pedidos.id"), nullable=False)
    produto_id = db.Column(db.Integer, db.ForeignKey("produtos.id"), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    preco_unitario = db.Column(db.Numeric(10, 2), nullable=False)

    pedido = db.relationship("Pedido", back_populates="itens")
    produto = db.relationship("Produto")

    def subtotal(self):
        return Decimal(self.preco_unitario) * self.quantidade


class Pagamento(db.Model):
    __tablename__ = "pagamentos"
    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey("pedidos.id"), nullable=False, unique=True)
    forma = db.Column(db.String(10), nullable=False)
    status = db.Column(db.String(10), nullable=False, default="PENDENTE")
    valor = db.Column(db.Numeric(10, 2), nullable=False)
    criado_em = db.Column(db.DateTime, nullable=False, default=agora)

    pedido = db.relationship("Pedido", back_populates="pagamento")


class Entrega(db.Model):
    __tablename__ = "entregas"
    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey("pedidos.id"), nullable=False, unique=True)
    entregador = db.Column(db.String(80))
    previsao = db.Column(db.Date)
    entregue_em = db.Column(db.DateTime)

    pedido = db.relationship("Pedido", back_populates="entrega")
