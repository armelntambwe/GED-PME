# utils/db.py
# Connexion à la base de données MySQL

import pymysql
from config import Config

def get_db():
    """
    Établit et retourne une connexion à la base de données MySQL.
    Retourne un curseur avec les résultats sous forme de dictionnaire.
    """
    return pymysql.connect(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DB,
        cursorclass=pymysql.cursors.DictCursor
    )

def test_connection():
    """Teste la connexion à la base de données"""
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.close()
        conn.close()
        return True, "Connexion MySQL OK"
    except Exception as e:
        return False, f"Erreur MySQL: {str(e)}"