# models/entreprise.py
# Modèle entreprise - Accès à la table entreprises

from utils.db import get_db

class Entreprise:
    """Classe modèle pour les entreprises"""

    @staticmethod
    def create(nom, adresse=None, telephone=None, email=None):
        """Crée une nouvelle entreprise"""
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO entreprises (nom, adresse, telephone, email, statut)
            VALUES (%s, %s, %s, %s, 'actif')
        """, (nom, adresse, telephone, email))
        entreprise_id = cur.lastrowid
        conn.commit()
        cur.close()
        conn.close()
        return entreprise_id

    @staticmethod
    def get_all():
        """Récupère toutes les entreprises avec leurs statistiques"""
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT e.id, e.nom, e.adresse, e.telephone, e.email, e.statut,
                   COUNT(DISTINCT u.id) AS nb_employes,
                   COUNT(DISTINCT d.id) AS nb_documents
            FROM entreprises e
            LEFT JOIN users u ON u.entreprise_id = e.id
            LEFT JOIN documents d ON d.entreprise_id = e.id
            GROUP BY e.id
            ORDER BY e.nom ASC
        """)
        entreprises = cur.fetchall()
        cur.close()
        conn.close()
        return entreprises

    @staticmethod
    def get_by_id(entreprise_id):
        """Récupère une entreprise par son ID"""
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM entreprises WHERE id = %s", (entreprise_id,))
        ent = cur.fetchone()
        cur.close()
        conn.close()
        return ent

    @staticmethod
    def update(entreprise_id, nom=None, adresse=None, telephone=None, email=None):
        """Met à jour une entreprise"""
        conn = get_db()
        cur = conn.cursor()
        updates = []
        params = []
        if nom:
            updates.append("nom = %s")
            params.append(nom)
        if adresse:
            updates.append("adresse = %s")
            params.append(adresse)
        if telephone:
            updates.append("telephone = %s")
            params.append(telephone)
        if email:
            updates.append("email = %s")
            params.append(email)
        if not updates:
            return True
        params.append(entreprise_id)
        cur.execute(f"UPDATE entreprises SET {', '.join(updates)} WHERE id = %s", params)
        conn.commit()
        cur.close()
        conn.close()
        return True

    @staticmethod
    def toggle_status(entreprise_id):
        """Active ou suspend une entreprise"""
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT statut FROM entreprises WHERE id = %s", (entreprise_id,))
        ent = cur.fetchone()
        if not ent:
            return None
        nouvel_etat = 'suspendu' if ent['statut'] == 'actif' else 'actif'
        cur.execute("UPDATE entreprises SET statut = %s WHERE id = %s", (nouvel_etat, entreprise_id))
        conn.commit()
        cur.close()
        conn.close()
        return nouvel_etat

    @staticmethod
    def get_stats(entreprise_id):
        """Récupère les statistiques d'une entreprise"""
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) as total FROM documents WHERE entreprise_id = %s", (entreprise_id,))
        total_documents = cur.fetchone()['total']
        cur.execute("SELECT COUNT(*) as total FROM users WHERE entreprise_id = %s AND role = 'employe'", (entreprise_id,))
        total_employes = cur.fetchone()['total']
        cur.execute("SELECT COUNT(*) as total FROM documents WHERE entreprise_id = %s AND statut = 'soumis'", (entreprise_id,))
        en_attente = cur.fetchone()['total']
        cur.execute("SELECT COUNT(*) as total FROM documents WHERE entreprise_id = %s AND statut = 'valide'", (entreprise_id,))
        valides = cur.fetchone()['total']
        cur.close()
        conn.close()
        return {
            "total_documents": total_documents,
            "total_employes": total_employes,
            "en_attente": en_attente,
            "valides": valides
        }