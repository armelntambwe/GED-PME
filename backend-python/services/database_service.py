# services/database_service.py
"""
Service de base de données unifié utilisant SQLAlchemy Core.
Centralise TOUS les accès à la base de données pour éviter le SQL brut.
"""

from extensions import engine
from sqlalchemy import select, insert, update, delete, and_, or_, text
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DatabaseService:
    """Service unifié pour toutes les opérations base de données."""
    
    # ==================== AUTHENTIFICATION ====================
    
    @staticmethod
    def get_user_by_email(email: str):
        """Récupère un utilisateur par email."""
        try:
            with engine.connect() as conn:
                result = conn.execute(
                    text("""
                        SELECT id, nom, email, password, role, actif, 
                               entreprise_id, date_inscription
                        FROM users 
                        WHERE email = :email
                    """),
                    {"email": email}
                )
                row = result.fetchone()
                if row:
                    return {
                        'id': row[0],
                        'nom': row[1],
                        'email': row[2],
                        'password': row[3],
                        'role': row[4],
                        'actif': row[5],
                        'entreprise_id': row[6],
                        'date_inscription': row[7]
                    }
                return None
        except Exception as e:
            logger.error(f"Erreur get_user_by_email: {e}")
            raise

    @staticmethod
    def get_user_by_id(user_id: int):
        """Récupère un utilisateur par ID."""
        try:
            with engine.connect() as conn:
                result = conn.execute(
                    text("""
                        SELECT id, nom, email, password, role, actif, 
                               entreprise_id, date_inscription
                        FROM users 
                        WHERE id = :id
                    """),
                    {"id": user_id}
                )
                row = result.fetchone()
                if row:
                    return {
                        'id': row[0],
                        'nom': row[1],
                        'email': row[2],
                        'password': row[3],
                        'role': row[4],
                        'actif': row[5],
                        'entreprise_id': row[6],
                        'date_inscription': row[7]
                    }
                return None
        except Exception as e:
            logger.error(f"Erreur get_user_by_id: {e}")
            raise

    @staticmethod
    def create_user(nom: str, email: str, password_hash: str, role: str = 'employe', 
                   telephone: str = '', entreprise_id: int = None):
        """Crée un nouvel utilisateur."""
        try:
            with engine.connect() as conn:
                result = conn.execute(
                    text("""
                        INSERT INTO users (nom, email, password, role, telephone, 
                                          entreprise_id, actif, date_inscription)
                        VALUES (:nom, :email, :password, :role, :telephone, 
                               :entreprise_id, 1, NOW())
                    """),
                    {
                        'nom': nom,
                        'email': email,
                        'password': password_hash,
                        'role': role,
                        'telephone': telephone,
                        'entreprise_id': entreprise_id or 1
                    }
                )
                conn.commit()
                return result.lastrowid
        except Exception as e:
            logger.error(f"Erreur create_user: {e}")
            raise

    # ==================== CATÉGORIES ====================
    
    @staticmethod
    def get_categories(entreprise_id: int = None, limit: int = 100):
        """Récupère les catégories."""
        try:
            with engine.connect() as conn:
                if entreprise_id:
                    result = conn.execute(
                        text("""
                            SELECT id, nom, description, created_at, updated_at
                            FROM categories
                            WHERE entreprise_id = :entreprise_id
                            LIMIT :limit
                        """),
                        {'entreprise_id': entreprise_id, 'limit': limit}
                    )
                else:
                    result = conn.execute(
                        text("""
                            SELECT id, nom, description, created_at, updated_at
                            FROM categories
                            LIMIT :limit
                        """),
                        {'limit': limit}
                    )
                
                rows = result.fetchall()
                return [
                    {
                        'id': row[0],
                        'nom': row[1],
                        'description': row[2],
                        'created_at': row[3],
                        'updated_at': row[4]
                    }
                    for row in rows
                ]
        except Exception as e:
            logger.error(f"Erreur get_categories: {e}")
            raise

    @staticmethod
    def get_category_by_id(category_id: int):
        """Récupère une catégorie par ID."""
        try:
            with engine.connect() as conn:
                result = conn.execute(
                    text("""
                        SELECT id, nom, description, created_at, updated_at
                        FROM categories
                        WHERE id = :id
                    """),
                    {'id': category_id}
                )
                row = result.fetchone()
                if row:
                    return {
                        'id': row[0],
                        'nom': row[1],
                        'description': row[2],
                        'created_at': row[3],
                        'updated_at': row[4]
                    }
                return None
        except Exception as e:
            logger.error(f"Erreur get_category_by_id: {e}")
            raise

    @staticmethod
    def create_category(nom: str, description: str = '', entreprise_id: int = None):
        """Crée une nouvelle catégorie."""
        try:
            with engine.connect() as conn:
                result = conn.execute(
                    text("""
                        INSERT INTO categories (nom, description, entreprise_id, created_at, updated_at)
                        VALUES (:nom, :description, :entreprise_id, NOW(), NOW())
                    """),
                    {
                        'nom': nom,
                        'description': description,
                        'entreprise_id': entreprise_id or 1
                    }
                )
                conn.commit()
                return result.lastrowid
        except Exception as e:
            logger.error(f"Erreur create_category: {e}")
            raise

    @staticmethod
    def update_category(category_id: int, nom: str = None, description: str = None):
        """Met à jour une catégorie."""
        try:
            with engine.connect() as conn:
                updates = {'updated_at': datetime.now()}
                if nom is not None:
                    updates['nom'] = nom
                if description is not None:
                    updates['description'] = description
                
                set_clause = ', '.join([f"{k} = :{k}" for k in updates.keys()])
                
                conn.execute(
                    text(f"""
                        UPDATE categories
                        SET {set_clause}
                        WHERE id = :id
                    """),
                    {**updates, 'id': category_id}
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Erreur update_category: {e}")
            raise

    @staticmethod
    def delete_category(category_id: int):
        """Supprime une catégorie."""
        try:
            with engine.connect() as conn:
                conn.execute(
                    text("DELETE FROM categories WHERE id = :id"),
                    {'id': category_id}
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Erreur delete_category: {e}")
            raise

    # ==================== DOCUMENTS ====================
    
    @staticmethod
    def get_documents(entreprise_id: int = None, limit: int = 100):
        """Récupère les documents."""
        try:
            with engine.connect() as conn:
                if entreprise_id:
                    result = conn.execute(
                        text("""
                            SELECT id, titre, description, auteur_nom, status, 
                                   created_at, updated_at
                            FROM documents
                            WHERE entreprise_id = :entreprise_id
                            ORDER BY created_at DESC
                            LIMIT :limit
                        """),
                        {'entreprise_id': entreprise_id, 'limit': limit}
                    )
                else:
                    result = conn.execute(
                        text("""
                            SELECT id, titre, description, auteur_nom, status, 
                                   created_at, updated_at
                            FROM documents
                            ORDER BY created_at DESC
                            LIMIT :limit
                        """),
                        {'limit': limit}
                    )
                
                rows = result.fetchall()
                return [
                    {
                        'id': row[0],
                        'titre': row[1],
                        'description': row[2],
                        'auteur_nom': row[3],
                        'status': row[4],
                        'created_at': row[5],
                        'updated_at': row[6]
                    }
                    for row in rows
                ]
        except Exception as e:
            logger.error(f"Erreur get_documents: {e}")
            raise

    # ==================== UTILISATEURS ====================
    
    @staticmethod
    def get_users(entreprise_id: int = None, role: str = None, limit: int = 100):
        """Récupère les utilisateurs avec filtres optionnels."""
        try:
            with engine.connect() as conn:
                query = "SELECT id, nom, email, telephone, role, actif, date_inscription FROM users WHERE 1=1"
                params = {'limit': limit}
                
                if entreprise_id:
                    query += " AND entreprise_id = :entreprise_id"
                    params['entreprise_id'] = entreprise_id
                
                if role:
                    query += " AND role = :role"
                    params['role'] = role
                
                query += " LIMIT :limit"
                
                result = conn.execute(text(query), params)
                rows = result.fetchall()
                
                return [
                    {
                        'id': row[0],
                        'nom': row[1],
                        'email': row[2],
                        'telephone': row[3],
                        'role': row[4],
                        'actif': row[5],
                        'date_inscription': row[6]
                    }
                    for row in rows
                ]
        except Exception as e:
            logger.error(f"Erreur get_users: {e}")
            raise

    @staticmethod
    def update_user_status(user_id: int, actif: int):
        """Met à jour le statut actif d'un utilisateur."""
        try:
            with engine.connect() as conn:
                conn.execute(
                    text("""
                        UPDATE users
                        SET actif = :actif
                        WHERE id = :id
                    """),
                    {'actif': actif, 'id': user_id}
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Erreur update_user_status: {e}")
            raise

    @staticmethod
    def reset_user_password(user_id: int, password_hash: str):
        """Réinitialise le mot de passe d'un utilisateur."""
        try:
            with engine.connect() as conn:
                conn.execute(
                    text("""
                        UPDATE users
                        SET password = :password
                        WHERE id = :id
                    """),
                    {'password': password_hash, 'id': user_id}
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Erreur reset_user_password: {e}")
            raise

    # ==================== STATISTIQUES ====================
    
    @staticmethod
    def get_stats(entreprise_id: int = None):
        """Récupère les statistiques de l'entreprise."""
        try:
            with engine.connect() as conn:
                stats = {}
                
                # Documents totaux
                if entreprise_id:
                    result = conn.execute(
                        text("SELECT COUNT(*) FROM documents WHERE entreprise_id = :eid"),
                        {'eid': entreprise_id}
                    )
                else:
                    result = conn.execute(text("SELECT COUNT(*) FROM documents"))
                stats['total_documents'] = result.scalar() or 0
                
                # Utilisateurs totaux
                if entreprise_id:
                    result = conn.execute(
                        text("SELECT COUNT(*) FROM users WHERE entreprise_id = :eid"),
                        {'eid': entreprise_id}
                    )
                else:
                    result = conn.execute(text("SELECT COUNT(*) FROM users"))
                stats['total_employes'] = result.scalar() or 0
                
                # Catégories totales (toujours globales, pas filtrées par entreprise)
                result = conn.execute(text("SELECT COUNT(*) FROM categories"))
                stats['total_categories'] = result.scalar() or 0
                
                return stats
        except Exception as e:
            logger.error(f"Erreur get_stats: {e}")
            raise
