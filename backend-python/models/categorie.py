# models/categorie.py
# Modèle catégorie - Accès à la table categories

from utils.db import get_db

class Categorie:
    """Classe modèle pour les catégories"""

    @staticmethod
    def create(nom, description=None):
        """Crée une nouvelle catégorie"""
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO categories (nom, description)
            VALUES (%s, %s)
        """, (nom, description))
        category_id = cur.lastrowid
        conn.commit()
        cur.close()
        conn.close()
        return category_id

    @staticmethod
    def get_all():
        """Récupère toutes les catégories"""
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, nom, description, date_creation
            FROM categories ORDER BY nom ASC
        """)
        categories = cur.fetchall()
        cur.close()
        conn.close()
        return categories

    @staticmethod
    def get_by_id(categorie_id):
        """Récupère une catégorie par son ID"""
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id, nom, description FROM categories WHERE id = %s", (categorie_id,))
        cat = cur.fetchone()
        cur.close()
        conn.close()
        return cat

    @staticmethod
    def update(categorie_id, nom=None, description=None):
        """Met à jour une catégorie"""
        conn = get_db()
        cur = conn.cursor()
        if nom:
            cur.execute("UPDATE categories SET nom = %s WHERE id = %s", (nom, categorie_id))
        if description:
            cur.execute("UPDATE categories SET description = %s WHERE id = %s", (description, categorie_id))
        conn.commit()
        cur.close()
        conn.close()
        return True

    @staticmethod
    def delete(categorie_id):
        """Supprime une catégorie"""
        conn = get_db()
        cur = conn.cursor()
        cur.execute("DELETE FROM categories WHERE id = %s", (categorie_id,))
        conn.commit()
        cur.close()
        conn.close()
        return True