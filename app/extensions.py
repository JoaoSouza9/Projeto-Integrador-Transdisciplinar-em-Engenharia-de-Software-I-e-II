import warnings

from flask_sqlalchemy import SQLAlchemy

warnings.filterwarnings("ignore", message=".*Decimal objects natively.*")

db = SQLAlchemy()
