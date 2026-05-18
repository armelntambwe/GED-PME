# extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy import create_engine, MetaData
from config import Config

# ORM existant (ne pas toucher)
db = SQLAlchemy()
migrate = Migrate()

# SQLAlchemy Core (nouveau)
engine = create_engine(Config.DATABASE_URL_CORE, echo=False)
# Utiliser la même MetaData que Flask-SQLAlchemy pour simplifier Alembic
data_metadata = db.metadata