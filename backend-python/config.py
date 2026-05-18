# config.py
import os

class Config:
    MYSQL_HOST = 'localhost'
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = ''
    MYSQL_DB = 'ged_pme_test'

    SECRET_KEY = 'votre-cle-secrete-tres-longue-et-difficile-a-deviner'

    JWT_SECRET_KEY = 'votre-cle-secrete-tres-longue-2025'
    JWT_EXPIRATION_HOURS = 24

    # Configuration SQLAlchemy (pour ORM existant)
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DB}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Configuration pour SQLAlchemy Core (nouveau)
    DATABASE_URL_CORE = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DB}"


# Variables en dehors de la classe pour l'import direct
UPLOAD_FOLDER = 'uploads'
MAX_CONTENT_LENGTH = 16 * 1024 * 1024
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'jpg', 'jpeg', 'png', 'txt'}