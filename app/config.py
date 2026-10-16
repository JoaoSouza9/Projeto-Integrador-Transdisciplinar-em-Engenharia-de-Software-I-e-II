import os


def _normalizar_uri(uri):
    # Alguns provedores (ex.: Render/Heroku) entregam "postgres://", que o SQLAlchemy não aceita.
    if uri.startswith("postgres://"):
        return uri.replace("postgres://", "postgresql://", 1)
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
