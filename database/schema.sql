-- Projeto físico do banco de dados · App de vendas de cupcakes · PostgreSQL 14+
-- Executar: psql -U <usuario> -d <banco> -f database/schema.sql

CREATE TABLE IF NOT EXISTS usuarios (
    id          SERIAL PRIMARY KEY,
    nome        VARCHAR(100) NOT NULL,
    email       VARCHAR(120) NOT NULL UNIQUE,
    senha_hash  VARCHAR(255) NOT NULL,
    telefone    VARCHAR(15),
    perfil      VARCHAR(10)  NOT NULL DEFAULT 'CLIENTE' CHECK (perfil IN ('CLIENTE', 'ADMIN')),
    criado_em   TIMESTAMP    NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc')
);

CREATE TABLE IF NOT EXISTS enderecos (
    id           SERIAL PRIMARY KEY,
    usuario_id   INTEGER     NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    rua          VARCHAR(120) NOT NULL,
    numero       VARCHAR(10)  NOT NULL,
    complemento  VARCHAR(60),
    bairro       VARCHAR(60)  NOT NULL,
    cidade       VARCHAR(60)  NOT NULL,
    uf           CHAR(2)      NOT NULL,
    cep          CHAR(8)      NOT NULL CHECK (cep ~ '^[0-9]{8}$')
);
CREATE INDEX IF NOT EXISTS idx_enderecos_usuario ON enderecos(usuario_id);

CREATE TABLE IF NOT EXISTS categorias (
    id    SERIAL PRIMARY KEY,
    nome  VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS produtos (
    id            SERIAL PRIMARY KEY,
    categoria_id  INTEGER       NOT NULL REFERENCES categorias(id),
    nome          VARCHAR(80)   NOT NULL,
    descricao     VARCHAR(300),
    preco         NUMERIC(10,2) NOT NULL CHECK (preco > 0),
    estoque       INTEGER       NOT NULL DEFAULT 0 CHECK (estoque >= 0),
    imagem_url    VARCHAR(255),
    ativo         BOOLEAN       NOT NULL DEFAULT TRUE
);
CREATE INDEX IF NOT EXISTS idx_produtos_categoria ON produtos(categoria_id);

CREATE TABLE IF NOT EXISTS pedidos (
    id           SERIAL PRIMARY KEY,
    usuario_id   INTEGER       NOT NULL REFERENCES usuarios(id),
    endereco_id  INTEGER       NOT NULL REFERENCES enderecos(id),
    status       VARCHAR(25)   NOT NULL DEFAULT 'AGUARDANDO_PAGAMENTO'
                 CHECK (status IN ('AGUARDANDO_PAGAMENTO','CONFIRMADO','EM_PREPARO',
                                   'SAIU_PARA_ENTREGA','ENTREGUE','CANCELADO')),
    subtotal     NUMERIC(10,2) NOT NULL DEFAULT 0,
    frete        NUMERIC(10,2) NOT NULL DEFAULT 0,
    total        NUMERIC(10,2) NOT NULL DEFAULT 0,
    observacao   VARCHAR(200),
    criado_em    TIMESTAMP     NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc')
);
CREATE INDEX IF NOT EXISTS idx_pedidos_usuario ON pedidos(usuario_id);
CREATE INDEX IF NOT EXISTS idx_pedidos_status  ON pedidos(status);

CREATE TABLE IF NOT EXISTS itens_pedido (
    id              SERIAL PRIMARY KEY,
    pedido_id       INTEGER       NOT NULL REFERENCES pedidos(id) ON DELETE CASCADE,
    produto_id      INTEGER       NOT NULL REFERENCES produtos(id),
    quantidade      INTEGER       NOT NULL CHECK (quantidade > 0),
    preco_unitario  NUMERIC(10,2) NOT NULL CHECK (preco_unitario > 0)
);
CREATE INDEX IF NOT EXISTS idx_itens_pedido ON itens_pedido(pedido_id);

CREATE TABLE IF NOT EXISTS pagamentos (
    id         SERIAL PRIMARY KEY,
    pedido_id  INTEGER       NOT NULL UNIQUE REFERENCES pedidos(id) ON DELETE CASCADE,
    forma      VARCHAR(10)   NOT NULL CHECK (forma IN ('PIX','CARTAO','DINHEIRO')),
    status     VARCHAR(10)   NOT NULL DEFAULT 'PENDENTE' CHECK (status IN ('PENDENTE','APROVADO','RECUSADO')),
    valor      NUMERIC(10,2) NOT NULL,
    criado_em  TIMESTAMP     NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc')
);

CREATE TABLE IF NOT EXISTS entregas (
    id           SERIAL PRIMARY KEY,
    pedido_id    INTEGER NOT NULL UNIQUE REFERENCES pedidos(id) ON DELETE CASCADE,
    entregador   VARCHAR(80),
    previsao     DATE,
    entregue_em  TIMESTAMP
);
