# ============================================
# utils/logger.py - Gestionnaire de logs
# ============================================
from flask import request

def ajouter_log(action, description, user_id, document_id=None):
    """
    Ajoute une entrée dans la table logs.
    À appeler dans chaque route importante.
    """
    from app import mysql
    
    cur = mysql.connection.cursor()
    cur.execute("""
        INSERT INTO logs (action, description, user_id, document_id)
        VALUES (%s, %s, %s, %s)
    """, (action, description, user_id, document_id))
    
    mysql.connection.commit()
    cur.close()