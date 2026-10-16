import os
 
 
def _normalizar_uri(uri):
    # Provedores (ex.: Render) entregam "postgres://" ou "postgresql://". Forçamos o driver
    # psycopg (v3), que é o instalado no requirements.txt e funciona nas versões novas do Python.
    for prefixo in ("postgres://", "postgresql://", "postgresql+psycopg2://"):
        if uri.startswith(prefixo):
            return "postgresql+psycopg://" + uri[len(prefixo):]
    return uri
 
 
class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-chave-insegura-trocar-em-producao")
    SQLALCHEMY_DATABASE_URI = _normalizar_uri(os.environ.get("DATABASE_URL", "sqlite:///cupcake.db"))
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CSRF_ATIVO = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
 
 
class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    CSRF_ATIVO = False
    SECRET_KEY = "teste"
 