# utils/db.py
# Connexion à la base de données MySQL

import pymysql
from config import Config
from extensions import engine


def get_db():
    """
    Établit et retourne une connexion à la base de données MySQL (compatibilité existante).
    Retourne un objet `pymysql` connecté.
    """
    return pymysql.connect(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DB,
        cursorclass=pymysql.cursors.DictCursor
    )


def test_connection():
    """Teste la connexion via SQLAlchemy Engine si possible, sinon via pymysql.

    Retourne (bool, message).
    """
    try:
        # Prefer using SQLAlchemy core engine (partage de configuration avec Flask-SQLAlchemy)
        conn = engine.connect()
        conn.execute("SELECT 1")
        conn.close()
        return True, "Connexion base via SQLAlchemy OK"
    except Exception:
        # Fallback to pymysql test
        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute("SELECT 1")
            cur.close()
            conn.close()
            return True, "Connexion MySQL OK"
        except Exception as e:
            return False, f"Erreur MySQL: {str(e)}"