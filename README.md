# 🧁 Doce Encanto – Aplicativo web de venda de cupcakes

Projeto Integrador Transdisciplinar em Engenharia de Software II (Cruzeiro do Sul Virtual).
Loja virtual com **vitrine, carrinho, pedido eletrônico, pagamento (simulado) e acompanhamento de entrega**, mais uma área administrativa.

**Aluno:** João Victor Moura Silva e Souza · **RGM:** 35687797

## Tecnologias
- Back-end: Python 3 + Flask, padrão **MVC** (Model, View, Controller + serviços)
- Banco de dados: **PostgreSQL** em produção · SQLite em desenvolvimento/testes (via SQLAlchemy)
- Front-end: HTML5, CSS3 e JavaScript (templates Jinja2), responsivo e acessível
- Testes: pytest (38 testes)

## Como rodar localmente
```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python seed.py                   # cria categorias, cupcakes de exemplo e o administrador
python run.py                    # http://127.0.0.1:5000
```
Administrador padrão: `admin@cupcakes.local` / `admin12345` (**troque** definindo `ADMIN_EMAIL` e `ADMIN_SENHA` antes de rodar o `seed.py`).

Cartões de teste do pagamento simulado: `4111 1111 1111 1111` (aprovado) e `4000 0000 0000 0002` (recusado). Use qualquer nome e CVV de 3 dígitos. Nenhum dado de cartão é armazenado.

## Testes
```bash
pytest
```

## Publicação (exemplo: Render)
1. Crie um banco **PostgreSQL** e copie a `DATABASE_URL`.
2. Crie um **Web Service** apontando para este repositório:
   - Build: `pip install -r requirements.txt`
   - Start: `gunicorn wsgi:app`
   - Variáveis: `DATABASE_URL`, `SECRET_KEY` (valor longo e aleatório), `ADMIN_EMAIL`, `ADMIN_SENHA`
3. No *Shell* do serviço, rode `python seed.py` uma vez.

## Estrutura do repositório
```
app/
  models.py          # MODEL: entidades e regras de domínio
  controllers/       # CONTROLLER: auth, catalogo, carrinho, pedidos, admin
  services/          # frete, pagamento (simulado) e carrinho em sessão
  templates/ static/ # VIEW: HTML, CSS, JS
tests/               # testes automatizados
database/schema.sql  # projeto físico (PostgreSQL)
docs/
  situacao-1-planejamento/   # UML (fontes .puml e imagens), DER, dicionário de dados, documentação em Word
  situacao-2-codigo/         # ver app/, tests/ e database/ (código-fonte)
  situacao-3-testes/         # formulário de teste, laudo de qualidade e evidências
```

## Regras de negócio e documentação
Todas as regras (RN01–RN12), os casos de uso expandidos e os diagramas estão em
`docs/situacao-1-planejamento/Documentacao_Projeto_Cupcakes.docx`.
