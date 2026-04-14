# models/user.py
# Modèle utilisateur - Accès à la table users

from utils.db import get_db

class User:
    """Classe modèle pour les utilisateurs"""

    @staticmethod
    def find_by_email(email):
        """Trouve un utilisateur par son email"""
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, nom, email, password, role, actif, entreprise_id, telephone, date_inscription
            FROM users WHERE email = %s
        """, (email,))
        user = cur.fetchone()
        cur.close()
        conn.close()
        return user

    @staticmethod
    def find_by_id(user_id):
        """Trouve un utilisateur par son ID"""
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, nom, email, telephone, role, actif, entreprise_id, date_inscription
            FROM users WHERE id = %s
        """, (user_id,))
        user = cur.fetchone()
        cur.close()
        conn.close()
        return user

    @staticmethod
    def create(nom, email, password_hash, role, telephone=None, entreprise_id=1):
        """Crée un nouvel utilisateur"""
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO users (nom, email, password, telephone, role, actif, entreprise_id)
            VALUES (%s, %s, %s, %s, %s, 1, %s)
        """, (nom, email, password_hash, telephone, role, entreprise_id))
        user_id = cur.lastrowid
        conn.commit()
        cur.close()
        conn.close()
        return user_id

    @staticmethod
    def get_all(entreprise_id=None):
        """Récupère tous les utilisateurs (filtrés par entreprise si spécifié)"""
        conn = get_db()
        cur = conn.cursor()
        if entreprise_id:
            cur.execute("""
                SELECT id, nom, email, telephone, role, actif, date_inscription
                FROM users WHERE entreprise_id = %s ORDER BY id DESC
            """, (entreprise_id,))
        else:
            cur.execute("""
                SELECT id, nom, email, telephone, role, actif, date_inscription
                FROM users ORDER BY id DESC
            """)
        users = cur.fetchall()
        cur.close()
        conn.close()
        return users

    @staticmethod
    def get_employees(entreprise_id):
        """Récupère les employés d'une entreprise (role = 'employe')"""
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, nom, email, telephone, role, actif, date_inscription
            FROM users WHERE entreprise_id = %s AND role = 'employe'
            ORDER BY id DESC
        """, (entreprise_id,))
        users = cur.fetchall()
        cur.close()
        conn.close()
        return users

    @staticmethod
    def deactivate(user_id):
        """Désactive un utilisateur (passe actif à 0)"""
        conn = get_db()
        cur = conn.cursor()
        cur.execute("UPDATE users SET actif = 0 WHERE id = %s", (user_id,))
        conn.commit()
        cur.close()
        conn.close()
        return True

    @staticmethod
    def update(user_id, nom=None, telephone=None):
        """Met à jour un utilisateur"""
        conn = get_db()
        cur = conn.cursor()
        if nom:
            cur.execute("UPDATE users SET nom = %s WHERE id = %s", (nom, user_id))
        if telephone:
            cur.execute("UPDATE users SET telephone = %s WHERE id = %s", (telephone, user_id))
        conn.commit()
        cur.close()
        conn.close()
        return True