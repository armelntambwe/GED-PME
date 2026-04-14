# models/log.py
# Modèle log - Accès à la table logs

from utils.db import get_db

class Log:
    """Classe modèle pour les logs"""

    @staticmethod
    def create(action, description, user_id, document_id=None, ip_adresse=None):
        """Crée un nouveau log"""
        conn = get_db()
        cur = conn.cursor()
        # Note: la colonne dans la table s'appelle 'adresse_ip' (pas 'ip_adresse')
        cur.execute("""
            INSERT INTO logs (action, description, user_id, document_id, adresse_ip)
            VALUES (%s, %s, %s, %s, %s)
        """, (action, description, user_id, document_id, ip_adresse))
        log_id = cur.lastrowid
        conn.commit()
        cur.close()
        conn.close()
        return log_id

    @staticmethod
    def get_all(limit=200):
        """Récupère tous les logs"""
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT l.*, u.nom as utilisateur_nom, u.role, e.nom as entreprise_nom
            FROM logs l
            LEFT JOIN users u ON u.id = l.user_id
            LEFT JOIN entreprises e ON e.id = u.entreprise_id
            ORDER BY l.date_action DESC
            LIMIT %s
        """, (limit,))
        logs = cur.fetchall()
        cur.close()
        conn.close()
        return logs

    @staticmethod
    def get_by_user(user_id, limit=50):
        """Récupère les logs d'un utilisateur"""
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT * FROM logs
            WHERE user_id = %s
            ORDER BY date_action DESC
            LIMIT %s
        """, (user_id, limit))
        logs = cur.fetchall()
        cur.close()
        conn.close()
        return logs

    @staticmethod
    def get_by_document(document_id, limit=50):
        """Récupère les logs d'un document"""
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT l.*, u.nom as utilisateur_nom
            FROM logs l
            LEFT JOIN users u ON u.id = l.user_id
            WHERE l.document_id = %s
            ORDER BY l.date_action DESC
            LIMIT %s
        """, (document_id, limit))
        logs = cur.fetchall()
        cur.close()
        conn.close()
        return logs