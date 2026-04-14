# models/document.py
# Modèle document - Accès à la table documents

from utils.db import get_db

class Document:
    """Classe modèle pour les documents"""

    @staticmethod
    def create(titre, description, fichier_nom, fichier_chemin, taille, type_mime, auteur_id, categorie_id=None, entreprise_id=None):
        """Crée un nouveau document"""
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO documents (titre, description, fichier_nom, fichier_chemin,
             fichier_taille, type_mime, auteur_id, statut, categorie_id, entreprise_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'brouillon', %s, %s)
        """, (titre, description, fichier_nom, fichier_chemin, taille, type_mime,
              auteur_id, categorie_id, entreprise_id))
        doc_id = cur.lastrowid
        conn.commit()
        cur.close()
        conn.close()
        return doc_id

    @staticmethod
    def get_by_id(doc_id):
        """Récupère un document par son ID avec ses relations"""
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT d.*, u.nom as auteur_nom, c.nom as categorie_nom, e.nom as entreprise_nom
            FROM documents d
            LEFT JOIN users u ON u.id = d.auteur_id
            LEFT JOIN categories c ON c.id = d.categorie_id
            LEFT JOIN entreprises e ON e.id = d.entreprise_id
            WHERE d.id = %s
        """, (doc_id,))
        doc = cur.fetchone()
        cur.close()
        conn.close()
        return doc

    @staticmethod
    def get_by_auteur(auteur_id):
        """Récupère les documents d'un auteur"""
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT d.*, c.nom as categorie_nom
            FROM documents d
            LEFT JOIN categories c ON c.id = d.categorie_id
            WHERE d.auteur_id = %s AND d.supprime_le IS NULL
            ORDER BY d.date_creation DESC
        """, (auteur_id,))
        docs = cur.fetchall()
        cur.close()
        conn.close()
        return docs

    @staticmethod
    def get_by_entreprise(entreprise_id):
        """Récupère les documents d'une entreprise"""
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT d.*, u.nom as auteur_nom, c.nom as categorie_nom
            FROM documents d
            LEFT JOIN users u ON u.id = d.auteur_id
            LEFT JOIN categories c ON c.id = d.categorie_id
            WHERE d.entreprise_id = %s AND d.supprime_le IS NULL
            ORDER BY d.date_creation DESC
        """, (entreprise_id,))
        docs = cur.fetchall()
        cur.close()
        conn.close()
        return docs

    @staticmethod
    def get_all(limit=100):
        """Récupère tous les documents (pour Admin Global)"""
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT d.*, u.nom as auteur_nom, e.nom as entreprise_nom, c.nom as categorie_nom
            FROM documents d
            LEFT JOIN users u ON u.id = d.auteur_id
            LEFT JOIN entreprises e ON e.id = d.entreprise_id
            LEFT JOIN categories c ON c.id = d.categorie_id
            WHERE d.supprime_le IS NULL
            ORDER BY d.date_creation DESC
            LIMIT %s
        """, (limit,))
        docs = cur.fetchall()
        cur.close()
        conn.close()
        return docs

    @staticmethod
    def get_by_status(status, entreprise_id=None):
        """Récupère les documents par statut"""
        conn = get_db()
        cur = conn.cursor()
        if entreprise_id:
            cur.execute("""
                SELECT d.*, u.nom as auteur_nom
                FROM documents d
                LEFT JOIN users u ON u.id = d.auteur_id
                WHERE d.statut = %s AND d.entreprise_id = %s AND d.supprime_le IS NULL
                ORDER BY d.date_creation DESC
            """, (status, entreprise_id))
        else:
            cur.execute("""
                SELECT d.*, u.nom as auteur_nom
                FROM documents d
                LEFT JOIN users u ON u.id = d.auteur_id
                WHERE d.statut = %s AND d.supprime_le IS NULL
                ORDER BY d.date_creation DESC
            """, (status,))
        docs = cur.fetchall()
        cur.close()
        conn.close()
        return docs

    @staticmethod
    def update_status(doc_id, status, validateur_id=None, commentaire=None):
        """Met à jour le statut d'un document"""
        conn = get_db()
        cur = conn.cursor()
        if status == 'valide':
            cur.execute("""
                UPDATE documents SET statut = %s, validateur_id = %s, date_validation = NOW()
                WHERE id = %s
            """, (status, validateur_id, doc_id))
        elif status == 'rejete':
            cur.execute("""
                UPDATE documents SET statut = %s, validateur_id = %s, commentaire_rejet = %s
                WHERE id = %s
            """, (status, validateur_id, commentaire, doc_id))
        else:
            cur.execute("UPDATE documents SET statut = %s WHERE id = %s", (status, doc_id))
        conn.commit()
        cur.close()
        conn.close()
        return True

    @staticmethod
    def soft_delete(doc_id, user_id):
        """Suppression logique (déplace vers corbeille)"""
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            UPDATE documents SET supprime_le = NOW(), supprime_par = %s
            WHERE id = %s
        """, (user_id, doc_id))
        conn.commit()
        cur.close()
        conn.close()
        return True

    @staticmethod
    def restore(doc_id):
        """Restaure un document depuis la corbeille"""
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            UPDATE documents SET supprime_le = NULL, supprime_par = NULL
            WHERE id = %s
        """, (doc_id,))
        conn.commit()
        cur.close()
        conn.close()
        return True

    @staticmethod
    def get_corbeille(entreprise_id=None):
        """Récupère les documents dans la corbeille"""
        conn = get_db()
        cur = conn.cursor()
        if entreprise_id:
            cur.execute("""
                SELECT id, titre, supprime_le as date_suppression
                FROM documents
                WHERE supprime_le IS NOT NULL AND entreprise_id = %s
                ORDER BY supprime_le DESC
            """, (entreprise_id,))
        else:
            cur.execute("""
                SELECT id, titre, supprime_le as date_suppression
                FROM documents
                WHERE supprime_le IS NOT NULL
                ORDER BY supprime_le DESC
            """)
        docs = cur.fetchall()
        cur.close()
        conn.close()
        return docs

    @staticmethod
    def delete_permanently(doc_id):
        """Supprime définitivement un document"""
        conn = get_db()
        cur = conn.cursor()
        cur.execute("DELETE FROM documents WHERE id = %s", (doc_id,))
        conn.commit()
        cur.close()
        conn.close()
        return True

    @staticmethod
    def get_evolution(entreprise_id=None, weeks=8):
        """Récupère l'évolution des documents sur N semaines"""
        conn = get_db()
        cur = conn.cursor()
        if entreprise_id:
            cur.execute("""
                SELECT DATE_FORMAT(date_creation, '%Y-%m-%d') as date_jour, COUNT(*) as total
                FROM documents
                WHERE entreprise_id = %s AND date_creation >= DATE_SUB(NOW(), INTERVAL %s WEEK)
                GROUP BY DATE(date_creation)
                ORDER BY date_jour ASC
            """, (entreprise_id, weeks))
        else:
            cur.execute("""
                SELECT DATE_FORMAT(date_creation, '%Y-%m-%d') as date_jour, COUNT(*) as total
                FROM documents
                WHERE date_creation >= DATE_SUB(NOW(), INTERVAL %s WEEK)
                GROUP BY DATE(date_creation)
                ORDER BY date_jour ASC
            """, (weeks,))
        results = cur.fetchall()
        cur.close()
        conn.close()
        return results