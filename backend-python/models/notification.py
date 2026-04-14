# models/notification.py
# Modèle notification - Accès à la table notifications

from utils.db import get_db

class Notification:
    """Classe modèle pour les notifications"""

    @staticmethod
    def create(user_id, type_notif, message, lien=None):
        """Crée une notification pour un utilisateur"""
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO notifications (user_id, type, message, lien, lue)
            VALUES (%s, %s, %s, %s, 0)
        """, (user_id, type_notif, message, lien))
        notif_id = cur.lastrowid
        conn.commit()
        cur.close()
        conn.close()
        return notif_id

    @staticmethod
    def get_unread(user_id, limit=50):
        """Récupère les notifications non lues d'un utilisateur"""
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, type, message, lien, date_creation, lue
            FROM notifications
            WHERE user_id = %s AND lue = 0
            ORDER BY date_creation DESC
            LIMIT %s
        """, (user_id, limit))
        notifs = cur.fetchall()
        cur.close()
        conn.close()
        return notifs

    @staticmethod
    def get_all(user_id, limit=100):
        """Récupère toutes les notifications d'un utilisateur"""
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, type, message, lien, date_creation, lue
            FROM notifications
            WHERE user_id = %s
            ORDER BY date_creation DESC
            LIMIT %s
        """, (user_id, limit))
        notifs = cur.fetchall()
        cur.close()
        conn.close()
        return notifs

    @staticmethod
    def mark_as_read(notif_id, user_id):
        """Marque une notification comme lue"""
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            UPDATE notifications SET lue = 1
            WHERE id = %s AND user_id = %s
        """, (notif_id, user_id))
        conn.commit()
        cur.close()
        conn.close()
        return True

    @staticmethod
    def mark_all_as_read(user_id):
        """Marque toutes les notifications comme lues"""
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            UPDATE notifications SET lue = 1
            WHERE user_id = %s
        """, (user_id,))
        conn.commit()
        cur.close()
        conn.close()
        return True

    @staticmethod
    def count_unread(user_id):
        """Compte les notifications non lues"""
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT COUNT(*) as total FROM notifications
            WHERE user_id = %s AND lue = 0
        """, (user_id,))
        count = cur.fetchone()['total']
        cur.close()
        conn.close()
        return count

    @staticmethod
    def send_to_admins(entreprise_id, type_notif, message, lien=None):
        """Envoie une notification à tous les admins d'une entreprise"""
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT id FROM users
            WHERE entreprise_id = %s AND role = 'admin_pme'
        """, (entreprise_id,))
        admins = cur.fetchall()
        cur.close()
        for admin in admins:
            Notification.create(admin['id'], type_notif, message, lien)
        conn.close()
        return True