# Dicionário de dados

Banco: PostgreSQL (produção) · SQLite (desenvolvimento e testes). Script: `database/schema.sql`.


## categorias

Agrupamento dos cupcakes na vitrine.

| Coluna | Tipo | Chave | Nulo? | Descrição |
|---|---|---|---|---|
| id | INTEGER | PK | Não | Identificador da categoria. |
| nome | VARCHAR(50) | UK | Não | Nome único da categoria. |

## usuarios

Pessoas que acessam o sistema (clientes e administradores).

| Coluna | Tipo | Chave | Nulo? | Descrição |
|---|---|---|---|---|
| id | INTEGER | PK | Não | Identificador único do usuário. |
| nome | VARCHAR(100) |  | Não | Nome completo. |
| email | VARCHAR(120) | UK | Não | E-mail de acesso, único e armazenado em minúsculas (RN01). |
| senha_hash | VARCHAR(255) |  | Não | Hash da senha (nunca a senha em texto puro). |
| telefone | VARCHAR(15) |  | Sim | Telefone com DDD, apenas dígitos (opcional). |
| perfil | VARCHAR(10) |  | Não | CLIENTE ou ADMIN (RN11). |
| criado_em | DATETIME |  | Não | Data/hora (UTC) do cadastro. |

## enderecos

Endereços de entrega informados pelo cliente.

| Coluna | Tipo | Chave | Nulo? | Descrição |
|---|---|---|---|---|
| id | INTEGER | PK | Não | Identificador do endereço. |
| usuario_id | INTEGER | FK | Não | Dono do endereço (FK usuarios). |
| rua | VARCHAR(120) |  | Não | Logradouro. |
| numero | VARCHAR(10) |  | Não | Número. |
| complemento | VARCHAR(60) |  | Sim | Complemento (opcional). |
| bairro | VARCHAR(60) |  | Não | Bairro. |
| cidade | VARCHAR(60) |  | Não | Cidade. |
| uf | VARCHAR(2) |  | Não | Sigla do estado (2 letras). |
| cep | VARCHAR(8) |  | Não | CEP, 8 dígitos sem máscara (RN05). |

## produtos

Cupcakes à venda.

| Coluna | Tipo | Chave | Nulo? | Descrição |
|---|---|---|---|---|
| id | INTEGER | PK | Não | Identificador do produto. |
| categoria_id | INTEGER | FK | Não | Categoria (FK categorias). |
| nome | VARCHAR(80) |  | Não | Nome do cupcake. |
| descricao | VARCHAR(300) |  | Sim | Descrição exibida ao cliente. |
| preco | NUMERIC(10, 2) |  | Não | Preço unitário em reais, maior que zero. |
| estoque | INTEGER |  | Não | Unidades disponíveis, ≥ 0 (RN06). |
| imagem_url | VARCHAR(255) |  | Sim | URL da foto (opcional). |
| ativo | BOOLEAN |  | Não | Se aparece na vitrine; produto com pedidos é só desativado (RN12). |

## pedidos

Pedidos realizados pelos clientes.

| Coluna | Tipo | Chave | Nulo? | Descrição |
|---|---|---|---|---|
| id | INTEGER | PK | Não | Número do pedido. |
| usuario_id | INTEGER | FK | Não | Cliente (FK usuarios). |
| endereco_id | INTEGER | FK | Não | Endereço de entrega (FK enderecos). |
| status | VARCHAR(25) |  | Não | AGUARDANDO_PAGAMENTO, CONFIRMADO, EM_PREPARO, SAIU_PARA_ENTREGA, ENTREGUE ou CANCELADO (RN09). |
| subtotal | NUMERIC(10, 2) |  | Não | Soma dos itens. |
| frete | NUMERIC(10, 2) |  | Não | Valor do frete (RN04). |
| total | NUMERIC(10, 2) |  | Não | subtotal + frete. |
| observacao | VARCHAR(200) |  | Sim | Observação do cliente (opcional). |
| criado_em | DATETIME |  | Não | Data/hora (UTC) do pedido. |

## entregas

Registro da entrega do pedido.

| Coluna | Tipo | Chave | Nulo? | Descrição |
|---|---|---|---|---|
| id | INTEGER | PK | Não | Identificador da entrega. |
| pedido_id | INTEGER | FK | Não | Pedido (FK única). |
| entregador | VARCHAR(80) |  | Sim | Nome do entregador (opcional). |
| previsao | DATE |  | Sim | Data prevista (opcional). |
| entregue_em | DATETIME |  | Sim | Data/hora da entrega efetiva. |

## itens_pedido

Itens de cada pedido.

| Coluna | Tipo | Chave | Nulo? | Descrição |
|---|---|---|---|---|
| id | INTEGER | PK | Não | Identificador do item. |
| pedido_id | INTEGER | FK | Não | Pedido (FK pedidos). |
| produto_id | INTEGER | FK | Não | Produto (FK produtos). |
| quantidade | INTEGER |  | Não | Quantidade, de 1 a 20 (RN03). |
| preco_unitario | NUMERIC(10, 2) |  | Não | Preço do produto no momento da compra (preserva histórico). |

## pagamentos

Pagamento do pedido (1 por pedido).

| Coluna | Tipo | Chave | Nulo? | Descrição |
|---|---|---|---|---|
| id | INTEGER | PK | Não | Identificador do pagamento. |
| pedido_id | INTEGER | FK | Não | Pedido (FK única). |
| forma | VARCHAR(10) |  | Não | PIX, CARTAO ou DINHEIRO (RN07). |
| status | VARCHAR(10) |  | Não | PENDENTE, APROVADO ou RECUSADO. Dados de cartão não são armazenados (RN08). |
| valor | NUMERIC(10, 2) |  | Não | Valor cobrado. |
| criado_em | DATETIME |  | Não | Data/hora (UTC). |
